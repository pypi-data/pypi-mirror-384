import statsmodels
import sys
import numpy as np
import pandas as pd
import json
import base64
import pickle

import warnings
warnings.filterwarnings('ignore')

# RETURNS('IDstr VARCHAR(255) CHARACTER SET UNICODE, ID_Model INTEGER, ID_Partition VARCHAR(2000) CHARACTER SET UNICODE, Model_Type VARCHAR(255) CHARACTER SET UNICODE, JSON_RESULTS VARCHAR(2000), Part_no INTEGER, BINARY_RESULTS BLOB')

STO_OUPTUT_DEFAULT_STO_PARTITION_ID = -1
STO_OUPTUT_DEFAULT_STO_ROW_ID = -1
STR_OUTPUT_DEFAULT_STO_MODEL_ID = -1
STO_OUPTUT_DEFAULT_FEATURE_VALUE = 'STO error'
STO_OUPTUT_DEFAULT_FEATURE_VALUE = 'STO error'
STO_OUTPUT_DEFAULT_FEATURE_TYPE = 'None'
STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed"}'

DELIMITER = '\t'


def print_outputs():
    print(
        str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID) + DELIMITER +
        str(STO_OUPTUT_DEFAULT_STO_ROW_ID) + DELIMITER +
        str(STR_OUTPUT_DEFAULT_STO_MODEL_ID) + DELIMITER +
        str(STO_OUPTUT_DEFAULT_FEATURE_VALUE) + DELIMITER +
        str(STO_OUPTUT_DEFAULT_STATUS)
    )


def print_when_exception():
    print_outputs()
    sys.exit()


# print_when_exception()

# Here we read the input data
data_Tbl = []
allNum = []
# Know your data: You must know in advance the number and data types of the
# incoming columns from the Teradata database!
# For this script, the input expected format is:
beg_cols = []

end_cols = [
    'sto_partition_id',
    'sto_row_id',
    'sto_fake_row',
    'sto_model_id',
    'sto_code_type',
    'sto_code',
    'arguments'
]

inputs_ = {x: i for i, x in enumerate(beg_cols)}
temp = {x: i-len(end_cols) for i, x in enumerate(end_cols)}
for k in temp:
    inputs_[k] = temp[k]


try:
    nObs = 0
    Code = []
    try:
        line = input()
        if line == '':  # Exit if user provides blank line
            pass
        else:
            nObs += 1
            allArgs = line.split(DELIMITER)
            for k in inputs_:
                exec(f'{k}=allArgs[inputs_["{k}"]]')

            allData = [x.replace(" ", "") for x in allArgs[(
                max(inputs_.values())+1):(min(inputs_.values())+2)]]
            data_Tbl.append(allData)

    except (EOFError):  # Exit if reached EOF or CTRL-D
        pass

    while 1:
        try:
            line = input()
            if line == '':  # Exit if user provides blank line
                break
            else:
                allArgs = line.split(DELIMITER)
                allData = [x.replace(" ", "") for x in allArgs[(
                    max(inputs_.values())+1):(min(inputs_.values())+2)]]
                data_Tbl.append(allData)
                nObs = len(data_Tbl)
        except (EOFError):  # Exit if reached EOF or CTRL-D
            break
except:
    # when error in loading the data
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"unexpected error in loading the data"}'
    print_when_exception()

# Number of records to score

# For AMPs that receive no data, simply exit the corresponding script instance.
if nObs < 1:
    sys.exit()

STO_OUPTUT_DEFAULT_STO_PARTITION_ID = sto_partition_id
STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
try:
    from io import StringIO
    from contextlib import redirect_stdout
except:
    # when error in parsing the parameter
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"unexpected error in importing io and contextlib packages"}'
    print_when_exception()

# Rebuild the Parameters
try:
    Params = json.loads(arguments)
