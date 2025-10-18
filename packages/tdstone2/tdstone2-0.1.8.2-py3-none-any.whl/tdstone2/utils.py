import functools
import teradataml as tdml
import os
import re
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sqlparse
import logging
from packaging import version
from teradataml.context.context import _get_database_username
from tqdm import tqdm

from teradatasqlalchemy.types import *



def get_connection_username():
    return _get_database_username()

def is_version_greater_than(tested_version, base_version="17.20.00.03"):
    """
    Check if the tested version is greater than the base version.

    Args:
        tested_version (str): Version number to be tested.
        base_version (str, optional): Base version number to compare. Defaults to "17.20.00.03".

    Returns:
        bool: True if tested version is greater, False otherwise.
    """
    return version.parse(tested_version) > version.parse(base_version)

def execute_query(f):
    """
    Decorator to execute a query. It wraps around the function and adds exception handling.

    Args:
        f (function): Function to be decorated.

    Returns:
        function: Decorated function.
    """
    @functools.wraps(f)
    def wrapped_f(*args, **kwargs):
        query = f(*args, **kwargs)
        if is_version_greater_than(tdml.__version__, base_version="17.20.00.03"):
            if type(query) == list:
                for q in query:
                    try:
                        tdml.execute_sql(q)
                    except Exception as e:
                        print(str(e).split('\n')[0])
                        print(q)
            else:
                try:
                    tdml.execute_sql(query)
                except Exception as e:
                    print(str(e).split('\n')[0])
                    print(query)
        else:
            if type(query) == list:
                for q in query:
                    try:
                        tdml.get_context().execute(q)
                    except Exception as e:
                        print(str(e).split('\n')[0])
                        print(q)
            else:
                try:
                    tdml.get_context().execute(query)
                except Exception as e:
                    print(str(e).split('\n')[0])       
                    print(query)
        return 
    return wrapped_f

def execute_query_with_path(f):
    """
    Decorator to execute a query with a specified path.
    It wraps around the function, executes the query, and then removes the file.

    Args:
        f (function): Function to be decorated.

    Returns:
        function: Decorated function.
    """
    @functools.wraps(f)
    def wrapped_f(*args, **kwargs):
        query, path = f(*args, **kwargs)
        #print(path)
        if is_version_greater_than(tdml.__version__, base_version="17.20.00.03"):
            tdml.execute_sql(query,[[path]])
        else:
            tdml.get_context().execute(query, path)
        
    return wrapped_f


def get_partition_datatype(tddf, columns):
    """
    Fetches the data types of specified columns in a Teradata DataFrame (tddf).

    The function queries the data type of each column specified and returns it as a dictionary.

    :param tddf: Teradata DataFrame
        Input DataFrame for which data types are to be fetched.

    :param columns: list
        List of column names for which data types need to be retrieved.

    :return: dict
        Dictionary where keys are column names and values are the data types of the respective columns.

    :Note: The function assumes the use of Teradata and Teradata ML (tdml) for data manipulation and querying.
    """

    # Try to get the table name from the tddf
    try:
        table_name = tddf._table_name
    except Exception as e:
        # If the table name attribute is not present, execute the tddf to get it
        tddf = tddf._DataFrame__execute_node_and_set_table_name(tddf._nodeid, tddf._metaexpr)
        table_name = tddf._table_name

    # Construct the SQL query to get the datatype of each column
    query = f"""
    SELECT TOP 1
        {','.join(['TYPE(' + x + ') AS ' + x for x in columns])}
    FROM {table_name}
    """

    # Execute the SQL query and convert the result to a pandas DataFrame
    df = tdml.DataFrame.from_query(query).to_pandas()

    # Construct a dictionary of column names and their data types
    types = {}
    for c in df.columns:
        types[c] = df[c].values[0].strip()

    return types


