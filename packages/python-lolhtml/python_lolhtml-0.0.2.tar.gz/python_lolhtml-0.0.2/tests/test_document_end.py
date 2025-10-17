import threading

import lolhtml


def test_append_text_inferred():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def end(self, e: lolhtml.DocumentEnd):
            assert not comment_processed.is_set()
            comment_processed.set()
            e.append("<Test>")

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --></html>&lt;Test&gt;"
    assert comment_processed.is_set()


def test_append_text_explicit():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def end(self, e: lolhtml.DocumentEnd):
            assert not comment_processed.is_set()
            comment_processed.set()
            e.append("<Test>", lolhtml.ContentType.TEXT)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --></html>&lt;Test&gt;"
    assert comment_processed.is_set()


def test_append_html():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def end(self, e: lolhtml.DocumentEnd):
            assert not comment_processed.is_set()
            comment_processed.set()
            e.append("<Test>", lolhtml.ContentType.HTML)

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b"<html><!-- Hello World --></html>")
    rewriter.end()

    assert output == b"<html><!-- Hello World --></html><Test>"
    assert comment_processed.is_set()
