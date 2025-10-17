"""
Implements all resources used by the 'Request' resource.
The resources are defined at https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/request
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_serializer

from arcade_google_docs.models.document import (
    SectionType,
)
from arcade_google_docs.models.document_writables import (
    DocumentStyleWritable,
    ParagraphStyleWritable,
    RangeWritable,
    SectionStyleWritable,
    SizeWritable,
    TableCellStyleWritable,
    TableColumnPropertiesWritable,
    TableRowStyleWritable,
    TextStyleWritable,
)


class EditRequestType(str, Enum):
    """Edit request types supported by the Google Docs batchUpdate endpoint.

    Does not include the following edit requests:
    - createHeader
    - createFooter
    - createFootnote
    - createNamedRange
    - deleteHeader
    - deleteFooter
    - deletePositionedObject
    - deleteNamedRange
    - replaceImage
    - replaceNamedRangeContent
    - insertInlineImage
    """

    REPLACE_ALL_TEXT = "replaceAllText"
    INSERT_TEXT = "insertText"
    UPDATE_TEXT_STYLE = "updateTextStyle"
    CREATE_PARAGRAPH_BULLETS = "createParagraphBullets"
    DELETE_PARAGRAPH_BULLETS = "deleteParagraphBullets"
    UPDATE_PARAGRAPH_STYLE = "updateParagraphStyle"
    DELETE_CONTENT_RANGE = "deleteContentRange"
    INSERT_TABLE = "insertTable"
    INSERT_TABLE_ROW = "insertTableRow"
    INSERT_TABLE_COLUMN = "insertTableColumn"
    DELETE_TABLE_ROW = "deleteTableRow"
    DELETE_TABLE_COLUMN = "deleteTableColumn"
    UPDATE_TABLE_COLUMN_PROPERTIES = "updateTableColumnProperties"
    UPDATE_TABLE_CELL_STYLE = "updateTableCellStyle"
    UPDATE_TABLE_ROW_STYLE = "updateTableRowStyle"
    PIN_TABLE_HEADER_ROWS = "pinTableHeaderRows"
    UPDATE_DOCUMENT_STYLE = "updateDocumentStyle"
    MERGE_TABLE_CELLS = "mergeTableCells"
    UNMERGE_TABLE_CELLS = "unmergeTableCells"
    UPDATE_SECTION_STYLE = "updateSectionStyle"
    INSERT_SECTION_BREAK = "insertSectionBreak"
    INSERT_PAGE_BREAK = "insertPageBreak"

    def is_location_based(self) -> bool:
        """Whether the request type needs to specify indices for the location of the edit"""
        location_based_requests_types = [
            EditRequestType.INSERT_TEXT,
            EditRequestType.INSERT_TABLE,
            EditRequestType.INSERT_TABLE_ROW,
            EditRequestType.INSERT_TABLE_COLUMN,
            EditRequestType.DELETE_TABLE_ROW,
            EditRequestType.DELETE_TABLE_COLUMN,
            EditRequestType.UPDATE_TABLE_CELL_STYLE,
            EditRequestType.MERGE_TABLE_CELLS,
            EditRequestType.UNMERGE_TABLE_CELLS,
            EditRequestType.INSERT_PAGE_BREAK,
            EditRequestType.UPDATE_TABLE_ROW_STYLE,
            EditRequestType.INSERT_SECTION_BREAK,
            EditRequestType.PIN_TABLE_HEADER_ROWS,
            EditRequestType.UPDATE_TEXT_STYLE,
            EditRequestType.CREATE_PARAGRAPH_BULLETS,
            EditRequestType.DELETE_PARAGRAPH_BULLETS,
            EditRequestType.UPDATE_PARAGRAPH_STYLE,
            EditRequestType.DELETE_CONTENT_RANGE,
            EditRequestType.UPDATE_SECTION_STYLE,
        ]
        return self in location_based_requests_types

    def is_style_or_formatting_edit(self) -> bool:
        """Whether the request type is a style or formatting edit.

        These types of edits can be safely batched together.
        """
        style_formatting_edits = [
            EditRequestType.UPDATE_TEXT_STYLE,
            EditRequestType.UPDATE_PARAGRAPH_STYLE,
            EditRequestType.UPDATE_TABLE_CELL_STYLE,
            EditRequestType.UPDATE_TABLE_ROW_STYLE,
            EditRequestType.UPDATE_TABLE_COLUMN_PROPERTIES,
            EditRequestType.UPDATE_SECTION_STYLE,
            EditRequestType.UPDATE_DOCUMENT_STYLE,
            EditRequestType.PIN_TABLE_HEADER_ROWS,
            EditRequestType.CREATE_PARAGRAPH_BULLETS,
            EditRequestType.DELETE_PARAGRAPH_BULLETS,
        ]
        return self in style_formatting_edits

    def get_precedence(self) -> int:
        """
        Returns the operation precedence for this edit request type.

        Lower numbers indicate edits that should come earlier in the batch.
        This is used for ordering edits to maintain document consistency.

        Returns:
            The precedence value (lower = earlier)
        """
        precedence_mapping = {
            # Document structure edits come first
            EditRequestType.INSERT_SECTION_BREAK: 10,
            EditRequestType.INSERT_PAGE_BREAK: 10,
            # Table structure edits
            EditRequestType.INSERT_TABLE: 20,
            EditRequestType.INSERT_TABLE_ROW: 30,
            EditRequestType.INSERT_TABLE_COLUMN: 30,
            EditRequestType.DELETE_TABLE_ROW: 35,
            EditRequestType.DELETE_TABLE_COLUMN: 35,
            # List/bullet removal before creation
            EditRequestType.DELETE_PARAGRAPH_BULLETS: 40,
            # Content insertion edits
            EditRequestType.REPLACE_ALL_TEXT: 45,  # Replace before styling
            EditRequestType.INSERT_TEXT: 50,
            # List/bullet creation after removal
            EditRequestType.CREATE_PARAGRAPH_BULLETS: 60,
            # Merge edits
            EditRequestType.MERGE_TABLE_CELLS: 70,
            # Style and formatting edits come later
            EditRequestType.UPDATE_TEXT_STYLE: 80,
            EditRequestType.UPDATE_PARAGRAPH_STYLE: 80,
            EditRequestType.UPDATE_TABLE_CELL_STYLE: 85,
            EditRequestType.UPDATE_TABLE_ROW_STYLE: 85,
            EditRequestType.UPDATE_TABLE_COLUMN_PROPERTIES: 85,
            EditRequestType.UPDATE_SECTION_STYLE: 85,
            EditRequestType.UPDATE_DOCUMENT_STYLE: 90,
            EditRequestType.PIN_TABLE_HEADER_ROWS: 90,
            # Unmerge operations
            EditRequestType.UNMERGE_TABLE_CELLS: 95,
            # Content removal edits come last
            EditRequestType.DELETE_CONTENT_RANGE: 100,
        }
        return precedence_mapping.get(self, 75)

    def get_request_model(self) -> type[BaseModel]:
        """
        Returns the corresponding Pydantic model class for this edit request.
        """
        mapping = {
            EditRequestType.REPLACE_ALL_TEXT: ReplaceAllTextRequest,
            EditRequestType.INSERT_TEXT: InsertTextRequest,
            EditRequestType.UPDATE_TEXT_STYLE: UpdateTextStyleRequest,
            EditRequestType.CREATE_PARAGRAPH_BULLETS: CreateParagraphBulletsRequest,
            EditRequestType.DELETE_PARAGRAPH_BULLETS: DeleteParagraphBulletsRequest,
            EditRequestType.UPDATE_PARAGRAPH_STYLE: UpdateParagraphStyleRequest,
            EditRequestType.DELETE_CONTENT_RANGE: DeleteContentRangeRequest,
            EditRequestType.INSERT_TABLE: InsertTableRequest,
            EditRequestType.INSERT_TABLE_ROW: InsertTableRowRequest,
            EditRequestType.INSERT_TABLE_COLUMN: InsertTableColumnRequest,
            EditRequestType.DELETE_TABLE_ROW: DeleteTableRowRequest,
            EditRequestType.DELETE_TABLE_COLUMN: DeleteTableColumnRequest,
            EditRequestType.INSERT_PAGE_BREAK: InsertPageBreakRequest,
            EditRequestType.UPDATE_TABLE_COLUMN_PROPERTIES: UpdateTableColumnPropertiesRequest,
            EditRequestType.UPDATE_TABLE_CELL_STYLE: UpdateTableCellStyleRequest,
            EditRequestType.UPDATE_TABLE_ROW_STYLE: UpdateTableRowStyleRequest,
            EditRequestType.UPDATE_DOCUMENT_STYLE: UpdateDocumentStyleRequest,
            EditRequestType.MERGE_TABLE_CELLS: MergeTableCellsRequest,
            EditRequestType.UNMERGE_TABLE_CELLS: UnmergeTableCellsRequest,
            EditRequestType.UPDATE_SECTION_STYLE: UpdateSectionStyleRequest,
            EditRequestType.INSERT_SECTION_BREAK: InsertSectionBreakRequest,
            EditRequestType.PIN_TABLE_HEADER_ROWS: PinTableHeaderRowsRequest,
        }
        return mapping[self]  # type: ignore[return-value]


class Request(BaseModel):
    """A request to edit a Google Document.

    Does not include the following requests:
    - createNamedRange
    - deleteNamedRange
    - insertInlineImage
    - deletePositionedObject
    - replaceImage
    - createHeader
    - createFooter
    - createFootnote
    - replaceNamedRangeContent
    - deleteHeader
    - deleteFooter
    """

    replaceAllText: ReplaceAllTextRequest | None = None
    insertText: InsertTextRequest | None = None
    updateTextStyle: UpdateTextStyleRequest | None = None
    createParagraphBullets: CreateParagraphBulletsRequest | None = None
    deleteParagraphBullets: DeleteParagraphBulletsRequest | None = None
    updateParagraphStyle: UpdateParagraphStyleRequest | None = None
    deleteContentRange: DeleteContentRangeRequest | None = None
    insertTable: InsertTableRequest | None = None
    insertTableRow: InsertTableRowRequest | None = None
    insertTableColumn: InsertTableColumnRequest | None = None
    deleteTableRow: DeleteTableRowRequest | None = None
    deleteTableColumn: DeleteTableColumnRequest | None = None
    insertPageBreak: InsertPageBreakRequest | None = None
    updateTableColumnProperties: UpdateTableColumnPropertiesRequest | None = None
    updateTableCellStyle: UpdateTableCellStyleRequest | None = None
    updateTableRowStyle: UpdateTableRowStyleRequest | None = None
    updateDocumentStyle: UpdateDocumentStyleRequest | None = None
    mergeTableCells: MergeTableCellsRequest | None = None
    unmergeTableCells: UnmergeTableCellsRequest | None = None
    updateSectionStyle: UpdateSectionStyleRequest | None = None
    insertSectionBreak: InsertSectionBreakRequest | None = None
    pinTableHeaderRows: PinTableHeaderRowsRequest | None = None


class ReplaceAllTextRequest(BaseModel):
    model_config = ConfigDict(
        title="Replaces all instances of text matching a criteria with replace text"
    )
    replaceText: str = Field(..., title="The text that will replace the matched text.")
    tabsCriteria: TabsCriteria | None = Field(
        None,
        title=(
            "Optional. The criteria used to specify in which tabs the replacement occurs. "
            "When omitted, the replacement applies to all tabs."
        ),
    )
    containsText: SubstringMatchCriteria = Field(
        ..., title="Finds text in the document matching this substring."
    )


class TabsCriteria(BaseModel):
    model_config = ConfigDict(title="A criteria that specifies in which tabs a request executes.")
    tabIds: list[str] = Field(
        ..., title="The list of tab IDs in which the request executes.", min_length=1
    )


class SubstringMatchCriteria(BaseModel):
    model_config = ConfigDict(
        title="A criteria that matches a specific string of text in the document."
    )
    text: str = Field(..., title="The text to search for in the document.")
    matchCase: bool = Field(
        ...,
        title=(
            "Indicates whether the search should respect case. "
            "True: the search is case sensitive. False: the search is case insensitive."
        ),
    )
    searchByRegex: bool | None = Field(
        None,
        title=(
            "Optional. True if the find value should be treated as a regular expression. "
            "Any backslashes in the pattern should be escaped. "
            "True: the search text is treated as a regular expression. "
            "False: the search text is treated as a substring for matching."
        ),
    )


class InsertTextRequest(BaseModel):
    model_config = ConfigDict(title="Inserts text at the specified location.")
    text: str = Field(
        ...,
        title=(
            "The text to be inserted. Inserting a newline character will implicitly create a new "
            "Paragraph at that index. The paragraph style of the new paragraph will be copied from "
            "the paragraph at the current insertion index, including lists and bullets. Text "
            "styles for inserted text will be determined automatically, generally preserving the "
            "styling "
            "of neighboring text. In most cases, the text style for the inserted text will match "
            "the text immediately before the insertion index. If your insertion is technically "
            "an 'append' to the end of a section, then this index should be equal to the "
            "'end index' of the section's range"
        ),
    )
    insertion_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field insertion_location. The location where the text will be inserted. "
            "insertion_location can be only one of the following: "
            "location — Text must be inserted inside the bounds of an existing Paragraph. "
            "For instance, text cannot be inserted at a table's start index "
            "(i.e. between the table and its preceding paragraph). "
            "The text must be inserted in the preceding paragraph. "
            "endOfSegmentLocation — Inserts the text at the end of a header, footer, footnote or "
            "the document body. Prefer this option when you want to 'append' text to the end of a "
            "section."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field insertion_location

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("insertion_location", None)
        if isinstance(self.insertion_location, Location):
            data["location"] = self.insertion_location.model_dump(exclude_none=True)
        elif isinstance(self.insertion_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.insertion_location.model_dump(exclude_none=True)
        return data


class Location(BaseModel):
    model_config = ConfigDict(title="A particular location in the document.")
    segmentId: str | None = Field(
        None,
        title="An empty segment ID signifies the document's body.",
    )
    index: int = Field(
        ...,
        title=(
            "The zero-based index. The index is relative to the beginning of the segment specified "
            "by segmentId. If your insertion is technically an 'append' to the end of a section, "
            "then this index should be equal to the 'end index' of the section's range"
        ),
        ge=0,
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that the location is in. "
            "When omitted, the request is applied to the first tab."
        ),
    )


class EndOfSegmentLocation(BaseModel):
    model_config = ConfigDict(
        title=(
            "Location at the end of a body, header, footer or footnote. "
            "The location is immediately before the last newline in the document segment."
        )
    )
    segmentId: str | None = Field(
        None,
        title=(
            "The ID of the header, footer or footnote the location is in. "
            "An empty segment ID signifies the document's body."
        ),
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that the location is in. "
            "When omitted, the request is applied to the first tab."
        ),
    )


class UpdateTextStyleFields(str, Enum):
    BOLD = "bold"
    ITALIC = "italic"
    UNDERLINE = "underline"
    STRIKETHROUGH = "strikethrough"
    SMALL_CAPS = "smallCaps"
    BACKGROUND_COLOR = "backgroundColor"
    FOREGROUND_COLOR = "foregroundColor"
    FONT_SIZE = "fontSize"
    FONT_FAMILY = "fontFamily"
    WEIGHT = "weight"
    BASELINE_OFFSET = "baselineOffset"
    LINK = "link"
    ALL = "*"


class UpdateTextStyleRequest(BaseModel):
    model_config = ConfigDict(title="Update the styling of text.")
    textStyle: TextStyleWritable = Field(
        ...,
        title=(
            "The styles to set on the text. If the value for a particular style matches that "
            "of the parent, that style will be set to inherit. Certain text style changes may "
            "cause other changes in order to mirror the behavior of the Docs editor. See the "
            "documentation of TextStyle for more information."
        ),
    )
    fields: list[UpdateTextStyleFields] = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "textStyle is implied and should not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example, to update the text style to bold, "
            "set fields to 'bold'. To reset a property to its default value, include its field "
            "name in the field mask but leave the field itself unset."
        ),
    )
    range: RangeWritable = Field(
        ...,
        title=(
            "The range of text to style. The range may be extended to include adjacent newlines. "
            "If the range fully contains a paragraph belonging to a list, the paragraph's bullet "
            "is also updated with the matching text style. Ranges cannot be inserted inside a "
            "relative UpdateTextStyleRequest."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_fields(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field 'fields'
        to a comma-separated string.

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("fields", None)
        if all(isinstance(field, UpdateTextStyleFields) for field in self.fields):
            if UpdateTextStyleFields.ALL in self.fields:
                data["fields"] = "*"
            else:
                data["fields"] = ",".join([field.value for field in self.fields])
        return data


class CreateParagraphBulletsRequest(BaseModel):
    model_config = ConfigDict(
        title=(
            "Creates bullets for all of the paragraphs that overlap with the given range. The "
            "nesting level is determined by leading tabs, which are removed to avoid excess space."
        )
    )
    range: RangeWritable = Field(
        ...,
        title="The range to apply the bullet preset to.",
    )
    bulletPreset: BulletGlyphPreset = Field(
        ...,
        title="The kinds of bullet glyphs to be used.",
    )


class BulletGlyphPreset(str, Enum):
    BULLET_GLYPH_PRESET_UNSPECIFIED = "BULLET_GLYPH_PRESET_UNSPECIFIED"
    BULLET_DISC_CIRCLE_SQUARE = "BULLET_DISC_CIRCLE_SQUARE"
    BULLET_DIAMONDX_ARROW3D_SQUARE = "BULLET_DIAMONDX_ARROW3D_SQUARE"
    BULLET_CHECKBOX = "BULLET_CHECKBOX"
    BULLET_ARROW_DIAMOND_DISC = "BULLET_ARROW_DIAMOND_DISC"
    BULLET_STAR_CIRCLE_SQUARE = "BULLET_STAR_CIRCLE_SQUARE"
    BULLET_ARROW3D_CIRCLE_SQUARE = "BULLET_ARROW3D_CIRCLE_SQUARE"
    BULLET_LEFTTRIANGLE_DIAMOND_DISC = "BULLET_LEFTTRIANGLE_DIAMOND_DISC"
    BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE = "BULLET_DIAMONDX_HOLLOWDIAMOND_SQUARE"
    BULLET_DIAMOND_CIRCLE_SQUARE = "BULLET_DIAMOND_CIRCLE_SQUARE"
    NUMBERED_DECIMAL_ALPHA_ROMAN = "NUMBERED_DECIMAL_ALPHA_ROMAN"
    NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS = "NUMBERED_DECIMAL_ALPHA_ROMAN_PARENS"
    NUMBERED_DECIMAL_NESTED = "NUMBERED_DECIMAL_NESTED"
    NUMBERED_UPPERALPHA_ALPHA_ROMAN = "NUMBERED_UPPERALPHA_ALPHA_ROMAN"
    NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL = "NUMBERED_UPPERROMAN_UPPERALPHA_DECIMAL"
    NUMBERED_ZERODECIMAL_ALPHA_ROMAN = "NUMBERED_ZERODECIMAL_ALPHA_ROMAN"


class DeleteParagraphBulletsRequest(BaseModel):
    model_config = ConfigDict(
        title=(
            "Deletes bullets from all of the paragraphs that overlap with the given range. "
            "The nesting level is visually preserved by adding indent to the start of the "
            "paragraph."
        )
    )
    range: RangeWritable = Field(
        ...,
        title="The range to delete bullets from.",
    )


class CreateNamedRangeRequest(BaseModel):
    model_config = ConfigDict(title="Creates a NamedRange referencing the given range.")
    name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        title=(
            "The name of the NamedRange. Names do not need to be unique. Names must be at least "
            "1 character and no more than 256 characters (UTF-16 code units)."
        ),
    )
    range: RangeWritable = Field(
        ...,
        title="The range to apply the name to.",
    )


class DeleteNamedRangeRequest(BaseModel):
    class NameRangeId(BaseModel):
        model_config = ConfigDict(title="The ID of the named range to delete.")
        namedRangeId: str = Field(
            ...,
            title="The ID of the named range to delete.",
        )

    class Name(BaseModel):
        model_config = ConfigDict(title="The name of the range(s) to delete.")
        name: str = Field(
            ...,
            title="The name of the range(s) to delete.",
        )

    model_config = ConfigDict(title="Deletes a NamedRange.")
    tabsCriteria: TabsCriteria | None = Field(
        None,
        title=(
            "Optional. The criteria used to specify which tab(s) "
            "the range deletion should occur in. "
            "When omitted, the range deletion is applied to all tabs."
        ),
    )
    named_range_reference: NameRangeId | Name = Field(
        ...,
        title=(
            "Union field named_range_reference. "
            "The value that determines which range or ranges to delete. Exactly one must be set. "
            "named_range_reference can be only one of the following:\n"
            "namedRangeId - The ID of the named range to delete.\n"
            "name - The name of the range(s) to delete. All named ranges with the given name will be deleted."  # noqa: E501
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field named_range_reference

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("named_range_reference", None)
        # Add the API-expected field based on the concrete type
        if isinstance(self.named_range_reference, ReplaceNamedRangeContentRequest.NamedRangeIdRef):
            data["namedRangeId"] = self.named_range_reference.namedRangeId
        elif isinstance(
            self.named_range_reference, ReplaceNamedRangeContentRequest.NamedRangeNameRef
        ):
            data["name"] = self.named_range_reference.namedRangeName
        return data


class UpdateParagraphStyleRequest(BaseModel):
    model_config = ConfigDict(
        title="Update the styling of all paragraphs that overlap with the given range."
    )
    paragraphStyle: ParagraphStyleWritable = Field(
        ...,
        title=(
            "The styles to set on the paragraphs. Certain paragraph style changes may cause other "
            "changes in order to mirror the behavior of the Docs editor. See the documentation of "
            "ParagraphStyle for more information."
        ),
    )
    # TODO: Create a UpdateParagraphStyleFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "paragraphStyle is implied and should not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example, to update the paragraph style's "
            "alignment property, set fields to 'alignment'. To reset a property to its default "
            "value, include its field name in the field mask but leave the field itself unset."
        ),
    )
    range: RangeWritable = Field(
        ...,
        title=("The range overlapping the paragraphs to style."),
    )


class DeleteContentRangeRequest(BaseModel):
    model_config = ConfigDict(title="Deletes content from the document.")
    range: RangeWritable = Field(
        ...,
        title=(
            "The range of content to delete. Deleting text that crosses a paragraph boundary may "
            "result in changes to paragraph styles, lists, positioned objects and bookmarks as the "
            "two paragraphs are merged. Attempting to delete certain ranges can result in an "
            "invalid document structure."
        ),
    )


class InsertInlineImageRequest(BaseModel):
    model_config = ConfigDict(
        title="Inserts an InlineObject containing an image at the given location."
    )
    uri: str = Field(
        ...,
        title=(
            "The image URI. The image is fetched once at insertion time and a copy is stored for "
            "display inside the document. Must be publicly accessible and <= 2 kB."
        ),
    )
    objectSize: SizeWritable | None = Field(
        None,
        title=(
            "The size the image should appear as in the document. If neither width nor height is "
            "specified, a default size is calculated. If one dimension is specified, the other is "
            "calculated to preserve aspect ratio. If both are specified, the image is scaled to "
            "fit within provided dimensions while maintaining aspect ratio."
        ),
    )
    insertion_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field insertion_location. The location where the image will be inserted. "
            "location — Inserts at a specific index inside an existing Paragraph. "
            "endOfSegmentLocation — Inserts at the end of a header, footer or the body."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field insertion_location

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("insertion_location", None)
        if isinstance(self.insertion_location, Location):
            data["location"] = self.insertion_location.model_dump(exclude_none=True)
        elif isinstance(self.insertion_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.insertion_location.model_dump(exclude_none=True)
        return data


class InsertTableRequest(BaseModel):
    model_config = ConfigDict(title="Inserts a table at the specified location.")
    rows: int = Field(
        ...,
        ge=1,
        title="The number of rows in the table.",
    )
    columns: int = Field(
        ...,
        ge=1,
        title="The number of columns in the table.",
    )
    insertion_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field insertion_location. The location where the table will be inserted. "
            "location — Inserts at a specific model index (table start index will be location+1). "
            "endOfSegmentLocation — Inserts at the end of the given header, footer or body."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field insertion_location

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("insertion_location", None)
        if isinstance(self.insertion_location, Location):
            data["location"] = self.insertion_location.model_dump(exclude_none=True)
        elif isinstance(self.insertion_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.insertion_location.model_dump(exclude_none=True)
        return data


class InsertTableRowRequest(BaseModel):
    model_config = ConfigDict(title="Inserts an empty row into a table.")
    tableCellLocation: TableCellLocation = Field(
        ...,
        title=("The reference table cell location from which rows will be inserted."),
    )
    insertBelow: bool = Field(
        ...,
        title=(
            "Whether to insert the new row below the reference cell location. "
            "True: below, False: above."
        ),
    )


class TableCellLocation(BaseModel):
    model_config = ConfigDict(title="Location of a single cell within a table.")
    tableStartLocation: Location = Field(
        ...,
        title="The location where the table starts in the document.",
    )
    rowIndex: int = Field(
        ...,
        ge=0,
        title=("The zero-based row index. For example, the second row has a row index of 1."),
    )
    columnIndex: int = Field(
        ...,
        ge=0,
        title=(
            "The zero-based column index. For example, the second column has a column index of 1."
        ),
    )


class InsertTableColumnRequest(BaseModel):
    model_config = ConfigDict(title="Inserts an empty column into a table.")
    tableCellLocation: TableCellLocation = Field(
        ...,
        title=("The reference table cell location from which columns will be inserted."),
    )
    insertRight: bool = Field(
        ...,
        title=(
            "Whether to insert the new column to the right of the reference cell location. "
            "True: right, False: left."
        ),
    )


class DeleteTableRowRequest(BaseModel):
    model_config = ConfigDict(title="Deletes a row from a table.")
    tableCellLocation: TableCellLocation = Field(
        ...,
        title=("The reference table cell location from which the row will be deleted."),
    )


class DeleteTableColumnRequest(BaseModel):
    model_config = ConfigDict(title="Deletes a column from a table.")
    tableCellLocation: TableCellLocation = Field(
        ...,
        title=("The reference table cell location from which the column will be deleted."),
    )


class InsertPageBreakRequest(BaseModel):
    model_config = ConfigDict(
        title="Inserts a page break followed by a newline at the specified location."
    )
    insertion_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field insertion_location. The location where the page break will be inserted. "
            "location — Inserts at a specific index inside an existing Paragraph; cannot be inside "
            "a table, equation, footnote, header or footer. Segment ID must be empty (body only). "
            "endOfSegmentLocation — Inserts at the end of the document body; cannot be inside a "
            "footnote, header or footer. Segment ID must be empty (body only)."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field insertion_location

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("insertion_location", None)
        if isinstance(self.insertion_location, Location):
            data["location"] = self.insertion_location.model_dump(exclude_none=True)
        elif isinstance(self.insertion_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.insertion_location.model_dump(exclude_none=True)
        return data


class DeletePositionedObjectRequest(BaseModel):
    model_config = ConfigDict(title="Deletes a PositionedObject from the document.")
    objectId: str = Field(
        ...,
        title="The ID of the positioned object to delete.",
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that the positioned object to delete is in. When omitted, the request is "
            "applied to the first tab."
        ),
    )


class UpdateTableColumnPropertiesRequest(BaseModel):
    model_config = ConfigDict(title="Updates the TableColumnProperties of columns in a table.")
    tableStartLocation: Location = Field(
        ...,
        title="The location where the table starts in the document.",
    )
    columnIndices: list[int] | None = Field(
        None,
        title=(
            "The list of zero-based column indices whose property should be updated. If no indices "
            "are specified, all columns will be updated."
        ),
    )
    tableColumnProperties: TableColumnPropertiesWritable = Field(
        ...,
        title=(
            "The table column properties to update. If width is less than 5 points, a 400 error "
            "is returned."
        ),
    )
    # TODO: Create a UpdateTableColumnPropertiesFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. Allowed: "
            '"width", "widthType", or "*". Use comma-separated list for multiple, e.g., '
            '"width,widthType".'
        ),
    )


class UpdateTableCellStyleRequest(BaseModel):
    model_config = ConfigDict(title="Updates the style of a range of table cells.")
    tableCellStyle: TableCellStyleWritable = Field(
        ...,
        title=(
            "The style to set on the table cells. When updating borders, adjacent shared borders "
            "are updated as well; merged and invisible borders are not updated."
        ),
    )
    # TODO: Create a UpdateTableCellStyleFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "tableCellStyle is implied and should not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example to update the table cell background "
            "color, set fields to 'backgroundColor'. To reset a property to its default value, "
            "include its field name in the field mask but leave the field itself unset."
        ),
    )
    cells: TableRange | Location = Field(
        ...,
        title=(
            "Union field cells. The cells which will be updated. "
            "tableRange — The subset of the table to which the updates are applied. "
            "tableStartLocation — The location where the table starts; applies updates to all "
            "cells in the table."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field cells

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("cells", None)
        if isinstance(self.cells, TableRange):
            data["tableRange"] = self.cells.model_dump(exclude_none=True)
        elif isinstance(self.cells, Location):
            data["tableStartLocation"] = self.cells.model_dump(exclude_none=True)
        return data


class TableRange(BaseModel):
    model_config = ConfigDict(title="A table range represents a reference to a subset of a table.")
    tableCellLocation: TableCellLocation = Field(
        ...,
        title="The cell location where the table range starts.",
    )
    rowSpan: int = Field(
        ...,
        title="The row span of the table range.",
    )
    columnSpan: int = Field(
        ...,
        title="The column span of the table range.",
    )


class UpdateTableRowStyleRequest(BaseModel):
    model_config = ConfigDict(title="Updates the TableRowStyle of rows in a table.")
    tableStartLocation: Location = Field(
        ...,
        title="The location where the table starts in the document.",
    )
    rowIndices: list[int] | None = Field(
        None,
        title=(
            "The list of zero-based row indices whose style should be updated. If no indices "
            "are specified, all rows will be updated."
        ),
    )
    tableRowStyle: TableRowStyleWritable = Field(
        ...,
        title="The styles to be set on the rows.",
    )
    # TODO: Create a UpdateTableRowStyleFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "tableRowStyle is implied and should not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example to update the minimum row height, "
            "set fields to 'minRowHeight'."
        ),
    )


class ImageReplaceMethod(str, Enum):
    CENTER_CROP = "CENTER_CROP"


class ReplaceImageRequest(BaseModel):
    model_config = ConfigDict(title="Replaces an existing image with a new image.")
    imageObjectId: str = Field(
        ...,
        title=(
            "The ID of the existing image that will be replaced. The ID can be retrieved from a "
            "get response."
        ),
    )
    uri: str = Field(
        ...,
        title=(
            "The URI of the new image. Must be publicly accessible and <= 2 kB. Images must be < "
            "50MB, <= 25 megapixels, and in PNG, JPEG, or GIF format."
        ),
    )
    imageReplaceMethod: ImageReplaceMethod = Field(ImageReplaceMethod.CENTER_CROP)
    tabId: str | None = Field(
        None,
        title=(
            "The tab that the image to be replaced is in. When omitted, the request applies to the "
            "first tab."
        ),
    )


class UpdateDocumentStyleRequest(BaseModel):
    model_config = ConfigDict(title="Updates the DocumentStyle.")
    documentStyle: DocumentStyleWritable = Field(
        ...,
        title=(
            "The styles to set on the document. Certain style changes may cause other changes to "
            "mirror Docs editor behavior. See DocumentStyle docs for details."
        ),
    )
    # TODO: Create a UpdateDocumentStyleFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "documentStyle is implied and should not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example to update the background, set fields "
            "to 'background'."
        ),
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that contains the style to update. When omitted, the request applies to the "
            "first tab."
        ),
    )


class MergeTableCellsRequest(BaseModel):
    model_config = ConfigDict(title="Merges cells in a Table.")
    tableRange: TableRange = Field(
        ...,
        title=(
            "The table range specifying which cells of the table to merge. Text is concatenated "
            "into the 'head' cell of the range. The 'head' cell is the upper-left cell of the "
            "range when the content direction is left to right, and the upper-right cell "
            "of the range otherwise."
        ),
    )


class UnmergeTableCellsRequest(BaseModel):
    model_config = ConfigDict(title="Unmerges cells in a Table.")
    tableRange: TableRange = Field(
        ...,
        title=(
            "The table range specifying which cells of the table to unmerge. If there is text in "
            "any of the merged cells, the text will remain in the 'head' cell of the resulting "
            "block of unmerged cells. The 'head' cell is the upper-left cell when the content "
            "direction is from left to right, and the upper-right otherwise."
        ),
    )


class CreateHeaderRequest(BaseModel):
    model_config = ConfigDict(title="Creates a Header.")
    type: HeaderFooterType = Field(
        ...,
        title="The type of header to create.",
    )
    sectionBreakLocation: Location | None = Field(
        None,
        title=(
            "The location of the SectionBreak which begins the section "
            "this header should belong to. "
            "If unset or if it refers to the first section break in the document body, the header "
            "applies to the DocumentStyle."
        ),
    )


class HeaderFooterType(str, Enum):
    HEADER_FOOTER_TYPE_UNSPECIFIED = "HEADER_FOOTER_TYPE_UNSPECIFIED"
    DEFAULT = "DEFAULT"


class CreateFooterRequest(BaseModel):
    model_config = ConfigDict(title="Creates a Footer.")
    type: HeaderFooterType = Field(
        ...,
        title="The type of footer to create.",
    )
    sectionBreakLocation: Location | None = Field(
        None,
        title=(
            "The location of the SectionBreak immediately preceding the section whose SectionStyle "
            "this footer should belong to. If unset or refers to the first section break in the "
            "document, the footer applies to the DocumentStyle."
        ),
    )


class CreateFootnoteRequest(BaseModel):
    model_config = ConfigDict(
        title=(
            "Creates a Footnote segment and inserts a new FootnoteReference to it at the given "
            "location. The new Footnote segment will contain a space followed by a newline."
        )
    )
    footnote_reference_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field footnote_reference_location. "
            "The location to insert the footnote reference. "
            "location — Inserts at a specific index inside an existing Paragraph; cannot be inside "
            "a table's start index. Footnote references cannot be inside an equation, header, "
            "footer or footnote. Segment ID must be empty (body only). "
            "endOfSegmentLocation — Inserts at the end of the document body; cannot be inside a "
            "header, footer or footnote. Segment ID must be empty (body only)."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field
        footnote_reference_location.

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("footnote_reference_location", None)
        if isinstance(self.footnote_reference_location, Location):
            data["location"] = self.footnote_reference_location.model_dump(exclude_none=True)
        elif isinstance(self.footnote_reference_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.footnote_reference_location.model_dump(
                exclude_none=True
            )
        return data


class ReplaceNamedRangeContentRequest(BaseModel):
    model_config = ConfigDict(
        title=(
            "Replaces the contents of the specified NamedRange or NamedRanges with the given "
            "replacement content. For NamedRanges with multiple discontinuous ranges, only the "
            "first is replaced; others are deleted."
        )
    )
    tabsCriteria: TabsCriteria | None = Field(
        None,
        title=(
            "Optional. The criteria used to specify in which tabs the replacement occurs. When "
            "omitted, the replacement applies to all tabs."
        ),
    )
    text: str = Field(
        ...,
        title=("Replaces the content of the specified named range(s) with the given text."),
    )

    class NamedRangeIdRef(BaseModel):
        namedRangeId: str = Field(
            ...,
            title="The ID of the named range whose content will be replaced.",
        )

    class NamedRangeNameRef(BaseModel):
        namedRangeName: str = Field(
            ...,
            title=(
                "The name of the NamedRanges whose content will be replaced. "
                "Multiple ranges with the same name will all be replaced; "
                "if none exist, the request is a no-op."
            ),
        )

    named_range_reference: NamedRangeIdRef | NamedRangeNameRef = Field(
        ...,
        title=(
            "Union field named_range_reference. "
            "A reference to the named range(s) whose content will be replaced. "
            "Exactly one of the following must be set: namedRangeId or namedRangeName."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field named_range_reference

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("named_range_reference", None)
        if isinstance(self.named_range_reference, ReplaceNamedRangeContentRequest.NamedRangeIdRef):
            data["namedRangeId"] = self.named_range_reference.namedRangeId
        elif isinstance(
            self.named_range_reference, ReplaceNamedRangeContentRequest.NamedRangeNameRef
        ):
            data["namedRangeName"] = self.named_range_reference.namedRangeName
        return data


class UpdateSectionStyleRequest(BaseModel):
    model_config = ConfigDict(title="Updates the SectionStyle.")
    range: RangeWritable = Field(
        ...,
        title=(
            "The range overlapping the sections to style. Because section breaks can only be "
            "inserted inside the body, the segment ID field must be empty."
        ),
    )
    sectionStyle: SectionStyleWritable = Field(
        ...,
        title=(
            "The styles to be set on the section. Certain section style changes may cause other "
            "changes to mirror Docs editor behavior. See SectionStyle docs for more information."
        ),
    )
    # TODO: Create a UpdateSectionStyleFields enum to reduce LLM hallucinations.
    # See UpdateTextStyleRequest for an example.
    fields: str = Field(
        ...,
        title=(
            "The fields that should be updated. At least one field must be specified. The root "
            "sectionStyle is implied and must not be specified. A single '*' can be used as "
            "short-hand for listing every field. For example to update the left margin, set fields "
            "to 'marginLeft'."
        ),
    )


class InsertSectionBreakRequest(BaseModel):
    model_config = ConfigDict(
        title=(
            "Inserts a section break at the given location. A newline character will be inserted "
            "before the section break."
        )
    )
    sectionType: SectionType = Field(
        ...,
        title="The type of section to insert.",
    )
    insertion_location: Location | EndOfSegmentLocation = Field(
        ...,
        title=(
            "Union field insertion_location. The location where the break will be inserted. "
            "location — Inserts a newline and a section break at a specific index inside an "
            "existing Paragraph; cannot be at a table's start index. Section breaks cannot be "
            "inside a table, equation, footnote, header, or footer. Segment ID must be empty "
            "(body only). "
            "endOfSegmentLocation — Inserts a newline and a section break at the end of the "
            "document body; cannot be inside a footnote, header or footer. Segment ID must be "
            "empty (body only)."
        ),
    )

    @model_serializer(mode="wrap")
    def _resolve_union_field(self, handler: Callable[[Any], Any]) -> Any:
        """
        Modify/wraps the result of the handler to resolve the union field insertion_location

        Args:
            handler: The handler function that would normally return the model's data
            such as `model_dump` or `model_json_schema`.

        Returns:
            The modified data with the union field resolved.
        """
        data = handler(self)
        data.pop("insertion_location", None)
        if isinstance(self.insertion_location, Location):
            data["location"] = self.insertion_location.model_dump(exclude_none=True)
        elif isinstance(self.insertion_location, EndOfSegmentLocation):
            data["endOfSegmentLocation"] = self.insertion_location.model_dump(exclude_none=True)
        return data


class DeleteHeaderRequest(BaseModel):
    model_config = ConfigDict(title="Deletes a Header from the document.")
    headerId: str = Field(
        ...,
        title=(
            "The id of the header to delete. If defined on DocumentStyle, "
            "the reference is removed, resulting in no header of that type for the first section. "
            "If defined on a SectionStyle, the reference is removed and the header of that type is "
            "continued from the previous section."
        ),
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab containing the header to delete. When omitted, the request applies to the "
            "first tab."
        ),
    )


class DeleteFooterRequest(BaseModel):
    model_config = ConfigDict(title="Deletes a Footer from the document.")
    footerId: str = Field(
        ...,
        title=(
            "The id of the footer to delete. If defined on DocumentStyle, the reference is "
            "removed, resulting in no footer of that type for the first section. If defined on "
            "a SectionStyle, the reference is removed and the footer of that type is continued "
            "from the previous section."
        ),
    )
    tabId: str | None = Field(
        None,
        title=(
            "The tab that contains the footer to delete. When omitted, the request applies to the "
            "first tab."
        ),
    )


class PinTableHeaderRowsRequest(BaseModel):
    model_config = ConfigDict(title="Updates the number of pinned table header rows in a table.")
    tableStartLocation: Location = Field(
        ...,
        title="The location where the table starts in the document.",
    )
    pinnedHeaderRowsCount: int = Field(
        ...,
        ge=0,
        title=("The number of table rows to pin, where 0 implies that all rows are unpinned."),
    )
