from devilry.devilry_compressionutil.backends.backends_base import PythonZipFileBackend


class MockDevilryZipBackend(PythonZipFileBackend):
    """
    Used for testing.
    """
    backend_id = 'default'

    def __init__(self, **kwargs):
        super(MockDevilryZipBackend, self).__init__(**kwargs)


class MockDevilryZipBackendS3(MockDevilryZipBackend):
    """

    """
    backend_id = 's3'
    storage_location = 'url/to/s3/filestorage'

    def __init__(self, **kwargs):
        super(MockDevilryZipBackendS3, self).__init__(**kwargs)


class MockDevilryZipBackendHeroku(MockDevilryZipBackend):
    """

    """
    backend_id = 'heroku'
    storage_location = 'url/to/heroku/filestorage'

    def __init__(self, **kwargs):
        super(MockDevilryZipBackendHeroku, self).__init__(**kwargs)