def get_sto_parameters(dataset):
    """
    Generate a dictionary of parameters related to the dataset, particularly focusing on column types.

    The function identifies columns of type float, integer, and also provides an output format.

    :param dataset: pd.DataFrame
        Input dataset for which the parameters are being generated.

    :return: dict
        Dictionary containing the following keys:
        - columnnames: All column names of the dataset.
        - float_columnames: Column names with float data type.
        - integer_columnames: Column names with integer data type.
        - category_columns: An empty list (reserved for potential future use).
        - output_format: Format for output, default is ['pickle'].

    :Note: The function depends on another function `get_partition_datatype` which is not provided in this context.
    """

    # Get the data types of each partition of the dataset using an external function
    types = get_partition_datatype(dataset, dataset.columns)

    sto_parameters = {}  # Initialize an empty dictionary for the parameters

    # Assign all column names
    sto_parameters["columnnames"] = list(dataset.columns)

    # Identify and assign float column names
    sto_parameters["float_columnames"] = [k for k, v in types.items() if v.lower() == 'float']

    # Identify and assign integer column names
    sto_parameters["integer_columnames"] = [k for k, v in types.items() if 'int' in v.lower()]

    # Placeholder for category columns, currently an empty list
    sto_parameters["category_columns"] = []

    # Assign the default output format
    sto_parameters['output_format'] = ['pickle']

    return sto_parameters


def cleanup(schema, rootname='TDS_'):
    """
    Clean up tables and views in the specified schema that have names starting with the given rootname.

    For tables or views starting with the given rootname (default "TDS_"), the function will attempt to drop them.
    The function can handle different versions of the 'tdml' module, using different methods for table and view
    deletion based on the module version.

    :param schema: str
        The name of the schema from which tables and views will be deleted.

    :param rootname: str, optional
        The prefix for table and view names to target for deletion. Default is "TDS_".

    :return: None
    """

    # Get the list of tables in the provided schema
    tables = tdml.db_list_tables(schema_name=schema).TableName.tolist()

    # Initialize the progress bar
    progress_bar = tqdm(tables, desc="Processing tables/views", unit="table/view")

    # Iterate over tables in the provided schema
    for x in progress_bar:

        # Only process tables or views starting with the rootname
        if x.startswith(rootname) or x.startswith('V_'+rootname):
            try:
                # If the 'tdml' module version is greater than the specified base version, use the new method for table deletion
                if is_version_greater_than(tdml.__version__, base_version="17.20.00.03"):
                    tdml.execute_sql(f"DROP TABLE {schema}.{x}")
                else:
                    # For older 'tdml' module versions, use the old method for table deletion
                    tdml.get_connection().execute(f"DROP TABLE {schema}.{x}")

                # Update the progress bar message
                progress_bar.set_postfix_str(f"Dropped TABLE {schema}.{x}")

            except Exception as e:
                # If dropping a table fails, attempt to drop a view
                try:
                    # If the 'tdml' module version is greater than the specified base version, use the new method for view deletion
                    if is_version_greater_than(tdml.__version__, base_version="17.20.00.03"):
                        tdml.execute_sql(f"DROP VIEW {schema}.{x}")
                    else:
                        # For older 'tdml' module versions, use the old method for view deletion
                        tdml.get_connection().execute(f"DROP VIEW {schema}.{x}")

                    # Update the progress bar message
                    progress_bar.set_postfix_str(f"Dropped VIEW {schema}.{x}")

                except Exception as e:
                    # If both table and view deletions fail, print the error message
                    error_message = str(e).split('\n')[0]
                    progress_bar.set_postfix_str(f"Failed {x}: {error_message}")


