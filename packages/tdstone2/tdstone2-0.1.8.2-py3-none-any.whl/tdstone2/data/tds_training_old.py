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


def encode_base64M(data: bytes) -> str:
    # Standard base64 encoding
    base64_encoded = base64.b64encode(data)
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

STO_OUPTUT_DEFAULT_STO_PARTITION_ID = -1
STR_OUTPUT_DEFAULT_STO_MODEL_ID = -1
STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID = 'STO error'
STO_OUPTUT_DEFAULT_TRAINED_MODEL = 'STO error'
STO_OUTPUT_DEFAULT_MODEL_TYPE = 'None'
STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed"}'
STO_OUPTUT_DEFAULT_EXECUTION_TIME = '9999-01-01 00:00:00.000000-04:00'

nb_partitions = None

DELIMITER = '\t'
OUTPUT_DELIMITER = DELIMITER


def print_outputs():
    if nb_partitions is None:
        for i in range(10):
            list_2_print = [str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID)] * (i + 1)
            list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID))
            list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL))
            list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
            print(DELIMITER.join(list_2_print))
    elif type(STO_OUPTUT_DEFAULT_STO_PARTITION_ID) == list and len(
            STO_OUPTUT_DEFAULT_STO_PARTITION_ID) == nb_partitions:
        list_2_print = [str(x) for x in STO_OUPTUT_DEFAULT_STO_PARTITION_ID]
        list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))
    else:
        list_2_print = [str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID)] * nb_partitions
        list_2_print.append(str(STR_OUTPUT_DEFAULT_STO_MODEL_ID))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID))
        list_2_print.append(str(STO_OUTPUT_DEFAULT_MODEL_TYPE))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_STATUS))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_TRAINED_MODEL))
        list_2_print.append(str(STO_OUPTUT_DEFAULT_EXECUTION_TIME))
        print(DELIMITER.join(list_2_print))


def print_outputs2():
    print(
        str(STO_OUPTUT_DEFAULT_STO_PARTITION_ID) + OUTPUT_DELIMITER +
        str(STR_OUTPUT_DEFAULT_STO_MODEL_ID) + OUTPUT_DELIMITER +
        str(STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID) + OUTPUT_DELIMITER +
        str(STO_OUTPUT_DEFAULT_MODEL_TYPE) + OUTPUT_DELIMITER +
        str(STO_OUPTUT_DEFAULT_STATUS) + OUTPUT_DELIMITER +
        str(STO_OUPTUT_DEFAULT_TRAINED_MODEL) + OUTPUT_DELIMITER +
        str(STO_OUPTUT_DEFAULT_EXECUTION_TIME)
    )


def print_when_exception():
    print_outputs()
    sys.exit()


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
    'sto_fold_id',
    'sto_code_type',
    'sto_code',
    'arguments',
    'execution_time'
]

inputs_ = {x: i for i, x in enumerate(beg_cols)}
temp = {x: i - len(end_cols) for i, x in enumerate(end_cols)}
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
                                                                   max(inputs_.values()) + 1):(min(inputs_.values()))]]
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
                                                                       max(inputs_.values()) + 1):(
                                                                   min(inputs_.values()))]]
                data_Tbl.append(allData)
                nObs = len(data_Tbl)
        except (EOFError):  # Exit if reached EOF or CTRL-D
            break
except:
    # when error in loading the data
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"unexpected error in loading the data"}'
    print_when_exception()

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

# Number of records to score
STO_OUPTUT_DEFAULT_STATUS = sto_partition_id + ' ' + sto_row_id + ' ' + sto_fold_id
STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id

# Rebuild the Parameters
try:
    Params = json.loads(arguments)
except:
    # when error in parsing the parameter
    # '{"error": "failed", "info":"arguments JSON may not be well formed"}'
    STO_OUPTUT_DEFAULT_STATUS = '{"error": "failed", "info":"arguments JSON may not be well formed"}' + arguments
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
    sto_fold_id = sto_fold_id.split(',')
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "problem to split sto_fold_id. {e}"}}'
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

if df.shape[0] < 30:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "not enough data left after the dropna. Only {df.shape[0]} rows."}}'

# rebuild the code
try:
    Code = base64.b64decode(sto_code).decode()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the code rebuild the code. Please test it locally first. {e}"}}'
    print_when_exception()

try:
    list1 = list_module_version()
    exec(Code)
    list2 = list_module_version()
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

    # Run the fit method on the data
    try:
        model.fit(df)
    except Exception as e:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "the model run failed. {e}"}}'
        print_when_exception()

try:
    model_type = model.get_model_type()
except Exception as e:
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "issue with get_model_type. {e}"}}'
    print_when_exception()

try:
    model_metadata = model.get_description()
except Exception as e:
    model_metadata = '{}'
    STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "issue with get_description. {e}"}}'
    print_when_exception()

import uuid

unique_id = str(uuid.uuid4())
STO_OUPTUT_DEFAULT_STATUS = 'after python class'

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

        STO_OUPTUT_DEFAULT_STO_PARTITION_ID = df[sto_partition_id].values[0].tolist()
        STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
        STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID = unique_id
        STO_OUPTUT_DEFAULT_TRAINED_MODEL = modelSerB64
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'pickle'
        STO_OUPTUT_DEFAULT_STATUS = str(json.dumps(metadata)).replace("'", '"')
        print_outputs()
    except Exception as e:
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'pickle'
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the pickle outputs failed {e}"}}'
        print_when_exception()

if 'onnx' in Params_STO['output_format']:
    STO_OUTPUT_DEFAULT_MODEL_TYPE = 'onnx'
    try:
        # model conversion
        onx = convert2onnx_mymodel_object(model, df, Params)
    except Exception as e:
        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "model conversion to ONNX failed {e}"}}'
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

        STO_OUPTUT_DEFAULT_STO_PARTITION_ID = df[sto_partition_id].values[0].tolist()
        STR_OUTPUT_DEFAULT_STO_MODEL_ID = sto_model_id
        STO_OUPTUT_DEFAULT_TRAINED_MODEL_ID = unique_id
        STO_OUPTUT_DEFAULT_TRAINED_MODEL = onx
        # onx.SerializeToString().decode('raw_unicode_escape')
        STO_OUTPUT_DEFAULT_MODEL_TYPE = 'onnx'
        STO_OUPTUT_DEFAULT_STATUS = str(json.dumps(metadata)).replace("'", '"')
        print_outputs()
    except Exception as e:

        STO_OUPTUT_DEFAULT_STATUS = f'{{"error": "failed", "info": "writing the onnx outputs failed {e}"}}'
        print_when_exception()

