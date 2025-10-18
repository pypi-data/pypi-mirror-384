from tdstone2.tdstone import TDStone
from tdstone2.tdscode import Code
from tdstone2.tdsmodel import Model
from tdstone2.tdsmapper import Mapper
from tdstone2.utils import execute_query, get_partition_datatype, get_sto_parameters
import os
import uuid
import json
import teradataml as tdml


class FeatureEngineering():
    """
    Manages the lifecycle of a feature engineering process, including initialization, model registration, and transformation.
    It supports both predefined scripts and dynamically generated feature engineering functions.

    Attributes:
        id (str): Unique identifier for the feature engineering process.
        tdstone (TDStone): An instance of the TDStone class for database operations.
        mapper (Mapper): An instance of the Mapper class for managing data mapping.
        id_model (str): Identifier for the associated model.
        metadata (dict): Metadata related to the feature engineering process.
        dataset (str): Name of the dataset being used.
        feature_engineering_type (str): Type of feature engineering process (e.g., 'feature engineering', 'feature engineering reducer').
        feature_engineering_func (function): A custom feature engineering function provided by the user.
    """
    def __init__(self, tdstone, id=None, metadata={},
                 script_path=None,
                 model_parameters=None,
                 dataset=None,
                 id_row=None,
                 id_partition=None,
                 feature_engineering_type=None,
                 feature_engineering_func=None,
                 imports = ''
                 ):
        """
        Initializes the feature engineering process, either by registering and uploading code and model based on a script or by dynamically generating and uploading them.

        Parameters:
            tdstone (TDStone): An instance of the TDStone class for database operations.
            id (str, optional): Unique identifier for the feature engineering process. Generated if not provided.
            metadata (dict, optional): Metadata related to the feature engineering process.
            script_path (str, optional): Path to a script file for feature engineering.
            model_parameters (dict, optional): Parameters for the model used in feature engineering.
            dataset (str, optional): Name of the dataset being used.
            id_row (str, optional): Identifier for the row.
            id_partition (str, optional): Identifier for the partition.
            feature_engineering_type (str, optional): Type of feature engineering process.
            feature_engineering_func (function, optional): Custom feature engineering function provided by the user.
            imports (str, optional): Additional imports required by the feature_engineering_func.
        """

        self.id              = str(uuid.uuid4()) if id is None else id
        self.tdstone         = tdstone
        self.mapper          = None
        self.id_model        = None
        try:
            self.metadata        = {'user': os.getlogin()}
        except Exception as e:
            self.metadata        = {}
        self.metadata.update(metadata)
        self.dataset         = dataset
        self.feature_engineering_type = feature_engineering_type

        if script_path is not None and all([model_parameters, dataset, id_row, id_partition, feature_engineering_type]):
            self._setup_from_script(script_path, model_parameters, metadata,id_row, id_partition, dataset)
        elif feature_engineering_func is not None and all([model_parameters, dataset, id_row, id_partition, feature_engineering_type]):
            self._setup_from_function(feature_engineering_func, model_parameters, metadata, id_row, id_partition, dataset, imports)

    def _setup_from_script(self, script_path, model_parameters, metadata, id_row, id_partition, dataset):
        """
        Private method to setup the feature engineering process by registering and uploading code and model based on a script.

        Parameters:
            script_path (str): Path to the script file for feature engineering.
            model_parameters (dict): Parameters for the model used in feature engineering.
            metadata (dict): Metadata related to the feature engineering process.
        """
        # register and upload the code
        mycode = Code(tdstone=self.tdstone)
        mycode.update_metadata(metadata)
        mycode.update_script(script_path)
        mycode.upload()

        arguments = {}
        arguments["sto_parameters"] = get_sto_parameters(tdml.DataFrame(self.dataset))
        arguments["model_parameters"] = model_parameters

        # register and upload the model
        model = Model(tdstone=self.tdstone)
        model.attach_code(mycode.id)
        model.update_arguments(arguments)
        model.update_metadata(metadata)
        model.upload()
        self.id_model = model.id

        # create the mapper for model training
        self.mapper = Mapper(tdstone      = self.tdstone,
                             mapper_type  = self.feature_engineering_type,
                             id_row       = id_row,
                             id_partition = id_partition,
                             dataset      = dataset
                             )
        self.mapper.upload()
        self.mapper.fill_mapping_full(model_id=self.id_model)
        self.mapper.create_on_clause()
        self.mapper.create_sto_view()
        self._register_feature_engineering_model()

        print('feature engineering process :', self.id)
        pass

    def _setup_from_function(self, feature_engineering_func, model_parameters, metadata, id_row, id_partition, dataset, imports):
        """
        Private method to setup the feature engineering process by dynamically generating and uploading code and model.

        Parameters:
            feature_engineering_func (function): Custom feature engineering function provided by the user.
            model_parameters (dict): Parameters for the model used in feature engineering.
            metadata (dict): Metadata related to the feature engineering process.
            imports (str): Additional imports required by the feature_engineering_func.
        """

        from tdstone2.model_maker.feature_engineering import generate_feature_engineering_code
        script = generate_feature_engineering_code(func=feature_engineering_func, imports=imports, feature_engineering_type = self.feature_engineering_type)

        # register and upload the code
        mycode = Code(tdstone=self.tdstone)
        mycode.update_metadata(metadata)
        mycode.update_script_code(script)
        mycode.upload()

        arguments = {}
        arguments["sto_parameters"] = get_sto_parameters(tdml.DataFrame(self.dataset))
        arguments["model_parameters"] = model_parameters

        # register and upload the model
        model = Model(tdstone=self.tdstone)
        model.attach_code(mycode.id)
        model.update_arguments(arguments)
        model.update_metadata(metadata)
        model.upload()
        self.id_model = model.id

        # create the mapper for model training
        self.mapper = Mapper(tdstone      = self.tdstone,
                             mapper_type  = self.feature_engineering_type,
                             id_row       = id_row,
                             id_partition = id_partition,
                             dataset      = dataset
                             )
        self.mapper.upload()
        self.mapper.fill_mapping_full(model_id=self.id_model)
        self.mapper.create_on_clause()
        self.mapper.create_sto_view()
        self._register_feature_engineering_model()

        print('feature engineering process :', self.id)
        pass
    @execute_query
    def _register_feature_engineering_model(self):
        """
        Private method decorated by @execute_query to register the feature engineering model in the database.

        Returns:
            str: SQL query for inserting the feature engineering process details into the database.
        """

        query = f"""
        INSERT INTO {self.tdstone.schema_name}.{self.tdstone.feature_engineering_process_repository}
            (ID, ID_MODEL, ID_MAPPER, FEATURE_ENGINEERING_TYPE, METADATA)
             VALUES
            ('{self.id}',
             '{self.id_model}',
             '{self.mapper.id}',
             '{self.feature_engineering_type}',
             '{json.dumps(self.metadata).replace("'", '"')}');
        """
        print(f'register feature engineering model with id : {self.id}')
        return query

    def transform(self, full_mapping_update=True):
        """
        Executes the transformation process by updating mappings and executing the mapper.

        Parameters:
            full_mapping_update (bool, optional): Flag to determine if a full mapping update is required. Defaults to True.
        """
        if full_mapping_update:
            self.mapper.fill_mapping_full(model_id=self.id_model)
        self.mapper.execute_mapper()
        return

    def get_computed_features(self, denormalized_view=True):
        """
        Retrieves the computed features from the database, optionally generating a denormalized view.

        Parameters:
            denormalized_view (bool, optional): Flag to generate a denormalized view of the features. Defaults to True.

        Returns:
            DataFrame: A DataFrame containing the computed features.
        """
        if self.feature_engineering_type == 'feature engineering':
            print(self.tdstone.schema_name, self.mapper.features_repository)
            #return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper.features_repository))
        elif self.feature_engineering_type == 'feature engineering reducer':
            print(self.tdstone.schema_name, self.mapper.reduced_feature_repository)
            #return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper.reduced_feature_repository))

        def generate_denormalized_view(schema_name, table_name, col_join = None):
            feature_names = tdml.execute_sql(f"SELECT DISTINCT FEATURE_NAME, FEATURE_TYPE FROM {schema_name}.{table_name} ORDER BY 1").fetchall()
            feature_names = {x[0]: x[1] for x in feature_names}

            if col_join is None:
                columns = tdml.DataFrame(tdml.in_schema(schema_name, table_name)).columns
                col_join = columns[0:-5] + [columns[-1]]

            query_select = f"""SELECT
            {','.join(['A.' + x for x in col_join])}
            """
            query_from = f"FROM ( SEL DISTINCT {','.join(col_join)} FROM {schema_name}.{table_name}) A"
            index = 1
            for k, v in feature_names.items():
                if 'float' in v:
                    query_select += f"""\n,CAST(A{index}.FEATURE_VALUE AS FLOAT) AS {k}"""
                elif 'int' in v:
                    query_select += f"""\n,CAST(A{index}.FEATURE_VALUE AS BIGINT) AS {k}"""
                else:
                    query_select += f"""\n,A{index}.FEATURE_VALUE AS {k}"""

                query_from += f"""\nLEFT JOIN (
                SELECT {','.join(col_join)} , FEATURE_VALUE FROM {schema_name}.{table_name}
                WHERE FEATURE_NAME = '{k}'
                ) A{index}
                ON {' AND '.join(['A.' + x + '=A' + str(index) + '.' + x for x in col_join])}
                """
                index += 1

            return query_select + '\n' + query_from

        if denormalized_view:
            if self.feature_engineering_type == 'feature engineering':
                return tdml.DataFrame.from_query(generate_denormalized_view(self.tdstone.schema_name, self.mapper.features_repository))
            elif  self.feature_engineering_type == 'feature engineering reducer':
                return tdml.DataFrame.from_query(
                    generate_denormalized_view(self.tdstone.schema_name, self.mapper.reduced_feature_repository))
        else:
            if self.feature_engineering_type == 'feature engineering':
                return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper.features_repository))
            elif  self.feature_engineering_type == 'feature engineering reducer':
                return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper.reduced_feature_repository))

    def download(self, id, tdstone=None):
        """
        Downloads the feature engineering process details based on the provided ID.

        Parameters:
            id (str): The unique identifier of the feature engineering process to be downloaded.
            tdstone (TDStone, optional): An instance of the TDStone class for database operations. Defaults to current instance if None.
        """

        if tdstone is not None:
            self.tdstone = tdstone

        query = f"""
        SELECT 
           ID
        ,  ID_MODEL
        ,  ID_MAPPER
        ,  FEATURE_ENGINEERING_TYPE
        ,  METADATA
        FROM {self.tdstone.schema_name}.{self.tdstone.feature_engineering_process_repository}
        WHERE ID = '{id}'
        """

        df = tdml.DataFrame.from_query(query).to_pandas().reset_index()
        # print(df)
        if df.shape[0] > 0:
            self.id = df.ID.values[0]
            self.id_model = df.ID_MODEL.values[0]
            id_mapper = df.ID_MAPPER.values[0]
            self.mapper = Mapper(tdstone=self.tdstone)
            self.mapper.download(id=id_mapper, tdstone=self.tdstone)
            self.metadata = eval(df.METADATA.values[0])
            self.feature_engineering_type = df.FEATURE_ENGINEERING_TYPE.values[0]
        else:
            print('there is no feature engineering process with this id')

    def retrieve_code_and_data(self, Partition=None, with_data=False):
        """
        Retrieves the code and data associated with the feature engineering process.

        Parameters:
            Partition (dict, optional): Partition details to filter the data. If None, defaults are used.
            with_data (bool, optional): Flag to include the data in the results. Defaults to False.

        Returns:
            dict: A dictionary containing 'code', 'arguments', and optionally 'data'.
        """

        # Get the model_id from list_mapping:
        if Partition is None:
            df = self.mapper.list_mapping().to_pandas(num_rows=1)
            Partition = df.iloc[:, 1:-2]
            Partition = {c: v[0] for c, v in zip(Partition.columns, Partition.values.tolist())}
        else:
            df = self.mapper.list_mapping()
            df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)
            where = " and ".join(
                [k + "='" + v + "'" if type(v) == str else k + "=" + str(v) for k, v in Partition.items()])
            df = tdml.DataFrame.from_query(f"""
                SEL *
                FROM {df._table_name}
                WHERE {where}
            """).to_pandas(num_rows=1)

        id_model = df.ID_MODEL.values[0]

        # Get the Code and the Arguments
        df = self.tdstone.list_models()
        df = df[df.ID == id_model].to_pandas(num_rows=1)
        arguments = eval(df.ARGUMENTS.values[0])
        id_code = df.ID_CODE.values[0]

        # Get the Code
        df = self.tdstone.list_codes(with_full_script=True)
        df = df[df.ID == id_code].to_pandas(num_rows=1)
        code = df.CODE.values[0].decode()

        results = {}
        results['code'] = code
        results['arguments'] = arguments['model_parameters']

        if with_data:
            df = tdml.DataFrame(self.mapper.dataset)
            df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)
            where = " and ".join(
                [k + "='" + v + "'" if type(v) == str else k + "=" + str(v) for k, v in Partition.items()])
            df = tdml.DataFrame.from_query(f"""
                SEL *
                FROM {df._table_name}
                WHERE {where}
            """).sort(self.mapper.id_row).to_pandas(all_rows=True)
            results['data'] = df

        return results
