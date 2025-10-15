from collate_sqllineage.core.models import DataFunction
from .helpers import assert_table_lineage_equal


def test_select():
    assert_table_lineage_equal("SELECT col1 FROM tab1", {"tab1"})


def test_select_with_schema():
    assert_table_lineage_equal("SELECT col1 FROM schema1.tab1", {"schema1.tab1"})


def test_select_with_schema_and_database():
    assert_table_lineage_equal(
        "SELECT col1 FROM db1.schema1.tbl1", {"db1.schema1.tbl1"}
    )


def test_select_multi_line():
    assert_table_lineage_equal(
        """SELECT col1 FROM
tab1""",
        {"tab1"},
    )


def test_select_asterisk():
    assert_table_lineage_equal("SELECT * FROM tab1", {"tab1"})


def test_select_value():
    assert_table_lineage_equal("SELECT 1")


def test_select_function():
    assert_table_lineage_equal("SELECT NOW()")


def test_select_trim_function_with_from_keyword():
    assert_table_lineage_equal("SELECT trim(BOTH '  ' FROM '  abc  ')")


def test_select_trim_function_with_from_keyword_from_source_table():
    assert_table_lineage_equal("SELECT trim(BOTH '  ' FROM col1) FROM tab1", {"tab1"})


def test_select_with_where():
    assert_table_lineage_equal(
        "SELECT * FROM tab1 WHERE col1 > val1 AND col2 = 'val2'", {"tab1"}
    )


def test_select_with_comment():
    assert_table_lineage_equal("SELECT -- comment1\n col1 FROM tab1", {"tab1"})


def test_select_with_comment_after_from():
    assert_table_lineage_equal("SELECT col1\nFROM  -- comment\ntab1", {"tab1"})


def test_select_with_comment_after_join():
    assert_table_lineage_equal(
        "SELECT * FROM tab1 JOIN --comment\ntab2 ON tab1.x = tab2.x", {"tab1", "tab2"}
    )


def test_select_keyword_as_column_alias():
    # here "as" is the column alias
    assert_table_lineage_equal('SELECT 1 "as" FROM tab1', {"tab1"})
    # the following is hive specific, MySQL doesn't allow this syntax. As of now, we don't test against it
    # assert_table_lineage_equal("SELECT 1 as FROM tab1", {"tab1"})


def test_select_with_table_alias():
    assert_table_lineage_equal("SELECT 1 FROM tab1 AS alias1", {"tab1"})


def test_select_count():
    assert_table_lineage_equal("SELECT count(*) FROM tab1", {"tab1"})


def test_select_subquery():
    assert_table_lineage_equal("SELECT col1 FROM (SELECT col1 FROM tab1) dt", {"tab1"})
    # with an extra space
    assert_table_lineage_equal("SELECT col1 FROM ( SELECT col1 FROM tab1) dt", {"tab1"})


def test_select_subquery_with_two_parenthesis():
    assert_table_lineage_equal(
        "SELECT col1 FROM ((SELECT col1 FROM tab1)) dt", {"tab1"}
    )


def test_select_subquery_with_more_parenthesis():
    assert_table_lineage_equal(
        "SELECT col1 FROM (((((((SELECT col1 FROM tab1))))))) dt", {"tab1"}
    )


def test_select_subquery_in_case():
    assert_table_lineage_equal(
        """SELECT
CASE WHEN (SELECT count(*) FROM tab1 WHERE col1 = 'tab2') = 1 THEN (SELECT count(*) FROM tab2) ELSE 0 END AS cnt""",
        {"tab1", "tab2"},
    )
    assert_table_lineage_equal(
        """SELECT
CASE WHEN 1 = (SELECT count(*) FROM tab1 WHERE col1 = 'tab2') THEN (SELECT count(*) FROM tab2) ELSE 0 END AS cnt""",
        {"tab1", "tab2"},
    )


def test_select_subquery_without_alias():
    """this syntax is valid in SparkSQL, not for MySQL"""
    assert_table_lineage_equal("SELECT col1 FROM (SELECT col1 FROM tab1)", {"tab1"})


def test_select_subquery_in_where_clause():
    assert_table_lineage_equal(
        """SELECT col1
FROM tab1
WHERE col1 IN (SELECT max(col1) FROM tab2)""",
        {"tab1", "tab2"},
    )


def test_select_inner_join():
    assert_table_lineage_equal("SELECT * FROM tab1 INNER JOIN tab2", {"tab1", "tab2"})


def test_select_join():
    assert_table_lineage_equal("SELECT * FROM tab1 JOIN tab2", {"tab1", "tab2"})


def test_select_left_join():
    assert_table_lineage_equal("SELECT * FROM tab1 LEFT JOIN tab2", {"tab1", "tab2"})


def test_select_left_join_with_extra_space_in_middle():
    assert_table_lineage_equal("SELECT * FROM tab1 LEFT  JOIN tab2", {"tab1", "tab2"})


def test_select_right_join():
    assert_table_lineage_equal("SELECT * FROM tab1 RIGHT JOIN tab2", {"tab1", "tab2"})


def test_select_full_outer_join():
    assert_table_lineage_equal(
        "SELECT * FROM tab1 FULL OUTER JOIN tab2", {"tab1", "tab2"}
    )


def test_select_cross_join():
    assert_table_lineage_equal("SELECT * FROM tab1 CROSS JOIN tab2", {"tab1", "tab2"})


