import statsmodels
import sys
import numpy as np
import pandas as pd
import json
import base64
import pickle

import warnings
warnings.filterwarnings('ignore')

STO_OUPTUT_DEFAULT_STO_PARTITION_ID = [-1]
STO_OUPTUT_DEFAULT_FEATURE_ROW      = 1
STO_OUPTUT_DEFAULT_FEATURE_NAME     = 'STO error'
STO_OUPTUT_DEFAULT_FEATURE_VALUE    = 'STO error'
STO_OUTPUT_DEFAULT_FEATURE_TYPE     = 'None'
STO_OUPTUT_DEFAULT_STATUS           = '{"error": "failed"}'
STO_OUTPUT_DEFAULT_STO_MODEL_ID     = 'STO error'
STO_OUPTUT_DEFAULT_EXECUTION_TIME   = '9999-01-01 00:00:00.000000-04:00'
DELIMITER = '\t'

nb_partitions = None

def print_outputs():
    if nb_partitions is None:
        for i in range(10):
            list_2_print = [str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID)] * (i + 1)
            list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_ROW))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_NAME))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_VALUE))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
            print(DELIMITER.join(list_2_print))
    elif type(STO_OUPTUT_DEFAULT_STO_PARTITION_ID) == list and len(
            STO_OUPTUT_DEFAULT_STO_PARTITION_ID) == nb_partitions:
        list_2_print = [str(x) for x in STO_OUPTUT_DEFAULT_STO_PARTITION_ID]
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_ROW))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_NAME))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_VALUE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))
    else:
        list_2_print = [str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID)] * nb_partitions
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_ROW))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_NAME))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_FEATURE_VALUE))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_FEATURE_TYPE))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))

def print_when_exception():
    print_outputs()
    sys.exit()

def list_module_version():
    res = []
    for module in list(sys.modules.keys()):  # Convert keys to list before iteration
        try:
            if not 'built-in' in str(module):
                res.append(module+'=='+sys.modules[module].__version__)
        except:
            pass

    return res

# Here we read the input data
data_Tbl = []
allNum = []
# Know your data: You must know in advance the number and data types of the
# incoming columns from the Teradata database!
# For this script, the input expected format is:
beg_cols = []

end_cols = [
    'sto_fake_row',
    'sto_model_id',
    'sto_row_id',
    'sto_partition_id',
    'sto_code_type',
    'sto_code',
    'arguments',
    'execution_time'
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
                max(inputs_.values())+1):(min(inputs_.values()))]]
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
                    max(inputs_.values())+1):(min(inputs_.values()))]]
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

try:
    STO_OUPTUT_DEFAULT_EXECUTION_TIME = execution_time
except:
    # when error in parsing the parameter
    # '{"error": "failed", "info":"arguments JSON may not be well formed"}'
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"fails to read execution_time"}'
    print_when_exception()

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

try:
    df = pd.DataFrame(
        data_Tbl,
        columns=Params_STO["columnnames"])
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem constructing the dataframe with columnnames. {e}"}}'
    print_when_exception()

try:
    sto_row_id = sto_row_id.split(',')
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem to split sto_row_id. {e}"}}'
    print_when_exception()

try:
    sto_partition_id = sto_partition_id.split(',')
    nb_partitions = len(sto_partition_id)
    STO_OUPTUT_DEFAULT_STO_PARTITION_ID = df[sto_partition_id].values[0].tolist()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem to split sto_partition_id. {e}"}}'
    print_when_exception()

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

if df.shape[0] < 1:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "not enough data left after the dropna. Only {df.shape[0]} rows."}}'

# rebuild the code
try:
    Code = base64.b64decode(sto_code).decode()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code rebuild the code. Please test it locally first. {e}"}}'
    print_when_exception()

try:
    list1=list_module_version()
    exec(Code)
    list2=list_module_version()
    imported_packages = list(set(list2).difference(set(list1)))
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code cannot be executed. Please test it locally first. {e} {Code[0:100]}"}}'
    print_when_exception()


STO_OUPTUT_DEFAULT_STATUS = sto_code_type

if sto_code_type == 'python class':
    # Instantiate the model
    try:
        model = MyModel(**Params_Model)
    except:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model cannot be instanciated. Check whether the model parameters are correct and consistent."}}'
        print_when_exception()

    # Run the transform method on the data
    try:
        features = model.transform(df)
    except Exception as e:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model run failed. {e}"}}'
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
    metadata['packages'] = imported_packages
    metadata['python_version'] = str(sys.version)
    if type(features) == dict:
        STO_OUPTUT_DEFAULT_FEATURE_ROW = 1
        for key in features.keys():
            #STO_OUPTUT_DEFAULT_STO_PARTITION_ID = sto_partition_id
            STO_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
            STO_OUPTUT_DEFAULT_FEATURE_NAME = key
            STO_OUPTUT_DEFAULT_FEATURE_VALUE = str(features[key])
            STO_OUTPUT_DEFAULT_FEATURE_TYPE = str(type(features[key]))
            STO_OUPTUT_DEFAULT_STATUS = str(metadata).replace("'", '"')
            print_outputs()
    elif type(features) == list and type(features[0]) == dict:
        for i, feats in enumerate(features):
            STO_OUPTUT_DEFAULT_FEATURE_ROW = i+1
            for key in feats.keys():
                #STO_OUPTUT_DEFAULT_STO_PARTITION_ID = sto_partition_id
                STO_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
                STO_OUPTUT_DEFAULT_FEATURE_NAME = key
                STO_OUPTUT_DEFAULT_FEATURE_VALUE = str(feats[key])
                STO_OUTPUT_DEFAULT_FEATURE_TYPE = str(type(feats[key]))
                STO_OUPTUT_DEFAULT_STATUS = str(metadata).replace("'", '"')
                print_outputs()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the outputs failed {e}"}}'
    print_when_exception()
sys.exit()
