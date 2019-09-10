from matplotlib import pyplot
from pathlib import Path
from tlsprint.learn import _dot_to_networkx
from distutils.version import LooseVersion
from collections import defaultdict
import click
import json


tls_versions = ["TLS10", "TLS11", "TLS12"]

# root = Path("models")
# for implementation_path in root.iterdir():
#     states_per_version = {tls: {} for tls in tls_versions}
#     for version_path in implementation_path.iterdir():
#         for tls_path in version_path.iterdir():
#             model_path = tls_path / "learnedModel.dot"
#             with open(model_path) as f:
#                 model = _dot_to_networkx(f.read())
#             states_per_version[tls_path.name][version_path.name] = len(model.nodes) - 1
#             print(tls_path)


#     for tls in tls_versions:
#         version_counts = sorted(states_per_version[tls].items(), key=lambda x: LooseVersion(x[0]))
#         versions = [version for version, _ in version_counts]
#         counts = [count for _, count in version_counts]
#         pyplot.plot(versions, counts)
#         print(versions)
#         print(counts)
#     pyplot.show()
#

def extract_for_version(version_path):
    tls_paths = list(version_path.iterdir())
    results = {}
    for path in tls_paths:
        model_path = path / "learnedModel.dot"
        with open(model_path) as f:
            model = _dot_to_networkx(f.read())
        results[path.name] = len(model.nodes) - 1
    return results


def extract_for_implementation(implementation_path):
    verion_paths = list(implementation_path.iterdir())
    results = defaultdict(list)
    for path in verion_paths:
        version_results = extract_for_version(path)
        for tls, count in version_results.items():
            results[tls].append((path.name, count))

    results = {
        tls: sorted(info, key=lambda x: LooseVersion(x[0])) for tls, info in results.items()
    }
    return results


@click.group()
def main():
    """Extract and plot states per TLS implementation version."""
    pass


@main.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("output", type=click.File(mode="w"))
def extract(directory, output):
    """Extract states per version from model directory."""
    root_path = Path(directory)
    implementation_paths = list(root_path.iterdir())
    results = {}
    for path in implementation_paths:
        results[path.name] = extract_for_implementation(path)

    json.dump(results, output)



def plot_implementation(data):
    data = sorted(data.items())
    for i, (tls, version_info) in enumerate(data):
        versions = [version for version, _ in version_info]
        counts = [count for _, count in version_info]
        pyplot.plot(versions, counts, label=tls)
    pyplot.tick_params(axis="x", labelbottom=False, bottom=False)
    pyplot.ylim(5, 15)
    pyplot.ylabel("Number of states")
    pyplot.legend()


@main.command()
@click.argument("input_file", type=click.File())
def plot(input_file):
    """Plot extracted information."""
    implementation_data = json.load(input_file)
    pyplot.style.use("ggplot")
    pyplot.figure(figsize=(10, 3))
    for i, (implementation, data) in enumerate(implementation_data.items()):
        pyplot.subplot(1, len(implementation_data), i + 1)
        pyplot.title(implementation)
        plot_implementation(data)
    pyplot.savefig("plot.svg")


if __name__ == "__main__":
    main()
