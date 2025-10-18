import sys
import numpy as np
import pandas as pd
import json
import base64
import pickle

import warnings
warnings.filterwarnings('ignore')

# from io import StringIO
# from contextlib import redirect_stdout, redirect_stderr
# Create StringIO objects to capture the process output
# output_capture = StringIO()

from skl2onnx.common.data_types import FloatTensorType, StringTensorType, Int64TensorType
from skl2onnx import convert_sklearn, to_onnx


def convert_dataframe_schema(df, drop=None):
    inputs = []
    for k, v in zip(df.columns, df.dtypes):
        if drop is not None and k in drop:
            continue
        if v == 'int64':
            t = Int64TensorType([None, 1])
        elif v == 'float64':
            t = FloatTensorType([None, 1])
        else:
            t = StringTensorType([None, 1])
        inputs.append((k, t))
    return inputs


def encode_base64M(data: bytes):
    # Standard base64 encoding
    base64_encoded = base64.b16encode(data)
    # Convert to string and replace characters for Base64M
    base64M_encoded = base64_encoded.decode('utf-8') #.replace('+', '-').replace('/', '_')
    return base64M_encoded




def convert2onnx_mymodel_object(model, dataset, arguments):
    # initial_inputs = convert_dataframe_schema(dataset[arguments['model_parameters']['column_names_X']])
    # initial_type = guess_initial_types(dataset[arguments['model_parameters']['column_names_X']],None)
    #initial_type = [
    #    ('float_input', FloatTensorType([None, dataset[arguments['model_parameters']['column_names_X']].shape[1]]))]
    #onx = convert_sklearn(model.model, initial_types=initial_type)

    initial_type = []
    for feature in arguments['model_parameters']['column_names_X']:
        if feature in arguments['model_parameters']['column_categorical']:
            try:
                # Attempt to convert the feature to integer
                dataset[feature].astype(int)
                initial_type.append((feature, Int64TensorType([None, 1])))
            except ValueError:
                initial_type.append((feature, StringTensorType([None, 1])))
        else:
            if pd.api.types.is_integer_dtype(dataset[feature]):
                initial_type.append((feature, Int64TensorType([None, 1])))
            elif pd.api.types.is_float_dtype(dataset[feature]):
                initial_type.append((feature, FloatTensorType([None, 1])))
            else:
                initial_type.append((feature, StringTensorType([None, 1])))


    # Convert the pipeline to ONNX
    onnx_model = convert_sklearn(
        model.model,
        initial_types=initial_type,
        target_opset=12
    )
    return encode_base64M(onnx_model.SerializeToString())


def list_module_version():
    res = []
    for module in list(sys.modules.keys()):  # Convert keys to list before iteration
        try:
            if not 'built-in' in str(module):
                res.append(module + '==' + sys.modules[module].__version__)
        except:
            pass

    return res


# RETURNS('IDstr VARCHAR(255) CHARACTER SET UNICODE, ID_Model INTEGER, ID_Partition VARCHAR(2000) CHARACTER SET UNICODE, Model_Type VARCHAR(255) CHARACTER SET UNICODE, JSON_RESULTS VARCHAR(2000), Part_no INTEGER, BINARY_RESULTS BLOB')

STO_OUTPUT_DEFAULT_STO_PARTITION_ID = -1
STR_OUTPUT_DEFAULT_STO_MODEL_ID = -1
STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID = 'STO error'
STO_OUTPUT_DEFAULT_TRAINED_MODEL = 'STO error'
STO_OUTPUT_DEFAULT_MODEL_TYPE = 'None'
STO_OUTPUT_DEFAULT_STATUS = '{"error": "failed"}'
STO_OUTPUT_DEFAULT_EXECUTION_TIME = '9999-01-01 00:00:00.000000-04:00'

nb_partitions = None

DELIMITER = '\t'
OUTPUT_DELIMITER = DELIMITER


def print_outputs():
    if nb_partitions is None:
        for i in range(10):
            list_2_print = [str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID)] * (i + 1)
            list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
            print(DELIMITER.join(list_2_print))
    elif type(STO_OUTPUT_DEFAULT_STO_PARTITION_ID) == list and len(
            STO_OUTPUT_DEFAULT_STO_PARTITION_ID) == nb_partitions:
        list_2_print = [str(x) for x in STO_OUTPUT_DEFAULT_STO_PARTITION_ID]
        list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))
    else:
        list_2_print = [str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID)] * nb_partitions
        list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))


def print_outputs2():
    print(
        str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID) + OUTPUT_DELIMITER +
        str(STR_OUTPUT_DEFAULT_STO_MODEL_ID) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_MODEL_TYPE) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_STATUS) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_TRAINED_MODEL) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_EXECUTION_TIME)
    )


