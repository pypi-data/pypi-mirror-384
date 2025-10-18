import uuid
import json
import os
from tdstone2.utils import execute_query, get_partition_datatype,get_connection_username
from tdstone2.tdstone import TDStone
import teradataml as tdml

class Mapper():
    
    def __init__(self, **kwargs):
        """
        Initialize the Mapper object.

        Keyword Args:
            id (str, optional): The ID of the mapper. If not provided, a new ID will be generated.
            mapper_type (str, optional): The type of the mapper. Can take values among 'training', 'scoring', 'feature engineering', 'feature engineering reducer', 'forecasting'.
            id_row (str, optional): [Description of id_row argument].
            id_partition (str, optional): [Description of id_partition argument].
            id_fold (str, optional): [Description of id_fold argument].
            dataset (str, optional): [Description of dataset argument].
            metadata (dict, optional): Additional metadata for the mapper. It will be merged with the default metadata, which contains the current user.
            mapper_repository (str, optional): [Description of mapper_repository argument].
            model_repository (str, optional): [Description of model_repository argument].
            trained_model_repository (str, optional): [Description of model_repository argument].
            schema_name (str, optional): [Description of schema_name argument].
            tdstone (obj, optional): The tdstone object.
        """
        
        self.schema_name       = kwargs.get('schema_name',None)
        self.mapper_repository = kwargs.get('mapper_repository',None)
        self.model_repository  = kwargs.get('model_repository',None)
        self.code_repository   = kwargs.get('code_repository',None)
        self.SEARCHUIFDBPATH   = kwargs.get('SEARCHUIFDBPATH',None)
        
        # If tdstone is provided, update schema_name, mapper_repository, and model_repository accordingly
        tdstone = kwargs.get('tdstone',None)
        if tdstone is not None:
            self.schema_name = tdstone.schema_name
            self.mapper_repository = tdstone.mapper_repository
            self.code_repository = tdstone.code_repository
            self.model_repository = tdstone.model_repository
            self.SEARCHUIFDBPATH = tdstone.SEARCHUIFDBPATH
            
        # Set default values if the corresponding arguments are not provided
        self.dataset = kwargs.get('dataset', None)
        if self.dataset is not None:
            dataset = tdml.DataFrame(self.dataset)
            self.dataset_columns = list(dataset.columns)
            self.types = get_partition_datatype(dataset, columns = self.dataset_columns)
        else:
            self.types = None
        self.id_row = kwargs.get('id_row', None)
        self.id_partition = kwargs.get('id_partition', None)
        self.id_fold = kwargs.get('id_fold', None)
        self.mapper_type = kwargs.get('mapper_type', '')

        
        # Determine if this is a new mapper or an existing one based on the provided id
        self.isnewmapper = True if kwargs.get('id') is None else False
        self.id = str(uuid.uuid4()) if kwargs.get('id') is None else kwargs['id']
        try:
            self.metadata = {'user': os.getlogin()}  # Initialize with the current user
        except Exception as e:
            self.metadata = {}
        self.mapper_table_name = 'TDS_MAPPER_'+self.id.replace('-','_')         
        # If metadata is provided, update the existing metadata with the new values
        if kwargs.get('metadata') is not None:
            self.metadata.update(kwargs['metadata'])
            
        self.on_clause_view_name      = 'TDS_ON_CLAUSE_'+self.mapper_type.upper().replace(' ','_')+'_'+self.id.replace('-','_') 
        self.sto_view_name            = 'TDS_STO_'+self.mapper_type.upper().replace(' ','_')+'_'+self.id.replace('-','_') 
        self.trained_model_repository = kwargs.get('trained_model_repository' , 'TDS_TRAINED_MODELS_'+self.id.replace('-','_'))
        self.scores_repository        = kwargs.get('scores_repository' , 'TDS_SCORES_'+self.id.replace('-','_'))
        self.features_repository = kwargs.get('features_repository', 'TDS_FEATURES_' + self.id.replace('-', '_'))
        self.reduced_feature_repository = kwargs.get('reduced_features_repository', 'TDS_REDUCED_FEATURES_' + self.id.replace('-', '_'))
        self.on_clause_volatile_table_name  = 'TDS_VOLATILE_ON_CLAUSE_'+self.mapper_type.upper().replace(' ','_')+'_'+self.id.replace('-','_') 
            
    def update_metadata(self, metadata):
        """
        Update the metadata for the model.

        Args:
            metadata (dict): New metadata to update.
        """        
        self.metadata.update(metadata)

    def update(self, **kwargs):
        """
        Update the arguments for this mapper like id_row, mapper_table_name, id_partition, id_fold, dataset, mapper_type.

        Keyword Args:
            id_row (str, optional): [Description of id_row argument].
            mapper_table_name (str, optional): [Description of mapper_table_name argument].
            id_partition (str, optional): [Description of id_partition argument].
            id_fold (str, optional): [Description of id_fold argument].
            dataset (str, optional): [Description of dataset argument].
            mapper_type (str, optional): The type of the mapper. Can take values among 'training', 'scoring', 'feature engineering', 'forecasting'.
        """
        # Update the corresponding attributes if the given keyword arguments are provided
        if 'id_row' in kwargs:
            self.id_row = kwargs['id_row']
            
        if 'mapper_table_name' in kwargs:
            self.mapper_table_name = kwargs['mapper_table_name']
                                            
        if 'id_partition' in kwargs:
            self.id_partition = kwargs['id_partition']
            
        if 'id_fold' in kwargs:
            self.id_partition = kwargs['id_fold']  # Check if this line should update id_partition or id_fold, should be clarified   
            
        if 'dataset' in kwargs:
            self.dataset = kwargs['dataset']  
            dataset = tdml.DataFrame(self.dataset)
            self.dataset_columns = list(dataset.columns)
            self.types = get_partition_datatype(dataset, columns=self.dataset_columns)
            
        if 'mapper_type' in kwargs:
            # Check if the provided mapper_type is valid
            valid_mapper_types = ['training', 'scoring', 'feature engineering', 'feature engineering reducer', 'forecasting']
            assert kwargs['mapper_type'] in valid_mapper_types, f"Invalid mapper_type. Should be one of {valid_mapper_types}"
            self.mapper_type = kwargs['mapper_type']                                              
        
    def update_repo(self,mapper_repository=None, schema_name=None, tdstone = None):

        if tdstone is not None:
            schema_name     = tdstone.schema_name
            mapper_repository = tdstone.mapper_repository
        self.schema_name      = schema_name
        self.mapper_repository = mapper_repository       
        

    
    def missing_fields(self):
                # check if there is not None in the important parameters
        if self.mapper_type in ['training','scoring']:
            fields = ['dataset','mapper_table_name','id_row','id_partition','id_fold']
        else:
            fields = ['dataset', 'mapper_table_name', 'id_row', 'id_partition']
        test  = True
        list_missing_fields = []
        
        if self.dataset is None:
            test = False
            list_missing_fields.append('dataset')
            
        if self.mapper_table_name is None:
            test = False
            list_missing_fields.append('mapper_table_name')
            
        if self.id_row is None:
            test = False
            list_missing_fields.append('id_row')
            
        if self.id_partition is None:
            test = False
            list_missing_fields.append('id_partition')

        if self.mapper_type in ['training', 'scoring'] and self.id_fold is None:
            test = False
            list_missing_fields.append('id_fold')     
            

        return test, list_missing_fields
        
        
    @execute_query
    def upload(self):
        """
        Uploads the model to the specified model repository.

        Returns:
            (query, path) where `query` is the SQL query and `path` is the path of the file.
        """        
        
        test, list_missing_fields = self.missing_fields()
    
        if test == False:
            print(f' The mapper cannot be uploaded because the following fields are missing:',list_missing_fields)
            return

        
        queries = []
        
        # creation of the mapper table
        if self.mapper_type in ['training']:
            #types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            sql_types = ', \n'.join([k+' '+v for k,v in self.types.items() if k in self.id_partition.split(',')])
            sql_names = ', \n'.join([k for k,v in self.types.items() if k in self.id_partition.split(',')])
            query_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.mapper_table_name},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    ID_MODEL VARCHAR(36),
                    {sql_types},
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    METADATA JSON(32000), 
                    ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
                )
                PRIMARY INDEX ({self.id_partition});
            """

            queries.append(query_table_creation)
            
            query_trained_model_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.trained_model_repository},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    --CREATION_DATE TIMESTAMP(6) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    TD_TIMEBUCKET BIGINT NOT NULL GENERATED SYSTEM TIMECOLUMN,
                    TD_TIMECODE TIMESTAMP(6) WITH TIME ZONE NOT NULL GENERATED TIMECOLUMN,                    
                    ID_PROCESS VARCHAR(255),
                    {sql_types},
                    ID_MODEL VARCHAR(36),                    
                    ID_TRAINED_MODEL VARCHAR(36),
                    MODEL_TYPE VARCHAR(255),
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    TRAINED_MODEL CLOB
                )
                PRIMARY TIME INDEX (TIMESTAMP(6) WITH TIME ZONE, DATE '2016-01-01', HOURS(1), columns({self.id_partition}))
            """

            query_view_model_pickle = f"""
                REPLACE VIEW {self.schema_name}.V_{self.trained_model_repository}_PICKLE AS
                LOCK ROW FOR ACCESS
                SELECT 
                    TD_TIMECODE,
                    ID_PROCESS,
                    {sql_names},
                    ID_MODEL,
                    ID_TRAINED_MODEL,
                    MODEL_TYPE,
                    STATUS,
                    TRAINED_MODEL
                FROM {self.schema_name}.{self.trained_model_repository}
                WHERE MODEL_TYPE = 'pickle'
            """

            query_view_model_onnx = f"""
                REPLACE VIEW {self.schema_name}.V_{self.trained_model_repository}_ONNX AS
                LOCK ROW FOR ACCESS
                SELECT 
                    TD_TIMECODE,
                    ID_PROCESS,
                    {sql_names},
                    ID_MODEL,
                    ID_TRAINED_MODEL,
                    MODEL_TYPE,
                    STATUS,
                    TO_BYTES(TRAINED_MODEL,'base16') AS TRAINED_MODEL
                FROM {self.schema_name}.{self.trained_model_repository}
                WHERE MODEL_TYPE = 'onnx'
            """

            query_view_byom_catalog = f"""
                    REPLACE VIEW {self.schema_name}.V_{self.trained_model_repository}_BYOM_CATALOG AS
                    SELECT
                        ID_TRAINED_MODEL AS model_id
                    ,   TRAINED_MODEL AS model
                    ,   {sql_names}
                    FROM {self.schema_name}.V_{self.trained_model_repository}_ONNX
                    QUALIFY row_number() OVER (PARTITION BY {sql_names} ORDER BY TD_TIMECODE DESC) = 1
            """

            queries.append(query_trained_model_table_creation)
            queries.append(query_view_model_pickle)
            queries.append(query_view_model_onnx)
            queries.append(query_view_byom_catalog)
            
        elif self.mapper_type in ['scoring']:
            #types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(',')+self.id_row.split(','))
            sql_types = ', \n'.join([k+' '+v for k,v in self.types.items() if k in self.id_partition.split(',')+self.id_row.split(',')])
            
            query_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.mapper_table_name},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    ID_TRAINED_MODEL VARCHAR(36),
                    {sql_types},
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    METADATA JSON(32000), 
                    ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
                )
                PRIMARY INDEX ({self.id_partition});
            """
            queries.append(query_table_creation)

            query_scored_model_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.scores_repository},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    TD_TIMEBUCKET BIGINT NOT NULL GENERATED SYSTEM TIMECOLUMN,
                    TD_TIMECODE TIMESTAMP(6) WITH TIME ZONE NOT NULL GENERATED TIMECOLUMN,                    
                    ID_PROCESS VARCHAR(255),
                    {sql_types},
                    FEATURE_NAME     VARCHAR(20000),
                    FEATURE_VALUE    VARCHAR(2000),
                    FEATURE_TYPE     VARCHAR(20000),                    
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    ID_TRAINED_MODEL VARCHAR(36)
                    
                )
                PRIMARY TIME INDEX (TIMESTAMP(6) WITH TIME ZONE, DATE '2016-01-01', HOURS(1), columns(ID_PROCESS, ID_TRAINED_MODEL, {self.id_partition}, {self.id_row}))
                """

            queries.append(query_scored_model_table_creation)
            
            query_secondary_index = f'CREATE INDEX ({self.id_row}) ON {self.schema_name}.{self.scores_repository}'
        
            queries.append(query_secondary_index)

        elif self.mapper_type in ['feature engineering reducer']:
            # types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            sql_types = ', \n'.join([k + ' ' + v for k, v in self.types.items() if k in self.id_partition.split(',')])

            query_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.mapper_table_name},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    ID_MODEL VARCHAR(36),
                    {sql_types},
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    METADATA JSON(32000), 
                    ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
                )
                PRIMARY INDEX (ID_MODEL, {self.id_partition});
            """

            queries.append(query_table_creation)

            query_trained_model_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.reduced_feature_repository},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    TD_TIMEBUCKET BIGINT NOT NULL GENERATED SYSTEM TIMECOLUMN,
                    TD_TIMECODE TIMESTAMP(6) WITH TIME ZONE NOT NULL GENERATED TIMECOLUMN,                    
                    ID_PROCESS VARCHAR(255),
                    {sql_types},
                    FEATURE_ROW      BIGINT,
                    FEATURE_NAME     VARCHAR(20000),
                    FEATURE_VALUE    VARCHAR(2000),
                    FEATURE_TYPE     VARCHAR(20000),                    
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    ID_MODEL VARCHAR(36)

                )
                PRIMARY TIME INDEX (TIMESTAMP(6) WITH TIME ZONE, DATE '2016-01-01', HOURS(1), columns(ID_PROCESS, ID_MODEL,{self.id_partition}))
                """

            queries.append(query_trained_model_table_creation)

        elif self.mapper_type in ['feature engineering']:
            # types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            sql_types = ', \n'.join([k + ' ' + v for k, v in self.types.items() if k in self.id_partition.split(',')])
            sql_types_row = ', \n'.join([k + ' ' + v for k, v in self.types.items() if k in self.id_row.split(',')])

            query_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.mapper_table_name},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    ID_MODEL VARCHAR(36),
                    {sql_types},
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    METADATA JSON(32000), 
                    ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                    PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
                )
                PRIMARY INDEX (ID_MODEL, {self.id_partition});
            """

            queries.append(query_table_creation)

            query_trained_model_table_creation = f"""
                CREATE MULTISET TABLE {self.schema_name}.{self.features_repository},
                FALLBACK,
                NO BEFORE JOURNAL,
                NO AFTER JOURNAL,
                CHECKSUM = DEFAULT,
                DEFAULT MERGEBLOCKRATIO,
                MAP = TD_MAP1
                (
                    TD_TIMEBUCKET BIGINT NOT NULL GENERATED SYSTEM TIMECOLUMN,
                    TD_TIMECODE TIMESTAMP(6) WITH TIME ZONE NOT NULL GENERATED TIMECOLUMN,                    
                    ID_PROCESS VARCHAR(255),
                    {sql_types},
                    {sql_types_row},
                    FEATURE_NAME     VARCHAR(20000),
                    FEATURE_VALUE    VARCHAR(2000),
                    FEATURE_TYPE     VARCHAR(20000),                    
                    STATUS VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                    ID_MODEL VARCHAR(36)

                )
                PRIMARY TIME INDEX (TIMESTAMP(6) WITH TIME ZONE, DATE '2016-01-01', HOURS(1), columns(ID_PROCESS, ID_MODEL, {self.id_row}))
                """

            queries.append(query_trained_model_table_creation)

            query_secondary_index = f'CREATE INDEX ({self.id_partition}) ON {self.schema_name}.{self.reduced_feature_repository}'

            queries.append(query_secondary_index)

        # here insert or update in the catalog
        if self.isnewmapper:
            if self.mapper_type in ['training']:
                # this is a new insert
                query = f"""CURRENT VALIDTIME INSERT INTO {self.schema_name}.{self.mapper_repository}
                (ID, MAPPER_TYPE, TABLE_NAME, CODE_REPOSITORY, MODEL_REPOSITORY,TRAINED_MODEL_REPOSITORY, DATASET_OBJECT,COL_ID_ROW,COL_ID_PARTITION,COL_FOLD,ON_CLAUSE_VIEW, STO_VIEW,METADATA)
                 VALUES
                ('{self.id}',
                 '{self.mapper_type}',
                 '{self.mapper_table_name}',
                 '{self.code_repository}',
                 '{self.model_repository}',
                 '{self.trained_model_repository}',
                 '{self.dataset}',
                 '{self.id_row}',
                 '{self.id_partition}',
                 '{self.id_fold}',
                 '{self.on_clause_view_name}',
                 '{self.sto_view_name}',
                 '{json.dumps(self.metadata).replace("'", '"')}');
                """
            elif  self.mapper_type in ['scoring']:
                # this is a new insert
                query = f"""CURRENT VALIDTIME INSERT INTO {self.schema_name}.{self.mapper_repository}
                (ID, MAPPER_TYPE, TABLE_NAME, CODE_REPOSITORY, MODEL_REPOSITORY,TRAINED_MODEL_REPOSITORY, SCORES_REPOSITORY, DATASET_OBJECT,COL_ID_ROW,COL_ID_PARTITION,COL_FOLD,ON_CLAUSE_VIEW, STO_VIEW,METADATA)
                 VALUES
                ('{self.id}',
                 '{self.mapper_type}',
                 '{self.mapper_table_name}',
                 '{self.code_repository}',
                 '{self.model_repository}',
                 '{self.trained_model_repository}',
                 '{self.scores_repository}',
                 '{self.dataset}',
                 '{self.id_row}',
                 '{self.id_partition}',
                 '{self.id_fold}',
                 '{self.on_clause_view_name}',
                 '{self.sto_view_name}',
                 '{json.dumps(self.metadata).replace("'", '"')}');
                """
            elif self.mapper_type in ['feature engineering','feature engineering reducer']:
                # this is a new insert
                if self.mapper_type == 'feature engineering':
                    feature_repo_name = self.features_repository
                else:
                    feature_repo_name = self.reduced_feature_repository

                query = f"""CURRENT VALIDTIME INSERT INTO {self.schema_name}.{self.mapper_repository}
                (ID, MAPPER_TYPE, TABLE_NAME, CODE_REPOSITORY, MODEL_REPOSITORY,FEATURE_REPOSITORY, DATASET_OBJECT,COL_ID_ROW,COL_ID_PARTITION,ON_CLAUSE_VIEW, STO_VIEW,METADATA)
                 VALUES
                ('{self.id}',
                 '{self.mapper_type}',
                 '{self.mapper_table_name}',
                 '{self.code_repository}',
                 '{self.model_repository}',
                 '{feature_repo_name}',
                 '{self.dataset}',
                 '{self.id_row}',
                 '{self.id_partition}',
                 '{self.on_clause_view_name}',
                 '{self.sto_view_name}',
                 '{json.dumps(self.metadata).replace("'", '"')}');
                """
            self.isnewmapper = False
            
        else:
            if self.mapper_type in ['training','forecast']:
                query = f"""
                CURRENT VALIDTIME UPDATE {self.schema_name}.{self.mapper_repository}
                SET 
                    TABLE_NAME = '{self.mapper_table_name}'
                ,   MAPPER_TYPE = '{self.mapper_type}'
                ,   CODE_REPOSITORY = '{self.code_repository}'
                ,   MODEL_REPOSITORY = '{self.model_repository}'
                ,   TRAINED_MODEL_REPOSITORY = '{self.trained_model_repository}'
                ,   SCORES_REPOSITORY = '{self.scores_repository}'
                ,   DATASET_OBJECT = '{self.dataset}'
                ,   COL_ID_ROW = '{self.id_row}'
                ,   COL_ID_PARTITION = '{self.id_partition}'
                ,   COL_FOLD = '{self.id_fold}'
                ,   ON_CLAUSE_VIEW = '{self.on_clause_view_name}'
                ,   STO_VIEW = '{self.sto_view_name}'
                ,   METADATA = '{json.dumps(self.metadata).replace("'", '"')}'
                WHERE ID = '{self.id}';
                """
            elif self.mapper_type in ['feature engineering','feature engineering reducer']:
                if self.mapper_type == 'feature engineering':
                    feature_repo_name = self.features_repository
                else:
                    feature_repo_name = self.reduced_feature_repository

                query = f"""
                CURRENT VALIDTIME UPDATE {self.schema_name}.{self.mapper_repository}
                SET 
                    TABLE_NAME = '{self.mapper_table_name}'
                ,   MAPPER_TYPE = '{self.mapper_type}'
                ,   CODE_REPOSITORY = '{self.code_repository}'
                ,   MODEL_REPOSITORY = '{self.model_repository}'
                ,   FEATURE_REPOSITORY = '{feature_repo_name}'
                ,   SCORES_REPOSITORY = '{self.scores_repository}'
                ,   DATASET_OBJECT = '{self.dataset}'
                ,   COL_ID_ROW = '{self.id_row}'
                ,   COL_ID_PARTITION = '{self.id_partition}'
                ,   ON_CLAUSE_VIEW = '{self.on_clause_view_name}'
                ,   STO_VIEW = '{self.sto_view_name}'
                ,   METADATA = '{json.dumps(self.metadata).replace("'", '"')}'
                WHERE ID = '{self.id}';
                """
        queries.append(query)
        print(f'registration of mapper with id = {self.id}')
        print(f'creation of dedicated mapper table : {self.schema_name}.{self.mapper_table_name}')

       
        return queries
    
    @execute_query
    def remove(self):

        
        return []
               
    def download(self, id, mapper_repository=None, schema_name=None, tdstone = None, mapper_type = None):
        
        if tdstone is not None:
            self.schema_name       = tdstone.schema_name
            self.mapper_repository = tdstone.mapper_repository
            self.SEARCHUIFDBPATH   = tdstone.SEARCHUIFDBPATH
        if mapper_repository is not None and schema_name is not None:
            self.schema_name       = schema_name
            self.mapper_repository = mapper_repository
            
        self.mapper_type = mapper_type
        
        query = f"""
        CURRENT VALIDTIME
        SELECT
             ID
        ,    MAPPER_TYPE
        ,    TABLE_NAME
        ,    CODE_REPOSITORY
        ,    MODEL_REPOSITORY
        ,    TRAINED_MODEL_REPOSITORY
        ,    FEATURE_REPOSITORY
        ,    SCORES_REPOSITORY
        ,    DATASET_OBJECT
        ,    COL_ID_ROW 
        ,    COL_ID_PARTITION
        ,    COL_FOLD
        ,    ON_CLAUSE_VIEW
        ,    STO_VIEW
        ,    METADATA 
        FROM {self.schema_name}.{self.mapper_repository}
        WHERE ID = '{id}'
        """
        
        df = tdml.DataFrame.from_query(query).to_pandas()
        
        if df.shape[0] != 1:
            print(f'error there is {df.shape[0]} rows corresponding to id = {id}')
        else:
            self.code_repository  = df.CODE_REPOSITORY.values[0]
            self.model_repository  = df.MODEL_REPOSITORY.values[0]
            self.trained_model_repository  = df.TRAINED_MODEL_REPOSITORY.values[0]
            self.scores_repository = df.SCORES_REPOSITORY.values[0]

            self.dataset           = df.DATASET_OBJECT.values[0]
            self.mapper_type       = df.MAPPER_TYPE.values[0]
            self.mapper_table_name = df.TABLE_NAME.values[0]
            if self.mapper_type == 'feature engineering':
                self.features_repository = df.FEATURE_REPOSITORY.values[0]
            elif self.mapper_type == 'feature engineering reducer':
                self.reduced_feature_repository = df.FEATURE_REPOSITORY.values[0]

            # Determine if this is a new mapper or an existing one based on the provided id
            self.isnewmapper       = False
            self.id                = df.ID.values[0]
            self.metadata          = eval(df.METADATA.values[0])
            self.on_clause_view_name = df.ON_CLAUSE_VIEW.values[0]
            self.sto_view_name       = df.STO_VIEW.values[0]
            
            self.id_row              = df.COL_ID_ROW.values[0]
            self.id_partition        = df.COL_ID_PARTITION.values[0]
            self.id_fold             = df.COL_FOLD.values[0]

            dataset = tdml.DataFrame(self.dataset)
            self.dataset_columns = list(dataset.columns)
            self.types = get_partition_datatype(dataset, columns=self.dataset_columns)
 
    def list_mapping(self,current_only=True, active_only = True):
        """
        List the mapping in the TDStone system.

        Args:
            with_full_script (bool, optional): If True, the full script is listed. Defaults to False.
            current_only (bool, optional): If True, only the current version is listed. Defaults to True.

        Returns:
            DataFrame: A DataFrame with the model details.
        """        
        if current_only:
            query = "CURRENT VALIDTIME \n"
        else:
            query = ''
            
        query = query + 'SELECT  * \n'
                
        query = query + f'\n FROM {self.schema_name}.{self.mapper_table_name}'
        
        if active_only:
            query = query + "\n WHERE STATUS = 'enabled'"
            
        
        return tdml.DataFrame.from_query(query)

    @execute_query
    def reset_mapping(self):
        query = f'DELETE {self.schema_name}.{self.mapper_table_name}'
        return query
    
    @execute_query
    def fill_mapping_full(self, model_id):
        
        if self.mapper_type in ['training','feature engineering','forecasting','feature engineering reducer']:
            sub_query = f"""
            SELECT
                A.ID
            ,   {','.join(['B.'+x for x in self.id_partition.split(',')])}
            ,   'enabled' AS STATUS
            FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) A
            , (
               SELECT DISTINCT {self.id_partition}
               FROM {self.dataset}
            ) B
            WHERE A.ID = '{model_id}'        
            """


            query = f"""
            CURRENT VALIDTIME
            INSERT INTO {self.schema_name}.{self.mapper_table_name}
            (ID_MODEL, {self.id_partition}, STATUS)
            SELECT
                AAA.ID
            ,   {','.join(['AAA.'+x for x in self.id_partition.split(',')])}
            ,   AAA.STATUS
            FROM (
                SELECT 
                    AA.*
                ,   BB.ID_MODEL AS EXISTING_ID
                FROM ({sub_query}) AA
                LEFT JOIN {self.schema_name}.{self.mapper_table_name} BB
                ON 
                -- AA.ID = BB.ID_MODEL AND
                {'AND '.join(['AA.'+x+'=BB.'+x for x in self.id_partition.split(',')])}
                WHERE EXISTING_ID IS NULL
            ) AAA
            """
            return query
        elif self.mapper_type in ['scoring']:
            join_clause = 'AND '.join(['B.'+x+'=CC.'+x for x in self.id_partition.split(',')])
            
            sub_query = f"""
            SELECT
                A.ID
            ,   {','.join(['B.'+x for x in self.id_partition.split(',')])}
            ,   'enabled' AS STATUS
            ,   CC.ID_TRAINED_MODEL
            FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) A
            , (
               SELECT DISTINCT {self.id_partition}
               FROM {self.dataset}
            ) B
            , (
                SEL {self.id_partition}, ID_MODEL, ID_TRAINED_MODEL, TRAINED_MODEL, MODEL_TYPE
                FROM {self.schema_name}.{self.trained_model_repository}
                QUALIFY ROW_NUMBER() OVER (PARTITION BY {self.id_partition}, ID_MODEL ORDER BY TD_TIMECODE DESC) = 1
               ) CC
            WHERE A.ID = '{model_id}' AND A.ID = CC.ID_MODEL    
            AND {join_clause}
            """

            query = f"""
            CURRENT VALIDTIME
            INSERT INTO {self.schema_name}.{self.mapper_table_name}
            (ID_TRAINED_MODEL, {self.id_partition}, STATUS)
            SELECT
                AAA.ID_TRAINED_MODEL
            ,   {','.join(['AAA.'+x for x in self.id_partition.split(',')])}
            ,   AAA.STATUS
            FROM (
                SELECT 
                    AA.*
                ,   BB.ID_TRAINED_MODEL AS EXISTING_ID
                FROM ({sub_query}) AA
                LEFT JOIN {self.schema_name}.{self.mapper_table_name} BB
                ON 
                -- AA.ID = BB.ID_TRAINED_MODEL AND
                {'AND '.join(['AA.'+x+'=BB.'+x for x in self.id_partition.split(',')])}
                WHERE EXISTING_ID IS NULL
            ) AAA
            """

            query_update = f"""
            CURRENT VALIDTIME
            UPDATE {self.schema_name}.{self.mapper_table_name}
            FROM (
                SELECT
                    AAA.ID_TRAINED_MODEL
                ,   {','.join(['AAA.'+x for x in self.id_partition.split(',')])}
                ,   AAA.STATUS
                FROM (
                    SELECT 
                        AA.*
                    ,   BB.ID_TRAINED_MODEL AS EXISTING_ID
                    FROM ({sub_query}) AA
                    LEFT JOIN {self.schema_name}.{self.mapper_table_name} BB
                    ON 
                    -- AA.ID = BB.ID_TRAINED_MODEL AND
                    {'AND '.join(['AA.'+x+'=BB.'+x for x in self.id_partition.split(',')])}
                    WHERE EXISTING_ID IS NOT NULL
                ) AAA            
            ) UPDATED_MAPPING
            SET
                ID_TRAINED_MODEL = UPDATED_MAPPING.ID_TRAINED_MODEL
            WHERE
                {'AND '.join([self.schema_name+'.'+self.mapper_table_name+'.'+x+'=UPDATED_MAPPING.'+x for x in self.id_partition.split(',')])}
            """
            return [query, query_update]
        
    @execute_query
    def enable_exiting_partitions(self, model_id, new_status='enabled'):
        
        sub_query = f"""
        SELECT
            A.ID
        ,   {','.join(['B.'+x for x in self.id_partition.split(',')])}
        ,   'enabled' AS STATUS
        FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) A
        , (
           SELECT DISTINCT {self.id_partition}
           FROM {self.dataset}
        ) B
        WHERE A.ID = '{model_id}'        
        """
        
        query_update = f"""
        CURRENT VALIDTIME
        UPDATE {self.schema_name}.{self.mapper_table_name}
        FROM (
            SELECT
                AAA.ID
            ,   {','.join(['AAA.'+x for x in self.id_partition.split(',')])}
            FROM (
                SELECT 
                    AA.*
                ,   BB.ID_MODEL AS EXISTING_ID
                FROM ({sub_query}) AA
                LEFT JOIN (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.mapper_table_name}) BB
                ON AA.ID = BB.ID_MODEL AND
                {'AND '.join(['AA.'+x+'=BB.'+x for x in self.id_partition.split(',')])}
                WHERE EXISTING_ID IS NOT NULL
            ) AAA        
        ) UPDATED_MAPPING
        SET
            STATUS = '{new_status}'
        WHERE
            ID_MODEL = UPDATED_MAPPING.ID AND
           {'AND '.join([f'{self.schema_name}.{self.mapper_table_name}.'+x+'=UPDATED_MAPPING.'+x for x in self.id_partition.split(',')])}
        """

        return query_update
    
    @execute_query
    def create_on_clause(self,fold=None):
        
        #self.on_clause_view_name = 'TDS_ON_CLAUSE_'self.ma+self.id.replace('-','_')
        
        #dataset = tdml.DataFrame(self.dataset)
        dataset_col_sql = ', \n'.join(['A.'+x for x in self.dataset_columns])
        
        
        
        if self.mapper_type in ['training','forecasting']:
            # view on clause
            query = f"""
                REPLACE VIEW {self.schema_name}.{self.on_clause_view_name} AS
                WITH LEFT_MAPPED_TABLE AS (
                    SEL 
                        A.*
                    ,	ROW_NUMBER() OVER (PARTITION BY 
                                            {','.join(['A.'+x for x in self.id_partition.split(',')] +
                                            ['MAPPER.ID_MODEL'] + 
                                            ['A.'+x for x in self.id_fold.split(',')])} 
                                            ORDER BY {','.join(['A.'+x for x in self.id_row.split(',')])}) AS STO_FAKE_ROW
                    ,	MAPPER.ID_MODEL AS STO_MODEL_ID
                    FROM {self.dataset} A
                    ,	(CURRENT VALIDTIME SEL * FROM {self.schema_name}.{self.mapper_table_name}) MAPPER
                    WHERE {'AND '.join(['A.'+x+'=MAPPER.'+x for x in self.id_partition.split(',')])}
                    AND MAPPER.STATUS = 'enabled'
                )
                SEL
                    LEFT_MAPPED_TABLE.*
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_row}' END AS STO_ROW_ID
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_partition}' END AS STO_PARTITION_ID
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_fold}' END AS STO_FOLD_ID
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.CODE_TYPE END AS STO_CODE_TYPE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN TRANSLATE(FROM_BYTES(CURRENT_MODELS.CODE, 'base64m') USING UNICODE_TO_LATIN) END AS STO_CODE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN REGEXP_REPLACE(REGEXP_REPLACE(CAST(CURRENT_MODELS.ARGUMENTS AS VARCHAR(32000)),'([\r|\t])', ''),'[\s+]', ' ') END AS ARGUMENTS
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CAST(CURRENT_TIME AS TIMESTAMP(6) WITH TIME ZONE) END AS EXECUTION_TIME
                FROM
                    LEFT_MAPPED_TABLE
                LEFT JOIN (
                    SELECT
                      AA.ID
                    , AA.ID_CODE
                    , AA.ARGUMENTS
                    , BB.CODE_TYPE
                    , BB.CODE
                    FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) AA
                    INNER JOIN (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.code_repository}) BB
                    ON AA.ID_CODE = BB.ID
                    WHERE BB.CODE_TYPE = 'python class'
                ) CURRENT_MODELS
                ON LEFT_MAPPED_TABLE.STO_MODEL_ID = CURRENT_MODELS.ID   
            """
            
            if fold is not None:
                query = query + f"\n WHERE LEFT_MAPPED_TABLE.{self.id_fold} = '{fold}'"

        elif self.mapper_type in ['feature engineering', 'feature engineering reducer']:
            # view on clause
            query = f"""
                REPLACE VIEW {self.schema_name}.{self.on_clause_view_name} AS
                WITH LEFT_MAPPED_TABLE AS (
                    SEL 
                        A.*
                    ,	ROW_NUMBER() OVER (PARTITION BY 
                                            {','.join(['A.' + x for x in self.id_partition.split(',')] +
                                                      ['MAPPER.ID_MODEL'])} 
                                            ORDER BY {','.join(['A.' + x for x in self.id_row.split(',')])}) AS STO_FAKE_ROW
                    ,	MAPPER.ID_MODEL AS STO_MODEL_ID
                    FROM {self.dataset} A
                    ,	(CURRENT VALIDTIME SEL * FROM {self.schema_name}.{self.mapper_table_name}) MAPPER
                    WHERE {'AND '.join(['A.' + x + '=MAPPER.' + x for x in self.id_partition.split(',')])}
                    AND MAPPER.STATUS = 'enabled'
                )
                SEL
                    LEFT_MAPPED_TABLE.*
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_row}' END AS STO_ROW_ID
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_partition}' END AS STO_PARTITION_ID
                 ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.CODE_TYPE END AS STO_CODE_TYPE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN TRANSLATE(FROM_BYTES(CURRENT_MODELS.CODE, 'base64m') USING UNICODE_TO_LATIN) END AS STO_CODE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN REGEXP_REPLACE(REGEXP_REPLACE(CAST(CURRENT_MODELS.ARGUMENTS AS VARCHAR(32000)),'([\r|\t])', ''),'[\s+]', ' ') END AS ARGUMENTS
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CAST(CURRENT_TIME AS TIMESTAMP(6) WITH TIME ZONE) END AS EXECUTION_TIME
                FROM
                    LEFT_MAPPED_TABLE
                LEFT JOIN (
                    SELECT
                      AA.ID
                    , AA.ID_CODE
                    , AA.ARGUMENTS
                    , BB.CODE_TYPE
                    , BB.CODE
                    FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) AA
                    INNER JOIN (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.code_repository}) BB
                    ON AA.ID_CODE = BB.ID
                    WHERE BB.CODE_TYPE = 'python class'
                ) CURRENT_MODELS
                ON LEFT_MAPPED_TABLE.STO_MODEL_ID = CURRENT_MODELS.ID   
            """


        elif self.mapper_type in ['scoring']:
            # view on clause
            
            query = f"""
                REPLACE VIEW {self.schema_name}.{self.on_clause_view_name} AS
                WITH LEFT_MAPPED_TABLE AS (
                    SEL 
                        A.*
                    ,	ROW_NUMBER() OVER (PARTITION BY 
                                        {','.join(['A.'+x for x in self.id_partition.split(',')] + 
                                        ['MAPPER.ID_TRAINED_MODEL'] + 
                                        ['A.'+x for x in self.id_fold.split(',')])} 
                                        ORDER BY {','.join(['A.'+x for x in self.id_row.split(',')])}) AS STO_FAKE_ROW
                    ,	MAPPER.ID_TRAINED_MODEL AS STO_MODEL_ID
                    FROM {self.dataset} A
                    ,	(CURRENT VALIDTIME SEL * FROM {self.schema_name}.{self.mapper_table_name}) MAPPER
                    WHERE {'AND '.join(['A.'+x+'=MAPPER.'+x for x in self.id_partition.split(',')])}
                    AND MAPPER.STATUS = 'enabled'
                )
                SEL
                    LEFT_MAPPED_TABLE.*
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_row}' END AS STO_ROW_ID
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_partition}' END AS STO_PARTITION_ID
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN '{self.id_fold}' END AS STO_FOLD_ID
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.CODE_TYPE END AS STO_CODE_TYPE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN TRANSLATE(FROM_BYTES(CURRENT_MODELS.CODE, 'base64m') USING UNICODE_TO_LATIN) END AS STO_CODE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN REGEXP_REPLACE(REGEXP_REPLACE(CAST(CURRENT_MODELS.ARGUMENTS AS VARCHAR(32000)),'([\r|\t])', ''),'[\s+]', ' ') END AS ARGUMENTS
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.ID_TRAINED_MODEL END AS STO_ID_TRAINED_MODEL
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.MODEL_TYPE END AS STO_MODEL_TYPE
                ,	CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CURRENT_MODELS.TRAINED_MODEL END AS STO_TRAINED_MODEL
                ,   CASE WHEN LEFT_MAPPED_TABLE.STO_FAKE_ROW = 1 THEN CAST(CURRENT_TIME AS TIMESTAMP(6) WITH TIME ZONE) END AS EXECUTION_TIME
                FROM
                    LEFT_MAPPED_TABLE
                LEFT JOIN (
                    SELECT
                      AA.ID
                    , AA.ID_CODE
                    , AA.ARGUMENTS
                    , BB.CODE_TYPE
                    , BB.CODE
                    , {','.join(['CC.'+x for x in self.id_partition.split(',')])}
                    , CC.ID_TRAINED_MODEL
                    , CC.TRAINED_MODEL
                    , CC.MODEL_TYPE
                    FROM (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.model_repository}) AA
                    INNER JOIN (CURRENT VALIDTIME SELECT * FROM {self.schema_name}.{self.code_repository}) BB
                    ON AA.ID_CODE = BB.ID
                    INNER JOIN {self.schema_name}.V_{self.trained_model_repository}_PICKLE CC
                    ON AA.ID = CC.ID_MODEL
                    WHERE BB.CODE_TYPE = 'python class' --AND CC.MODEL_TYPE = 'pickle'
                ) CURRENT_MODELS
                ON LEFT_MAPPED_TABLE.STO_MODEL_ID = CURRENT_MODELS.ID_TRAINED_MODEL   
            """
            if fold is not None:
                query = query + f"\n WHERE LEFT_MAPPED_TABLE.{self.id_fold} = '{fold}'"
                
        print(f'creation of the on clause view {self.schema_name}.{self.on_clause_view_name}')
        return query
    
    def generate_sto_query(self):
        
        dataset = tdml.DataFrame(self.dataset)
        dataset_col_sql = ', \n'.join(['A.'+x for x in dataset.columns])
        partition_col_sql = ', \n'.join(['A.'+x for x in self.id_partition.split(',')])
        id_col_sql = ', \n'.join(['A.'+x for x in self.id_row.split(',')])

        
        if self.mapper_type == 'training':
            #types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            output_sql = ', \n'.join([f"'{k} {v}'" for k,v in self.types.items() if k in self.id_partition.split(',')])
            # view on clause
            query = f"""
                    SELECT 
                        EXECUTION_TIME as TD_TIMECODE
                    ,    '{self.sto_view_name}' as ID_PROCESS
                    ,   {self.id_partition}
                    ,   ID_MODEL
                    ,   ID_TRAINED_MODEL
                    ,   MODEL_TYPE
                    ,   STATUS
                    ,   TRAINED_MODEL
                    FROM Script(
                        ON {self.schema_name}.{self.on_clause_view_name}
                        PARTITION BY {self.id_partition}
                        -- ,	STO_MODEL_ID ,{self.id_fold}
                        ORDER BY {self.id_row}
                        SCRIPT_COMMAND(
                            'tdpython3 ./{self.SEARCHUIFDBPATH}/tds_training.py  | awk -F"\t" "NF == {6+len(self.id_partition.split(','))}"'
                        )
                        RETURNS(
                                   {output_sql}
                                ,	'ID_MODEL         VARCHAR(36)'
                                ,	'ID_TRAINED_MODEL VARCHAR(36)'
                                ,	'MODEL_TYPE       VARCHAR(255)'
                                ,	'STATUS           VARCHAR(20000)'
                                ,	'TRAINED_MODEL    CLOB'
                                ,   'EXECUTION_TIME   TIMESTAMP(6) WITH TIME ZONE'
                        )
                        CHARSET('LATIN')
                    ) AS d
                    """
        elif self.mapper_type == 'feature engineering reducer':
            # types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            output_sql = ', \n'.join(
                [f"'{k} {v}'" for k, v in self.types.items() if k in self.id_partition.split(',')])
            # view on clause
            query = f"""
                    SELECT 
                        EXECUTION_TIME as TD_TIMECODE
                    ,    '{self.sto_view_name}' as ID_PROCESS
                    ,   {self.id_partition}
                    ,   FEATURE_ROW
                    ,   FEATURE_NAME
                    ,   FEATURE_VALUE
                    ,   FEATURE_TYPE
                    ,   STATUS
                    ,   ID_MODEL
                    FROM Script(
                        ON {self.schema_name}.{self.on_clause_view_name}
                        PARTITION BY {self.id_partition}
                        -- ,	STO_MODEL_ID ,{self.id_fold}
                        ORDER BY {self.id_row}
                        SCRIPT_COMMAND(
                            'tdpython3 ./{self.SEARCHUIFDBPATH}/tds_feature_engineering_reducer.py  | awk -F"\t" "NF == {7 + len(self.id_partition.split(','))}"'
                        )
                        RETURNS(
                                {output_sql}
                            ,   'FEATURE_ROW      BIGINT'
                            ,	'FEATURE_NAME     VARCHAR(2000)'
                            ,	'FEATURE_VALUE    VARCHAR(2000)'
                            ,	'FEATURE_TYPE     VARCHAR(20000)'
                            ,	'STATUS           VARCHAR(20000)'
                            ,   'ID_MODEL         VARCHAR(36)'
                            ,   'EXECUTION_TIME   TIMESTAMP(6) WITH TIME ZONE'
                        )
                        CHARSET('LATIN')
                    ) AS d
                    """
        elif self.mapper_type == 'feature engineering':
            # types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
            output_sql = ', \n'.join(
                [f"'{k} {v}'" for k, v in self.types.items() if k in self.id_partition.split(',')+self.id_row.split(',')])
            # view on clause
            query = f"""
                    SELECT 
                         EXECUTION_TIME as TD_TIMECODE
                    ,    '{self.sto_view_name}' as ID_PROCESS
                    ,   {self.id_partition}
                    ,   {self.id_row}
                    ,   FEATURE_NAME
                    ,   FEATURE_VALUE
                    ,   FEATURE_TYPE
                    ,   STATUS
                    ,   ID_MODEL
                    FROM Script(
                        ON {self.schema_name}.{self.on_clause_view_name}
                        PARTITION BY {self.id_partition}
                        -- ,	STO_MODEL_ID ,{self.id_fold}
                        ORDER BY {self.id_row}
                        SCRIPT_COMMAND(
                            'tdpython3 ./{self.SEARCHUIFDBPATH}/tds_feature_engineering.py  | awk -F"\t" "NF == {6 + len(self.id_partition.split(',')+self.id_row.split(','))}"'
                        )
                        RETURNS(
                                {output_sql}
                            ,	'FEATURE_NAME     VARCHAR(2000)'
                            ,	'FEATURE_VALUE    VARCHAR(2000)'
                            ,	'FEATURE_TYPE     VARCHAR(20000)'
                            ,	'STATUS           VARCHAR(20000)'
                            ,   'ID_MODEL         VARCHAR(36)'
                            ,   'EXECUTION_TIME   TIMESTAMP(6) WITH TIME ZONE'
                        )
                        CHARSET('LATIN')
                    ) AS d
                    """
        elif self.mapper_type in ['scoring']:
            #types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(',')+self.id_row.split(','))
            output_sql = ', \n'.join([f"'{k} {v}'" for k,v in self.types.items() if k in self.id_partition.split(',')+self.id_row.split(',')])
            
            username = get_connection_username() # for VOLATILE table access
            
            query = f"""
                    SELECT
                        EXECUTION_TIME as TD_TIMECODE
                    ,   '{self.sto_view_name}' as ID_PROCESS
                    ,   {self.id_partition}
                    ,   {self.id_row}
                    ,   FEATURE_NAME
                    ,   FEATURE_VALUE
                    ,   FEATURE_TYPE
                    ,   STATUS
                    ,   ID_TRAINED_MODEL
                    FROM Script(
                        --ON {self.schema_name}.{self.on_clause_view_name}
                        ON {username}.{self.on_clause_volatile_table_name}
                        PARTITION BY {self.id_partition}
                         --,  STO_MODEL_ID ,{self.id_fold}
                        ORDER BY {self.id_row}
                        SCRIPT_COMMAND(
                            'tdpython3 ./{self.SEARCHUIFDBPATH}/tds_scoring.py  | awk -F"\t" "NF == {8+len(self.id_partition.split(','))+len(self.id_row.split(','))}"'
                        )
                        RETURNS(
                                   {output_sql}
                                ,	'FEATURE_NAME     VARCHAR(2000)'
                                ,	'FEATURE_VALUE    VARCHAR(2000)'
                                ,	'FEATURE_TYPE     VARCHAR(20000)'
                                ,	'STATUS           VARCHAR(20000)'
                                ,   'ID_MODEL         VARCHAR(36)'
                                ,	'MODEL_TYPE       VARCHAR(255)'
                                ,	'ID_TRAINED_MODEL VARCHAR(36)'
                                ,   'EXECUTION_TIME   TIMESTAMP(6) WITH TIME ZONE'
                        )
                        CHARSET('LATIN')
                    ) AS d
                    """
            
        return query
    
    def create_volatile_table_on_clause(self):
        print(f'creation of the volatile table on on clause view {self.schema_name}.{self.sto_view_name}')
        tdml.DataFrame(tdml.in_schema(self.schema_name,self.on_clause_view_name)).to_sql(
            temporary=True,
            table_name = self.on_clause_volatile_table_name,
            if_exists='replace',
            primary_index = self.id_partition.split(','))
        return
    
    @execute_query
    def create_sto_view(self):
        
        
        
        #dataset = tdml.DataFrame(self.dataset)
        dataset_col_sql = ', \n'.join(['A.'+x for x in self.dataset_columns])
        partition_col_sql = ', \n'.join(['A.'+x for x in self.id_partition.split(',')])
        id_col_sql = ', \n'.join(['A.'+x for x in self.id_row.split(',')])
        #types = get_partition_datatype(tdml.DataFrame(self.dataset),self.id_partition.split(','))
        output_sql = ', \n'.join([f"'{k} {v}'" for k,v in self.types.items() if k in self.id_partition.split(',')])
        
        # view on clause
        query = f"""
                REPLACE VIEW {self.schema_name}.{self.sto_view_name} AS
                -- SET SESSION SEARCHUIFDBPATH = "{self.SEARCHUIFDBPATH}"
                {self.generate_sto_query()}
                    """
        session = f'SET SESSION SEARCHUIFDBPATH = "{self.SEARCHUIFDBPATH}";'
        print(f'creation of the sto view {self.schema_name}.{self.sto_view_name}')
        return [session,query]    
    
    @execute_query
    def execute_mapper(self):

        session = f'SET SESSION SEARCHUIFDBPATH = "{self.SEARCHUIFDBPATH}";'
        query   = ''
        if self.mapper_type == 'training':
            query = f"""
            INSERT INTO {self.schema_name}.{self.trained_model_repository}
            (TD_TIMECODE, ID_PROCESS, {self.id_partition}, ID_MODEL, ID_TRAINED_MODEL, MODEL_TYPE, STATUS, TRAINED_MODEL)
            {self.generate_sto_query()}
            WHERE STATUS LIKE '%successful%'
            """

            print(f'insert trained models in {self.schema_name}.{self.trained_model_repository}')
            print(f'- access pickle models in {self.schema_name}.V_{self.trained_model_repository}_PICKLE')
            print(f'- access  onnx  models in {self.schema_name}.V_{self.trained_model_repository}_ONNX')
            print(f'- onnx byom catalog    in {self.schema_name}.V_{self.trained_model_repository}_BYOM_CATALOG')

        if self.mapper_type == 'feature engineering reducer':
            query = f"""
            INSERT INTO {self.schema_name}.{self.reduced_feature_repository}
            (TD_TIMECODE, ID_PROCESS, {self.id_partition}, FEATURE_ROW, FEATURE_NAME, FEATURE_VALUE, FEATURE_TYPE, STATUS, ID_MODEL)
            {self.generate_sto_query()}
            WHERE STATUS LIKE '%successful%'
            """

            print(f'insert features in {self.schema_name}.{self.reduced_feature_repository}')

        if self.mapper_type == 'feature engineering':
            query = f"""
            INSERT INTO {self.schema_name}.{self.features_repository}
            (TD_TIMECODE, ID_PROCESS, {self.id_partition}, {self.id_row}, FEATURE_NAME, FEATURE_VALUE, FEATURE_TYPE, STATUS, ID_MODEL)
            {self.generate_sto_query()}
            WHERE STATUS LIKE '%successful%'
            """

            print(f'insert features in {self.schema_name}.{self.features_repository}')

        if self.mapper_type == 'scoring':
            
            # materialize the ON_CLAUSE in a volatile table
            self.create_volatile_table_on_clause()
            
            # manage temporal
            query = f"""
            INSERT INTO {self.schema_name}.{self.scores_repository}
            (TD_TIMECODE, ID_PROCESS, {self.id_partition},{self.id_row}, FEATURE_NAME, FEATURE_VALUE, FEATURE_TYPE, STATUS, ID_TRAINED_MODEL)
            {self.generate_sto_query()}
            WHERE STATUS LIKE '%successful%'
            """

            print(f'insert scores in {self.schema_name}.{self.scores_repository}')            
        return [session, query]
        
        queries.append(query_table_creation)