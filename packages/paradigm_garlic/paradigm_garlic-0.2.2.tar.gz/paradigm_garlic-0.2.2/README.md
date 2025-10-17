
# garlic 🧄

cli and python interface for interacting with Snowflake

Features
- run queries against snowflake using simple UX
- auto-convert query results to polars dataframes
- convenience functions for:
    - formatting timestamps for use in SQL queries
    - setting the context (warehouse, database, schema, role)
    - listing catalog of databases, schemas, tables, and query history
    - creating tables from select queries


## Installation

```bash
uv add paradigm_garlic
```

## Example Usage

#### Simplest example
```python
import garlic

dataframe = garlic.query('SELECT * FROM my_table')
```

#### Set different default warehouse:
```python
import garlic

garlic.use_warehouse('BIG_WAREHOUSE')
dataframe = garlic.query('SELECT * FROM my_table')
```

#### Read from Snowflake management tables

```python
import garlic

databases = garlic.list_databases()
schemas = garlic.list_schemas()
tables = garlic.list_tables()
query_history = garlic.list_query_history()
```

#### Use timestamps in CLI queries

```python
import garlic
import datetime

sql = """
SELECT *
FROM my_table
WHERE
    block_timestamp >= {start_time}
    AND block_timestamp < {end_time}
""".format(
    start_time=garlic.format_timestamp('2024-01-01'),
    end_time=garlic.format_timestamp(datetime.datetime.now()),
)

dataframe = garlic.query(sql)
```

#### Set environment context

```python
garlic.use_warehouse('BIG_WH')
garlic.use_schema('MY_SCHEMA')
garlic.use_database('MY_DB')
garlic.use_role('MY_ROLE')

dataframe = garlic.query('SELECT * FROM my_table')
```

#### Create table from select query

```python
import garlic

garlic.create_table(
    target_table='new_table_name',
    select_sql='SELECT * FROM my_table WHERE some_column = some_value',
)
```
