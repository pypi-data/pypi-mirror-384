# Quick docker build

This script is used to copy source code to the runtimes docker image for quick testing. DO NOT USE IN PRODUCTION.

## Usage

Copy the script and the Dockerfiles into the same folder. Clone the repository of digitalhub-sdk also in the same folder. When you add modifications to the repo and want to test them, run the script.:

```bash
./build_containers.sh
```

By default the script uses the latest version of the runtime images. To use a specific version, specify as argument the desired tag.

```bash
./build_containers.sh tag
```

## Runtimes

The following runtimes are available:

- dbt
- kfp
- python 3.9
- python 3.10
- python 3.11

To only build specific runtimes, comment out the others.
