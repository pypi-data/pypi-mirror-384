"""Test reading of html files."""
import pymscada_html


def test_read():
    """Test file read."""
    fh = pymscada_html.get_html_file('favicon.ico')
    assert fh.name == 'favicon.ico'


def test_html_file():
    """Read bus config."""
    fn = pymscada_html.get_html_file('robots.txt')
    with open(fn, 'r') as fh:
        assert fh.readline().strip() == 'User-agent: *'
        assert fh.readline().strip() == 'Disallow: /'
