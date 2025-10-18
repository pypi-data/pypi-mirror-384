from tdstone2.data_distribution import EquallyDistributed,setup_table_for_model_generation
from tdstone2.data_distribution import InverseHash
import teradataml as tdml
import re
import pandas as pd
import numpy as np


from tdstone2.utils import generate_sequence
def GenerateDataSet(n_x=9, n_f=1, n_partitions=2, n_rows=5,
                    noise_classif=0.01,
                    train_test_split_ratio = 0.2,
                    database=tdml.context.context._get_current_databasename()):
    """
    Generates a multi-partitioned dataset within a Teradata database.

    :param n_x: Number of float features. These features are standardized with a zero mean.
    :param n_f: Number of 2-level categorical variables. Levels are 0 and 1.
    :param n_partitions: Number of partitions.
    :param n_rows: Number of rows per partition.
    :param noise_classif: Noise level added to the classification.
    :param train_test_split_ratio: Ratio for splitting the dataset into training and testing sets.
    :param database: The name of the Teradata database.

    :return: SQL query to generate the dataset and the names of the columns in the dataset.
    """


    N = int(n_partitions * n_rows / 99999 + 1)

    setup_table_for_model_generation(database)
    if n_x < 2:
        raise ValueError('The number of float features must be > 1 !')

    if n_f < 1:
        raise ValueError('The number of categorical feature must be > 0 !')

    if n_partitions < 1:
        raise ValueError('The number of partition must be > 0 !')

    if n_rows < 5:
        raise ValueError('The number of rows per partition must be > 4 !')

    random_x = """sqrt(-2.0*ln(CAST(RANDOM(1,999999999) AS FLOAT)/1000000000))
    * cos(2.0*3.14159265358979323846 * CAST(RANDOM(0,999999999) AS FLOAT)
    /1000000000)"""
    random_f = "RANDOM(0,1)"
    random_c = """RANDOM(0,1)*sqrt(-2.0 * ln(CAST(RANDOM(1,999999999) AS
    FLOAT)/1000000000)) * cos(2.0*3.14159265358979323846 *
    CAST(RANDOM(0,999999999) AS FLOAT)/1000000000)"""

    X_names = ['X'+str(i+1) for i in range(n_x)]
    F_names = ['flag'+str(i+1) for i in range(n_f)]
    if len(F_names) == 1:
        F_names = ['flag']


    if train_test_split_ratio > 1:
        train_test_split_condition = f"""CASE WHEN B.RNK-1<{train_test_split_ratio} THEN 'train' ELSE 'test' END"""
    else:
        train_test_split_condition = f"""CASE WHEN B.RNK-1<{train_test_split_ratio*n_rows} THEN 'train' ELSE 'test' END"""

    query = f"""
        SELECT AA.*
        , CASE WHEN (AA.Y1 + {random_x}*{noise_classif}> AVG(AA.Y1)
                     OVER (PARTITION BY AA.PARTITION_ID))
        THEN 1 ELSE 0 END AS Y2
        FROM (
        SELECT
            A.RNK as Partition_ID
        ,   ROW_NUMBER() OVER (PARTITION BY 1 ORDER BY A.RNK, B.RNK) as "ID"
        ,   {', '.join([random_x+' as '+X_names[i] for i in range(n_x)])}
        ,   {','.join([random_f+' as '+F_names[i] for i in range(n_f)])}
        ,   {'+'.join(['C1_'+str(i+1)+'*'+X_names[i] for i in range(n_x)])} as Y1
        ,   {train_test_split_condition} as FOLD        
        FROM
            (
            -- partitions
            SELECT
                DD.RNK
            ,   {', '.join([random_c+' as C1_'+str(i+1) for i in range(n_x)])}
            FROM (
            {generate_sequence(n_partitions, column_name='RNK')}
            ) DD
            ) A
        ,
            (
            -- inside partitions
            {generate_sequence(n_rows, column_name='RNK')}
            ) B
            ) AA
        """


    return query, X_names+F_names+['Y1', 'Y2']+['FOLD']


def introducemissingvalues(df_dataset, missing_values_proportions):
    """
    Introduces missing values (NULLs) into specified columns of a Teradata table.

    :param df_dataset: DataFrame-like object representing the Teradata table.
    :param missing_values_proportions: Dictionary specifying the columns and their respective proportions of missing values.

    :return: SQL query with missing values introduced as per the specifications.
    """

    # Generates a SQL CASE statement to introduce missing values for a variable based on given proportions.
    def casewhenmissingvalues(variable, n_missing, n_total):
        return f'CASE WHEN RANDOM(1,{n_total}) < {n_total}-{n_missing} THEN {variable} END AS {variable}'

    # Checks if a given variable has specified missing values proportions.
    def hasmissing(variable, missing_values_proportions):
        return variable in missing_values_proportions.keys()

    # Determines the transformation for each column - either introducing missing values or leaving as-is.
    def transform(variable, missing_values_proportions):
        if hasmissing(variable, missing_values_proportions):
            return casewhenmissingvalues(variable, missing_values_proportions[variable][0],
                                         missing_values_proportions[variable][1])
        else:
            return variable

    # Construct the SQL query to introduce missing values in the specified columns.
    query = f"""
    SELECT
    {','.join(list(map(lambda x: transform(x, missing_values_proportions), df_dataset.columns)))}
    FROM {df_dataset._table_name}
    """

    return query





