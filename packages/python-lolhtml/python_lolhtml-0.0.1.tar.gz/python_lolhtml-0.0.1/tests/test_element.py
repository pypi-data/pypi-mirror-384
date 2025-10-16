import lolhtml


def test_metadata():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            assert el.tag_name == "a"
            assert el.has_attribute("href")
            assert el.get_attribute("href") == "example"
            assert el.attributes == {"href": "example"}

            assert not el.removed

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a[href]", ElementHandler())

    rewriter.transform(b'<a href="example">Link</a>')


def test_set_attribute():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.set_attribute("href", "something-else")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a[href]", ElementHandler())

    result = rewriter.transform(b'<a href="example">Link</a>')
    assert result == b'<a href="something-else">Link</a>'


def test_remove_attribute():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.remove_attribute("href")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a[href]", ElementHandler())

    result = rewriter.transform(b'<a href="example">Link</a>')
    assert result == b"<a>Link</a>"


def test_before_text_inferred():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.before("<Test>")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"&lt;Test&gt;<a>Link</a>"


def test_before_text_explicit():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.before("<Test>", text=True)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"&lt;Test&gt;<a>Link</a>"


def test_before_html():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.before("<Test>", text=False)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"<Test><a>Link</a>"


def test_after_text_inferred():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.after("<Test>")

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"<a>Link</a>&lt;Test&gt;"


def test_after_text_explicit():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.after("<Test>", text=True)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"<a>Link</a>&lt;Test&gt;"


def test_after_html():
    class ElementHandler:
        def element(self, el: lolhtml.Element):
            if el.tag_name != "a":
                return

            el.after("<Test>", text=False)

    rewriter: lolhtml.HTMLRewriter = lolhtml.HTMLRewriter()
    rewriter.on("a", ElementHandler())

    result = rewriter.transform(b"<a>Link</a>")
    assert result == b"<a>Link</a><Test>"
