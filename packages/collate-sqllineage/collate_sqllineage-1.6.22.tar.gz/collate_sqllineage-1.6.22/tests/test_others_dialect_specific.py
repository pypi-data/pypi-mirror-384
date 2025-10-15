import pytest

from .helpers import (
    TestColumnQualifierTuple,
    assert_column_lineage_equal,
    assert_table_lineage_equal,
)

"""
This test class will contain all the tests for testing 'Other Queries' where the dialect is not ANSI.
"""


@pytest.mark.parametrize("dialect", ["bigquery", "snowflake"])
def test_create_bucket_table(dialect: str):
    assert_table_lineage_equal(
        "CREATE TABLE tab1 USING parquet CLUSTERED BY (col1) INTO 500 BUCKETS",
        None,
        {"tab1"},
        dialect,
    )


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_create_select_without_as(dialect: str):
    assert_table_lineage_equal(
        "CREATE TABLE tab1 SELECT * FROM tab2", {"tab2"}, {"tab1"}, dialect
    )


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_create_with_identifier(dialect: str):
    assert_table_lineage_equal(
        "CREATE TABLE IDENTIFIER('TABLE_FROM_SQL_SP') AS SELECT * FROM NEW_TABLE",
        {"NEW_TABLE"},
        {"TABLE_FROM_SQL_SP"},
        dialect,
        test_sqlparse=False,
    )


def test_create_using_serde():
    """
    https://cwiki.apache.org/confluence/display/Hive/LanguageManual+DDL#LanguageManualDDL-RowFormats&SerDe
    here with is not an indicator for CTE
    FIXME: sqlfluff hive dialect doesn't support parsing this yet
    """
    # Check
    #
    assert_table_lineage_equal(
        """CREATE TABLE apachelog (
  host STRING,
  identity STRING,
  user STRING,
  time STRING,
  request STRING,
  status STRING,
  size STRING,
  referer STRING,
  agent STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  "input.regex" = "([^]*) ([^]*) ([^]*) (-|\\[^\\]*\\]) ([^ \"]*|\"[^\"]*\") (-|[0-9]*) (-|[0-9]*)(?: ([^ \"]*|\".*\") ([^ \"]*|\".*\"))?"
)
STORED AS TEXTFILE""",  # noqa
        None,
        {"apachelog"},
        test_sqlfluff=False,
    )


@pytest.mark.parametrize("dialect", ["mysql"])
def test_update_with_join(dialect: str):
    assert_table_lineage_equal(
        "UPDATE tab1 a INNER JOIN tab2 b ON a.col1=b.col1 SET a.col2=b.col2",
        {"tab2"},
        {"tab1"},
        dialect=dialect,
    )


@pytest.mark.parametrize("dialect", ["exasol", "mysql", "teradata"])
def test_rename_table(dialect: str):
    """
    https://docs.exasol.com/db/latest/sql/rename.htm
    https://dev.mysql.com/doc/refman/8.0/en/rename-table.html
    https://docs.teradata.com/r/Teradata-Database-SQL-Data-Definition-Language-Syntax-and-Examples/December-2015/Table-Statements/RENAME-TABLE
    """
    assert_table_lineage_equal("rename table tab1 to tab2", None, None, dialect)


@pytest.mark.parametrize("dialect", ["exasol", "mysql", "teradata"])
def test_rename_tables(dialect: str):
    assert_table_lineage_equal(
        "rename table tab1 to tab2, tab3 to tab4", None, None, dialect
    )


@pytest.mark.parametrize("dialect", ["hive"])
def test_alter_table_exchange_partition(dialect: str):
    """
    See https://cwiki.apache.org/confluence/display/Hive/Exchange+Partition for language manual
    """
    assert_table_lineage_equal(
        "alter table tab1 exchange partition(pt='part1') with table tab2",
        {"tab2"},
        {"tab1"},
        dialect=dialect,
    )


@pytest.mark.parametrize("dialect", ["snowflake", "bigquery"])
def test_create_clone(dialect: str):
    """
    Language manual:
        https://cloud.google.com/bigquery/docs/table-clones-create
        https://docs.snowflake.com/en/sql-reference/sql/create-clone
    Note clone is not a keyword in sqlparse, we'll skip testing for it.
    """
    assert_table_lineage_equal(
        "create table tab2 CLONE tab1;",
        {"tab1"},
        {"tab2"},
        dialect=dialect,
        test_sqlparse=False,
    )


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_alter_table_swap_partition(dialect: str):
    """
    See https://docs.snowflake.com/en/sql-reference/sql/alter-table for language manual
    Note swap is not a keyword in sqlparse, we'll skip testing for it.
    """
    assert_table_lineage_equal(
        "alter table tab1 swap with tab2",
        {"tab2"},
        {"tab1"},
        dialect=dialect,
        test_sqlparse=False,
    )


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_refresh_table(dialect: str):
    assert_table_lineage_equal("refresh table tab1", None, None, dialect)


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_cache_table(dialect: str):
    assert_table_lineage_equal(
        "cache table tab1 select * from tab2", None, None, dialect
    )


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_uncache_table(dialect: str):
    assert_table_lineage_equal("uncache table tab1", None, None, dialect)


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_uncache_table_if_exists(dialect: str):
    assert_table_lineage_equal("uncache table if exists tab1", None, None, dialect)