def sql_random(distribution, data_type='float', center=None, half_width=None, one_ratio=None, total=None):
    """
    Generate SQL expressions to produce random values based on different distributions and data types.

    :param distribution: Type of distribution ('uniform', 'normal', 'binomial').
    :param data_type: Type of data ('float' or 'int').
    :param center: Center or mean of the distribution.
    :param half_width: Half width or standard deviation for the distribution.
    :param one_ratio: Probability for 1 in binomial distribution.
    :param total: Total possible outcomes (used in binomial distribution).

    :return: SQL expression as a string.

    # random_param_01 = {'data_type': 'int',
    #                   'distribution': 'uniform',
    #                   'center': 500,
    #                   'half_width': 250
    #                   }
    # random_param_02 = {'data_type': 'float',
    #                   'distribution': 'uniform',
    #                   'center': 0,
    #                   'half_width': 10
    #                   }
    # random_param_03 = {'data_type': 'float',
    #                   'distribution': 'normal',
    #                   'center': 0,
    #                   'half_width': 1
    #                   }
    # print(sql_random(**random_param_01))
    # print(sql_random(**random_param_02))
    # print(sql_random(**random_param_03))
    """

    # Uniform Distribution
    if distribution == 'uniform':
        mu = center
        delta = half_width
        a = f'{mu} - {delta}'
        b = f'{mu} + {delta}'

        # For integers
        if data_type == 'int':
            return f'CAST(CAST(RANDOM(0,999999999) AS FLOAT)/999999999*(({b})-({a}))+({a}) AS BIGINT)'

        # For floats
        elif data_type == 'float':
            return f'CAST(RANDOM(0,999999999) AS FLOAT)/999999999*(({b})-({a}))+({a})'

    # Normal Distribution using Box-Muller method
    elif distribution == 'normal':
        mu = center
        sigma = half_width
        return f'''sqrt(-2.0*ln(CAST(RANDOM(1,999999999) AS FLOAT)/1000000000))*cos(2.0*3.14159265358979323846*CAST(RANDOM(0,999999999) AS FLOAT)/1000000000)*({sigma})+({mu})'''

    # Binomial Distribution
    elif distribution == 'binomial':
        return f'CASE WHEN RANDOM(1,{total}) < {one_ratio} THEN 1 ELSE 0 END'

    return


def generaterandomsamples(df, random_params, nb_gen, id_columns='id',
                          database=tdml.context.context._get_current_databasename()):
    """
    Generate a SQL query to produce random samples based on input dataframe.

    :param df: Input dataframe.
    :param random_params: Random parameters for columns.
    :param nb_gen: Number of times each row should be replicated.
    :param id_columns: Columns serving as ID.
    :param database: Name of the database.

    :return: DataFrame with generated random samples.
    """

    # Probably some table initialization or setup
    setup_table_for_model_generation(database)

    # Check if a variable/column should be randomized
    def hastoberandomized(variable, random_params):
        return variable in random_params.keys()

    # Replace column with random SQL if it should be randomized
    def transform(variable, random_params):
        if hastoberandomized(variable, random_params):
            return random_params[variable]
        else:
            return variable

    # Extract all columns from df except id_columns
    columns = [x for x in df.columns if x.lower() != id_columns.lower()]

    # Main SQL query construction
    query = f"""
    SELECT
    {id_columns} as PARTITION_ID,
    row_number() OVER (ORDER BY {id_columns}, n__) as ID,
    {','.join(list(map(lambda x: transform(x, random_params) + f' AS {x}', columns)))}
    FROM {df._table_name} A,
    (SEL
        row_number() OVER (ORDER BY A.pd) as n__
    FROM
        (
        SELECT  pd
        FROM {database}.TABLE_FOR_GENERATION
        EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND
        ) A
    QUALIFY n__ < {nb_gen}+1
    ) B
    """

    return tdml.DataFrame.from_query(query)


def generatesinglesensordata(table_name, schema_name, if_exists='replace',
                             params=[1, 1000, 600., 100., 500., 200., 200., 25., 10., 300., 200., 0.05, 200., 100., 1,
                                     260.]):
    """
    Generates a single row of sensor data and copies it to a specified SQL table.

    :param table_name: Name of the target SQL table.
    :param schema_name: Name of the schema where the table belongs.
    :param if_exists: Behavior when the table already exists ('replace' will overwrite).
    :param params: List of default values for the sensor data.

    :return: A DataFrame representation of the data in the target table.
    """

    # Create a single-row dataframe with the provided parameters
    df = pd.DataFrame([params],
                      columns=['id', 'nbpts'] + ['x_param' + str(i + 1) for i in range(5)] + ['y_param' + str(i + 1) for
                                                                                              i in range(9)])

    # Copy the dataframe to the specified SQL table
    tdml.copy_to_sql(df, table_name=table_name, schema_name=schema_name, if_exists=if_exists)

    # Return the data in the table as a dataframe
    return tdml.DataFrame(tdml.in_schema(schema_name, table_name))