def test_select_cross_join_with_on():
    assert_table_lineage_equal(
        "SELECT * FROM tab1 CROSS JOIN tab2 ON tab1.col1 = tab2.col2", {"tab1", "tab2"}
    )


def test_select_join_with_subquery():
    assert_table_lineage_equal(
        "SELECT col1 FROM tab1 AS a LEFT JOIN tab2 AS b ON a.id=b.tab1_id "
        "WHERE col1 = (SELECT col1 FROM tab2 WHERE id = 1)",
        {"tab1", "tab2"},
    )


def test_select_join_in_ansi89_syntax():
    assert_table_lineage_equal("SELECT * FROM tab1 a, tab2 b", {"tab1", "tab2"})


def test_select_join_in_ansi89_syntax_with_subquery():
    assert_table_lineage_equal(
        "SELECT * FROM (SELECT * FROM tab1) a, (SELECT * FROM tab2) b", {"tab1", "tab2"}
    )


def test_select_group_by():
    assert_table_lineage_equal(
        "SELECT col1, col2 FROM tab1 GROUP BY col1, col2", {"tab1"}
    )


def test_select_group_by_ordinal():
    assert_table_lineage_equal("SELECT col1, col2 FROM tab1 GROUP BY 1, 2", {"tab1"})


def test_select_from_values():
    assert_table_lineage_equal("SELECT * FROM (VALUES (1, 2))")


def test_select_from_values_newline():
    assert_table_lineage_equal("SELECT * FROM (\nVALUES (1, 2))")


def test_select_from_values_with_alias():
    assert_table_lineage_equal(
        "SELECT * FROM (VALUES (1, 2)) AS t(col1, col2)", test_sqlparse=False
    )


def test_select_from_unnest():
    # unnest function is Presto specific
    assert_table_lineage_equal(
        "SELECT student, score FROM tests CROSS JOIN UNNEST(scores) AS t (score)",
        {"tests", DataFunction("UNNEST")},
        test_sqlparse=False,
    )


def test_select_from_unnest_parsed_as_keyword():
    # an extra space after UNNEST changes the AST structure
    assert_table_lineage_equal(
        "SELECT student, score FROM tests CROSS JOIN UNNEST (scores) AS t (score)",
        {"tests", DataFunction("UNNEST")},
        test_sqlparse=False,
    )


def test_select_from_unnest_with_ordinality():
    """
    https://prestodb.io/docs/current/sql/select.html#unnest
    FIXME: sqlfluff athena dialect doesn't support parsing this yet
    """
    sql = """
    SELECT numbers, n, a
    FROM (
      VALUES
        (ARRAY[2, 5]),
        (ARRAY[7, 8, 9])
    ) AS x (numbers)
    CROSS JOIN UNNEST(numbers) WITH ORDINALITY AS t (n, a);
    """
    assert_table_lineage_equal(sql, test_sqlfluff=False, test_sqlparse=False)


def test_select_union_all():
    sql = """SELECT col1
FROM tab1
UNION ALL
SELECT col1
FROM tab2
UNION ALL
SELECT col1
FROM tab3
ORDER BY col1"""
    assert_table_lineage_equal(
        sql,
        {"tab1", "tab2", "tab3"},
    )


def test_select_subquery_row_to_json():
    sql = """
    SELECT
    row_to_json(t) AS result
    FROM
    (
        SELECT
            t2.id AS t2_id,
            t2.name AS t2_name,
            t1.name AS t1_name
        FROM
            tab2 t2
        JOIN
            tab1 t1 ON t2.t2_id = t1.t1_id
    ) t;
    """
    assert_table_lineage_equal(
        sql,
        {"tab1", "tab2"},
    )


def test_token_matching_empty_in_clause():
    """Test case to reproduce the AttributeError: 'Token' object has no attribute '_token_matching'.

    Error is specific to SQLParse."""
    sql = """
        SELECT * FROM some_table
        WHERE some_column IN (
            'SOME_STRING\\\\',
            'SOME_STRING)',
            'SOME_STRING;',
            'to'
        )
    """
    assert_table_lineage_equal(
        sql,
        {"some_table"},
        test_sqlparse=True,
        test_sqlfluff=False,
    )


def test_select_join_with_union_subquery():
    """Test that UNION subqueries in JOIN clauses extract all source tables."""
    assert_table_lineage_equal(
        """
        SELECT t1.col1, t2.col2
        FROM tab1 t1
            INNER JOIN (SELECT * FROM tab2 UNION SELECT * FROM tab3) t2
                ON t1.id = t2.id;
        """,
        {"tab1", "tab2", "tab3"},
    )


def test_select_join_with_complex_union_subquery():
    """Test multiple JOINs with UNION subqueries containing multiple tables."""
    assert_table_lineage_equal(
        """SELECT t1.col1, t2.col2, t3.col3
        FROM tab1 t1
            INNER JOIN (SELECT * FROM tab2 UNION SELECT * FROM tab3 UNION SELECT * FROM tab4) t2
                ON t1.id = t2.id
            LEFT JOIN (SELECT * FROM tab5 UNION SELECT * FROM tab6) t3
                ON t1.other_id = t3.id;
        """,
        {"tab1", "tab2", "tab3", "tab4", "tab5", "tab6"},
    )
