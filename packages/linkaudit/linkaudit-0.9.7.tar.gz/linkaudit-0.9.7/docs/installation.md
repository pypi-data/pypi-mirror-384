# Installation and Usage

## Installation

Linkaudit can be installed using `pip`:
```
pip install -U linkaudit
```


## Usage

Linkaudit is a CLI tool.

To get help just run `linkaudit` without arguments.
```shell 
Linkaudit

Command 	: showlinks
Shows all URLs from MyST Markdown files in a directory and generates an HTML report.

Command 	: checklinks
Print txt tables of URLs checks of JB Book

Command 	: version
Prints the module version. Use [-v] [--v] [-version] or [--version].

Use linkaudit [COMMAND] --help for detailed help per command.
```

To use it on a  documentation created for `Jupyterbook` or `Sphinx`:

To show links, do:
```
linkaudit showlinks [DIRECTORY_TO_SPHINX or JUPYERBOOK files]
```

To check links, do:
```
linkaudit checklinks [DIRECTORY_TO_SPHINX or JUPYERBOOK files]
```

