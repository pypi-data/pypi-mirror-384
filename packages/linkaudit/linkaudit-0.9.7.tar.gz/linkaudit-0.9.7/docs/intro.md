# Introduction

[![PythonCodeAudit Badge](https://img.shields.io/badge/Python%20Code%20Audit-Security%20Verified-FF0000?style=flat-square)](https://github.com/nocomplexity/codeaudit)

Linkaudit is a simple CLI tool to check for broken links in `markdown` in Sphinx or [JupyterBook](https://jupyterbook.org/en/stable/intro.html) documentation.  

All `markdown`, `MyST`, or `rst` used in a documentation directory are checked. 

This tool is created to make maintenance of broken links simpler when working with Jupyterbook or Sphinx.

:::{attention} 
This tool is created for JupyterBook `version 1`, so the version that is build upon Sphinx. JupyterBook version 2 will still be working with `MyST markdown` files, this tool should also work for that version. 
:::

## Background

The Internet is flooded with broken links. However keeping documentation with many links up-to-date is shit work. Even great FOSS CMS systems like WordPress do not offer by default automatic link checking. And installing a `plugin` for WordPress is not the way forward. Trustworthy documentation on the internet is maintained. Maintaining text is still partly manual work. But online documentation created with `Sphinx` and `Jupyterbook` is partly generated to get the advantage of 'living' documentation. But dead links in documentation is frustrating. For readers and for documentation creators.

To avoid misunderstandings: The [Sphinx linkcheck builder](https://www.sphinx-doc.org/en/master/usage/builders/index.html#module-sphinx.builders.linkcheck) is a great piece of Python software. It does the job and it works! If you use Jupyterbook or Sphinx with a lot of URLs in your documentation this tool can be used to check dead links. Use it by:
```shell
Usage: jb build [OPTIONS] PATH_SOURCE

and with the option:
--builder linkcheck

So:

jb build --builder linkcheck PATH_SOURCE

```

:::{tip}
If you create of maintain documentation created in markdown that has many URLs, this `Linkaudit` tool is designed to be a fast and simple solution to maintain working URLs in your documentation.
:::

Running the default Sphinx link checker on documentation with `markdown` and `*.rst` with many links  did give me energy to create something simpler and better. Of course I searched to find a better alternative to check `Sphinx` or `JupyterBook` documentation on dead links, but could not find a simple tool. This is always a good motivation to [make IT better](https://nocomplexity.com/business/)!

My arguments to make a simpler and better link checker to correct broken links :
* The Sphinx code for the linkcheck builder is not simple to adjust and make it better. The [Sphinx linkcheck](https://www.sphinx-doc.org/en/master/_modules/sphinx/builders/linkcheck.html#CheckExternalLinksBuilder) code is  complex and intimidating to improve. 
* Reuse existing Sphinx code and create pull request would be time consumming. With a uncertain outcome. Hetting adjusted code into the core code base of Sphinx, which code is used at large, is not simple! And the linkcheck builder is a Sphinx core module.
* The overview of the default Sphinx linkcheck is not very clear. All links are tested and I only am interested in broken links. 
* Correcting or removing dead links is often manual work and should be as frictionless as possible. So per file and line number a status of a broken link.
* When a Jupyer Book or directory of `*.md` or `*.rst` files contain a lot of URLs link checking should be fast. And since link checking is an I/O operation, this should be done using the Python `asyncio` module.

A great advantage of online publication is to use URLs that can be used, studied or read later. But URLs are not all stable. Most publications on the internet are no scientific publications with a URI or DOI that is designed to be active and stable.

```{tableofcontents}
```