def _analyze_sql_query(sql_query):
    """
    Analyze a SQL query to extract the source tables, target tables, and views.

    The function uses regular expressions to search for patterns indicative
    of source tables, target tables, and views in the given SQL query.

    :param sql_query: str
        A string containing a SQL query to be analyzed.

    :return: dict
        A dictionary containing lists of source tables, target tables, and views.
        Format: {
            'source': [source_tables],
            'target': [target_tables]
        }
    """

    # Regular expression patterns for different SQL components
    create_table_pattern = r'CREATE\s+TABLE\s+([\w\s\.\"]+?)\s+AS'
    insert_into_pattern = r'INSERT\s+INTO\s+([\w\s\.\"]+?)'
    create_view_pattern = r'(CREATE|REPLACE)\s+VIEW\s+([\w\s\.\"]+?)\s+AS'
    select_pattern = r'(FROM|JOIN|\s+ON)\s+([\w\s\.\"]+?)(?=\s*(,|group|$|where|pivot|unpivot|\)|\s+AS))'
    # select_pattern2 =  r'(FROM|JOIN)\s+([\w\s\.\"]+?)(?=\s*(,|group|$|where|pivot|unpivot|\)|AS))'

    # Find all matches in the SQL query for each pattern
    create_table_matches = re.findall(create_table_pattern, sql_query, re.IGNORECASE)
    insert_into_matches = re.findall(insert_into_pattern, sql_query, re.IGNORECASE)
    create_view_matches = re.findall(create_view_pattern, sql_query, re.IGNORECASE)
    select_matches = re.findall(select_pattern, sql_query, re.IGNORECASE)
    # select_matches2 = re.findall(select_pattern2, sql_query, re.IGNORECASE)
    # print(select_matches2)
    # Extract the actual table or view name from the match tuples
    create_table_matches = [match[0] if match[0] else match[1] for match in create_table_matches]
    insert_into_matches = [match[0] if match[0] else match[1] for match in insert_into_matches]
    create_view_matches = [match[1] if match[0] else match[1] for match in create_view_matches]
    select_matches = [match[1] for match in select_matches]
    # select_matches2 = [match[0] for match in select_matches2]

    table_names = {
        'source': [],
        'target': []
    }

    # Categorize the matched tables and views into 'source' or 'target'
    table_names['target'].extend(create_table_matches)
    table_names['target'].extend(insert_into_matches)
    table_names['target'].extend(create_view_matches)
    table_names['source'].extend(select_matches)
    # table_names['source'].extend(select_matches2)

    # Remove duplicate table and view names
    table_names['source'] = list(set(table_names['source']))
    table_names['target'] = list(set(table_names['target']))

    correct_source = []
    for target in table_names['source']:
        if '"' not in target:
            correct_source.append('.'.join(['"' + t + '"' for t in target.split('.')]))
        else:
            correct_source.append(target)

    correct_target = []
    for target in table_names['target']:
        if '"' not in target:
            correct_target.append('.'.join(['"' + t + '"' for t in target.split('.')]))
        else:
            correct_target.append(target)

    table_names['source'] = correct_source
    table_names['target'] = correct_target

    return table_names


