import gzip

try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

import brotli
# from zopfli import gzip as zopfli
from django.core.files.base import ContentFile

__all__ = ["BrotliCompressor", "ZlibCompressor"]  # , "ZopfliCompressor"


class BrotliCompressor:
    extension = "br"

    def compress(self, path, file):
        return ContentFile(brotli.compress(file.read()))


class ZlibCompressor:
    extension = "gz"

    def compress(self, path, file):
        output = BytesIO()
        # Explicitly set mtime to 0 so gzip content is fully determined
        # by file content (0 = "no timestamp" according to gzip spec)
        with gzip.GzipFile(filename='', mode='wb', fileobj=output,
                           compresslevel=9, mtime=0) as gz_file:
            gz_file.write(file.read())
        return ContentFile(output.getvalue())


# class ZopfliCompressor:
#     extension = "gz"

#     def compress(self, path, file):
#         return ContentFile(zopfli.compress(file.read()))
