import json
from ast import parse

from ast2json import ast2json


def test_ast_parsing(fixtures_folder):
    file = fixtures_folder / "condo_models.py"
    with open(file) as f:
        content = f.read()
    tree = parse(content)
    ast_json = ast2json(tree)
    assert isinstance(ast_json, dict)

    json_file = fixtures_folder / "condo_models_ast.json"
    with open(json_file, "w") as f:
        json.dump(ast_json, f, indent=4, default=str)
