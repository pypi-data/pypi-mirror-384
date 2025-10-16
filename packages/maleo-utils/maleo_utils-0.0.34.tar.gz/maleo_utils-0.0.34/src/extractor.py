import traceback
from io import BytesIO
from fastapi import Response
from fastapi.responses import StreamingResponse
from typing import Tuple


class ResponseBodyExtractor:
    @staticmethod
    async def async_extract(
        response: Response, *, raise_exc: bool = False
    ) -> Tuple[bytes, Response]:
        """
        Extract body from a (possibly streaming) Response.
        Always returns a tuple of (raw_bytes, new_response).
        """
        response_body: bytes = b""

        if hasattr(response, "body_iterator"):  # StreamingResponse
            body_buffer = BytesIO()

            try:
                async for chunk in response.body_iterator:  # type: ignore
                    if isinstance(chunk, str):
                        body_buffer.write(chunk.encode("utf-8"))
                    elif isinstance(chunk, (bytes, memoryview)):
                        body_buffer.write(bytes(chunk))
                    else:
                        body_buffer.write(str(chunk).encode("utf-8"))

                response_body = body_buffer.getvalue()

                new_response = StreamingResponse(
                    iter([response_body]),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                    background=response.background,  # preserve background tasks
                )

            except Exception as e:
                if raise_exc:
                    raise
                print(f"Error consuming body iterator: {e}\n{traceback.format_exc()}")
                new_response = Response(
                    content=b"",
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        else:  # Normal Response
            try:
                response_body = getattr(response, "body", b"") or b""
            except Exception as e:
                if raise_exc:
                    raise
                print(f"Failed retrieving response body: {e}\n{traceback.format_exc()}")
                response_body = b""

            # No reconstruction needed
            new_response = response

        return response_body, new_response

    @staticmethod
    def sync_extract(
        response: Response, *, raise_exc: bool = False
    ) -> Tuple[bytes, Response]:
        """
        Extract body for non-streaming responses in sync code.
        """
        if hasattr(response, "body_iterator"):
            raise ValueError(
                "Cannot process StreamingResponse synchronously. "
                "Use 'await async_extract()' instead."
            )

        try:
            response_body = getattr(response, "body", b"") or b""
        except Exception as e:
            if raise_exc:
                raise
            print(f"Failed retrieving response body: {e}\n{traceback.format_exc()}")
            response_body = b""

        return response_body, response
