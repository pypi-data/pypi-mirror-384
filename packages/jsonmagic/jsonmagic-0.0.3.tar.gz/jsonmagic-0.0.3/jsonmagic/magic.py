from IPython import get_ipython
from IPython.core.magic import register_line_magic


class _view:
    def __init__(self, data):
        self.data = data

    def _repr_json_(self):
        return self.data


def view_json(data):
    """Show JSON-like data in JupyterLab rich display"""
    return _view(data)


def load_ipython_extension(ipython):
    """This function is called automatically by `%load_ext"""

    @register_line_magic
    def json(line):
        """
        A line magic that triggers the JupyterLab rich display for the
        JSON MIME type on the given data.
        """

        ip = get_ipython()
        try:
            obj = ip.ev(line)
        except:
            return "%json magic reported: Could not interpret given object"

        return _view(obj)
