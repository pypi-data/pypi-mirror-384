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

def save_tokenizer_and_embeddings_model_onnx_batch_size(model_name: str, local_dir: str, model_task: None, device: str = "cpu",
                                             opset_version: int = 16):
    """
    Downloads and saves the tokenizer, exports the full transformer model using optimum-cli,
    and refines the exported ONNX model by fixing dynamic dimensions and removing unnecessary outputs.

    Args:
        model_name (str): The name of the pre-trained SentenceTransformer model to download.
        local_dir (str): The directory where the tokenizer and full transformer model will be saved.
        device (str): The device to move the model and inputs to ('cpu' or 'cuda').
        opset_version (int): The ONNX opset version to use for the export.
    """

    logger = logging.getLogger(__name__)

    # Ensure the local directory exists
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
        logger.info(f"Created directory: {local_dir}")

    # Step 1: Download and save the tokenizer locally
    logger.info(f"Downloading tokenizer for model: {model_name}")
    model = SentenceTransformer(model_name)
    tokenizer = model.tokenizer
    tokenizer.save_pretrained(local_dir)
    logger.info(f"Tokenizer saved in {local_dir}")

    # Step 2: Run the optimum-cli export command as a system command
    logger.info(f"Running optimum-cli export command for model: {model_name}")
    local_dir = local_dir.replace('\\', '/')
    if model_task is None:
        command = f"optimum-cli export onnx --opset {opset_version} --trust-remote-code -m {model_name} {local_dir} "
    else:
        command = f"optimum-cli export onnx --task {model_task} --opset {opset_version} --trust-remote-code -m {model_name} {local_dir} "
    logger.info(f"optimum-cli command: {command}")
    exit_code = os.system(command)

    # Check if the system command was successful
    if exit_code != 0:
        logger.error(f"Error: optimum-cli command failed with exit code {exit_code}")
        sys.exit(exit_code)

    logger.info(f"Model exported successfully to {local_dir}")

    # Step 3: Load the exported ONNX model
    onnx_model_path = os.path.join(local_dir, "model.onnx")
    model = onnx.load(onnx_model_path)

    # Step 4: Refine the ONNX model (fix dimensions, remove outputs)
    logger.info("Refining the ONNX model...")

    # Modify input dimension to allow variable batch size and keep sequence length fixed
    for input_tensor in model.graph.input:
        if input_tensor.name == "input_ids":  # Modify for input_ids, attention_mask, token_type_ids
            input_tensor.type.tensor_type.shape.dim[0].dim_param = "batch_size"  # Variable batch size
            input_tensor.type.tensor_type.shape.dim[1].dim_value = 512  # Fixed sequence length
        if input_tensor.name == "attention_mask":
            input_tensor.type.tensor_type.shape.dim[0].dim_param = "batch_size"
            input_tensor.type.tensor_type.shape.dim[1].dim_value = 512  # Fixed sequence length
        if input_tensor.name == "token_type_ids":
            input_tensor.type.tensor_type.shape.dim[0].dim_param = "batch_size"
            input_tensor.type.tensor_type.shape.dim[1].dim_value = 512  # Fixed sequence length

    # Infer shapes after modifying
    model = shape_inference.infer_shapes(model)

    # Step 5: Save the refined ONNX model
    refined_onnx_model_path = os.path.join(local_dir, "full_model.onnx")
    onnx.save(model, refined_onnx_model_path)

    logger.info(f"Refined ONNX model saved at {refined_onnx_model_path}")

    # Clean up
    os.remove(os.path.join(local_dir, "model.onnx"))
    logger.info(f"Suboptimal ONNX model {onnx_model_path} removed")

    return

