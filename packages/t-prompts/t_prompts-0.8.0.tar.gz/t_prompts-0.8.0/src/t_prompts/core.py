"""Core implementation of structured prompts."""

import inspect
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from string.templatelib import Template
from typing import Any, Literal, Optional, Union

from .exceptions import (
    DuplicateKeyError,
    EmptyExpressionError,
    ImageRenderError,
    MissingKeyError,
    NotANestedPromptError,
    UnsupportedValueTypeError,
)
from .parsing import parse_format_spec as _parse_format_spec
from .parsing import parse_render_hints as _parse_render_hints
from .parsing import parse_separator as _parse_separator
from .text import process_dedent as _process_dedent


# Workaround for Python 3.14.0b3 missing convert function
def convert(value: str, conversion: Literal["r", "s", "a"]) -> str:
    """Apply string conversion (!r, !s, !a) to a value."""
    if conversion == "s":
        return str(value)
    elif conversion == "r":
        return repr(value)
    elif conversion == "a":
        return ascii(value)
    return value


# Try to import PIL for image support (optional dependency)
try:
    from PIL import Image as PILImage

    HAS_PIL = True
except ImportError:
    PILImage = None  # type: ignore
    HAS_PIL = False


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """
    Source code location information for an Element.

    All fields are optional to handle cases where source information is unavailable
    (e.g., REPL, eval, exec). Use the is_available property to check if location
    information is present.

    This information is captured directly from Python stack frames without reading
    source files, making it fast and lightweight.

    Attributes
    ----------
    filename : str | None
        Short filename (e.g., 'script.py', '<stdin>', '<string>').
    filepath : str | None
        Full absolute path to the file.
    line : int | None
        Line number where prompt was created (1-indexed).
    """

    filename: Optional[str] = None
    filepath: Optional[str] = None
    line: Optional[int] = None

    @property
    def is_available(self) -> bool:
        """
        Check if source location information is available.

        Returns
        -------
        bool
            True if location info is present (filename is not None), False otherwise.
        """
        return self.filename is not None

    def format_location(self) -> str:
        """
        Format location as a readable string.

        Returns
        -------
        str
            Formatted location string (e.g., "script.py:42" or "<unavailable>").
        """
        if not self.is_available:
            return "<unavailable>"
        parts = [self.filename or "<unknown>"]
        if self.line is not None:
            parts.append(str(self.line))
        return ":".join(parts)


def _capture_source_location() -> Optional[SourceLocation]:
    """
    Capture source code location information from the call stack.

    Walks up the stack to find the first frame outside this library
    (the actual user code that called prompt()). Only uses information
    directly available from the stack frame without reading source files.

    Returns
    -------
    SourceLocation | None
        Source location if available, None if unavailable.
    """
    # Walk up the stack to find the first non-library frame
    frame = inspect.currentframe()
    if frame is None:
        return None

    # Get the directory of this library to identify internal frames
    library_dir = str(Path(__file__).parent.resolve())

    try:
        # Skip frames until we're out of this library
        while frame is not None:
            frame_file = frame.f_code.co_filename

            # Check if we're outside the library
            if not frame_file.startswith(library_dir):
                # Found user code frame - extract info directly from frame
                filename = Path(frame_file).name
                filepath = str(Path(frame_file).resolve())
                lineno = frame.f_lineno

                return SourceLocation(
                    filename=filename,
                    filepath=filepath,
                    line=lineno,
                )

            frame = frame.f_back
    finally:
        # Clean up frame references to avoid reference cycles
        del frame

    return None


@dataclass(frozen=True, slots=True)
class TextChunk:
    """
    A chunk of text in the rendered output.

    Attributes
    ----------
    text : str
        The text content of this chunk.
    chunk_index : int
        Position of this chunk in the output sequence.
    """

    text: str
    chunk_index: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class ImageChunk:
    """
    An image chunk in the rendered output.

    Attributes
    ----------
    image : Any
        The PIL Image object (typed as Any to avoid hard dependency on PIL).
    chunk_index : int
        Position of this chunk in the output sequence.
    id : str
        Unique identifier for this chunk (UUID4 string).
    """

    image: Any
    chunk_index: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """
    Represents a span in the rendered output that maps back to a source element.

    Attributes
    ----------
    start : int
        Starting position (inclusive) in the rendered chunk.
        For text chunks: character offset. For image chunks: 0.
    end : int
        Ending position (exclusive) in the rendered chunk.
        For text chunks: character offset. For image chunks: 1 (whole image).
    key : Union[str, int]
        The key of the element: string for interpolations, int for static segments.
    path : tuple[Union[str, int], ...]
        Path from root to this element (sequence of keys).
    element_type : Literal["static", "interpolation", "image"]
        The type of element this span represents.
    chunk_index : int
        Index of the chunk this span refers to in the chunks list.
    element_id : str
        UUID of the source element (from Element.id or StructuredPrompt.id).
    """

    start: int
    end: int
    key: Union[str, int]
    path: tuple[Union[str, int], ...]
    element_type: Literal["static", "interpolation", "image"]
    chunk_index: int
    element_id: str


