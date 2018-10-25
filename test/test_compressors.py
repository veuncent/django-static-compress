import unittest
import gzip
import zlib
from io import BytesIO

from static_compress.compressors import BrotliCompressor, ZopfliCompressor, ZlibCompressor
import brotli

content = b"a" * 100


class ZopfliCompressorTestCase(unittest.TestCase):
    def test_compress(self):
        file = BytesIO(content)

        compressor = ZopfliCompressor()
        out = compressor.compress("", file)
        self.assertGreater(out.size, 0)
        self.assertLessEqual(out.size, len(content))

        result = gzip.decompress(out.read())
        self.assertEqual(result, content)


class BrotliCompressorTestCase(unittest.TestCase):
    def test_compress(self):
        file = BytesIO(content)

        compressor = BrotliCompressor()
        out = compressor.compress("", file)
        self.assertGreater(out.size, 0)
        self.assertLessEqual(out.size, len(content))

        result = brotli.decompress(out.read())
        self.assertEqual(result, content)


class ZlibCompressorTestCase(unittest.TestCase):
    def test_compress(self):
        file = BytesIO(content)

        compressor = ZlibCompressor()
        out = compressor.compress("", file)
        self.assertGreater(out.size, 0)
        self.assertLessEqual(out.size, len(content))

        result = gzip.zlib.decompress(out.read())
        self.assertEqual(result, content)
