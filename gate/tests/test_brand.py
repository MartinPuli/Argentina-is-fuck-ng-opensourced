"""Brand macros render through the app's own Jinja environment."""

from gate.app import templates


def test_brand_macros_render():
    brand = templates.env.get_template("brand.html").module
    for variant in ("light", "dark"):
        mark = str(brand.logo(16, variant))
        assert 'role="img"' in mark and 'aria-label="ArgenSec"' in mark
        word = str(brand.wordmark(20, variant))
        assert "Argen" in word and "Sec" in word and "<svg" in word
    assert 3 <= len(str(brand.tagline()).split()) <= 6
    favicon = str(brand.favicon_link())
    assert favicon.startswith('<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg')
    assert "#" not in favicon.split("href=")[1]
