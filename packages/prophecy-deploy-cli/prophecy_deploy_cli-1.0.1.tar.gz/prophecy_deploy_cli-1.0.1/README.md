# prophecy-deploy-cli

Complete Prophecy Deploy CLI package for JPMC.

## Contents
This is a metapackage that automatically installs:
- `prophecy-deploy-cli-core` (main executable)
- `prophecy-deploy-cli-deps` (dependencies)

## Install
```bash
pip install prophecy-deploy-cli
```

## Usage
```python
import prophecy_deploy_cli

# Get path to the main executable
binary_path = prophecy_deploy_cli.get_binary_path()
print(f"CLI binary: {binary_path}")

# Get path to the directory containing all CLI files
binary_dir = prophecy_deploy_cli.get_binary_dir()
print(f"CLI directory: {binary_dir}")

# Get path to the shell script wrapper
shell_script = prophecy_deploy_cli.get_shell_script_path()
print(f"Shell script: {shell_script}")

# Get path to dependencies directory
deps_dir = prophecy_deploy_cli.get_deps_dir()
print(f"Dependencies directory: {deps_dir}")
```

## Package Structure
This package is split into multiple components to stay under PyPI file size limits:
- **Core**: Main executable and configuration (~200MB)
- **Dependencies**: Required libraries and binaries (~120MB)
- **Meta**: This package that depends on both
