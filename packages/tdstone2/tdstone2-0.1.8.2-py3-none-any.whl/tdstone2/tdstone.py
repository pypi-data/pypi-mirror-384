from tdstone2.utils import execute_query, retry_on_upstream_timeout
import teradataml as tdml
from tqdm import tqdm
import os
import logging
import os
import logging
from datetime import datetime
from tqdm import tqdm

# Setting up the logger to include timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

file_list = ['tds_feature_engineering',
             'tds_feature_engineering_reducer',
             'tds_training',
             'tds_scoring',
             'tds_training_old',
             'tds_scoring_old',
             'tds_feature_engineering_jsonoutput',
             'tds_vector_embedding',
             'tds_vector_embedding_lake',
             'tds_seq2seq'
             ]
this_dir, this_filename = os.path.split(__file__)

class TDStone():
    """
    Class to manage the TDStone system.
    """
    def __init__(self, schema_name, **kwargs):
        """
        Initialize the TDStone object.
        ...
        """        
        self.schema_name      = schema_name
        self.SEARCHUIFDBPATH  = kwargs.get('SEARCHUIFDBPATH', schema_name)
        self.oaf_env          = kwargs.get('oaf_env', None)
        self.code_repository  = kwargs.get('code_repository', 'TDS_CODE_REPOSITORY')
        self.model_repository = kwargs.get('model_repository', 'TDS_MODEL_REPOSITORY')
        self.trained_model_repository = kwargs.get('trained_model_repository', 'TDS_TRAINED_MODEL_REPOSITORY')
        self.mapper_repository = kwargs.get('mapper_repository', 'TDS_MAPPER_REPOSITORY')
        self.hyper_model_repository = kwargs.get('hyper_model_repository', 'TDS_HYPER_MODEL_REPOSITORY')
        self.feature_engineering_process_repository = kwargs.get('feature_engineering_process_repository', 'TDS_FEATURE_ENGINEERING_PROCESS_REPOSITORY')
        
    @execute_query
    def PushFile(self):
        """
        This method is used to create a list of database queries that will update 
        the search path, remove the current file, and then install a new file based 
        on the operating system type. It is specifically designed for handling file 
        management on different systems.

        Returns:
            list: A list of SQL queries to be executed.
        """

        # Creating an empty list to hold the queries
        queries = []

        # Appending the SET SESSION and DATABASE queries to the list
        queries.append('SET SESSION SEARCHUIFDBPATH = "{}"'.format(self.SEARCHUIFDBPATH))
        queries.append('DATABASE {}'.format(self.SEARCHUIFDBPATH))

        # Looping through each filename in the file list
        for filename in (pbar := tqdm(file_list)):
            pbar.set_description(f"Installing {filename}")
            # Adding a command to remove the existing file
            queries.append("CALL SYSUIF.REMOVE_FILE('{}',1);".format(filename))

            # Checking the OS name to determine the file path format
            if os.name == 'nt':
                # If it's Windows, we need to format the path a little differently
                queries.append("CALL SYSUIF.INSTALL_FILE('{}','{}','cz!{}')".format(filename,
                     filename+'.py',
                     os.path.join(this_dir, "data", filename+".py").replace("\\", "/").split(':')[1]))

            else:
                # If it's Linux or another OS, we can use the standard path format
                queries.append("CALL SYSUIF.INSTALL_FILE('{}','{}','cz!{}')".format(filename,
                     filename+'.py',
                     os.path.join(this_dir, "data", filename+".py")))

        # Return the complete list of queries
        return queries

    def PushFile_Lake(self):
        """
        Prepares and executes a series of file installation tasks across operating systems,
        generating and logging SQL queries to update paths, remove old files, and install
        new files as specified in `file_list`.

        This method is designed to adapt to different operating systems by formatting paths
        according to the OS type (Windows or Linux/Unix). The SQL queries to update the
        environment are prepared but not executed within this function.

        Returns:
            list: A list of SQL queries generated for updating the database, installing new
                  files, and managing the search path.

        Logging:
            Logs each file installation attempt with a timestamp.
        """
        from time import sleep
        # Retrieve the environment configuration
        oaf = retry_on_upstream_timeout(logger=None)(tdml.get_env)(self.oaf_env)
        sql_queries = []

        # Loop through each filename in the file list and log progress
        logger.info(f"Installing {','.join(file_list)} in the {self.oaf_env} environment")
        for filename in file_list:
            # Determine file path format based on OS
            if os.name == 'nt':
                # Windows path adjustment
                file_path = os.path.join(this_dir, "data", filename + ".py").replace("\\", "/").split(':')[1]
            else:
                # Standard path for Linux or Unix
                file_path = os.path.join(this_dir, "data", filename + ".py")
            # Execute installation with environment configuration
            try:

                claim_id = ''
                nb_tentatives = 0
                while nb_tentatives < 10:
                    try:
                        if nb_tentatives == 0:
                            logger.info(
                                f"Starting installation of {filename}.py to environment: {self.oaf_env}")
                        else:
                            logger.info(
                                f"Starting installation of {filename}.py to environment: {self.oaf_env} tentative #{nb_tentatives}")
                        claim_id = oaf.install_file(
                            file_path       = file_path,
                            replace         = True,
                            suppress_output = True,
                            asynchronous    = True
                        )
                        logger.info(
                            f"Successful install_file execution (e.g. no timeout issue)")
                        break
                    except Exception as e:
                        # Check if this is an upstream timeout error
                        logger.error(f"An unexpected error occurred: {str(e)}")
                        if 'TDML_2412' in str(e):
                            logger.warning("TeradataMlException: Upstream request timeout occurred. New tentative.")
                        else:
                            logger.error(f"An unexpected error occurred: {str(e)}")
                            raise
                    nb_tentatives += 1
                    sleep(nb_tentatives)
                    if nb_tentatives >= 10:
                        raise
                if isinstance(claim_id, str):
                    logger.info(
                        f"Claimid for {filename}.py installation '{claim_id}'")
                    try:
                        stage = oaf.status(claim_id)['Stage'].iloc[-1]
                        while stage != 'File Installed':
                            stage = oaf.status(claim_id)['Stage'].iloc[-1]
                            logger.info(
                                f"Claimid {claim_id} status '{stage}'")
                            sleep(1)
                    except Exception as e:
                        logger.info(
                            f"Claimid {claim_id} status '{stage}'")
                        logger.info(f"error {str(e)}")
                        raise

                logger.info(
                    f"{filename}.py successfully installed in environment '{self.oaf_env}'.")
            except Exception as e:
                # Log the error with relevant details
                logger.error(
                    f"Installation failed for {filename}.py in environment: {self.oaf_env}. Error: {str(e)}")
                raise


        logger.info(f"All files installed")

        return

    def setup(self, install_files=True):
        """
        Sets up necessary repositories and optionally installs files based on the environment.

        This method initializes various repositories required for the system, such as code, model,
        mapper, hypermodel, and feature engineering process repositories. Based on the specified
        environment (`self.oaf_env`), it either installs files using `PushFile` (for Vantage Enterprise)
        or `PushFile_Lake` (for Vantage Cloud Lake).

        Parameters:
            install_files (bool, optional): If True, triggers the installation of files based on the
                                            environment. Defaults to True.

        Repository Initialization:
            Initializes:
                - Code Repository
                - Model Repository
                - Mapper Repository
                - Hypermodel Repository
                - Feature Engineering Process Repository

        Logging:
            Logs each repository creation and file installation operation with timestamps.
        """

        # Creating repositories and logging each step
        logger.info("Starting setup: Creating repositories.")

        self._create_code_repository()
        logger.info("Code repository created.")

        self._create_model_repository()
        logger.info("Model repository created.")

        self._create_mapper_repository()
        logger.info("Mapper repository created.")

        self._create_hypermodel_repository()
        logger.info("Hypermodel repository created.")

        self._create_feature_engineering_process_repository()
        logger.info("Feature engineering process repository created.")

        # Conditional file installation based on environment and install_files flag
        if install_files:
            if self.oaf_env is None:
                # Assume Vantage Enterprise if environment is None
                logger.info("Environment detected as Vantage Enterprise. Starting file installation with PushFile.")
                self.PushFile()
            else:
                # Assume Vantage Cloud Lake otherwise
                logger.info(
                    "Environment detected as Vantage Cloud Lake. Starting file installation with PushFile_Lake.")
                self.PushFile_Lake()

        logger.info("Setup complete.")
