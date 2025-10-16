# Link Audit

[![PythonCodeAudit Badge](https://img.shields.io/badge/Python%20Code%20Audit-Security%20Verified-FF0000?style=flat-square)](https://github.com/nocomplexity/codeaudit)

[![PyPI - Version](https://img.shields.io/pypi/v/linkaudit.svg)](https://pypi.org/project/linkaudit)
[![Documentation](https://img.shields.io/badge/Link%20Audit%20Handbook-Available-blue)](https://nocomplexity.com/documents/linkaudit)
[![License](https://img.shields.io/badge/License-GPLv3-FFD700)](https://github.com/nocomplexity/linkaudit/blob/main/LICENSE.md)

LinkAudit – Superfast, simple, and deadly accurate to find broken links in markdown.

This `linkaudit` tool has the following features:

* Shows all external links (aka URLs) for a Shpinx or JupyterBook. Output is saved.
* Validate status of all discoverd external links for a Sphinx or Jupyterbook document. Output is saved.


## Installation

```
pip install linkaudit

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

## Documentation
Full documentation is available at [https://nocomplexity.com/documents/linkaudit](https://nocomplexity.com/documents/linkaudit)

## License

This tool is licensed  GPL-3.0-or-later. 