except:
    # when error in parsing the parameter
    # '{"error": "failed", "info":"arguments JSON may not be well formed"}'
    STO_OUPTUT_DEFAULT_STATUS = arguments
    print_when_exception()

try:
    Params_STO = Params['sto_parameters']
except:
    # there is no field 'sto_parameters'
    # when error in parsing the parameter
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"there is no field sto_parameters in arguments"}'
    print_when_exception()

try:
    Params_Model = Params['model_parameters']
except:
    # there is no field 'model_parameters'
    # when error in parsing the parameter
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"there is no field model_parameters in arguments"}'
    print_when_exception()

df = pd.DataFrame(
    data_Tbl,
    columns=Params_STO["columnnames"]+['sto_row_id','sto_partition_id' ])

# Cast the columns
if "float_columnames" in Params_STO:
    for c in Params_STO["float_columnames"]:
        if len(c) > 0:
            try:
                df[c] = pd.to_numeric(df[c])
            except:
                STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "column {c} cannot be converted to float Python"}}'
                print_when_exception()

if "integer_columnames" in Params_STO:
    for c in Params_STO["integer_columnames"]:
        if len(c) > 0:
            try:
                df[c] = df[c].astype('int')
            except:
                STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "column {c} cannot be converted to int Python"}}'
                print_when_exception()

if "category_columns" in Params_STO:
    for c in Params_STO["category_columns"]:
        if len(c) > 0:
            try:
                df[c] = df[c].astype('category')
            except:
                STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "column {c} cannot be converted to category Python"}}'
                print_when_exception()

if "datetime_columns" in Params_STO:
    for c in Params_STO["datetime_columns"]:
        if len(c) > 0:
            try:
                df[c] = pd.to_datetime(df[c])
            except:
                STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "column {c} cannot be converted to category Python"}}'
                print_when_exception()


df = df.dropna(how='all')

if df.shape[0] < 30:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "not enough data left after the dropna. Only {df.shape[0]} rows."}}'

# rebuild the code
Code = base64.b64decode(sto_code).decode()

try:
    exec(Code)
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code cannot be executed. Please test it locally first. "}}'
    print_when_exception()



if sto_code_type == 'python class MyModel':
    # Instantiate the model
    try:
        model = MyModel(**Params_Model)
    except:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model cannot be instanciated. Check whether the model parameters are correct and consistent."}}'
        print_when_exception()

    try:
        model_type = model.get_model_type()
    except Exception as e:
        model_type = 'unknown model type'

    # Run the transform method on the data
    try:
        columns_in = df.columns
        df = model.transform(df)
    except Exception as e:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model {model_type} run failed. "}}'
        print_when_exception()
    try:
        columns_out = df.columns
        new_columns = set(columns_out)-set(columns_in)
        df = df[['sto_partition_id', 'sto_row_id']+list(new_columns)]
        # sys.exit()
    except Exception as e:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem managing the model outputs of {model_type}. Are you sure you use the script? chekc you feature engineering mapper attached to your process id. "}}'
        print_when_exception()

try:
    model_type = model.get_model_type()
except Exception as e:
    model_type = 'unknown model type'

try:
    model_metadata = model.get_description()
except Exception as e:
    model_metadata = '{}'

try:
    metadata = {}
    metadata["error"] = "successful"
    metadata["model_type"] = model_type
    metadata.update(eval(model_metadata))
    for i, row in df.iterrows():
            STO_OUPTUT_DEFAULT_STO_PARTITION_ID = row['sto_partition_id']
            STO_OUPTUT_DEFAULT_STO_ROW_ID = row['sto_row_id']
            STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
            STO_OUPTUT_DEFAULT_FEATURE_VALUE = str(row[new_columns].to_json()).replace("'", '"')
            STO_OUPTUT_DEFAULT_STATUS = str(metadata).replace("'", '"')
            print_outputs()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the outputs failed {e}"}}'
    print_when_exception()

#STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "successful", "info": "left the output to implement"}}'
#print_when_exception()
