"""Read config, either from command line argument or from resources."""
import importlib.resources
from importlib.abc import Traversable
from pymscada_html import html


def get_html_file(filename: str) -> Traversable:
    """Provide file resources to package."""
    fn = importlib.resources.files(html).joinpath(filename)
    if fn.is_file():
        return fn
    else:
        raise FileNotFoundError(filename)
