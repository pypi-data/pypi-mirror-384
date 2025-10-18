import pytest
from unittest.mock import MagicMock, patch, call
from code_review.plugins.git.handlers import display_branches
from code_review.schemas import BranchSchema
from datetime import datetime
from code_review.plugins.git.handlers import compare_branches


class TestCompareBranches:
    def test_compare_handler(self):
        result = compare_branches("master", "feature/bulk_git_sync")
        assert result is not None



class TestDisplayBranches:
    @pytest.mark.parametrize(
        "branches,page_size,expected_calls",
        [
            (
                [
                    BranchSchema(
                        name="feature/login",
                        author="John Doe",
                        email="john@example.com",
                        date=datetime(2024, 1, 15),
                        hash="abc123"
                    ),
                    BranchSchema(
                        name="fix/bug-123",
                        author="Jane Smith",
                        email="jane@example.com",
                        date=datetime(2024, 1, 20),
                        hash="def456"
                    ),
                ],
                None,
                2,
            ),
            (
                [
                    BranchSchema(
                        name="feature/login",
                        author="John Doe",
                        email="john@example.com",
                        date=datetime(2024, 1, 15),
                        hash="abc123"
                    ),
                    BranchSchema(
                        name="fix/bug-123",
                        author="Jane Smith",
                        email="jane@example.com",
                        date=datetime(2024, 1, 20),
                        hash="def456"
                    ),
                ],
                1,
                1,
            ),
            (
                [],
                None,
                0,
            ),
        ],
    )
    @patch("code_review.plugins.git.handlers.CLI_CONSOLE")
    def test_display_branches(self, mock_console, branches, page_size, expected_calls):
        display_branches(branches, page_size)

        assert mock_console.print.call_count == expected_calls

        if expected_calls > 0:
            for i, branch in enumerate(branches[:page_size] if page_size else branches, 1):
                expected_output = f" {i} [yellow]{branch.name}[/yellow] {branch.date}(by [blue]{branch.author}[/blue])"
                mock_console.print.assert_any_call(expected_output)