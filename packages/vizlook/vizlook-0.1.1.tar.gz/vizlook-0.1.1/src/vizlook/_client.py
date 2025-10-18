import json
import inspect
import httpx
from typing import Optional, Literal, Any, Union, Type, Mapping, List, cast
from ._version import __version__
from ._exceptions import APIError, HttpStatusCode
from ._types import (
    NonStreamResponseT,
    BaseModel,
    Category,
    SearchResponse,
    SearchOptions,
    VideoContentsOptions,
    VideoContentsResponse,
    AnswerOptions,
    AnswerResponse,
    StreamAnswerResponse,
    AsyncStreamAnswerResponse,
)
from pydantic import ValidationError

DEFAULT_TIMEOUT = httpx.Timeout(timeout=300, connect=10.0)


class Vizlook:
    """The Vizlook class encapsulates the API's endpoints."""

    _client: httpx.Client
    _base_url: str
    _headers: dict[str, str]
    _timeout: httpx.Timeout

    def __init__(
        self,
        *,
        api_key: Optional[str],
        base_url: str = "https://api.vizlook.com",
        timeout: Union[httpx.Timeout, float, None] = DEFAULT_TIMEOUT,
    ):
        if api_key is None:
            import os

            api_key = os.environ.get("VIZLOOK_API_KEY")
            if api_key is None:
                raise APIError(
                    "The API key must be provided as an argument or as an environment variable (VIZLOOK_API_KEY).",
                    HttpStatusCode.Unauthorized,
                )

        self._base_url = base_url
        self._headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": f"vizlook-python-sdk {__version__}",
        }
        self._timeout = (
            timeout if isinstance(timeout, httpx.Timeout) else httpx.Timeout(timeout)
        )
        self._client = httpx.Client(
            base_url=self._base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    def request(
        self,
        *,
        endpoint: str,
        method: Literal["POST"] = "POST",
        body: dict[str, Any] | None = None,
        headers: httpx.Headers | Mapping[str, str] | None = None,
        stream: bool = False,
        non_stream_cls: Type[NonStreamResponseT] | None = None,
        stream_cls: StreamAnswerResponse | None = None,
    ) -> NonStreamResponseT | StreamAnswerResponse:
        """
        Makes a request to the Vizlook API.

        Raises:
        APIError: When any API request fails with structured error information.
        """
        try:
            request = self._client.build_request(
                method, endpoint, json=body, headers=headers
            )
            response = self._client.send(request, stream=stream)

            if not response.is_success:
                error_data = {}
                try:
                    if stream:
                        response.read()
                        error_data = json.loads(response.text)
                    else:
                        error_data = response.json()
                except:
                    error_data = {"error": response.text or "Unknown error."}

                error_message = error_data.pop("error", "Unknown error.")
                extra = None if not error_data else error_data
                raise APIError(
                    error_message,
                    response.status_code,
                    path=endpoint,
                    extra=extra,
                )

            if stream and stream_cls:
                return cast(StreamAnswerResponse, stream_cls(http_response=response))

            if not stream and non_stream_cls:
                if inspect.isclass(non_stream_cls) and issubclass(
                    non_stream_cls, BaseModel
                ):
                    return cast(NonStreamResponseT, non_stream_cls(**response.json()))
                if non_stream_cls == httpx.Response:
                    return cast(httpx.Response, response)

                return cast(NonStreamResponseT, response.json())

            return cast(httpx.Response, response)
        except httpx.RequestError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path=endpoint,
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path=endpoint,
            )

    def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
        category: Optional[Category] = None,
        start_published_date: Optional[Union[str, int]] = None,
        end_published_date: Optional[Union[str, int]] = None,
        contain_spoken_text: Optional[str] = None,
        contain_screen_text: Optional[str] = None,
        include_transcription: Optional[bool] = None,
        include_summary: Optional[bool] = None,
    ) -> SearchResponse:
        """
        Args:
            query: The query to search.
            max_results: The maximum number of search results to return. The default value is 10 and the maximum value is 20.
            category: Video category.
            start_published_date: Start date for results based on video published date in millisecond or ISO timestamp string.
            end_published_date: End date for results based on video published date in millisecond or ISO timestamp string.
            contain_spoken_text: A text string to search for in the video's spoken audio transcription, case-insensitive.
            contain_screen_text: A text string to search for in the video's on-screen text, case-insensitive.
            include_transcription: Whether to include video transcription in the search results.
            include_summary: Whether to include video summary in the search results.
        """
        try:
            search_options = SearchOptions(
                query=query,
                max_results=max_results,
                category=category,
                start_published_date=start_published_date,
                end_published_date=end_published_date,
                contain_spoken_text=contain_spoken_text,
                contain_screen_text=contain_screen_text,
                content_options={
                    "include_transcription": include_transcription,
                    "include_summary": include_summary,
                },
            )
            request_body = search_options.to_dict(exclude_none=True)

            response: SearchResponse = self.request(
                endpoint="/search",
                method="POST",
                body=request_body,
                non_stream_cls=SearchResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/search",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/search",
            )

    def get_video_contents(
        self,
        urls: Union[str, List[str]],
        *,
        crawl_mode: Optional[Literal["Never", "Fallback", "Always"]] = "Never",
        include_transcription: Optional[bool] = None,
        include_summary: Optional[bool] = None,
    ) -> VideoContentsResponse:
        """
        Args:
            urls: Video page url list.
            crawl_mode:
                - Never: never crawl from source
                - Fallback: crawl from source when there is no existing data
                - Always: always real-time crawl from source
            include_transcription: Whether to include video transcription in the search results.
            include_summary: Whether to include video summary in the search results.
        """
        try:
            contents_options = VideoContentsOptions(
                urls=urls if type(urls) is list else [urls],
                crawl_mode=crawl_mode,
                content_options={
                    "include_transcription": include_transcription,
                    "include_summary": include_summary,
                },
            )
            request_body = contents_options.to_dict(exclude_none=True)

            response: VideoContentsResponse = self.request(
                endpoint="/videos",
                method="POST",
                body=request_body,
                non_stream_cls=VideoContentsResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/videos",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/videos",
            )

    def answer(
        self,
        query: str,
        *,
        include_transcription: Optional[bool] = None,
    ) -> AnswerResponse:
        """
        Args:
            query: The query to answer.
            include_transcription: Whether to include video transcription in the answer citations.
        """
        try:
            answer_options = AnswerOptions(
                query=query,
                stream=False,
                content_options={
                    "include_transcription": include_transcription,
                },
            )
            request_body = answer_options.to_dict(exclude_none=True)

            response: AnswerResponse = self.request(
                endpoint="/answer",
                method="POST",
                body=request_body,
                non_stream_cls=AnswerResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/answer",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/answer",
            )

    def stream_answer(
        self,
        query: str,
        *,
        include_transcription: Optional[bool] = None,
    ) -> StreamAnswerResponse:
        """
        Args:
            query: The query to answer.
            include_transcription: Whether to include video transcription in the answer citations.
        """
        try:
            answer_options = AnswerOptions(
                query=query,
                stream=True,
                content_options={
                    "include_transcription": include_transcription,
                },
            )
            request_body = answer_options.to_dict(exclude_none=True)

            response: StreamAnswerResponse = self.request(
                endpoint="/answer",
                method="POST",
                body=request_body,
                stream=True,
                stream_cls=StreamAnswerResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/answer",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/answer",
            )


