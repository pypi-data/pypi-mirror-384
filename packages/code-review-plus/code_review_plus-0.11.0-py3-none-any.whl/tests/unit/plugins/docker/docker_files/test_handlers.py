import pytest

from code_review.plugins.docker.docker_files.handlers import (
    extract_using_from,
    get_versions_from_dockerfile,
    parse_dockerfile,
)


def test_dockerfile_handler(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        content = dockerfile.read_text()
        version = get_versions_from_dockerfile(content)
        print(dockerfile, " version:", version)


def test_parse_dockerfile(fixtures_folder):
    compose_folder = fixtures_folder / "compose"
    dockerfiles = list(compose_folder.glob("**/Dockerfile"))
    for dockerfile in dockerfiles:
        dockerfile_schema = parse_dockerfile(dockerfile)
        print(dockerfile, " schema:", dockerfile_schema)


def test_parse_dockerfile_using_from(fixtures_folder):
    compose_folder = fixtures_folder / "compose_from"

    dockerfiles = list(compose_folder.glob("**/Dockerfile"))

    for dockerfile in dockerfiles:
        dockerfile_schema = parse_dockerfile(dockerfile)
        print(dockerfile, " schema:", dockerfile_schema)


class TestGetVersionsFromDockerfile:
    @pytest.mark.parametrize(
        "dockerfile_content,expected",
        [
            (
                "FROM python:3.10.5-slim",
                {"version": "3.10.5-slim", "product": "python"},
            ),
            (
                "ARG PYTHON_VERSION=3.9.7\nFROM python:${PYTHON_VERSION}",
                {"version": "3.9.7", "product": "python"},
            ),
            (
                "FROM postgres:14.2",
                {"version": "14.2", "product": "postgres"},
            ),
            (
                "FROM node:18.0.0",
                {"version": "18.0.0", "product": "node"},
            ),
            (
                "FROM ubuntu:20.04",
                {"version": None, "product": None},
            ),
        ],
    )
    def test_get_versions(self, dockerfile_content, expected):
        result = get_versions_from_dockerfile(dockerfile_content)
        assert result == expected


class TestExtractUsingFrom:
    @pytest.mark.parametrize(
        "dockerfile_content,expected",
        [
            ("FROM python:3.10.5-slim", None),
            (
                "FROM docker.io/postgres:17",
                {"source": "docker.io", "product": "postgres", "version": "17"},
            ),
            (
                "FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS python",
                {"source": "ghcr.io/astral-sh", "product": "uv", "version": "python3.13-bookworm-slim"},
            ),
            (
                "FROM docker.io/traefik:2.11.2",
                {"source": "docker.io", "product": "traefik", "version": "2.11.2"},
            ),
            (
                "FROM docker.io/nginx:1.17.8-alpine",
                {"source": "docker.io", "product": "nginx", "version": "1.17.8-alpine"},
            ),
            ("FROM node:18.0.0", None),
        ],
    )
    def test_extract_using_from(self, dockerfile_content, expected):
        result = extract_using_from(dockerfile_content, product=None)
        assert result == expected