def generationmultiplesignals(df_params, id_columns='id', id_partition=None, partition_id_number=1,database=tdml.context.context._get_current_databasename()):
    """
    Generates synthetic signals based on provided parameters and mathematical functions.

    :param df_params: DataFrame or table reference with signal parameters.
    :param id_columns: ID column name.
    :param id_partition: Optional partition column name.
    :param partition_id_number: Default partition ID if `id_partition` is not provided.
    :param database: Name of the database (extracted from the context URL).

    :return: A DataFrame with the generated signal data.
    """

    # Initial database setup
    setup_table_for_model_generation(database)

    # Determine the SQL query based on the presence of id_partition
    if id_partition is None:
        query = f"""
        SEL
            PARTITION_ID
        ,   ID
        ,	X0 AS X
        ,	Y AS Y
        FROM
        (
            SEL
                {partition_id_number} AS PARTITION_ID
            ,	TS.{id_columns} AS ID
            ,	CASE WHEN B.n< TS.nbpts THEN B.n END AS x0
            ,	SIN(X0/TS.x_param1)*TS.x_param2 AS x1
            ,	EXP((-1.)*(x0-TS.x_param3)*(x0-TS.x_param3)/TS.x_param4/TS.x_param4)*x_param5 AS x2
            ,	x0 + x1 + x2 AS x
            ,	EXP((-1)*x/TS.y_param1) AS y0
            ,	EXP((-1)*x/TS.y_param2) AS y1
            ,	EXP((-1)*(x-TS.y_param3)*(x-TS.y_param3)/TS.y_param4/TS.y_param4) AS y2
            ,   CASE WHEN TS.y_param8 > 0.5 AND x0 > TS.y_param9 THEN 0 ELSE 1 END AS flag
            ,	(y0 + y1 + y2*flag + TS.y_param5/sqrt(2)*sqrt(-2.0*ln(CAST(RANDOM(1,999999999) AS FLOAT)/1000000000))
            * cos(2.0*3.14159265358979323846 * CAST(RANDOM(0,999999999) AS FLOAT)
            /1000000000))*TS.y_param6+TS.y_param7 AS y
            FROM
            (
            SEL
                row_number() OVER (ORDER BY A.pd) as n
            FROM
                (
                SELECT  pd
                FROM {database}.TABLE_FOR_GENERATION
                EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND
                ) A
            ) B,
            {df_params._table_name} TS
            WHERE x0 IS NOT NULL
        ) GEN
        """
    else:
        query = f"""
        SEL
            PARTITION_ID
        ,   ID
        ,	X0 AS X
        ,	Y AS Y
        FROM
        (
            SEL
                TS.{id_partition} AS PARTITION_ID
            ,	TS.{id_columns} AS ID
            ,	CASE WHEN B.n< TS.nbpts THEN B.n END AS x0
            ,	SIN(X0/TS.x_param1)*TS.x_param2 AS x1
            ,	EXP((-1.)*(x0-TS.x_param3)*(x0-TS.x_param3)/TS.x_param4/TS.x_param4)*x_param5 AS x2
            ,	x0 + x1 + x2 AS x
            ,	EXP((-1)*x/TS.y_param1) AS y0
            ,	EXP((-1)*x/TS.y_param2) AS y1
            ,	EXP((-1)*(x-TS.y_param3)*(x-TS.y_param3)/TS.y_param4/TS.y_param4) AS y2
            ,   CASE WHEN TS.y_param8 > 0.5 AND x0 > TS.y_param9 THEN 0 ELSE 1 END AS flag
            ,	(y0 + y1 + y2*flag + TS.y_param5/sqrt(2)*sqrt(-2.0*ln(CAST(RANDOM(1,999999999) AS FLOAT)/1000000000))
            * cos(2.0*3.14159265358979323846 * CAST(RANDOM(0,999999999) AS FLOAT)
            /1000000000))*TS.y_param6+TS.y_param7 AS y
            FROM
            (
            SEL
                row_number() OVER (ORDER BY A.pd) as n
            FROM
                (
                SELECT  pd
                FROM {database}.TABLE_FOR_GENERATION
                EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND
                ) A
            ) B,
            {df_params._table_name} TS
            WHERE x0 IS NOT NULL
        ) GEN
        """

    # Execute the SQL query and return the result as a DataFrame
    return tdml.DataFrame.from_query(query)


