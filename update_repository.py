import os
import sys

import click
import gitlab


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
def main(api_key, gitlab_url, project_id, verbose):
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
    project = gl.projects.get(50)


if __name__ == "__main__":
    main()
