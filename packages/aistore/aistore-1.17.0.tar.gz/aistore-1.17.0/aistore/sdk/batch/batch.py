#
# Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
#

import base64
from io import BytesIO
from typing import Generator, List, Tuple, Union, Optional
from urllib3.response import HTTPResponse

from aistore.sdk.batch.extractor.extractor_manager import ExtractorManager
from aistore.sdk.batch.multipart.multipart_decoder import MultipartDecoder
from aistore.sdk.batch.types import MossIn, MossOut, MossReq, MossResp
from aistore.sdk.bucket import Bucket
from aistore.sdk.const import (
    EXT_TAR,
    HEADER_CONTENT_TYPE,
    HTTP_METHOD_GET,
    JSON_CONTENT_TYPE,
    QPARAM_PROVIDER,
    URL_PATH_GB,
)
from aistore.sdk.obj.object import Object
from aistore.sdk.request_client import RequestClient
from aistore.sdk.utils import get_logger

_BUCKET_REQUIRED_MSG = "Bucket must be provided when objects are specified as raw names (str or list of str)"
logger = get_logger(__name__)

# Type alias for batch get results: generator yielding (metadata, content) pairs
BatchResult = Generator[Tuple[MossOut, bytes], None, None]


class Batch:
    """
    Batch (Get-Batch) API - Direct mapping to Go's MOSS (Multi-Object Streaming Service).

    Builds and executes Get-Batch requests to retrieve multiple objects, archived files,
    or byte ranges in a single efficient operation.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        request_client: RequestClient,
        objects: Optional[Union[List[Object], Object, str, List[str]]] = None,
        bucket: Optional[Bucket] = None,
        output_format: str = EXT_TAR,
        cont_on_err: bool = True,
        only_obj_name: bool = False,
        streaming_get: bool = True,
    ):
        """
        Initialize Batch request.

        Args:
            request_client (RequestClient): Client for making HTTP requests
            objects (Optional[Union[List[Object], Object, str, List[str]]]): Objects to retrieve. Can be:
                Note: if objects are specified as raw names (str or list of str), bucket must be provided
                - Single object name: "file.txt"
                - List of names: ["file1.txt", "file2.txt"]
                - Single Object instance
                - List of Object instances
                - None (add objects later via add())
                Note: if objects are specified as raw names (str or list of str), bucket must be provided
            bucket (Bucket): Default bucket for all objects
            output_format (str): Archive format (tar, tgz, zip)
            cont_on_err (bool): Continue on errors (missing files under __404__/). Defaults to True
            only_obj_name (bool): Use only obj name in archive path. Defaults to False
            streaming_get (bool): Stream resulting archive prior to finalizing it in memory. Defaults to True

        Example:
            # Quick batch with string names
            batch = client.batch(["file1.txt", "file2.txt"], bucket)

            # Or add later for complex requests
            batch = client.batch(bucket=bucket)
            batch.add("simple.txt")
            batch.add("shard.tar", archpath="images/photo.jpg")  # extract from archive
            batch.add("custom-format.txt", opaque=b"user-id-123")  # with tracking data

        """
        self.request_client = request_client
        self.bucket = bucket

        # Initialize MossReq
        self.request = MossReq(
            moss_in=[],
            output_format=output_format,
            cont_on_err=cont_on_err,
            only_obj_name=only_obj_name,
            streaming_get=streaming_get,
        )

        # Process initial objects if provided
        if objects is not None:
            self._add_objects(objects)

        self.extractor = ExtractorManager().get_extractor(output_format)

    def _add_objects(self, objects: Union[List[Object], Object, str, List[str]]):
        """
        Internal helper to add objects in bulk.
        Supports strings, Object instances, or lists of either.
        """
        if isinstance(objects, list):
            for obj in objects:
                if isinstance(obj, Object):
                    self.request.add(
                        MossIn(
                            obj_name=obj.name,
                            bck=obj.bucket_name,
                            provider=obj.bucket_provider.value,
                        )
                    )
                elif isinstance(obj, str):
                    if not self.bucket:
                        logger.error(
                            "Cannot add string object '%s': no bucket provided", obj
                        )
                        raise ValueError(_BUCKET_REQUIRED_MSG)
                    self.request.add(MossIn(obj_name=obj))
                else:
                    logger.error("Unsupported object type: %s", type(obj))
                    raise ValueError(f"Unsupported object type: {type(obj)}")
        elif isinstance(objects, Object):
            self.request.add(
                MossIn(
                    obj_name=objects.name,
                    bck=objects.bucket_name,
                    provider=objects.bucket_provider.value,
                )
            )
        elif isinstance(objects, str):
            if not self.bucket:
                logger.error(
                    "Cannot add string object '%s': no bucket provided", objects
                )
                raise ValueError(_BUCKET_REQUIRED_MSG)
            self.request.add(MossIn(obj_name=objects))

    def add(
        self,
        obj: Union[Object, str],
        opaque: Optional[bytes] = None,
        archpath: Optional[str] = None,
        start: Optional[int] = None,
        length: Optional[int] = None,
    ) -> "Batch":
        """
        Add object with advanced parameters (archpath, byte ranges, opaque data).

        For simple objects, prefer passing them to __init__ instead.

        Note: if objects are specified as raw names (str), default bucket must be provided in __init__

        Args:
            obj (Union[Object, str]): Object or object name string
            opaque (Optional[bytes]): User-provided binary identifier (returned unchanged)
            archpath (Optional[str]): Extract file from archive (e.g., "images/photo.jpg")
            start (Optional[int]): Byte range start offset
            length (Optional[int]): Byte range length

        Returns:
            Batch: Self for method chaining

        Example:
            batch = Batch(client, ["simple1.txt", "simple2.txt"])
            batch.add("shard.tar", archpath="data/file.json")  # Archive extraction
            batch.add("tracked.txt", opaque=b"user-id-123")  # With tracking data
        """
        # TODO: Implement byte range support on server-side
        if start or length:
            logger.warning(
                "Byte range request not yet supported: start=%s, length=%s",
                start,
                length,
            )
            raise NotImplementedError("Batch byte range support is not yet implemented")

        # Build MossIn
        if isinstance(obj, Object):
            moss_in = MossIn(
                obj_name=obj.name,
                bck=obj.bucket_name,
                provider=obj.bucket_provider.value,
            )
        else:
            if not self.bucket:
                logger.error("Cannot add string object '%s': no bucket provided", obj)
                raise ValueError(_BUCKET_REQUIRED_MSG)
            moss_in = MossIn(obj_name=obj)

        # Add optional parameters
        if opaque:
            moss_in.opaque = base64.urlsafe_b64encode(opaque).decode("utf-8")
        if archpath:
            moss_in.archpath = archpath
        if start:
            moss_in.start = start
        if length:
            moss_in.length = length

        self.request.add(moss_in)
        return self  # Allow chaining

    def get(
        self,
        raw: bool = False,
        decode_as_stream: bool = False,
    ) -> Union[BatchResult, HTTPResponse]:
        """
        Execute the Get-Batch request.

        Args:
            raw (bool): Return raw HTTP response stream. User must close the stream
            decode_as_stream (bool): Stream multipart decoding (memory efficient)

        Returns:
            Union[BatchResult, HTTPResponse]:
                - If raw=True: HTTPResponse object (caller must close)
                - If raw=False: Generator yielding (MossOut, file_content) tuples

        Raises:
            ValueError: If no objects added to batch
        """
        if not self.request.moss_in:
            logger.error("Cannot execute batch: no objects added")
            raise ValueError("No objects added to batch")

        logger.debug(
            "Executing batch get: objects=%d, format=%s, streaming=%s, raw=%s",
            len(self.request.moss_in),
            self.request.output_format,
            self.request.streaming_get,
            raw,
        )

        # Build request
        url_path = URL_PATH_GB
        params = {}

        if self.bucket:
            url_path = f"{URL_PATH_GB}/{self.bucket.name}"
            params[QPARAM_PROVIDER] = self.bucket.provider.value

        # Execute HTTP request
        response = self.request_client.request(
            method=HTTP_METHOD_GET,
            path=url_path,
            params=params,
            headers={HEADER_CONTENT_TYPE: JSON_CONTENT_TYPE},
            stream=True,
            json=self.request.dict(),
        )

        if raw:
            # Returns raw batch stream, user must close
            return response.raw

        # TODO: Handle error response, create customized errors
        if self.request.streaming_get:
            return self._extract_streaming(response)
        return self._extract_multipart(response, decode_as_stream)

    def _extract_streaming(self, response) -> BatchResult:
        """
        Extract from streaming response (no metadata).
        Infer MossOut from request data.

        Args:
            response (Response): HTTP response object

        Returns:
            BatchResult: Generator yielding (MossOut, content) tuples
        """

        return self.extractor.extract(response, response.raw, self.request, None)

    # TODO: revisit
    def _extract_multipart(self, response, decode_as_stream: bool) -> BatchResult:
        """
        Extract from multipart response (with metadata).
        Returns actual MossOut with size, errors, etc.

        Args:
            response (Response): HTTP response object
            decode_as_stream (bool): Whether to decode multipart as stream

        Returns:
            BatchResult: Generator yielding (MossOut, content) tuples
        """
        try:
            # Decode multipart
            decoder = MultipartDecoder(parse_as_stream=decode_as_stream)
            parts_iter = decoder.decode(response)

            # Part 1: Deserialize MossResp metadata
            if decode_as_stream:
                metadata_body = next(parts_iter)[1].read()
            else:
                metadata_body = next(parts_iter)[1]
            moss_resp = MossResp.parse_raw(metadata_body.decode(decoder.encoding))

            # Part 2: Archive data stream
            if decode_as_stream:
                data_stream = next(parts_iter)[1]
            else:
                data_stream = BytesIO(next(parts_iter)[1])

            # Extract archive and pair with metadata
            return self.extractor.extract(
                response, data_stream, self.request, moss_resp
            )

        except Exception as e:
            logger.error(
                "Failed to decode multipart batch response: %s", str(e), exc_info=True
            )
            response.close()
            raise

    def __len__(self) -> int:
        """
        Number of objects in batch.

        Returns:
            int: Number of objects in the batch
        """
        return len(self.request.moss_in)

    def __repr__(self) -> str:
        """
        String representation of the Batch object.

        Returns:
            str: String representation showing number of objects and format
        """
        return f"Batch(objects={len(self)}, format={self.request.output_format})"