def linspace(start=1, stop=100, step=1, name='n'):
    n_total = int((stop - start) / step) +1

    n_total_days = int(n_total / 24 / 60 / 60)
    n_total_hours = int((n_total - n_total_days * (24 * 60 * 60)) / (60 * 60))
    n_total_minutes = int((n_total - n_total_days * (24 * 60 * 60) - n_total_hours * (60 * 60)) / 60)
    n_total_secondes = int((n_total - n_total_days * (24 * 60 * 60) - n_total_hours * (60 * 60) - n_total_minutes * 60))

    #print(n_total, n_total_days, n_total_hours, n_total_minutes, n_total_secondes)
    query = f"""
    SELECT (row_number() OVER (ORDER BY pd) -1)*{step} + {start} AS {name}
    FROM (
        SELECT pd
        FROM (
            SEL PERIOD(TIMESTAMP '2005-02-02 00:00:00+02:00',TIMESTAMP '2005-02-02 00:00:00+02:00' 
            + INTERVAL '{n_total_days}' DAY 
            + INTERVAL '{n_total_hours}' HOUR 
            + INTERVAL '{n_total_minutes}' MINUTE
            + INTERVAL '{n_total_secondes}' SECOND) AS TIME_SLICE
            FROM (
                SEL TOP 1 * FROM dbc.dbcinfo
            ) B
        ) A
        EXPAND ON TIME_SLICE AS pd BY INTERVAL '1' SECOND
    ) A2
    """

    return query


def generaterandomsignalparams(spreading=10, one_ratio=5, total=100):
    """
    Generates a dictionary of random signal parameters based on specified distributions.

    :param spreading: A factor to determine the variability around a center for some parameters.
    :param one_ratio: Parameter for the binomial distribution.
    :param total: Total count for binomial distribution.

    :return: Dictionary of random signal parameters.
    """

    # Initial parameter generation for 'nbpts'
    random_params = {
        'nbpts': sql_random(distribution='uniform', center='nbpts', half_width=500, data_type='int'),
    }

    # Add 'x_param' values to the dictionary
    random_params.update({'x_param' + str(i): sql_random(distribution='normal', center='x_param' + str(i),
                                                         half_width='x_param' + str(i) + '/' + str(spreading),
                                                         data_type='float') for i in range(5)})

    # Add 'y_param' values (1-7 and 9) to the dictionary
    random_params.update({'y_param' + str(i): sql_random(distribution='normal', center='y_param' + str(i),
                                                         half_width='y_param' + str(i) + '/' + str(spreading),
                                                         data_type='float') for i in range(7)})

    # Special case for 'y_param8'
    random_params.update({'y_param8': sql_random(distribution='binomial', one_ratio=one_ratio, total=total)})

    # 'y_param9' value addition
    random_params.update({'y_param9': sql_random(distribution='normal', center='y_param9',
                                                 half_width='y_param9/' + str(spreading), data_type='float')})

    # Remove 'y_param5' from the dictionary
    del random_params['y_param5']

    return random_params


def GenerateDataSetIoT(schema_name, nb_partitions, nb_signals_per_partitions,spreading_inter=8,spreading_intra=10, one_ratio=5, total=100):
    """
    Generates a dataset for IoT based on specified configurations.

    :param schema_name: Name of the database schema to use.
    :param nb_partitions: Number of partitions desired in the dataset.
    :param nb_signals_per_partitions: Number of signals per partition.
    :param spreading_inter: Variability factor for inter-partition parameter randomization. Default is 8.
    :param spreading_intra: Variability factor for intra-partition parameter randomization. Default is 10.
    :param one_ratio: Parameter for the binomial distribution used in signal randomization. Default is 5.
    :param total: Total count for the binomial distribution used in signal randomization. Default is 100.

    :return: SQL query string to fetch the generated IoT dataset and a list containing columns ['X', 'Y'].
    """
    # generation params
    singlesignalparam = generatesinglesensordata(table_name='ts_params', schema_name=schema_name)

    # randomize parameter inter partition
    random_interpartition = generaterandomsignalparams(spreading=spreading_inter, one_ratio=0, total=100)
    random_intrapartition = generaterandomsignalparams(spreading=spreading_intra, one_ratio=one_ratio, total=total)
    params_partitions = generaterandomsamples(singlesignalparam, random_interpartition, nb_partitions).drop(
        columns='PARTITION_ID')
    shape0 = params_partitions.shape

    params_signals = generaterandomsamples(params_partitions, random_intrapartition, nb_signals_per_partitions)
    shape1 = params_signals.shape
    # generate the signals
    df_signals = generationmultiplesignals(params_signals, id_columns='id', id_partition='partition_id')

    return df_signals.show_query(), ['X', 'Y']

GenerateEquallyDistributedDataSetIoT = EquallyDistributed(GenerateDataSetIoT)



