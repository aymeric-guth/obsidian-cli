# obsidian-cli

## Description

CLI helper for Obsidian

## Installation

```shell
python3 -m virtualenv .venv
source .venv/bin/activate
python -m pip install git+https://git.ars-virtualis.org/yul/obsidian-cli@master

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
# open obsidian
obsidian

# opens default file if filename is not provided
# else, tries to open filename
obsidian open | o [filename]

# query, can be any of tag, nested tag
# filename has to exist
obs find | f #query | filename
```

### References

https://help.obsidian.md/Advanced+topics/Using+obsidian+URI
https://forum.obsidian.md/t/use-obsidian-uri-to-open-a-static-link-with-id/17360
https://forum.obsidian.md/t/command-line-interface-to-open-files-folders-in-obsidian-from-the-terminal/860/40
https://forum.obsidian.md/t/anyone-using-imdone-io-that-can-elaborate-on-its-use/13340

https://publish.obsidian.md/hub/04+-+Guides%2C+Workflows%2C+%26+Courses/Guides/Markdown+Syntax
https://help.obsidian.md/How+to/Format+your+notes

slide 53
https://www.slideshare.net/billkarwin/models-for-hierarchical-data

#### AIOSQL

https://nackjicholson.github.io/aiosql/defining-sql-queries.html#query-names


### Commands

```shell
# opens all files containing tag language/go
o find files language/go | xargs -I '{}' zsh -c '$WORKSPACE/.venv/bin/python -m $PROJECT_NAME open "{}"'

# take 10 random entry from orphaned in /001 Zettelkasten
shuf -n 10 <(o find orphaned 001\ Zettelkasten)
```
