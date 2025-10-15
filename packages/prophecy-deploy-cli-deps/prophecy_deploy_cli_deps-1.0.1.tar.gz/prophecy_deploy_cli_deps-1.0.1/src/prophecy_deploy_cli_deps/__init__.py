from importlib import resources as _resources
from pathlib import Path as _Path

def get_bin_dir() -> str:
    """Return filesystem path to the bin directory containing dependencies."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/bin")) as p:
        return str(_Path(p))

def get_hyperd_path() -> str:
    """Return filesystem path to the hyperd binary."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/bin/hyperd")) as p:
        return str(_Path(p))

def get_lib_tableau_cpp_path() -> str:
    """Return filesystem path to libTableauCppLibrary.so."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/bin/libTableauCppLibrary.so")) as p:
        return str(_Path(p))

def get_lib_tableau_hyperapi_path() -> str:
    """Return filesystem path to libtableauhyperapi.so."""
    with _resources.as_file(_resources.files(__package__).joinpath("deploy-cli-standalone-v1.0.1-jpmc-bec9ef6/bin/libtableauhyperapi.so")) as p:
        return str(_Path(p))