def analyze_sql_query(sql_query, df=None, target=None, root_name='ml__', node_info=None):
    """
    Analyzes the provided SQL query to determine source and target tables/views relationships.
    It then captures these relationships in a pandas DataFrame.

    :param sql_query: str
        A string containing the SQL query to be analyzed.
    :param df: pd.DataFrame, optional
        An existing DataFrame to append the relationships to. If not provided, a new DataFrame is created.
    :param target: str, optional
        Name of the target table/view. If not provided, it's deduced from the SQL query.

    :return: pd.DataFrame
        A DataFrame with two columns: 'source' and 'target', representing the relationships.

    :Note: This function is specifically tailored for Teradata and makes use of teradataml (tdml) for certain operations.
    """

    # Extract source and potential target tables/views from the provided SQL query
    table_name = _analyze_sql_query(sql_query)
    # print(table_name)
    # print(sql_query)
    # print('-----')

    # Extract node informations
    if node_info is None and target is None:
        node_info = [{'target': target, 'columns': tdml.DataFrame.from_query(sql_query).columns, 'query': sql_query}]
    elif node_info is None:
        if '"' not in target:
            target = '.'.join(['"' + t + '"' for t in target.split('.')])
            #print(target)
        node_info = [{'target': target, 'columns': tdml.DataFrame(target).columns, 'query': sql_query}]
    else:
        if '"' not in target:
            target = '.'.join(['"' + t + '"' for t in target.split('.')])
            #print(target)
        node_info = node_info + [{'target': target, 'columns': tdml.DataFrame(target).columns, 'query': sql_query}]

    # If df is not provided, initialize it; else append to the existing df
    table_name['target'] = [target] * len(table_name['source'])
    if df is None:
        df = pd.DataFrame(table_name)
    else:
        df = pd.concat([df, pd.DataFrame(table_name)], ignore_index=True)

    # Check for teradataml views in the source and recursively analyze them
    for obj in table_name['source']:
        if root_name.lower() in obj.lower():
            #print(obj)
            # It's a teradataml view. Fetch its definition.
            sql_query_ = tdml.execute_sql(f"SHOW VIEW {obj}").fetchall()[0][0].replace('\r', '\n').replace('\t', '\n')
            # Recursively analyze the view definition to get its relationships
            df, node_info = analyze_sql_query(sql_query_, df, target=obj, node_info=node_info, root_name=root_name)
        else:
            print(root_name.lower(), ' not in ', obj.lower(), 'then excluded')

    return df, node_info


def plot_graph(tddf, root_name='ml__'):
    """
    Visualizes a given dataframe's source-target relationships using a Sankey diagram.

    :param df: pd.DataFrame
        The input dataframe should have two columns: 'source' and 'target'.
        Each row represents a relationship between a source and a target.

    :Note: This function makes use of Plotly's Sankey diagram representation for visualization.

    :return: None
        The function outputs the Sankey diagram and doesn't return anything.
    """

    tddf._DataFrame__execute_node_and_set_table_name(tddf._nodeid, tddf._metaexpr)

    df, node_info = analyze_sql_query(tddf.show_query(), df=None, target=tddf._table_name, root_name=root_name)

    if df['source'].values[0].lower() == df['target'].values[0].lower():
        df = df.iloc[1::, :]

    # Create a list of unique labels combining sources and targets from the dataframe
    labels = list(pd.concat([df['source'], df['target']]).unique())

    # Creating a mapping of node labels to additional information
    node_info_dict = pd.DataFrame(node_info).set_index('target').T.to_dict()

    # Create hovertext for each label using the node_info_map
    hovertexts = [
        f"Columns:<br> {','.join(node_info_dict[label]['columns'])}<br> Query: {sqlparse.format(node_info_dict[label]['query'], reindent=True, keyword_case='upper')}".replace(
            '\n', '<br>').replace('PARTITION BY', '<br>PARTITION BY').replace('USING', '<br>USING').replace(' ON',
                                                                                                            '<br>ON').replace(') ',')<br>').replace(')<br>AS',') AS').replace(', ',',<br>')

        if label in node_info_dict else '' for label in labels]

    # Use the length of 'columns' for the value (thickness) of each link
    values = df['source'].apply(lambda x: len(node_info_dict[x]['columns']) if x in node_info_dict else 1)

    # Convert source and target names to indices based on their position in the labels list
    source_indices = df['source'].apply(lambda x: labels.index(x))
    target_indices = df['target'].apply(lambda x: labels.index(x))

    # Construct the Sankey diagram with nodes (sources & targets) and links (relationships)
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,  # Space between the nodes
            thickness=20,  # Node thickness
            line=dict(color="black", width=0.5),  # Node border properties
            label=labels,  # Labels for nodes
            color="blue",  # Node color
            # hovertext=link_hovertexts  # set hover text for nodes
            customdata=hovertexts,
            hovertemplate=' %{customdata}<extra></extra>',
        ),
        link=dict(
            source=source_indices,  # Link sources
            target=target_indices,  # Link targets
            value=values  # [1] * len(df)  # Assuming equal "flow" for each link. Can be modified if needed.
        )
    )])

    # Customize the layout, such as setting the title and font size
    fig.update_layout(title_text="Hierarchical Data Visualization", font_size=10)

    # Display the Sankey diagram
    fig.show()

    return df
