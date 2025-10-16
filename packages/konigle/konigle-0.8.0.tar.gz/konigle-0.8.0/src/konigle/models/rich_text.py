"""
Pydantic models for EditorJS rich text content.

This module provides models for validating EditorJS block content format
used in blog posts and other rich text fields in the Konigle SDK.
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class HeadingBlockData(BaseModel):
    """Data structure for heading blocks."""

    text: str = Field(..., title="Text", description="The heading text")
    level: Optional[int] = Field(
        default=1, title="Level", description="Heading level (1-6)", ge=1, le=6
    )


class ParagraphBlockData(BaseModel):
    """Data structure for paragraph blocks."""

    text: str = Field(..., title="Text", description="The paragraph text")


class ListBlockData(BaseModel):
    """Data structure for list blocks."""

    items: List[str] = Field(
        ..., title="Items", description="List of text items"
    )
    style: Optional[Literal["ordered", "unordered"]] = Field(
        default="unordered", title="Style", description="List style"
    )


class ImageBlockData(BaseModel):
    """Data structure for image blocks."""

    url: str = Field(..., title="URL", description="Image URL")
    caption: Optional[str] = Field(
        default=None, title="Caption", description="Image caption"
    )
    alt: Optional[str] = Field(
        default=None,
        title="Alt Text",
        description="Alt text for accessibility",
    )


class QuoteBlockData(BaseModel):
    """Data structure for quote blocks."""

    text: str = Field(..., title="Text", description="The quote text")
    caption: Optional[str] = Field(
        default=None, title="Caption", description="Quote attribution"
    )


class CodeBlockData(BaseModel):
    """Data structure for code blocks."""

    code: str = Field(..., title="Code", description="The code content")
    languageCode: Optional[str] = Field(
        default=None,
        title="Language Code",
        description="Programming language identifier",
    )


class FactBlockData(BaseModel):
    """Data structure for fact blocks."""

    text: str = Field(..., title="Text", description="The fact text")
    title: Optional[str] = Field(
        default=None, title="Title", description="Fact title"
    )


class ButtonBlockData(BaseModel):
    """Data structure for button blocks."""

    text: str = Field(..., title="Text", description="Button text")
    url: str = Field(..., title="URL", description="Button URL")


class ChecklistItem(BaseModel):
    """Individual checklist item."""

    text: str = Field(..., title="Text", description="Item text")
    checked: bool = Field(
        ..., title="Checked", description="Whether item is checked"
    )


class ChecklistBlockData(BaseModel):
    """Data structure for checklist blocks."""

    items: List[ChecklistItem] = Field(
        ..., title="Items", description="List of checklist items"
    )


class TableBlockData(BaseModel):
    """Data structure for table blocks."""

    content: List[List[str]] = Field(
        ...,
        title="Content",
        description="Table content as 2D array of strings",
    )


class RawBlockData(BaseModel):
    """Data structure for raw HTML blocks."""

    html: str = Field(..., title="HTML", description="Raw HTML content")


class HeadingBlock(BaseModel):
    """Heading block model."""

    type: Literal["heading"] = Field(
        ..., title="Type", description="Block type"
    )
    data: HeadingBlockData = Field(..., title="Data", description="Block data")


class ParagraphBlock(BaseModel):
    """Paragraph block model."""

    type: Literal["paragraph"] = Field(
        ..., title="Type", description="Block type"
    )
    data: ParagraphBlockData = Field(
        ..., title="Data", description="Block data"
    )


class ListBlock(BaseModel):
    """List block model."""

    type: Literal["list"] = Field(..., title="Type", description="Block type")
    data: ListBlockData = Field(..., title="Data", description="Block data")


class ImageBlock(BaseModel):
    """Image block model."""

    type: Literal["image"] = Field(..., title="Type", description="Block type")
    data: ImageBlockData = Field(..., title="Data", description="Block data")


class QuoteBlock(BaseModel):
    """Quote block model."""

    type: Literal["quote"] = Field(..., title="Type", description="Block type")
    data: QuoteBlockData = Field(..., title="Data", description="Block data")


class CodeBlock(BaseModel):
    """Code block model."""

    type: Literal["code"] = Field(..., title="Type", description="Block type")
    data: CodeBlockData = Field(..., title="Data", description="Block data")


class FactBlock(BaseModel):
    """Fact block model."""

    type: Literal["fact"] = Field(..., title="Type", description="Block type")
    data: FactBlockData = Field(..., title="Data", description="Block data")


class ButtonBlock(BaseModel):
    """Button block model."""

    type: Literal["button"] = Field(
        ..., title="Type", description="Block type"
    )
    data: ButtonBlockData = Field(..., title="Data", description="Block data")


class ChecklistBlock(BaseModel):
    """Checklist block model."""

    type: Literal["checklist"] = Field(
        ..., title="Type", description="Block type"
    )
    data: ChecklistBlockData = Field(
        ..., title="Data", description="Block data"
    )


class TableBlock(BaseModel):
    """Table block model."""

    type: Literal["table"] = Field(..., title="Type", description="Block type")
    data: TableBlockData = Field(..., title="Data", description="Block data")


class DelimiterBlock(BaseModel):
    """Delimiter block model (no data required)."""

    type: Literal["delimiter"] = Field(
        ..., title="Type", description="Block type"
    )


class RawBlock(BaseModel):
    """Raw HTML block model."""

    type: Literal["raw"] = Field(..., title="Type", description="Block type")
    data: RawBlockData = Field(..., title="Data", description="Block data")


# Union type for all supported blocks
EditorJSBlock = Union[
    HeadingBlock,
    ParagraphBlock,
    ListBlock,
    ImageBlock,
    QuoteBlock,
    CodeBlock,
    FactBlock,
    ButtonBlock,
    ChecklistBlock,
    TableBlock,
    DelimiterBlock,
    RawBlock,
]


class EditorJSContent(BaseModel):
    """
    Top-level EditorJS content model.

    Validates the complete EditorJS format with all supported block types.
    """

    blocks: List[EditorJSBlock] = Field(
        ..., title="Blocks", description="List of EditorJS blocks"
    )
