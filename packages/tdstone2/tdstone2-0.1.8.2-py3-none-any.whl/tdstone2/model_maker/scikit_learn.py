from datetime import datetime
from sklearn.base import ClassifierMixin, RegressorMixin, OutlierMixin


from datetime import datetime

from sklearn.base import ClassifierMixin, RegressorMixin, OutlierMixin

def detect_pipeline_type(steps):
    """
    Detect whether a scikit-learn pipeline is for classification, regression, or anomaly detection.

    Parameters:
    steps (list of tuples): A list of (name, estimator) tuples that represent the steps in a pipeline.

    Returns:
    str: 'classification' if the pipeline is for classification,
         'regression' if for regression,
         'anomaly detection' if for anomaly detection,
         or 'unknown' otherwise.
    """
    # Check if the pipeline is empty
    if not steps:
        return 'unknown'

    # Get the last step of the pipeline, which is typically the estimator
    _, estimator = steps[-1]

    # Check the type of the estimator
    if isinstance(estimator, ClassifierMixin):
        return 'classification'
    elif isinstance(estimator, RegressorMixin):
        return 'regression'
    elif isinstance(estimator, OutlierMixin):
        return 'anomaly detection'
    else:
        return 'unknown'


def generate_code_skl_pipeline(steps):
    """
    Generates code for a classifier or regressor pipeline based on the provided steps.

    This function first determines whether the provided pipeline steps correspond to a
    classification or regression task by using the `detect_pipeline_type` function. Then,
    it calls either `generate_classifier_pipeline` or `generate_regressor_pipeline` to generate
    the appropriate pipeline code.

    Parameters:
    - steps (list of tuples): A list of (name, estimator) tuples representing the steps in a pipeline.

    Returns:
    - The generated code for the specified classifier or regressor pipeline.

    Raises:
    - ValueError: If the pipeline type is neither classification nor regression.
    """
    pipeline_type = detect_pipeline_type(steps)
    if pipeline_type == 'classification':
        return generate_classifier_pipeline(steps)
    elif pipeline_type == 'regression':
        return generate_regressor_pipeline(steps)
    elif pipeline_type == 'anomaly detection':
        return generate_outlier_pipeline(steps)
    else:
        # This else block is technically redundant due to the ValueError raised in detect_pipeline_type
        # But it's here for logical completeness and clarity.
        raise ValueError("Unsupported pipeline type detected.")

def save_code_to_file(code, filename, add_timestamp=True):
    """
    Saves the given Python code string to a file, optionally appending a timestamp to the filename to ensure uniqueness.

    Parameters:
    - code (str): The Python code to be saved. It should be a string containing valid Python code.
    - filename (str): The base name of the file where the code will be saved. This should include the '.py' extension if `add_timestamp` is False.
    - add_timestamp (bool, optional): Whether to append a timestamp to the filename for uniqueness. Defaults to True.

    Returns:
    - str: The final filename with or without a timestamp, indicating the exact file name used to save the code. If an error occurs, returns None.

    Raises:
    - IOError: If the function encounters an issue while trying to write to the file, it will print an error message. Note: the function catches and handles IOError, so it does not explicitly raise it to the caller.
    """

    if add_timestamp:
        # Strip '.py' extension if present to correctly append the timestamp
        if filename.lower().endswith('.py'):
            filename = filename[:-3]
        # Generate a timestamp in the format 'YYYYMMDD_HHMMSS'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Append the timestamp to the filename, preserving the '.py' extension
        final_filename = f"{filename}_{timestamp}.py"
    else:
        final_filename = filename

    try:
        with open(final_filename, 'w') as file:
            file.write(code)
        return final_filename
    except IOError as e:
        print(f"An error occurred while writing to {final_filename}: {e}")
        return None



def extract_hyperparameters(steps):
    """
    Extracts hyperparameters from a list of pipeline steps.

    Parameters:
        steps (list): A list of tuples, where each tuple contains the name of the step and an instance of a transformer or estimator.

    Returns:
        dict: A dictionary suitable for use with set_params(**arguments).
    """
    arguments = {}
    for step_name, step_instance in steps:
        # For each step, get its parameters
        params = step_instance.get_params()
        # Prefix parameter names with the step name and a double underscore
        for param_name, param_value in params.items():
            prefixed_param_name = f"{step_name}__{param_name}"
            arguments[prefixed_param_name] = param_value
    return arguments