@pytest.mark.parametrize("dialect", ["hive"])
def test_lateral_view_using_json_tuple(dialect: str):
    # disabling this method for dialect "databricks", "sparksql"
    # as sqlfluff produces incorrect tree for those cases
    sql = """INSERT OVERWRITE TABLE foo
SELECT sc.id, q.item0, q.item1
FROM bar sc
LATERAL VIEW json_tuple(sc.json, 'key1', 'key2') q AS item0, item1"""
    assert_table_lineage_equal(sql, {"bar"}, {"foo"}, dialect)


@pytest.mark.parametrize("dialect", ["databricks", "hive", "sparksql"])
def test_lateral_view_outer(dialect: str):
    sql = """INSERT OVERWRITE TABLE foo
SELECT sc.id, q.col1
FROM bar sc
LATERAL VIEW OUTER explode(sc.json_array) q AS col1"""
    assert_table_lineage_equal(sql, {"bar"}, {"foo"}, dialect)


@pytest.mark.parametrize("dialect", ["databricks", "sparksql"])
def test_show_create_table(dialect: str):
    assert_table_lineage_equal("show create table tab1", None, None, dialect)


@pytest.mark.parametrize("dialect", ["tsql"])
def test_if_then_statement(dialect: str):
    sql = """IF OBJECT_ID(N'REPORTING.[dbo].[AggregateHTSEntrypoint]', N'U') IS NOT NULL
    DROP TABLE REPORTING.[dbo].[AggregateHTSEntrypoint];
SELECT DISTINCT
    MFLCode
INTO REPORTING.[dbo].[AggregateHTSEntrypoint]
FROM NDWH.dbo.FactHTSClientTests hts"""
    assert_table_lineage_equal(
        sql,
        {"ndwh.dbo.facthtsclienttests"},
        {"reporting.dbo.aggregatehtsentrypoint"},
        dialect=dialect,
    )


@pytest.mark.parametrize("dialect", ["tsql"])
def test_tsql_create_view(dialect: str):
    sql = """CREATE VIEW [dbo].[client_product]
AS
SELECT [client].[client_name], [product].[product_name]
FROM [dbo].[client]
LEFT JOIN [dbo].[product] ON [client].[id] = [product].[client_id]"""
    assert_table_lineage_equal(
        sql,
        {"dbo.client", "dbo.product"},
        {"dbo.client_product"},
        dialect=dialect,
    )


@pytest.mark.parametrize("dialect", ["tsql"])
def test_tsql_create_view_with_nolock(dialect: str):
    sql = """CREATE VIEW [dbo].[test_view_lineage] AS
SELECT
    [s].[account_code] AS 'Account Code',
    [c].[iso_code] AS 'ISO Code'
FROM
    [dbo].[source_table] (NOLOCK) [s]
LEFT JOIN
    [dbo].[lookup_currency] (NOLOCK) [c]
    ON [s].[currency_id] = [c].[currency_id]
WHERE
    [s].[currency_id] IS NOT NULL;"""
    assert_table_lineage_equal(
        sql,
        {"dbo.source_table", "dbo.lookup_currency"},
        {"dbo.test_view_lineage"},
        dialect=dialect,
        test_sqlparse=False,
    )


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_snowflake_materialize_view(dialect: str):
    sql = """CREATE OR REPLACE MATERIALIZED VIEW IF NOT EXISTS view_with_rls
(
    COL1,
    COL2
) WITH ROW ACCESS POLICY my_db.my_schema.my_policy ON (COL1) AS (
  SELECT
    COL1,
    COL2
  FROM my_table
);
"""
    assert_table_lineage_equal(
        sql, {"my_table"}, {"view_with_rls"}, dialect=dialect, test_sqlparse=False
    )

    sql = """CREATE OR REPLACE VIEW IF NOT EXISTS view_with_rls
(
    COL1 WITH MASKING POLICY my_db.my_schema.my_policy,
    COL2
) WITH ROW ACCESS POLICY my_db.my_schema.my_policy ON (COL1) AS (
  SELECT
    C1,
    C2
  FROM my_table
);
"""
    assert_table_lineage_equal(
        sql, {"my_table"}, {"view_with_rls"}, dialect=dialect, test_sqlparse=False
    )

    assert_column_lineage_equal(
        sql,
        [
            (
                TestColumnQualifierTuple("c1", "my_table"),
                TestColumnQualifierTuple("col1", "view_with_rls"),
            ),
            (
                TestColumnQualifierTuple("c2", "my_table"),
                TestColumnQualifierTuple("col2", "view_with_rls"),
            ),
        ],
        dialect=dialect,
        test_sqlparse=False,
    )


