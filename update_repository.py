import datetime
import json
import logging
from distutils.version import LooseVersion
from pathlib import Path

import click
import dymport
import git
import requests
from git import Repo
from jinja2 import Template

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


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


def query_learned_models(implementation, model_dir="models"):
    directory = Path(model_dir) / implementation
    try:
        versions = {path.name for path in directory.iterdir()}
        combinations = {
            (version, path.name)
            for version in versions
            for path in (directory / version).iterdir()
        }
        return combinations
    except FileNotFoundError:
        return set()


@click.command()
@click.option(
    "--commit",
    is_flag=True,
    default=False,
    help="Indicates whether the files modified by this script should be committed.",
)
def main(commit):
    logger.info("Updating submodules")
    update_submodules()

    implementation_dirs = [
        path for path in Path("docker-images").iterdir() if path.is_dir()
    ]
    logger.info("Found the following implementations:")
    for directory in implementation_dirs:
        logger.info("  - %s", directory.name)

    targets = []
    for directory in implementation_dirs:
        implementation = directory.name

        logger.info(f"Querying image tags for '{implementation}'")

        try:
            docker_tags = query_docker_image_tags(implementation)
        except TypeError:
            # Query failed
            logger.warning(f"Failed to retrieve tags for '{implementation}'")
            continue

        logger.info(f"  - found {len(docker_tags)} tags in Docker registry")

        # Query supported TLS versions for every tag
        module = dymport.import_file(implementation, directory / "__init__.py")
        tag_protocol_version_map = {
            tag: module.get_supported_tls(tag) for tag in docker_tags
        }

        # Create a set of all (tag, protocol) combinations
        possible_combinations = {
            (tag, protocol)
            for tag, protocols in tag_protocol_version_map.items()
            for protocol in protocols
        }

        logger.info(
            f"  - found {len(possible_combinations)} possible tag-protocol combinations"
        )

        # Check which versions already have models
        learned_combinations = query_learned_models(implementation)

        logger.info(
            f"  - found {len(learned_combinations)} learned tag-protocol combinations"
        )

        # Takes the difference of all possible combinations and the
        # combinations already learned, to get the set of combinations which
        # still need to be learned.
        combinations_to_learn = possible_combinations - learned_combinations

        logger.info(
            f"  - found {len(combinations_to_learn)} tag-protocol combinations to learn"
        )

        # Sort for deterministic output
        combinations = sorted(
            combinations_to_learn, key=lambda comb: (LooseVersion(comb[0]), comb[1])
        )

        # Append to the list of learning targets for use in the template
        targets += [
            {"implementation": implementation, "version": version, "protocol": protocol}
            for version, protocol in combinations
        ]

    logger.info(f"Found {len(targets)} tag-protocol combinations to learn in total")
    logger.info("Generating .drone.yml from template")

    with open(".drone.yml.j2") as f:
        template = Template(f.read())

    with open(".drone.yml", "w") as f:
        f.write(template.render(targets=targets))

    if commit:
        repo = git.Repo(".")
        # Since this script is supposed to run autonomously on the master
        # branch, we make the (potentially dangerous) assumption that we need
        # to checkout the master branch (since the CI is in detached state).
        repo.git.checkout("master")
        repo.git.pull("--rebase")

        logger.info("Commiting files")
        repo.git.add(".")
        repo.git.commit(message=f"Automatic update {datetime.date.today()}")
        repo.git.push()


if __name__ == "__main__":
    main()