from sklearn.compose import ColumnTransformer

def extract_explicit_hyperparameters(steps):
    """
    Extracts hyperparameters that were explicitly set for a list of pipeline steps.

    Parameters:
        steps (list): A list of tuples, where each tuple contains the name of the step and an instance of a transformer or estimator.

    Returns:
        dict: A dictionary of explicitly set parameters, suitable for use with set_params(**arguments).
    """
    explicit_arguments = {}
    for step_name, step_instance in steps:
        # Skip subscript access for unfitted ColumnTransformer
        if isinstance(step_instance, ColumnTransformer) and not hasattr(step_instance, 'transformers_'):
            continue  # or log a warning if needed

        try:
            default_instance = step_instance.__class__()
            current_params = step_instance.get_params()
            default_params = default_instance.get_params()

            for param_name, current_value in current_params.items():
                if current_value != default_params[param_name]:
                    prefixed_param_name = f"{step_name}__{param_name}"
                    explicit_arguments[prefixed_param_name] = current_value
        except Exception as e:
            print(f"Warning: could not extract parameters from step '{step_name}': {e}")

    return explicit_arguments

def generate_classifier_pipeline(steps):
    """
    Generates the source code for a class encapsulating a scikit-learn pipeline with the specified steps,
    and includes methods for model description, data preparation, fitting, and scoring.

    Parameters:
        steps (list of tuples): A list where each element is a tuple containing the name of the step
                                and its corresponding scikit-learn object. Example:
                                [('scaler', StandardScaler()), ('classifier', RandomForestClassifier())]

    Returns:
        str: The source code of the class as a string.
    """
    # Import statements required for the pipeline
    imports = set(["import pandas as pd", "import numpy as np", "import json",
                   "from sklearn.pipeline import Pipeline", "from sklearn.metrics import f1_score, precision_score, recall_score, accuracy_score, roc_auc_score",
                   "from sklearn import __version__"])

    # Add necessary import statements for each step in the pipeline
    for step_name, step_instance in steps:
        # Assuming step_instance is an instance of the class, not the class itself
        module = step_instance.__module__
        class_name = type(step_instance).__name__  # Gets the class name of the instance

        # Heuristic to convert module path to a likely public import path
        public_module = module.split('.')[:-1]  # Drop the last part which might be private
        public_import = '.'.join(public_module) + f" import {class_name}"
        public_import = 'from ' + public_import
        # Add the constructed import statement
        imports.add(public_import)

    # Begin class definition
    class_code = f"""
class MyModel():
    \"\"\"
    A class to encapsulate a scikit-learn pipeline model with preprocessing and prediction steps:
    
    
    Attributes:
        target (str): The name of the target variable in the dataset.
        scaler_X (StandardScaler): An instance of StandardScaler to standardize features.
        arguments (dict): Configuration arguments for the Logistic Regression model.
        model (LogisticRegression): The Logistic Regression model instance.
        f1_score (float): The F1 score of the model, initialized as -1.
        precision (float): Precision of the model, initialized as -1.
        recall (float): Recall of the model, initialized as -1.
        accuracy (float): Accuracy of the model, initialized as -1.
        auc (float): Area Under the ROC Curve of the model, initialized as -1.
        column_names (list): List of column names in the dataset.
        column_names_X (list): List of column names to be used as features.
        column_categorical (list): List of categorical feature names.
        partition_ID (int): An identifier for dataset partition, if used.
        nrow_for_training (int): Number of rows used for training.
        target_categories (list): Categories of the target variable.
    
    \"\"\"

    def __init__(self, target,
                 column_names=['ID'] + ['x' + str(i) for i in range(10)] + ['class', 'y1', 'y2', 'partitionID'],
                 column_names_X=['x' + str(i) for i in range(10)] + ['class'],
                 column_categorical=['class'],
                 partitionID=1,
                 arguments=None
                 ):
        self.target = target
        self.f1_score = -1.
        self.precision = -1.
        self.recall = -1.
        self.accuracy = -1.
        self.auc = -1.
        self.coef_ = dict()
        self.feature_importance = dict()
        
        self.column_names = column_names
        self.column_names_X = column_names_X
        self.column_categorical = column_categorical
        self.partition_ID = partitionID
        self.nrow_for_training = np.nan
        self.target_categories = []

        # Default arguments for the pipeline if none are provided
        if arguments is None:
            arguments = {{{','.join([f"'{step[0]}__param_name': 'default_value'" for step in steps])}}}

        # Constructing the pipeline
        self.model = Pipeline([
            {', '.join([f"('{step[0]}', {step[1].__class__.__name__}())" for step in steps])}
        ])

        # Updating the pipeline parameters with provided arguments
        self.model.set_params(**arguments)
        self.arguments = arguments

    def get_model_type(self):
        \"\"\"Returns the type of model as a string for metadata storage.\"\"\"
        return 'classification scikit-learn pipeline'

    def get_description(self):
        \"\"\"
        Returns a JSON string containing relevant hyperparameters, model details, and metadata for storage.
        \"\"\"
        res = {{
            'partitionID': self.partition_ID,
            'target': self.target,
            'package': 'scikit-learn',
            'package_version': __version__,
            'f1_score': self.f1_score,
            'precision': self.precision,
            'recall' : self.recall,
            'accuracy' : self.accuracy,
            'auc' : self.auc,            
            'column_order': self.column_names,
            'column_predictors': self.column_names_X,
            'column_categorical': self.column_categorical,
            'nrow_for_training': self.nrow_for_training,
            'arguments': self.arguments
        }}
        if len(self.coef_) > 0:
            res['coeffs'] = self.coef_
        if len(self.feature_importance) > 0:
            res['feature_importance'] = self.feature_importance
        return json.dumps(res)

    def prepare_X(self, my_data):
        \"\"\"Prepares the feature matrix X from the dataset.\"\"\"
        # Data preparation code here
        X = my_data[self.column_names_X]
        X = pd.DataFrame(X, columns=self.column_names_X)
        for c in set.intersection(set(self.column_categorical), set(self.column_names_X)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X
        
    def prepare_y(self, my_data):
        \"\"\"Prepares the target variable series y from the dataset.\"\"\"
        # Data preparation code here
        y = my_data[[self.target]]
        y = pd.DataFrame(y, columns=[self.target])
        for c in set.intersection(set(self.column_categorical), set([self.target])):
            if len(c) > 0:
                y[c] = y[c].astype('category')        
        return y

    def fit(self, my_data):
        \"\"\"Fits the model to the dataset.\"\"\"
        X = self.prepare_X(my_data)
        y = self.prepare_y(my_data)
        self.nrow_for_training = X.shape[0]
        self.model.fit(X, y.values.ravel())
    
        y_pred = self.model.predict(X)
        self.target_categories = list(y[self.target].cat.categories) if y[self.target].dtype.name == 'category' else np.unique(y)
    
        # Update metric calculations to handle both binary and multiclass
        self.f1_score = f1_score(y, y_pred, average='weighted')  # 'weighted' accounts for label imbalance in multiclass
        self.precision = precision_score(y, y_pred, average='weighted')
        self.recall = recall_score(y, y_pred, average='weighted')
        self.accuracy = accuracy_score(y, y_pred)
    
        # Handling ROC AUC for binary and multiclass
        if len(self.target_categories) == 2:  # Binary classification case
            y_prob = self.model.predict_proba(X)[:, 1]  # Probabilities for the positive class
            self.auc = roc_auc_score(y, y_prob)
        elif hasattr(self.model, "predict_proba"):  # Multiclass case, only calculate AUC if meaningful and possible
            try:
                y_prob = self.model.predict_proba(X)
                # AUC is only calculated if it's meaningful (binary) or explicitly requested for multiclass with a viable averaging method
                self.auc = roc_auc_score(y, y_prob, multi_class="ovr", average="weighted")
            except ValueError:
                self.auc = None  # AUC cannot be calculated meaningfully for multiclass in some contexts
        else:
            self.auc = None  # AUC is not applicable without predict_proba or for multiclass without a specified method
    
        # Extract coefficients and intercepts
        self.coef_ = dict()  # Ensure this is initialized in the class scope
        self.feature_importance = dict()
        for name, step in self.model.named_steps.items():
            if hasattr(step, 'coef_'):
                # Handle potential multi-class scenario and 1D/2D coef_ arrays
                coefs = step.coef_
                if coefs.ndim == 1:  # Single set of coefficients, make it a 2D array for uniform processing
                    coefs = [coefs]
                self.coef_[name] = []
                for class_idx, class_coefs in enumerate(coefs):
                    coef_dict = {{feature_name: coef for feature_name, coef in zip(self.column_names_X, class_coefs.tolist())}}
                    if hasattr(step, 'intercept_'):
                        coef_dict['intercept'] = step.intercept_[class_idx] if step.intercept_.ndim > 0 else step.intercept_
                    self.coef_[name].append(coef_dict)  
            # Extracting feature importances if available
            if hasattr(step, 'feature_importances_'):
                # feature_importances_ is already a 1D array representing the importance of each feature
                importances = step.feature_importances_
                importance_dict = {{feature_name: importance for feature_name, importance in zip(self.column_names_X, importances)}}
                self.feature_importance[name] = importance_dict                    
        return
        
    def score(self, my_data):
        \"\"\"Scores the dataset using the fitted model and returns predictions and probabilities.\"\"\"
        X = self.prepare_X(my_data)
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
    
        # Copying the input dataframe to include predictions
        res = my_data.copy()
        res[self.target + '_prediction'] = predictions
    
        # Handling target categories for proper column naming in multiclass scenarios
        if len(self.target_categories) > 1:
            proba_columns = [self.target + '_proba_' + str(category) for category in self.target_categories]
        else:
            proba_columns = [self.target + '_proba_0', self.target + '_proba_1']  # Assuming binary classification
    
        # Creating a DataFrame for probabilities and ensuring proper alignment with the original data
        tmp = pd.DataFrame(probabilities, columns=proba_columns, index=my_data.index)
        res = pd.concat([res, tmp], axis=1)
    
        return res
    """

    return '\n'.join(imports) + class_code


