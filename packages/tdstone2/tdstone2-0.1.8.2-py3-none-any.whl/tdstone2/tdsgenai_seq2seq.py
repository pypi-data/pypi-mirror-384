import warnings
warnings.filterwarnings("ignore")
import shutil
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
from sqlalchemy import func
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
import uuid
import json

warnings.resetwarnings()
# Set up logging
logger = logging.getLogger(__name__)


def make_dim_param_fixed(graph, dim_name, fixed_value):
    """Utility function to fix dynamic dimension sizes."""
    for dim_param in graph.input:
        for dim in dim_param.type.tensor_type.shape.dim:
            if dim.dim_param == dim_name:
                dim.dim_value = fixed_value


def fix_model_dimensions(model, opset_version = 12, batch_size=1, sequence_length=512, num_return_sequences=1, max_length=100):
    """
    Fix the dimensions in an ONNX model manually.

    Parameters:
    - model_path: Path to the input ONNX model.
    - output_path: Path to save the modified ONNX model.
    - batch_size: Fixed batch size.
    - sequence_length: Fixed sequence length.
    - num_return_sequences: Fixed number of return sequences.
    - max_length: Fixed maximum length for generated sequences.
    """

    op = onnx.OperatorSetIdProto()
    logger.info(f"Use opset version {opset_version}")
    op.version = opset_version

    # Load the existing ONNX model
    model = onnx.helper.make_model(model.graph, ir_version = 8, opset_imports = [op])

    # Fix the dimensions for input_ids and attention_mask
    for input in model.graph.input:
        if input.name in ["input_ids", "attention_mask"]:
            # Fix batch_size and sequence_length
            input.type.tensor_type.shape.dim[0].dim_param = str(batch_size)
            input.type.tensor_type.shape.dim[1].dim_param = str(sequence_length)
            

    # Fix dimensions for inputs
    for input in model.graph.input:
        if input.type.tensor_type.shape.dim:
            input.type.tensor_type.shape.dim[0].dim_value = batch_size
            if len(input.type.tensor_type.shape.dim) > 1:
                input.type.tensor_type.shape.dim[1].dim_value = sequence_length

    # Fix dimensions for outputs and intermediate tensors
    for value_info in model.graph.value_info:
        if value_info.type.tensor_type.shape.dim:
            value_info.type.tensor_type.shape.dim[0].dim_value = batch_size
            if len(value_info.type.tensor_type.shape.dim) > 1:
                value_info.type.tensor_type.shape.dim[1].dim_value = sequence_length
                
    make_dim_param_fixed(model.graph, "num_return_sequences", 1)
    make_dim_param_fixed(model.graph, "max_length", 100)  

    return model
    
def save_tokenizer_and_seq2seq_model_onnx(
        model_name: str,
        local_dir: str,
        model_task: None,
        device: str = "cpu",
        opset_version: int = 12,
        sequence_length: int = 512,
        max_length: int = 100,
        model_type: str = 't5',
        no_repeat_ngram_size: int = 2,
        total_runs: int = 0
        ):
    """
    Downloads and saves the tokenizer, exports the full transformer model using optimum-cli,
    and refines the exported ONNX model by fixing dynamic dimensions and removing unnecessary outputs.

    Args:
        model_name (str): The name of the pre-trained SentenceTransformer model to download.
        local_dir (str): The directory where the tokenizer and full transformer model will be saved.
        device (str): The device to move the model and inputs to ('cpu' or 'cuda').
        opset_version (int): The ONNX opset version to use for the export.
    """
    # Ensure the local directory exists
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        logger.info(f"Created directory: {local_dir}")

    if model_type == 't5':
        from transformers import T5TokenizerFast 
        logger.info(f"Downloading the tokenizer of: {model_name}")
        tokenizer = T5TokenizerFast.from_pretrained(model_name)
        logger.info(f"Save the tokenizer in: {local_dir}")
        tokenizer.save_pretrained(local_dir)
    else:
        logger.error(f"Model type {model_type} not supported ")
        raise

    # Step 1: Download and save the tokenizer locally
    logger.info(f"Downloading and converting the model: {model_name}")
    onnx_model_path = os.path.join(local_dir,'model.onnx')
    logger.info(f"Running onnxruntime.transformers.convert_generation export command for model: {model_name}")
    command = f"python -m onnxruntime.transformers.convert_generation --total_runs {total_runs} --disable_perf_test --disable_parity -m {model_name} --model_type {model_type} --output {onnx_model_path} --no_repeat_ngram_size {no_repeat_ngram_size}  --custom_attention_mask "
    logger.info(f"onnx conversion command: {command}")

    # Use os.system to execute the command
    exit_code = os.system(command)

    # Check if the system command was successful
    if exit_code not in [0] and not os.path.exists(onnx_model_path):
        logger.error(f"Error: onnxruntime.transformers.convert_generation command failed with exit code {exit_code}")
        sys.exit(exit_code)

    logger.info(f"Model exported successfully to {local_dir}")

    # Step 3: Load the exported ONNX model
    if os.path.exists(onnx_model_path):
        logger.info(f"Reload the onnx file  {onnx_model_path}")
        model = onnx.load(onnx_model_path)
    else:
        logger.error(f"{onnx_model_path} does not exist. Check if the generation was successful")
        raise

    # Step 4: Refine the ONNX model (fix dimensions, remove outputs)
    logger.info("Refining the ONNX model...")

    refined_model = fix_model_dimensions(model,
                                        opset_version= opset_version,
                                        sequence_length = sequence_length,
                                        max_length = max_length,
                                        )
    # # Set the opset version for the refined model
    # op = onnx.OperatorSetIdProto()
    # op.version = opset_version
    # logger.info(f"Use opset version {opset_version}")
    # refined_model = onnx.helper.make_model(model.graph, ir_version=8, opset_imports=[op])

    # # Step 5: Fix dynamic dimension sizes (batch_size, sequence_length, max_lenght)
    # make_dim_param_fixed(refined_model.graph, "sequence_length", sequence_length)
    # make_dim_param_fixed(refined_model.graph, "num_return_sequences", 1)
    # make_dim_param_fixed(refined_model.graph, "max_length", max_length)

    # # Step 6: Save the refined ONNX model
    refined_onnx_model_path = os.path.join(local_dir, f"full_model.onnx")
    logger.info(f"Refined ONNX model saved at {refined_onnx_model_path}")
    onnx.save(refined_model, refined_onnx_model_path)
 
    for file_name in os.listdir(local_dir):
        if file_name.endswith(".onnx") and file_name != "full_model.onnx":
            file_path = os.path.join(local_dir, file_name)
            try:
                os.remove(file_path)
                logger.info(f"Removed suboptimal ONNX model: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")

    return



