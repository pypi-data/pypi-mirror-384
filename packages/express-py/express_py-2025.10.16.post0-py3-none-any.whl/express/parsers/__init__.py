import os

from express.mixins import RoundNumericValuesMixin


class BaseParser(RoundNumericValuesMixin):
    """
    Base Parser class.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.version = kwargs.get("version", None)

    def _get_file_content(self, file_path):
        """
        Returns the content of a given file.

        Args:
            file_path (str): file path.

        Returns:
             str
        """
        content = ""
        if file_path and os.path.exists(file_path):
            with open(file_path) as f:
                content = f.read()
        return content
