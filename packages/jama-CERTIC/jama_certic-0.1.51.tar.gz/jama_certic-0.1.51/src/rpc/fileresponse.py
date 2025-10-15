from django.http.response import StreamingHttpResponse
import os
import mimetypes
from urllib.parse import quote


class FileResponse(StreamingHttpResponse):
    """
    A streaming HTTP response class optimized for files.
    """

    block_size = 4096

    def __init__(self, *args, as_attachment=False, filename="", **kwargs):
        self.as_attachment = as_attachment
        self.filename = filename
        super().__init__(*args, **kwargs)

    def _set_streaming_content(self, value):
        if self.filename:
            self.headers["Content-Disposition"] = "attachment;filename={}".format(
                self.filename
            )
        if not hasattr(value, "read"):
            self.file_to_stream = None
            return super()._set_streaming_content(value)
        self.file_to_stream = filelike = value
        if hasattr(filelike, "close"):
            self._resource_closers.append(filelike.close)
        value = iter(lambda: filelike.read(self.block_size), b"")
        self.set_headers(filelike)
        super()._set_streaming_content(value)

    def set_headers(self, filelike):
        """
        Set some common response headers (Content-Length, Content-Type, and
        Content-Disposition) based on the `filelike` response content.
        """
        encoding_map = {
            "bzip2": "application/x-bzip",
            "gzip": "application/gzip",
            "xz": "application/x-xz",
        }
        # filename = getattr(filelike, 'name', None)
        # filename = filename if (isinstance(filename, str) and filename) else self.filename
        # filename = self.filename if self.filename else filename
        filename = self.filename
        if os.path.isabs(filename):
            self.headers["Content-Length"] = os.path.getsize(filelike.name)
        elif hasattr(filelike, "getbuffer"):
            self.headers["Content-Length"] = filelike.getbuffer().nbytes

        if self.headers.get("Content-Type", "").startswith("text/html"):
            if filename:
                content_type, encoding = mimetypes.guess_type(filename)
                # Encoding isn't set to prevent browsers from automatically
                # uncompressing files.
                content_type = encoding_map.get(encoding, content_type)
                self.headers["Content-Type"] = (
                    content_type or "application/octet-stream"
                )
            else:
                self.headers["Content-Type"] = "application/octet-stream"

        filename = self.filename or os.path.basename(filename)
        if filename:
            disposition = "attachment" if self.as_attachment else "inline"
            try:
                filename.encode("ascii")
                file_expr = 'filename="{}"'.format(filename)
            except UnicodeEncodeError:
                file_expr = "filename*=utf-8''{}".format(quote(filename))
            self.headers["Content-Disposition"] = "{}; {}".format(
                disposition, file_expr
            )
        elif self.as_attachment:
            self.headers["Content-Disposition"] = "attachment"


class RangedFileReader(object):
    """
    Wraps a file like object with an iterator that runs over part (or all) of
    the file defined by start and stop. Blocks of block_size will be returned
    from the starting position, up to, but not including the stop point.
    """

    block_size = 8192

    def __init__(self, file_like, start=0, stop=float("inf"), block_size=None):
        """
        Args:
            file_like (File): A file-like object.
            start (int): Where to start reading the file.
            stop (Optional[int]:float): Where to end reading the file.
                Defaults to infinity.
            block_size (Optional[int]): The block_size to read with.
        """
        self.f = file_like
        self.size = len(self.f.read())
        self.block_size = block_size or RangedFileReader.block_size
        self.start = start
        self.stop = stop

    def __iter__(self):
        """
        Reads the data in chunks.
        """
        self.f.seek(self.start)
        position = self.start
        while position < self.stop:
            data = self.f.read(min(self.block_size, self.stop - position))
            if not data:
                break

            yield data
            position += self.block_size

    def parse_range_header(self, header, resource_size):
        """
        Parses a range header into a list of two-tuples (start, stop) where
        `start` is the starting byte of the range (inclusive) and
        `stop` is the ending byte position of the range (exclusive).

        Args:
            header (str): The HTTP_RANGE request header.
            resource_size (int): The size of the file in bytes.

        Returns:
            None if the value of the header is not syntatically valid.
        """
        if not header or "=" not in header:
            return None

        ranges = []
        units, range_ = header.split("=", 1)
        units = units.strip().lower()

        if units != "bytes":
            return None

        for val in range_.split(","):
            val = val.strip()
            if "-" not in val:
                return None

            if val.startswith("-"):
                # suffix-byte-range-spec: this form specifies the last N bytes
                # of an entity-body.
                start = resource_size + int(val)
                if start < 0:
                    start = 0
                stop = resource_size
            else:
                # byte-range-spec: first-byte-pos "-" [last-byte-pos].
                start, stop = val.split("-", 1)
                start = int(start)
                # The +1 is here since we want the stopping point to be
                # exclusive, whereas in the HTTP spec, the last-byte-pos
                # is inclusive.
                stop = int(stop) + 1 if stop else resource_size
                if start >= stop:
                    return None

            ranges.append((start, stop))

        return ranges


class RangedFileResponse(FileResponse):
    """
    This is a modified FileResponse that returns `Content-Range` headers with
    the response, so browsers that request the file, can stream the response
    properly.
    """

    def __init__(self, request, file, *args, **kwargs):
        """
        RangedFileResponse constructor also requires a request, which
        checks whether range headers should be added to the response.

        Args:
            request(WGSIRequest): The Django request object.
            file (File): A file-like object.
        """
        self.ranged_file = RangedFileReader(file)
        super(RangedFileResponse, self).__init__(self.ranged_file, *args, **kwargs)

        if "HTTP_RANGE" in request.META:
            self.add_range_headers(request.META["HTTP_RANGE"])

    def add_range_headers(self, range_header):
        """
        Adds several headers that are necessary for a streaming file
        response, in order for Safari to play audio files. Also
        sets the HTTP status_code to 206 (partial content).

        Args:
            range_header (str): Browser HTTP_RANGE request header.
        """
        self["Accept-Ranges"] = "bytes"
        size = self.ranged_file.size
        try:
            ranges = self.ranged_file.parse_range_header(range_header, size)
        except ValueError:
            ranges = None
        # Only handle syntactically valid headers, that are simple (no
        # multipart byteranges).
        if ranges is not None and len(ranges) == 1:
            start, stop = ranges[0]
            if start >= size:
                # Requested range not satisfiable.
                self.status_code = 416
                return

            if stop >= size:
                stop = size

            self.ranged_file.start = start
            self.ranged_file.stop = stop
            self["Content-Range"] = "bytes %d-%d/%d" % (start, stop - 1, size)
            self["Content-Length"] = stop - start
            self.status_code = 206
