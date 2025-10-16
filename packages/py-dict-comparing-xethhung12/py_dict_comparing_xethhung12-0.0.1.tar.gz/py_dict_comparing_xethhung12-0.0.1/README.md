
# py_dict_comparing

## Execution
Run through python interpreter:
```shell
python -m py_dict_comparing -h
```

Run through python project script
```shell
py-dict-comparing -h
```
## Development
The project requires `python` (3+ version) installed and `pip` ready for use on adding manage dependencies

#### Tools
|Name|Platform|Type|Description|
|---|---|---|---|
|install-dependencies.sh|shell|script| The scripts for installing depencies required|
|build.sh|shell|script| The scripts for build the package|
|build-and-deploy.sh|shell|script| The scripts for build and deploy the package|

* install-dependencies.sh
The script will install dependencies listed in `dev-requirements.txt` and `requirements.txt`. The first requirement file contains the dependencies for development like build and deploy tools. The second requirement file defined all required dependencies for the making the package works (**actual dependencies**).

## Useful Scripts
### Project Versioning
For version update in `pyproject.toml`.
This project use package [`xh-py-project-versioning`](https://github.com/xh-dev/xh-py-project-versioning) to manipulate the project version.

Simple usage includes:\
Base on current version, update the patch number with dev id
`python -m xh_py_project_versioning --patch` \
In case current version is `0.0.1`, the updated version will be `0.0.2-dev+000` 

To prompt the dev version to official version use command.
`python -m xh_py_project_versioning -r`.
Through the command, version `0.0.2-dev+000` will be prompt to `0.0.2` official versioning.

Base on current version, update the patch number directly
`python -m xh_py_project_versioning --patch -d` \
In case current version is `0.0.1`, the updated version will be `0.0.2` 

Base on current version, update the minor number directly
`python -m xh_py_project_versioning --minor -d` \
In case current version is `0.0.1`, the updated version will be `0.1.0` 

Base on current version, update the minor number directly
`python -m xh_py_project_versioning --minor -d` \
In case current version is `0.0.1`, the updated version will be `1.0.0` 