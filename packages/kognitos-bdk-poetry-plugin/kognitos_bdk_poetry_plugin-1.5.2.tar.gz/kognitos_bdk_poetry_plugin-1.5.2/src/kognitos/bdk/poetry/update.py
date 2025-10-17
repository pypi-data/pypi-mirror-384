import os

import boto3
import semver
from poetry.console.commands.command import Command
from poetry.utils.env import EnvManager
from rich.console import Console

console = Console()


def normalize_version(tag):
    parts = tag.split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts)


def sort_semver(image_tags):
    versioned_tags = []
    non_versioned_tags = []

    for tag in image_tags:
        try:
            normalized_tag = normalize_version(tag)
            versioned_tags.append((semver.VersionInfo.parse(normalized_tag), tag))
        except ValueError:
            non_versioned_tags.append(tag)

    sorted_versioned_tags = sorted(versioned_tags, key=lambda x: x[0], reverse=True)
    sorted_versioned_tags = [tag[1] for tag in sorted_versioned_tags]

    return sorted_versioned_tags + non_versioned_tags


def get_latest_bdk_runtime_version(image_repository, region_name):
    ecr_client = boto3.client("ecr", region_name=region_name)
    images_response = ecr_client.list_images(repositoryName=image_repository)
    if "imageIds" not in images_response or len(images_response["imageIds"]) == 0:
        return None
    images = images_response["imageIds"]
    iterations = 0
    while "nextToken" in images_response:
        next_token = images_response["nextToken"]
        images_response = ecr_client.list_images(repositoryName=image_repository, nextToken=next_token)
        images.extend(images_response["imageIds"])
        iterations += 1
        if iterations > 100:  # prevent infinite loop just in case
            break
    image_tags = [image["imageTag"] for image in images if "imageTag" in image]
    sorted_tags = sort_semver(image_tags)
    latest_tag = sorted_tags[0]
    return latest_tag


class UpdateCommand(Command):
    name = "bdk update"
    description = "Update BDK runtime from the current active virtual environment"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._container = None

    def handle(self) -> int:
        console.log("[bold blue]Loading up virtual environment...[/bold blue]")
        env = EnvManager(self.poetry).get()
        console.log(f"[bold blue]Virtual Environment: [/bold blue][bold green]{env.path}[/bold green]")

        console.log("[bold blue]Running Docker fetch BDK runtime version...[/bold blue]")
        region_name = self.poetry.pyproject.data.get("cloud", {}).get("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if not region_name:
            console.log("[bold red]AWS_REGION is not set in pyproject.toml or environment variables[/bold red]")
            return 1

        latest_tag = get_latest_bdk_runtime_version(image_repository="kognitos/bdk", region_name=region_name)

        if not latest_tag:
            console.log("[bold red]Failed to fetch BDK runtime latest version[/bold red]")
            return 1

        current_bdk_runtime_version = self.poetry.pyproject.data.get("environment", {}).get("bdk_runtime_version")

        console.log(f"[bold blue]Current BDK runtime version: {current_bdk_runtime_version}[/bold blue]")

        if current_bdk_runtime_version == latest_tag:
            console.log("[bold blue]Current BDK runtime version is up-to-date[/bold blue]")
            return 0

        self.poetry.pyproject.data["environment"]["bdk_runtime_version"] = latest_tag  # type: ignore
        self.poetry.pyproject.file.write(self.poetry.pyproject.data)

        console.log(f"[bold blue]pyproject.toml updated successfully with BDK runtime version {latest_tag}[/bold blue]")
        return 0
