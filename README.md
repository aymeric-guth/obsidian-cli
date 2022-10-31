# obsidian-cli

## Description

CLI helper for Obsidian

## Installation

```shell
python3 -m virtualenv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app

# hopefully a setup.py soon
```

### Environment Setup

2 environment variables are required

OBSIDIAN_VAULT
location of your obsidian vault on disk

OBSIDIAN_DIR
location to local obsidian config dir
(hopefully a runtime lookup, soon)

1 optional
STACK_FILE
for lack of a better name
default file that will be opened


## Usage

```shell
# opens default file if filename is not provided
# else, tries to open filename
obs open | o [filename]

# query, can be any of tag, nested tag
# filename has to exist
obs find | f #query | filename
```