class IntermediateRepresentation:
    """
    Intermediate representation of a StructuredPrompt with multi-modal chunks and source mapping.

    This class serves as the bridge between structured prompts and their final output.
    It's ideal for:
    - Structured prompt optimization (removing parts when approaching context limits)
    - Debugging optimization strategies with full provenance
    - Multi-modal support (text and image chunks)
    - Token counting for specific portions of the prompt

    The name "IntermediateRepresentation" reflects that this is not necessarily the
    final output sent to an LLM, but rather a structured intermediate form that can
    be further processed, optimized, or transformed before final rendering.

    Attributes
    ----------
    chunks : list[TextChunk | ImageChunk]
        Ordered list of output chunks (text or image).
    source_map : list[SourceSpan]
        List of source spans mapping chunks and positions back to source elements.
    element_spans : dict[str, list[SourceSpan]]
        Reverse index: element_id → spans for bidirectional lookup.
    source_prompt : StructuredPrompt
        The StructuredPrompt that was rendered to produce this result.
    """

    def __init__(
        self,
        chunks: list[Union[TextChunk, ImageChunk]],
        source_map: list[SourceSpan],
        source_prompt: "StructuredPrompt",
    ):
        self._chunks = chunks
        self._source_map = source_map
        self._source_prompt = source_prompt
        self._id = str(uuid.uuid4())  # Unique identifier for this IntermediateRepresentation

        # Build reverse index: element_id -> list of spans
        self._element_spans: dict[str, list[SourceSpan]] = {}
        for span in source_map:
            if span.element_id not in self._element_spans:
                self._element_spans[span.element_id] = []
            self._element_spans[span.element_id].append(span)

    @property
    def chunks(self) -> list[Union[TextChunk, ImageChunk]]:
        """Return the list of output chunks."""
        return self._chunks

    @property
    def text(self) -> str:
        """
        Return the rendered text (concatenates all text chunks).

        Raises
        ------
        ImageRenderError
            If any image chunks are present.
        """
        # Check for image chunks
        for chunk in self._chunks:
            if isinstance(chunk, ImageChunk):
                raise ImageRenderError()

        # Concatenate all text chunks
        return "".join(chunk.text for chunk in self._chunks if isinstance(chunk, TextChunk))

    @property
    def source_map(self) -> list[SourceSpan]:
        """Return the source map."""
        return self._source_map

    @property
    def element_spans(self) -> dict[str, list[SourceSpan]]:
        """Return the element ID to spans mapping (for source→output lookups)."""
        return self._element_spans

    @property
    def source_prompt(self) -> "StructuredPrompt":
        """Return the source StructuredPrompt that was rendered."""
        return self._source_prompt

    @property
    def id(self) -> str:
        """Return the unique identifier for this IntermediateRepresentation."""
        return self._id

    def get_span_at(self, position_or_chunk: int, position: Optional[int] = None) -> Optional[SourceSpan]:
        """
        Get the source span at a given position.

        This method supports two calling conventions:
        1. get_span_at(position) - searches in chunk 0 (backward compatible)
        2. get_span_at(chunk_index, position) - searches in specific chunk

        Parameters
        ----------
        position_or_chunk : int
            Either the position (if position is None) or chunk_index (if position is provided).
        position : int, optional
            Position within the chunk (for text chunks: character offset, for image chunks: should be 0).
            If None, position_or_chunk is treated as the position in chunk 0.

        Returns
        -------
        SourceSpan | None
            The span containing this position, or None if not in any span.
        """
        if position is None:
            # Backward compatible: get_span_at(position) searches chunk 0
            chunk_index = 0
            position = position_or_chunk
        else:
            # New API: get_span_at(chunk_index, position)
            chunk_index = position_or_chunk

        for span in self._source_map:
            if span.chunk_index == chunk_index and span.start <= position < span.end:
                return span
        return None

    def get_span_for_key(self, key: Union[str, int], path: tuple[Union[str, int], ...] = ()) -> Optional[SourceSpan]:
        """
        Get the source span for a specific key and path.

        Parameters
        ----------
        key : Union[str, int]
            The key to search for (string for interpolations, int for statics).
        path : tuple[Union[str, int], ...]
            The path from root to the element (empty for root level).

        Returns
        -------
        SourceSpan | None
            The span for this key/path, or None if not found.
        """
        for span in self._source_map:
            if span.key == key and span.path == path:
                return span
        return None

    def get_static_span(self, static_index: int, path: tuple[Union[str, int], ...] = ()) -> Optional[SourceSpan]:
        """
        Get the source span for a static segment by its index.

        Parameters
        ----------
        static_index : int
            The index of the static segment (position in template strings tuple).
        path : tuple[Union[str, int], ...]
            The path from root to the static (empty for root level).

        Returns
        -------
        SourceSpan | None
            The span for this static, or None if not found.
        """
        for span in self._source_map:
            if span.element_type == "static" and span.key == static_index and span.path == path:
                return span
        return None

    def get_interpolation_span(self, key: str, path: tuple[Union[str, int], ...] = ()) -> Optional[SourceSpan]:
        """
        Get the source span for an interpolation by its key.

        Parameters
        ----------
        key : str
            The key of the interpolation.
        path : tuple[Union[str, int], ...]
            The path from root to the interpolation (empty for root level).

        Returns
        -------
        SourceSpan | None
            The span for this interpolation, or None if not found.
        """
        for span in self._source_map:
            if span.element_type == "interpolation" and span.key == key and span.path == path:
                return span
        return None

    def get_spans_for_element(self, element_id: str) -> list[SourceSpan]:
        """
        Get all source spans for a specific element by its ID.

        This enables source→output lookups: given an element, find all spans
        in the output that came from it.

        Parameters
        ----------
        element_id : str
            The UUID of the element (from Element.id or StructuredPrompt.id).

        Returns
        -------
        list[SourceSpan]
            List of all spans for this element (may be empty if not found).
        """
        return self._element_spans.get(element_id, [])

    def get_spans_for_prompt(self, prompt: "StructuredPrompt") -> list[SourceSpan]:
        """
        Get all source spans for a specific StructuredPrompt (aggregate query).

        This returns spans from all elements within the prompt, including
        nested prompts. Useful for token counting and optimization.

        Parameters
        ----------
        prompt : StructuredPrompt
            The StructuredPrompt to get spans for.

        Returns
        -------
        list[SourceSpan]
            List of all spans from this prompt and its nested prompts.
        """
        result = []
        # Get spans for all elements in this prompt
        for element in prompt.elements:
            result.extend(self.get_spans_for_element(element.id))
            # If this is a nested prompt, recursively get its spans
            if isinstance(element, StructuredInterpolation) and isinstance(element.value, StructuredPrompt):
                result.extend(self.get_spans_for_prompt(element.value))
            elif isinstance(element, ListInterpolation):
                for item in element.items:
                    result.extend(self.get_spans_for_prompt(item))
        return result

    def __str__(self) -> str:
        """Return the rendered text."""
        return self.text

    def toJSON(self) -> dict[str, Any]:
        """
        Export IntermediateRepresentation as JSON with bidirectional source mapping.

        This method provides a comprehensive JSON representation optimized for analysis,
        debugging, and provenance tracking. The structure includes:

        1. **ir_id**: UUID of this IntermediateRepresentation
        2. **source_prompt**: Complete hierarchical JSON of the StructuredPrompt (from toJSON())
        3. **chunks**: Array of text/image chunks with metadata
        4. **chunk_id_to_index**: Lookup table mapping chunk UUIDs to their indices
        5. **source_map**: Bidirectional mapping using element_id and chunk_id

        The source map enables efficient queries in both directions:
        - Source → Output: Given element_id, find all chunks/positions where it appears
        - Output → Source: Given chunk_id and position, find which element produced it

        Returns
        -------
        dict[str, Any]
            JSON-serializable dictionary with complete IR structure and mappings.

        Examples
        --------
        >>> x = "value"
        >>> p = prompt(t"{x:x}")
        >>> ir = p.render()
        >>> data = ir.toJSON()
        >>> data.keys()
        dict_keys(['ir_id', 'source_prompt', 'chunks', 'chunk_id_to_index', 'source_map'])
        """
        # 1. Serialize source prompt using hierarchical toJSON()
        source_prompt_json = self._source_prompt.toJSON()

        # 2. Serialize chunks array
        chunks_json = []
        for chunk in self._chunks:
            if isinstance(chunk, TextChunk):
                chunks_json.append({
                    "type": "text",
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                })
            elif isinstance(chunk, ImageChunk):
                chunks_json.append({
                    "type": "image",
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "image_data": _serialize_image(chunk.image),
                })

        # 3. Build chunk_id_to_index lookup
        chunk_id_to_index = {chunk.id: chunk.chunk_index for chunk in self._chunks}

        # 4. Serialize source_map with chunk_id for bidirectional lookup
        source_map_json = []
        for span in self._source_map:
            # Look up the chunk at this span's chunk_index to get its ID
            chunk = self._chunks[span.chunk_index]
            source_map_json.append({
                "start": span.start,
                "end": span.end,
                "key": span.key,
                "path": list(span.path),  # Convert tuple to list for JSON
                "element_type": span.element_type,
                "chunk_index": span.chunk_index,
                "chunk_id": chunk.id,
                "element_id": span.element_id,
            })

        return {
            "ir_id": self._id,
            "source_prompt": source_prompt_json,
            "chunks": chunks_json,
            "chunk_id_to_index": chunk_id_to_index,
            "source_map": source_map_json,
        }

    def __repr__(self) -> str:
        """Return a helpful debug representation."""
        return f"IntermediateRepresentation(chunks={len(self._chunks)}, spans={len(self._source_map)})"


