import lolhtml


def test_metadata():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            assert comment.text == " Hello World "
            assert not comment.removed

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("*", ElementHandler())

    rewriter.transform(b"<html><!-- Hello World --></html>")


def test_set_text():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.set_text("Set Comment")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html><!--Set Comment--></html>"


def test_remove():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.remove()
            assert comment.removed

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html></html>"


def test_before_text_inferred():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.before("<Test>")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html>&lt;Test&gt;<!-- Hello World --></html>"


def test_before_text_explicit():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.before("<Test>", text=True)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html>&lt;Test&gt;<!-- Hello World --></html>"


def test_before_html():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.before("<Test>", text=False)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html><Test><!-- Hello World --></html>"


def test_after_text_inferred():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.after("<Test>")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html><!-- Hello World -->&lt;Test&gt;</html>"


def test_after_text_explicit():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.after("<Test>", text=True)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html><!-- Hello World -->&lt;Test&gt;</html>"


def test_after_html():
    class ElementHandler:
        def comments(self, comment: lolhtml.Comment):
            comment.after("<Test>", text=False)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("html", ElementHandler())

    result = rewriter.transform(b"<html><!-- Hello World --></html>")
    assert result == b"<html><!-- Hello World --><Test></html>"
