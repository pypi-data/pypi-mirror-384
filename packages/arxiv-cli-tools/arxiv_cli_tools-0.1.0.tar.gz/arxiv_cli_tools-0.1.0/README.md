# arxiv-cli-tools

Command-line interface for searching and downloading arXiv papers, built on top of the [arxiv](https://pypi.org/project/arxiv/) Python client.

## Installation

```bash
pip install arxiv-cli-tools
```

To work from source instead, clone the repository and install in editable mode:

```bash
pip install -e .
```

## Usage

Inspect the available commands and options:

```bash
arxiv-cli --help
arxiv-cli search --help
arxiv-cli download --help
```

Typical commands:

```bash
# Search the API and show abstracts
arxiv-cli search "prompt engineering" -n 5 --summary

# Fetch specific papers by identifier into a folder
arxiv-cli download --id 2101.01234 --id 2105.06789 --dest papers --skip-existing
```

The CLI mirrors the underlying arXiv API, adding convenience flags for authors, categories, result limits, and download preferences. See the built-in help for the full reference.