@dataclass(frozen=True, slots=True)
class Element:
    """
    Base class for all elements in a StructuredPrompt.

    An element can be either a Static text segment or a StructuredInterpolation.

    Attributes
    ----------
    key : Union[str, int]
        Identifier for this element. For interpolations: string key from format_spec.
        For static segments: integer index in the strings tuple.
    parent : StructuredPrompt | None
        The parent StructuredPrompt that contains this element.
    index : int
        The position of this element in the overall element sequence.
    source_location : SourceLocation | None
        Source code location information for this element (if available).
    id : str
        Unique identifier for this element (UUID4 string).
    metadata : dict[str, Any]
        Metadata dictionary for storing analysis results and other information.
    """

    key: Union[str, int]
    parent: Optional["StructuredPrompt"]
    index: int
    source_location: Optional[SourceLocation] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Static(Element):
    """
    Represents a static string segment from the t-string.

    Static segments are the literal text between interpolations.

    Attributes
    ----------
    key : int
        The position of this static in the template's strings tuple.
    parent : StructuredPrompt | None
        The parent StructuredPrompt that contains this static.
    index : int
        The position of this element in the overall element sequence.
    source_location : SourceLocation | None
        Source code location information for this element (if available).
    value : str
        The static text content.
    """

    value: str = ""  # Default not used, but required for dataclass field ordering


@dataclass(frozen=True, slots=True)
class StructuredInterpolation(Element):
    """
    Immutable record of one interpolation occurrence in a StructuredPrompt.

    Attributes
    ----------
    key : str
        The key used for dict-like access (parsed from format_spec or expression).
    parent : StructuredPrompt | None
        The parent StructuredPrompt that contains this interpolation.
    index : int
        The position of this element in the overall element sequence.
    source_location : SourceLocation | None
        Source code location information for this element (if available).
    expression : str
        The original expression text from the t-string (what was inside {}).
    conversion : str | None
        The conversion flag if present (!s, !r, !a), or None.
    format_spec : str
        The format specification string (everything after :), or empty string.
    render_hints : str
        Rendering hints parsed from format_spec (everything after first colon in format spec).
    value : str | StructuredPrompt
        The evaluated value (string or nested StructuredPrompt).
    """

    expression: str = ""
    conversion: Optional[str] = None
    format_spec: str = ""
    render_hints: str = ""
    value: Union[str, "StructuredPrompt"] = ""

    def __getitem__(self, key: str) -> "StructuredInterpolation":
        """
        Delegate dict-like access to nested StructuredPrompt if present.

        Parameters
        ----------
        key : str
            The key to look up in the nested prompt.

        Returns
        -------
        StructuredInterpolation
            The interpolation node from the nested prompt.

        Raises
        ------
        NotANestedPromptError
            If the value is not a StructuredPrompt.
        """
        if isinstance(self.value, StructuredPrompt):
            return self.value[key]
        raise NotANestedPromptError(self.key)

    def render(self) -> Union[str, "IntermediateRepresentation"]:
        """
        Render this interpolation node.

        If the value is a StructuredPrompt, returns an IntermediateRepresentation.
        If the value is a string, returns a string with conversions applied.

        Returns
        -------
        str | IntermediateRepresentation
            The rendered value of this interpolation.
        """
        if isinstance(self.value, StructuredPrompt):
            return self.value.render()
        else:
            out = self.value
            if self.conversion:
                # Type narrowing for convert - only valid conversion types
                conv: Literal["r", "s", "a"] = self.conversion  # type: ignore
                return convert(out, conv)
            return out

    def __repr__(self) -> str:
        """Return a helpful debug representation."""
        value_repr = "StructuredPrompt(...)" if isinstance(self.value, StructuredPrompt) else repr(self.value)
        return (
            f"StructuredInterpolation(key={self.key!r}, expression={self.expression!r}, "
            f"conversion={self.conversion!r}, format_spec={self.format_spec!r}, "
            f"render_hints={self.render_hints!r}, value={value_repr}, index={self.index})"
        )


