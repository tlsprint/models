import json
import os
import sys
from distutils.version import LooseVersion
from pathlib import Path

import click
import gitlab
import requests
from jinja2 import Template
from git import Repo
import dymport

def update_submodules():
    repo = Repo(".")

    for submodule in repo.submodules:
        # Pull the most recent version of the submodule
        module = submodule.module()
        module.heads.master.checkout()
        module.remote().pull()

        # Update the submodules of this submodule
        module.git.submodule(["update", "--recursive"])


def query_docker_image_tags(image):
    req = requests.get(
        f"https://registry.hub.docker.com/v1/repositories/tlsprint/{image}/tags"
    )
    tag_info = json.loads(req.content.decode())
    return {info["name"] for info in tag_info}


def query_tags_with_models(implementation, model_dir="models"):
    directory = Path(model_dir) / implementation
    try:
        return {path.name for path in directory.iterdir()}
    except FileNotFoundError:
        return set()


@click.command()
@click.option(
    "--api-key",
    help="Gitlab API key. If empty, the 'GITLAB_TLSPRINT_API_KEY' environment variable will be used instead.",
)
@click.option(
    "--gitlab-url",
    default="https://gitlab.sidnlabs.nl",
    help="Base URL for the Gitlab installation",
)
@click.option(
    "--project-id",
    default=50,
    help="Gitlab ID of the project where the model should be committed to",
)
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Provide verbose output"
)
@click.option(
    "--commit",
    is_flag=True,
    default=False,
    help="Indicates whether the files modified by this script should be committed.",
)
def main(api_key, gitlab_url, project_id, verbose, commit):

    if verbose:
        print("Updating submodules")
    update_submodules()

    implementation_dirs = [path for path in Path("docker-images").iterdir() if path.is_dir()]
    if verbose:
        print("Found the following implementations:")
        for directory in implementation_dirs:
            print("  -", directory.name)

    targets = []
    model_dir = Path("models")
    for directory in implementation_dirs:
        implementation = directory.name

        if verbose:
            print(f"Querying image tags for '{implementation}'")

        try:
            docker_tags = query_docker_image_tags(implementation)
        except TypeError:
            # Query failed
            print(f"Failed to retrieve tags for '{implementation}'", file=sys.stderr)
            continue

        if verbose:
            print(f"  - found {len(docker_tags)} tags in Docker registry")

        # Check which versions already have models
        model_tags = query_tags_with_models(implementation)

        if verbose:
            print(f"  - found {len(model_tags)} tags with learned models")

        tags_to_learn = docker_tags - model_tags

        if verbose:
            print(f"  - found {len(tags_to_learn)} tags to learn")

        # Sort tags for deterministic output
        versions = sorted(tags_to_learn, key=LooseVersion)

        # Get supported TLS versions for every implementation, and add to
        # targets.
        module = dymport.import_file(implementation, directory / "__init__.py")
        targets += [
            {
                "implementation": implementation,
                "version": version,
                "supported_tls": module.get_supported_tls(version),
            } for version in versions
        ]

    if verbose:
        print(f"Found {len(targets)} versions to learn in total")
        print("Generating .drone.yml from template")

    with open(".drone.yml.j2") as f:
        template = Template(f.read())

    with open(".drone.yml", "w") as f:
        f.write(template.render(targets=targets))

    if commit:
        # Query environment variable if --api-key is not passed
        if not api_key:
            try:
                api_key = os.environ["GITLAB_TLSPRINT_API_KEY"]
            except KeyError:
                print(
                    "No API key specified. Specify via --api-key or define GITLAB_TLSPRINT_API_KEY.",
                    file=sys.stderr,
                )
                sys.exit(1)

        gl = gitlab.Gitlab(gitlab_url, private_token=api_key)
        project = gl.projects.get(project_id)


if __name__ == "__main__":
    main()
