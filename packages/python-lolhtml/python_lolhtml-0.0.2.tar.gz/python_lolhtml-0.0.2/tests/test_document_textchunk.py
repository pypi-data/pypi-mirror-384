import threading
from typing import List

import lolhtml


def test_text():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if not t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            assert t.text == " Hello World "

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World </html>"
    assert comment_processed.is_set()


def test_removed():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            comment_processed.set()
            assert not t.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World </html>"
    assert comment_processed.is_set()


def test_remove():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            comment_processed.set()
            assert not t.removed
            t.remove()
            assert t.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html></html>"
    assert comment_processed.is_set()


def test_last_in_text_node():
    comment_processed: threading.Event = threading.Event()
    last_counter: List[int] = [0]

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            comment_processed.set()
            if t.last_in_text_node:
                last_counter[0] += 1

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World </html>"
    assert last_counter[0] == 1
    assert comment_processed.is_set()


def test_replace_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.replace("<Howdy>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html>&lt;Howdy&gt;</html>"
    assert comment_processed.is_set()


def test_replace_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.replace("<Howdy>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html>&lt;Howdy&gt;</html>"
    assert comment_processed.is_set()


def test_replace_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.replace("<Howdy>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html><Howdy></html>"
    assert comment_processed.is_set()


def test_before_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.before("<Howdy>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html>&lt;Howdy&gt; Hello World </html>"
    assert comment_processed.is_set()


def test_before_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.before("<Howdy>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html>&lt;Howdy&gt; Hello World </html>"
    assert comment_processed.is_set()


def test_before_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.before("<Howdy>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html><Howdy> Hello World </html>"
    assert comment_processed.is_set()


def test_after_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.after("<Howdy>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World &lt;Howdy&gt;</html>"
    assert comment_processed.is_set()


def test_after_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.after("<Howdy>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World &lt;Howdy&gt;</html>"
    assert comment_processed.is_set()


def test_after_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def text(self, t: lolhtml.TextChunk):
            if " Hello World " not in t.text:
                return

            assert not comment_processed.is_set()
            comment_processed.set()
            t.after("<Howdy>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html> Hello World </html>")
    rewriter.end()

    assert output == b"<html> Hello World <Howdy></html>"
    assert comment_processed.is_set()
