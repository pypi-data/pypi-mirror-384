import os
import torch
import torch.nn as nn
import zipfile
import subprocess

from transformers import AutoTokenizer, AutoModel
import teradataml as tdml
from teradataml.context.context import _get_database_username, _get_current_databasename, _get_context_temp_databasename
import pandas as pd
import time

import tdstone2.tdstone
from tdstone2 import logger

import os
import sys
import torch
from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch.nn as nn
import logging
import onnx
from onnx import helper, shape_inference  # Add shape_inference import
import onnxruntime as rt
from onnxruntime.tools.onnx_model_utils import make_dim_param_fixed
import pandas as pd
import ast
import uuid
from tdstone2.utils import generate_create_table_teradata, retry_on_upstream_timeout

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture all log levels, including DEBUG

# Create handlers
console_handler = logging.StreamHandler()  # Logs to console
file_handler = logging.FileHandler('tdsgenai_lake.log')  # Logs to a file

# Ensure both handlers log all levels
console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add the formatter to the handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to the logger
#logger.addHandler(console_handler)
logger.addHandler(file_handler)

def save_embeddings_model(model_name: str, local_dir: str):
    """
    Downloads the specified Hugging Face SentenceTransformer model and saves it in the native format
    at a specified local directory. The model can later be reloaded directly from this directory
    using SentenceTransformer.

    Args:
        model_name (str): The name of the pre-trained SentenceTransformer model to download.
        local_dir (str): The root directory where the model will be saved in a subdirectory named
                         after the model, with '/' replaced by '--' for a valid path.

    Returns:
        str: The path to the saved model directory.
    """

    # Sanitize model name by replacing '/' with '--' for a valid directory name
    valid_model_name = 'models--' + model_name.replace("/", "--")
    model_dir = os.path.join(local_dir, valid_model_name)

    # Ensure the target directory exists
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        logger.info(f"Created model directory at: {model_dir}")

    # Set up a temporary cache directory to download model files
    temporary_cache_dir = os.path.join(model_dir, "temp_cache")
    os.environ["TRANSFORMERS_CACHE"] = temporary_cache_dir  # Or os.environ["HF_HOME"] for future compatibility
    logger.info(f"Temporary cache directory set to: {temporary_cache_dir}")

    # Download and save the model locally in the specified directory
    try:
        logger.info(f"Downloading and saving model: {model_name}")
        model = SentenceTransformer(model_name)
        model.save(model_dir)
        logger.info(f"Model '{model_name}' successfully saved at: {model_dir}")
    finally:
        # Clean up by removing the temporary cache directory and unsetting the environment variable
        if os.path.exists(temporary_cache_dir):
            for root, dirs, files in os.walk(temporary_cache_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(temporary_cache_dir)
            logger.info(f"Temporary cache directory '{temporary_cache_dir}' has been cleaned up.")

        # Unset the TRANSFORMERS_CACHE environment variable
        del os.environ["TRANSFORMERS_CACHE"]

    return model_dir


def zip_saved_files(model_name: str, local_dir: str) -> str:
    """
    Archives the specified model's tokenizer and embeddings files by creating a zip file
    with a standardized name. The zip file is saved in a 'models' directory for organization.

    Args:
        model_name (str): The name of the model whose files are being archived.
        local_dir (str): The directory containing the tokenizer and embeddings model files.

    Returns:
        str: The path to the created zip file stored in the 'models' directory.
    """

    # Sanitize model name by replacing '/' with '--' for a valid file name
    valid_model_name = 'models--'+model_name.replace("/", "--")

    # Ensure a dedicated 'models' directory exists to store the zip file
    models_dir = os.path.join(".", "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Created 'models' directory at {models_dir}")

    # Define the zip file path using the sanitized model name
    zip_path = os.path.join(models_dir, f"{valid_model_name}.zip")

    # Zip the contents of local_dir into the specified zip file
    logger.info(f"Creating zip archive for files in {local_dir} at {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Add each file to the zip, preserving directory structure relative to local_dir
                zipf.write(file_path, os.path.relpath(file_path, local_dir))

    logger.info(f"Successfully created zip file at {zip_path}")
    return zip_path


def get_embeddings_model_zip(model_name: str, local_dir: str) -> str:
    """
    Downloads the specified model's tokenizer and embeddings layer, saves them locally in the
    specified directory, exports the embeddings layer to ONNX format, and archives the saved files
    into a zip file for easy deployment.

    Args:
        model_name (str): The name of the pre-trained model to download.
        local_dir (str): The directory where the tokenizer, embeddings model, and ONNX files will be saved.

    Returns:
        str: The path to the created zip file containing the tokenizer and ONNX model files.
    """

    # Step 1: Save the tokenizer and embeddings model locally in ONNX format
    logger.info(f"Starting download and saving process for model: {model_name} in directory: {local_dir}")
    save_embeddings_model(model_name, local_dir)
    logger.info(f"Model {model_name} successfully saved in native huggingface format in directory: {local_dir}")

    # Step 2: Archive the saved files into a zip file
    logger.info(f"Creating zip archive for model: {model_name} in directory: {local_dir}")
    zip_file_path = zip_saved_files(model_name, local_dir)
    logger.info(f"Zip archive created at: {zip_file_path}")

    return zip_file_path


def install_zip_in_vantage(zip_file_path: str, oaf_env_name: str, replace=False):
    """
    Installs the specified model zip file into a Teradata Vantage environment, setting up the necessary
    session parameters. Handles errors and ensures logging for successful installation.

    Args:
        zip_file_path (str): The full path to the zip file, including the filename and .zip extension.
        oaf_env_name (str): The Teradata Vantage environment name where the model will be installed.
        replace (bool, optional): If True, replaces any existing model with the same name in Vantage.

    Returns:
        None
    """

    # Extract the file name without the .zip extension and replace '-' with '_'
    file_name = os.path.basename(zip_file_path).replace(".zip", "").replace('-', '_')
    logger.info(f"Preparing to install model from zip file: {file_name} in environment: {oaf_env_name}")

    # Set up the environment based on the provided environment name
    logger.info(f"Connecting to the {oaf_env_name} environment.")
    oaf_env = retry_on_upstream_timeout(logger=logger)(tdml.get_env)(oaf_env_name)

    # Attempt to install the zip file in the specified Vantage environment
    try:
        logger.info(
            f"Starting installation of zip file: {zip_file_path} to environment: {oaf_env_name} (model name: {file_name})")
        claim_id = oaf_env.install_model(model_path=zip_file_path, replace=replace, asynchronous = True)
        logger.info(
            f"Claimid for model installation '{claim_id}'")
        try:
            stage = oaf_env.status(claim_id)['Stage'].iloc[-1]
            while stage != 'File Installed':
                stage = oaf_env.status(claim_id)['Stage'].iloc[-1]
                logger.info(
                    f"Claimid {claim_id}  status '{stage}'")
                time.sleep(5)
        except Exception as e:
            logger.info(f"error {str(e)}")
            raise
        logger.info(
            f"Successfully installed model '{file_name}' from zip file: {zip_file_path} in environment '{oaf_env_name}'.")

    except Exception as e:
        # Log the error with relevant details
        logger.error(
            f"Installation failed for zip file: {zip_file_path} (model name: {file_name}) in environment: {oaf_env_name}. Error: {str(e)}")
        raise

    logger.info(f"Installation completed for zip file: {zip_file_path} in environment: {oaf_env_name}.")


def install_model_in_vantage_from_name(
        model_name: str,
        local_dir: str = None,
        oaf_env_name: str = None,
        replace=False
):
    """
    Downloads the specified model, saves it in a zip file, and installs the file in the specified
    Teradata Vantage environment. Ensures database context is restored after the installation.

    Args:
        model_name (str): The name of the pre-trained model to download.
        local_dir (str, optional): Directory to save the tokenizer, embeddings model, and zip file.
                                   Defaults to './models/{model_name}' with '/' replaced by '--'.
        oaf_env_name (str, optional): The Teradata Vantage environment name where the model zip
                                      file will be installed.
        replace (bool, optional): If True, replaces the existing model in Vantage if one exists.
                                  Defaults to False.

    Returns:
        None
    """

    # Set the local directory for saving model files
    if local_dir is None:
        valid_model_name = model_name.replace("/", "--")
        local_dir = os.path.join(".", "models", valid_model_name)
        logger.info(f"Set local directory for model files: {local_dir}")

    # Step 1: Download model and create a zip file
    logger.info(f"Creating zip file for model: {model_name}")
    zip_file_path = get_embeddings_model_zip(model_name, local_dir)
    logger.info(f"Zip file created at: {zip_file_path}")

    # Step 2: Install the zip file in Teradata Vantage environment
    try:
        logger.info(f"Installing model in Vantage environment: {oaf_env_name}")
        install_zip_in_vantage(zip_file_path, oaf_env_name, replace=replace)
    except Exception as e:
        logger.error(f"Failed to install model in Vantage: {e}")
        raise

    logger.info(f"Model '{model_name}' successfully installed in Vantage environment '{oaf_env_name}'.")


def list_installed_models(oaf: str = None):
    """
    Lists all installed models in the specified Teradata database environment that start with a defined prefix and end with a specified suffix.

    Args:
        oaf (str, optional): The identifier for the Teradata database environment. If not provided, defaults to the current or temporary environment.

    Returns:
        DataFrame: A Teradata DataFrame containing the list of installed models with filenames that match the specified prefix and suffix.

    Raises:
        ValueError: If the specified database environment cannot be loaded.
    """

    logger.info("Starting model listing in environment: %s", oaf)

    try:
        oaf_env = retry_on_upstream_timeout(logger=logger)(tdml.get_env)(oaf)
        if not oaf_env:
            raise ValueError(f"Environment '{oaf}' could not be loaded.")
    except Exception as e:
        logger.error("Failed to load environment %s: %s", oaf, e)
        raise ValueError(f"Environment '{oaf}' could not be loaded due to an error: {e}")

    logger.info("Environment %s loaded successfully", oaf)
    result = oaf_env.models
    logger.info("Models listed successfully in environment: %s", oaf)

    return result


def setup_and_execute_script(model_name: str, dataset, text_column, hash_columns: list, accumulate_columns=[],
                             delimiter: str = ',', oaf_env: str = None, batch_size = 32, half_precision = False, device = 'cuda'):
    """
    Set up the Teradata session, unzip the model, and execute the script via tdml.
    If no database is provided, the default one will be used. After execution, the original default database is restored.

    Args:
        model (str): The model file to be unzipped and used.
        dataset: The dataset used in the tdml.Script.
        delimiter (str): The delimiter used in the script for data splitting (default is tab-delimited '\t').
        database (str, optional): The database to set the session for and work with (uses default if not provided).
        data_hash_column (str, optional): The column name for the data hash (default is 'Problem_Type').

    Returns:
        sto (tdml.Script): The tdml.Script object configured and executed.
    """
    accumulate_columns = hash_columns + [c for c in accumulate_columns if c not in hash_columns]
    text_column_position, hash_columns_positions, accumulate_positions = get_column_positions(dataset, text_column,
                                                                                              hash_columns,
                                                                                              accumulate_columns)

    sqlalchemy_types = dataset._td_column_names_and_sqlalchemy_types

    # Get the current database before changing the session
    previous_database = _get_current_databasename()

    if half_precision:
        half = 1
    else:
        half = 0

    # Set default database if not provided
    if oaf_env is None:
        database = _get_current_databasename()
        logger.info(f"Using default OpenAF environment: {oaf_env}")
    else:
        logger.info(f"Using provided OpenAF environment: {oaf_env}")

    try:
        # Generate the execution command
        command = f"""python3 tds_vector_embedding_lake.py {model_name} {batch_size} {text_column_position} [{'-'.join([str(a) for a in accumulate_positions])}] {delimiter} {device} {half}"""
        logger.info(f"bash command : {command}")
        # Create the tdml.Script object
        oaf = tdml.Apply(
            data             = dataset[[text_column]+accumulate_columns],
            apply_command    = command,
            data_hash_column = hash_columns,
            is_local_order   = False,
            env_name         = oaf_env,
            delimiter        = delimiter if len(delimiter)==1 else ast.literal_eval(delimiter),
            returns          = tdml.OrderedDict(
                [('"'+c+'"', sqlalchemy_types[c.lower()]) for c in accumulate_columns] +
                [
                    ("jobid", tdml.VARCHAR(length=36, charset='latin')),
                    ("process_time", tdml.FLOAT()),
                    ("elapsed_time", tdml.FLOAT())
                ] +
                [
                    ("Model", tdml.VARCHAR(length=1024, charset='latin')),
                    ("Device", tdml.VARCHAR(length=1024, charset='latin')),
                    ("Half_Precision", tdml.SMALLINT()),
                    ("Batch_Size", tdml.INTEGER()),
                    ("Batch_Id", tdml.INTEGER()),
                    ("Vector_Dimension", tdml.INTEGER()),
                    ("Vector", tdml.VARCHAR(length=32000, charset='latin'))
                ]
            )
        )

        return oaf
        logger.info(f"Apply object successfully created")
    except Exception as e:
        # Restore the previous database after execution
        logger.error(f"Apply object not successfully created")
        raise


def execute_and_create_pivot_view(oaf, schema_name: str, table_name: str, hash_columns: list = None, if_exists: str ='replace'):
    """
    Execute the given tdml.Script, save the results to a SQL table, and create a pivot view.

    Args:
        oaf (tdml.Script): The tdml.Script object to execute.
        schema_name (str): The name of the schema where the table and view will be created.
        table_name (str): The name of the table to store the results.

    Returns:
        tdml.DataFrame: A DataFrame of the created pivot view.
    """

    from teradataml.context.context import _get_database_username




    logger.info(oaf.show_query())
    # check if the table exists:
    logger.info(f"Check the existence of the destination table")
    table_exists = ('t_'+table_name.lower() in [c.lower() for c in tdml.db_list_tables(object_type='table',schema_name=schema_name).TableName.tolist()])

    # create the table if it does not exists of drop it before if if_exists == 'replace'
    if table_exists == False or (table_exists and if_exists == 'replace'):


        query = generate_create_table_teradata(table_name=tdml.in_schema(schema_name,'T_'+table_name), columns=oaf.returns, primary_index=hash_columns)

        if table_exists and if_exists == 'replace':
            tdml.execute_sql(f"DROP TABLE {tdml.in_schema(schema_name,'T_'+table_name)}")
            logger.info(f"The T_{table_name} in the {schema_name} database has been dropped.")
        else:
            logger.info(f"The T_{table_name} does not exists in the {schema_name} database.")
        try:
            tdml.execute_sql(query)
        except Exception as e:
            print(str(e))
            print(query)
            raise
        logger.info(f"Table T_{table_name} has been successfully created in the {schema_name} database.")
    else:
        logger.info(f"Destination table T_{table_name} already exists in the {schema_name} database. Results will be append in.")
        query = None
    logger.info("Starting script execution and SQL table creation.")
    # Measure the execution time
    tic = time.time()
    # Execute the script and store the result in a SQL table
    try:
        res = retry_on_upstream_timeout(logger=logger)(oaf.execute_script)()
    except Exception as e:
        tac = time.time()
        logger.info(f"Script execution. Computation time: {tac - tic:.2f} seconds")
        if query:
            logger.info(query)
        try:
            logger.info(oaf.execute_script().columns)
            logger.info(oaf.execute_script()._td_column_names_and_sqlalchemy_types)
            #logger.info(tdml.DataFrame(tdml.in_schema(schema_name,'T_' + table_name)))
        except Exception as e:
            raise
        raise

    tac = time.time()
    logger.info(f"Script execution. Computation time: {tac - tic:.2f} seconds")

    # Attribute a uuid
    run_uuid = str(uuid.uuid4())
    cols     = res.columns
    res      = res.assign(run_id = run_uuid)[['run_id']+cols]
    logger.info(f"This computations is identified with the {run_uuid} identifier")


    logger.info("Starting storage of the result in OFS table.")
    tic = time.time()
    try:
        res.to_sql(
            schema_name=schema_name,
            table_name='T_' + table_name,
            if_exists='append'
        )
    except Exception as e:
        logger.error(f"Storage in OFS table: error {str(e)}")
        logger.error(f"Storage in OFS table: res.columns {res.columns}")
        res.to_sql(
            schema_name=schema_name,
            table_name='T_' + table_name,
            if_exists='replace'
        )
    tac = time.time()
    logger.info(f"Storage in OFS table. Storage time: {tac - tic:.2f} seconds")

    # Compute vector_dimension from the stored table
    vector_dimension_query = f"SEL TOP 1 Vector_Dimension FROM {schema_name}.T_{table_name}"
    vector_dimension = tdml.execute_sql(vector_dimension_query).fetchall()[0][0]
    logger.info(f"Computed vector dimension: {vector_dimension}")

    # Create a expanded view
    output_cols = ','.join(["'V_" + str(i) + "'" for i in range(vector_dimension)])
    type_cols = ','.join(["'real'"] * vector_dimension)
    accumulate_cols = ','.join(["'" + c + "'" for c in res.columns if c not in ['Vector']])
    cols = ','.join([c for c in res.columns if c not in ['Vector']] + ["V_" + str(i) for i in range(vector_dimension)])
    query = f"""
    REPLACE VIEW {schema_name}.{table_name} AS
    LOCK ROW FOR ACCESS
    SELECT {cols} FROM Unpack (
      ON {schema_name}.T_{table_name} AS InputTable
      USING
      TargetColumn ('Vector')
      OutputColumns ({output_cols})
      OutputDataTypes ({type_cols})
      Delimiter (' ') 
      Regex ('(.*)')
      RegexSet (1)
      IgnoreInvalid ('true')
      Accumulate ({accumulate_cols})
    ) AS dt
    """
    # Execute the SQL query to create the pivot view
    logger.info(f"Creating pivot view {table_name}.")
    tdml.execute_sql(query)

    logger.info(f"Pivot view {table_name} created successfully.")

    # Return the DataFrame of the created view
    return tdml.DataFrame(tdml.in_schema(schema_name, table_name))


def get_column_positions(dataset, text_column: str, hash_columns: list, accumulate: list):
    """
    Get the positions of the text_column, hash_columns, and accumulate columns in the dataset.
    Ensure that there is no overlap between the sets of indices.

    Args:
        dataset: A Teradata DataFrame.
        text_column (str): The name of the text column.
        hash_columns (list): A list of column names to hash.
        accumulate (list): A list of column names to accumulate.

    Returns:
        tuple: The position of text_column, list of positions of hash_columns, and list of positions of accumulate columns.

    Raises:
        ValueError: If there is an overlap in the column indices between the three sets.
    """
    # Get the list of columns from the dataset
    dataset_columns = list(dataset.columns)

    # Get the position of text_column
    try:
        text_column_position = dataset_columns.index(text_column)
    except ValueError:
        raise ValueError(f"'{text_column}' not found in the dataset columns.")

    # Get the positions of hash_columns
    if hash_columns is not None:
        try:
            hash_columns_positions = [dataset_columns.index(col) for col in hash_columns]
        except ValueError as e:
            raise ValueError(f"One or more hash_columns not found in the dataset: {e}")
    else:
        hash_columns_positions = None

    # Get the positions of accumulate columns
    try:
        accumulate_positions = [dataset_columns.index(col) for col in accumulate]
    except ValueError as e:
        raise ValueError(f"One or more accumulate columns not found in the dataset: {e}")

    # Ensure no overlap between the three sets of column indices
    all_positions = set([text_column_position]) | set(accumulate_positions)
    if len(all_positions) != 1 + len(accumulate_positions):
        raise ValueError("There is an overlap in the column indices between text_column, hash_columns, and accumulate.")

    # Return the positions
    return text_column_position, hash_columns_positions, accumulate_positions


def compute_vector_embedding(model_name, dataset, schema_name, table_name, text_column, hash_columns = None, accumulate_columns=[], oaf_env = None, batch_size = 32, half_precision = False, device = 'cuda', delimiter = ',', if_exists= 'replace'):
    """
    Set up and execute a script for the given model and dataset, ensuring that the text column is VARCHAR
    and the model exists. Finally, create a pivot view of the results.

    Args:
        model_name (str): The name of the model file.
        dataset: A Teradata DataFrame.
        schema_name (str): The schema name where the table and view will be created.
        table_name (str): The name of the table to store the results.
        text_column (str): The name of the text column.
        hash_columns (list): A list of columns to hash.
        accumulate_columns (list): A list of columns to accumulate.

    Returns:
        tdml.DataFrame: A DataFrame of the created pivot view.

    Raises:
        ValueError: If the text_column is not of type VARCHAR or the model is not found.
    """
    from sqlalchemy.sql.sqltypes import VARCHAR, CLOB

    # Get the environment
    if oaf_env in retry_on_upstream_timeout(logger=logger)(tdml.list_user_envs)()['env_name'].tolist():
        logger.info(f"The {oaf_env} environment exists.")
    else:
        logger.error(f"The {oaf_env} environment does not exist.")
        logger.error(f"Here is the list of environments")
        logger.error(retry_on_upstream_timeout(logger=logger)(tdml.list_user_envs)()['env_name'].tolist())
        raise

    # Initial logger message explaining the function's purpose
    if hash_columns is None:
        logger.info(f"Starting computation of vector embedding for the text in '{text_column}' using model '{model_name}'. "
                    f"and the results will be stored in the '{schema_name}' schema. "
                    f"Results will be saved in the table 'T_{table_name}' and accessible through the pivoted view '{table_name}'."
                    )
    else:
        logger.info(f"Starting computation of vector embedding for the text in '{text_column}' using model '{model_name}'. "
                    f"The computation will be distributed across the hash columns {hash_columns}, "
                    f"and the results will be stored in the '{schema_name}' schema. "
                    f"Results will be saved in the table 'T_{table_name}' and accessible through the pivoted view '{table_name}'."
                    )
    if len(accumulate_columns)>0:
        logger.info(f"{accumulate_columns} will be included in the result set.")
    logger.info("Starting the process of script execution and view creation.")

    # Check if the text_column is a VARCHAR in the dataset
    column_types = dataset._td_column_names_and_sqlalchemy_types
    logger.info(f"Checking if the column '{text_column}' is of type VARCHAR.")

    if text_column.lower() not in column_types or not (isinstance(column_types[text_column.lower()], VARCHAR) or isinstance(column_types[text_column.lower()], CLOB)):
        logger.error(f"The column '{text_column}' is not of type VARCHAR or CLOB but of type {str(column_types[text_column.lower()])}.")
        raise ValueError(f"The column '{text_column}' must be of type VARCHAR.")
    else:
        logger.info(f"Column '{text_column}' is valid and of type VARCHAR.")

    # Check if the model exists in the installed models
    logger.info(f"Checking if the model '{model_name}' exists in the installed models.")
    installed_models_df = retry_on_upstream_timeout(logger=logger)(list_installed_models)(oaf_env)

    if not any(installed_models_df['Model'].str.contains(model_name)):
        logger.error(f"Model '{model_name}' not found in the installed models.")
        raise ValueError(f"Model '{model_name}' not found in the installed models.")
    else:
        logger.info(f"Model '{model_name}' found in the installed models.")

    # If the checks pass, set up and execute the script
    logger.info("Setting up and executing the script.")
    oaf = setup_and_execute_script(
        model_name         = model_name,
        dataset            = dataset,
        text_column        = text_column,
        hash_columns       = hash_columns,
        accumulate_columns = accumulate_columns,
        oaf_env            = oaf_env,
        batch_size         = batch_size,
        half_precision     = half_precision,
        device             = device,
        delimiter          = delimiter
    )
    logger.info("Script setup and execution completed.")
    logger.info(f"Dataset size :{dataset.shape}")

    # Execute and create the pivot view
    logger.info(f"Creating pivot view for schema '{schema_name}' and table '{table_name}'.")
    res = execute_and_create_pivot_view(oaf, schema_name, table_name, hash_columns = hash_columns, if_exists = if_exists)
    logger.info(f"Pivot view created successfully for table '{table_name}' in schema '{schema_name}'.")

    return res


def get_tdstone2_data_script_path():
    """
    Dynamically find the path of the 'tds_vector_embedding.py' script in the tdstone2 package.
    This works for editable mode installations (pip install -e).
    """
    return os.path.join(tdstone2.tdstone.this_dir, "data", "tds_vector_embedding_lake.py")


def run_tds_vector_embedding_script_locally(df, model_name, text_column, accumulate_columns, batch_size = 32, delimiter = ',', print_warnings = False, half_precision = False, device = 'cuda'):
    """
    Runs the 'tds_vector_embedding.py' script in the data module of the 'tdstone2' package
    by passing a dataframe via stdin and the required arguments.

    Args:
        df (pd.DataFrame): The dataframe to process.
        zip_file_path (str): The path to the zip file.
        text_column (int): The index of the text column in the dataframe.
        accumulate_columns (list): The list of column indexes to accumulate and print.

    Returns:
        pd.DataFrame: The resulting output from stdout as a pandas DataFrame.
    """

    logger.info("Starting the vector embedding script.")

    # Convert the dataframe to the expected input format (tab-delimited)
    input_data = df[[text_column]+accumulate_columns].apply(lambda row: '\t'.join(map(str, row.values)), axis=1).str.cat(sep='\n')
    logger.info("Dataframe converted to tab-delimited format.")

    # Get column positions
    text_column_, _, accumulate_columns_ = get_column_positions(df, accumulate=accumulate_columns, hash_columns='',
                                                                text_column=text_column)
    logger.info(f"Text column: {text_column_}, Accumulate columns: {accumulate_columns_}")

    # Prepare the arguments to pass to the script
    script_path = get_tdstone2_data_script_path()  # Replace this with how you get the path in your environment

    # Check if the script path exists
    if not os.path.exists(script_path):
        logger.error(f"Script file not found: {script_path}")
        return None

    if half_precision:
        half = 1
    else:
        half = 0

    # Prepare the command-line arguments
    args = [sys.executable, script_path, model_name, str(batch_size), str(text_column_), str(accumulate_columns_), delimiter, str(device), str(half)]
    logger.info(f"Running script with arguments: {args}")

    # Run the script with the dataframe input piped to stdin
    try:
        result = subprocess.run(
            args,
            input          = input_data,  # Pass the dataframe as stdin input
            text           = True,  # Treat input and output as text (string)
            capture_output = True,  # Capture the stdout and stderr
            check          = False  # Raise an error if the subprocess fails
        )
        logger.info("Script executed successfully.")
        if print_warnings:
            print(result.stderr)
        print(result.stderr)
        # Parse the stdout into a pandas DataFrame
        output = result.stdout.strip()  # Remove any extra whitespace around the output

        if output:  # Ensure there is output to process
            logger.info("Processing script output into DataFrame.")
            rows = [line.split('\t') for line in output.split('\n')]  # Split rows and columns based on tab delimiter
            logger.info(rows[0])
            df_output = pd.DataFrame(rows,
                                     columns=accumulate_columns + ['jobid','process_time','elapsed_time'] + ['Model', 'Device', 'Half_Precision', 'Batch_Size', 'Batch_Id', 'Vector_Dimension', 'Vector'])

            # # Pivot the DataFrame to get the embeddings in a proper structure
            # df_output = df_output.pivot(columns='Vector_Dimension', values='V',
            #                             index=accumulate_columns + ['jobid','process_time','elapsed_time']  + ['model','device', 'half_precision', 'batch_size'])[[str(i) for i in range(df_output['Vector_Dimension'].astype(int).max()+1)]]
        else:
            logger.warning("No output from the script. Returning an empty DataFrame.")
            df_output = pd.DataFrame()  # Return an empty DataFrame if no output

        return df_output

    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running the script: {e.stderr}")
        return None