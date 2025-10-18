import inspect
def analyze_function(func):
    """
    Analyzes a given function to extract its argument names, differentiate between arguments with and without default values,
    and retrieve the source code, while also providing the function's name.

    Parameters:
    - func: The function to be analyzed.

    Returns:
    - A tuple containing two dictionaries (one for arguments without default values and another for arguments with default values),
      the source code of the function, and the function's name.
    """
    # Get the signature of the function
    sig = inspect.signature(func)

    # Initialize dictionaries for arguments with and without default values
    args_with_defaults = {}
    args_without_defaults = {}

    # Separate the parameters based on whether they have default values
    for param in list(sig.parameters.values())[1:]:  # Skipping the first parameter
        if param.default is inspect.Parameter.empty:
            # Parameter does not have a default value
            args_without_defaults[param.name] = None
        else:
            # Parameter has a default value
            args_with_defaults[param.name] = param.default

    # Use inspect.getsource() to get the source code of the function
    source_code = inspect.getsource(func)

    # Function name
    func_name = func.__name__

    return args_without_defaults, args_with_defaults, source_code, func_name


def generate_feature_engineering_code(func, feature_engineering_type, imports='' ):
    # Use the analyze_function
    args_without_defaults, args_with_defaults, source_code, func_name = analyze_function(func)

    if feature_engineering_type == 'feature engineering reducer':
        output_1 = "{y+'_'+str(x): val[y] for x, val in df.iterrows() for y in val.keys()}"
        output_2 = "[{y: val[y]  for y in val.keys()} for x, val in df.iterrows()]"
    else:
        output_2 = "df"
        output_1 = "df"

    code = f"""
# Import necessary libraries
{imports}
import numpy as np
import pandas as pd
import json  # Added to use json.dumps in get_description method

# the actual code
"""

    code += source_code.replace('    ', '\t')

    code += f"""

class MyModel:
    \"\"\"
    A class representing a model for handling and processing data with specific characteristics.

    Attributes:
    column_names (list of str): Column names to be used in the dataframe.
    column_names_X (list of str): Subset of column names used for feature set.
    column_categorical (list of str): List of columns to be treated as categorical.
    partition_ID (int): Identifier for the data partition.
    arguments (dict): Additional arguments for model configuration.
    \"\"\"

    def __init__(
        self,
        column_categorical=['class'],
        arguments={{}}):
        \"\"\"
        Initializes the MyModel with the provided configuration.

        Parameters:
        column_names (list of str): Initial column names.
        column_names_X (list of str): Initial column names for features.
        column_categorical (list of str): Initial categorical columns.
        partitionID (int): Initial partition ID.
        arguments (dict): Additional model arguments.
        \"\"\"
        self.column_categorical = column_categorical
        self.arguments = {args_with_defaults}
        self.arguments.update(arguments)

    def get_model_type(self):
        \"\"\"
        Returns the type of the model.

        Returns:
        str: A string indicating the model type.
        \"\"\"
        # give a model type name for metadata storage
        return 'basic kpis'

    def get_description(self):
        \"\"\"
        Returns a description of the model including relevant hyperparameters.

        Returns:
        str: A JSON string representing model description with hyperparameters.
        \"\"\"
        res = {{}}
        res = json.dumps(res)  # Convert dictionary to JSON string
        return res 

    def prepare_X(self, my_data):
        \"\"\"
        Prepares the feature set (X) from the input data.

        Parameters:
        my_data (DataFrame): The input data from which features are extracted.

        Returns:
        DataFrame: The processed feature set.
        \"\"\"
        X = my_data
        # Convert specified columns to category type if they are in column_names_X
        for c in set.intersection(set(self.column_categorical)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X

    def transform(self, df_local):
        \"\"\"
        Transforms the input dataframe by aggregating features and returns a dictionary of results.

        Parameters:
        df_local (DataFrame): The local dataframe to be transformed.

        Returns:
        dict: A dictionary with keys representing aggregated feature names and values as their corresponding metrics.
        \"\"\"
        X = self.prepare_X(df_local)

        def has_standard_index(df):
            \"\"\"
            Checks if the DataFrame has a standard index.
            A standard index starts at 0, is continuous, and increments by 1.
        
            Parameters:
            - df: pandas.DataFrame to check
        
            Returns:
            - bool: True if the DataFrame has a standard index, False otherwise.
            \"\"\"
            # Check if the index is a RangeIndex, which inherently satisfies the standard index criteria
            #if isinstance(df.index, pd.RangeIndex) and df.index.start == 0 and df.index.step == 1:
            #    return True
            
            # If not RangeIndex, check manually
            # Generate a standard range index for comparison
            expected_index = range(len(df))
            # Check if the actual index matches the expected standard index
            is_standard = (df.index == expected_index).all()
        
            return is_standard
        
        # Perform aggregation on X and compute mean and max for each column
        if len(self.arguments.keys()) > 0:
            df = {func_name}(X, **self.arguments)
        else:
            df = {func_name}(X)

        # Convert aggregated results into a dictionary format
        if has_standard_index(df):
            return {output_2}
        else:
            return {output_1}
        """
    return code