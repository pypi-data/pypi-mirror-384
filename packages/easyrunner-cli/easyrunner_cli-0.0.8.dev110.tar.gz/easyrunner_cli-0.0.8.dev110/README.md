# EasyRunner CLI

Application hosting platform that runs on a single server. Easily turn your VPS into a secure web host.

Copyright (c) 2024 - 2025 Janaka Abeywardhana

## Contribution

Setup python tools on a new machine

- `brew install pyenv` - python virtual environment manager
- `brew install pipx` - pipx python package manager, for install poetry
- `pipx install poetry` (pipx installs global packages in isolated environments)
- add `export PATH="$HOME/.local/bin:$PATH"` to ~/.zshrc for poetry.


Setup python environment for an application

- `pyenv install 3.13` install this version of python.
- `pyenv local` show the version in this environment
- `poetry env use $(pyenv which python)` to create a poetry environment in this project for dependencies. the `.venv`
- `source $(poetry env info --path)/bin/activate` to activate the environment (avail on path etc.)
- `poetry config virtualenvs.in-project true`
- `poetry install`

if the location of the repo changes on your local machine then the virtual env will get disconnected. Therefore remove and recreate

- `poetry env remove $(poetry env list --full-path | grep -Eo '/.*')` Remove the current Poetry environment to force a clean rebuild:
- `poetry install` Recreate the environment and install dependencies
- `source $(poetry env info --path)/bin/activate` activate the environment