def GenerateDatasetSeries(table_name, nb_partitions=20000,nb_coeffs=6, noise = 0.01, series_length=120,database=tdml.context.context._get_current_databasename()):
    """
     Generates a series dataset with given parameters and stores the dataset in a table.

     :param table_name: Name of the target table where the generated dataset will be stored.
     :param nb_partitions: Number of partitions desired in the dataset. Default is 20000.
     :param nb_coeffs: Number of coefficients for the series. Default is 6.
     :param noise: Noise factor to introduce into the generated series. Default is 0.01.
     :param series_length: Length of the series. Default is 120.
     :param database: Name of the database to use. Default is extracted from the current context's URL.

     :return: DataFrame containing the generated series dataset.
     """

    # Generate coefficients and their normalizations
    coeffs = ','.join(['CAST(RANDOM(-9999999,9999999) AS FLOAT)/2/9999999*EXP((-10.)*(1-1)) AS A'+str(i+1) for i in range(nb_coeffs)])
    module = 'SQRT('+'+'.join(['A'+str(i+1)+'**2' for i in range(nb_coeffs)])+')'
    normalized_coeffs = ','.join([f'A{i+1} / Module*0.99 AS A{i+1}_' for i in range(nb_coeffs)])

    N =int( nb_partitions/9999)+1

    ref_table = f"""
            (
             SELECT  pd
             FROM {database}.TABLE_FOR_GENERATION
             EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND
             ) B
        """

    query_long = f"""
            select
                row_number() over (
                    order by  pd) as pd
            from
                {ref_table}"""

    if N > 1:
        for iter in range(N-1):
            query_long += f"""
                UNION ALL
                select
                row_number() over (
                    order by  pd)
                + (SEL count(*) FROM {ref_table})*({iter}+1)
                as pd
            from
                {ref_table}"""


    query_coeffs = f"""
    CREATE TABLE {database}.TEMP_COEFFS AS
    (
    SEL
        CASE WHEN E.n< {nb_partitions}+1 THEN E.n END AS PARTITION_ID
    ,	CASE WHEN B.n< 2 THEN B.n END AS ID
    ,	{coeffs}
    ,	{module} as Module
    ,	{normalized_coeffs}
    FROM
    (
    SEL
        row_number() OVER (ORDER BY A.pd) as n
    FROM
        (
        SELECT  pd
        FROM {database}.TABLE_FOR_GENERATION
        EXPAND ON duration AS pd BY ANCHOR PERIOD ANCHOR_SECOND
        ) A
    ) B
    ,
    (
    SEL
        row_number() OVER (ORDER BY A.pd) as n
    FROM
        (
        {query_long}
        ) A
    ) E
    WHERE PARTITION_ID IS NOT NULL AND ID IS NOT NULL
    ) WITH DATA
    NO PRIMARY INDEX
    """

    variables = ','.join(['X'+str(i+1) for i in range(nb_coeffs)])
    init_variables = ','.join(['CAST(RANDOM(-9999999,9999999) AS FLOAT)/2/9999999/10 AS X'+str(i+1) for i in range(nb_coeffs)])
    calculated_variables = '+'.join([f'direct.X{i+1}*coeffs.A{i+1}_' for i in range(nb_coeffs)])
    shifted_variables = ','.join([f'direct.X{i+1} as X{i+2}' for i in range(nb_coeffs-1)])

    query_generation = f"""
    CREATE TABLE {database}.{table_name} AS
    (
    WITH RECURSIVE temp_table (PARTITION_ID, ID, {variables}, depth) AS
    ( 
        SEL
            PARTITION_ID
        ,	ID
        ,	{init_variables}
        ,	0 as depth
        FROM
        {database}.TEMP_COEFFS coeffs
    UNION ALL
      SELECT 
            direct.PARTITION_ID as ID
      ,		direct.ID + 1 as ID
      ,		{calculated_variables}*0.9 + CAST(RANDOM(-9999999,9999999) AS FLOAT)/2/9999999*{noise}  as X1
      ,		{shifted_variables}
      ,     direct.depth+1 AS newdepth
      FROM temp_table direct, {database}.TEMP_COEFFS coeffs
      WHERE direct.PARTITION_ID = coeffs.PARTITION_ID
      AND newdepth < {series_length+1}
    )
    SELECT PARTITION_ID, ID, X1 as Y FROM temp_table
    ) WITH DATA
    PRIMARY INDEX (PARTITION_ID)
    """

    try:
        tdml.get_context().execute(f'DROP TABLE {database}.TEMP_COEFFS')
    except:
        print(f'unable to drop {database}.TEMP_COEFFS')
    tdml.get_context().execute(query_coeffs)
    print(f'{database}.TEMP_COEFFS created')
    try:
        tdml.get_context().execute(f'DROP TABLE {database}.{table_name}')
    except:
        print(f'unable to drop {database}.{table_name}')
    tdml.get_context().execute(query_generation)
    print(f'{database}.{table_name} created')

    return tdml.DataFrame(tdml.in_schema(database,table_name))


