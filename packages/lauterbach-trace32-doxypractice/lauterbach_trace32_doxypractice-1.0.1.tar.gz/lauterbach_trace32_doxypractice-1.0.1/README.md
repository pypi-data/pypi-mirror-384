# Doxypractice

**Doxypractice** is a language filter for [Doxygen](https://www.doxygen.nl) that adds support for Lauterbach TRACE32 scripts.
It translates TRACE32 scripts into a C-like format that is understood by Doxygen.

## Quick Start

### Dependencies

Python version 3.10 or higher is required.

- [chardet](https://github.com/chardet/chardet)
- [Doxygen](https://www.doxygen.nl)
- [Python Tree-sitter](https://github.com/tree-sitter/py-tree-sitter)
- [tree-sitter-t32](https://codeberg.org/xasc/tree-sitter-t32)

### Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Doxypractice.

```bash
pip install doxypractice
```

### Usage

Doxypractice is a console script that expects the path to a PRACTICE file as only input argument:

```bash
doxypractice <script>
```

### Doxygen Integration

To integrate Doxypractice with Doxygen, update your `Doxyfile`[^1] as follows:

```ini
EXTENSION_MAPPING   = cmm=C++
FILTER_PATTERNS     = *.cmm=doxypractice
FILE_PATTERNS       = *.cmm
FILTER_SOURCE_FILES = YES
INLINE_SOURCES      = YES
```

Create the project documentation:

```bash
doxygen Doxyfile
```

> [!NOTE]
> Make sure Doxypractice is installed and in `PATH`.

[^1]: https://www.doxygen.nl/manual/starting.html#step1
