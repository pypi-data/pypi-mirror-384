[![PyPI Version](https://badge.fury.io/py/iql.svg)](https://pypi.python.org/pypi/iql)

<!--[![Anaconda-Server Badge](https://anaconda.org/conda-forge/iql/badges/version.svg)](https://anaconda.org/conda-forge/iql)-->

[![BuildRelease](https://github.com/iqmo-org/iql/actions/workflows/build_release.yml/badge.svg)](https://github.com/iqmo-org/iql/actions/workflows/build_release.yml)
[![Tests](https://github.com/iqmo-org/iql/actions/workflows/test_coverage.yml/badge.svg)](https://github.com/iqmo-org/iql/actions/workflows/test_coverage.yml)
[![Coverage badge](https://github.com/iqmo-org/iql/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/iqmo-org/iql/tree/python-coverage-comment-action-data)

# I\* Query Language (IQL)

IQL is a framework and a collection of Python-based extensions for financial data acquisition.

## Disclaimers

THIS PROJECT IS NOT AFFILIATED WITH, SUPPORTED BY, ENDORSED BY OR CONNECTED TO ANY OF THE COMPANIES, PRODUCTS OR SERVICES BELOW.

# Installation

```
# Install
%pip install iql --upgrade

# Load Magics to enable %iql and %%iql for VScode and Jupyter
%load_ext iql
```

# Usage

Python API

```
import iql
df1 = iql.execute(f"select * from ...")
```

Cell Magic

```
%%iql -o df1
select * from ...
```

Line Magic

```
df1 = %iql select * from ...
```

# About IQL

IQL serves two purposes: a framework for adding lightweight extensions to data pipelines through declarative SQL queries, and a collection of useful extensions.

## IQL: The Framework

IQL allows python functions to be registered and executed inline with SQL. These functions take parameters and can return DataFrames, Parquet Files, or CSVs.

```
SELECT * FROM myextension(param='abc', param2='def')
```

In this simple example, IQL extracts and preprocesses myextension. The SQL is rewritten to replace myextension, and the DataFrame is registered with the database. The exact mechanism depends on the database: for DuckDB (default database), the dataframes can be queried on the fly without loading explicitly to the database.

## IQL: The Extensions

IQL works out of the box, allowing you to execute SQL statements over your dataframes and external data sources with no configuration.

- Bloomberg Query Language (BQL)

  ```sql
  select * from bql("get(px_last) for(['IBM US Equity']) with(dates=range(-90D, 0D), fill=prev)") order by value desc limit 3
  ```

- Bloomberg BLPAPI
  ```sql
  select * from blpapi(fields=("PX_LAST","PX_OPEN", "BID"), historical=False, securities=("IBM US Equity","SPX Index"))
  ```
- Pandas operations
  ```sql
  SELECT * FROM pandas(table=xyz, pivot=('col1', 'col2', 'values'))
  ```

## Why?

SQL is a powerful declarative language, capable of expressing complex data manipulations and enabling efficient optimized processing. Often, interaction with external data is required, making it difficult to build interactive systems leveraging declarative data structures. Combining SQL with a pre-processing framework to externalize data load within the context of a SQL query makes many workflows simpler.

Modern analytical databases, such as [DuckDB](https://github.com/duckdb), provide many powerful tools to allow more to be done within SQL and eliminating the back and forth required for data loading and manipulation. IQL is intended to extend the power of these platforms without being tied to a single platform: through the use of pre-processed extensions.

### Native Formats

After preprocessing of the IQL Extension queries, the database engine will execute a native query unmodified. This minimizes the dependency on specific databases and database versions.

The native SQL format of the database engine is supported: the SQL runs unmodified except for replacement of the IQL SubQueries.

The native SubQuery syntax is preserved. Bloomberg BQL queries run without modification. REST API calls can be called via URLs directly. etc.

### Simplicity and Performance

Multiple transformations, aggregations and operations can be expressed in a single statement. This reduces the amount of code we need to write, eliminates long chains of Pandas operations, and often leads to significant performance increases.

IQL's default database is a higly efficient in-memory OLAP database called DuckDB, which requires zero configuration or administration. You may use a transient database per query, or create a long-lived database and reuse across queries. [DuckDB Performance vs Pandas](https://duckdb.org/2021/05/14/sql-on-pandas.html)

### All in One Place and Extensible

You can query REST APIs as if they were database tables. You can add custom business logic to control how certain files are retrieved, cached or pre-processed.

IQL is portable across DB environments. DuckDB is shipped by default, but can be replaced by other databases.

### How Does It Work

How does it work? IQL iterates over SQL statements (if multiple statements are used), and extracts IQL SubQuerys (ie: fred(...)). Each SubQuery is executed and stored (as a DataFrame or local file). The SQL query is modified to reference the results of the SubQuery instead of the SubQuery itself, and the database engine runs the modified SQL query.

For example, given the following query:

```
%%iql
SELECT *
  FROM fred('query1') as q1
  JOIN fred('query2') as q2
      ON q1.id=q2.id
```

In pseudocode (this is logically but not literally what happens):

```
  # pseudocode
  df_q1 = iql.execute("fred('query1")")
  df_q2 = iql.execute("fred('query2")")

  db.execute("SELECT * FROM df_q1 JOIN df_q2 on df_q1.id = df_q2.id")
```

Or, using the %iql cell magic:

# Extensions:

- [Bloomberg BQL](BLOOMBERG_BQL_README.md)

- [Bloomberg BLPAPI](https://www.bloomberg.com/professional/support/api-library/)
- [Pandas](https://pandas.pydata.org/): Allows Pandas operations to be executed within the SQL statement. Not all Pandas operations are available.

See the examples/ folder for complete examples.

## Syntax

IQL extensions are executed as functional subqueries. Each extension is registered with a unique name.

```
SELECT \*
FROM
bql("get (...) for (...)") q1
JOIN
bql("get (...) for (...)") q2
ON
q1.id = q2.id
```

See the example notebooks for more interesting examples.

## SQL Syntax

IQL uses a superset of the underlying database language. DuckDB is the default database, with a dialect similar/consistent with PostgreSQL's:
[DuckDB SQL Introduction](https://duckdb.org/docs/sql/introduction.html)
[DuckDB SQL Statements](https://duckdb.org/docs/sql/introduction)

## Quoting Strings

Strings must be properly quoted and/or escaped, according to normal Python rules. The SubQuery requires a quoted string, be careful to use different quote types for the entire SQL string and the SubQuery string.

Triple quotes are convenient, since SQL queries tend to be long and multi-line. Note the three levels of quotes: triple """, single " and single '.

```
import iql

bql_str = "get (...) for ('XYZ')"
sql_str = f"""
    -- This uses a Python f-string, which allows us to use the {bql_str} variable
    SELECT *
    FROM
        -- bql() is an IQL extension. Note the quotes around the BQL statement.
        -- if the BQL statement contains double quotes,
        bql("{bql_str}")
    """

iql.execute(sql_str)
```

In Notebooks, this is a little simpler, since the outer quotes aren't needed:

```
%%iql -o bql_df

SELECT * FROM bql("get(px_last) for ([`IBM US Equity`])")
```

# Pandas Extension

The pandas options are available in every extension, but sometimes its better to run after the data has been first populated in an earlier query.

The syntax is:

```
iql.execute("""SELECT \* FROM pandas(table=xyz, pivot=('col1', 'col2', 'values'))"""
```

These operations may also be used in each of the extensions:

- fillna_pre='string': Before pivoting, replaces only in a single column: DataFrame["value"].fillna(val)
- dropna_pre=True | str | list[str]: Before pivoting, If True, DataFrame.dropna(). Else, DataFrame.dropna(subset=[value])
- pivot=(index,columns,values): DataFrame.pivot(index=index, columns=columns, values=values)
- fillna=val: DataFrame.fillna(val)
- dropna=True | str | list[str]: If True, DataFrame.dropna(). Else, DataFrame.dropna(subset=[value])

Note: While still in development, [DuckDB's Pivot and Unpivot](https://github.com/duckdb/duckdb/pull/6387) may change how we handle pivoting.

# Operations available to all IQL SubQueries:

# IQL extension for Bloomberg BQL

See [IQL Extension for Bloomberg BQL Readme](BLOOMBERG_BQL_README.md) for more information.

## Troubleshooting: If you see an initialization failure, verify that BQL is available and working.

```
import bql
bq = bql.Service()
bq.execute("get(name) for('IBM US Equity')")
```

If this fails, you are probably not running in BQuant.

# Database

## Database Lifecycle

### Default: In-Memory Database for each iql.execute()

By default, a series of iql.execute() calls will create and close an in-memory DuckDB connection for each request.

### Option 1: Keep Database Open

Use the iql default connection setting (in-memory only), but leave the connection open:

```
con = iql.IQL.get_dbconnector().get_connection()
try:
  iql.execute("CREATE TABLE abc as SELECT * FROM (values(1),(2),(3))", con=con)
  df=iql.execute("SELECT * FROM abc", con=con)
  display(df)
finally:
  con.close()
```

SQL statements separated by semicolons. The entire set will be run sequentially against a single database, so side effects will be maintained.

### Option 2: Create Database Externally

With this method, you can use a file-based persistent database along with other connectivity options.

Or, create a DuckDB Connection [duckdb.connect()](https://duckdb.org/docs/api/python/overview), such as for a file-based persistent database.

```
df=iql.execute("SELECT * FROM abc", con=con)
```

# FAQ

## How can I simplify my SQL?

There are several approaches to using IQL SubQueries:

### Inline

```
  SELECT fields
  FROM table1
  JOIN table2
    on table1.id=table2.id
  JOIN bql(".....") as k3
    on k3.dates < table2.dates
  WHERE k3.something is true
```

### Common Table Expressions (WITH clause)

CTEs are necessary when the same subquery will be transformed multiple times within a single query. CTEs are also helpful syntactic sugar: the declaration of a subquery is separate from its use, making the SELECT statement simpler.

```
  WITH k3 as (select * from bql(".....") WHERE something is true)
  SELECT fields
  FROM table1
  JOIN table2
    on table1.id=table2.id
  JOIN k3
    on k3.dates < table2.dates
```

### Storing the Data in Tables

When data will be accessed by multiple queries, store the data first via CREATE TABLE / CREATE TEMP TABLE instead of running the same IQL SubQueries multiple times. IQL's caching is helpful, if enabled, but storing the data in tables provides more flexibility.

```
  CREATE [TEMP] TABLE k3 as (SELECT * FROM bql(".....") WHERE something is true);
  SELECT fields
  FROM table2
    on table1.id=table2.id
  JOIN k3
    on k3.dates < table2.dates
```

## Why DuckDB as the default?

We chose [DuckDB](https://duckdb.org/) as the default database module for a few reasons:

- DuckDB is awesome and [fast](https://duckdb.org/2021/05/14/sql-on-pandas.html), with vectorized columnar operations.
- It runs with no setup
- It runs fully in memory and has support for a variety of data sources
- DuckDB's SQL language is standard
- DuckDB has extensive support for the Python ecosystem, including Pandas, PyArrow and Polars

## Why not a DuckDB Extensions?

We didn't implement IQL as an extension for a few reasons:

- Portability: DuckDB is great, but it's not the only game in town. Engines like SnowFlake are important.
- Speed of development: Native Python is easy to develop, easy to debug, and convenient to modify and extend.
- Performance: In our workflows, there was little performance to be gained. Runtime was dominated by external data transfer.

We may still implement DuckDB extension(s) to eliminate the extra preprocess/rewrite step.

## Other Databases Engines

Any database can be supported by implementing a database module. IQL was written in a syntax neutral method. The key step that's dependent on the database engine is registering (or loading) the SubQuery dataframes to the database engine prior to executing the queries.

Modules could be added to support other engines and formats:

- [SQLDF](https://pypi.org/project/sqldf/) and [PandaSQL](https://pypi.org/project/pandasql/): Local-only databases that can connect to in-memory Pandas dataframes
- PyArrow (w/ PySpark/Dask): SubQuery dataframes would be loaded via [pyarrow.Table.from_pandas()](https://arrow.apache.org/docs/python/pandas.html)
- SnowFlake: During registration step, the Pandas dataframes need to be loaded via the [SnowFlake Pandas Connector](https://docs.snowflake.com/en/user-guide/python-connector-pandas)
- Other Pandas-centric engines, such as SQLDF and PandaSQL

## Design Principles

- Extensibility: Extensions and Database Connectors can be easily modified, replaced, or extended.
- KISS: Keep it simple. Don't add complexity.
  - REST APIs, such as FRED: Use the complete URL, rather than building yet-another-Python-API
  - Bloomberg BQL: Use native BQL queries without modification
- Minimal dependencies: Extensions are loaded on-demand. Unused dependencies are not required.

# Footnotes

## Useful DuckDB Features

### CTEs

```
import iql
df = iql.execute("""
  WITH c AS keyword("..."),
      idx AS keyword("...")
    SELECT c.*, idx.*
    FROM c
    JOIN idx
      ON c.idx=idx.id""")
display(df)
```

### Accessing Global DataFrames:

```
import iql
import pandas as pd

fun = pd.DataFrame([{'id': 'Someone', 'fun_level': 'High'}])
iql.execute("""SELECT * FROM fun""")
```

### Copy (query) to 'file'

```
import iql
iql.execute("""COPY (query) TO 'somefile.parquet'""")
```

## Copy to Parquet

- Copy to parquet:
  https://duckdb.org/docs/guides/import/parquet_export.html#:~:text=To%20export%20the%20data%20from,exported%20to%20a%20Parquet%20file.

# Futures and Ideas

## SQL ReWrite

Instead of modifying the SQL in a single step, we could introduce an intermediate statement that has the same logical flow as the code today. This would make it easier to debug, allowing the user to view and debug each step.

```
SELECT * FROM fred() a JOIN fred() b on a.id=b.id
```

could be transformed first into:

```
a=fred();
b=fred();
SELECT * FROM a JOIN b
```

One decision needed here is how to express the first two statements: would we use a CREATE TEMP TABLE or COPY TO to store the SubQuery results, or do we introduce something like CREATE DF.

## Simplifying Parsing

We didn't implement a grammar, because each grammar is very platform dependent. Each database has its own product-specific grammar.

The current IQL implementation first parses the SQL to extract the named functions, using the sqlparse library, then extracts the IQL subquerys by their named keywords. The SubQueries are then parsed via an AST to extract the parameters and values. Any parsing introduces risks and fragility:

- It's possible that sqlparse will fail to parse certain database specific language features. We haven't encountered this yet, but it's something we're thinking about
- It's also possible that our extraction will fail to recognize proper subqueries, due to how sqlparse extracts the tokens. The code here is not as robust as we'd like, and more testing is needed.

There's a few ways to improve this:

- Direct string extraction: identify subquery() blocks and extract them directly as strings, rather than parsing the entire SQL file. This would have to properly account for commenting, quoting, and nesting.
- DuckDB (or whatever platform) extensions: use a lightweight extension to allow the database to externally call the IQL layer, rather than having IQL act as an intermediate step. Or, use a table function, which is not yet supported in SQL, only in relational API.

## Caching

The default in-memory cache will grow unbounded within each kernel session. The expiration is only used to invalid data, but expired results are not evicted from memory if not accessed.

IQL doesn't provide a default implementation, but the QueryCacheBase is intended to be extended to provide file or S3 caching for large, expensive operations along with more sophisticated caching rules.

# Footer

Copyright (C) 2024, IQMO Corporation [info@iqmo.com]
All Rights Reserved