def generate_regressor_pipeline(steps):
    """
    Generates the source code for a class encapsulating a scikit-learn pipeline with the specified steps,
    and includes methods for model description, data preparation, fitting, and scoring.

    Parameters:
        steps (list of tuples): A list where each element is a tuple containing the name of the step
                                and its corresponding scikit-learn object. Example:
                                [('scaler', StandardScaler()), ('classifier', RandomForestClassifier())]

    Returns:
        str: The source code of the class as a string.
    """
    # Import statements required for the pipeline
    imports = set(["import pandas as pd", "import numpy as np", "import json",
                   "from sklearn.pipeline import Pipeline",
                   "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score",
                   "from sklearn import __version__"])

    # Add necessary import statements for each step in the pipeline
    for step_name, step_instance in steps:
        # Assuming step_instance is an instance of the class, not the class itself
        module = step_instance.__module__
        class_name = type(step_instance).__name__  # Gets the class name of the instance

        # Heuristic to convert module path to a likely public import path
        public_module = module.split('.')[:-1]  # Drop the last part which might be private
        public_import = '.'.join(public_module) + f" import {class_name}"
        public_import = 'from ' + public_import
        # Add the constructed import statement
        imports.add(public_import)

    # Begin class definition
    class_code = f"""
class MyModel():
    \"\"\"
    A class to encapsulate a scikit-learn pipeline model with preprocessing and prediction steps.
    
    Attributes:
        target (str): The name of the target variable in the dataset.
        scaler_X (StandardScaler): An instance of StandardScaler to standardize features.
        arguments (dict): Configuration arguments for the LassoLarsCV Regression model.
        model (LassoLarsCV): The LassoLarsCV Regression model instance.
        mae (float): The Mean Absolute Error of the model, initialized as -1.
        mse (float): The Mean Squared Error of the model, initialized as -1.
        rmse (float): The Root Mean Squared Error of the model, initialized as -1.
        r2 (float): The R-squared value of the model, initialized as -1.
        column_names (list): List of column names in the dataset.
        column_names_X (list): List of column names to be used as features.
        column_categorical (list): List of categorical feature names.
        partition_ID (int): An identifier for dataset partition, if used.
        nrow_for_training (int): Number of rows used for training.    
    \"\"\"

    def __init__(self, target,
                 column_names=['ID'] + ['x' + str(i) for i in range(10)] + ['class', 'y1', 'y2', 'partitionID'],
                 column_names_X=['x' + str(i) for i in range(10)] + ['class'],
                 column_categorical=['class'],
                 partitionID=1,
                 arguments=None
                 ):
        self.target = target
        self.mae = -1.
        self.mse = -1.
        self.rmse = -1.
        self.r2 = -1.
        self.column_names = column_names
        self.column_names_X = column_names_X
        self.column_categorical = column_categorical
        self.partition_ID = partitionID
        self.nrow_for_training = np.nan
        self.target_categories = []
        self.coef_ = dict()
        self.feature_importance = dict()

        # Default arguments for the pipeline if none are provided
        if arguments is None:
            arguments = {{{','.join([f"'{step[0]}__param_name': 'default_value'" for step in steps])}}}

        # Constructing the pipeline
        self.model = Pipeline([
            {', '.join([f"('{step[0]}', {step[1].__class__.__name__}())" for step in steps])}
        ])

        # Updating the pipeline parameters with provided arguments
        self.model.set_params(**arguments)
        self.arguments = arguments

    def get_model_type(self):
        \"\"\"Returns the type of model as a string for metadata storage.\"\"\"
        return 'regression scikit-learn pipeline'

    def get_description(self):
        \"\"\"
        Returns a JSON string containing relevant hyperparameters, model details, and metadata for storage.
        \"\"\"
        res = {{
            'partitionID': self.partition_ID,
            'target': self.target,
            'package': 'scikit-learn',
            'package_version': __version__,
            'mae': self.mae,
            'mse': self.mse,
            'rmse': self.rmse,
            'r2': self.r2,
            'column_order': self.column_names,
            'column_predictors': self.column_names_X,
            'column_categorical': self.column_categorical,
            'nrow_for_training': self.nrow_for_training,
            'arguments': self.arguments
        }}
        if len(self.coef_) > 0:
            res['coeffs'] = self.coef_
        if len(self.feature_importance) > 0:
            res['feature_importance'] = self.feature_importance            
        return json.dumps(res)

    def prepare_X(self, my_data):
        \"\"\"Prepares the feature matrix X from the dataset.\"\"\"
        # Data preparation code here
        X = my_data[self.column_names_X]
        X = pd.DataFrame(X, columns=self.column_names_X)
        for c in set.intersection(set(self.column_categorical), set(self.column_names_X)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X
        
    def prepare_y(self, my_data):
        \"\"\"Prepares the target variable series y from the dataset.\"\"\"
        # Data preparation code here
        y = my_data[[self.target]]
        y = pd.DataFrame(y, columns=[self.target])
        for c in set.intersection(set(self.column_categorical), set([self.target])):
            if len(c) > 0:
                y[c] = y[c].astype('category')        
        return y
        
    def fit(self, my_data):
        \"\"\"Fits the model to the dataset.\"\"\"
        # Model fitting code here
        X = self.prepare_X(my_data)
        y = self.prepare_y(my_data)
        self.nrow_for_training = X.shape[0]
        self.model.fit(X, y.values.ravel())

        y_pred = self.model.predict(X)

        self.mae = mean_absolute_error(y, y_pred)
        self.mse = mean_squared_error(y, y_pred)
        self.rmse = np.sqrt(self.mse)
        self.r2 = r2_score(y, y_pred)

        self.coef_ = dict()  # Ensure this is initialized in the class scope
        self.feature_importance = dict() 
        for name, step in self.model.named_steps.items():
            if hasattr(step, 'coef_'):
                # Handle potential multi-class scenario and 1D/2D coef_ arrays
                coefs = step.coef_
                if coefs.ndim == 1:  # Single set of coefficients, make it a 2D array for uniform processing
                    coefs = [coefs]
                self.coef_[name] = []
                for class_idx, class_coefs in enumerate(coefs):
                    coef_dict = {{feature_name: coef for feature_name, coef in zip(self.column_names_X, class_coefs.tolist())}}
                    if hasattr(step, 'intercept_'):
                        coef_dict['intercept'] = step.intercept_[class_idx] if step.intercept_.ndim > 0 else step.intercept_
                    self.coef_[name].append(coef_dict)  
            # Extracting feature importances if available
            if hasattr(step, 'feature_importances_'):
                # feature_importances_ is already a 1D array representing the importance of each feature
                importances = step.feature_importances_
                importance_dict = {{feature_name: importance for feature_name, importance in zip(self.column_names_X, importances)}}
                self.feature_importance[name] = importance_dict
        return
        
    def score(self, my_data):
        \"\"\"Scores the dataset using the fitted model and returns predictions and probabilities.\"\"\"
        # Scoring code here
        X = self.prepare_X(my_data)
        res = my_data.copy()
        res[self.target+'_prediction'] = self.model.predict(X)
        return res        
    """

    return '\n'.join(imports) + class_code


