import ast
from pathlib import Path

from boa_restrictor.projections.occurrence import Occurrence
from boa_restrictor.rules.python.return_type_hints import ReturnStatementRequiresTypeHintRule


def test_function_has_return_and_type_hint():
    source_tree = ast.parse("""def my_function(self) -> bool:
            return True
        """)

    occurrences = ReturnStatementRequiresTypeHintRule.run_check(
        file_path=Path("/path/to/file/my_file.py"), source_tree=source_tree
    )

    assert len(occurrences) == 0


def test_function_has_return_missing_type_hint():
    source_tree = ast.parse("""def my_function(self):
            return True
        """)

    occurrences = ReturnStatementRequiresTypeHintRule.run_check(
        file_path=Path("/path/to/file/my_file.py"), source_tree=source_tree
    )

    assert len(occurrences) == 1
    assert occurrences[0] == Occurrence(
        filename="my_file.py",
        file_path=Path("/path/to/file/my_file.py"),
        line_number=1,
        rule_id=ReturnStatementRequiresTypeHintRule.RULE_ID,
        rule_label=ReturnStatementRequiresTypeHintRule.RULE_LABEL,
        identifier="my_function",
    )


def test_function_missing_return_has_type_hint():
    source_tree = ast.parse("""def my_function(self) -> bool:
            pass
        """)

    occurrences = ReturnStatementRequiresTypeHintRule.run_check(
        file_path=Path("/path/to/file/my_file.py"), source_tree=source_tree
    )

    assert len(occurrences) == 0
