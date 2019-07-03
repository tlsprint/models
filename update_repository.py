import json
import os
import sys

import click
import gitlab
import requests
from jinja2 import Template


def query_docker_image_tags(image):
    req = requests.get(
        f"https://registry.hub.docker.com/v1/repositories/tlsprint/{image}/tags"
    )
    tag_info = json.loads(req.content.decode())
    return {info["name"] for info in tag_info}


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
    tags = query_docker_image_tags("openssl")

    # For now only use image > 1.0.1, these support all TLS12
    targets = [
        {"implementation": "openssl", "version": version, "supported_TLS": ["TLS12"]}
        for version in tags
        if version > "1.0.1"
    ]
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
