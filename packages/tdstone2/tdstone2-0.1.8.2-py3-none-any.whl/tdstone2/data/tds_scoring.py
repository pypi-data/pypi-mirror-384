import sys
import numpy as np
import pandas as pd
import json
import base64
import pickle

import warnings
warnings.filterwarnings('ignore')

# RETURNS('IDstr VARCHAR(255) CHARACTER SET UNICODE, ID_Model INTEGER, ID_Partition VARCHAR(2000) CHARACTER SET UNICODE, Model_Type VARCHAR(255) CHARACTER SET UNICODE, JSON_RESULTS VARCHAR(2000), Part_no INTEGER, BINARY_RESULTS BLOB')

batch_size  = sys.argv[1] if len(sys.argv) > 1 else 100000


STO_OUTPUT_DEFAULT_STO_PARTITION_ID = -1
STO_OUTPUT_DEFAULT_STO_ROW_ID = -1
STO_OUTPUT_DEFAULT_STO_MODEL_ID = -1
STO_OUTPUT_DEFAULT_FEATURE_NAME = 'STO error'
STO_OUTPUT_DEFAULT_FEATURE_VALUE = 'STO error'
STO_OUTPUT_DEFAULT_FEATURE_TYPE = 'None'
STO_OUTPUT_DEFAULT_STATUS = '{"error": "failed"}'
STO_OUTPUT_DEFAULT_MODEL_TYPE = 'STO error'
STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID = 'STO error'
STO_OUTPUT_DEFAULT_EXECUTION_TIME = '9999-01-01 00:00:00.000000-04:00'
DELIMITER = '\t'


def print_outputs2():
    print(
        str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_STO_ROW_ID) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_FEATURE_NAME) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_FEATURE_VALUE) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_FEATURE_TYPE) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_STATUS) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_STO_MODEL_ID) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_MODEL_TYPE) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID) + DELIMITER +
        str(STO_OUTPUT_DEFAULT_EXECUTION_TIME)

    )

nb_partitions = None
nb_rows       = None

def print_outputs():
    
    if nb_partitions is None:
        for i in range(10):
            list_2_print = [str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID)]*(i+1)
            list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_NAME))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_VALUE))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
            print(DELIMITER.join(list_2_print))
    elif type(STO_OUTPUT_DEFAULT_STO_PARTITION_ID) == list and len(STO_OUTPUT_DEFAULT_STO_PARTITION_ID) == nb_partitions and type(STO_OUTPUT_DEFAULT_STO_ROW_ID) == list and len(STO_OUTPUT_DEFAULT_STO_ROW_ID) == nb_rows:
        list_2_print = [str(x) for x in STO_OUTPUT_DEFAULT_STO_PARTITION_ID]
        list_2_print = list_2_print + [str(x) for x in STO_OUTPUT_DEFAULT_STO_ROW_ID]
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_NAME))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_VALUE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))
    else:
        list_2_print = [str(STO_OUTPUT_DEFAULT_STO_PARTITION_ID)]*nb_partitions
        list_2_print = list_2_print + [str(STO_OUTPUT_DEFAULT_STO_ROW_ID)]*nb_rows
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_NAME))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_VALUE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))    

def print_when_exception():
    print_outputs()
    sys.exit()


#print_when_exception()

# Here we read the input data
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
    'id_trained_model',
    'model_type',
    'sto_trained_model',
    'execution_time'
]

import uuid

unique_id = str(uuid.uuid4())

def reconstruct_pandas_dataframe(beg_cols, end_cols, batch_size=1):
    """
    Reads standard input line by line to construct a pandas DataFrame with
    appropriate data types specified for each column.

    Returns:
        df (DataFrame): A DataFrame with data read from standard input,
                        with columns typed as float, int, and category as appropriate.
    """
    data_Tbl = []

    for _ in range(batch_size):
        try:
            line = sys.stdin.readline()
            if line == '':  # Stop if the line is empty or EOF
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
    if df.shape[0] < 1:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "not enough data left after the dropna. Only {df.shape[0]} rows."}}'
        print_when_exception()


    return df


df, dummy_cols = reconstruct_pandas_dataframe(beg_cols, end_cols)

if df.shape[0] < 1:
    sys.exit()



# Extract values
try:
    sto_fake_row      = df['sto_fake_row'].values[0]
    sto_model_id      = df['sto_model_id'].values[0]
    sto_row_id        = df['sto_row_id'].values[0]
    sto_partition_id  = df['sto_partition_id'].values[0]
    sto_fold_id       = df['sto_fold_id'].values[0]
    sto_code_type     = df['sto_code_type'].values[0]
    sto_code          = df['sto_code'].values[0]
    arguments         = df['arguments'].values[0]
    id_trained_model  = df['id_trained_model'].values[0]
    model_type        = df['model_type'].values[0]
    sto_trained_model = df['sto_trained_model'].values[0]
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "Extract values failed. {e}"}}'
    print_when_exception()



