from tdstone2.tdstone import TDStone
from tdstone2.tdscode import Code
from tdstone2.tdsmodel import Model
from tdstone2.tdsmapper import Mapper
from tdstone2.utils import execute_query,get_partition_datatype, get_sto_parameters
import os
import uuid
import json
import teradataml as tdml


class HyperModel():
    """
    Initializes the HyperModel instance.

    Args:
        tdstone (TDStone): Instance of the TDStone class for database operations.
        id (str, optional): Unique identifier for the hypermodel process. Defaults to None.
        metadata (dict, optional): Metadata associated with the hypermodel process. Defaults to an empty dictionary.
        script_path (str, optional): Path to the script for model code. Defaults to None.
        model_parameters (dict, optional): Dictionary of model parameters. Defaults to None.
        dataset (str, optional): Name of the dataset being used. Defaults to None.
        id_row (str, optional): Identifier for the row. Defaults to None.
        id_partition (str, optional): Identifier for the partition. Defaults to None.
        id_fold (str, optional): Identifier for the fold. Defaults to None.
        fold_training (Any, optional): Specifies the fold for training. Defaults to None.
        skl_pipeline_steps (list, optional): Steps for the scikit-learn pipeline. Defaults to None.
        convert_to_onnx (bool, optional): Whether to convert the model to ONNX format. Defaults to False.
        store_pickle (bool, optional): Whether to store the model as a pickle file. Defaults to True.
    """
    def __init__(self, tdstone, id = None, metadata ={},
                 script_path = None,
                 model_parameters = None,
                 dataset = None,
                 id_row = None,
                 id_partition = None,
                 id_fold = None,
                 fold_training = None,
                 skl_pipeline_steps = None,
                 convert_to_onnx = False,
                 store_pickle = True
                ):
        
        self.id               = str(uuid.uuid4()) if id is None else id
        self.tdstone          = tdstone
        self.mapper_training  = None
        self.mapper_scoring   = None
        self.id_model         = None
        self.fold_training    = fold_training
        try:
            self.metadata = {'user': os.getlogin()}
        except Exception as e:
            self.metadata = {}
        self.metadata.update(metadata)
        self.dataset          = dataset

        if model_parameters is not None and 'target' not in model_parameters.keys():
            model_parameters['target'] = ''

        if script_path is not None and model_parameters is not None and dataset is not None and id_row is not None and id_partition is not None and fold_training is not None:
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
            self.mapper_training = Mapper(tdstone=self.tdstone,
                                          mapper_type  = 'training',
                                          id_row       = id_row,
                                          id_partition = id_partition,
                                          id_fold      = id_fold,
                                          dataset      = dataset
                                         )
            self.mapper_training.upload()
            self.mapper_training.fill_mapping_full(model_id=self.id_model)
            self.mapper_training.create_on_clause(fold=self.fold_training)
            self.mapper_training.create_sto_view()
            
            # create the mapper for model scoring
            self.mapper_scoring = Mapper(tdstone=self.tdstone,
                                         mapper_type  = 'scoring',
                                         id_row       = self.mapper_training.id_row,
                                         id_partition = self.mapper_training.id_partition,
                                         id_fold      = self.mapper_training.id_fold,
                                         dataset      = self.mapper_training.dataset,
                                         trained_model_repository = self.mapper_training.trained_model_repository
                                        )
            
            self.mapper_scoring.upload()
            self.mapper_scoring.create_on_clause()
            self.mapper_scoring.create_volatile_table_on_clause()
            self.mapper_scoring.create_sto_view()
            self.mapper_scoring.fill_mapping_full(model_id=self.id_model)
            self._register_hyper_model()
            print('hyper model :', self.id)

        elif skl_pipeline_steps is not None and model_parameters is not None and dataset is not None and id_row is not None and id_partition is not None and fold_training is not None:

            from tdstone2.model_maker.scikit_learn import extract_explicit_hyperparameters, generate_code_skl_pipeline
            model_parameters["arguments"] = extract_explicit_hyperparameters(skl_pipeline_steps)
            script = generate_code_skl_pipeline(skl_pipeline_steps)

            # register and upload the code
            mycode = Code(tdstone=self.tdstone)
            mycode.update_metadata(metadata)
            mycode.update_script_code(script)
            mycode.upload()

            arguments = {}
            arguments["sto_parameters"] = get_sto_parameters(tdml.DataFrame(self.dataset))
            output_format = []
            if convert_to_onnx:
                output_format.append('onnx')

            if store_pickle:
                output_format.append('pickle')
            arguments["sto_parameters"]['output_format'] = output_format
            arguments["model_parameters"] = model_parameters

            # register and upload the model
            model = Model(tdstone=self.tdstone)
            model.attach_code(mycode.id)
            model.update_arguments(arguments)
            model.update_metadata(metadata)
            model.upload()
            self.id_model = model.id

            # create the mapper for model training
            self.mapper_training = Mapper(tdstone=self.tdstone,
                                          mapper_type='training',
                                          id_row=id_row,
                                          id_partition=id_partition,
                                          id_fold=id_fold,
                                          dataset=dataset
                                          )
            self.mapper_training.upload()
            self.mapper_training.fill_mapping_full(model_id=self.id_model)
            self.mapper_training.create_on_clause(fold=self.fold_training)
            self.mapper_training.create_sto_view()

            # create the mapper for model scoring
            self.mapper_scoring = Mapper(tdstone=self.tdstone,
                                         mapper_type='scoring',
                                         id_row=self.mapper_training.id_row,
                                         id_partition=self.mapper_training.id_partition,
                                         id_fold=self.mapper_training.id_fold,
                                         dataset=self.mapper_training.dataset,
                                         trained_model_repository=self.mapper_training.trained_model_repository
                                         )

            self.mapper_scoring.upload()
            self.mapper_scoring.create_on_clause()
            self.mapper_scoring.create_volatile_table_on_clause()
            self.mapper_scoring.create_sto_view()
            self.mapper_scoring.fill_mapping_full(model_id=self.id_model)
            self._register_hyper_model()
            print('hyper model :', self.id)
            
    @execute_query
    def _register_hyper_model(self):
        """
        Registers the hypermodel in the database by inserting relevant details into a designated repository table.

        Returns:
            str: SQL query for registering the hypermodel in the database.
        """

        query = f"""
        INSERT INTO {self.tdstone.schema_name}.{self.tdstone.hyper_model_repository}
            (ID, ID_MODEL, ID_MAPPER_TRAINING, ID_MAPPER_SCORING, METADATA)
             VALUES
            ('{self.id}',
             '{self.id_model}',
             '{self.mapper_training.id}',
             '{self.mapper_scoring.id}',
             '{json.dumps(self.metadata).replace("'", '"')}');
        """
        print(f'register hyper model with id : {self.id}')
        return query
        
        
        
    def train(self, full_mapping_update = True):
        """
        Executes the training process for the hypermodel by updating mappings and executing the mapper for training.

        Parameters:
            full_mapping_update (bool, optional): Determines whether a full mapping update is required. Defaults to True.
        """
        if full_mapping_update:
            self.mapper_training.fill_mapping_full(model_id=self.id_model)
        self.mapper_training.execute_mapper()       
        return
        
    def score(self, full_mapping_update = True):
        """
        Executes the scoring process for the hypermodel by updating mappings and executing the mapper for scoring.

        Parameters:
            full_mapping_update (bool, optional): Determines whether a full mapping update is required. Defaults to True.
        """
        if full_mapping_update:
            self.mapper_scoring.fill_mapping_full(model_id=self.id_model)
        self.mapper_scoring.create_on_clause()
        self.mapper_scoring.execute_mapper()        
        return
    
    def get_trained_models(self, with_binary_model = False):
        """
        Retrieves details of trained models, optionally including the binary model itself.

        Parameters:
            with_binary_model (bool, optional): Determines whether to include the binary model in the results. Defaults to False.

        Returns:
            DataFrame: DataFrame containing details of trained models.
        """
        print(self.tdstone.schema_name, self.mapper_training.model_repository)
        if with_binary_model:
            return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper_training.trained_model_repository))
        else:
            df = tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper_training.trained_model_repository))
            return df[[x for x in df.columns if x.lower() != 'trained_model']]

    def get_byom_catalog(self):
        """
        Retrieves details of trained models, optionally including the binary model itself.

        Parameters:
            with_binary_model (bool, optional): Determines whether to include the binary model in the results. Defaults to False.

        Returns:
            DataFrame: DataFrame containing details of trained models.
        """
        print(self.tdstone.schema_name, 'V_'+self.mapper_training.trained_model_repository+'_BYOM_CATALOG')
        return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, 'V_'+self.mapper_training.trained_model_repository+'_BYOM_CATALOG'))

    def get_model_predictions(self, denormalized_view = True):
        """
        Retrieves model predictions, optionally generating a denormalized view for easier analysis.

        Parameters:
            denormalized_view (bool, optional): Determines whether to generate a denormalized view of the predictions. Defaults to True.

        Returns:
            DataFrame: DataFrame containing model predictions.
        """
        print(self.tdstone.schema_name, self.mapper_scoring.scores_repository)

        def generate_denormalized_view(schema_name, table_name, col_join = None):
            feature_names = tdml.execute_sql(f"SELECT DISTINCT FEATURE_NAME, FEATURE_TYPE FROM {schema_name}.{table_name}").fetchall()
            feature_names = {x[0]: x[1] for x in feature_names}

            if col_join is None:
                columns = tdml.DataFrame(tdml.in_schema(schema_name, table_name)).columns
                col_join = columns[0:-5] + [columns[-1]]

            query_select = f"""SELECT
            {','.join(['A1.' + x for x in col_join])}
            """
            #query_from = f"FROM ( SEL DISTINCT {','.join(col_join)} FROM {schema_name}.{table_name}) A"
            index = 1
            for k, v in feature_names.items():
    
                if 'float' in v:
                    query_select += f"""\n,CAST(A{index}.FEATURE_VALUE AS FLOAT) AS {k}"""
                elif 'int' in v:
                    query_select += f"""\n,CAST(A{index}.FEATURE_VALUE AS BIGINT) AS {k}"""
                else:
                    query_select += f"""\n,A{index}.FEATURE_VALUE AS {k}"""

                if index == 1:
                    query_from = f"""\nFROM (
                    SELECT {','.join(col_join)} , FEATURE_VALUE FROM {schema_name}.{table_name}
                    WHERE FEATURE_NAME = '{k}'
                    ) A{index}
                    """
                else:
                    query_from += f"""\nFULL OUTER JOIN (
                    SELECT {','.join(col_join)} , FEATURE_VALUE FROM {schema_name}.{table_name}
                    WHERE FEATURE_NAME = '{k}'
                    ) A{index}
                    ON {' AND '.join(['A1.' + x + '=A' + str(index) + '.' + x for x in col_join])}
                    """
                index += 1

            return query_select + '\n' + query_from

        if denormalized_view:
            col_join = ['TD_TIMECODE', 'ID_PROCESS', 'ID_TRAINED_MODEL']+self.mapper_training.id_partition.split(',')+self.mapper_training.id_row.split(',')
            return tdml.DataFrame.from_query(generate_denormalized_view(self.tdstone.schema_name, self.mapper_scoring.scores_repository, col_join))
        else:
            return tdml.DataFrame(tdml.in_schema(self.tdstone.schema_name, self.mapper_scoring.scores_repository))

    def download(self, id, tdstone=None):
        """
        Downloads the details of a hypermodel process based on the provided ID, allowing for inspection or modification.

        Parameters:
            id (str): The unique identifier of the hypermodel process to download.
            tdstone (TDStone, optional): Instance of the TDStone class for database operations, if different from the initially provided one.
        """
        if tdstone is not None:
            self.tdstone = tdstone

        query = f"""
        SELECT 
           ID
        ,  ID_MODEL
        ,  ID_MAPPER_TRAINING
        ,  ID_MAPPER_SCORING
        ,  METADATA
        FROM {self.tdstone.schema_name}.{self.tdstone.hyper_model_repository}
        WHERE ID = '{id}'
        """

        df = tdml.DataFrame.from_query(query).to_pandas().reset_index()
        #print(df)
        if df.shape[0] > 0:
            self.id              = df.ID.values[0]
            self.id_model        = df.ID_MODEL.values[0]
            id_mapper_training   = df.ID_MAPPER_TRAINING.values[0]
            self.mapper_training = Mapper(tdstone=self.tdstone, mapper_type = 'training')
            self.mapper_training.download(id=id_mapper_training, mapper_type = 'training')
            id_mapper_scoring   = df.ID_MAPPER_SCORING.values[0]
            self.mapper_scoring = Mapper(tdstone=self.tdstone, mapper_type = 'training')
            self.mapper_scoring.download(id=id_mapper_scoring, mapper_type = 'scoring')
            self.metadata = json.loads(df.METADATA.values[0])
        else:
            print('there is no hyper model with this id')

    def retrieve_code_and_data(self, Partition=None, with_data=False):
        """
        Retrieves the code and optionally the data associated with the hypermodel process.

        Parameters:
            Partition (dict, optional): Partition details to filter the data, if specific subsets are required.
            with_data (bool, optional): Flag indicating whether to include the data in the retrieval. Defaults to False.

        Returns:
            dict: A dictionary containing 'code', 'arguments', and optionally 'data'.
        """

        # Get the model_id from list_mapping:
        if Partition is None:
            df = self.mapper_training.list_mapping().to_pandas(num_rows=1)
            Partition = df.iloc[:, 1:-2]
            Partition = {c: v[0] for c, v in zip(Partition.columns, Partition.values.tolist())}
        else:
            df = self.mapper_training.list_mapping()
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
        arguments = json.loads(df.ARGUMENTS.values[0])
        id_code = df.ID_CODE.values[0]

        # Get the Code
        df = self.tdstone.list_codes(with_full_script=True)
        df = df[df.ID == id_code].to_pandas(num_rows=1)
        code = df.CODE.values[0].decode()

        results = {}
        results['code'] = code
        results['arguments'] = arguments['model_parameters']

        if with_data:
            df = tdml.DataFrame(self.mapper_training.dataset)
            df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)
            where = " and ".join(
                [k + "='" + v + "'" if type(v) == str else k + "=" + str(v) for k, v in Partition.items()])
            df = tdml.DataFrame.from_query(f"""
                SEL *
                FROM {df._table_name}
                WHERE {where}
            """).to_pandas().reset_index()
            results['data'] = df

        return results