def plot_distribution(table_name, database):
    """
    Plots the data distribution of a given table across different AMPs in Teradata.
    It fetches the data distribution and table definition and then visualizes and prints them respectively.

    Parameters:
    :param table_name: str
        The name of the table whose distribution needs to be plotted.
    :param database: str
        The name of the database where the table resides.

    Returns:
    None

    Note:
    This function specifically works with Teradata and utilizes the teradataml library for fetching data.
    """

    # SQL query to fetch the data distribution of the specified table across AMPs.
    query = f"""
    SELECT
        vproc AS AMP_
    ,   TableName (FORMAT 'X(20)')
    ,   CurrentPerm
    FROM DBC.TableSizeV
    WHERE DatabaseName = '{database}'
    AND TableName = '{table_name}'
    """

    # Execute the SQL query to get data distribution and then convert the results to a pandas DataFrame.
    df = tdml.DataFrame.from_query(query).to_pandas()

    # Plot the data distribution using a bar chart with AMPs on the x-axis and CurrentPerm on the y-axis.
    df.plot(x='AMP_', y='CurrentPerm', kind='bar', title=f"Data Distribution for {database}.{table_name}")

    # Fetch and print the table definition from Teradata.
    print(tdml.execute_sql(f'SHOW TABLE {database}.{table_name}').fetchall()[0][0].replace('\r', '\n'))

    return


def add_multiplicative_gaussian_noise(df, series_id, column, column_flag = [], stddev=0.1, noise_type='proportional', row_axis_type = 'TIMECODE', row_axis = 'TD_TIMECODE'):
    """
    Add either multiplicative (proportional) or additive Gaussian noise to specific column(s) of a DataFrame.

    Parameters:
    - df: Teradata DataFrame object representing the data to which noise will be added.
    - series_id: String representing the identifier for the data series.
    - column: String or List of Strings representing the column name(s) to which noise will be added.
    - stddev: Float or List of Floats representing the standard deviation of the Gaussian noise. Default is 0.1.
    - noise_type: String or List of Strings specifying the type of noise ('proportional' or 'additive'). Default is 'proportional'.

    Returns:
    - DataFrame with added Gaussian noise.
    """
    df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)

    # Convert single column name and stddev to lists if they are not already.
    if type(column) == str:
        column = [column]
    if type(stddev) != list:
        stddev = [stddev] * len(column)
    if type(noise_type) != list:
        noise_type = [noise_type] * len(column)

    def gen_query_(df, series_id, column, stddev=0.1, noise_type='proportional', column_type = 'float'):
        """
        Generate a subquery for the given column and stddev using TD_GENSERIES4FORMULA to produce noisy data.
        """
        # Determine formula based on noise type.
        if column_type == 'float':
            if noise_type == 'proportional':
                formula = f'Y=X1*(1 + {stddev}*sqrt(-2.0*ln(RANDOM(1,999999999)/1000000000.0)) * cos(2.0*3.14159265358979323846 * RANDOM(0,999999999)/1000000000.0))'
            elif noise_type == 'additive':
                formula = f'Y=X1 + {stddev}*sqrt(-2.0*ln(RANDOM(1,999999999)/1000000000.0)) * cos(2.0*3.14159265358979323846 * RANDOM(0,999999999)/1000000000.0)'

        else:
            formula = f'Y=RANDOM(0,1)'

        # Construct the subquery.
        query = f"""
        EXECUTE FUNCTION TD_GENSERIES4FORMULA (
            SERIES_SPEC(
                TABLE_NAME({df._table_name}),
                ROW_AXIS({row_axis_type}({row_axis})),
                SERIES_ID({series_id}),
                PAYLOAD(
                    FIELDS ({column}),
                    CONTENT(REAL)
                    )
             ),
            FUNC_PARAMS(FORMULA('{formula}'))
        )
        """
        return query

    # Create a list of subqueries for each column, stddev, and noise type combination.
    queries = [gen_query_(df, series_id, column_, stddev_, noise_type_) for column_, stddev_, noise_type_ in
               zip(column, stddev, noise_type)] + \
            [gen_query_(df, series_id, column_,  column_type='flag') for column_ in
     column_flag]

    # Join all the subqueries.
    sub_query_list = ', \n'.join(['(' + query + ') B' + str(i) for i, query in enumerate(queries)])

    # Construct the WHERE clause for the main query.
    where_list = ' AND \n'.join(
        [f'A.ROW_I = B{i}.ROW_I AND A.{series_id} = B{i}.{series_id}' for i in range(len(queries))])

    # Prepare column names for the main SELECT query.
    columns = df.columns
    all_column = column+column_flag
    for i, c in enumerate(columns):
        if c in all_column:
            columns[i] = f'B{all_column.index(c)}.MAGNITUDE AS ' + c
        else:
            columns[i] = 'A.' + c
    columns = ', \n'.join(columns)

    select_ = ', \n'.join(['D.' + c for c in df.columns])
    # Construct the main query.
    query2 = f"""
    SELECT
    {columns}
    FROM (SEL {select_}, ROW_NUMBER() OVER (PARTITION BY D.{series_id} ORDER BY D.{row_axis}) -1 AS ROW_I FROM {df._table_name} D) A,
    {sub_query_list}
    WHERE  {where_list}
    """

    # Return the DataFrame after executing the main query.
    return tdml.DataFrame.from_query(query2)