@dataclass(frozen=True, slots=True)
class ListInterpolation(Element):
    """
    Immutable record of a list interpolation in a StructuredPrompt.

    Represents interpolations where the value is a list of StructuredPrompts.
    Stores the separator as a field for proper handling during rendering.

    Attributes
    ----------
    key : str
        The key used for dict-like access (parsed from format_spec or expression).
    parent : StructuredPrompt | None
        The parent StructuredPrompt that contains this interpolation.
    index : int
        The position of this element in the overall element sequence.
    source_location : SourceLocation | None
        Source code location information for this element (if available).
    expression : str
        The original expression text from the t-string (what was inside {}).
    conversion : str | None
        The conversion flag if present (!s, !r, !a), or None.
    format_spec : str
        The format specification string (everything after :), or empty string.
    render_hints : str
        Rendering hints parsed from format_spec (everything after first colon in format spec).
    items : list[StructuredPrompt]
        The list of StructuredPrompt items.
    separator : str
        The separator to use when joining items (parsed from render_hints, default "\n").
    """

    expression: str = ""
    conversion: Optional[str] = None
    format_spec: str = ""
    render_hints: str = ""
    items: list["StructuredPrompt"] = None  # type: ignore
    separator: str = "\n"

    def __getitem__(self, idx: int) -> "StructuredPrompt":
        """
        Access list items by index.

        Parameters
        ----------
        idx : int
            The index of the item to access.

        Returns
        -------
        StructuredPrompt
            The item at the given index.

        Raises
        ------
        IndexError
            If the index is out of bounds.
        """
        return self.items[idx]

    def __len__(self) -> int:
        """Return the number of items in the list."""
        return len(self.items)

    def __repr__(self) -> str:
        """Return a helpful debug representation."""
        return (
            f"ListInterpolation(key={self.key!r}, expression={self.expression!r}, "
            f"separator={self.separator!r}, items={len(self.items)}, index={self.index})"
        )


@dataclass(frozen=True, slots=True)
class ImageInterpolation(Element):
    """
    Immutable record of an image interpolation in a StructuredPrompt.

    Represents interpolations where the value is a PIL Image object.
    Cannot be rendered to text - raises ImageRenderError when attempting to render.

    Attributes
    ----------
    key : str
        The key used for dict-like access (parsed from format_spec or expression).
    parent : StructuredPrompt | None
        The parent StructuredPrompt that contains this interpolation.
    index : int
        The position of this element in the overall element sequence.
    source_location : SourceLocation | None
        Source code location information for this element (if available).
    expression : str
        The original expression text from the t-string (what was inside {}).
    conversion : str | None
        The conversion flag if present (!s, !r, !a), or None.
    format_spec : str
        The format specification string (everything after :), or empty string.
    render_hints : str
        Rendering hints parsed from format_spec (everything after first colon in format spec).
    value : Any
        The PIL Image object (typed as Any to avoid hard dependency on PIL).
    """

    expression: str = ""
    conversion: Optional[str] = None
    format_spec: str = ""
    render_hints: str = ""
    value: Any = None  # PIL Image type

    def __repr__(self) -> str:
        """Return a helpful debug representation."""
        return (
            f"ImageInterpolation(key={self.key!r}, expression={self.expression!r}, "
            f"value=<PIL.Image>, index={self.index})"
        )


def _serialize_source_location(source_location: Optional[SourceLocation]) -> Optional[dict[str, Any]]:
    """
    Serialize a SourceLocation to a JSON-compatible dict.

    Parameters
    ----------
    source_location : SourceLocation | None
        The source location to serialize.

    Returns
    -------
    dict[str, Any] | None
        Dictionary with filename, filepath, line if available, None otherwise.
    """
    if source_location is None or not source_location.is_available:
        return None
    return {
        "filename": source_location.filename,
        "filepath": source_location.filepath,
        "line": source_location.line,
    }


def _serialize_image(image: Any) -> dict[str, Any]:
    """
    Serialize a PIL Image to a JSON-compatible dict with base64 data and metadata.

    Parameters
    ----------
    image : PIL.Image.Image
        The PIL Image object to serialize.

    Returns
    -------
    dict[str, Any]
        Dictionary with base64_data, format, size (width, height), mode, and other metadata.
    """
    import base64
    import io

    if not HAS_PIL or PILImage is None:
        return {"error": "PIL not available"}

    try:
        # Get image metadata
        width, height = image.size
        mode = image.mode
        img_format = image.format or "PNG"  # Default to PNG if format not set

        # Encode image to base64
        buffer = io.BytesIO()
        image.save(buffer, format=img_format)
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "base64_data": base64_data,
            "format": img_format,
            "width": width,
            "height": height,
            "mode": mode,
        }
    except Exception as e:
        return {"error": f"Failed to serialize image: {e}"}


