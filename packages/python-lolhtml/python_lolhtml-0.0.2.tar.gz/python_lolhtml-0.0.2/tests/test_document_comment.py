import threading

import lolhtml


def test_text():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            assert comment.text == " Hello World "

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())
    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --></html>"
    assert comment_processed.is_set()


def test_removed():
    comment_processed: threading.Event = threading.Event()

    class ElementHandler:
        # noinspection PyMethodMayBeStatic
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            assert not comment.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on("*", ElementHandler())
    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --></html>"
    assert comment_processed.is_set()


def test_set_text():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.text = "Set Comment"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!--Set Comment--></html>"
    assert comment_processed.is_set()


def test_remove():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        # noinspection PyMethodMayBeStatic
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.remove()
            assert comment.removed

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html></html>"
    assert comment_processed.is_set()


def test_before_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.before("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html>&lt;Test&gt;<!-- Hello World --></html>"
    assert comment_processed.is_set()


def test_before_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.before("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html>&lt;Test&gt;<!-- Hello World --></html>"
    assert comment_processed.is_set()


def test_before_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.before("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><Test><!-- Hello World --></html>"
    assert comment_processed.is_set()


def test_after_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.after("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World -->&lt;Test&gt;</html>"
    assert comment_processed.is_set()


def test_after_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.after("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World -->&lt;Test&gt;</html>"
    assert comment_processed.is_set()


def test_after_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def comments(self, comment: lolhtml.Comment):
            assert not comment_processed.is_set()
            comment_processed.set()
            comment.after("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --><Test></html>"
    assert comment_processed.is_set()
