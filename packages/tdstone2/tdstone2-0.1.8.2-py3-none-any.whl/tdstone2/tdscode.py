import uuid
import json
import os
from tdstone2.utils import execute_query_with_path, execute_query
from tdstone2.tdstone import TDStone
import teradataml as tdml

class Code():  # class names in Python should typically use the CapWords convention
    """
    A class to handle code object, specifically designed for code execution in Teradata Vantage.
    
    Attributes:
        id (str): The unique identifier for the code.
        metadata (dict): Metadata associated with the code.
        script_path (str): Path to the script file.
        code_type (str): Type of the code.
        code_repository (str): The repository where the code is stored.
        schema_name (str): Name of the schema.
        tdstone (TDStone object): A TDStone object.
    """    
    def __init__(self, id=None, metadata=None, script_path=None, code_type='python class',code_repository=None, schema_name=None, tdstone = None):
        """
        Initialize the Code object.
        ...
        """        
        if tdstone is not None:
            schema_name     = tdstone.schema_name
            code_repository = tdstone.code_repository
            
        self.schema_name     = schema_name
        self.code_repository = code_repository
        
        self.isnewcode = True if id is None else False
        self.id = str(uuid.uuid4()) if id is None else id
        try:
            self.metadata = {'user': os.getlogin(), 'code_type': code_type}
        except Exception as e:
            self.metadata = {'code_type': code_type}
        if metadata is not None:
            self.metadata.update(metadata)  # I'm guessing this is what you meant to do
        self.update_script(script_path)
        self.code_type = code_type

    def update_metadata(self, metadata):
        """
        Update the metadata for the code.

        Args:
            metadata (dict): New metadata to update.
        """        
        self.metadata.update(metadata)

    def update_script(self, script_path):
        """
        Update the code script from a specified file path.

        Args:
            script_path (str): File path of the script.
        """        
        if script_path is not None:
            with open(script_path, 'r') as file:
                self.script = file.read()
            self.metadata.update({'script_path': script_path})
            #print('The script is updated locally, you still have to upload it in Vantage')
    def update_script_code(self, script_code):
        """
        Update the code script from a specified file path.

        Args:
            script_path (str): File path of the script.
        """
        if script_code is not None:
            self.script = script_code
            self.metadata.update({'script_path': 'from memory'})
            #print('The script is updated locally, you still have to upload it in Vantage')

    def update_repo(self,code_repository=None, schema_name=None, tdstone = None):
        if tdstone is not None:
            schema_name     = tdstone.schema_name
            code_repository = tdstone.code_repository
        self.schema_name = schema_name
        self.code_repository = code_repository       

    @execute_query_with_path
    def upload(self):
        """
        Uploads the code to the specified code repository.

        Returns:
            (query, path) where `query` is the SQL query and `path` is the path of the file.
        """        
        if self.isnewcode:
            # this is a new insert
            query = f"""CURRENT VALIDTIME INSERT INTO {self.schema_name}.{self.code_repository}
            (ID, CODE_TYPE, CODE, METADATA)
             VALUES
            ('{self.id}',
             '{self.code_type}',
             ?,
             '{json.dumps(self.metadata).replace("'", '"')}');
            """
            self.isnewcode = False
        else:
            query = f"""
            CURRENT VALIDTIME UPDATE {self.code_repository}
            SET 
                CODE   = ?
            ,   CODE_TYPE = '{self.code_type}'
            ,   METADATA = '{json.dumps(self.metadata).replace("'", '"')}'
            WHERE ID = '{self.id}';
            """
        
        return query, self.script.encode('ascii')   
    
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
            
        self.isnewcode = False
               
        query = f"""
        CURRENT VALIDTIME
        SELECT 
           ID
        ,  CODE_TYPE
        ,  CODE
        ,  METADATA
        FROM {self.schema_name}.{self.code_repository}
        WHERE ID = '{id}'
        """
        
        df = tdml.DataFrame.from_query(query).to_pandas()
        
        if df.shape[0]>0:
            self.id        = df.ID.values[0]
            self.code_type = df.CODE_TYPE.values[0]
            self.script    = df.CODE.values[0]
            self.metadata  = eval(df.METADATA.values[0])
            self.isnewcode = False
        else:
            print('there is no code with this id')
        