def materialize_view(tddf, view_name, schema_name):
    """
    Materializes a given teradataml DataFrame as a view in the database with sub-views, if needed. This function
    helps in creating nested views, where complex views are broken down into simpler sub-views to simplify debugging
    and optimization. Each sub-view is named based on the main view's name with an additional suffix.

    Parameters:
    :param tddf: teradataml.DataFrame
        The teradataml dataframe whose view needs to be materialized.
    :param view_name: str
        The name of the main view to be created.
    :param schema_name: str
        The schema in which the view should be created.

    Returns:
    :return: teradataml.DataFrame
        A teradataml DataFrame representation of the created view.

    Notes:
    This function is specific to the teradataml library, and assumes the existence of certain attributes in the input DataFrame.
    """

    # Create the _table_name attribute for the teradataml DataFrame if it doesn't exist
    tddf._DataFrame__execute_node_and_set_table_name(tddf._nodeid, tddf._metaexpr)

    # Generate the dependency graph for the input DataFrame's SQL representation
    tddf_graph, _ = analyze_sql_query(tddf.show_query(), target=tddf._table_name)

    # Generate new names for sub-views based on the main view's name and store in a mapping dictionary
    mapping = {n: schema_name + '.' + view_name + '_sub_' + str(i) for i, n in enumerate(tddf_graph['target'].values)}

    # Replace or create the sub-views with their new names in the database
    for old_name, new_name in reversed(mapping.items()):
        query = tdml.execute_sql(f"SHOW VIEW {old_name}").fetchall()[0][0].replace('\r','\n').lower()
        query = query.replace('create', 'replace')
        for old_sub_name, new_sub_name in mapping.items():
            query = query.replace(old_sub_name.lower(), new_sub_name.lower())
        #print(query)
        print('REPLACE VIEW ', new_name)
        tdml.execute_sql(query)

    # Construct the final view by replacing the old names with new ones in the SQL representation
    mapping[new_name] = view_name
    #query = tdml.execute_sql(f"SHOW VIEW {tddf._table_name}").fetchall()[0][0].replace('\r','\n').lower()
    #query = f'replace view {schema_name}.{view_name} AS \n' + query
    for old_name, new_name in mapping.items():
        query = query.replace(old_name.lower(), new_name.lower())

    # Execute the final query to create the main view
    #print(query)
    print('REPLACE VIEW ', view_name)
    tdml.execute_sql(query)


    # Return a teradataml DataFrame representation of the created view
    return tdml.DataFrame(tdml.in_schema(schema_name, view_name))

