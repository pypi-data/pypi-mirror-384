from __future__ import annotations

import typing

from . import env
from . import execute

if typing.TYPE_CHECKING:
    import polars as pl
    from snowflake.connector import SnowflakeConnection
    from snowflake.connector.cursor import SnowflakeCursor


def list_databases(
    *,
    cursor: SnowflakeCursor | None = None,
    conn: SnowflakeConnection | None = None,
) -> pl.DataFrame:
    import polars as pl

    if cursor is None:
        cursor = env.get_cursor(conn=conn)

    cursor.execute('SHOW DATABASES')
    raw = cursor.fetchall()

    raw_schema: dict[str, pl.DataType | type[pl.DataType]] = {
        'created_on': pl.Datetime(
            time_unit='us', time_zone='America/Los_Angeles'
        ),
        'name': pl.String,
        'is_default': pl.String,
        'is_current': pl.String,
        'origin': pl.String,
        'owner': pl.String,
        'comment': pl.String,
        'options': pl.String,
        'retention_time': pl.String,
        'kind': pl.String,
        'owner_role_type': pl.String,
        'object_visibility': pl.String,
    }

    catalogs = pl.DataFrame(
        raw,
        schema=raw_schema,
        orient='row',
        infer_schema_length=999999,
    )

    return catalogs


def list_schemas(
    catalog: str | list[str] | None = None,
    cursor: 'SnowflakeCursor' | None = None,
    conn: 'SnowflakeConnection' | None = None,
) -> 'pl.DataFrame':
    import polars as pl

    if isinstance(catalog, str):
        sql = 'SELECT * FROM {catalog}.INFORMATION_SCHEMA.SCHEMATA'.format(
            catalog=catalog
        )
        return (
            execute.query(sql, cursor=cursor, conn=conn)
            .filter(pl.col('SCHEMA_NAME') != 'INFORMATION_SCHEMA')
            .sort('CATALOG_NAME', 'SCHEMA_NAME')
        )

    elif isinstance(catalog, list) or catalog is None:
        if catalog is None:
            catalogs = list_databases(cursor=cursor, conn=conn)
            catalog = catalogs['name'].to_list()

        results: list[pl.DataFrame] = []
        for item in catalog:
            if item in ('SNOWFLAKE_SAMPLE_DATA',):
                continue
            try:
                df = list_schemas(item, cursor=cursor, conn=conn)
                results.append(df)
            except Exception:
                print('could not access', item)
        if not results:
            raise Exception('no accessible catalogs found')
        return pl.concat(results, how='vertical_relaxed')

    else:
        raise ValueError('catalog must be str, list[str], or None')


def list_tables(
    catalog: str | list[str],
    all_columns: bool = False,
    cursor: SnowflakeCursor | None = None,
    conn: SnowflakeConnection | None = None,
) -> pl.DataFrame:
    import polars as pl

    # get list of catalogs
    if catalog is None:
        catalogs = list_databases(cursor=cursor, conn=conn)
        catalog = catalogs['name'].to_list()

    # get tables of each catalog
    if isinstance(catalog, list):
        results = []
        for item in catalog:
            if item == 'SNOWFLAKE_SAMPLE_DATA':
                continue
            print('getting tables of', item)
            try:
                df = list_tables(
                    item, cursor=cursor, conn=conn, all_columns=all_columns
                )
                results.append(df)
            except Exception:
                print('could not access', item)
        return pl.concat(results)

    # execute query
    sql = 'SELECT * FROM {catalog}.INFORMATION_SCHEMA.TABLES'.format(
        catalog=catalog
    )
    df = execute.query(sql, cursor=cursor, conn=conn)

    # process result
    df = df.filter(pl.col.TABLE_SCHEMA != 'INFORMATION_SCHEMA')
    if not all_columns:
        columns = [
            'TABLE_CATALOG',
            'TABLE_SCHEMA',
            'TABLE_NAME',
            'TABLE_TYPE',
            'IS_TRANSIENT',
            'ROW_COUNT',
            'BYTES',
            'CLUSTERING_KEY',
            'LAST_ALTERED',
        ]
        df = df.select(columns)
    df = df.sort('TABLE_CATALOG', 'TABLE_SCHEMA', 'TABLE_NAME')

    return df