def save_tokenizer_and_embeddings_model_onnx(model_name: str,  local_dir: str, model_task: None, device: str = "cpu",
                                             opset_version: int = 16, sequence_length: int = 512):
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

    # Step 1: Download and save the tokenizer locally
    logger.info(f"Downloading tokenizer for model: {model_name}")
    model = SentenceTransformer(model_name)

    tokenizer = model.tokenizer
    tokenizer.save_pretrained(local_dir)
    logger.info(f"Tokenizer saved in {local_dir}")

    # Extract embedding dimension
    embedding_dimension = model.get_sentence_embedding_dimension()
    logger.info(f"the embedding dimension of this model is: {embedding_dimension}")

    # Save the embedding dimension to a text file
    dimension_file_path = os.path.join(local_dir, "embedding_dimension.txt")
    with open(dimension_file_path, "w") as dimension_file:
        dimension_file.write(str(embedding_dimension))
    logger.info(f"Embedding dimension saved in {dimension_file_path}")

    # Step 2: Run the optimum-cli export command as a system command
    logger.info(f"Running optimum-cli export command for model: {model_name}")
    local_dir = local_dir.replace('\\', '/')
    if model_task is None:
        command = f"optimum-cli export onnx --opset {opset_version} --trust-remote-code -m {model_name} {local_dir}"
    else:
        command = f"optimum-cli export onnx --task {model_task} --opset {opset_version} --trust-remote-code -m {model_name} {local_dir}"
    logger.info(f"optimum-cli command: {command}")
    # Use os.system to execute the command
    exit_code = os.system(command)

    # Check if the system command was successful
    if exit_code != 0:
        logger.error(f"Error: optimum-cli command failed with exit code {exit_code}")
        sys.exit(exit_code)

    logger.info(f"Model exported successfully to {local_dir}")

    # Step 3: Load the exported ONNX model
    onnx_model_path = os.path.join(local_dir, "model.onnx")
    onnx_model_path_encoder = os.path.join(local_dir, "encoder_model.onnx")

    if os.path.exists(onnx_model_path_encoder):
        logger.info(f"encoder_model detected in  {onnx_model_path_encoder}")
        model = onnx.load(onnx_model_path_encoder)
    else:
        model = onnx.load(onnx_model_path)

    # Step 4: Refine the ONNX model (fix dimensions, remove outputs)
    logger.info("Refining the ONNX model...")

    # Set the opset version for the refined model
    op = onnx.OperatorSetIdProto()
    op.version = opset_version
    refined_model = onnx.helper.make_model(model.graph, ir_version=8, opset_imports=[op])

    # Step 5: Save the refined ONNX model
    refined_onnx_model_path_ = os.path.join(local_dir, f"full_model_onnxembeddings.onnx")
    onnx.save(refined_model, refined_onnx_model_path_)

    # Fix dynamic dimension sizes (batch_size, sequence_length)
    make_dim_param_fixed(refined_model.graph, "batch_size", 1)  # Fix batch size to 1
    if os.path.exists(onnx_model_path_encoder):
        make_dim_param_fixed(refined_model.graph, "encoder_sequence_length", sequence_length)  # Fix sequence length to 512
    else:    
        make_dim_param_fixed(refined_model.graph, "sequence_length", sequence_length)  # Fix sequence length to 512

    # Remove 'token_embeddings' output from the model graph
    for node in list(refined_model.graph.output):
        if node.name == "token_embeddings":
            refined_model.graph.output.remove(node)

    # Step 5: Save the refined ONNX model
    refined_onnx_model_path = os.path.join(local_dir, f"full_model.onnx")
    onnx.save(refined_model, refined_onnx_model_path)

    logger.info(f"Refined ONNX model saved at {refined_onnx_model_path}")

    for file_name in os.listdir(local_dir):
        if file_name.endswith(".onnx") and file_name != "full_model.onnx":
            file_path = os.path.join(local_dir, file_name)
            try:
                os.remove(file_path)
                logger.info(f"Removed suboptimal ONNX model: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")

    return