####################################################################################################
#
#               CCCCC   OOOOO  DDDDD   EEEEEEE 
#              CC    C OO   OO DD  DD  EE      
#              CC      OO   OO DD   DD EEEEE   
#              CC    C OO   OO DD   DD EE      
#               CCCCC   OOOO0  DDDDDD  EEEEEEE 
#
####################################################################################################  

    @execute_query
    def _create_code_repository(self):
        """
        Create a code repository in the TDStone system.

        Returns:
            query: SQL query to create the code repository.
        """        
        query = f"""
            CREATE MULTISET TABLE {self.schema_name}.{self.code_repository},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (
                ID VARCHAR(36) NOT NULL,
                CODE_TYPE VARCHAR(255) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL,
                CODE BLOB,
                METADATA JSON(32000), 
                ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
            )
            PRIMARY INDEX (ID);
        """
        return query
    
    def list_codes(self, with_full_script = False, current_only = True):
        """
        List the code in the TDStone system.

        Args:
            with_full_script (bool, optional): If True, the full script is listed. Defaults to False.
            current_only (bool, optional): If True, only the current version is listed. Defaults to True.

        Returns:
            DataFrame: A DataFrame with the code details.
        """        
        if current_only:
            query = "CURRENT VALIDTIME \n"
        else:
            query = ''
            
        query = query + 'SELECT \n'
        
        if with_full_script:
            query = query + '* \n'
        else:
            if current_only:
                query = query + ',\n'.join(['ID','CODE_TYPE','METADATA'])
            else:
                query = query + ',\n'.join(['ID','CODE_TYPE','METADATA','ValidStart','ValidEnd'])
                
        query = query + f'\n FROM {self.schema_name}.{self.code_repository}'
        
        return tdml.DataFrame.from_query(query)
    
    @execute_query
    def remove_codes(self, code_id):
        """
        Remove a code from the TDStone system.

        Args:
            code_id (str or list): The ID or list of IDs of the code to be removed.

        Returns:
            query: SQL query to remove the code.
        """        
        if type(code_id) == list:
            code_list = ",".join(["'"+x+"'" for x in code_id])
            query = f"""
                DELETE {self.schema_name}.{self.code_repository} WHERE ID IN ({code_list});
                """
        else:
            query = f"""
                DELETE {self.schema_name}.{self.code_repository} WHERE ID = '{code_id}';
                """
        
        return query

