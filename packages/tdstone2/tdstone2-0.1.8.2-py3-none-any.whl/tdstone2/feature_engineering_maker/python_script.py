import re


def generate_aggregating_custom_function(custom_function_str):
    """
    Generates Python code for a class that incorporates a custom function
    into its method. This function automatically adds `**kwargs` to the custom
    function if not present, handles the inclusion of import statements, and
    initializes `self.arguments` with the default arguments of the custom function.

    Parameters:
    - custom_function_str (str): A string representation of the custom function,
      including any import statements necessary for the function and its default arguments.

    Returns:
    - str: A string of Python code for a class that includes the custom function
           and initializes `self.arguments` with the function's default arguments.

    Example:
    >>> custom_function = \'''
    from scipy import signal

    def customized_function(X, param_list=['mean','max']):
        return X.agg(param_list)
    \'''
    >>> print(generate_code_with_custom_function(custom_function))
    # This will output the generated Python code including the provided custom function
    # and the initialization of `self.arguments` with `{'param_list': ['mean', 'max']}`.
    """
    # Split the custom function into import lines and the function definition
    import_lines = []
    function_lines = []
    default_args = {}
    for line in custom_function_str.split('\n'):
        if line.strip().startswith('from') or line.strip().startswith('import'):
            import_lines.append(line)
        else:
            function_lines.append(line)
            # Extract default arguments
            match = re.search(r"def \w+\(.*?([\w]+)=\s*(.*?)\)", line)
            if match:
                arg_name, arg_val = match.groups()
                # Attempt to convert arg_val to a Python literal
                try:
                    arg_val = eval(arg_val)
                except:
                    pass
                default_args[arg_name] = arg_val

    # Ensure **kwargs is added to the function signature
    if not 'kwargs' in custom_function_str:
        function_lines[-1] = function_lines[-1].replace('):', ', **kwargs):')

    # Reconstruct the custom function string without imports
    function_str = '\n'.join(function_lines)

    # Convert default arguments to dictionary initialization code
    default_args_str = f"{default_args}".replace("'", '"')

    # Generate the code
    code = f"""## AUTOMATICALLY ADDED IMPORT - BEGIN
{'\\n'.join(import_lines)}
## AUTOMATICALLY ADDED IMPORT - END
import numpy as np
import pandas as pd
import json

class MyModel:

    def __init__(self, column_names=['ID'] + ['x' + str(i) for i in range(10)] + ['class', 'y1', 'y2', 'partitionID'],
                 column_names_X=['x' + str(i) for i in range(10)] + ['class'],
                 column_categorical=['class'],
                 partitionID=1,
                 arguments={default_args_str}):

        self.column_names = column_names
        self.column_names_X = column_names_X
        self.column_categorical = column_categorical
        self.partition_ID = partitionID
        self.arguments = arguments

    def get_model_type(self):
        # give a model type name for metadata storage
        return 'feature engineering aggregation type'

    def get_description(self):
        # give the list of relevant hyper parameters for metadata storage
        res = {{}}
        res = json.dumps(res)
        return res 

    def prepare_X(self, my_data):
        X = my_data[self.column_names_X]
        X = pd.DataFrame(X, columns=self.column_names_X)
        for c in set.intersection(set(self.column_categorical),set(self.column_names_X)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X

    def prepare_y(self, my_data):
        y = my_data[['class']] # Assuming 'class' is the target for demonstration
        y = pd.DataFrame(y,columns=['class'])
        for c in set.intersection(set(self.column_categorical),set(['class'])):
            if len(c) > 0:
                y[c] = y[c].astype('category')        
        return y

    def transform(self, df_local):
        X = self.prepare_X(df_local)
        ## CUSTOMIZED CODE - BEGIN
{function_str}
        df = customized_function(X, **self.arguments)
        ## CUSTOMIZED CODE - END
        return {{y+'_'+x:val[y] for x,val in df.iterrows() for y in val.keys()}}
"""

    return code


