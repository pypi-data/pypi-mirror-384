from unittest.mock import MagicMock


class S3BotoResource(MagicMock):
    class Bucket:
        def __init__(self, name):
            self.name = name