def print_when_exception():
    print_outputs()
    sys.exit()

# Know your data: You must know in advance the number and data types of the
# incoming columns from the Teradata database!
# For this script, the input expected format is:
beg_cols = []

end_cols = [
    'sto_fake_row',
    'sto_model_id',
    'sto_row_id',
    'sto_partition_id',
    'sto_fold_id',
    'sto_code_type',
    'sto_code',
    'arguments',
    'execution_time'
]

def reconstruct_pandas_dataframe(beg_cols, end_cols):
    """
    Reads standard input line by line to construct a pandas DataFrame with
    appropriate data types specified for each column.

    Returns:
        df (DataFrame): A DataFrame with data read from standard input,
                        with columns typed as float, int, and category as appropriate.
    """
    data_Tbl = []
    while True:
        try:
            line = input()
            if line == '':
                break
            data_Tbl.append([x for x in line.split(DELIMITER)])
        except EOFError:
            break

    if not data_Tbl:
        sys.exit("The input DataFrame is empty. Exiting the script.")

    num_columns = len(data_Tbl[0])

    # Generate column names
    dummy_cols = [f"dummy_col_{i}" for i in range(num_columns - len(beg_cols) - len(end_cols))]
    column_names = beg_cols + dummy_cols + end_cols

    # Ensure no duplicate column names
    if len(set(column_names)) != len(column_names):
        sys.exit("Error: Duplicate column names generated. Check beg_cols and end_cols.")

    df = pd.DataFrame(data_Tbl, columns=column_names)

    return df, dummy_cols

# Helper functions
def update_status(message):
    global STO_OUTPUT_DEFAULT_STATUS
    STO_OUTPUT_DEFAULT_STATUS = message
    print_when_exception()

def parse_execution_time(df):
    try:
        return df['execution_time'].values[0]
    except:
        update_status('{"error": "failed", "info":"fails to read execution_time"}')
        return None

def parse_arguments(df):
    try:
        return json.loads(df['arguments'].values[0])
    except:
        update_status('{"error": "failed", "info":"arguments JSON may not be well formed"}')
        return None

def extract_param(params, key, error_message):
    try:
        return params[key]
    except:
        update_status(f'{{"error": "failed", "info":"{error_message}"}}')
        return None

def split_column_values(value, column_name):
    try:
        return value.split(',')
    except Exception as e:
        update_status(f'{{"error": "failed", "info": "problem to split {column_name}. {e}"}}')
        return None

def process_partition_id(df, partition_id):
    try:
        partition_list = partition_id.split(',')
        return partition_list, df[partition_list].values[0].tolist()
    except Exception as e:
        update_status(f'{{"error": "failed", "info": "problem to split sto_partition_id. {e}"}}')
        return None, None
    
def construct_dataframe(df, Params_STO, dummy_cols):
    global STO_OUTPUT_DEFAULT_STATUS

    # Construct DataFrame with specified column names
    try:
        df = df[dummy_cols]
        df.columns = Params_STO["columnnames"]
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem constructing the dataframe with columnnames. {e}"}}'
        print_when_exception()
        return None

    # Cast columns to specified types
    column_type_mapping = {
        "float_columnames": pd.to_numeric,
        "integer_columnames": lambda col: col.astype("int"),
        "category_columns": lambda col: col.astype("category"),
        "datetime_columns": pd.to_datetime
    }

    for col_type, cast_func in column_type_mapping.items():
        if col_type in Params_STO:
            for c in Params_STO[col_type]:
                if len(c) > 0:
                    try:
                        # Replace spaces with empty strings before applying the type conversion
                        df[c] = df[c].str.replace(" ", "").astype(str)  # Ensure string type for replace
                        df[c] = cast_func(df[c])
                    except:
                        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "column {c} cannot be converted to {col_type.split("_")[0]} Python"}}'
                        print_when_exception()

    # Drop rows with all NaN values
    df = df.dropna(how="all")

    # Check if enough data remains
    if df.shape[0] < 30:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "not enough data left after the dropna. Only {df.shape[0]} rows."}}'
        print_when_exception()
        return None

    return df

df, dummy_cols = reconstruct_pandas_dataframe(beg_cols, end_cols)

# Extract values
sto_fake_row     = df['sto_fake_row'].values[0]
sto_model_id     = df['sto_model_id'].values[0]
sto_row_id       = df['sto_row_id'].values[0]
sto_partition_id = df['sto_partition_id'].values[0]
sto_fold_id      = df['sto_fold_id'].values[0]
sto_code_type    = df['sto_code_type'].values[0]
sto_code         = df['sto_code'].values[0]
arguments        = df['arguments'].values[0]
execution_time   = parse_execution_time(df)