def generate_sequence(n, column_name='n'):
    """
    Generates a SQL query to create a sequence of timestamps starting from a specified date.

    The function calculates the equivalent of the given number of seconds in days, hours,
    minutes, and seconds. It then constructs a SQL query that uses these components to
    generate a sequence of timestamps from a base date, incrementing by the smallest time
    unit provided (seconds, minutes, hours, or days) until the total duration is covered.

    Parameters:
    - n (int): The total duration in seconds to be converted into a sequence of timestamps.
    - column_name (str, optional): The name to be assigned to the sequence column in the
      resulting SQL query. Defaults to 'n'.

    Returns:
    - str: A SQL query string that, when executed, will generate a sequence of timestamps
      covering the duration specified by `n`, starting from '2022-01-01'.
    """

    # Convert the total duration in seconds into days, hours, minutes, and seconds
    n_days    = np.floor(n / (24 * 60 * 60))  # Number of whole days
    n_hours   = np.floor((n - n_days * 24 * 60 * 60) / (60 * 60))  # Remaining hours
    n_minutes = np.floor((n - n_days * 24 * 60 * 60 - n_hours * 60 * 60) / 60)  # Remaining minutes
    n_seconds = n - n_days * 24 * 60 * 60 - n_hours * 60 * 60 - n_minutes * 60  # Remaining seconds

    # Construct the SQL query
    query = f"""
    SELECT 
        ROW_NUMBER() OVER (PARTITION BY 1 ORDER BY pd) AS {column_name}  -- Generate a sequence number for each timestamp
    FROM (
        SELECT pd 
        FROM (
            SELECT 
                CAST(DATE '2022-01-01' AS TIMESTAMP) as t0  -- Base date as starting timestamp
            ,   t0 
                + CAST({n_seconds} AS INTERVAL SECOND(4))  -- Add seconds to the base timestamp
                + CAST({n_minutes} AS INTERVAL MINUTE(4))  -- Add minutes
                + CAST({n_hours} AS INTERVAL HOUR(4))      -- Add hours
                + CAST({n_days} AS INTERVAL DAY(4))        -- Add days
                as t1
            , PERIOD(t0, t1) as duration  -- Define a period from t0 to t1
            FROM (SELECT TOP 1 * FROM dbc.databases) B  -- Dummy table for query execution
            ) AS A
        EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND  -- Expand the period into individual seconds
    ) D
    """

    return query


def move2OFS(df, destination_schema, destination_table, if_exists='overwrite', map = 'td_map2'):
    features = df.columns  # just to instanciate the view
    try:
        df_ = tdml.DataFrame(tdml.in_schema(destination_schema, destination_table))
        exists = True
    except Exception as e:
        exists = False

    if not exists:
        query_ebs2ofs = f"""
        -- Create target table reference 
        CREATE MULTISET TABLE {destination_schema}.{destination_table},
        NO FALLBACK ,
        MAP     = {map}, 
        STORAGE = TD_OFSSTORAGE AS 
        (   
            SEL * FROM {df._table_name.split('.')[0]}.{df._table_name.split('.')[1]}
        )  WITH DATA
        NO PRIMARY INDEX;
        """
    else:
        if if_exists == 'append':
            query_ebs2ofs = f"""
                INSERT {destination_schema}.{destination_table} SELECT {','.join(features)} FROM {df._table_name.split('.')[0]}.{df._table_name.split('.')[1]};
            """
        elif if_exists == 'overwrite':
            query_ebs2ofs = f"""
                DELETE FROM {destination_schema}.{destination_table};
                INSERT {destination_schema}.{destination_table} SELECT {','.join(features)} FROM {df._table_name.split('.')[0]}.{df._table_name.split('.')[1]};
            """
    tdml.execute_sql(query_ebs2ofs)
    return tdml.DataFrame(tdml.in_schema(destination_schema, destination_table))


