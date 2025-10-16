<!--suppress HtmlDeprecatedAttribute-->
<div align="center">
   <h1>😂 python-lolhtml</h1>

[![Build Status](https://github.com/Jayson-Fong/python-lolhtml/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/Jayson-Fong/python-lolhtml/actions/workflows/CI.yml)
[![Latest Version](https://img.shields.io/pypi/v/python-lolhtml.svg)](https://pypi.org/project/python-lolhtml/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-lolhtml.svg)](https://pypi.org/project/python-lolhtml/)
[![Format](https://img.shields.io/pypi/format/python-lolhtml.svg)](https://pypi.org/project/python-lolhtml/)
[![License](https://img.shields.io/pypi/l/python-lolhtml)](https://github.com/Jayson-Fong/python-lolhtml/blob/main/README.md)
[![Status](https://img.shields.io/pypi/status/python-lolhtml)](https://pypi.org/project/python-lolhtml/)
[![Types](https://img.shields.io/pypi/types/python-lolhtml)](https://pypi.org/project/python-lolhtml/)


</div>

<hr />

<div align="center">

[💼 Purpose](#purpose) | [⚡ Performance](#performance) | [⚙️ Usage](#usage)

</div>

<hr />

# Purpose

python-lolhtml provides Python bindings for the [lol-html](https://crates.io/crates/lol_html) Rust crate, enabling
HTML rewriting and parsing with minimal buffering while using CSS selectors.

It is particularly powerful when using Python as a reverse proxy to transform HTML content, such as for rewriting mixed
content links; however, while the API isn't directly made for it, it can also be used for web scraping.

# Performance

As a Python binding, parsing is predominantly offloaded to Rust, which can provide a noticeable speedup.

<details style="border: 1px solid; border-radius: 8px; padding: 8px; margin-top: 4px;">
<summary>🔍 python-lolhtml v. BeautifulSoup4: Text Extraction</summary>

For websites where there exists minimal content to parse, BeautifulSoup4 tends to produce output faster compared to 
python-lolhtml; however, when parsing real-world websites such as Wikipedia, there can be noticeable speedups in 
parsing time.

The following example fetches a Wikipedia article about the Python programming language. While this metric is not run on
standardized hardware (rather, it is a consumer-grace laptop with an Intel CPU), it produces the following output:

```
BeautifulSoup4: 36.397512998009915
python-lolhtml: 25.727217955995002
```

This demonstrates roughly a 1.4x speedup compared to parsing conducted with BeautifulSoup4 for text extraction.

```python
import timeit
from typing import List

import requests
from bs4 import BeautifulSoup

import lolhtml


content: str = requests.get(
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    headers={"User-Agent": "Python - Performance Testing"},
).text


def time_beautiful_soup():
    soup = BeautifulSoup(content, "html.parser")
    soup.get_text()


class ElementHandler:

    def __init__(self, value_store: List[str]):
        self.value_store: List[str] = value_store

    def text(self, text_chunk: lolhtml.TextChunk):
        self.value_store.append(text_chunk.text)


rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
element_handler: ElementHandler = ElementHandler([])
rewriter.on("*", element_handler)


def time_lolhtml():
    element_handler.value_store = []
    rewriter.transform(content)


print("BeautifulSoup4:", timeit.timeit(time_beautiful_soup, number=100))
print("python-lolhtml:", timeit.timeit(time_lolhtml, number=100))
```

</details>

# Usage

For any rewriting or parsing task, a `lolhtml.HTMLRewriter` is required:

Each HTML rewriter can be reused and is not tied to the content used for parsing (unless customization is made to the 
contrary). A CSS selector is required to specify which part of the content to target. For each CSS selector, an element
handler is required, which can process entries at an element, text chunk, or comment-level.

The following example strips all comments from the HTML payload:

```python
import lolhtml


class ElementHandler:
    def comments(self, comment: lolhtml.Comment):
        comment.remove()

rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
rewriter.on("*", ElementHandler())
rewriter.transform("<html><!-- Payload Goes Here --></html>")
```

A rewriter can contain encompass many element handlers. If no element handlers are provided, it effectively functions as
pass-through.

Element handlers are expected to implement one or more of these methods:
```python
import lolhtml

class ElementHandler:
    def element(self, el: lolhtml.Element): ...
    def comments(self, c: lolhtml.Comment): ...
    def text(self, t: lolhtml.TextChunk): ...
```

When lolhtml streams the content and encounters an element, comment, or text chunk matching a selector, it will execute
the appropriate method of the element handler.