class StructuredPrompt(Mapping[str, Union[StructuredInterpolation, ListInterpolation, ImageInterpolation]]):
    """
    A provenance-preserving, navigable tree representation of a t-string.

    StructuredPrompt wraps a string.templatelib.Template (from a t-string)
    and provides dict-like access to its interpolations, preserving full
    provenance information (expression, conversion, format_spec, value).

    Attributes
    ----------
    metadata : dict[str, Any]
        Metadata dictionary for storing analysis results and other information.

    Parameters
    ----------
    template : Template
        The Template object from a t-string literal.
    allow_duplicate_keys : bool, optional
        If True, allows duplicate keys and provides get_all() for access.
        If False (default), raises DuplicateKeyError on duplicate keys.

    Raises
    ------
    UnsupportedValueTypeError
        If any interpolation value is not str, StructuredPrompt, or list[StructuredPrompt].
    DuplicateKeyError
        If duplicate keys are found and allow_duplicate_keys=False.
    EmptyExpressionError
        If an empty expression {} is encountered.
    """

    def __init__(
        self,
        template: Template,
        *,
        allow_duplicate_keys: bool = False,
        _processed_strings: Optional[tuple[str, ...]] = None,
        _source_location: Optional[SourceLocation] = None,
    ):
        self._template = template
        self._processed_strings = _processed_strings  # Dedented/trimmed strings if provided
        self._source_location = _source_location  # Source location for all elements in this prompt
        self._id = str(uuid.uuid4())  # Unique identifier for this StructuredPrompt
        self.metadata: dict[str, Any] = {}  # Metadata dictionary for storing analysis results
        # All elements (Static, StructuredInterpolation, ListInterpolation, ImageInterpolation)
        self._elements: list[Element] = []
        # Only interpolations
        self._interps: list[Union[StructuredInterpolation, ListInterpolation, ImageInterpolation]] = []
        self._allow_duplicates = allow_duplicate_keys

        # Index maps keys to interpolation indices (within _interps list)
        # If allow_duplicates, maps to list of indices; otherwise, maps to single index
        self._index: dict[str, Union[int, list[int]]] = {}

        self._build_nodes()

    def _build_nodes(self) -> None:
        """Build Element nodes (Static and StructuredInterpolation) from the template."""
        # Use processed strings if available (from dedenting), otherwise use original
        strings = self._processed_strings if self._processed_strings is not None else self._template.strings
        interpolations = self._template.interpolations

        element_idx = 0  # Overall position in element sequence
        interp_idx = 0  # Position within interpolations list

        # Interleave statics and interpolations
        for static_key, static_text in enumerate(strings):
            # Add static element
            static = Static(
                key=static_key,
                value=static_text,
                parent=self,
                index=element_idx,
                source_location=self._source_location,
            )
            self._elements.append(static)
            element_idx += 1

            # Add interpolation if there's one after this static
            if static_key < len(interpolations):
                itp = interpolations[static_key]

                # Parse format spec to extract key and render hints
                key, render_hints = _parse_format_spec(itp.format_spec, itp.expression)

                # Guard against empty keys
                if not key:
                    raise EmptyExpressionError()

                # Validate and extract value - create appropriate node type
                val = itp.value
                if isinstance(val, list):
                    # Check that all items in the list are StructuredPrompts
                    if not all(isinstance(item, StructuredPrompt) for item in val):
                        raise UnsupportedValueTypeError(key, type(val), itp.expression)

                    # Create ListInterpolation node
                    separator = _parse_separator(render_hints)
                    node = ListInterpolation(
                        key=key,
                        expression=itp.expression,
                        conversion=itp.conversion,
                        format_spec=itp.format_spec,
                        render_hints=render_hints,
                        items=val,
                        separator=separator,
                        parent=self,
                        index=element_idx,
                        source_location=self._source_location,
                    )
                elif HAS_PIL and PILImage and isinstance(val, PILImage.Image):
                    # Create ImageInterpolation node
                    node = ImageInterpolation(
                        key=key,
                        expression=itp.expression,
                        conversion=itp.conversion,
                        format_spec=itp.format_spec,
                        render_hints=render_hints,
                        value=val,
                        parent=self,
                        index=element_idx,
                        source_location=self._source_location,
                    )
                elif isinstance(val, StructuredPrompt) or isinstance(val, str):
                    # Create StructuredInterpolation node
                    node = StructuredInterpolation(
                        key=key,
                        expression=itp.expression,
                        conversion=itp.conversion,
                        format_spec=itp.format_spec,
                        render_hints=render_hints,
                        value=val,
                        parent=self,
                        index=element_idx,
                        source_location=self._source_location,
                    )
                else:
                    raise UnsupportedValueTypeError(key, type(val), itp.expression)

                self._interps.append(node)
                self._elements.append(node)
                element_idx += 1

                # Update index (maps string keys to positions in _interps list)
                if self._allow_duplicates:
                    if key not in self._index:
                        self._index[key] = []
                    self._index[key].append(interp_idx)  # type: ignore
                else:
                    if key in self._index:
                        raise DuplicateKeyError(key)
                    self._index[key] = interp_idx

                interp_idx += 1

    # Mapping protocol implementation

    def __getitem__(self, key: str) -> Union[StructuredInterpolation, ListInterpolation, ImageInterpolation]:
        """
        Get the interpolation node for the given key.

        Parameters
        ----------
        key : str
            The key to look up (derived from format_spec or expression).

        Returns
        -------
        StructuredInterpolation | ListInterpolation | ImageInterpolation
            The interpolation node for this key.

        Raises
        ------
        MissingKeyError
            If the key is not found.
        ValueError
            If allow_duplicate_keys=True and the key is ambiguous (use get_all instead).
        """
        if key not in self._index:
            raise MissingKeyError(key, list(self._index.keys()))

        idx = self._index[key]
        if isinstance(idx, list):
            if len(idx) > 1:
                raise ValueError(f"Ambiguous key '{key}' with {len(idx)} occurrences. Use get_all('{key}') instead.")
            idx = idx[0]

        return self._interps[idx]

    def __iter__(self) -> Iterable[str]:
        """Iterate over keys in insertion order."""
        seen = set()
        for node in self._interps:
            if node.key not in seen:
                yield node.key
                seen.add(node.key)

    def __len__(self) -> int:
        """Return the number of unique keys."""
        return len(set(node.key for node in self._interps))

    def get_all(self, key: str) -> list[Union[StructuredInterpolation, ListInterpolation, ImageInterpolation]]:
        """
        Get all interpolation nodes for a given key (for duplicate keys).

        Parameters
        ----------
        key : str
            The key to look up.

        Returns
        -------
        list[StructuredInterpolation | ListInterpolation | ImageInterpolation]
            List of all interpolation nodes with this key.

        Raises
        ------
        MissingKeyError
            If the key is not found.
        """
        if key not in self._index:
            raise MissingKeyError(key, list(self._index.keys()))

        idx = self._index[key]
        if isinstance(idx, list):
            return [self._interps[i] for i in idx]
        else:
            return [self._interps[idx]]

    # Properties for provenance

    @property
    def id(self) -> str:
        """Return the unique identifier for this StructuredPrompt."""
        return self._id

    @property
    def template(self) -> Template:
        """Return the original Template object."""
        return self._template

    @property
    def strings(self) -> tuple[str, ...]:
        """Return the static string segments from the template."""
        return self._template.strings

    @property
    def interpolations(self) -> tuple[Union[StructuredInterpolation, ListInterpolation, ImageInterpolation], ...]:
        """Return all interpolation nodes in order."""
        return tuple(self._interps)

    @property
    def elements(self) -> tuple[Element, ...]:
        """Return all elements (Static and StructuredInterpolation) in order."""
        return tuple(self._elements)

    # Rendering

    def render(
        self, _path: tuple[Union[str, int], ...] = (), max_header_level: int = 4, _header_level: int = 1
    ) -> IntermediateRepresentation:
        """
        Render this StructuredPrompt to an IntermediateRepresentation with source mapping.

        Creates source spans for both static text segments and interpolations.
        Conversions (!s, !r, !a) are always applied.
        Format specs are parsed as "key : render_hints".

        The IntermediateRepresentation is ideal for:
        - Structured optimization when approaching context limits
        - Debugging and auditing with full provenance
        - Future multi-modal transformations

        Parameters
        ----------
        _path : tuple[Union[str, int], ...]
            Internal parameter for tracking path during recursive rendering.
        max_header_level : int, optional
            Maximum header level for markdown headers (default: 4).
        _header_level : int
            Internal parameter for tracking current header nesting level.

        Returns
        -------
        IntermediateRepresentation
            Object containing the rendered text and source map.

        Raises
        ------
        ImageRenderError
            If the prompt contains any image interpolations.
        """
        # Check for images in interpolations (cannot render to text-only)
        has_images = any(isinstance(interp, ImageInterpolation) for interp in self._interps)
        if has_images:
            raise ImageRenderError()

        # For now, render everything to a single text chunk
        # TODO: Support multiple chunks for multi-modal output
        out_parts: list[str] = []
        source_map: list[SourceSpan] = []
        current_pos = 0
        chunk_index = 0  # All spans go in chunk 0 for text-only rendering

        # Iterate through all elements (Static and StructuredInterpolation)
        for element in self._elements:
            span_start = current_pos

            if isinstance(element, Static):
                # Render static element
                rendered_text = element.value
                out_parts.append(rendered_text)
                current_pos += len(rendered_text)

                # Create span for static (only if non-empty)
                if rendered_text:
                    source_map.append(
                        SourceSpan(
                            start=span_start,
                            end=current_pos,
                            key=element.key,
                            path=_path,
                            element_type="static",
                            chunk_index=chunk_index,
                            element_id=element.id,
                        )
                    )

            elif isinstance(element, ListInterpolation):
                # Render list interpolation element
                node = element

                # Parse render hints
                hints = _parse_render_hints(node.render_hints, node.key)

                # Determine next header level if header hint is present
                next_header_level = _header_level
                if "header" in hints:
                    next_header_level = _header_level + 1

                # Check if the preceding static has trailing whitespace on the same line
                # This will be used as base indentation for all list items after the first
                base_indent = ""
                if out_parts:
                    last_part = out_parts[-1]
                    if last_part and "\n" in last_part:
                        # Get text after last newline
                        lines = last_part.split("\n")
                        last_line = lines[-1]
                        # If it's all whitespace, it's the base indent for list items
                        if last_line and last_line.strip() == "":
                            base_indent = last_line

                # Calculate prefix length from render hints FIRST
                prefix_len = 0  # Track total prefix length for span adjustment

                if "xml" in hints:
                    xml_tag = hints["xml"]
                    xml_wrapper_start = f"<{xml_tag}>\n"
                    prefix_len += len(xml_wrapper_start)

                if "header" in hints:
                    level = min(_header_level, max_header_level)
                    header_prefix = "#" * level + " " + hints["header"] + "\n"
                    prefix_len += len(header_prefix)

                # Render each item and join with separator + base indent
                rendered_parts = []
                for item in node.items:
                    item_rendered = item.render(
                        _path=_path + (node.key,), max_header_level=max_header_level, _header_level=next_header_level
                    )
                    rendered_parts.append(item_rendered.text)
                    # Add nested source spans with offset
                    # Account for prefix from render hints AND separator/base_indent between items
                    if len(rendered_parts) == 1:
                        current_offset = span_start + prefix_len
                    else:
                        # Previous items + their separators and indents
                        prev_content_len = sum(len(p) for p in rendered_parts[:-1])
                        prev_seps_len = (len(rendered_parts) - 2) * (len(node.separator) + len(base_indent))
                        sep_and_indent_len = len(node.separator) + len(base_indent)
                        current_offset = span_start + prefix_len + prev_content_len + prev_seps_len + sep_and_indent_len

                    for nested_span in item_rendered.source_map:
                        source_map.append(
                            SourceSpan(
                                start=current_offset + nested_span.start,
                                end=current_offset + nested_span.end,
                                key=nested_span.key,
                                path=nested_span.path,
                                element_type=nested_span.element_type,
                                chunk_index=chunk_index,
                                element_id=nested_span.element_id,
                            )
                        )

                # Join with separator, adding base indent after each separator (except before first item)
                if base_indent and len(rendered_parts) > 1:
                    # First item has no prefix, subsequent items get separator + base_indent
                    rendered_text = rendered_parts[0]
                    for part in rendered_parts[1:]:
                        rendered_text += node.separator + base_indent + part
                else:
                    rendered_text = node.separator.join(rendered_parts)

                # Apply render hints (header first, then xml wrapper) to the entire list
                if "xml" in hints:
                    # Wrap with XML tags (inner wrapper)
                    xml_tag = hints["xml"]
                    xml_wrapper_start = f"<{xml_tag}>\n"
                    xml_wrapper_end = f"\n</{xml_tag}>"
                    rendered_text = xml_wrapper_start + rendered_text + xml_wrapper_end

                if "header" in hints:
                    # Prepend markdown header (outer wrapper)
                    level = min(_header_level, max_header_level)
                    header_prefix = "#" * level + " " + hints["header"] + "\n"
                    rendered_text = header_prefix + rendered_text

                # Adjust span start for all added content
                span_start += prefix_len

                # Update position
                current_pos += len(rendered_text)
                out_parts.append(rendered_text)

            elif isinstance(element, StructuredInterpolation):
                # Render interpolation element
                node = element

                # Parse render hints
                hints = _parse_render_hints(node.render_hints, node.key)

                # Determine if we need to increment header level for nested rendering
                next_header_level = _header_level
                if "header" in hints:
                    next_header_level = _header_level + 1

                # Get value (render recursively if nested)
                if isinstance(node.value, StructuredPrompt):
                    nested_rendered = node.value.render(
                        _path=_path + (node.key,), max_header_level=max_header_level, _header_level=next_header_level
                    )
                    rendered_text = nested_rendered.text
                    # Add nested source spans with updated paths
                    for nested_span in nested_rendered.source_map:
                        source_map.append(
                            SourceSpan(
                                start=span_start + nested_span.start,
                                end=span_start + nested_span.end,
                                key=nested_span.key,
                                path=nested_span.path,
                                element_type=nested_span.element_type,
                                chunk_index=chunk_index,
                                element_id=nested_span.element_id,
                            )
                        )
                else:
                    rendered_text = node.value
                    # Apply conversion if present
                    if node.conversion:
                        conv: Literal["r", "s", "a"] = node.conversion  # type: ignore
                        rendered_text = convert(rendered_text, conv)

                # Apply render hints (header first, then xml wrapper)
                prefix_len = 0  # Track total prefix length for span adjustment

                if "xml" in hints:
                    # Wrap with XML tags (inner wrapper)
                    xml_tag = hints["xml"]
                    xml_wrapper_start = f"<{xml_tag}>\n"
                    xml_wrapper_end = f"\n</{xml_tag}>"
                    rendered_text = xml_wrapper_start + rendered_text + xml_wrapper_end
                    prefix_len += len(xml_wrapper_start)

                if "header" in hints:
                    # Prepend markdown header (outer wrapper)
                    level = min(_header_level, max_header_level)
                    header_prefix = "#" * level + " " + hints["header"] + "\n"
                    rendered_text = header_prefix + rendered_text
                    prefix_len += len(header_prefix)

                # Adjust span start for all added content
                span_start += prefix_len

                # Add span for this interpolation
                current_pos += len(rendered_text)
                if not isinstance(node.value, StructuredPrompt):
                    # Only add direct span if not nested (nested spans are already added above)
                    source_map.append(
                        SourceSpan(
                            start=span_start,
                            end=current_pos,
                            key=node.key,
                            path=_path,
                            element_type="interpolation",
                            chunk_index=chunk_index,
                            element_id=element.id,
                        )
                    )

                out_parts.append(rendered_text)

        # Create a single text chunk with all the rendered text
        text = "".join(out_parts)
        chunks: list[Union[TextChunk, ImageChunk]] = [TextChunk(text=text, chunk_index=chunk_index)]

        return IntermediateRepresentation(chunks, source_map, self)

    def __str__(self) -> str:
        """Render to string (convenience for render().text)."""
        return self.render().text

    # Convenience methods for JSON export

    def to_values(self) -> dict[str, Any]:
        """
        Export a JSON-serializable dict of rendered values.

        Nested StructuredPrompts are recursively converted to dicts.

        Returns
        -------
        dict[str, Any]
            A dictionary mapping keys to rendered string values or nested dicts.
        """
        result = {}
        for node in self._interps:
            if isinstance(node, ListInterpolation):
                result[node.key] = [item.to_values() for item in node.items]
            elif isinstance(node, StructuredInterpolation):
                if isinstance(node.value, StructuredPrompt):
                    result[node.key] = node.value.to_values()
                else:
                    # Get rendered value for this node
                    rendered = node.render()
                    result[node.key] = rendered if isinstance(rendered, str) else rendered.text
        return result

    def to_provenance(self) -> dict[str, Any]:
        """
        Export a JSON-serializable dict with full provenance information.

        Returns
        -------
        dict[str, Any]
            A dictionary with 'strings' (the static segments) and 'nodes'
            (list of dicts with key, expression, conversion, format_spec, render_hints, value info,
            and source_location if available).
        """
        nodes_data = []
        for node in self._interps:
            node_dict = {
                "key": node.key,
                "expression": node.expression,
                "conversion": node.conversion,
                "format_spec": node.format_spec,
                "render_hints": node.render_hints,
                "index": node.index,
            }

            # Add source location if available
            if node.source_location is not None and node.source_location.is_available:
                node_dict["source_location"] = {
                    "filename": node.source_location.filename,
                    "filepath": node.source_location.filepath,
                    "line": node.source_location.line,
                }

            if isinstance(node, ListInterpolation):
                node_dict["value"] = [item.to_provenance() for item in node.items]
            elif isinstance(node, StructuredInterpolation):
                if isinstance(node.value, StructuredPrompt):
                    node_dict["value"] = node.value.to_provenance()
                else:
                    node_dict["value"] = node.value
            nodes_data.append(node_dict)

        return {"strings": list(self._template.strings), "nodes": nodes_data}

    def toJSON(self) -> dict[str, Any]:
        """
        Export complete structured prompt as hierarchical JSON tree.

        This method provides a comprehensive JSON representation optimized for analysis
        and traversal, using a natural tree structure with explicit children arrays and
        parent references.

        The output has a root structure with:
        1. **prompt_id**: UUID of the root StructuredPrompt
        2. **children**: Array of child elements, each with their own children if nested

        Each element includes:
        - **parent_id**: UUID of the parent element (enables upward traversal)
        - **children**: Array of nested elements (for nested_prompt and list types)

        Images are serialized as base64-encoded data with metadata (format, size, mode).

        Returns
        -------
        dict[str, Any]
            JSON-serializable dictionary with 'prompt_id' and 'children' keys.

        Examples
        --------
        >>> x = "value"
        >>> p = prompt(t"{x:x}")
        >>> data = p.toJSON()
        >>> data.keys()
        dict_keys(['prompt_id', 'children'])
        >>> len(data['children'])  # Static "", interpolation, static ""
        3
        """

        def _build_element_tree(element: Element, parent_id: str) -> dict[str, Any]:
            """Build JSON representation of a single element with its children."""
            base = {
                "type": "",  # Will be set below
                "id": element.id,
                "parent_id": parent_id,
                "key": element.key,
                "index": element.index,
                "source_location": _serialize_source_location(element.source_location),
            }

            if isinstance(element, Static):
                base["type"] = "static"
                base["value"] = element.value

            elif isinstance(element, StructuredInterpolation):
                base.update({
                    "expression": element.expression,
                    "conversion": element.conversion,
                    "format_spec": element.format_spec,
                    "render_hints": element.render_hints,
                })

                if isinstance(element.value, StructuredPrompt):
                    # Nested prompt - recurse
                    base["type"] = "nested_prompt"
                    base["prompt_id"] = element.value.id
                    base["children"] = _build_children_tree(element.value, element.id)
                else:
                    # String interpolation
                    base["type"] = "interpolation"
                    base["value"] = element.value

            elif isinstance(element, ListInterpolation):
                base["type"] = "list"
                base.update({
                    "expression": element.expression,
                    "conversion": element.conversion,
                    "format_spec": element.format_spec,
                    "render_hints": element.render_hints,
                    "separator": element.separator,
                })
                # Build array of child prompt structures
                base["children"] = [
                    {"prompt_id": item.id, "children": _build_children_tree(item, element.id)}
                    for item in element.items
                ]

            elif isinstance(element, ImageInterpolation):
                base["type"] = "image"
                base.update({
                    "expression": element.expression,
                    "conversion": element.conversion,
                    "format_spec": element.format_spec,
                    "render_hints": element.render_hints,
                    "image_data": _serialize_image(element.value),
                })

            return base

        def _build_children_tree(prompt: "StructuredPrompt", parent_id: str) -> list[dict[str, Any]]:
            """Build children array for a prompt."""
            return [_build_element_tree(elem, parent_id) for elem in prompt.elements]

        return {"prompt_id": self._id, "children": _build_children_tree(self, self._id)}

    def __repr__(self) -> str:
        """Return a helpful debug representation."""
        keys = ", ".join(repr(k) for k in list(self)[:3])
        if len(self) > 3:
            keys += ", ..."
        return f"StructuredPrompt(keys=[{keys}], num_interpolations={len(self._interps)})"