# Update status and model ID
STO_OUTPUT_DEFAULT_STATUS = f"{sto_partition_id} {sto_row_id} {sto_fold_id}"
STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id

# Rebuild parameters
Params = parse_arguments(df)
if Params is None:
    print_outputs()
    sys.exit()

Params_STO       = extract_param(Params, 'sto_parameters', 'there is no field sto_parameters in arguments')
Params_Model     = extract_param(Params, 'model_parameters', 'there is no field model_parameters in arguments')

# Split column values
sto_row_id       = split_column_values(sto_row_id, 'sto_row_id')
sto_fold_id      = split_column_values(sto_fold_id, 'sto_fold_id')

# Set the proper data types:
df = construct_dataframe(df, Params_STO, dummy_cols)
sto_partition_id, STO_OUTPUT_DEFAULT_STO_PARTITION_ID = process_partition_id(df, sto_partition_id)
nb_partitions = len(sto_partition_id)

# rebuild the code
try:
    Code = base64.b64decode(sto_code).decode()
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code rebuild the code. Please test it locally first. {e}"}}'
    print_when_exception()

try:
    list1 = list_module_version()
    exec(Code)
    list2 = list_module_version()
    imported_packages = list(set(list2).difference(set(list1)))
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code cannot be executed. Please test it locally first. {e} {Code[0:100]}"}}'
    print_when_exception()

STO_OUTPUT_DEFAULT_STATUS = sto_code_type

if sto_code_type == 'python class':

    # Instantiate the model
    try:
        model = MyModel(**Params_Model)
    except:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model cannot be instanciated. Check whether the model parameters are correct and consistent."}}'
        print_when_exception()

    # Run the fit method on the data
    try:
        model.fit(df)
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model run failed. {e}"}}'
        print_when_exception()
else:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "unknown model type: {sto_code_type}."}}'
    print_when_exception()    

try:
    model_type = model.get_model_type()
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "issue with get_model_type. {e}"}}'
    print_when_exception()

try:
    model_metadata = model.get_description()
except Exception as e:
    model_metadata = '{}'
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "issue with get_description. {e}"}}'
    print_when_exception()

import uuid

unique_id = str(uuid.uuid4())
STO_OUTPUT_DEFAULT_STATUS = 'after python class'

if 'pickle' in Params_STO['output_format']:
    STO_OUTPUT_DEFAULT_MODEL_TYPE = 'pickle'
    try:
        metadata = {}
        metadata["error"] = "successful"
        metadata["model_type"] = model_type
        metadata.update(json.loads(model_metadata))
        metadata['packages'] = imported_packages
        metadata['python_version'] = str(sys.version)

        modelSer = pickle.dumps(model)
        modelSerB64 = base64.b64encode(modelSer)

        STO_OUTPUT_DEFAULT_STO_PARTITION_ID = df[sto_partition_id].values[0].tolist()
        STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
        STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID = unique_id
        STO_OUTPUT_DEFAULT_TRAINED_MODEL = modelSerB64
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'pickle'
        STO_OUTPUT_DEFAULT_STATUS = str(json.dumps(metadata)).replace("'", '"')
        print_outputs()
    except Exception as e:
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'pickle'
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the pickle outputs failed {e}"}}'
        print_when_exception()

if 'onnx' in Params_STO['output_format']:
    STO_OUTPUT_DEFAULT_MODEL_TYPE = 'onnx'
    try:
        # model conversion
        onx = convert2onnx_mymodel_object(model, df, Params)
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "model conversion to ONNX failed {e}"}}'
        print_when_exception()

    try:
        metadata = {}
        metadata["error"] = "successful"
        metadata["model_type"] = model_type
        metadata.update(json.loads(model_metadata))
        metadata['packages'] = imported_packages
        metadata['python_version'] = str(sys.version)
        metadata['features'] = Params_Model['column_names_X']
        metadata['target'] = Params_Model['target']

        import uuid

        STO_OUTPUT_DEFAULT_STO_PARTITION_ID = df[sto_partition_id].values[0].tolist()
        STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
        STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID = unique_id
        STO_OUTPUT_DEFAULT_TRAINED_MODEL = onx
        # onx.SerializeToString().decode('raw_unicode_escape')
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'onnx'
        STO_OUTPUT_DEFAULT_STATUS = str(json.dumps(metadata)).replace("'", '"')
        print_outputs()
    except Exception as e:

        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the onnx outputs failed {e}"}}'
        print_when_exception()

