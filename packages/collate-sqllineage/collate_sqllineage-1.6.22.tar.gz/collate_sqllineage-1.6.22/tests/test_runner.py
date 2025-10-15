from collate_sqllineage.runner import LineageRunner
from collate_sqllineage.utils.constant import LineageLevel


def test_runner_dummy():
    runner = LineageRunner(
        """insert into tab2 select col1, col2, col3, col4, col5, col6 from tab1;
insert into tab3 select * from tab2""",
        verbose=True,
    )
    assert str(runner)
    assert runner.to_cytoscape() is not None
    assert runner.to_cytoscape(level=LineageLevel.COLUMN) is not None