@pytest.mark.parametrize("dialect", ["redshift"])
def test_redshift_materialize_view(dialect: str):
    sql = """create materialized view test_schema.sales_current2 as (
    WITH current_or_previous AS (
        SELECT
            MAX(data_release_version) AS data_release_version
        FROM metadata_schema.datamart_run
        WHERE dag_id = 'test_id'
    ) select eventid, listid, salesrow from test_schema.sales);
"""
    assert_table_lineage_equal(
        sql,
        {"test_schema.sales", "metadata_schema.datamart_run"},
        {"test_schema.sales_current2"},
        dialect=dialect,
        test_sqlparse=False,
    )


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_snowflake_dynamic_table_name(dialect: str):
    sql = """
    create or replace dynamic table TEST_DB.PUBLIC.XYA(
    ID,
    NAME
    ) target_lag = '20 minutes' refresh_mode = AUTO initialize = ON_CREATE warehouse = COMPUTE_WH
    as select * from t1;
    """
    assert_table_lineage_equal(sql, {"t1"}, {"TEST_DB.PUBLIC.XYA"}, dialect)


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_snowflake_dynamic_table_2(dialect: str):
    sql = """
    CREATE DYNAMIC ICEBERG TABLE product (date TIMESTAMP_NTZ, id NUMBER, content STRING)
    TARGET_LAG = '20 minutes'
    WAREHOUSE = mywh
    EXTERNAL_VOLUME = 'my_external_volume'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'my_iceberg_table'
    AS
        SELECT product_id, product_name FROM staging_table;
    """
    assert_table_lineage_equal(sql, {"staging_table"}, {"product"}, dialect)


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_snowflake_create_stream(dialect: str):
    sql = """
    CREATE STREAM mystream ON TABLE mytable;
    """
    assert_table_lineage_equal(
        sql, {"mytable"}, {"mystream"}, dialect, test_sqlparse=False
    )


@pytest.mark.parametrize("dialect", ["snowflake"])
def test_snowflake_create_stream_complex(dialect: str):
    sql = """
    CREATE STREAM mystream ON TABLE mytable AT (TIMESTAMP =>
    TO_TIMESTAMP_TZ('02/02/2019 01:02:03', 'mm/dd/yyyy hh24:mi:ss'));
    """
    assert_table_lineage_equal(
        sql, {"mytable"}, {"mystream"}, dialect, test_sqlparse=False
    )

    sql = """
    CREATE STREAM mystream ON TABLE mytable
    BEFORE(STATEMENT => '8e5d0ca9-005e-44e6-b858-a8f5b37c5726');
    """
    assert_table_lineage_equal(
        sql, {"mytable"}, {"mystream"}, dialect, test_sqlparse=False
    )

    sql = """
    CREATE STREAM mystream ON VIEW myview;
    """
    assert_table_lineage_equal(
        sql, {"myview"}, {"mystream"}, dialect, test_sqlparse=False
    )


@pytest.mark.parametrize("dialect", ["oracle"])
def test_update_set_clause_with_select_statement(dialect: str):
    sql = """
    UPDATE "RAW".TABLKE_A MAS
    SET MAS.ACCURE_INT_LAST_MONTH = (SELECT NVL(SUM(TRANS_AMOUNT), 0) FROM "RAW".TABLE_B D
    WHERE D.POSTED_DT = '2023-07-11')
    """
    assert_table_lineage_equal(
        sql, {"RAW.TABLE_B"}, {"RAW.TABLKE_A"}, dialect, test_sqlparse=False
    )


@pytest.mark.parametrize("dialect", ["trino"])
def test_trino_create_view(dialect: str):
    """
    Test Trino CREATE VIEW statement syntax
    Reference: https://trino.io/docs/current/sql/create-view.html
    """
    sql = """CREATE VIEW test AS
SELECT orderkey, orderstatus, totalprice / 2 AS half
FROM orders"""
    assert_table_lineage_equal(
        sql,
        {"orders"},
        {"test"},
        dialect=dialect,
    )

    sql = """CREATE OR REPLACE VIEW orders_by_date
COMMENT 'A view to keep track of orders.'
AS
SELECT orderdate, sum(totalprice) AS price
FROM orders
GROUP BY orderdate"""
    assert_table_lineage_equal(
        sql,
        {"orders"},
        {"orders_by_date"},
        dialect=dialect,
    )

    sql = """CREATE VIEW test
SECURITY INVOKER
AS
SELECT orderkey, orderstatus
FROM orders"""
    assert_table_lineage_equal(
        sql,
        {"orders"},
        {"test"},
        dialect=dialect,
    )