####################################################################################################
#
#              MM    MM  OOOOO  DDDDD   EEEEEEE LL      
#              MMM  MMM OO   OO DD  DD  EE      LL      
#              MM MM MM OO   OO DD   DD EEEEE   LL      
#              MM    MM OO   OO DD   DD EE      LL      
#              MM    MM  OOOO0  DDDDDD  EEEEEEE LLLLLLL 
#
####################################################################################################    
    @execute_query
    def _create_model_repository(self):
        """
        Create a model repository in the TDStone system.

        Returns:
            query: SQL query to create the model repository.
        """        
        query = f"""
        CREATE MULTISET TABLE {self.schema_name}.{self.model_repository},
        FALLBACK,
        NO BEFORE JOURNAL,
        NO AFTER JOURNAL,
        CHECKSUM = DEFAULT,
        DEFAULT MERGEBLOCKRATIO,
        MAP = TD_MAP1
        (
            ID VARCHAR(36) NOT NULL,
            ID_CODE VARCHAR(36),
            ARGUMENTS VARCHAR(32000) CHARACTER SET UNICODE NOT CASESPECIFIC NOT NULL, --JSON(32000),
            METADATA JSON(32000), 
            ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
            ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
            PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME	
        )
        PRIMARY INDEX (ID_CODE);
        """
        return query
    
    def list_models(self, current_only = True):
        """
        List the models in the TDStone system.

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
            
        query = query + 'SELECT \n'
        
        if current_only:
            query = query + ',\n'.join(['ID','ID_CODE','ARGUMENTS','METADATA'])
        else:
            query = query + ',\n'.join(['ID','ID_CODE','ARGUMENTS','METADATA','ValidStart','ValidEnd'])
                
        query = query + f'\n FROM {self.schema_name}.{self.model_repository}'
        
        return tdml.DataFrame.from_query(query)
    
    @execute_query
    def remove_models(self, model_id):
        """
        Remove a model from the TDStone system.

        Args:
            model_id (str or list): The ID or list of IDs of the model to be removed.

        Returns:
            query: SQL query to remove the model.
        """        
        if type(model_id) == list:
            model_list = ",".join(["'"+x+"'" for x in model_id])
            query = f"""
                DELETE {self.schema_name}.{self.model_repository} WHERE ID IN ({model_list});
                """
        else:
            query = f"""
                DELETE {self.schema_name}.{self.model_repository} WHERE ID = '{model_id}';
                """
        
        return query  
    
####################################################################################################
#
#              MM    MM   AAA   PPPPPP  PPPPPP  EEEEEEE RRRRRR  
#              MMM  MMM  AAAAA  PP   PP PP   PP EE      RR   RR 
#              MM MM MM AA   AA PPPPPP  PPPPPP  EEEEE   RRRRRR  
#              MM    MM AAAAAAA PP      PP      EE      RR  RR  
#              MM    MM AA   AA PP      PP      EEEEEEE RR   RR 
#
####################################################################################################

                                                   
    @execute_query
    def _create_mapper_repository(self):
        """
        Create a mapper repository in the TDStone system.

        Returns:
            query: SQL query to create the mapper repository.
        """        
        query = f"""
            CREATE MULTISET TABLE {self.schema_name}.{self.mapper_repository},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (
                ID VARCHAR(36) NOT NULL,
                MAPPER_TYPE VARCHAR(255) CHARACTER SET UNICODE,
                TABLE_NAME VARCHAR(255) CHARACTER SET UNICODE,
                CODE_REPOSITORY VARCHAR(255) CHARACTER SET UNICODE,
                MODEL_REPOSITORY VARCHAR(255) CHARACTER SET UNICODE,
                TRAINED_MODEL_REPOSITORY VARCHAR(255) CHARACTER SET UNICODE,
                FEATURE_REPOSITORY VARCHAR(255) CHARACTER SET UNICODE,
                SCORES_REPOSITORY VARCHAR(255) CHARACTER SET UNICODE,
                DATASET_OBJECT VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                COL_ID_ROW VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                COL_ID_PARTITION VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                COL_FOLD VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                ON_CLAUSE_VIEW VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                STO_VIEW VARCHAR(2000) CHARACTER SET UNICODE NOT CASESPECIFIC,
                METADATA JSON(32000),
                ValidStart TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                ValidEnd TIMESTAMP(0) WITH TIME ZONE NOT NULL,
                PERIOD FOR ValidPeriod  (ValidStart, ValidEnd) AS VALIDTIME            
            )
            PRIMARY INDEX (ID);
            """
        return query
    
    def list_mappers(self, current_only = True, mapper_type = None):
        """
        List the mappers in the TDStone system.

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
            
        query = query + 'SELECT * \n'
        
               
        query = query + f'\n FROM {self.schema_name}.{self.mapper_repository}'
        
        if mapper_type is not None:
            query = query + f"\n WHERE MAPPER_TYPE = '{mapper_type}'"
        
        return tdml.DataFrame.from_query(query)
    
    @execute_query
    def remove_mappers(self, mapper_id):
        """
        Remove a model from the TDStone system.

        Args:
            model_id (str or list): The ID or list of IDs of the mapper to be removed.

        Returns:
            query: SQL query to remove the model.
        """        
        if type(mapper_id) == list and len(mapper_id)>0:
            mapper_list = ",".join(["'"+x+"'" for x in mapper_id])
            query = f"""
                DELETE {self.schema_name}.{self.mapper_repository} WHERE ID IN ({mapper_list});
                """
        else:
            query = f"""
                DELETE {self.schema_name}.{self.mapper_repository} WHERE ID = '{mapper_id}';
                """
        
        return query  
    
