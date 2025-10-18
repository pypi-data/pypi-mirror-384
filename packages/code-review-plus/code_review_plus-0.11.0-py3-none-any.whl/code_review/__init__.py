# In code_review/__main__.py or similar
import code_review.plugins.linting.ruff.main  # This imports the ruff commands
import code_review.plugins.git.main  # This imports the git commands
import code_review.review.main  # This imports the review commands
from code_review.cli import cli

__version__ = "0.11.0"
if __name__ == "__main__":
    cli()