def zip_saved_files(model_name: str, local_dir: str, sequence_length: int = 512, max_length: int = 100) -> list:
    """
    Zips all files in the specified directory (excluding subdirectories) and splits the resulting zip file into three parts.
    The model_name will have '/' replaced with '_' to create a valid filename.
    The zip files will be placed in a dedicated 'models' folder to avoid issues with the source folder.

    Args:
        model_name (str): The name of the model whose files are being zipped.
        local_dir (str): The directory where the files are located.

    Returns:
        list: A list of paths to the created zip files in the 'models' directory.
    """
    # Replace '/' with '_' in the model name for valid file naming
    valid_model_name = model_name.replace("/", "_").replace(".", "_")

    # Create a dedicated models folder if it doesn't exist
    models_dir = os.path.join(".", "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Created models directory at {models_dir}")

    # Path for the zip file in the models folder
    zip_path = os.path.join(models_dir, f"tdstone2_seq2seq_{sequence_length}_{max_length}_{valid_model_name}.zip")

    # Zip the contents of the local_dir (excluding subdirectories)
    logger.info(f"Zipping files in directory: {local_dir} to {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_name in os.listdir(local_dir):
            file_path = os.path.join(local_dir, file_name)
            if os.path.isfile(file_path):
                zipf.write(file_path, os.path.basename(file_path))

    logger.info(f"Files have been zipped to {zip_path}")

    # Split the resulting zip file into three parts
    logger.info(f"Splitting zip file: {zip_path} into 3 parts")
    zip_files = split_zip_file(zip_path, models_dir)

    return zip_files

def split_zip_file(zip_path, output_dir, num_parts=3):
    """
    Split `zip_path` into `num_parts` byte-level chunks
    so they can be reassembled with: 
        cat part1 part2 ... > original.zip
    """
    file_size = os.path.getsize(zip_path)
    logger.info(f"File size: {file_size}")
    part_size = file_size // num_parts
    remainder = file_size % num_parts
    
    parts = []
    
    with open(zip_path, 'rb') as src:
        for i in range(num_parts):
            # Determine how many bytes this part should contain
            current_part_size = part_size + (1 if i < remainder else 0)
            if current_part_size == 0:
                break
            
            # Name each part
            part_filename = os.path.join(output_dir, f"{os.path.basename(zip_path)}.part{i+1}")
            parts.append(part_filename)
            
            # Write the chunk to the part file
            with open(part_filename, 'wb') as dst:
                chunk = src.read(current_part_size)
                dst.write(chunk)
    
    return parts


def get_tokenizer_and_seq2seq_model_zip(
        model_name: str,
        local_dir: str,
        model_task: str = None,
        sequence_length: int = 512,
        max_length: int = 100,
        generate_zip = True,
        model_type: str = 't5',
        no_repeat_ngram_size: int = 2,
        total_runs: int = 0
        ) -> str:
    """
    Downloads the tokenizer and embeddings layer of the specified model, saves them locally,
    exports the embeddings layer to ONNX format, and zips the saved files into a single archive.

    Args:
        model_name (str): The name of the pre-trained model to download.
        local_dir (str): The directory where the tokenizer, embeddings model, and ONNX files will be saved.

    Returns:
        str: The path to the created zip file containing the tokenizer and ONNX model files.
    """
    # Save the tokenizer and embeddings model in ONNX format
    logger.info(f"Saving tokenizer and seq2seq model for: {model_name}")
    save_tokenizer_and_seq2seq_model_onnx(
        model_name,
        local_dir,
        model_task,
        sequence_length=sequence_length,
        max_length = max_length,
        model_type = model_type,
        no_repeat_ngram_size = no_repeat_ngram_size,
        total_runs = total_runs
    )

    if generate_zip:
        # Zip the saved files and return the zip file path
        zip_file_path = zip_saved_files(model_name, local_dir, sequence_length=sequence_length, max_length=max_length)

        return zip_file_path
    else:
        return local_dir


def install_zip_in_vantage(zip_file_path: str, database: str, replace = False, SEARCHUIFDBPATH : str = None) :
    """
        Installs a specified zip file into a Teradata Vantage database after setting required session parameters.

        This function sets up the environment by configuring the session to the target database, then installs
        the provided zip file into Teradata Vantage. If the `replace` flag is set to True, any existing installation
        with the same file identifier will be replaced.

        Args:
            zip_file_path (str): The full path to the zip file, including the filename and `.zip` extension.
            database (str): The name of the Teradata Vantage database where the file will be installed.
            replace (bool, optional): If set to True, replaces an existing file with the same identifier in the
                database. Defaults to False.
            SEARCHUIFDBPATH (str, optional): A specific database path to use for session parameters. If not
                provided, defaults to the `database` argument.

        Returns:
            None

        Raises:
            Exception: Logs an error if the zip file installation fails.

        Notes:
            - The function requires that `tdml` is properly configured for executing SQL commands and file
              installations within Teradata Vantage.
            - The function assumes that `logger` is set up for logging the installation process and any
              potential errors.

        Example:
            install_zip_in_vantage('/path/to/file.zip', 'my_database', replace=True)

        Steps:
            1. Extracts the file name without the .zip extension for use as a file identifier.
            2. Sets session parameters in Teradata to configure the appropriate database.
            3. Initiates the installation process for the zip file within Teradata Vantage.
            4. Logs installation success or failure.
    """
    # Extract the file name without the zip extension
    file_name = os.path.basename(zip_file_path).replace(".zip", "").replace('-', '_').replace('.','__')

    # Set session parameters to point to the correct database
    if SEARCHUIFDBPATH is None:
        SEARCHUIFDBPATH = database
    logger.info(f"Setting session parameters for database: {SEARCHUIFDBPATH}")
    tdml.execute_sql(f"SET SESSION SEARCHUIFDBPATH = {SEARCHUIFDBPATH};")
    tdml.execute_sql(f'DATABASE "{SEARCHUIFDBPATH}";')

    # Install the zip file in Teradata Vantage
    logger.info(f"Installing zip file: {zip_file_path} in database: {SEARCHUIFDBPATH}")
    try:
        logger.info(f"Zip file {zip_file_path} installation to {SEARCHUIFDBPATH} database started ({file_name})")
        tdml.install_file(
            replace = replace,
            file_identifier=file_name,  # Filename without the zip extension
            file_path=zip_file_path,  # Full path to the zip file with .zip extension
            file_on_client=True,  # Indicates the file is located on the client machine
            is_binary=True  # Specifies that the file is binary
        )
        logger.info(f"Zip file {zip_file_path} has been installed in the {SEARCHUIFDBPATH} database.")

    except Exception as e:
        # Log error details and the file info
        logger.error(
            f"Failed to install the zip file: {zip_file_path} (file_name: {file_name}) in database: {SEARCHUIFDBPATH}. Error: {str(e)}")
        if 'The user does not have CREATE EXTERNAL PROCEDURE access to SYSUIF.REPLACE_FILE.' in str(e):
            try:
                tdml.install_file(
                    replace = False,  # Do not replace if the file already exists
                    file_identifier=file_name,  # Filename without the zip extension
                    file_path=zip_file_path,  # Full path to the zip file with .zip extension
                    file_on_client=True,  # Indicates the file is located on the client machine
                    is_binary=True  # Specifies that the file is binary
                )
                logger.info(f"Zip file {zip_file_path} has been installed in the {SEARCHUIFDBPATH} database.")
            except Exception as e:
                logger.error(
                            f"Failed to install the zip file: {zip_file_path} (file_name: {file_name}) in database: {SEARCHUIFDBPATH}. Error: {str(e)}")
        else:
            raise Exception(
                f"Error installing the zip file: {zip_file_path} in database: {SEARCHUIFDBPATH}. Error: {str(e)}"
            )
        

    


def install_model_in_vantage_from_name(
        model_name: str,
        local_dir: str = None,
        model_task: str = None,
        database: str = None,
        replace=False,
        sequence_length: int = 512,
        max_length: int = 100,
        upload = True,
        generate_zip = True,
        model_type: str = 't5',
        no_repeat_ngram_size: int = 2,
        total_runs: int = 0
):
    """
    Downloads the tokenizer and embeddings layer of the specified model, saves them as a zip file,
    and installs the zip file in Teradata Vantage. Ensures that the database context is restored
    to its original state after the installation.

    Args:
        model_name (str): The name of the pre-trained model to download (e.g., "bert-base-uncased").
        local_dir (str, optional): The directory where the tokenizer, embeddings model, and zip file
                                   will be saved. Defaults to './models/{model_name}'.
        model_task (str, optional): The specific task type for the model (e.g., "classification").
        database (str, optional): The Teradata Vantage database where the model's zip file will
                                  be installed. Defaults to the current database in the session.
        replace (bool, optional): Whether to replace an existing model installation. Defaults to False.
        sequence_length (int, optional): The sequence length used by the embeddings model.
                                         Defaults to 512.
        upload (bool, optional) : If true, the zip file will be uploaded. Defaults to True.
        generate_zip (bool, optional) : If true, the zip file will be generated. Defaults to True.

    Returns:
        None

    Raises:
        Exception: Propagates any exceptions raised during model file preparation or installation.
    """

    if upload:
        generate_zip = True

    # Determine the local directory for storing model files if not explicitly provided
    if local_dir is None:
        valid_model_name = model_name.replace("/", "_")  # Replace slashes for file-system compatibility
        local_dir = os.path.join(".", "models", valid_model_name)
        logger.info(f"Local directory for model files set to: {local_dir}")

    # Retrieve the current database name to restore context later
    original_database = _get_current_databasename()

    # Use the original database if no specific database is provided
    if database is None:
        database = original_database
        logger.info(f"Using default database: {database}")

    # Step 1: Prepare the zip file by saving the tokenizer and embeddings model
    zip_file_path = get_tokenizer_and_seq2seq_model_zip(
        model_name,
        local_dir,
        model_task,
        sequence_length      = sequence_length,
        max_length           = max_length,
        generate_zip         = generate_zip,
        model_type           = model_type,
        no_repeat_ngram_size = no_repeat_ngram_size,
        total_runs           = total_runs 
    )

    # Step 2: Install the zip file into the specified database in Teradata Vantage
    if upload:
        try:
            for file in zip_file_path:
                install_zip_in_vantage(file, database, replace=replace)
        finally:
            # Restore the original database context to ensure no side effects
            if original_database:
                tdml.execute_sql(f'DATABASE "{original_database}";')
                logger.info(f"Database context has been reset to {original_database}.")
            else:
                logger.warning("No original database context was found to reset.")

        # Log success
        logger.info(f"Model {model_name} has been successfully installed in the {database} database.")
    else:
        logger.info(f"The zip file for Model {model_name} has been successfully created.")


def list_installed_files(database: str = None, startswith: str = 'tdstone2_seq2seq_', endswith: str = 'part1', SEARCHUIFDBPATH : str = None):
    """
    Lists all installed files in the specified database that start with the specified prefix and end with the specified suffix.

    Args:
        database (str, optional): The database where the files are installed. If not provided, defaults to the current or temporary database.
        startswith (str, optional): The prefix for filtering filenames. Defaults to 'tdstone2_emb_'.
        endswith (str, optional): The suffix for filtering filenames. Defaults to '.zip'.

    Returns:
        DataFrame: A Teradata DataFrame containing the list of matching files in the specified database.
    """

    # Set default database if not provided
    if database is None:
        database = _get_current_databasename()
        logger.info(f"Using default database: {database}")
    else:
        logger.info(f"Using provided database: {database}")

    # Ensure that session search path is set to the correct database
    if SEARCHUIFDBPATH is None:
        SEARCHUIFDBPATH = database
    tdml.execute_sql(f"SET SESSION SEARCHUIFDBPATH = {SEARCHUIFDBPATH};")
    logger.info(f"Session search path set to database: {SEARCHUIFDBPATH}")

    # Prepare the query to list installed files
    query = f"""
    SELECT DISTINCT
      '{SEARCHUIFDBPATH}' as DATABASE_LOCATION,
      res as tdstone2_models,
      file_size as file_size
    FROM
        Script(
            SCRIPT_COMMAND(
                'ls -lh {SEARCHUIFDBPATH.upper()}/ | awk ''{{print $9, $5}}''' 
            )
            RETURNS(
                'res varchar(1024)',
                'file_size varchar(1024)'
            )
            DELIMITER(' ')
        ) AS d
    WHERE lower(res) LIKE '{startswith.lower()}%{endswith.lower()}%'
    """

    logger.info(
        f"Executing query to list installed files starting with '{startswith}' and ending with '{endswith}' in database {SEARCHUIFDBPATH}")

    # Execute the query and return the result as a DataFrame
    #result = pd.read_sql(query, con=tdml.get_context())
    result = pd.DataFrame(tdml.execute_sql(query).fetchall(), columns = ['DATABASE_LOCATION','tdstone2_models','file_size'])
    logger.info(f"Query executed successfully, returning result")
    
    result['file_id_1'] = result['tdstone2_models'].str.replace(".part1", "__part1", regex=False).str.replace("-", "_", regex=False)
    result['file_id_2'] = result['tdstone2_models'].str.replace(".part1", "__part2", regex=False).str.replace("-", "_", regex=False)
    result['file_id_3'] = result['tdstone2_models'].str.replace(".part1", "__part3", regex=False).str.replace("-", "_", regex=False)
    result['tdstone2_models'] = result['tdstone2_models'].str.replace(".part1", "", regex=False)
    result = result.sort_values('tdstone2_models')
    return result


def setup_and_execute_script(
        model: str,
        dataset, 
        text_column, 
        hash_columns: list, 
        accumulate_columns=[],
        delimiter: str = '\t',
        database: str = None,
        SEARCHUIFDBPATH: str = None,
        min_length = 10,
        repetition_penalty = 2,
        num_beams = 4,
        num_return_sequences = 1,
        length_penalty = 0,
        prompt = 'summarize:',
        model_type = 't5',
        max_length = 100
        ):
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

    # Set default database if not provided
    if database is None:
        database = _get_current_databasename()
        logger.info(f"Using default database: {database}")
    else:
        logger.info(f"Using provided database: {database}")

    try:
        # Set the Teradata session and database path
        if SEARCHUIFDBPATH is None:
            SEARCHUIFDBPATH = database
        tdml.execute_sql(f"SET SESSION SEARCHUIFDBPATH = {SEARCHUIFDBPATH};")
        tdml.execute_sql(f'DATABASE "{SEARCHUIFDBPATH}";')

        # Generate the unzip and execution command
        model_folder = model.split('.')[0]
        command = f"""cat {SEARCHUIFDBPATH}/{model}.zip.part1 {SEARCHUIFDBPATH}/{model}.zip.part2 {SEARCHUIFDBPATH}/{model}.zip.part3 > $PWD/temp.zip && unzip $PWD/temp.zip -d $PWD/{model_folder}/ > /dev/null && tdpython3 ./{SEARCHUIFDBPATH}/tds_seq2seq.py {model_folder} {text_column_position} [{'-'.join([str(a) for a in accumulate_positions])}] {min_length} {repetition_penalty} {num_beams} {num_return_sequences} {length_penalty} {max_length} {model_type} "{prompt}" """
        logger.info(f"bash command : {command}")
        # Create the tdml.Script object
        sto = tdml.Script(
            data=dataset,
            script_name='tds_seq2seq.py',
            files_local_path='.',
            script_command=command,
            data_hash_column=hash_columns,  # Use provided data_hash_column or default 'Problem_Type'
            is_local_order=False,
            returns=tdml.OrderedDict(
                [(c, sqlalchemy_types[c.lower()]) for c in accumulate_columns] +
                [
                    ("jobid", tdml.VARCHAR(length=36, charset='latin')),
                    ("process_time", tdml.FLOAT()),
                    ("elapsed_time", tdml.FLOAT())
                ] +
                [
                    ("Model", tdml.VARCHAR(length=1024, charset='latin')),
                    ("nb_tokens_input", tdml.INTEGER()),
                    ("nb_tokens_output", tdml.INTEGER()),
                    ("response", tdml.VARCHAR(length=32000, charset='latin')),
                ]
            )
        )
        logger.info(f"returns : {sto.returns}")
        return sto

    finally:
        # Restore the previous database after execution
        tdml.execute_sql(f'DATABASE "{previous_database}";')
        logger.info(f"Restored previous database: {previous_database}")


def execute_and_create_pivot_view(sto, schema_name: str, table_name: str, hash_columns = None, if_exists='replace'):
    """
    Execute the given tdml.Script, save the results to a SQL table, and create a pivot view.

    Args:
        sto (tdml.Script): The tdml.Script object to execute.
        schema_name (str): The name of the schema where the table and view will be created.
        table_name (str): The name of the table to store the results.

    Returns:
        tdml.DataFrame: A DataFrame of the created pivot view.
    """

    from teradataml.context.context import _get_database_username

    logger.info("Starting script execution and SQL table creation.")

    # Measure the execution time
    tic = time.time()

    # Execute the script and store the result in a SQL table
    try:
        df_sto = sto.execute_script()
    except Exception as e:
        tac = time.time()
        logger.info(f"Script query construction. Construction time: {tac - tic:.2f} seconds")
        raise


    tac = time.time()
    logger.info(f"Script query construction. Construction time: {tac - tic:.2f} seconds")

    # Measure the execution time
    tic = time.time()
    # Execute the script and store the result in a SQL table
    try:
        types = sto.returns
        
        df_sto.to_sql(
            schema_name = schema_name,
            table_name  = 'TV_' + table_name,
            if_exists   = if_exists,
            temporary   = True,
            types       = types
        )
        df_sto = tdml.DataFrame(tdml.in_schema(_get_database_username(), 'TV_' + table_name))
    except Exception as e:
        tac = time.time()
        logger.info(f"Script execution and storage in volatile table. Computation time: {tac - tic:.2f} seconds")
        raise

    tac = time.time()
    logger.info(f"Script execution and storage in volatile table. Computation time: {tac - tic:.2f} seconds")

    # Attribute a uuid
    run_uuid = str(uuid.uuid4())
    cols = df_sto.columns
    df_sto = df_sto.assign(run_id = run_uuid)[['run_id']+cols]
    logger.info(f"This computations is identified with the {run_uuid} identifier")

    # Measure the storage time
    tic = time.time()
    try:
        if hash_columns is None:
            df_sto.to_sql(
                schema_name   = schema_name,
                table_name    = 'T_' + table_name,
                if_exists     = if_exists,
                temporary     = True,
                types         = {'run_id':tdml.VARCHAR(length=36, charset='LATIN')}
            )
        else:
            df_sto.to_sql(
                schema_name   = schema_name,
                table_name    = 'T_' + table_name,
                if_exists     = if_exists,
                primary_index = hash_columns,
                types         = {'run_id':tdml.VARCHAR(length=36, charset='LATIN')}
            )
    except Exception as e:
        tac = time.time()
        logger.info(f"Data stored in T_{table_name}. Storage time: {tac - tic:.2f} seconds")
        raise

    tac = time.time()
    logger.info(f"Data stored in T_{table_name}. Storage time: {tac - tic:.2f} seconds")

    # Generate the pivot columns for the view using the computed vector_dimension
    columns = '\n,'.join(df_sto.columns)

    # Create a Expanded view
    query = f"""
    REPLACE VIEW {schema_name}."{table_name}" AS
    LOCK ROW FOR ACCESS
    SELECT 
    {columns} 
    FROM {schema_name}.T_{table_name}
    """

    # Execute the SQL query to create the pivot view
    logger.info(f"Creating view {table_name}.")
    try:
        tdml.execute_sql(query)
    except Exception as e:
        logger.error(f"Error when creating the view {table_name}.")
        print(query)
        raise

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
    try:
        hash_columns_positions = [dataset_columns.index(col) for col in hash_columns]
    except ValueError as e:
        raise ValueError(f"One or more hash_columns not found in the dataset: {e}")

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


def compute_seq2seq(model, dataset, schema_name, table_name, text_column, hash_columns, accumulate_columns=[],
                             SEARCHUIFDBPATH=None, if_exists='replace',
                             min_length = 10,
                            repetition_penalty = 2,
                            num_beams = 4,
                            num_return_sequences = 1,
                            length_penalty = 0,
                            prompt = 'summarize:',
                            model_type = 't5',
                            max_length = 100,
                    ):
    """
    Computes vector embeddings for a specified text column using a given model, stores the results
    in a database table, and creates a pivot view for analysis.

    This function validates the input parameters, ensures the model is available, checks the
    type of the text column, and orchestrates the embedding computation and view creation processes.

    Args:
        model (str): The name of the model file to use for embedding computation.
        dataset: A Teradata DataFrame containing the data to process.
        schema_name (str): The schema name where the result table and view will be created.
        table_name (str): The name of the table to store computed embeddings.
        text_column (str): The column in the dataset containing text for embedding computation.
        hash_columns (list): A list of columns used to hash and distribute computations.
        accumulate_columns (list, optional): Additional columns to include in the result set. Defaults to an empty list.
        SEARCHUIFDBPATH (str, optional): The file path for the model search UI database. Defaults to None.
        if_exists (str, optional): Policy for handling table/view creation if they already exist. Defaults to 'replace'.

    Returns:
        tdml.DataFrame: A DataFrame representing the created pivot view with computed embeddings.

    Raises:
        ValueError:
            - If the `text_column` is not of type VARCHAR or CLOB.
            - If the specified model is not found among installed models.
    """
    from sqlalchemy.sql.sqltypes import VARCHAR, CLOB

    # Log the start of the vector embedding computation process
    logger.info(f"Starting vector embedding computation for column '{text_column}' using model '{model}'.")
    logger.info(
        f"Results will be stored in schema '{schema_name}', table 'T_{table_name}', and accessed via view '{table_name}'.")
    if accumulate_columns:
        logger.info(f"Accumulating additional columns in results: {accumulate_columns}.")

    # Step 1: Validate that the text_column exists and is of type VARCHAR or CLOB
    column_types = dataset._td_column_names_and_sqlalchemy_types
    logger.info(f"Validating type of column '{text_column}' (must be VARCHAR or CLOB).")
    if text_column.lower() not in column_types or not (
            isinstance(column_types[text_column.lower()], VARCHAR) or isinstance(column_types[text_column.lower()],
                                                                                 CLOB)
    ):
        logger.error(
            f"Invalid type for column '{text_column}'. Expected VARCHAR or CLOB, but got: {str(column_types[text_column.lower()])}.")
        raise ValueError(f"Column '{text_column}' must be of type VARCHAR or CLOB.")
    logger.info(f"Column '{text_column}' is valid and correctly typed.")

    # Step 2: Verify the model exists among installed models
    logger.info(f"Checking if model '{model}' exists in the installed models.")
    installed_models_df = list_installed_files(SEARCHUIFDBPATH=SEARCHUIFDBPATH)
    if not any(installed_models_df['tdstone2_models'].str.contains(model)):
        logger.error(f"Model '{model}' not found in the installed models.")
        raise ValueError(f"Model '{model}' not found in installed models.")
    logger.info(f"Model '{model}' successfully verified as installed.")

    # Step 3: Set up and execute the embedding computation script
    logger.info("Setting up and executing the script for embedding computation.")
    sto = setup_and_execute_script(
        model=model,
        dataset=dataset,
        text_column=text_column,
        hash_columns=hash_columns,
        accumulate_columns=accumulate_columns,
        SEARCHUIFDBPATH=SEARCHUIFDBPATH,
        min_length = min_length,
        repetition_penalty = repetition_penalty,
        num_beams = num_beams,
        num_return_sequences = num_return_sequences,
        length_penalty = length_penalty,
        prompt = prompt,
        model_type = model_type,
        max_length = max_length
    )
    logger.info("Script execution completed successfully.")

    # Step 4: Create the pivot view to organize and expose the computed embeddings
    logger.info(f"Creating pivot view in schema '{schema_name}' for table '{table_name}'.")
    res = execute_and_create_pivot_view(
        sto,
        schema_name,
        table_name,
        hash_columns=hash_columns,
        if_exists=if_exists
    )
    logger.info(f"Pivot view successfully created for table '{table_name}' in schema '{schema_name}'.")

    # Return the resulting pivot view as a DataFrame
    return res

def get_tdstone2_data_script_path():
    """
    Dynamically find the path of the 'tds_seq2seq.py' script in the tdstone2 package.
    This works for editable mode installations (pip install -e).
    """
    return os.path.join(tdstone2.tdstone.this_dir, "data", "tds_seq2seq.py")


def run_tds_seq2seq_script_locally(df, zip_file_path, text_column, accumulate_columns,
                                    min_length = 10,
                                    repetition_penalty = 2,
                                    num_beams = 4,
                                    num_return_sequences = 1,
                                    length_penalty = 0,
                                    prompt = 'summarize:',
                                    model_type = 't5',
                                    max_length = 100):
    """
    Runs the 'tds_seq2seq.py' script in the data module of the 'tdstone2' package
    by passing a dataframe via stdin and the required arguments.

    Args:
        df (pd.DataFrame): The dataframe to process.
        zip_file_path (str): The path to the zip file.
        text_column (int): The index of the text column in the dataframe.
        accumulate_columns (list): The list of column indexes to accumulate and print.

    Returns:
        pd.DataFrame: The resulting output from stdout as a pandas DataFrame.
    """
    logger.info("Starting the seq2seq script.")

    # Convert the dataframe to the expected input format (tab-delimited)
    input_data = df.apply(lambda row: '\t'.join(map(str, row.values)), axis=1).str.cat(sep='\n')
    logger.info("Dataframe converted to tab-delimited format.")

    # Get column positions
    text_column_, _, accumulate_columns_ = get_column_positions(df, accumulate=accumulate_columns, hash_columns=[],
                                                                text_column=text_column)
    logger.info(f"Text column: {text_column_}, Accumulate columns: {accumulate_columns_}")

    # Prepare the arguments to pass to the script
    script_path = get_tdstone2_data_script_path()  # Replace this with how you get the path in your environment

    # Check if the script path exists
    if not os.path.exists(script_path):
        logger.error(f"Script file not found: {script_path}")
        return None

    # Prepare the command-line arguments
    args = [sys.executable, script_path, zip_file_path, str(text_column_), str(accumulate_columns_),
            str(min_length), str(repetition_penalty), str(num_beams), str(num_return_sequences),
            str(length_penalty), str(max_length), str(model_type), prompt]
    logger.info(f"Running script with arguments: {args}")

    # Run the script with the dataframe input piped to stdin
    try:
        result = subprocess.run(
            args,
            input=input_data,  # Pass the dataframe as stdin input
            text=True,  # Treat input and output as text (string)
            capture_output=True,  # Capture the stdout and stderr
            check=True  # Raise an error if the subprocess fails
        )
        logger.info("Script executed successfully.")

        # Parse the stdout into a pandas DataFrame
        output = result.stdout.strip()  # Remove any extra whitespace around the output
        if output:  # Ensure there is output to process
            logger.info("Processing script output into DataFrame.")
            rows = [line.split('\t') for line in output.split('\n')]  # Split rows and columns based on tab delimiter
            logger.info(rows)
            cols = accumulate_columns + ['jobid','process_time','elapsed_time'] + ['Model', 'nb_tokens_input','nb_tokens_output', 'response']
            logger.info(f"columns : {cols}")
            df_output = pd.DataFrame(rows, columns=cols)



        else:
            logger.warning("No output from the script. Returning an empty DataFrame.")
            df_output = pd.DataFrame()  # Return an empty DataFrame if no output

        return df_output

    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running the script: {e.stderr}")
        return None
    

def GenerateChunks(table_name, id_column, text_column, delimiter='. ', sentence_per_chunk=2, mode='overlapping'):
    """
    This function generates chunks of text from a given table in a database. It splits the text into sentences,
    groups them into chunks based on the specified sentence count (`sentence_per_chunk`), and optionally allows for
    overlapping chunks. The function returns a dataframe containing the chunked text.

    :param table_name: Name of the table containing the text data.
    :param id_column: The column containing the unique document ID.
    :param text_column: The column containing the text data to be chunked.
    :param delimiter: The delimiter used to split the text into sentences (default is '. ').
    :param sentence_per_chunk: Number of sentences per chunk (default is 2).
    :param mode: Mode for chunking (either 'overlapping' or other options) (default is 'overlapping').
    :return: A dataframe containing the chunked text.
    """
    
    # Step 1: Generate atomic chunks by splitting text into sentences
    # The query splits the text into sentences using the delimiter and generates a list of sentence chunks
    query = f"""
    SELECT d.* 
    FROM TABLE (strtok_split_to_table({table_name}.{id_column},{table_name}.{text_column}, '{delimiter}')
    RETURNS (doc_id BIGINT, chunck_id integer, chunck varchar(2000) character set latin) ) as d
    """

    # Execute the query to generate atomic chunks of sentences
    atomic_chunks = tdml.DataFrame.from_query(query)
    
    # Step 2: Group sentences into chunks based on the specified sentence count
    if sentence_per_chunk == 1:
        # If only one sentence per chunk, return the atomic chunks directly
        return atomic_chunks
    else:
        # If multiple sentences per chunk, group sentences into chunks
        
        # NPath is used to group sentences by document and create chunks
        res = tdml.NPath(
             data1=atomic_chunks,                      # Input data containing sentence-level chunks
             data1_partition_column='doc_id',          # Partition the data by document ID
             data1_order_column='sentence_id',         # Order sentences by their sentence ID
             result=[
                 'FIRST(doc_id of ANY(sentence_)) AS doc_id',  # Get the document ID for each chunk
                 'FIRST(chunck_id of ANY(sentence_)) AS chunck_id',  # Get the chunk ID
                 "ACCUMULATE((chunck || '[SEP]') of ANY(sentence_)) AS chunck"  # Accumulate sentences into a chunk with separator '[SEP]'
             ],
             mode=mode,  # Specify the mode (e.g., overlapping or non-overlapping)
             pattern=f'sentence_{{{sentence_per_chunk}}}',  # Specify the sentence pattern (e.g., 2 sentences per chunk)
             symbols=["True AS sentence_"],  # Define the sentence symbols to be accumulated
         ).result
        
        # Step 3: Clean-up the generated chunk to replace separators and trim unwanted characters
        
        # Replace '[SEP]' with the defined delimiter
        res = res.assign(
            chunck=func.Regexp_Replace(
                res.chunck.expression, r"[\[]SEP[\]],", f"{delimiter}"  # Replace '[SEP],' with the delimiter
            )
        )
        
        # Remove trailing '[SEP]' from the chunk
        res = res.assign(
            chunck=func.Regexp_Replace(
                res.chunck.expression, r"[\[]SEP[\]]", f"{delimiter}"  # Replace the remaining '[SEP]' with the delimiter
            )
        )
        
        # Remove any leading or trailing delimiters from the chunk text
        res = res.assign(
            chunck=func.Regexp_Replace(
                res.chunck.expression, r"^.|.$", ""  # Trim leading and trailing periods
            )
        )
        
        # Step 4: Return the resulting dataframe containing the chunked sentences
        return res