def generate_nonaggregating_custom_function(custom_function_str):
    """
    Generates Python code for a class that incorporates a custom function
    into its method. This function automatically adds `**kwargs` to the custom
    function if not present, handles the inclusion of import statements, and
    initializes `self.arguments` with the default arguments of the custom function.

    Parameters:
    - custom_function_str (str): A string representation of the custom function,
      including any import statements necessary for the function and its default arguments.

    Returns:
    - str: A string of Python code for a class that includes the custom function
           and initializes `self.arguments` with the function's default arguments.

    Example:
    >>> custom_function = \'''
    from scipy import signal

    def customized_function(X, column_list=[]):
        for c1 in column_list:
            for c2 in column_list:
                new_feature_name = c1+'_x_'+c2
                if new_feature_name not in X.columns: # Ensure not to duplicate columns
                    X[new_feature_name] = X[c1] * X[c2]
        return X
    \'''
    >>> print(generate_nonaggregating_custom_function(custom_function))
    # This will output the generated Python code including the provided custom function
    # and the initialization of `self.arguments` with `{'column_list': []}`.
    """
    # Split the custom function into import lines and the function definition
    import_lines = []
    function_lines = []
    default_args = {}
    for line in custom_function_str.split('\n'):
        if line.strip().startswith('from') or line.strip().startswith('import'):
            import_lines.append(line)
        else:
            function_lines.append(line)
            # Extract default arguments
            match = re.search(r"def \w+\(.*?([\w]+)=\s*(.*?)\)", line)
            if match:
                arg_name, arg_val = match.groups()
                # Attempt to convert arg_val to a Python literal
                try:
                    arg_val = eval(arg_val)
                except:
                    pass
                default_args[arg_name] = arg_val

    # Ensure **kwargs is added to the function signature
    if not 'kwargs' in custom_function_str:
        function_lines[-1] = function_lines[-1].replace('):', ', **kwargs):')

    # Reconstruct the custom function string without imports
    function_str = '\n'.join(function_lines)

    # Convert default arguments to dictionary initialization code
    default_args_str = f"{default_args}".replace("'", '"')

    # Generate the code
    code = f"""## AUTOMATICALLY ADDED IMPORT - BEGIN
{'\\n'.join(import_lines)}
## AUTOMATICALLY ADDED IMPORT - END
import numpy as np
import pandas as pd
import json

class MyModel:

    def __init__(self, column_names=['ID'] + ['x' + str(i) for i in range(10)] + ['class', 'y1', 'y2', 'partitionID'],
                 column_names_X=['x' + str(i) for i in range(10)] + ['class'],
                 column_categorical=['class'],
                 partitionID=1,
                 arguments={default_args_str}):

        self.column_names = column_names
        self.column_names_X = column_names_X
        self.column_categorical = column_categorical
        self.partition_ID = partitionID
        self.arguments = arguments

    def get_model_type(self):
        # give a model type name for metadata storage
        return 'feature engineering non-aggregation type'

    def get_description(self):
        # give the list of relevant hyper parameters for metadata storage
        res = {{}}
        res = json.dumps(res)
        return res 

    def prepare_X(self, my_data):
        X = my_data[self.column_names_X]
        X = pd.DataFrame(X, columns=self.column_names_X)
        for c in set.intersection(set(self.column_categorical),set(self.column_names_X)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X

    def prepare_y(self, my_data):
        y = my_data[['class']] # Assuming 'class' is the target for demonstration
        y = pd.DataFrame(y,columns=['class'])
        for c in set.intersection(set(self.column_categorical),set(['class'])):
            if len(c) > 0:
                y[c] = y[c].astype('category')        
        return y

    def transform(self, df_local):
        X = self.prepare_X(df_local)
        ## CUSTOMIZED CODE - BEGIN
{function_str}
        df = customized_function(X, **self.arguments)
        ## CUSTOMIZED CODE - END
        return df
"""

    return code