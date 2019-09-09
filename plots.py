from matplotlib import pyplot
from pathlib import Path
from tlsprint.learn import _dot_to_networkx
from distutils.version import LooseVersion


tls_versions = ["TLS10", "TLS11", "TLS12"]

root = Path("models")
for implementation_path in root.iterdir():
    states_per_version = {tls: {} for tls in tls_versions}
    for version_path in implementation_path.iterdir():
        for tls_path in version_path.iterdir():
            model_path = tls_path / "learnedModel.dot"
            with open(model_path) as f:
                model = _dot_to_networkx(f.read())
            states_per_version[tls_path.name][version_path.name] = len(model.nodes) - 1
            print(tls_path)


    for tls in tls_versions:
        version_counts = sorted(states_per_version[tls].items(), key=lambda x: LooseVersion(x[0]))
        versions = [version for version, _ in version_counts]
        counts = [count for _, count in version_counts]
        pyplot.plot(versions, counts)
        print(versions)
        print(counts)
    pyplot.show()
