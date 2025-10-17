import threading

import lolhtml


def test_tag_name():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            assert el.tag_name == "a"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_has_attribute():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            assert el.has_attribute("href")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_get_attribute():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            assert el.get_attribute("href") == "example"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_attributes():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            assert el.attributes == [("href", "example")]

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_removed():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            assert not el.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_remove():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.remove()
            assert el.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b""
    assert comment_processed.is_set()


def test_namespace_uri():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            # noinspection HttpUrlsUsage
            assert el.namespace_uri == "http://www.w3.org/1999/xhtml"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert comment_processed.is_set()


def test_set_attribute():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.set_attribute("data-test", "true")
            assert el.has_attribute("data-test")
            assert el.get_attribute("data-test") == "true"
            assert el.attributes == [("href", "example"), ("data-test", "true")]

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example" data-test="true">Link</a>'
    assert comment_processed.is_set()


def test_remove_attribute():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.remove_attribute("href")
            assert not el.has_attribute("href")
            assert el.get_attribute("data-test") is None
            assert el.attributes == []

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a[href]", ElementHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b"<a>Link</a>"
    assert comment_processed.is_set()


def test_prepend_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.prepend("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">&lt;Test&gt;Link</a></html>'
    assert comment_processed.is_set()


def test_prepend_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.prepend("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">&lt;Test&gt;Link</a></html>'
    assert comment_processed.is_set()


def test_prepend_html():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.prepend("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example"><Test>Link</a></html>'
    assert comment_processed.is_set()


def test_append_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.append("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link&lt;Test&gt;</a></html>'
    assert comment_processed.is_set()


def test_append_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.append("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link&lt;Test&gt;</a></html>'
    assert comment_processed.is_set()


def test_append_html():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.append("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link<Test></a></html>'
    assert comment_processed.is_set()


def test_before_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.before("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html>&lt;Test&gt;<a href="example">Link</a></html>'
    assert comment_processed.is_set()


def test_before_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.before("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html>&lt;Test&gt;<a href="example">Link</a></html>'
    assert comment_processed.is_set()


def test_before_html():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.before("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><Test><a href="example">Link</a></html>'
    assert comment_processed.is_set()


def test_after_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.after("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link</a>&lt;Test&gt;</html>'
    assert comment_processed.is_set()


def test_after_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.after("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link</a>&lt;Test&gt;</html>'
    assert comment_processed.is_set()


def test_after_html():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.after("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">Link</a><Test></html>'
    assert comment_processed.is_set()


def test_set_inner_content_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.set_inner_content("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">&lt;Test&gt;</a></html>'
    assert comment_processed.is_set()


def test_set_inner_content_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.set_inner_content("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example">&lt;Test&gt;</a></html>'
    assert comment_processed.is_set()


def test_set_inner_content_html():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.set_inner_content("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b'<html><a href="example"><Test></a></html>'
    assert comment_processed.is_set()


def test_remove_and_keep_content():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        def element(self, el: lolhtml.Element):
            comment_processed.set()
            el.remove_and_keep_content()

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("a", ElementHandler())

    rewriter.write(b'<html><a href="example">Link</a></html>')
    rewriter.end()

    assert output == b"<html>Link</html>"
    assert comment_processed.is_set()
