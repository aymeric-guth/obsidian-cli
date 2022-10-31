# obsidian-cli

## Description

CLI helper for Obsidian

## Installation

```shell
python3 -m virtualenv .venv
source .venv/bin/activate
python -m pip install git+https://git.ars-virtualis.org/yul/obsidian-cli@master

# hopefully a setup.py soon
```

### Environment Setup

1 environment variable is required

OBSIDIAN_VAULT
location of your obsidian vault on disk

1 is optional
STACK_FILE
(for lack of a better name)
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

## References

https://help.obsidian.md/Advanced+topics/Using+obsidian+URI
https://forum.obsidian.md/t/use-obsidian-uri-to-open-a-static-link-with-id/17360
https://forum.obsidian.md/t/command-line-interface-to-open-files-folders-in-obsidian-from-the-terminal/860/40
https://forum.obsidian.md/t/anyone-using-imdone-io-that-can-elaborate-on-its-use/13340
