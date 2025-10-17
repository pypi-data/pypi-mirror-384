# Sphinx Indexed Definitions

## Introduction

This Sphinx extension provides an easy way to add entries to a genreated index based on **strong**, *emphasized* and/or `literal` terms used within `prf:definition` admonitions and the title of the adminition.

## What does it do?

If you code includes an admonition with the source code

```md
:::{prf:definition} Lorem
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse **Pharetra**, ex ut commodo varius,
est justo vestibulum nunc, *(id) dignissim* lorem nibh in mauris. Duis varius lorem et neque posuere,
ac elementum eros consequat. Maecenas sed risus suscipit, **fermentum Kelvin** quam vitae, consectetur
augue. Maecenas aliquam leo vitae velit interdum efficitur.
:::
```

this extension, once loaded, will add (with default settings) the terms Lorem, **pharetra**, *id dignissim*, *dignissim* and **fermentum Kelvin** to the generated index.

This extension can be used in conjunction with the regular usage of generating an index, as explained at [Indexes](https://jupyterbook.org/en/stable/content/content-blocks.html#indexes).

## Installation
To use this extenstion, follow these steps (be aware, more steps then usual):

**Step 1: Install the Package**

Install the module `sphinx-indexed-definitions` package using `pip`:
```
pip install sphinx-indexed-definitions
```
    
**Step 2: Add to `requirements.txt`**

Make sure that the package is included in your project's `requirements.txt` to track the dependency:
```
sphinx-indexed-definitions
```

**Step 3: Enable in `_config.yml`**

In your `_config.yml` file, add the extension to the list of extra Sphinx extensions (**important**: underscore, not dash this time):
```
sphinx: 
    extra_extensions:
        .
        .
        .
        - sphinx_indexed_definitions
        .
        .
        .
```

**Step 4: Add the general index to ToC**

To do this, if you have not done this, please follow the instructions at [Add the general index to your table of contents](https://jupyterbook.org/en/stable/content/content-blocks.html#add-the-general-index-to-your-table-of-contents).

## Configuration

The extension provides several configuration values, which can be added to `_config.yml` if the default value should be changed:

```yaml
sphinx: 
    config:
        -
        -
        -
        sphinx_indexed_defs_indexed_nodes:     ['strong','emphasis'] # default value
        sphinx_indexed_defs_skip_indices:      []                    # default value
        sphinx_indexed_defs_lowercase_indices: true                  # default value
        sphinx_indexed_defs_index_titles:      true                  # default value
        sphinx_indexed_defs_capital_words:     []                    # default value
        sphinx_indexed_defs_remove_brackets:   true                  # default value
        sphinx_indexed_defs_force_main:        true                  # default value
        sphinx_indexed_defs_index_theorems:    true                  # default value
        -
        -
        -
```

- `sphinx_indexed_defs_indexed_nodes`: `['strong','emphasis']` (_default_) or **list of strings**:
  - All nodes of the provided classes from the Python submodule `docutils.nodes` will be extracted and converted to entries in the index.
  - Supported classes are `strong`, `emphasis` and `literal`.
- `sphinx_indexed_defs_skip_indices`: `[]` (_default_) or **list of strings**:
  - All entries that match at least one _regular expression_ within the provided list will not be added to the index (i.e. skipped).
  - An example is `['\bdet\w*','\$i\$-th entry']`, which causes any entry that starts with _det_ to be skipped and the entry _$i$-th entry_ will also be skipped.
  - Note that special characters must be escaped.
- `sphinx_indexed_defs_lowercase_indices`: `true` (_default_) or `false`:
  - If `true`, all extracted entries will be converted to lower case, except for words that are provided in `sphinx_indexed_defs_capital_words` and a prefixed set of common names from beta sciences. 
  - This prefixed set can be found in the source `py`-file of this extension.
  - Users are welcome to add names to this list by forking and opening a pull request. 
  - If `false`, all extracted entries will be added to the index as written.
- `sphinx_indexed_defs_index_titles`: `true` (_default_) or `false`:
  - If `true`, any title provided in a `prf:definition` admonition will also be added as an entry to the index.
  - If `false`, all titles in `prf:definition` admonitions will be ignored.
- `sphinx_indexed_defs_capital_words`: `[]` (_default_) or **list of strings**:
  - See `sphinx_indexed_defs_lowercase_indices`.
- `sphinx_indexed_defs_remove_brackets`: `true` (_default_) or `false`:
  - If `true`, any extracted term containing words between matching opening and closing round brackets, i.e. `(` and `)`, are converted to two entries: one with the entire term with all round brackets removed, and one with all words between matching round brackets removed (including the brackets).
  - An example: the extracted term `(id) dignissim` will result in two entries: `id dignissim` and `dignissim`.
  - If `false`, no parsing of terms with brackets will occur and terms are converted to entries as written.
- `sphinx_indexed_defs_force_main`: `true` (_default_) or `false`:
  - If `true`, all extracted terms will be added as the **main** entry to the index, which means the entry will be emphasized in the generated index.
  - If `false`, extracted terms will not be emphasized in the generated index.
- `sphinx_indexed_defs_index_theorems`: `true` (_default_) or `false`:
  - If `true`, any title provided in a `prf:theorem`, `prf:lemma`, `prf:conjecture`, `prf:corollary` or `prf:proposition` admonition will also be added as an entry to the index.
  - If `false`, all titles provided in `prf:theorem`, `prf:lemma`, `prf:conjecture`, `prf:corollary` and `prf:proposition` admonitions will be ignored.
 
## Provided code

In case a single admonition should be skipped during indexing, add the class `skipindexing` to the admonition, for example:

```md
:::{prf:definition} Lorem
:class: skipindexing

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse **Pharetra**, ex ut commodo varius,
est justo vestibulum nunc, *(id) dignissim* lorem nibh in mauris. Duis varius lorem et neque posuere,
ac elementum eros consequat. Maecenas sed risus suscipit, **fermentum Kelvin** quam vitae, consectetur
augue. Maecenas aliquam leo vitae velit interdum efficitur.
:::
```

## Example

An example of an index generated using this extension can be found at https://douden.github.io/openlabook/main/genindex.html.

## Contribute

This tool's repository is stored on [GitHub](https://github.com/TeachBooks/Sphinx-Indexed-Definitions). If you'd like to contribute, you can create a fork and open a pull request on the [GitHub repository](https://github.com/TeachBooks/Sphinx-Indexed-Definitions). 
The `README.md` of the branch `manual` is also part of the [TeachBooks manual](https://teachbooks.io/manual).