def prompt(
    template: Template,
    /,
    *,
    dedent: bool = False,
    trim_leading: bool = True,
    trim_empty_leading: bool = True,
    trim_trailing: bool = True,
    capture_source_location: bool = True,
    **opts,
) -> StructuredPrompt:
    """
    Build a StructuredPrompt from a t-string Template with optional dedenting.

    This is the main entry point for creating structured prompts. Supports automatic
    dedenting and trimming to make indented t-strings in source code more readable.

    Parameters
    ----------
    template : Template
        The Template object from a t-string literal (e.g., t"...").
    dedent : bool, optional
        If True, dedent all static text by the indent level of the first non-empty line.
        Default is False (no dedenting).
    trim_leading : bool, optional
        If True, remove the first line of the first static if it's whitespace-only
        and ends in a newline. Default is True.
    trim_empty_leading : bool, optional
        If True, remove empty lines (just newlines) after the first line in the
        first static. Default is True.
    trim_trailing : bool, optional
        If True, remove trailing newlines from the last static. Default is True.
    capture_source_location : bool, optional
        If True, capture source code location information for all elements.
        Default is True. Set to False to disable (improves performance).
    **opts
        Additional options passed to StructuredPrompt constructor
        (e.g., allow_duplicate_keys=True).

    Returns
    -------
    StructuredPrompt
        The structured prompt object.

    Raises
    ------
    TypeError
        If template is not a Template object.
    DedentError
        If dedenting fails due to invalid configuration or mixed tabs/spaces.

    Examples
    --------
    Basic usage:
    >>> instructions = "Always answer politely."
    >>> p = prompt(t"Obey {instructions:inst}")
    >>> str(p)
    'Obey Always answer politely.'
    >>> p['inst'].expression
    'instructions'

    With dedenting:
    >>> p = prompt(t\"\"\"
    ...     You are a helpful assistant.
    ...     Task: {task:t}
    ... \"\"\", dedent=True)
    >>> print(str(p))
    You are a helpful assistant.
    Task: ...

    Disable source location capture for performance:
    >>> p = prompt(t"Hello {name}", capture_source_location=False)
    """
    if not isinstance(template, Template):
        raise TypeError("prompt(...) requires a t-string Template")

    # Capture source location if enabled
    source_location = _capture_source_location() if capture_source_location else None

    # Apply dedenting/trimming if any are enabled
    if dedent or trim_leading or trim_empty_leading or trim_trailing:
        processed_strings = _process_dedent(
            template.strings,
            dedent=dedent,
            trim_leading=trim_leading,
            trim_empty_leading=trim_empty_leading,
            trim_trailing=trim_trailing,
        )
        # Create a new Template with processed strings
        # We need to pass the processed strings to StructuredPrompt
        return StructuredPrompt(
            template, _processed_strings=processed_strings, _source_location=source_location, **opts
        )

    return StructuredPrompt(template, _source_location=source_location, **opts)