def list_columns(
    tables: str | list[str],
    all_columns: bool = False,
    cursor: SnowflakeCursor | None = None,
    conn: SnowflakeConnection | None = None,
) -> pl.DataFrame:
    import polars as pl

    # normalize tables to list format
    if isinstance(tables, str):
        tables = [tables]

    # parse all tables and check if they're fully qualified
    parsed_tables = []
    all_fully_qualified = True

    for table in tables:
        parts = table.split('.')
        if len(parts) == 3:
            catalog, schema, table_name = parts
            parsed_tables.append((catalog, schema, table_name))
        elif len(parts) == 2:
            all_fully_qualified = False
            schema, table_name = parts
            # get current catalog if not specified
            if cursor is None:
                cursor = env.get_cursor(conn=conn)
            cursor.execute('SELECT CURRENT_DATABASE()')
            catalog = cursor.fetchone()[0]  # type: ignore
            parsed_tables.append((catalog, schema, table_name))
        else:
            raise ValueError(
                f'Table must be in format "catalog.schema.table" or "schema.table", got: {table}'
            )

    # if all tables are fully qualified, use a single UNION ALL query
    if all_fully_qualified and len(parsed_tables) > 1:
        subqueries = []
        for catalog, schema, table_name in parsed_tables:
            subquery = """
                SELECT * FROM {catalog}.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
            """.format(catalog=catalog, schema=schema, table_name=table_name)
            subqueries.append(f'({subquery.strip()})')

        sql = '\nUNION ALL\n'.join(subqueries)
        df = execute.query(sql, cursor=cursor, conn=conn)

    # otherwise, use the loop approach
    else:
        results = []
        for catalog, schema, table_name in parsed_tables:
            sql = """
                SELECT * FROM {catalog}.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
            """.format(catalog=catalog, schema=schema, table_name=table_name)

            try:
                df_part = execute.query(sql, cursor=cursor, conn=conn)
                results.append(df_part)
            except Exception as e:
                print(
                    f'Could not access columns for {catalog}.{schema}.{table_name}: {e}'
                )

        if not results:
            raise Exception('No accessible tables found')

        df = pl.concat(results, how='vertical_relaxed')

    # filter columns if requested
    if not all_columns:
        columns = [
            'TABLE_CATALOG',
            'TABLE_SCHEMA',
            'TABLE_NAME',
            'COLUMN_NAME',
            'ORDINAL_POSITION',
            'DATA_TYPE',
            'IS_NULLABLE',
            'COLUMN_DEFAULT',
        ]
        df = df.select(columns)

    # sort results
    df = df.sort(
        'TABLE_CATALOG', 'TABLE_SCHEMA', 'TABLE_NAME', 'ORDINAL_POSITION'
    )

    return df


# def list_columns(
#     tables: str | list[str],
#     all_columns: bool = False,
#     cursor: SnowflakeCursor | None = None,
#     conn: SnowflakeConnection | None = None,
# ) -> pl.DataFrame:
#     import polars as pl
#
#     # normalize tables to list format
#     if isinstance(tables, str):
#         tables = [tables]
#
#     # collect results for each table
#     results = []
#     for table in tables:
#         # parse table reference (catalog.schema.table or schema.table)
#         parts = table.split('.')
#         if len(parts) == 3:
#             catalog, schema, table_name = parts
#         elif len(parts) == 2:
#             schema, table_name = parts
#             # get current catalog if not specified
#             if cursor is None:
#                 cursor = env.get_cursor(conn=conn)
#             cursor.execute('SELECT CURRENT_DATABASE()')
#             catalog = cursor.fetchone()[0]
#         else:
#             raise ValueError(
#                 f'Table must be in format "catalog.schema.table" or "schema.table", got: {table}'
#             )
#
#         # query columns for this table
#         sql = '''
#             SELECT * FROM {catalog}.INFORMATION_SCHEMA.COLUMNS
#             WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
#         '''.format(
#             catalog=catalog, schema=schema, table_name=table_name
#         )
#
#         try:
#             df = execute.query(sql, cursor=cursor, conn=conn)
#             results.append(df)
#         except Exception as e:
#             print(f'Could not access columns for {table}: {e}')
#
#     if not results:
#         raise Exception('No accessible tables found')
#
#     # combine results
#     df = pl.concat(results, how='vertical_relaxed')
#
#     # filter columns if requested
#     if not all_columns:
#         columns = [
#             'TABLE_CATALOG',
#             'TABLE_SCHEMA',
#             'TABLE_NAME',
#             'COLUMN_NAME',
#             'ORDINAL_POSITION',
#             'DATA_TYPE',
#             'IS_NULLABLE',
#             'COLUMN_DEFAULT',
#         ]
#         df = df.select(columns)
#
#     # sort results
#     df = df.sort('TABLE_CATALOG', 'TABLE_SCHEMA', 'TABLE_NAME', 'ORDINAL_POSITION')
#
#     return df


def list_query_history(
    *,
    n: int | None = None,
    all_columns: bool = False,
    cursor: SnowflakeCursor | None = None,
    conn: SnowflakeConnection | None = None,
) -> pl.DataFrame:
    if all_columns:
        columns = '*'
    else:
        column_names = [
            'QUERY_TEXT',
            'USER_NAME',
            'START_TIME',
            'END_TIME',
            'EXECUTION_STATUS',
            'BYTES_SCANNED',
            'BYTES_READ_FROM_RESULT',
            'BYTES_WRITTEN',
            'BYTES_WRITTEN_TO_RESULT',
            'BYTES_DELETED',
            'ROWS_PRODUCED',
            'ROWS_WRITTEN_TO_RESULT',
            'ROWS_INSERTED',
            'ROWS_UPDATED',
            'ROWS_DELETED',
            'ROWS_UNLOADED',
            'PERCENTAGE_SCANNED_FROM_CACHE',
            'QUERY_HASH',
        ]
        columns = ','.join(column_names)
    sql = 'SELECT {columns} FROM snowflake.account_usage.query_history'.format(
        columns=columns
    )
    sql = sql + ' ORDER BY START_TIME DESC'

    if n is not None:
        sql = sql + ' LIMIT ' + str(n)

    return execute.query(sql, conn=conn, cursor=cursor).sort('START_TIME')
