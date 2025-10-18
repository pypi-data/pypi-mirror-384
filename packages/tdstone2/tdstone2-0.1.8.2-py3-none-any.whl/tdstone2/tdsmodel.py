import uuid
import json
import os
from tdstone2.utils import execute_query_with_path, execute_query
from tdstone2.tdstone import TDStone
import teradataml as tdml

class Model():

    def __init__(self, id=None, metadata=None, id_code=None, arguments=None, model_repository=None, code_repository = None, schema_name=None, tdstone = None):
        """
        Initialize the Model object.
        A Model is made of a Code and a set of arguments.
        """        
        if tdstone is not None:
            schema_name      = tdstone.schema_name
            code_repository  = tdstone.code_repository
            model_repository = tdstone.model_repository
            
        self.schema_name      = schema_name
        self.code_repository  = code_repository
        self.model_repository = model_repository
        self.id_code          = id_code
        
        self.isnewcode        = True if id is None else False
        self.id               = str(uuid.uuid4()) if id is None else id
        try:
            self.metadata         = {'user': os.getlogin()}
        except Exception as e:
            self.metadata = {}
        if metadata is not None:
            self.metadata.update(metadata)  # I'm guessing this is what you meant to do
            
        self.arguments        = {}
        if arguments is not None:
            self.arguments.update(arguments)
            
    def update_metadata(self, metadata):
        """
        Update the metadata for the model.

        Args:
            metadata (dict): New metadata to update.
        """        
        self.metadata.update(metadata)

    def update_arguments(self, arguments):
        """
        Update the arguments for this model.

        Args:
            arguments (dict): new arguments to update.
        """        
        self.arguments.update(arguments)
        
    def update_repo(self,model_repository=None, schema_name=None, tdstone = None):

        if tdstone is not None:
            schema_name     = tdstone.schema_name
            code_repository = tdstone.code_repository
            model_repository = tdstone.model_repository
        self.schema_name      = schema_name
        self.model_repository = model_repository       
        
    def attach_code(self, id_code):
        self.id_code = id_code

    @execute_query
    def upload(self):
        """
        Uploads the model to the specified model repository.

        Returns:
            (query, path) where `query` is the SQL query and `path` is the path of the file.
        """        
        
        if self.isnewcode:
            # this is a new insert
            query = f"""CURRENT VALIDTIME INSERT INTO {self.schema_name}.{self.model_repository}
            (ID, ID_CODE, ARGUMENTS, METADATA)
             VALUES
            ('{self.id}',
             '{self.id_code}',
             '{json.dumps(self.arguments).replace("'", '"')}',
             '{json.dumps(self.metadata).replace("'", '"')}');
            """
            self.isnewcode = False
        else:
            query = f"""
            CURRENT VALIDTIME UPDATE {self.schema_name}.{self.model_repository}
            SET 
                ID_CODE = '{self.id_code}'
            ,   ARGUMENTS = '{json.dumps(self.arguments).replace("'", '"')}'
            ,   METADATA = '{json.dumps(self.metadata).replace("'", '"')}'
            WHERE ID = '{self.id}';
            """

        return query
    
    @execute_query
    def remove(self):
        """
        Removes the code from the specified code repository.

        Returns:
            query: SQL query to remove the code.
        """            
        query = f"""
            DELETE {self.schema_name}.{self.code_repository} WHERE ID = '{self.id}';
            """
        
        return query
               
    def download(self, id, code_repository=None, schema_name=None, tdstone = None):
        
        if tdstone is not None:
            self.schema_name     = tdstone.schema_name
            self.code_repository = tdstone.code_repository
        if code_repository is not None and schema_name is not None:
            self.schema_name     = schema_name
            self.code_repository = code_repository       
               
        query = f"""
        CURRENT VALIDTIME
        SELECT 
           ID
        ,  ID_CODE
        ,  ARGUMENTS
        ,  METADATA
        FROM {self.schema_name}.{self.model_repository}
        WHERE ID = '{id}'
        """
        
        df = tdml.DataFrame.from_query(query).to_pandas()
        
        if df.shape[0]>0:
            self.id        = df.ID.values[0]
            self.id_code   = df.ID_CODE.values[0]
            self.arguments = eval(df.ARGUMENTS.values[0])
            self.metadata  = eval(df.METADATA.values[0])
            self.isnewcode = False
        else:
            print('there is no code with this id')
            
        