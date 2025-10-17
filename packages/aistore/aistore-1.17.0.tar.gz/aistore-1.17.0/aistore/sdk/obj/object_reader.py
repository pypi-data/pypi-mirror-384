#
# Copyright (c) 2024-2025, NVIDIA CORPORATION. All rights reserved.
#

from io import BufferedIOBase
from typing import Optional, Generator

import requests

from aistore.sdk.obj.content_iter_provider import ContentIterProvider
from aistore.sdk.obj.object_client import ObjectClient
from aistore.sdk.obj.obj_file.object_file import ObjectFileReader
from aistore.sdk.const import DEFAULT_CHUNK_SIZE
from aistore.sdk.obj.object_attributes import ObjectAttributes


class ObjectReader:
    """
    Provide a way to read an object's contents and attributes, optionally iterating over a stream of content.

    Args:
        object_client (ObjectClient): Client for making requests to a specific object in AIS
        chunk_size (int, optional): Size of each data chunk to be fetched from the stream.
            Defaults to DEFAULT_CHUNK_SIZE.
    """

    def __init__(
        self, object_client: ObjectClient, chunk_size: int = DEFAULT_CHUNK_SIZE
    ):
        self._object_client = object_client
        self._chunk_size = chunk_size
        self._content_provider = ContentIterProvider(
            self._object_client, self._chunk_size
        )
        self._attributes = None

    def head(self) -> ObjectAttributes:
        """
        Make a head request to AIS to update and return only object attributes.

        Returns:
            `ObjectAttributes` containing metadata for this object.
        """
        self._attributes = self._object_client.head()
        return self._attributes

    def _make_request(self, stream: bool = True) -> requests.Response:
        """
        Use the object client to get a response from AIS and update the reader's object attributes.

        Args:
            stream (bool, optional): If True, use the `requests` library `stream` option to stream the response content.
                                     Defaults to True.

        Returns:
            The response object from the request.
        """
        resp = self._object_client.get(stream=stream)
        self._attributes = ObjectAttributes(resp.headers)
        return resp

    @property
    def attributes(self) -> ObjectAttributes:
        """
        Object metadata attributes.

        Returns:
            ObjectAttributes: Parsed object attributes from the headers returned by AIS.
        """
        if not self._attributes:
            self._attributes = self.head()
        return self._attributes

    def read_all(self) -> bytes:
        """
        Read all byte data directly from the object response without using a stream.

        This requires all object content to fit in memory at once and downloads all content before returning.

        Returns:
            bytes: Object content as bytes.
        """
        return self._make_request(stream=False).content

    def raw(self) -> requests.Response:
        """
        Return the raw byte stream of object content.

        Returns:
            requests.Response: Raw byte stream of the object content.
        """
        return self._make_request(stream=True).raw

    # pylint: disable=unused-argument
    def as_file(
        self,
        buffer_size: Optional[int] = None,
        max_resume: Optional[int] = 5,
    ) -> BufferedIOBase:
        """
        Create a read-only, non-seekable `ObjectFileReader` instance for streaming object data in chunks.
        This file-like object primarily implements the `read()` method to retrieve data sequentially,
        with automatic retry/resumption in case of unexpected stream interruptions (e.g. `ChunkedEncodingError`,
        `ConnectionError`) or timeouts (e.g. `ReadTimeout`).

        Args:
            buffer_size (int, optional): Currently unused; retained for backward compatibility and future
                                         enhancements.
            max_resume (int, optional): Total number of retry attempts allowed to resume the stream in case of
                                        interruptions. Defaults to 5.

        Returns:
            BufferedIOBase: A read-only, non-seekable file-like object for streaming object content.

        Raises:
            ValueError: If `max_resume` is invalid (must be a non-negative integer).
        """
        if max_resume < 0:
            raise ValueError(
                f"Invalid max_resume (must be a non-negative integer): {max_resume}."
            )

        return ObjectFileReader(self._content_provider, max_resume=max_resume)

    def __iter__(self) -> Generator[bytes, None, None]:
        """
        Make a request to get a stream from the provided object and yield chunks of the stream content.

        Returns:
            Generator[bytes, None, None]: An iterator over each chunk of bytes in the object.
        """
        return self._content_provider.create_iter()