def generate_outlier_pipeline(steps):
    """
    Generates the source code for a class encapsulating a scikit-learn pipeline with the specified steps,
    and includes methods for model description, data preparation, fitting, and scoring.

    Parameters:
        steps (list of tuples): A list where each element is a tuple containing the name of the step
                                and its corresponding scikit-learn object. Example:
                                [('scaler', StandardScaler()), ('classifier', RandomForestClassifier())]

    Returns:
        str: The source code of the class as a string.
    """
    # Import statements required for the pipeline
    imports = set(["import pandas as pd", "import numpy as np", "import json",
                   "from sklearn.pipeline import Pipeline",
                   "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score",
                   "from sklearn import __version__"])

    # Add necessary import statements for each step in the pipeline
    for step_name, step_instance in steps:
        # Assuming step_instance is an instance of the class, not the class itself
        module = step_instance.__module__
        class_name = type(step_instance).__name__  # Gets the class name of the instance

        # Heuristic to convert module path to a likely public import path
        public_module = module.split('.')[:-1]  # Drop the last part which might be private
        public_import = '.'.join(public_module) + f" import {class_name}"
        public_import = 'from ' + public_import
        # Add the constructed import statement
        imports.add(public_import)

    # Begin class definition
    class_code = f"""
class MyModel():
    \"\"\"
    A class to encapsulate a scikit-learn pipeline model with preprocessing and prediction steps.

    Attributes:
        target (str): The name of the target variable in the dataset.
        scaler_X (StandardScaler): An instance of StandardScaler to standardize features.
        arguments (dict): Configuration arguments for the LassoLarsCV Regression model.
        model (LassoLarsCV): The LassoLarsCV Regression model instance.
        mae (float): The Mean Absolute Error of the model, initialized as -1.
        mse (float): The Mean Squared Error of the model, initialized as -1.
        rmse (float): The Root Mean Squared Error of the model, initialized as -1.
        r2 (float): The R-squared value of the model, initialized as -1.
        column_names (list): List of column names in the dataset.
        column_names_X (list): List of column names to be used as features.
        column_categorical (list): List of categorical feature names.
        partition_ID (int): An identifier for dataset partition, if used.
        nrow_for_training (int): Number of rows used for training.    
    \"\"\"

    def __init__(self, target,
                 column_names=['ID'] + ['x' + str(i) for i in range(10)] + ['class', 'y1', 'y2', 'partitionID'],
                 column_names_X=['x' + str(i) for i in range(10)] + ['class'],
                 column_categorical=['class'],
                 partitionID=1,
                 arguments=None
                 ):
        self.target = target
        self.column_names = column_names
        self.column_names_X = column_names_X
        self.column_categorical = column_categorical
        self.partition_ID = partitionID
        self.nrow_for_training = np.nan
        self.target_categories = []
        self.support_vectors_ = dict()

        # Default arguments for the pipeline if none are provided
        if arguments is None:
            arguments = {{{','.join([f"'{step[0]}__param_name': 'default_value'" for step in steps])}}}

        # Constructing the pipeline
        self.model = Pipeline([
            {', '.join([f"('{step[0]}', {step[1].__class__.__name__}())" for step in steps])}
        ])

        # Updating the pipeline parameters with provided arguments
        self.model.set_params(**arguments)
        self.arguments = arguments

    def get_model_type(self):
        \"\"\"Returns the type of model as a string for metadata storage.\"\"\"
        return 'anomaly detection scikit-learn pipeline'

    def get_description(self):
        \"\"\"
        Returns a JSON string containing relevant hyperparameters, model details, and metadata for storage.
        \"\"\"
        res = {{
            'partitionID': self.partition_ID,
            'target': self.target,
            'package': 'scikit-learn',
            'package_version': __version__,
            'column_order': self.column_names,
            'column_predictors': self.column_names_X,
            'column_categorical': self.column_categorical,
            'nrow_for_training': self.nrow_for_training,
            'arguments': self.arguments
        }}
        if len(self.support_vectors_) > 0:
            res['nb_support_vectors'] = self.support_vectors_.shape[0]
        return json.dumps(res)

    def prepare_X(self, my_data):
        \"\"\"Prepares the feature matrix X from the dataset.\"\"\"
        # Data preparation code here
        X = my_data[self.column_names_X]
        X = pd.DataFrame(X, columns=self.column_names_X)
        for c in set.intersection(set(self.column_categorical), set(self.column_names_X)):
            if len(c) > 0:
                X[c] = X[c].astype('category')
        return X

    def prepare_y(self, my_data):
        \"\"\"Prepares the target variable series y from the dataset.\"\"\"
        # Data preparation code here
        y = my_data[[self.target]]
        y = pd.DataFrame(y, columns=[self.target])
        for c in set.intersection(set(self.column_categorical), set([self.target])):
            if len(c) > 0:
                y[c] = y[c].astype('category')        
        return y

    def fit(self, my_data):
        \"\"\"Fits the model to the dataset.\"\"\"
        X = self.prepare_X(my_data)  # Prepare your features
        self.nrow_for_training = X.shape[0]
        
        # Assuming self.model is your anomaly detection model (e.g., OneClassSVM)
        self.model.fit(X)
    
        # For anomaly detection, we often don't have y (labels) during training
        # Hence, we don't calculate MAE, MSE, RMSE, or R2 as in regression
        # Instead, we might want to store the decision function or score_samples for later thresholding or analysis
    
        # Storing model attributes if needed (e.g., support vectors in OneClassSVM)
        self.support_vectors_ = dict()  # Ensure this is initialized in the class scope
        for name, step in self.model.named_steps.items():
            if hasattr(step, 'support_vectors_'):
                # Handle potential multi-class scenario and 1D/2D coef_ arrays
                self.support_vectors_ = step.support_vectors_ 
    
        # Optionally, you can calculate some form of "fit score" based on the training data itself, 
        # such as average anomaly score, but interpret with caution as it doesn't validate performance
        
        return
    def score(self, my_data):
        \"\"\"Scores the dataset using the fitted model and returns predictions and probabilities.\"\"\"
        # Scoring code here
        X = self.prepare_X(my_data)
        res = my_data.copy()
        
        # Predicting labels (-1 for outliers, 1 for inliers)
        res['anomaly_prediction'] = self.model.predict(X)
        
        # Getting the distance of samples to the separating hyperplane
        res['decision_function'] = self.model.decision_function(X)
        
        # Calculating the anomaly score of each sample
        res['anomaly_score'] = self.model.score_samples(X)
        return res        
    """

    return '\n'.join(imports) + class_code