####################################################################################################
#
# ooooo   ooooo oooooo   oooo ooooooooo.   oooooooooooo ooooooooo.   ooo        ooooo   .oooooo.   oooooooooo.   oooooooooooo ooooo        
# `888'   `888'  `888.   .8'  `888   `Y88. `888'     `8 `888   `Y88. `88.       .888'  d8P'  `Y8b  `888'   `Y8b  `888'     `8 `888'        
#  888     888    `888. .8'    888   .d88'  888          888   .d88'  888b     d'888  888      888  888      888  888          888         
#  888ooooo888     `888.8'     888ooo88P'   888oooo8     888ooo88P'   8 Y88. .P  888  888      888  888      888  888oooo8     888         
#  888     888      `888'      888          888    "     888`88b.     8  `888'   888  888      888  888      888  888    "     888         
#  888     888       888       888          888       o  888  `88b.   8    Y     888  `88b    d88'  888     d88'  888       o  888       o 
# o888o   o888o     o888o     o888o        o888ooooood8 o888o  o888o o8o        o888o  `Y8bood8P'  o888bood8P'   o888ooooood8 o888ooooood8 
#
####################################################################################################

                                                   
    @execute_query
    def _create_hypermodel_repository(self):
        """
        Create a mapper repository in the TDStone system.

        Returns:
            query: SQL query to create the mapper repository.
        """        
        query = f"""
            CREATE MULTISET TABLE {self.schema_name}.{self.hyper_model_repository},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (
                CREATION_DATE TIMESTAMP(6) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                ID VARCHAR(36) NOT NULL,
                ID_MODEL VARCHAR(36) NOT NULL,
                ID_MAPPER_TRAINING VARCHAR(36) NOT NULL,
                ID_MAPPER_SCORING VARCHAR(36) NOT NULL,
                METADATA JSON(32000)
            )
            PRIMARY INDEX (ID);
            """
        return query
    
    def list_hyper_models(self):
        """
        List the hyper models in the TDStone system.

        Returns:
            DataFrame: A DataFrame with the hyper model details.
        """        
            
        query = 'SELECT * \n'
        
               
        query = query + f'\n FROM {self.schema_name}.{self.hyper_model_repository}'
        
        
        return tdml.DataFrame.from_query(query)
    
    @execute_query
    def remove_hyper_models(self, hyper_model_id):
        """
        Remove a hyper model from the TDStone system.

        Args:
            model_id (str or list): The ID or list of IDs of the mapper to be removed.

        Returns:
            query: SQL query to remove the model.
        """        
        if type(hyper_model_id) == list and len(hyper_model_id)>0:
            hyper_model_list = ",".join(["'"+x+"'" for x in hyper_model_id])
            query = f"""
                DELETE {self.schema_name}.{self.hyper_model_repository} WHERE ID IN ({hyper_model_list});
                """
        else:
            query = f"""
                DELETE {self.schema_name}.{self.hyper_model_repository} WHERE ID = '{hyper_model_id}';
                """
        
        return query

    ####################################################################################################
    #
    #    oooooooooooo oooooooooooo       .o.       ooooooooooooo ooooo     ooo ooooooooo.   oooooooooooo      oooooooooooo ooooo      ooo   .oooooo.    ooooo ooooo      ooo oooooooooooo oooooooooooo ooooooooo.   ooooo ooooo      ooo   .oooooo.    
    # `888'     `8 `888'     `8      .888.      8'   888   `8 `888'     `8' `888   `Y88. `888'     `8      `888'     `8 `888b.     `8'  d8P'  `Y8b   `888' `888b.     `8' `888'     `8 `888'     `8 `888   `Y88. `888' `888b.     `8'  d8P'  `Y8b   
    #  888          888             .8"888.          888       888       8   888   .d88'  888               888          8 `88b.    8  888            888   8 `88b.    8   888          888          888   .d88'  888   8 `88b.    8  888           
    #  888oooo8     888oooo8       .8' `888.         888       888       8   888ooo88P'   888oooo8          888oooo8     8   `88b.  8  888            888   8   `88b.  8   888oooo8     888oooo8     888ooo88P'   888   8   `88b.  8  888           
    #  888    "     888    "      .88ooo8888.        888       888       8   888`88b.     888    "          888    "     8     `88b.8  888     ooooo  888   8     `88b.8   888    "     888    "     888`88b.     888   8     `88b.8  888     ooooo 
    #  888          888       o  .8'     `888.       888       `88.    .8'   888  `88b.   888       o       888       o  8       `888  `88.    .88'   888   8       `888   888       o  888       o  888  `88b.   888   8       `888  `88.    .88'  
    # o888o        o888ooooood8 o88o     o8888o     o888o        `YbodP'    o888o  o888o o888ooooood8      o888ooooood8 o8o        `8   `Y8bood8P'   o888o o8o        `8  o888ooooood8 o888ooooood8 o888o  o888o o888o o8o        `8   `Y8bood8P'   

    #
    ####################################################################################################

    @execute_query
    def _create_feature_engineering_process_repository(self):
        """
        Create a mapper repository in the TDStone system.

        Returns:
            query: SQL query to create the mapper repository.
        """
        query = f"""
            CREATE MULTISET TABLE {self.schema_name}.{self.feature_engineering_process_repository},
            FALLBACK,
            NO BEFORE JOURNAL,
            NO AFTER JOURNAL,
            CHECKSUM = DEFAULT,
            DEFAULT MERGEBLOCKRATIO,
            MAP = TD_MAP1
            (
                CREATION_DATE TIMESTAMP(6) WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                ID VARCHAR(36) NOT NULL,
                ID_MODEL VARCHAR(36) NOT NULL,
                ID_MAPPER VARCHAR(36) NOT NULL,
                FEATURE_ENGINEERING_TYPE VARCHAR(255) NOT NULL,
                METADATA JSON(32000)
            )
            PRIMARY INDEX (ID);
            """
        return query

    def list_feature_engineering_models(self):
        """
        List the hyper models in the TDStone system.

        Returns:
            DataFrame: A DataFrame with the hyper model details.
        """

        query = 'SELECT * \n'

        query = query + f'\n FROM {self.schema_name}.{self.feature_engineering_process_repository}'

        return tdml.DataFrame.from_query(query)

    @execute_query
    def remove_feature_engineering_models(self, feature_engineering_process_id):
        """
        Remove a hyper model from the TDStone system.

        Args:
            model_id (str or list): The ID or list of IDs of the mapper to be removed.

        Returns:
            query: SQL query to remove the model.
        """
        if type(feature_engineering_process_id) == list and len(feature_engineering_process_id) > 0:
            feature_engineering_process_list = ",".join(["'" + x + "'" for x in feature_engineering_process_id])
            query = f"""
                DELETE {self.schema_name}.{self.feature_engineering_process_repository} WHERE ID IN ({feature_engineering_process_list});
                """
        else:
            query = f"""
                DELETE {self.schema_name}.{self.feature_engineering_process_repository} WHERE ID = '{feature_engineering_process_id}';
                """

        return query