import threading

import lolhtml


def test_name():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def doctype(self, el: lolhtml.Doctype):
            comment_processed.set()
            assert el.name == "html"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b'<!DOCTYPE html><a href="example">Link</a>')
    rewriter.end()

    assert output == b'<!DOCTYPE html><a href="example">Link</a>'
    assert comment_processed.is_set()


def test_full():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def doctype(self, el: lolhtml.Doctype):
            comment_processed.set()
            assert el.name == "html"
            assert el.public_id == "-//W3C//DTD HTML 4.01 Transitional//EN"
            # noinspection HttpUrlsUsage
            assert el.system_id == "http://www.w3.org/TR/html4/loose.dtd"

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    # noinspection HttpUrlsUsage
    rewriter.write(b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" '
                   b'"http://www.w3.org/TR/html4/loose.dtd"><a href="example">Link</a>')
    rewriter.end()

    # noinspection HttpUrlsUsage
    assert output == (b'<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" '
                      b'"http://www.w3.org/TR/html4/loose.dtd"><a href="example">Link</a>')
    assert comment_processed.is_set()


def test_blank_doctype():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def doctype(self, el: lolhtml.Doctype):
            comment_processed.set()
            assert el.name is None
            assert el.system_id is None
            assert el.public_id is None

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b'<!DOCTYPE><a href="example">Link</a>')
    rewriter.end()

    assert output == b'<!DOCTYPE><a href="example">Link</a>'
    assert comment_processed.is_set()


def test_nonexistent_doctype():
    comment_processed: threading.Event = threading.Event()

    class DocumentHandler:
        def doctype(self, el: lolhtml.Doctype):
            comment_processed.set()
            assert el.name is None
            assert el.public_id is None
            assert el.system_id is None

    output: bytearray = bytearray()
    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter(output.extend)
    rewriter.on_document(DocumentHandler())

    rewriter.write(b'<a href="example">Link</a>')
    rewriter.end()

    assert output == b'<a href="example">Link</a>'
    assert not comment_processed.is_set()