def generate_create_table_teradata(table_name, columns, primary_index: list = None, ofs=True):
    type_mapping = {
        DATE: "DATE",
        VARCHAR: "VARCHAR",
        CLOB: "CLOB",
        BIGINT: "BIGINT",
        TIMESTAMP: "TIMESTAMP",
        FLOAT: "FLOAT",
        DECIMAL: "DECIMAL",
        BLOB: "BLOB",
        CHAR: "CHAR",
        SMALLINT: "SMALLINT",
        INTEGER: "INTEGER",
        BYTEINT: "BYTEINT",
        PERIOD_DATE: "PERIOD(DATE)",
        PERIOD_TIME: "PERIOD(TIME)",
        JSON: "JSON(32000)"
    }

    sql_columns = []

    for column_name_, column_type in columns.items():
        column_name = '"' + column_name_.replace('"', '') + '"'
        column_sql_type = type_mapping.get(type(column_type), "VARCHAR")

        if isinstance(column_type, VARCHAR):
            length = column_type.length if column_type.length else 32000
            charset = column_type.charset if column_type.charset == 'UNICODE' else 'LATIN'
            sql_columns.append(f"{column_name} {column_sql_type}({length}) CHARACTER SET {charset}")

        elif isinstance(column_type, CLOB):
            length = column_type.length if column_type.length else 1000000
            charset = column_type.charset if column_type.charset == 'LATIN' else 'UNICODE'
            sql_columns.append(f"{column_name} {column_sql_type}({length}) CHARACTER SET {charset}")

        elif isinstance(column_type, JSON):
            charset = 'LATIN'
            sql_columns.append(f"{column_name} {column_sql_type} CHARACTER SET {charset}")

        elif isinstance(column_type, BIGINT):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, DATE):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, TIMESTAMP):
            if hasattr(column_type, "timezone") and column_type.timezone:
                sql_columns.append(f"{column_name} {column_sql_type} WITH TIME ZONE")
            else:
                sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, DECIMAL):
            precision = column_type.precision if column_type.precision else 18
            scale = column_type.scale if column_type.scale else 0
            sql_columns.append(f"{column_name} {column_sql_type}({precision}, {scale})")

        elif isinstance(column_type, BLOB):
            length = column_type.length if column_type.length else 1000000
            sql_columns.append(f"{column_name} {column_sql_type}({length})")

        elif isinstance(column_type, CHAR):
            length = column_type.length if column_type.length else 1
            charset = column_type.charset if column_type.charset == 'UNICODE' else 'LATIN'
            sql_columns.append(f"{column_name} {column_sql_type}({length}) CHARACTER SET {charset}")

        elif isinstance(column_type, SMALLINT):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, FLOAT):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, INTEGER):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, BYTEINT):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, PERIOD_DATE):
            sql_columns.append(f"{column_name} {column_sql_type}")

        elif isinstance(column_type, PERIOD_TIME):
            sql_columns.append(f"{column_name} {column_sql_type}")

        else:
            raise TypeError(f"Unsupported type for column: {column_name}")

    columns_sql = ",\n    ".join(['run_id VARCHAR(36) CHARACTER SET LATIN'] +sql_columns)
    create_table_sql = f"CREATE MULTISET TABLE {table_name}"
    create_table_sql += """
    , NO FALLBACK 
    , MAP = TD_MAP2
    , STORAGE = TD_OFSSTORAGE 
    """
    create_table_sql += f"(\n    {columns_sql}\n)"
    if primary_index is not None:
        prim = ','.join(primary_index)
        create_table_sql += f"\n PRIMARY INDEX ({prim})"
    return create_table_sql


import time
from functools import wraps

def retry_on_upstream_timeout(max_retries=10, logger=None):
    # Set up a default logger if none is provided
    if logger is None:
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    if attempt>1:
                        logger.info(f"Attempt {attempt}: Calling function '{func.__name__}'...")
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"Function '{func.__name__}' succeeded on attempt {attempt}.")
                    return result
                except Exception as e:
                    if "upstream request timeout" in str(e).lower():
                        logger.warning(f"Attempt {attempt} failed due to 'upstream timeout'. Retrying in {attempt} seconds...")
                        time.sleep(attempt)  # Delay increases with each attempt
                    else:
                        logger.error(f"Function '{func.__name__}' failed with an unexpected error: {e}")
                        raise
            logger.error(f"Function '{func.__name__}' failed after {max_retries} attempts due to 'upstream timeout'.")
            raise TimeoutError(f"Function failed after {max_retries} attempts due to 'upstream timeout'.")
        return wrapper
    return decorator


def get_installed_packages():

    return tdml.DataFrame.from_query(
    """
    SELECT
    distinct(res) as packages_
    FROM
        Script(
            
            SCRIPT_COMMAND(
                'tdpip3 freeze' 
            )
            RETURNS(
                'res varchar(1024)'
            )
    ) AS d
    """
    )