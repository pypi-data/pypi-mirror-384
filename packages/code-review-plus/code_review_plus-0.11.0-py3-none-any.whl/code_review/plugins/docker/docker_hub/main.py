import json
from pathlib import Path

import requests

from code_review.plugins.docker.docker_hub.filters.exclusions import exclude_by_content
from code_review.plugins.docker.docker_hub.filters.inclusions import include_by_regex
from code_review.plugins.docker.docker_hub.schemas import ImageTag


def get_image_versions(image_name: str, cache_folder: Path, ignore_cache: bool = False) -> list[ImageTag]:
    """Fetches and prints all available tags for the official Python image on Docker Hub."""
    base_url = f"https://hub.docker.com/v2/repositories/library/{image_name}/tags"
    all_versions = []
    page = 1
    page_size = 200  # You can increase this to reduce the number of requests
    cache_file = cache_folder / f"{image_name}_tags.json"
    if cache_file.exists() and not ignore_cache:
        print(f"Loading cached tags from {cache_file}")
        with open(cache_file) as f:
            cached_data = json.load(f)
            all_versions = [ImageTag(**item) for item in cached_data]
            print(f"Loaded {len(all_versions)} tags from {cache_file}")
        return all_versions

    while True:
        params = {"page": page, "page_size": page_size}
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            # Extract tag names from the results and add to our list
            for result in data["results"]:
                image_info_schema = ImageTag(**result)
                image_info_schema.set_version()
                if image_info_schema.tag_status == "active":
                    all_versions.append(image_info_schema)

            # Check for the next page
            if data["next"]:
                page += 1
            else:
                break  # No more pages to retrieve
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            break
    with open(cache_file, "w") as f:
        data = [tag.model_dump() for tag in all_versions]
        json.dump(data, f)

    return all_versions


if __name__ == "__main__":
    name = "python"
    # name = "postgres"
    # name = "node"
    print(f"Fetching all {name.capitalize()} image versions from Docker Hub...")
    cache_folder = Path(__file__).parent.parent.parent / "output" / ".cache" / "docker_hub"
    cache_folder.mkdir(parents=True, exist_ok=True)
    versions = get_image_versions(image_name=name, cache_folder=cache_folder, ignore_cache=True)
    filtered_tags = [
        v for v in versions if not exclude_by_content(v, ["alpine", "beta", "-rc1", "-rc", "windowsservercore"])
    ]

    regex = r"(\d+\.\d+\.?\d*?)-(.+)"
    filtered_tags = [v for v in filtered_tags if include_by_regex(v, regex)]

    if filtered_tags:
        for i, version in enumerate(filtered_tags, 1):
            print(f"{i}. {version.name} ({version.version})- Last Updated: {version.last_updated}")
            # print(f"{version.name}")
    else:
        print("Could not retrieve any versions.")
    print(f"Found {len(filtered_tags)} tags for the official {name.capitalize()} image:")
