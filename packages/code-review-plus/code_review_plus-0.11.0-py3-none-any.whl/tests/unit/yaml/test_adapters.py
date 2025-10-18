from code_review.yaml.adapters import parse_yaml_file


def test_parse_yaml_file(fixtures_folder):
    yaml_file = fixtures_folder / "gitlab-ci.yml"

    result = parse_yaml_file(yaml_file)

    assert result is not None, "The function should return a dictionary for a valid YAML file."

    assert len(result.keys()) == 8
    for key, value in result.items():
        if isinstance(value, dict) and "only" in value:
            assert isinstance(value["only"], list)
            if "production" in key:
                assert len(value["only"]) == 1
            else:
                assert len(value["only"]) == 2