def zip_saved_files(model_name: str, local_dir: str, sequence_length: int = 512) -> str:
    """
    Zips the saved tokenizer and embeddings model using the specified model_name.
    The model_name will have '/' replaced with '_' to create a valid filename.
    The zip file will be placed in a dedicated 'models' folder to avoid issues with the source folder.

    Args:
        model_name (str): The name of the model whose files are being zipped.
        local_dir (str): The directory where the tokenizer and embeddings model files are located.

    Returns:
        str: The path to the created zip file in the 'models' directory.
    """
    # Replace '/' with '_' in the model name for valid file naming
    valid_model_name = model_name.replace("/", "_").replace(".", "_")

    # Create a dedicated models folder if it doesn't exist
    models_dir = os.path.join(".", "models")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        logger.info(f"Created models directory at {models_dir}")

    # Path for the zip file in the models folder
    zip_path = os.path.join(models_dir, f"tdstone2_emb_{sequence_length}_{valid_model_name}.zip")

    # Zip the contents of the local_dir and place the zip in the models folder
    logger.info(f"Zipping files in directory: {local_dir} to {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Add each file to the zip, maintaining the directory structure relative to local_dir
                zipf.write(file_path, os.path.relpath(file_path, local_dir))

    logger.info(f"Files have been zipped to {zip_path}")
    return zip_path


def get_tokenizer_and_embeddings_model_zip(model_name: str, local_dir: str, model_task: str = None, sequence_length: int = 512, generate_zip = True) -> str:
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
    logger.info(f"Saving tokenizer and embeddings model for: {model_name}")
    save_tokenizer_and_embeddings_model_onnx(model_name,  local_dir, model_task, sequence_length=sequence_length)

    if generate_zip:
        # Zip the saved files and return the zip file path
        zip_file_path = zip_saved_files(model_name, local_dir, sequence_length=sequence_length)

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
    file_name = os.path.basename(zip_file_path).replace(".zip", "").replace('-', '_')

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
    logger.info(f"Zip file {zip_file_path} has been installed in the {SEARCHUIFDBPATH} database.")


def load_embedding_dimension(local_dir: str) -> int:
    """
    Loads the embedding dimension from the vector_dimension.txt file.

    Args:
        local_dir (str): The directory where the vector_dimension.txt file is stored.

    Returns:
        int: The embedding dimension.
    """
    dimension_file_path = os.path.join(local_dir, "embedding_dimension.txt")

    # Check if the file exists
    if not os.path.exists(dimension_file_path):
        raise FileNotFoundError(f"The file {dimension_file_path} does not exist.")

    # Read the dimension from the file
    with open(dimension_file_path, "r") as dimension_file:
        dimension = int(dimension_file.read().strip())

    return dimension

def install_model_in_byom_catalog(
    model_id,
    model_file,
    tokenizer_file,
    model_embedding_catalog=None,
    tokenizer_catalog=None,
    schema_name=None,
    replace = False
):
    """
    Install a model and its tokenizer into the BYOM (Bring Your Own Model) catalog.

    This function saves a machine learning model and its corresponding tokenizer into specified BYOM catalog tables.
    If a model or tokenizer already exists in the catalog, it prompts the user to reload (overwrite) it.

    Parameters:
        model_id (str): Unique identifier for the model.
        model_file (str): Path to the model file to be saved.
        tokenizer_file (str): Path to the tokenizer file to be saved.
        model_embedding_catalog (str, optional): Catalog table name for storing the model. Defaults to 'embeddings_models'.
        tokenizer_catalog (str, optional): Catalog table name for storing the tokenizer. Defaults to 'embeddings_tokenizers'.
        schema_name (str, optional): Schema name where the catalog tables reside. If None, the current database schema is used.

    Raises:
        ValueError: If saving the model or tokenizer fails due to an unexpected error.
    """

    # Determine the catalogs
    if model_embedding_catalog is None:
        model_embedding_catalog = tdstone2.EMBEDDINGS_MODEL_CATALOG
    if tokenizer_catalog is None:
        tokenizer_catalog = tdstone2.EMBEDDINGS_TOKENIZER_CATALOG

    # Prepare lists for iteration
    model_ids = [model_id, model_id]  # One ID for the model, another for the tokenizer
    model_files = [model_file, tokenizer_file]  # Files for the model and tokenizer
    table_names = [model_embedding_catalog, tokenizer_catalog]  # Corresponding table names

    # Determine the schema name if not provided
    if schema_name is None:
        schema_name = _get_current_databasename()

    dimension = load_embedding_dimension(os.path.dirname(model_file))
    sequence_length = int(model_id.split('_')[2])

    # Iterate over model IDs, files, and table names to save them
    for model_id, model_file, table_name in zip(model_ids, model_files, table_names):
        try:
            logger.info(f"Install {model_id} : upload {model_file} in {schema_name}.{table_name}")
            tdml.save_byom(model_id=model_id, model_file=model_file, table_name=table_name, schema_name=schema_name, additional_columns={"Dimension": dimension, "sequence_length": sequence_length})
        except Exception as e:
            # Handle the case where the model or tokenizer already exists
            if 'TDML_2200' in str(e.args):  # Specific error code for existing entry
                if replace:
                    tdml.delete_byom(model_id=model_id, table_name=table_name)  # Delete existing entry
                    tdml.save_byom(model_id=model_id, model_file=model_file, table_name=table_name, schema_name=schema_name, additional_columns={"Dimension": dimension, "sequence_length": sequence_length})  # Save new entry
                else:
                    print("Skipping reload as per user choice.")
            else:
                # Raise a detailed error if the failure is not due to an existing entry
                raise ValueError(
                    f"Unable to save the {table_name.split('_')[1][:-1]} '{model_id}' in '{table_name}' due to the following error: {e}"
                )

def install_model_in_vantage_from_name_for_byom(
        model_name: str,
        local_dir: str = None,
        model_task: str = None,
        database: str = None,
        replace=False,
        sequence_length: int = 512,
        model_embedding_catalog: str = None,
        tokenizer_catalog: str = None
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

    Returns:
        None

    Raises:
        Exception: Propagates any exceptions raised during model file preparation or installation.
    """
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
    # Save the tokenizer and embeddings model in ONNX format
    logger.info(f"Saving tokenizer and embeddings model for: {model_name}")
    logger.info(f"embeddings model catalog : {model_embedding_catalog} in {database}")
    logger.info(f"tokenizer catalog : {tokenizer_catalog} in {database}")
    save_tokenizer_and_embeddings_model_onnx(model_name,  local_dir, model_task, sequence_length=sequence_length)

    # Step 2: Install the zip file into the specified database in Teradata Vantage
    try:
        install_model_in_byom_catalog(
            model_id                = f"tdstone2_emb_{sequence_length}_{valid_model_name}",
            model_file              = os.path.join(local_dir, "full_model.onnx"),
            tokenizer_file          = os.path.join(local_dir, "tokenizer.json"),
            model_embedding_catalog = model_embedding_catalog,
            tokenizer_catalog       = tokenizer_catalog,
            schema_name             = database,
            replace                 = replace
        )
    finally:
        # Restore the original database context to ensure no side effects
        if original_database:
            tdml.execute_sql(f'DATABASE "{original_database}";')
            logger.info(f"Database context has been reset to {original_database}.")
        else:
            logger.warning("No original database context was found to reset.")

    # Log success
    logger.info(f"Model {model_name} has been successfully installed in the {database} database.")

def install_model_in_vantage_from_name(
        model_name: str,
        local_dir: str = None,
        model_task: str = None,
        database: str = None,
        replace=False,
        sequence_length: int = 512,
        upload = True,
        generate_zip = True
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
    zip_file_path = get_tokenizer_and_embeddings_model_zip(
        model_name, local_dir, model_task, sequence_length=sequence_length, generate_zip=generate_zip
    )

    # Step 2: Install the zip file into the specified database in Teradata Vantage
    if upload:
        try:
            install_zip_in_vantage(zip_file_path, database, replace=replace)
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

def list_installed_files_byom(database: str = None,
                              model_embedding_catalog: str = None,
                              tokenizer_catalog: str = None):
    """
    Lists all installed files in the specified database that start with the specified prefix and end with the specified suffix.

    Args:
        database (str, optional): The database where the files are installed. If not provided, defaults to the current or temporary database.
        startswith (str, optional): The prefix for filtering filenames. Defaults to 'tdstone2_emb_'.
        endswith (str, optional): The suffix for filtering filenames. Defaults to '.zip'.

    Returns:
        DataFrame: A Teradata DataFrame containing the list of matching files in the specified database.
    """
    # Determine the catalogs
    if model_embedding_catalog is None:
        model_embedding_catalog = tdstone2.EMBEDDINGS_MODEL_CATALOG
    if tokenizer_catalog is None:
        tokenizer_catalog = tdstone2.EMBEDDINGS_TOKENIZER_CATALOG

    # Set default database if not provided
    if database is None:
        database = _get_current_databasename()
        logger.info(f"Using default database: {database}")
    else:
        logger.info(f"Using provided database: {database}")

    # Prepare the query to list installed files
    query = f"""
    SELECT DISTINCT
      '{database}' as DATABASE_LOCATION,
      A.model_id as tdstone2_models,
    CASE
        WHEN BYTES(A.model)  < 1024 THEN BYTES(A.model) || 'B'
        WHEN BYTES(A.model)  < 1048576 THEN (BYTES(A.model) / 1024.0) || 'K'
        WHEN BYTES(A.model)  < 1073741824 THEN (BYTES(A.model) / 1048576.0) || 'M'
        WHEN BYTES(A.model)  < 1099511627776 THEN (BYTES(A.model) / 1073741824.0) || 'G'
        ELSE (BYTES(A.model) / 1099511627776.0) || 'T'
    END AS file_size,
          A.dimension as vector_dimension,
          A.sequence_length 
    FROM {database}.{model_embedding_catalog} A
    INNER JOIN {database}.{tokenizer_catalog} B
    ON A.model_id = B.model_id
    """

    logger.info(
        f"Executing query to list installed embeddings models in {model_embedding_catalog} and {tokenizer_catalog} in database {database}")

    # Execute the query and return the result as a DataFrame
    #result = pd.read_sql(query, con=tdml.get_context())
    result = pd.DataFrame(tdml.execute_sql(query).fetchall(), columns = ['DATABASE_LOCATION','tdstone2_models','file_size','embedding_dimension','sequence_length'])
    logger.info(f"Query executed successfully, returning result")

    return result

def list_installed_files(database: str = None, startswith: str = 'tdstone2_emb_', endswith: str = '.zip', SEARCHUIFDBPATH : str = None):
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
    result['file_id'] = result['tdstone2_models'].str.replace(".zip", "", regex=False).str.replace("-", "_", regex=False)


    return result


def setup_and_execute_script(model: str, dataset, text_column, hash_columns: list, accumulate_columns=[],
                             delimiter: str = '\t', database: str = None, SEARCHUIFDBPATH: str = None):
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
        command = f"""unzip {SEARCHUIFDBPATH}/{model} -d $PWD/{model_folder}/ > /dev/null && tdpython3 ./{SEARCHUIFDBPATH}/tds_vector_embedding.py {model_folder} {text_column_position} [{'-'.join([str(a) for a in accumulate_positions])}] {delimiter}"""
        logger.info(f"bash command : {command}")
        # Create the tdml.Script object
        sto = tdml.Script(
            data=dataset,
            script_name='tds_vector_embedding.py',
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
                    ("Vector_Dimension", tdml.INTEGER()),
                    ("Model", tdml.VARCHAR(length=1024, charset='latin')),
                    ("nb_tokens", tdml.INTEGER()),
                    ("Vector", tdml.VARCHAR(length=32000, charset='latin')),
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
 
        types['Vector'] = tdml.JSON()
        
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
                types         = {'Vector' : tdml.JSON(), 'run_id':tdml.VARCHAR(length=36, charset='LATIN')}
            )
        else:
            df_sto.to_sql(
                schema_name   = schema_name,
                table_name    = 'T_' + table_name,
                if_exists     = if_exists,
                primary_index = hash_columns,
                types         = {'Vector' : tdml.JSON(), 'run_id':tdml.VARCHAR(length=36, charset='LATIN')}
            )
    except Exception as e:
        tac = time.time()
        logger.info(f"Data stored in T_{table_name}. Storage time: {tac - tic:.2f} seconds")
        raise

    tac = time.time()
    logger.info(f"Data stored in T_{table_name}. Storage time: {tac - tic:.2f} seconds")

    # Compute vector_dimension from the stored table
    vector_dimension_query = f"SEL max(Vector_Dimension) FROM {schema_name}.T_{table_name}"
    vector_dimension = tdml.execute_sql(vector_dimension_query).fetchall()[0][0]
    logger.info(f"Computed vector dimension: {vector_dimension}")

    # Generate the pivot columns for the view using the computed vector_dimension
    columns = '\n,'.join(df_sto.columns[0:-1]+[f"CAST(Vector.V{i} AS FLOAT) AS V{i}" for i in range(vector_dimension)])

    # Create a Expanded view
    query = f"""
    REPLACE VIEW {schema_name}.{table_name} AS
    LOCK ROW FOR ACCESS
    SELECT 
    {columns} 
    FROM {schema_name}.T_{table_name}
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


def compute_vector_embedding(model, dataset, schema_name, table_name, text_column, hash_columns, accumulate_columns=[],
                             SEARCHUIFDBPATH=None, if_exists='replace'):
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
        SEARCHUIFDBPATH=SEARCHUIFDBPATH
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

def get_model_dimension(model_id: str, database: str = None, model_embedding_catalog: str = None) -> int:
    """
    Retrieves the dimension of the embeddings for a specified model from the catalog.

    Args:
        model_id (str): The identifier for the model whose embedding dimension is to be retrieved.
        database (str, optional): The name of the database to query. If not provided, the default
                                  database is determined using `_get_current_databasename`.
        model_embedding_catalog (str, optional): The name of the catalog containing model information.
                                                 If not provided, it defaults to `tdstone2.EMBEDDINGS_MODEL_CATALOG`.

    Returns:
        int: The dimension of the embeddings for the specified model.

    Raises:
        ValueError: If the query returns no results or an unexpected format.

    Example:
        dimension = get_model_dimension(model_id="my_model", database="my_database")
        print(f"Embedding dimension: {dimension}")
    """
    # Set default database if not provided
    if database is None:
        database = _get_current_databasename()  # Fallback to default database
        logger.info(f"Using default database: {database}")
    else:
        logger.info(f"Using provided database: {database}")

    # Determine the catalog to query
    if model_embedding_catalog is None:
        model_embedding_catalog = tdstone2.EMBEDDINGS_MODEL_CATALOG

    # Construct the SQL query to fetch the embedding dimension
    query = f"SELECT dimension FROM {database}.{model_embedding_catalog} WHERE model_id = '{model_id}'"

    # Execute the SQL query and fetch results
    try:
        result = tdml.execute_sql(query).fetchall()
        if not result:
            raise ValueError(f"No dimension found for model_id '{model_id}' in catalog '{model_embedding_catalog}'.")
        return int(result[0][0])  # Extract and return the first result as an integer
    except Exception as e:
        logger.error(f"Error fetching model dimension: {e}")
        raise

def compute_vector_embedding_byom(model, dataset, schema_name, table_name, text_column, primary_index = None, accumulate_columns=[],
                             database=None, if_exists='replace',  model_embedding_catalog: str = None,
                              tokenizer_catalog: str = None, mldb_function = 'BYOM', caching = 'inquery', overwritecachedmodel = 'false'):
    """
    Computes vector embeddings for a specified text column using a given model and stores
    the results in a database table. It supports both BYOM (Bring Your Own Model) and iVSM scoring.

    Args:
        model (str): Name of the model to use for embedding computation.
        dataset: A Teradata DataFrame containing the input data to process.
        schema_name (str): Name of the schema where the result table and view will be created.
        table_name (str): Name of the table to store computed embeddings.
        text_column (str): Column in the dataset containing the text for embeddings.
        primary_index (list, optional): List of columns to use as the primary index. Defaults to None.
        accumulate_columns (list, optional): Additional columns to include in the results. Defaults to [].
        database (str, optional): Name of the database to use. Defaults to the current database.
        if_exists (str, optional): Policy for handling table creation if it already exists. Options:
                                   ['replace', 'append']. Defaults to 'replace'.
        model_embedding_catalog (str, optional): Name of the model embedding catalog. Defaults to None.
        tokenizer_catalog (str, optional): Name of the tokenizer catalog. Defaults to None.
        mldb_function (str, optional): Scoring function to use. Options: ['BYOM', 'iVSM']. Defaults to 'BYOM'.
        caching (str, optional): Caching strategy. Options: ['inquery', 'interquery']. Defaults to 'inquery'.
        overwritecachedmodel (str, optional): Whether to overwrite cached models.
                                              Options: ['true', 'false', ...]. Defaults to 'false'.

    Returns:
        tdml.DataFrame: A DataFrame representing the created pivot view with computed embeddings.

    Raises:
        ValueError:
            - If `text_column` is not found or is not of type VARCHAR or CLOB.
            - If the specified `model` is not found in the installed models.
            - If invalid values are provided for `mldb_function`, `caching`, or `if_exists`.

    """
    # Input validation
    if mldb_function not in ['BYOM', 'iVSM']:
        raise ValueError(f"Invalid value for `mldb_function`: {mldb_function}. Must be 'BYOM' or 'iVSM'.")

    if caching not in ['inquery', 'interquery']:
        raise ValueError(f"Invalid value for `caching`: {caching}. Must be 'inquery' or 'interquery'.")

    if if_exists not in ['replace', 'append']:
        raise ValueError(f"Invalid value for `if_exists`: {if_exists}. Must be 'replace' or 'append'.")

    overwritecachedmodel = overwritecachedmodel.lower() in {'*', 'true', 't', 'yes', 'y', '1'}

    # Set default database if not provided
    if database is None:
        database = _get_current_databasename()
        logger.info(f"Using default database: {database}")
    else:
        logger.info(f"Using provided database: {database}")

    # Determine the catalogs
    if model_embedding_catalog is None:
        model_embedding_catalog = tdstone2.EMBEDDINGS_MODEL_CATALOG
    if tokenizer_catalog is None:
        tokenizer_catalog = tdstone2.EMBEDDINGS_TOKENIZER_CATALOG

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
    installed_models_df = list_installed_files_byom(
        database                = database,
        model_embedding_catalog = model_embedding_catalog,
        tokenizer_catalog       = tokenizer_catalog
    )

    if not any(installed_models_df['tdstone2_models'].str.contains(model)):
        logger.error(f"Model '{model}' not found in the installed models.")
        raise ValueError(f"Model '{model}' not found in installed models.")
    logger.info(f"Model '{model}' successfully verified as installed.")

    embedding_dimension = get_model_dimension(model_id=model)
    logger.info(f"Model dimension is '{embedding_dimension}'")

    # Step 4: Set up and execute the embedding computation script
    columns = primary_index + [c for c in accumulate_columns if c not in primary_index]
    dataset._DataFrame__execute_node_and_set_table_name(dataset._nodeid, dataset._metaexpr)
    logger.info("Setting up and executing the script for embedding computation.")

    if mldb_function == 'BYOM':
        logger.info(f"ONNXEmbeddings computations start with OverwriteCachedModel set to '{overwritecachedmodel}'")
        tic = time.time()
        query = f"""
            select 
                *
        from mldb.ONNXEmbeddings(
                --on {dataset._table_name} as InputTable
                on (select {','.join([c for c in columns])}, {text_column} as txt from {dataset._table_name})
                on (select * from {database}.{model_embedding_catalog} where model_id = '{model}') as ModelTable DIMENSION
                on (select model as tokenizer from {database}.{tokenizer_catalog} where model_id = '{model}') as TokenizerTable DIMENSION
           
                using
                    Accumulate({','.join(["'"+c+"'" for c in columns])}) 
                    ModelOutputTensor('sentence_embedding')
                    EnableMemoryCheck('false')
                    OutputFormat('FLOAT32({embedding_dimension})')
                    OverwriteCachedModel('{overwritecachedmodel}')
            ) a 
        """
    elif mldb_function == 'iVSM':
        logger.info(f"iVSM computations start with Caching set to '{caching}'")
        tic = time.time()
        query_view = f"""
        select
            {','.join(columns)},
            txt,
            IDS as input_ids,
            attention_mask
        from ivsm.tokenizer_encode(
            on (select {','.join([c for c in columns])}, {text_column} as txt from {dataset._table_name})
            on (select model as tokenizer from {database}.{tokenizer_catalog} where model_id = '{model}') DIMENSION
            USING
                ColumnsToPreserve({','.join(["'"+c+"'" for c in columns+['txt']])})
                OutputFields('IDS', 'ATTENTION_MASK')
                MaxLength(1024)
                PadToMaxLength('True')
                TokenDataType('INT64')
        ) a
        """

        query = f"""
            select 
            *
            from ivsm.IVSM_score(
                on ({query_view})  -- table with data to be scored
                on (select model_id, model from {database}.{model_embedding_catalog} where model_id = '{model}') dimension
                using
                    ColumnsToPreserve({','.join(["'"+c+"'" for c in columns])}) -- columns to be copied from input table
                    ModelType('ONNX') -- model format
                    BinaryInputFields('input_ids', 'attention_mask') -- enables binary input vectors
                    BinaryOutputFields('sentence_embedding')
                    Caching('{caching}') -- tun on model caching within the query
                ) a 
        """

        tdml.DataFrame.from_query(query).to_sql(table_name='volatile_'+table_name, primary_index = primary_index, if_exists = if_exists, temporary= True)
        tac2 = time.time()
        logger.info(f"iVSM computation : vector embedding computation  time: {tac2 - tic:.2f} seconds")

        query = f"""
        select
                *
        from ivsm.vector_to_columns(
                on {_get_database_username()}.volatile_{table_name}
                using
                    ColumnsToPreserve({','.join(["'"+c+"'" for c in columns])})
                    VectorDataType('FLOAT32')
                    VectorLength({embedding_dimension})
                    OutputColumnPrefix('V')
                    InputColumnName('sentence_embedding')
            ) a
        """
        tac2 = time.time()
        logger.info("Convert vectors to columns.")


    tdml.DataFrame.from_query(query).to_sql(schema_name=schema_name, table_name=table_name, primary_index = primary_index, if_exists = if_exists)
    tac = time.time()
    if mldb_function == 'iVSM':
        logger.info(f"iVSM computation : vector to column conversion: {tac - tac2:.2f} seconds")
    logger.info(f"Execution completed successfully in {tac - tic:.2f} seconds in total.")

    # Return the resulting pivot view as a DataFrame
    return tdml.DataFrame(tdml.in_schema(schema_name, table_name))


def get_tdstone2_data_script_path():
    """
    Dynamically find the path of the 'tds_vector_embedding.py' script in the tdstone2 package.
    This works for editable mode installations (pip install -e).
    """
    return os.path.join(tdstone2.tdstone.this_dir, "data", "tds_vector_embedding.py")


def run_tds_vector_embedding_script_locally(df, zip_file_path, text_column, accumulate_columns):
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
    args = [sys.executable, script_path, zip_file_path, str(text_column_), str(accumulate_columns_)]
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
            logger.info(rows[0])
            df_output = pd.DataFrame(rows,
                                     columns=accumulate_columns + ['jobid','process_time','elapsed_time'] + ['Vector_Dimension', 'Model', 'nb_tokens' 'Vector'])

            # Normalize the JSON column
            df_output['Vector'] = df_output['Vector'].apply(json.loads)
            expanded_columns = pd.json_normalize(df_output['Vector'])

            # Merge the expanded columns with the original DataFrame
            df_output = pd.concat([df_output.drop(columns=['Vector']), expanded_columns], axis=1)

            # # Pivot the DataFrame to get the embeddings in a proper structure
            # df_output = df_output.pivot(columns='Vector_Dimension', values='V',
            #                             index=accumulate_columns + ['jobid','process_time','elapsed_time'] + [text_column] + ['model'])[
            #     [str(i) for i in range(df_output['Vector_Dimension'].astype(int).max()+1)]]
        else:
            logger.warning("No output from the script. Returning an empty DataFrame.")
            df_output = pd.DataFrame()  # Return an empty DataFrame if no output

        return df_output

    except subprocess.CalledProcessError as e:
        logger.error(f"Error while running the script: {e.stderr}")
        return None
    
def modify_onnx_model(source_file: str, output_file: str, batch_size: int = 1, max_sequence_length: int = 512):
    """
    Modify the ONNX model by fixing dynamic dimensions, and removing unwanted outputs.

    Args:
        source_file (str): Path to the source ONNX file.
        output_file (str): Path to save the modified ONNX file.
        batch_size (int, optional): Fixed batch size to set. Default is 1.
        max_sequence_length (int, optional): Fixed sequence length to set. Default is 512.
    """
    # Load the ONNX model
    model = onnx.load(source_file)

    # Fix dynamic dimension sizes (batch_size, sequence_length)
    make_dim_param_fixed(model.graph, "batch_size", batch_size)  # Fix batch size
    make_dim_param_fixed(model.graph, "sequence_length", max_sequence_length)  # Fix sequence length

    # Remove 'token_embeddings' output from the model graph
    for node in list(model.graph.output):
        if node.name == "token_embeddings":
            model.graph.output.remove(node)

    # Save the modified model without quantization
    onnx.save(model, output_file)
    logger.info(f"Modified ONNX model saved to: {output_file}")


def customize_existing_model(src_dir, dest_dir, exclude_onnx=True, model_name=None, tokenizer_file=None, onnx_file=None, batch_size: int = 1, max_sequence_length: int = 512, generate_zip=True):
    """
    Customizes an existing model by copying files from the source directory to the destination directory.
    Optionally excludes .onnx files from the copy and allows the addition of specific tokenizer and ONNX files.
    
    :param src_dir: Source directory to copy from.
    :param dest_dir: Destination directory to copy to.
    :param exclude_onnx: If True, excludes .onnx files from being copied.
    :param model_name: Optional model name to be used when generating the zip.
    :param tokenizer_file: Optional tokenizer file to be copied to the destination.
    :param onnx_file: Optional ONNX file to be copied to the destination.
    :param batch_size: Batch size to be passed to the `modify_onnx_model` function.
    :param max_sequence_length: Maximum sequence length to be passed to the `modify_onnx_model` function.
    :param generate_zip: If True, a ZIP of the directory will be generated.
    """
    
    # Ensure source directory exists
    if not os.path.exists(src_dir) or not os.path.isdir(src_dir):
        logger.error(f"Source directory '{src_dir}' does not exist or is not a directory.")
        return

    # Ensure destination directory exists, create if not
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        logger.info(f"Destination directory '{dest_dir}' created.")
    
    # Walk through the source directory and copy each file/folder
    if not src_dir == dest_dir:
        for root, dirs, files in os.walk(src_dir):
            # Determine the relative path of the current folder
            rel_path = os.path.relpath(root, src_dir)
            # Define the destination folder path
            dest_folder = os.path.join(dest_dir, rel_path)
            
            # Create the folder in the destination if it doesn't exist
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            
            # Copy files to the destination
            for file in files:
                # If exclude_onnx is True and file is .onnx, skip it
                if exclude_onnx and file.lower().endswith('.onnx'):
                    logger.info(f"Skipping '{file}' as it is an ONNX file.")
                    continue
                
                # Define the full paths for the file copy
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_folder, file)
                
                # Copy the file
                shutil.copy2(src_file, dest_file)
                logger.info(f"Copied: '{src_file}' to '{dest_file}'")

    # Copy additional optional files if specified
    if tokenizer_file and os.path.exists(tokenizer_file):
        tokenizer_dest = os.path.join(dest_dir, os.path.basename(tokenizer_file))
        shutil.copy2(tokenizer_file, tokenizer_dest)
        logger.info(f"Copied tokenizer file: '{tokenizer_file}' to '{tokenizer_dest}'")

    if onnx_file and os.path.exists(onnx_file):
        onnx_dest = os.path.join(dest_dir, os.path.basename('full_model.onnx'))
        # Modify the ONNX model
        modify_onnx_model(onnx_file, onnx_dest, batch_size, max_sequence_length)
        logger.info(f"Copied and modified ONNX file: '{onnx_file}' to '{onnx_dest}'")

    # Generate a zip file of the directory if requested
    if generate_zip:
        if model_name is None:
            model_name = os.path.basename(dest_dir.rstrip(os.sep))  # Use destination folder's name if model name is not provided
        zip_saved_files(model_name=model_name, local_dir=dest_dir.rstrip(os.sep), sequence_length=512)
        logger.info(f"Generated zip file for the model: '{model_name}'")

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
