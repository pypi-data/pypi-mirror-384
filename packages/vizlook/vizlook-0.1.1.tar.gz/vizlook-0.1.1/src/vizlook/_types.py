import os
import json
import httpx
from typing import (
    List,
    Optional,
    Union,
    Literal,
    Any,
    TypeVar,
    Dict,
    Iterator,
    AsyncIterator,
)
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from ._exceptions import APIError, HttpStatusCode


def is_env_boolean(val: str) -> bool:
    return val == "true" or val == "1" or val == "on"


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
        defer_build=is_env_boolean(os.environ.get("PYDANTIC_DEFER_BUILD", "true")),
    )

    def to_dict(
        self,
        *,
        mode: Literal["json", "python"] = "python",
        use_api_field_name: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        """Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
        By default, fields will match the API response, not the property names from the model, unless `use_api_field_name=False` is passed.

        Args:
            mode: The mode in which to_python should run. If mode is 'json', the dictionary will only contain JSON serializable types. If mode is 'python', the dictionary may contain any Python objects.
            use_api_field_name: Whether to use the field that the API responded with or the property name. Default is `True`.
            exclude_unset: Whether to exclude fields that are unset or None from the output.
            exclude_defaults: Whether to exclude fields that are set to their default value from the output.
            exclude_none: Whether to exclude fields that have a value of `None` from the output.
            warnings: Whether to log warnings when invalid fields are encountered.
        """
        return self.model_dump(
            mode=mode,
            by_alias=use_api_field_name,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            warnings=warnings,
        )

    def to_json(
        self,
        *,
        indent: int | None = 2,
        use_api_field_name: bool = True,
        exclude_unset: bool = True,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        warnings: bool = True,
    ) -> str:
        """Generates a JSON representation of the model using Pydantic's `model_dump_json` method.
        By default, fields will match the API response, not the property names from the model, unless `use_api_field_name=False` is passed.

        Args:
            indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
            use_api_field_name: Whether to use the field that the API responded with or the property name. Default is `True`.
            exclude_unset: Whether to exclude fields that have not been explicitly set.
            exclude_defaults: Whether to exclude fields that have the default value.
            exclude_none: Whether to exclude fields that have a value of `None`.
            warnings: Whether to show any warnings that occurred during serialization.
        """
        return self.model_dump_json(
            indent=indent,
            by_alias=use_api_field_name,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            warnings=warnings,
        )


class ContentOptions(BaseModel):
    """
    Configure what search results include.
    """

    # Whether to include video transcription in the search results.
    include_transcription: Optional[bool] = None
    # Whether to include video summary in the search results.
    include_summary: Optional[bool] = None


Category = Literal["Healthcare", "Ecommerce", "Tech", "Finance", "Education"]
"""Video category"""


class SearchOptions(BaseModel):
    """
    Search options for performing a search query.
    """

    query: str
    # A video category.
    category: Optional[Category] = None
    # Start date for results based on video published date in millisecond or ISO timestamp string.
    start_published_date: Optional[Union[str, int]] = None
    # End date for results based on video published date in millisecond or ISO timestamp string.
    end_published_date: Optional[Union[str, int]] = None
    # A text string to search for in the video's spoken audio transcription, case-insensitive.
    contain_spoken_text: Optional[str] = None
    # A text string to search for in the video's on-screen text, case-insensitive.
    contain_screen_text: Optional[str] = None
    # The maximum number of search results to return. The default value is 10 and the maximum value is 20.
    max_results: Optional[int] = None
    # Configure what search results include.
    content_options: Optional[ContentOptions] = None


class VideoClip(BaseModel):
    """
    Video clip
    """

    # Start time of the video clip in seconds.
    start_time: int
    # End time of the video clip in seconds.
    end_time: int
    # Visual description of the video clip.
    visual_description: str


class AudioClip(BaseModel):
    """
    Audio clip
    """

    # Start time of the audio clip in seconds.
    start_time: int
    # End time of the audio clip in seconds.
    end_time: int
    # Transcription of the audio clip.
    transcription: str
    # The speaker ID of the audio clip, such as 'speaker_1'. If the speaker is identified, it will be set to the speaker's name.
    speaker_id: str


class VideoTranscription(BaseModel):
    """
    Video transcription
    """

    # Video clips with visual descriptions.
    video_clips: List[VideoClip]
    # Audio clips with transcriptions.
    audio_clips: List[AudioClip]


class VideoHighlight(BaseModel):
    """
    The video clip that best matches the query.
    """

    # Start time of the video clip in seconds.
    start_time: int
    # End time of the video clip in seconds.
    end_time: int
    # Visual description of the video clip.
    visual_description: str
    # Audio transcription of the video clip.
    audio_transcription: Optional[str] = None


class SectionSummary(BaseModel):
    """
    Section summaries of the video.
    """

    # Start time of the section in seconds.
    start_time: int
    # End time of the section in seconds.
    end_time: int
    # Title of the section.
    title: str
    # Summary of the section.
    summary: str


class VideoSummary(BaseModel):
    """
    Video summary
    """

    # Overall summary of the video.
    overall_summary: str
    # Section summaries of the video.
    section_summaries: List[SectionSummary]


class Thumbnail(BaseModel):
    url: str
    width: int
    height: int


class Author(BaseModel):
    name: str
    # Author page url.
    url: Optional[str] = None
    avatar: str


class SearchResultItem(BaseModel):
    """
    Search Result Item
    """

    # Video page url
    url: str
    title: str
    description: str
    thumbnail: Thumbnail
    author: Author
    # Video published date, ISO timestamp string
    published_date: str
    # Video duration in seconds
    duration: int
    favicon: str
    # relevance score for query
    score: Optional[float] = None
    highlights: List[VideoHighlight]
    transcription: Optional[VideoTranscription] = None
    summary: Optional[VideoSummary] = None


class SearchDollarCostBreakdown(BaseModel):
    # Search dollar cost.
    search: float
    # Summary dollar cost.
    summary: Optional[float] = None
    # Transcription dollar cost.
    transcription: Optional[float] = None


class SearchDollarCost(BaseModel):
    """
    Dollar cost of the search.
    """

    # Total dollar cost.
    total: float
    # Dollar cost breakdown.
    breakdown: Optional[SearchDollarCostBreakdown] = None


class SearchResponse(BaseModel):
    """
    Search response
    """

    # Search results.
    results: List[SearchResultItem]
    # Dollar cost of the search.
    dollar_cost: SearchDollarCost


class AnswerContentOptions(BaseModel):
    """
    Configure what search results include.
    """

    # Whether to include video transcription in the answer citations.
    include_transcription: Optional[bool] = None


class AnswerOptions(BaseModel):
    """
    Answer Options
    """

    query: str
    stream: Optional[bool] = None
    content_options: Optional[AnswerContentOptions] = None


class AnswerCitationItem(BaseModel):
    """
    Answer Citation Item
    """

    # Video page url
    url: str
    title: str
    description: str
    thumbnail: Thumbnail
    author: Author
    # Video published date, ISO timestamp string
    published_date: str
    # Video duration in seconds
    duration: int
    favicon: str
    # relevance score for query
    score: Optional[float] = None
    highlights: List[VideoHighlight]
    transcription: Optional[VideoTranscription] = None


class AnswerDollarCost(BaseModel):
    """
    Dollar cost of the answer.
    """

    # Total dollar cost.
    total: float


class AnswerResponse(BaseModel):
    """
    Answer response
    """

    # Answer to the query.
    answer: str
    # Answer citations.
    citations: List[AnswerCitationItem]
    # Dollar cost of the answer.
    dollar_cost: AnswerDollarCost


# Note: For discriminated unions, Pydantic's Union needs models to be distinct.


class AnswerStreamChunkAnswerData(BaseModel):
    # Type of the stream chunk.
    type: Literal["answer-chunk"]
    # Data of the stream chunk.
    data: str


class AnswerStreamChunkCitationsDataContent(BaseModel):
    citations: List[AnswerCitationItem]


class AnswerStreamChunkCitationsData(BaseModel):
    # Type of the stream chunk.
    type: Literal["data-citations"]
    # Data of the stream chunk.
    data: AnswerStreamChunkCitationsDataContent


class AnswerStreamChunkCostDataContent(BaseModel):
    dollar_cost: AnswerDollarCost


class AnswerStreamChunkCostData(BaseModel):
    # Type of the stream chunk.
    type: Literal["data-cost"]
    # Data of the stream chunk.
    data: AnswerStreamChunkCostDataContent


class AnswerStreamChunkErrorDataContent(BaseModel):
    # Error message if has message.
    error_text: str


class AnswerStreamChunkErrorData(BaseModel):
    # Type of the stream chunk.
    type: Literal["error"]
    # Data of the stream chunk.
    data: AnswerStreamChunkErrorDataContent


AnswerStreamChunk = Union[
    AnswerStreamChunkAnswerData,
    AnswerStreamChunkCitationsData,
    AnswerStreamChunkCostData,
    AnswerStreamChunkErrorData,
]
"""Type of the stream chunk."""


class VideoContentsOptions(BaseModel):
    """
    Video Contents Options
    """

    # Video page url list
    urls: List[str]
    # Crawl mode, default is 'Never'
    crawl_mode: Optional[Literal["Never", "Fallback", "Always"]] = "Never"
    # Configure what video results include.
    content_options: Optional[ContentOptions] = None


VideoContentErrorType = Literal[
    "FAILED_TO_PARSE_URL",
    "CACHE_NOT_FOUND",
    "CRAWL_SOURCE_FAIL",
    "CRAWL_NOT_FOUND",
    "CRAWL_VIDEO_DURATION_EXCEEDS_LIMIT",
    "CRAWL_SERVER_ERROR",
    "CRAWL_TIMEOUT",
]
"""Error type when getting video contents"""


class VideoContentData(BaseModel):
    """
    Video content data.
    """

    # Video page url.
    url: str
    # Video title.
    title: str
    # Video description.
    description: str
    # Video thumbnail.
    thumbnail: Thumbnail
    # Video author.
    author: Author
    # Video published date, ISO timestamp string.
    published_date: str
    # Video duration in seconds.
    duration: int
    # Video page favicon.
    favicon: str
    # Video transcription.
    transcription: Optional[VideoTranscription] = None
    # Video summary.
    summary: Optional[VideoSummary] = None


class VideoContentError(BaseModel):
    """
    Video content error if has error.
    """

    # Error type.
    type: VideoContentErrorType
    # Error message if has message.
    message: Optional[str] = None


class VideoContentStatus(BaseModel):
    """
    Video content status.
    """

    # Video page url.
    url: str
    # Video content status.
    status: Literal["Success", "Fail"]
    # Video content error if has error.
    error: Optional[VideoContentError] = None
    # Whether the video content is crawled live.
    is_live_crawl: Optional[bool] = None


class VideoContent(BaseModel):
    """
    Video Content
    """

    # Video content data.
    data: Optional[VideoContentData] = None
    # Video content status.
    status: VideoContentStatus


class VideoContentsCostBreakdown(BaseModel):
    # Transcription dollar cost.
    transcription: Optional[float] = None
    # Summary dollar cost.
    summary: Optional[float] = None
    # Live crawl dollar cost.
    crawl: Optional[float] = None


class VideoContentsDollarCost(BaseModel):
    """
    Dollar cost of the video contents.
    """

    # Total dollar cost.
    total: float
    # Dollar cost breakdown.
    breakdown: Optional[VideoContentsCostBreakdown] = None


class VideoContentsResponse(BaseModel):
    """
    Video Contents Response
    """

    # Video contents.
    results: List[VideoContent]
    # Dollar cost of the video contents.
    dollar_cost: VideoContentsDollarCost


class StreamAnswerResponse:
    """A class representing a streaming answer response."""

    _http_response: httpx.Response

    def __init__(self, http_response: httpx.Response):
        self._http_response = http_response
        self._ensure_response_success()

    def _ensure_response_success(self):
        if not self._http_response.is_success:
            error_data = {}
            try:
                self._http_response.read()
                error_data = json.loads(self._http_response.text)
            except:
                error_data = {"error": self._http_response.text or "Unknown error."}

            error_message = error_data.pop("error", "Unknown error.")
            extra = None if not error_data else error_data
            raise APIError(
                error_message,
                self._http_response.status_code,
                path="/answer",
                extra=extra,
            )

    def __iter__(self) -> Iterator[AnswerStreamChunk]:
        for line in self._http_response.iter_lines():
            if not line:
                continue

            chunk_str = line.removeprefix("data: ")

            if chunk_str.strip() == "[DONE]":
                continue

            try:
                chunk = json.loads(chunk_str)
            except json.JSONDecodeError:
                continue

            stream_chunk = None

            try:
                chunk_type = chunk.get("type")

                if chunk_type == "answer-chunk":
                    stream_chunk = AnswerStreamChunkAnswerData(**chunk)
                if chunk_type == "data-citations":
                    stream_chunk = AnswerStreamChunkCitationsData(**chunk)
                if chunk_type == "data-cost":
                    stream_chunk = AnswerStreamChunkCostData(**chunk)
                if chunk_type == "error":
                    stream_chunk = AnswerStreamChunkErrorData(**chunk)
            except Exception as err:
                raise APIError(
                    str(err) or "Unknown error.",
                    HttpStatusCode.InternalServerError,
                    path="/answer",
                )

            if stream_chunk:
                yield stream_chunk

    def close(self) -> None:
        self._http_response.close()


class AsyncStreamAnswerResponse:
    """A class representing a async streaming answer response."""

    _http_response: httpx.Response

    def __init__(self, *, http_response: httpx.Response):
        self._http_response = http_response
        self._ensure_response_success()

    def _ensure_response_success(self):
        if not self._http_response.is_success:
            raise APIError(
                "Answer request failed.",
                self._http_response.status_code,
                path="/answer",
            )

    def __aiter__(self):
        async def generator() -> AsyncIterator[AnswerStreamChunk]:
            async for line in self._http_response.aiter_lines():
                if not line:
                    continue

                chunk_str = line.removeprefix("data: ")

                if chunk_str.strip() == "[DONE]":
                    continue

                try:
                    chunk = json.loads(chunk_str)
                except json.JSONDecodeError:
                    continue

                stream_chunk = None

                try:
                    chunk_type = chunk.get("type")

                    if chunk_type == "answer-chunk":
                        stream_chunk = AnswerStreamChunkAnswerData(**chunk)
                    if chunk_type == "data-citations":
                        stream_chunk = AnswerStreamChunkCitationsData(**chunk)
                    if chunk_type == "data-cost":
                        stream_chunk = AnswerStreamChunkCostData(**chunk)
                    if chunk_type == "error":
                        stream_chunk = AnswerStreamChunkErrorData(**chunk)
                except Exception as err:
                    raise APIError(
                        str(err) or "Unknown error.",
                        HttpStatusCode.InternalServerError,
                        path="/answer",
                    )

                if stream_chunk:
                    yield stream_chunk

        return generator()

    async def close(self) -> None:
        await self._http_response.aclose()


NonStreamResponseT = TypeVar(
    "NonStreamResponseT",
    bound=Union[
        "BaseModel",
        httpx.Response,
        Dict[str, Any],
    ],
)
