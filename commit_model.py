import json
import os
import sys

import click
import gitlab


@click.command()
@click.option("--implementation", required=True, help="Name of the implementation")
@click.option("--version", required=True, help="Version of the implementation")
@click.option(
    "--tls-version",
    required=True,
    type=click.Choice(["TLS10", "TLS11", "TLS12"]),
    help="TLS version for which this model is learned",
)
@click.option(
    "--model",
    required=True,
    type=click.File("r"),
    help="File where the model to be committed is stored",
)
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
def main(
    implementation,
    version,
    tls_version,
    model,
    api_key,
    gitlab_url,
    project_id,
    verbose,
):
    """Commit the model of a TLS implementation to a Git repository."""
    # Make sure the implementation name and version is lowercase
    implementation = implementation.lower()
    version = version.lower()

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

    data = {
        "id": project_id,
        "branch": "master",
        "commit_message": f"Add model of {implementation} version {version}, for {tls_version}",
        "actions": [
            {
                "action": "create",
                "file_path": f"{implementation}/{version}/{tls_version}/learnedModel.dot",
                "content": model.read(),
            }
        ],
    }

    if verbose:
        print("Data:")
        print(json.dumps(data, indent=4))

    project = gl.projects.get(50)

    # Create commit
    commit = project.commits.create(data)

    if verbose:
        print(commit)


if __name__ == "__main__":
    main()