def gen_query(df, n, replication_column = 'REPLICATION_ID'):
    """
    Generates a query that replicates the given dataframe n times,
    labeling each replication with a unique identifier in the column 'REPLICATION_ID'.

    Parameters:
    - df: DataFrame object, data that needs to be replicated.
    - n: Integer, number of replications required.

    Returns:
    - A new DataFrame with n times the original data with a new column 'REPLICATION_ID' to identify each replication.
    """
    df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)

    # Construct a subquery using Teradata's TD_GENSERIES4FORMULA function.
    # This appears to generate a series with a payload that goes from 0 to n-1.
    # This payload will be used later as REPLICATION_ID.
    query = f"""
    EXECUTE FUNCTION TD_GENSERIES4FORMULA(
    GENSERIES_SPEC(
       INSTANCE_NAMES('{{"series_id": 3 }}'),
       DT(INTEGER),
       GEN_PAYLOAD(0,1,{n})
    ),
    FUNC_PARAMS(FORMULA('Y = X1')), 
    OUTPUT_FMT(INDEX_STYLE(NUMERICAL_SEQUENCE))
    )
     """

    # Construct the main query that joins the original dataframe with the generated series,
    # effectively replicating the data n times.
    # It also creates a new column REPLICATION_ID using the payload from the generated series.
    select_ = ', \n'.join(['A.' + c for c in df.columns])
    query2 = f"""
    SELECT 
        {select_}
    ,   B.ROW_I AS {replication_column}
    FROM {df._table_name} A,
    ({query}) B
    """

    # Print the main query.
    #print(query2)

    # Return the result of the query as a DataFrame.
    return tdml.DataFrame.from_query(query2)


def add_missing_values(df, series_id, column, missing_ratio):
    """
    Introduce missing values to a specific column or columns of a DataFrame based on a given ratio.

    Parameters:
    - df: Teradata DataFrame object, data in which the missing values will be introduced.
    - series_id: String representing the identifier for the data series.
    - column: String or List of Strings representing the column name(s) to which missing values will be added.
    - missing_ratio: Float or List of Floats, ratio of missing values. If the generated random value is greater than this ratio, the value is kept as is; otherwise, it's set to NULL.

    Returns:
    - DataFrame with missing values introduced as per the specified ratio.
    """
    df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)
    # Convert single column name and missing_ratio to lists if they are not already.
    if type(column) == str:
        column = [column]
    if type(missing_ratio) != list:
        missing_ratio = [missing_ratio] * len(column)

    def gen_query_(df, series_id, column):
        """
        Generate a subquery using TD_GENSERIES4FORMULA to produce random values.
        These random values will be used to determine if an original value should be replaced with NULL.
        """

        df._DataFrame__execute_node_and_set_table_name(df._nodeid, df._metaexpr)

        query = f"""
        EXECUTE FUNCTION TD_GENSERIES4FORMULA (
            SERIES_SPEC(
                TABLE_NAME({df._table_name}),
                ROW_AXIS(TIMECODE(TD_TIMECODE)),
                SERIES_ID({series_id}),
                PAYLOAD(
                    FIELDS ({column}),
                    CONTENT(REAL)
                    )
             ),
            FUNC_PARAMS(FORMULA('Y=X1'))
        )
         """
        return query

    # Create a list of subqueries for each column.
    queries = [gen_query_(df, series_id, column_) for column_ in column]

    # Construct the list of columns for the main SELECT query.
    columns = df.columns
    for i, c in enumerate(columns):
        if c in column:
            columns[
                i] = f'CASE WHEN B{column.index(c)}.MAGNITUDE > {missing_ratio[column.index(c)]} THEN A.{c} ELSE NULL END AS {c}'
        else:
            columns[i] = f'A.{c}'
    columns = ', \n'.join(columns)

    # Join all the subqueries.
    sub_query_list = ', \n'.join(['(' + query + ') B' + str(i) for i, query in enumerate(queries)])

    # Construct the WHERE clause for the main query.
    where_list = ' AND \n'.join(
        [f'A.ROW_I = B{i}.ROW_I AND A.{series_id} = B{i}.{series_id}' for i in range(len(queries))])

    select_ = ', \n'.join(['D.' + c for c in df.columns])
    # Build the main query.
    query2 = f"""
    SELECT
    {columns}
    FROM (SEL {select_}, ROW_NUMBER() OVER (PARTITION BY D.{series_id} ORDER BY D.TD_TIMECODE) -1 AS ROW_I FROM {df._table_name} D) A,
    {sub_query_list}
    WHERE {where_list}
    """

    # Return the modified data as a DataFrame.
    return tdml.DataFrame.from_query(query2)


def gen_columns(n_x, n_f):
    X_Features = ['X' + str(i + 1) for i in range(n_x)]
    if n_f == 1:
        F_Features = ['Flag']
    elif n_f > 1:
        F_Features = ['Flag' + str(i + 1) for i in range(n_f)]
    return X_Features, F_Features