class AsyncVizlook:
    """The Vizlook class encapsulates the API's endpoints for async call."""

    _client: httpx.AsyncClient
    _base_url: str
    _headers: dict[str, str]
    _timeout: httpx.Timeout

    def __init__(
        self,
        *,
        api_key: Optional[str],
        base_url: str = "https://api.vizlook.com",
        timeout: Union[httpx.Timeout, float, None] = DEFAULT_TIMEOUT,
    ):
        if api_key is None:
            import os

            api_key = os.environ.get("VIZLOOK_API_KEY")
            if api_key is None:
                raise APIError(
                    "The API key must be provided as an argument or as an environment variable (VIZLOOK_API_KEY).",
                    HttpStatusCode.Unauthorized,
                )

        self._base_url = base_url
        self._headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "User-Agent": f"vizlook-python-sdk {__version__}",
        }
        self._timeout = (
            timeout if isinstance(timeout, httpx.Timeout) else httpx.Timeout(timeout)
        )
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._headers,
            timeout=self._timeout,
        )

    async def request(
        self,
        *,
        endpoint: str,
        method: Literal["POST"] = "POST",
        body: dict[str, Any] | None = None,
        headers: httpx.Headers | Mapping[str, str] | None = None,
        stream: bool = False,
        non_stream_cls: Type[NonStreamResponseT] | None = None,
        stream_cls: AsyncStreamAnswerResponse | None = None,
    ) -> NonStreamResponseT | AsyncStreamAnswerResponse:
        """
        Makes a request to the Vizlook API.

        Raises:
        APIError: When any API request fails with structured error information.
        """
        try:
            request = self._client.build_request(
                method, endpoint, json=body, headers=headers
            )
            response = await self._client.send(request, stream=stream)

            if not response.is_success:
                error_data = {}
                try:
                    if stream:
                        await response.aread()
                        error_data = json.loads(response.text)
                    else:
                        error_data = response.json()
                except:
                    error_data = {"error": response.text or "Unknown error."}

                error_message = error_data.pop("error", "Unknown error.")
                extra = None if not error_data else error_data
                raise APIError(
                    error_message,
                    response.status_code,
                    path=endpoint,
                    extra=extra,
                )

            if stream and stream_cls:
                return cast(
                    AsyncStreamAnswerResponse, stream_cls(http_response=response)
                )

            if not stream and non_stream_cls:
                if inspect.isclass(non_stream_cls) and issubclass(
                    non_stream_cls, BaseModel
                ):
                    return cast(NonStreamResponseT, non_stream_cls(**response.json()))
                if non_stream_cls == httpx.Response:
                    return cast(httpx.Response, response)

                return cast(NonStreamResponseT, response.json())

            return cast(httpx.Response, response)
        except httpx.RequestError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path=endpoint,
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path=endpoint,
            )

    async def search(
        self,
        query: str,
        *,
        max_results: Optional[int] = None,
        category: Optional[Category] = None,
        start_published_date: Optional[Union[str, int]] = None,
        end_published_date: Optional[Union[str, int]] = None,
        contain_spoken_text: Optional[str] = None,
        contain_screen_text: Optional[str] = None,
        include_transcription: Optional[bool] = None,
        include_summary: Optional[bool] = None,
    ) -> SearchResponse:
        """
        Args:
            query: The query to search.
            max_results: The maximum number of search results to return. The default value is 10 and the maximum value is 20.
            category: Video category.
            start_published_date: Start date for results based on video published date in millisecond or ISO timestamp string.
            end_published_date: End date for results based on video published date in millisecond or ISO timestamp string.
            contain_spoken_text: A text string to search for in the video's spoken audio transcription, case-insensitive.
            contain_screen_text: A text string to search for in the video's on-screen text, case-insensitive.
            include_transcription: Whether to include video transcription in the search results.
            include_summary: Whether to include video summary in the search results.
        """
        try:
            search_options = SearchOptions(
                query=query,
                max_results=max_results,
                category=category,
                start_published_date=start_published_date,
                end_published_date=end_published_date,
                contain_spoken_text=contain_spoken_text,
                contain_screen_text=contain_screen_text,
                content_options={
                    "include_transcription": include_transcription,
                    "include_summary": include_summary,
                },
            )
            request_body = search_options.to_dict(exclude_none=True)

            response: SearchResponse = await self.request(
                endpoint="/search",
                method="POST",
                body=request_body,
                non_stream_cls=SearchResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/search",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/search",
            )

    async def get_video_contents(
        self,
        urls: Union[str, List[str]],
        *,
        crawl_mode: Optional[Literal["Never", "Fallback", "Always"]] = "Never",
        include_transcription: Optional[bool] = None,
        include_summary: Optional[bool] = None,
    ) -> VideoContentsResponse:
        """
        Args:
            urls: Video page url list.
            crawl_mode:
                - Never: never crawl from source
                - Fallback: crawl from source when there is no existing data
                - Always: always real-time crawl from source
            include_transcription: Whether to include video transcription in the search results.
            include_summary: Whether to include video summary in the search results.
        """
        try:
            contents_options = VideoContentsOptions(
                urls=urls if type(urls) is list else [urls],
                crawl_mode=crawl_mode,
                content_options={
                    "include_transcription": include_transcription,
                    "include_summary": include_summary,
                },
            )
            request_body = contents_options.to_dict(exclude_none=True)

            response: VideoContentsResponse = await self.request(
                endpoint="/videos",
                method="POST",
                body=request_body,
                non_stream_cls=VideoContentsResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/videos",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/videos",
            )

    async def answer(
        self,
        query: str,
        *,
        include_transcription: Optional[bool] = None,
    ) -> AnswerResponse:
        """
        Args:
            query: The query to answer.
            include_transcription: Whether to include video transcription in the answer citations.
        """
        try:
            answer_options = AnswerOptions(
                query=query,
                stream=False,
                content_options={
                    "include_transcription": include_transcription,
                },
            )
            request_body = answer_options.to_dict(exclude_none=True)

            response: AnswerResponse = await self.request(
                endpoint="/answer",
                method="POST",
                body=request_body,
                non_stream_cls=AnswerResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/answer",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/answer",
            )

    async def stream_answer(
        self,
        query: str,
        *,
        include_transcription: Optional[bool] = None,
    ) -> AsyncStreamAnswerResponse:
        """
        Args:
            query: The query to answer.
            include_transcription: Whether to include video transcription in the answer citations.
        """
        try:
            answer_options = AnswerOptions(
                query=query,
                stream=True,
                content_options={
                    "include_transcription": include_transcription,
                },
            )
            request_body = answer_options.to_dict(exclude_none=True)

            response: AsyncStreamAnswerResponse = await self.request(
                endpoint="/answer",
                method="POST",
                body=request_body,
                stream=True,
                stream_cls=AsyncStreamAnswerResponse,
            )

            return response
        except ValidationError as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.BadRequest,
                path="/answer",
            )
        except APIError:
            raise
        except Exception as err:
            raise APIError(
                str(err) or "Unknown error.",
                HttpStatusCode.InternalServerError,
                path="/answer",
            )
