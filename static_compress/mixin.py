import os
from os.path import getatime, getctime, getmtime
import errno

from django.core.exceptions import ImproperlyConfigured

from . import compressors

import logging

logger = logging.getLogger(__name__)


__all__ = ["CompressMixin"]


DEFAULT_METHODS = ["gz+zlib", "br"]
METHOD_MAPPING = {
    # "gz": compressors.ZopfliCompressor,
    "br": compressors.BrotliCompressor,
    "gz+zlib": compressors.ZlibCompressor,
    # gz+zlib and gz cannot be used at the same time, because they produce the same file extension.
}


class CompressMixin(object):
    allowed_extensions = []
    compress_methods = []
    keep_original = True
    compressors = []
    minimum_kb = 0

    def __init__(self, *args, **kwargs):
        super(CompressMixin, self).__init__(*args, **kwargs)
        # We access Django settings lately here, to allow our app to be imported without
        # defining DJANGO_SETTINGS_MODULE.
        from django.conf import settings

        self.allowed_extensions = getattr(settings, "STATIC_COMPRESS_FILE_EXTS", ["js", "css", "svg", "html", "txt", "xml"])
        self.compress_methods = getattr(settings, "STATIC_COMPRESS_METHODS", DEFAULT_METHODS)
        self.keep_original = getattr(settings, "STATIC_COMPRESS_KEEP_ORIGINAL", True)
        self.minimum_kb = getattr(settings, "STATIC_COMPRESS_MIN_SIZE_KB", 30)

        logger.info("Using compress methods: [{0}]".format(', '.join(str(cm) for cm in self.compress_methods)))

        valid = [i for i in self.compress_methods if i in METHOD_MAPPING]
        if not valid:
            raise ImproperlyConfigured("No valid method is defined in STATIC_COMPRESS_METHODS setting.")
        if "gz" in valid and "gz+zlib" in valid:
            raise ImproperlyConfigured("STATIC_COMPRESS_METHODS: gz and gz+zlib cannot be used at the same time.")
        self.compressors = [METHOD_MAPPING[k]() for k in valid]
        
        logger.info("Using compressors: [{0}]".format(', '.join(str(c.__name__) for c in self.compressors)))

    def get_alternate_compressed_path(self, name):
        for compressor in self.compressors:
            ext = compressor.extension
            if name.endswith(".{}".format(ext)):
                path = self.path(name)
            else:
                path = self.path("{}.{}".format(name, ext))
            if os.path.exists(path):
                return path
        raise OSError(errno.ENOENT, os.strerror(errno.ENOENT), path)

    def get_accessed_time(self, name):
        if self.keep_original:
            return super(CompressMixin, self).get_accessed_time(name)
        return self._datetime_from_timestamp(getatime(self.get_alternate_compressed_path(name)))

    def get_created_time(self, name):
        if self.keep_original:
            return super(CompressMixin, self).get_created_time(name)
        return self._datetime_from_timestamp(getctime(self.get_alternate_compressed_path(name)))

    def get_modified_time(self, name):
        if self.keep_original:
            return super(CompressMixin, self).get_modified_time(name)
        alt = self.get_alternate_compressed_path(name)
        return self._datetime_from_timestamp(getmtime(alt))

    def post_process(self, paths, dry_run=False, **options):
        logger.info("Post-processing {0} static files...".format(len(paths)))
        if hasattr(super(CompressMixin, self), "post_process"):
            for sup in super(CompressMixin, self).post_process(paths, dry_run, **options):
                yield sup

        if dry_run:
            return

        for name in paths.keys():
            if not self._is_file_allowed(name):
                continue

            source_storage, path = paths[name]
            # Process if file is big enough
            if os.path.getsize(self.path(path)) < self.minimum_kb * 1024:
                continue
            src_mtime = source_storage.get_modified_time(path)
            dest_path = self._get_dest_path(path)
            with self._open(dest_path) as file:
                for compressor in self.compressors:
                    dest_compressor_path = "{}.{}".format(dest_path, compressor.extension)
                    # Check if the original file has been changed.
                    # If not, no need to compress again.
                    full_compressed_path = self.path(dest_compressor_path)
                    try:
                        dest_mtime = self._datetime_from_timestamp(getmtime(full_compressed_path))
                        file_is_unmodified = dest_mtime.replace(microsecond=0) >= src_mtime.replace(microsecond=0)
                    except OSError:
                        file_is_unmodified = False
                    if file_is_unmodified:
                        continue

                    # Delete old gzip file, or Nginx will pick the old file to serve.
                    # Note: Django won't overwrite the file, so we have to delete it ourselves.
                    if self.exists(dest_compressor_path):
                        self.delete(dest_compressor_path)
                    out = compressor.compress(path, file)

                    if out:
                        logger.info("Saving compressed output to: {0}".format(dest_compressor_path))
                        self._save(dest_compressor_path, out)
                        if not self.keep_original:
                            self.delete(name)
                        yield dest_path, dest_compressor_path, True
                    else:
                        raise IOError("Failed to produce output in compressor: {0}".format(compressor))

                    file.seek(0)

    def _get_dest_path(self, path):
        if hasattr(self, "hashed_name"):
            return self.hashed_name(path)

        return path

    def _is_file_allowed(self, file):
        for extension in self.allowed_extensions:
            if file.endswith("." + extension):
                return True
        return False