from teradataml.context.context import _get_database_username
from teradataml import DataFrame, execute_sql, in_schema


def create_seed(n_x=9, n_f=1):
    X_Features, F_Features = gen_columns(n_x, n_f)
    X_Features = ','.join(['0 AS ' + feat for feat in X_Features])

    if len(F_Features) == 1:
        F_Features = '0 AS ' + F_Features[0]
    elif len(F_Features) > 1:
        F_Features = ','.join(['0 AS ' + feat for feat in F_Features])

    user_database = _get_database_username()

    query = f"""
    CREATE MULTISET VOLATILE TABLE {user_database}.dataset_generation_seed AS
    (
    SELECT 
    {X_Features},
    {F_Features}
    ) WITH DATA
    NO PRIMARY INDEX
    ON COMMIT PRESERVE ROWS
    """

    try:
        execute_sql(f'DROP TABLE {user_database}.dataset_generation_seed')
    except:
        pass  # Handle the exception if needed

    execute_sql(query).fetchall()

    return DataFrame(in_schema(user_database, 'dataset_generation_seed'))


from tdstone2.dataset_generation import gen_query, add_multiplicative_gaussian_noise


def GenerateDataSetNew(n_x=9, n_f=1, n_partitions=2, n_rows=5,
                       noise_classif=0.01,
                       train_test_split_ratio=0.2,
                       database=tdml.context.context._get_current_databasename()):
    df = create_seed(n_x, n_f)

    df = gen_query(n=n_partitions, df=df)
    df = df.assign(Partition_ID=df.REPLICATION_ID)[['Partition_ID'] + df.columns[0:-1]]


    subquery_redistribution = InverseHash(df.show_query(), n_factor_hash_map=500)
    query = f"""
    SELECT
      B.NEW_PARTITION_ID AS Partition_ID
    , {','.join([c for c in df.columns if c != 'Partition_ID'])}
    FROM ({df.show_query()}) A
    , ({subquery_redistribution}) B
    WHERE A.Partition_ID = B.Partition_ID
    """
    df2 = tdml.DataFrame.from_query(query)

    user_database = _get_database_username()
    df2.to_sql(schema_name=user_database, table_name='temp_seed_distributed', primary_index='Partition_ID',
               temporary=True, if_exists='replace')
    df = tdml.DataFrame(tdml.in_schema(user_database, 'temp_seed_distributed'))


    X_Features, F_Features = gen_columns(n_x, n_f)

    df_coefficients = add_multiplicative_gaussian_noise(
        df,
        'Partition_ID',
        column=X_Features,
        row_axis_type='SEQUENCE',
        row_axis='Partition_ID',
        noise_type='additive'
    )

    df_coefficients = df_coefficients.assign(
        drop_columns=True,
        Partition_ID=df_coefficients.Partition_ID,
        **{x.replace('X', 'C'): df_coefficients[x] for x in df.columns if x.startswith('X')}
    )

    df_coefficients.to_sql(schema_name=user_database, table_name='temp_coefficients', primary_index='Partition_ID',
                           temporary=True, if_exists='replace')

    df_features = gen_query(n=n_rows, df=df)
    df_features = df_features.assign(ID=df_features.REPLICATION_ID)[['Partition_ID', 'ID'] + df_features.columns[1:-1]]
    df_features = add_multiplicative_gaussian_noise(
        df_features,
        'Partition_ID',
        column=X_Features,
        column_flag=F_Features,
        row_axis_type='SEQUENCE',
        row_axis='ID',
        noise_type='additive'
    )
    df_features.to_sql(schema_name=user_database, table_name='temp_features', primary_index='Partition_ID',
                       temporary=True, if_exists='replace')
    df_features = DataFrame(in_schema(user_database, 'temp_features'))

    query = f"""
        SELECT 
        AA.Partition_ID
        , AA.ID
        ,   {', '.join(['AA.'+c for c in X_Features])}
        ,   {', '.join(['AA.'+c for c in F_Features])}   
        , AA.Y1   
        , CASE WHEN (AA.Y1 > AVG(AA.Y1)
                     OVER (PARTITION BY AA.PARTITION_ID))
        THEN 1 ELSE 0 END AS Y2
        , AA.FOLD
        FROM (
        SELECT
            A.Partition_ID as Partition_ID
        ,   B.ID as "ID"
        ,   {', '.join(X_Features)}
        ,   {','.join(F_Features)}
        ,   {'+'.join(['C' + str(i + 1) + '*' + X_Features[i] for i in range(n_x)])} as Y1
        ,   CASE WHEN B.ID -1 < {int(n_rows * train_test_split_ratio)} THEN 'train' ELSE 'test' END as FOLD        
        FROM {user_database}.temp_coefficients A
        , {user_database}.temp_features B
        WHERE A.Partition_ID = B.Partition_ID
        ) AA
    """

    return tdml.DataFrame.from_query(query)

GenerateEquallyDistributedDataSet = EquallyDistributed(GenerateDataSet)