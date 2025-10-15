# prophecy-deploy-cli-deps

Dependencies package for the Prophecy Deploy CLI used by JPMC.

## Contents
- `hyperd` binary
- `libTableauCppLibrary.so` library
- `libtableauhyperapi.so` library

## Install
```bash
pip install prophecy-deploy-cli-deps
```

## Usage
```python
import prophecy_deploy_cli_deps

# Get path to the bin directory
bin_dir = prophecy_deploy_cli_deps.get_bin_dir()
print(f"Bin directory: {bin_dir}")

# Get specific binary paths
hyperd_path = prophecy_deploy_cli_deps.get_hyperd_path()
lib_cpp_path = prophecy_deploy_cli_deps.get_lib_tableau_cpp_path()
lib_hyperapi_path = prophecy_deploy_cli_deps.get_lib_tableau_hyperapi_path()
```

## Note
This package contains only the dependencies. For the complete CLI with the main executable, install `prophecy-deploy-cli` instead.