execution_time    = parse_execution_time(df)


# Update status and model ID
STO_OUTPUT_DEFAULT_STATUS = f"{sto_partition_id} {sto_row_id} {sto_fold_id}"
STO_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id

# Rebuild parameters
Params = parse_arguments(df)
if Params is None:
    print_when_exception()
    sys.exit()

Params_STO       = extract_param(Params, 'sto_parameters', 'there is no field sto_parameters in arguments')
Params_Model     = extract_param(Params, 'model_parameters', 'there is no field model_parameters in arguments')

# Split column values
sto_row_id       = split_column_values(sto_row_id, 'sto_row_id')
sto_fold_id      = split_column_values(sto_fold_id, 'sto_fold_id')
sto_partition_id = split_column_values(sto_partition_id, 'sto_partition_id')

# Set the proper data types:
try:
    df = construct_dataframe(df, Params_STO, dummy_cols)
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "Set the proper data types failed. {e}"}}'
    print_when_exception()



nb_partitions    = len(sto_partition_id)
nb_rows          = len(sto_row_id)

# rebuild the code
Code = base64.b64decode(sto_code).decode()
STO_OUTPUT_DEFAULT_MODEL_TYPE = model_type
STO_OUTPUT_DEFAULT_TRAINED_MODEL_ID = id_trained_model

try:
    exec(Code)
except Exception as e:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code cannot be executed. Please test it locally first. {e}"}}'
    print_when_exception()



if sto_code_type == 'python class':
    # Instantiate the model
    try:
        model = pickle.loads(base64.b64decode(sto_trained_model[2:-1]))
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model cannot be deserialized. Check trained model object.{sto_trained_model}"}}'
        print_when_exception()
else:
    STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "unkown code type: {sto_code_type}"}}'
    print_when_exception()


try:
    model_type = model.get_model_type()
except Exception as e:
    model_type = 'unknown model type'

try:
    model_metadata = model.get_description()
except Exception as e:
    model_metadata = '{}'

batch = 1
while True:

    # Run the score method on the data
    try:
        columns_in = df.columns
        df = model.score(df)
        columns_out = df.columns
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model run failed. {e}"}}'
        print_when_exception()

    try:
        new_columns = set(columns_out) - set(columns_in)
        new_columns = list(new_columns)
        df = df[new_columns + sto_partition_id + sto_row_id]
        df.drop_duplicates(inplace=True)
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "df = df[["sto_partition_id", "sto_row_id"] + list(new_columns)] failed. columns_in : {",".join(columns_in)} columns_out : {",".join(columns_out)} sto_partition_id : {",".join(sto_partition_id)} sto_row_id : {",".join(sto_row_id)} {e}"}}'
        print_when_exception()


    # print the results
    try:
        metadata = {}
        metadata["error"] = "successful"
        metadata["batch"] = batch
        metadata["job"]   = unique_id
        metadata["batch_size"] = df.shape[0]
        #metadata["model_type"] = model_type
        #metadata.update(json.loads(model_metadata))
        for i, row in df.iterrows():
            for col in new_columns:
                STO_OUTPUT_DEFAULT_STO_PARTITION_ID = [row[x] for x in sto_partition_id]
                STO_OUTPUT_DEFAULT_STO_ROW_ID = [row[x] for x in sto_row_id]
                STO_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
                STO_OUTPUT_DEFAULT_FEATURE_NAME = col
                STO_OUTPUT_DEFAULT_FEATURE_VALUE = str(row[col])
                STO_OUTPUT_DEFAULT_FEATURE_TYPE = str(type(row[col]))
                STO_OUTPUT_DEFAULT_STATUS = str(metadata).replace("'", '"')
                print_outputs()

    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the outputs failed STO_OUTPUT_DEFAULT_STO_PARTITION_ID : {",".join(STO_OUTPUT_DEFAULT_STO_PARTITION_ID)} STO_OUTPUT_DEFAULT_STO_ROW_ID : {",".join(STO_OUTPUT_DEFAULT_STO_ROW_ID)}{e}"}}'
        print_when_exception()

    batch += 1
    # load next batch
    df,dummy_cols = reconstruct_pandas_dataframe(beg_cols, end_cols, batch_size=batch_size+1)
    if df.shape[0]<1:
        sys.exit('no more rows to process')
    
    # Set the proper data types:
    try:
        df = construct_dataframe(df, Params_STO, dummy_cols)
    except Exception as e:
        STO_OUTPUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "Set the proper data types failed. {e}"}}'
        print_when_exception()