import json
import os
import sys

import click
import requests


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
def main(implementation, version, tls_version, model, api_key, gitlab_url, project_id):
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

    headers = {"PRIVATE-TOKEN"}

    payload = {
        "id": project_id,
        "branch": "master",
        "commit_message": f"Add model of {implementation} version {version}, for {tls_version}",
        "actions": [
            {
                "action": "create",
                "file_path": "{implementation}/{version}/{tls_version}/learnedModel.dot",
                "content": model.read(),
            }
        ],
    }

    url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/commits"

    req = requests.post(
        f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits",
        headers=headers,
        json=payload,
    )

    if req.status_code != 201:
        print("Failed to create commit:", file=sys.stderr)
        print(json.dumps(json.loads(req.content.decode()), indent=4), file=sys.stderr)
        sys.exit(1)
    else:
        print(json.dumps(json.loads(req.content.decode()), indent=4), file=sys.stderr)


if __name__ == "__main__":
    main()
