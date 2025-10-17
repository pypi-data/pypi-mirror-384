# ----------------------------------------------------------------------------
# Writable models that are used by batchUpdate requests.
# The purpose of these models is to prevent LLMs from 'seeing' readonly fields
# for types that are a part of the Document model AND the Request model.
#
# Writables are used by the batchUpdate request model and the optionality
# of fields may differ from the Document model. Addtionally, writables do not
# contain readonly fields.
#
# Enum writables have thier placeholder values removed.
# ----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_serializer

from arcade_google_docs.models.document import (
    Alignment,
    BaselineOffset,
    ContentDirection,
    NamedStyleType,
    SpacingMode,
    TabStopAlignment,
    Unit,
)


class BookmarkLinkWritable(BaseModel):
    model_config = ConfigDict(title="A reference to a bookmark in this document")
    id: str = Field(..., title="The ID of a bookmark in this document")
    tabId: str = Field(..., title="The ID of the tab in this document")


class HeadingLinkWritable(BaseModel):
    model_config = ConfigDict(title="A reference to a heading in this document")
    id: str = Field(..., title="The ID of a heading in this document")
    tabId: str = Field(..., title="The ID of the tab in this document")


class LinkWritable(BaseModel):
    class Url(BaseModel):
        url: str = Field(..., title="An external URL")

    class TabId(BaseModel):
        tabId: str = Field(..., title="The ID of a tab in this document")

    class BookmarkId(BaseModel):
        bookmarkId: str = Field(..., title="The ID of a bookmark in this document")

    class HeadingId(BaseModel):
        headingId: str = Field(..., title="The ID of a heading in this document")

    model_config = ConfigDict(
        title="A reference to another portion of a document or an external URL resource."
    )
    destination: (
        Url | TabId | BookmarkLinkWritable | HeadingLinkWritable | BookmarkId | HeadingId
    ) = Field(
        ...,
        title="The link destination",
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field destination

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("destination", None)
        if isinstance(self.destination, LinkWritable.Url):
            data["url"] = self.destination.url
        elif isinstance(self.destination, LinkWritable.TabId):
            data["tabId"] = self.destination.tabId
        elif isinstance(self.destination, BookmarkLinkWritable):
            data["bookmark"] = self.destination.model_dump(exclude_none=True)
        elif isinstance(self.destination, HeadingLinkWritable):
            data["heading"] = self.destination.model_dump(exclude_none=True)
        elif isinstance(self.destination, LinkWritable.BookmarkId):
            data["bookmarkId"] = self.destination.bookmarkId
        elif isinstance(self.destination, LinkWritable.HeadingId):
            data["headingId"] = self.destination.headingId
        return data


class WeightedFontFamilyWritable(BaseModel):
    model_config = ConfigDict(
        title="The font family and rendered weight of the text.",
    )
    fontFamily: str | None = Field(
        None,
        title=(
            "The font family of the text. The font family can be any font from the Font menu "
            "in Docs or from Google Fonts. If the font name is unrecognized, "
            "the text is rendered in Arial."
        ),
    )
    weight: int | None = Field(
        None,
        title=(
            "The weight of the font. This field can have any value that's a multiple of 100 "
            "between 100 and 900, inclusive. The default value is 400 (normal)."
        ),
        ge=100,
        le=900,
    )


class TextStyleWritable(BaseModel):
    model_config = ConfigDict(
        title=(
            "Represents the styling that can be applied to text."
            "Inherited text styles are represented as unset fields in this message. A text style's "
            "parent depends on where the text style is defined:\n"
            "- The TextStyle of text in a Paragraph inherits from the paragraph's corresponding "
            "named style type.\n"
            "- The TextStyle on a named style inherits from the normal text named style.\n"
            "- The TextStyle of the normal text named style inherits from the default text style "
            "in the Docs editor.\n"
            "- The TextStyle on a Paragraph element that's contained in a table may inherit its "
            "text style from the table style.\n"
            "If the text style does not inherit from a parent, unsetting fields will revert the "
            "style to a value matching the defaults in the Docs editor."
        ),
    )
    bold: bool | None = Field(None, title="Whether the text is rendered as bold")
    italic: bool | None = Field(None, title="Whether the text is rendered as italic")
    underline: bool | None = Field(None, title="Whether the text is rendered as underlined")
    strikethrough: bool | None = Field(None, title="Whether the text is rendered as struck through")
    smallCaps: bool | None = Field(
        None, title="Whether or not the text is in small capital letters."
    )
    backgroundColor: OptionalColorWritable | None = Field(
        None,
        title=(
            "The background color of the text. If set, the color is either an RGB color or "
            "transparent, depending on the color field."
        ),
    )
    foregroundColor: OptionalColorWritable | None = Field(
        None,
        title=(
            "The foreground color of the text. If set, the color is either an RGB color or "
            "transparent, depending on the color field."
        ),
    )
    fontSize: DimensionWritable | None = Field(
        None,
        title="The size of the text's font.",
    )
    weightedFontFamily: WeightedFontFamilyWritable | None = Field(
        None,
        title="The font family and rendered weight of the text.",
        description=(
            "If an update request specifies values for both weightedFontFamily and bold, the "
            "weightedFontFamily is applied first, then bold. If weightedFontFamily#weight is not "
            "set, it defaults to 400. If weightedFontFamily is set, then "
            "weightedFontFamily#fontFamily must also be set with a non-empty value. Otherwise, a "
            "400 bad request error is returned."
        ),
    )
    baselineOffset: BaselineOffset | None = Field(
        None,
        title="The text's vertical offset from its normal position..",
    )
    link: LinkWritable | None = Field(
        None,
        title=(
            "The hyperlink destination of the text. If unset, there's no link. Links are not "
            "inherited from parent text."
        ),
    )


class TableRowStyleWritable(BaseModel):
    model_config = ConfigDict(title="Styles that apply to a table row.")
    minRowHeight: DimensionWritable | None = Field(
        None,
        title=(
            "The minimum height of the row. The row will be rendered in the Docs editor at a "
            "height equal to or greater than this value in order to show all the content in the "
            "row's cells."
        ),
    )
    tableHeader: bool | None = Field(
        None,
        title="Whether the row is a table header",
    )
    preventOverflow: bool | None = Field(
        None, title="Whether the row cannot overflow across page or column boundaries."
    )


class TableColumnPropertiesWritable(BaseModel):
    model_config = ConfigDict(title="The properties of a column in a table.")
    widthType: WidthTypeWritable | None = Field(None, title="The width type of the column")
    width: DimensionWritable | None = Field(
        None,
        title="The width of the column. Set when the column's widthType is FIXED_WIDTH.",
    )


class WidthTypeWritable(str, Enum):
    EVENLY_DISTRIBUTED = "EVENLY_DISTRIBUTED"
    FIXED_WIDTH = "FIXED_WIDTH"


class TableCellStyleWritable(BaseModel):
    model_config = ConfigDict(
        title=(
            "The style of a TableCell. Inherited table cell styles are represented as unset fields "
            "in this message. A table cell style can inherit from the table's style."
        )
    )
    backgroundColor: OptionalColorWritable | None = Field(
        None,
        title="The background color of the table cell",
    )
    borderLeft: TableCellBorderWritable | None = Field(
        None,
        title="The border to the left of the table cell",
    )
    borderRight: TableCellBorderWritable | None = Field(
        None,
        title="The border to the right of the table cell",
    )
    borderTop: TableCellBorderWritable | None = Field(
        None,
        title="The border at the top of the table cell",
    )
    borderBottom: TableCellBorderWritable | None = Field(
        None,
        title="The border at the bottom of the table cell",
    )
    paddingLeft: DimensionWritable | None = Field(
        None,
        title="The padding at the left of the table cell",
    )
    paddingRight: DimensionWritable | None = Field(
        None,
        title="The padding at the right of the table cell",
    )
    paddingTop: DimensionWritable | None = Field(
        None,
        title="The padding at the top of the table cell",
    )
    paddingBottom: DimensionWritable | None = Field(
        None,
        title="The padding at the bottom of the table cell",
    )
    contentAlignment: ContentAlignmentWritable | None = Field(
        None,
        title=(
            "The alignment of the content in the table cell. The default alignment matches the "
            "alignment for newly created table cells in the Docs editor."
        ),
    )


class ContentAlignmentWritable(str, Enum):
    CONTENT_ALIGNMENT_UNSPECIFIED = "CONTENT_ALIGNMENT_UNSPECIFIED"
    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


class TableCellBorderWritable(BaseModel):
    model_config = ConfigDict(
        title=(
            "A border around a table cell. Table cell borders cannot be transparent. "
            "To hide a table cell border, make its width 0."
        )
    )
    color: OptionalColorWritable | None = Field(
        None,
        title="The color of the border. Table cell borders cannot be transparent",
    )
    width: DimensionWritable | None = Field(
        None,
        title="The width of the border. Table cell borders cannot be transparent",
    )
    dashStyle: DashStyleWritable | None = Field(None, title="The dash style of the border")


class DashStyleWritable(str, Enum):
    SOLID = "SOLID"
    DOT = "DOT"
    DASH = "DASH"


class SectionStyleWritable(BaseModel):
    model_config = ConfigDict(title="The styling that applies to a section.")
    columnProperties: list[SectionColumnPropertiesWritable] | None = Field(
        None,
        title=(
            "The section's columns properties. If empty, the section contains one column with "
            "the default properties in the Docs editor. A section can be updated to have no more "
            "than 3 columns."
        ),
    )
    columnSeparatorStyle: ColumnSeparatorStyleWritable | None = Field(
        None,
        title=(
            "The style of column separators. "
            "This style can be set even when there's one column in the section."
        ),
    )
    contentDirection: ContentDirectionWritable | None = Field(
        None,
        title=(
            "The content direction of the section. If unset, the value defaults to LEFT_TO_RIGHT."
        ),
    )
    marginTop: DimensionWritable | None = Field(
        None,
        title=(
            "The top margin of the section. "
            "If unset, the value defaults to marginTop from DocumentStyle."
        ),
    )
    marginBottom: DimensionWritable | None = Field(
        None,
        title=(
            "The bottom margin of the section. "
            "If unset, the value defaults to marginBottom from DocumentStyle."
        ),
    )
    marginRight: DimensionWritable | None = Field(
        None,
        title=(
            "The right margin of the section. "
            "If unset, the value defaults to marginRight from DocumentStyle."
        ),
    )
    marginLeft: DimensionWritable | None = Field(
        None,
        title=(
            "The left margin of the section. "
            "If unset, the value defaults to marginLeft from DocumentStyle."
        ),
    )
    marginHeader: DimensionWritable | None = Field(
        None,
        title=(
            "The header margin of the section. If unset, the value defaults to marginHeader "
            "from DocumentStyle. If updated, useCustomHeaderFooterMargins is set to true on "
            "DocumentStyle. The value of useCustomHeaderFooterMargins on DocumentStyle indicates "
            "if a header margin is being respected for this section."
        ),
    )
    marginFooter: DimensionWritable | None = Field(
        None,
        title=(
            "The footer margin of the section. If unset, the value defaults to marginFooter "
            "from DocumentStyle. If updated, useCustomHeaderFooterMargins is set to true on "
            "DocumentStyle. The value of useCustomHeaderFooterMargins on DocumentStyle indicates "
            "if a footer margin is being respected for this section"
        ),
    )
    useFirstPageHeaderFooter: bool | None = Field(
        None,
        title=(
            "Indicates whether to use the first page header / footer IDs for the first page of "
            "the section. If unset, it inherits from DocumentStyle's useFirstPageHeaderFooter "
            "for the first section. If the value is unset for subsequent sectors, "
            "it should be interpreted as false."
        ),
    )
    pageNumberStart: int | None = Field(
        None,
        title=(
            "The page number from which to start counting the number of pages for this section. "
            "If unset, page numbering continues from the previous section. If the value is unset "
            "in the first SectionBreak, refer to DocumentStyle's pageNumberStart."
        ),
    )
    flipPageOrientation: bool | None = Field(
        None,
        title=(
            "Indicates whether to flip the dimensions of DocumentStyle's pageSize for this "
            "section, which allows changing the page orientation between portrait and landscape. "
            "If unset, the value inherits from DocumentStyle's flipPageOrientation."
        ),
    )


class ColumnSeparatorStyleWritable(str, Enum):
    NONE = "NONE"
    BETWEEN_EACH_COLUMN = "BETWEEN_EACH_COLUMN"


class ContentDirectionWritable(str, Enum):
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
    RIGHT_TO_LEFT = "RIGHT_TO_LEFT"


class SectionColumnPropertiesWritable(BaseModel):
    model_config = ConfigDict(title="Properties that apply to a section's column.")
    paddingEnd: DimensionWritable = Field(..., title="The padding at the end of the column")


class ParagraphStyleWritable(BaseModel):
    model_config = ConfigDict(
        title=(
            "Styles that apply to a whole paragraph. "
            "Inherited paragraph styles are represented as unset fields in this message. "
            "A paragraph style's parent depends on where the paragraph style is defined:\n"
            "- The ParagraphStyle on a Paragraph inherits from the paragraph's corresponding named style type.\n"  # noqa: E501
            "- The ParagraphStyle on a named style inherits from the normal text named style.\n"
            "- The ParagraphStyle of the normal text named style inherits from the default paragraph style in the Docs editor.\n"  # noqa: E501
            "- The ParagraphStyle on a Paragraph element that's contained in a table may inherit its paragraph style from the table style.\n"  # noqa: E501
            "If the paragraph style does not inherit from a parent, unsetting fields will revert the style to a value matching the defaults in the Docs editor."  # noqa: E501
        )
    )

    namedStyleType: NamedStyleType | None = Field(
        None,
        title=("Named style type is applied before the other properties are updated."),
    )
    alignment: Alignment | None = Field(None, title="The text alignment for this paragraph.")
    lineSpacing: float | None = Field(
        None,
        title=(
            "The amount of space between lines, as a percentage of normal, where normal is "
            "represented as 100.0. If unset, the value is inherited from the parent."
        ),
    )
    direction: ContentDirection = Field(
        ContentDirection.LEFT_TO_RIGHT,
        title=(
            "The text direction of this paragraph. If unset, the value defaults to LEFT_TO_RIGHT"
        ),
    )
    spacingMode: SpacingMode | None = Field(None, title="The spacing mode for the paragraph.")
    spaceAbove: DimensionWritable | None = Field(
        None,
        title=(
            "The amount of extra space above the paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    spaceBelow: DimensionWritable | None = Field(
        None,
        title=(
            "The amount of extra space below the paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    borderBetween: ParagraphBorderWritable | None = Field(
        None,
        title=(
            "The border between this paragraph and the next and previous paragraphs. "
            "If unset, the value is inherited from the parent."
        ),
    )
    borderTop: ParagraphBorderWritable | None = Field(
        None,
        title=(
            "The border at the top of this paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    borderBottom: ParagraphBorderWritable | None = Field(
        None,
        title=(
            "The border at the bottom of this paragraph. "
            "If unset, the value is inherited from the parent"
        ),
    )
    borderLeft: ParagraphBorderWritable | None = Field(
        None,
        title=(
            "The border to the left of this paragraph. "
            "If unset, the value is inherited from the parent"
        ),
    )
    borderRight: ParagraphBorderWritable | None = Field(
        None,
        title=(
            "The border to the right of this paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    indentFirstLine: DimensionWritable | None = Field(
        None,
        title=(
            "The amount of indentation for the first line of the paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    indentStart: DimensionWritable | None = Field(
        None,
        title=(
            "The amount of indentation for the paragraph on the side that corresponds to the "
            "start of the text, based on the current paragraph direction. "
            "If unset, the value is inherited from the parent"
        ),
    )
    indentEnd: DimensionWritable | None = Field(
        None,
        title=(
            "The amount of indentation for the paragraph on the side that corresponds to the "
            "end of the text, based on the current paragraph direction. "
            "If unset, the value is inherited from the parent"
        ),
    )
    keepLinesTogether: bool | None = Field(
        None,
        title=(
            "Whether all lines of the paragraph should be laid out on the same page or column "
            "if possible. If unset, the value is inherited from the parent."
        ),
    )
    keepWithNext: bool | None = Field(
        None,
        title=(
            "Whether at least a part of this paragraph should be laid out on the same page or "
            "column as the next paragraph if possible. "
            "If unset, the value is inherited from the parent."
        ),
    )
    avoidWidowAndOrphan: bool | None = Field(
        None,
        title=(
            "Whether to avoid widows and orphans for the paragraph. "
            "If unset, the value is inherited from the parent."
        ),
    )
    shading: ShadingWritable | None = Field(
        None,
        title="The shading of the paragraph. If unset, the value is inherited from the parent.",
    )
    pageBreakBefore: bool | None = Field(
        None,
        title=(
            "Whether the current paragraph should always start at the beginning of a page. If "
            "unset, the value is inherited from the parent. Attempting to update pageBreakBefore "
            "for paragraphs in unsupported regions, including Table, Header, Footer and Footnote, "
            "can result in an invalid document state that returns a 400 bad request error."
        ),
    )


class ParagraphBorderWritable(BaseModel):
    model_config = ConfigDict(title="A border around a paragraph.")
    color: OptionalColorWritable = Field(..., title="The color of the border.")
    width: DimensionWritable = Field(..., title="The width of the border.")
    padding: DimensionWritable = Field(..., title="The padding of the border.")
    dashStyle: DashStyleWritable = Field(..., title="The dash style of the border.")


class TabStopWritable(BaseModel):
    model_config = ConfigDict(title="A tab stop within a paragraph.")
    offset: DimensionWritable = Field(..., title="The offset of the tab stop.")
    alignment: TabStopAlignment = Field(
        TabStopAlignment.START,
        title="The alignment of this tab stop. If unset, the value defaults to START.",
    )


class ShadingWritable(BaseModel):
    model_config = ConfigDict(title="The shading of a paragraph.")
    backgroundColor: OptionalColorWritable = Field(
        ..., title="The background color of this paragraph shading."
    )


class RangeWritable(BaseModel):
    segmentId: str | None = Field(
        None,
        title=(
            "The ID of the header, footer, or footnote that this range is contained in. "
            "An empty segment ID signifies the document's body."
        ),
    )
    startIndex: int = Field(
        ...,
        title="The zero-based start index of this range, in UTF-16 code units.",
        ge=0,
    )
    endIndex: int = Field(
        ...,
        title="The zero-based end index of this range, in UTF-16 code units.",
        ge=0,
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that contains this range. When omitted, the request applies to the first tab."
        ),
    )


class OptionalColorWritable(BaseModel):
    model_config = ConfigDict(title="The color of the text.")
    color: ColorWritable | None = Field(
        None,
        title=(
            "If set, this will be used as an opaque color. If unset, this represents a "
            "transparent color."
        ),
    )


class ColorWritable(BaseModel):
    model_config = ConfigDict(title="A solid color.")
    rgbColor: RgbColorWritable = Field(
        ...,
        title="The RGB color value",
    )


class RgbColorWritable(BaseModel):
    model_config = ConfigDict(title="An RGB color.")
    red: float = Field(
        ...,
        title="The red component of the color, from 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )
    green: float = Field(
        ...,
        title="The green component of the color, from 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )
    blue: float = Field(
        ...,
        title="The blue component of the color, from 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )


class DimensionWritable(BaseModel):
    model_config = ConfigDict(title="A magnitude in a single direction in the specified units.")
    magnitude: float = Field(
        ...,
        title="The magnitude.",
        ge=5.0,
    )
    unit: Unit = Field(..., title="The units for magnitude. A PT is 1/72 of an inch.")


class BackgroundWritable(BaseModel):
    model_config = ConfigDict(title="The background of the document.")
    color: OptionalColorWritable = Field(..., title="The background color.")


class SizeWritable(BaseModel):
    model_config = ConfigDict(title="A width and height")
    height: DimensionWritable = Field(..., title="The height of the object.")
    width: DimensionWritable = Field(..., title="The width of the object.")


class DocumentStyleWritable(BaseModel):
    model_config = ConfigDict(title="The styles to set on the document.")

    background: BackgroundWritable | None = Field(
        None,
        title=(
            "The background of the document. Documents cannot have a transparent background color."
        ),
    )
    useFirstPageHeaderFooter: bool | None = Field(
        None,
        title="Indicates whether to use the first page header / footer IDs for the first page.",
    )
    useEvenPageHeaderFooter: bool | None = Field(
        None,
        title="Indicates whether to use the even page header / footer IDs for the even pages.",
    )
    pageNumberStart: int | None = Field(
        None,
        title="The page number from which to start counting the number of pages.",
    )
    marginTop: DimensionWritable | None = Field(
        None,
        title=(
            "The top page margin. Updating the top page margin on the document style "
            "clears the top page margin on all section styles."
        ),
    )
    marginBottom: DimensionWritable | None = Field(
        None,
        title=(
            "The bottom page margin. Updating the bottom page margin on the document style "
            "clears the bottom page margin on all section styles."
        ),
    )
    marginRight: DimensionWritable | None = Field(
        None,
        title=(
            "The right page margin. Updating the right page margin on the document style "
            "clears the right page margin on all section styles. It may also cause columns "
            "to resize in all sections."
        ),
    )
    marginLeft: DimensionWritable | None = Field(
        None,
        title=(
            "The left page margin. Updating the left page margin on the document style "
            "clears the left page margin on all section styles. It may also cause columns "
            "to resize in all sections."
        ),
    )
    pageSize: SizeWritable | None = Field(
        None,
        title="The size of a page in the document.",
    )
    marginHeader: DimensionWritable | None = Field(
        None,
        title="The amount of space between the top of the page and the contents of the header.",
    )
    marginFooter: DimensionWritable | None = Field(
        None,
        title="The amount of space between the bottom of the page and the contents of the footer.",
    )
    flipPageOrientation: bool | None = Field(
        None,
        title=(
            "Optional. Indicates whether to flip the dimensions of the pageSize, "
            "which allows changing the page orientation between portrait and landscape."
        ),
    )
