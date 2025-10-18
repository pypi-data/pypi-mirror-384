from code_review.plugins.gitlab.ci.handlers import handle_multi_targets


def test_handle_mult_targets(fixtures_folder) -> None:
    result = handle_multi_targets(fixtures_folder, "gitlab-ci.yml")

    assert result is not None, "The function should return a dictionary for a valid .gitlab-ci.yml file."
    assert isinstance(result, dict), "The function should return a dictionary."

    # Check for expected top-level keys
    assert "build_staging" in result, "The result should contain 'build_staging' job."
    assert "deploy_staging" in result, "The result should contain 'deploy_staging' job."
    assert "build_production" in result, "The result should contain 'build_production' job."
    assert "deploy_production" in result, "The result should contain 'deploy_production' job."

    # Check length of lists
    assert len(result["build_staging"]) == 2, "'build_staging' should have one 'only' condition."
    assert len(result["deploy_staging"]) == 2, "'deploy_staging' should have one 'only' condition."
    assert len(result["build_production"]) == 1, "'build_production' should have one 'only' condition."
    assert len(result["deploy_production"]) == 1, "'deploy_production' should have one 'only' condition."
