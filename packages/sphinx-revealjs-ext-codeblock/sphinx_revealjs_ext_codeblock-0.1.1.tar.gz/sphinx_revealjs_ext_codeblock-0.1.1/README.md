# sphinx-revealjs-ext-codeblock

[![PyPI - Version](https://img.shields.io/pypi/v/sphinx-revealjs-ext-codeblock.svg)](https://pypi.org/project/sphinx-revealjs-ext-codeblock)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sphinx-revealjs-ext-codeblock.svg)](https://pypi.org/project/sphinx-revealjs-ext-codeblock)

Extend `code-block` directive for Sphinx `revealjs` builder.

-----

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation

```console
pip install sphinx-revealjs-ext-codeblock
```

## Usage

conf.py

```python
extensions = [
    "sphinx_revealjs",
    "sphinx_revealjs_ext_codeblock",
]
```

Specify `revealjs_script_plugins` & `revealjs_css_files`.

* https://sphinx-revealjs.readthedocs.io/en/stable/configurations/#confval-revealjs_script_plugins
* https://sphinx-revealjs.readthedocs.io/en/stable/configurations/#confval-revealjs_css_files

### Line Numbers

```rst
.. code-block:: python
    :linenos:

    while True:
        print("Hello world!")
```

```html
<pre>
  <code class="python" data-line-numbers>
while True:
    print(&quot;Hello world!&quot;)
  </code>
</pre>
```

See https://revealjs.com/code/#line-numbers-%26-highlights

### Highlights

```rst
.. code-block:: python
    :emphasize-lines: 2

    while True:
        print("Hello world!")
```

```html
<pre>
  <code class="python" data-line-numbers="2">
while True:
    print(&quot;Hello world!&quot;)
  </code>
</pre>
```

See https://revealjs.com/code/#line-numbers-%26-highlights

## License

`sphinx-revealjs-ext-codeblock` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
