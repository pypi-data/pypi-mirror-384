# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 14:44:33 2021

@author: dm250067
"""


from functools import wraps
import teradataml as tdml
import re
from tdstone2.utils import generate_sequence


def setup_table_for_model_generation(database=tdml.context.context._get_current_databasename()):
    query = f"""
        SEL CAST(DATE '2022-01-01' AS TIMESTAMP) as t0
            , t0 + CAST(9999 AS INTERVAL SECOND(4)) as t1
            , PERIOD(t0, t1) as duration

    """
    tdml.DataFrame.from_query(query).to_sql(schema_name=database, table_name='TABLE_FOR_GENERATION',if_exists='replace')
    return

def InverseHash(subquery, n_factor_hash_map=50, partition_column = 'Partition_ID'):
    """ A SQL query that compute interger partition ID for each Partition_ID
    values output by the subquery, whatever the data type.

    The results of the query consist of three columns:
        - the Partition_ID column of the input subquery
        - the New_Partition_ID which is an integer
        - the AMP_ID corresponding the retulst of HASHAMP(HASHBUCKET(HASHROW(
            New_Partition_ID)))

    :param subquery: a SQL query as a string that output a column named
    Partition_ID.
    :param n_factor_hash_map: the HASHAMP(HASHBUCKET(HASHROW())) is applied
    to a list of integer from 1 to n_factor_hash_map*(hashamp()+1)
    :return: a SQL query that returns Partition_ID, New_Partition_ID and
    AMP_ID.
    """

    query = f"""
            SELECT
                A2.{partition_column}
            ,	A1.New_Partition_ID
            ,	A1.AMP_ID
        FROM
        (
            SELECT
                I.New_Partition_ID
            ,	I.AMP_ID
            ,	I.row_num4 as row_num
            FROM (
                SELECT
                    B.New_Partition_ID
                ,	B.AMP_ID
                ,	ROW_NUMBER() OVER
                (ORDER BY B.row_key,B.AMP_ID ) as row_num
                ,	ROW_NUMBER() OVER
                (PARTITION BY B.row_key ORDER BY B.AMP_ID  ) as row_num2
                ,	ROW_NUMBER() OVER
                (PARTITION BY B.AMP_ID ORDER BY B.row_key ) as row_num3
                ,	CASE
                    WHEN row_num3 MOD 2 = 1 THEN row_num
                    ELSE row_num-2*row_num2 + hashamp()+2
                    END as row_num4
                FROM
                (
                    SELECT
                        A.RNK as New_Partition_ID
                    ,	A.AMP_ID
                    ,	ROW_NUMBER() OVER
                    ( PARTITION BY A.AMP_ID ORDER BY  A.RNK) as row_key
                    FROM
                    (
                        SELECT
                            DD.RNK
                        ,   HASHAMP(HASHBUCKET(HASHROW(DD.RNK))) as AMP_ID
                        FROM
                            ({generate_sequence(n=n_factor_hash_map*215, column_name='RNK')}) DD
                        --QUALIFY RNK < 50*(hashamp()+1)+1 -- large enough
                    ) A
                    QUALIFY row_key <
                    (
                        SELECT count(distinct A.Partition_ID)
                        FROM ({subquery}) A)/(hashamp()+1)+1+1
                ) B
            ) I
        ) A1
        ,
        (
            SELECT
                F.{partition_column}
            ,	ROW_NUMBER() OVER (ORDER BY F.Partition_size DESC) as row_num
            FROM (
                SELECT
                    A.{partition_column}
                ,	count(*) as Partition_size
                FROM ({subquery}) A
                GROUP BY 1
            ) F
        ) A2
        WHERE A1.row_num = A2.row_num
        """
    return query


def EquallyDistributed(func):
    """A decorator that reverses the hash function to equally distributed
    partitions among the AMP, so that we have the same number of partition
    per AMP."""
    # Define the wrapper function to return.
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Call the decorated function and store the result.
        subquery_dataset, features = func(*args, **kwargs)

        # Get the conversion of the Partition_ID to a New_Partition_ID that
        # is an integer that fits better with the hash function
        subquery_redistribution = InverseHash(subquery_dataset)

        # Rewrite the query
        query = f"""
        SELECT
        B.New_Partition_ID as Partition_ID
        ,   A.ID
        ,   {',  '.join(features)}
        FROM ({subquery_dataset}) A
        , ({subquery_redistribution}) B
        WHERE A.Partition_ID = B.Partition_ID
        """
        return query, features
    return wrapper

def EquallyDistribute(df, partition_column = 'Partition_ID'):

    subquery_redistribution = InverseHash(df.show_query(), partition_column = partition_column)
    features = [c for c in df.columns if c not in [partition_column]]
    # Rewrite the query
    query = f"""
    SELECT
    B.New_Partition_ID as {partition_column}
    ,   {',  '.join(features)}
    FROM ({df.show_query()}) A
    , ({subquery_redistribution}) B
    WHERE A.{partition_column} = B.{partition_column}
    """
    return tdml.DataFrame.from_query(query)


def PlotDistribution(schemaT, table_name, partition='partition_id', dataframe_only=False):
    """
    Generates a SQL query to assess the data distribution across partitions of a specified table
    and optionally visualizes this distribution as a bar chart.

    This function constructs a query that calculates the number of distinct partitions and the total
    number of rows for each AMP (Access Module Processor) in the table. If `dataframe_only` is set to True,
    it returns the query results as a DataFrame. Otherwise, it visualizes the distribution of rows across
    AMPs using a bar chart.

    Parameters
    ----------
    schemaT : str
        The name of the database schema containing the table.
    table_name : str
        The name of the table to analyze.
    partition : str, optional
        The column used to partition the data. Defaults to 'partition_id'.
    dataframe_only : bool, optional
        Determines the return format. If True, returns the query results as a DataFrame without plotting.
        Otherwise, plots the distribution and returns the DataFrame. Defaults to False.

    Returns
    -------
    pandas.DataFrame or None
        If `dataframe_only` is True, returns a DataFrame containing the data distribution results.
        If `dataframe_only` is False, visualizes the data distribution as a bar chart and also returns
        the DataFrame.
    """
    # Construct the SQL query to analyze data distribution
    query = f"""
    SELECT
        hashamp(hashbucket(hashrow({partition}))) as AMP_ID,  -- Calculate the AMP ID
        count(distinct {partition}) as Nb_Partitions,         -- Count distinct partitions in each AMP
        count(*) as Nb_rows                                   -- Count total rows in each AMP
    FROM {schemaT}.{table_name}
    GROUP BY 1  -- Group results by AMP ID
    --ORDER BY 3 DESC  -- Uncomment to order by number of rows descending
    """

    # Execute the query and return results as a DataFrame
    if dataframe_only:
        # Return the query results directly as a DataFrame
        return tdml.DataFrame.from_query(query)
    else:
        # Execute the query and store results in a DataFrame
        df = tdml.DataFrame.from_query(query)
        # Convert to Pandas DataFrame, sort by AMP ID, and plot the distribution of rows across AMPs
        df.to_pandas().sort_values('AMP_ID').plot(x='AMP_ID', y='Nb_rows', kind='bar', figsize=(30, 10), xlabel='AMP_ID', ylabel='nb rows')
        # Return the DataFrame after plotting
        return df