def dedent(
    template: Template,
    /,
    *,
    trim_leading: bool = True,
    trim_empty_leading: bool = True,
    trim_trailing: bool = True,
    **opts,
) -> StructuredPrompt:
    """
    Build a StructuredPrompt from a t-string Template with dedenting enabled.

    This is a convenience function that forwards to `prompt()` with `dedent=True`.
    Use this when writing indented multi-line prompts to keep your source code
    readable while producing clean output without indentation.

    Parameters
    ----------
    template : Template
        The Template object from a t-string literal (e.g., t"...").
    trim_leading : bool, optional
        If True, remove the first line of the first static if it's whitespace-only
        and ends in a newline. Default is True.
    trim_empty_leading : bool, optional
        If True, remove empty lines (just newlines) after the first line in the
        first static. Default is True.
    trim_trailing : bool, optional
        If True, remove trailing newlines from the last static. Default is True.
    **opts
        Additional options passed to StructuredPrompt constructor
        (e.g., allow_duplicate_keys=True).

    Returns
    -------
    StructuredPrompt
        The structured prompt object with dedenting applied.

    Raises
    ------
    TypeError
        If template is not a Template object.
    DedentError
        If dedenting fails due to invalid configuration or mixed tabs/spaces.

    Examples
    --------
    >>> task = "translate to French"
    >>> p = dedent(t\"\"\"
    ...     You are a helpful assistant.
    ...     Task: {task:t}
    ...     Please respond.
    ... \"\"\")
    >>> print(str(p))
    You are a helpful assistant.
    Task: translate to French
    Please respond.
    """
    return prompt(
        template,
        dedent=True,
        trim_leading=trim_leading,
        trim_empty_leading=trim_empty_leading,
        trim_trailing=trim_trailing,
        **opts,
    )
