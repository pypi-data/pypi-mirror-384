"""
Implements all resources used by the 'Document' resource.
The resources are defined at https://developers.google.com/workspace/docs/api/reference/rest/v1/documents
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Document(BaseModel):
    documentId: str | None = None
    title: str | None = None
    tabs: list[Tab] | None = None
    revisionId: str | None = None
    suggestionsViewMode: SuggestionsViewMode | None = None
    body: Body | None = None
    headers: dict[str, Header] | None = None
    footers: dict[str, Footer] | None = None
    footnotes: dict[str, Footnote] | None = None
    documentStyle: DocumentStyle | None = None
    suggestedDocumentStyleChanges: dict[str, SuggestedDocumentStyle] | None = None
    namedStyles: NamedStyles | None = None
    suggestedNamedStylesChanges: dict[str, SuggestedNamedStyles] | None = None
    lists: dict[str, List] | None = None
    namedRanges: dict[str, NamedRanges] | None = None
    inlineObjects: dict[str, InlineObject] | None = None
    positionedObjects: dict[str, PositionedObject] | None = None


class Tab(BaseModel):
    tabProperties: TabProperties | None = None
    childTabs: list[Tab] | None = None
    documentTab: DocumentTab | None = None


class TabProperties(BaseModel):
    tabId: str | None = None
    title: str | None = None
    parentTabId: str | None = None
    index: int | None = None
    nestingLevel: int | None = None


class DocumentTab(BaseModel):
    body: Body | None = None
    headers: dict[str, Header] | None = None
    footers: dict[str, Footer] | None = None
    footnotes: dict[str, Footnote] | None = None
    documentStyle: DocumentStyle | None = None
    suggestedDocumentStyleChanges: dict[str, SuggestedDocumentStyle] | None = None
    namedStyles: NamedStyles | None = None
    suggestedNamedStylesChanges: dict[str, SuggestedNamedStyles] | None = None
    lists: dict[str, List] | None = None
    namedRanges: dict[str, NamedRanges] | None = None
    inlineObjects: dict[str, InlineObject] | None = None
    positionedObjects: dict[str, PositionedObject] | None = None


class Body(BaseModel):
    content: list[StructuralElement] | None = None


class StructuralElement(BaseModel):
    startIndex: int | None = None
    endIndex: int | None = None
    paragraph: Paragraph | None = None
    sectionBreak: SectionBreak | None = None
    table: Table | None = None
    tableOfContents: TableOfContents | None = None


class Paragraph(BaseModel):
    elements: list[ParagraphElement] | None = None
    paragraphStyle: ParagraphStyle | None = None
    suggestedParagraphStyleChanges: dict[str, SuggestedParagraphStyle] | None = None
    bullet: Bullet | None = None
    suggestedBulletChanges: dict[str, SuggestedBullet] | None = None
    positionedObjectIds: list[str] | None = None
    suggestedPositionedObjectIds: dict[str, ObjectReferences] | None = None


class ParagraphElement(BaseModel):
    startIndex: int | None = None
    endIndex: int | None = None
    textRun: TextRun | None = None
    autoText: AutoText | None = None
    pageBreak: PageBreak | None = None
    columnBreak: ColumnBreak | None = None
    footnoteReference: FootnoteReference | None = None
    horizontalRule: HorizontalRule | None = None
    equation: Equation | None = None
    inlineObjectElement: InlineObjectElement | None = None
    person: Person | None = None
    richLink: RichLink | None = None


class TextRun(BaseModel):
    content: str | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class TextStyle(BaseModel):
    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikethrough: bool | None = None
    smallCaps: bool | None = None
    backgroundColor: OptionalColor | None = None
    foregroundColor: OptionalColor | None = None
    fontSize: Dimension | None = None
    weightedFontFamily: WeightedFontFamily | None = None
    baselineOffset: BaselineOffset | None = None
    link: Link | None = None


class OptionalColor(BaseModel):
    color: Color | None = None


class Color(BaseModel):
    rgbColor: RgbColor | None = None


class RgbColor(BaseModel):
    red: float | None = None
    green: float | None = None
    blue: float | None = None


class Dimension(BaseModel):
    magnitude: float | None = None
    unit: Unit | None = None


class Unit(str, Enum):
    UNIT_UNSPECIFIED = "UNIT_UNSPECIFIED"
    PT = "PT"


class WeightedFontFamily(BaseModel):
    fontFamily: str | None = None
    weight: int | None = None


class BaselineOffset(str, Enum):
    BASELINE_OFFSET_UNSPECIFIED = "BASELINE_OFFSET_UNSPECIFIED"
    NONE = "NONE"
    SUPERSCRIPT = "SUPERSCRIPT"
    SUBSCRIPT = "SUBSCRIPT"


class Link(BaseModel):
    url: str | None = None
    tabId: str | None = None
    bookmark: BookmarkLink | None = None
    heading: HeadingLink | None = None
    bookmarkId: str | None = None
    headingId: str | None = None


class BookmarkLink(BaseModel):
    id: str | None = None
    tabId: str | None = None


class HeadingLink(BaseModel):
    id: str | None = None
    tabId: str | None = None


class SuggestedTextStyle(BaseModel):
    textStyle: TextStyle | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None


class TextStyleSuggestionState(BaseModel):
    boldSuggested: bool | None = None
    italicSuggested: bool | None = None
    underlineSuggested: bool | None = None
    strikethroughSuggested: bool | None = None
    smallCapsSuggested: bool | None = None
    backgroundColorSuggested: bool | None = None
    foregroundColorSuggested: bool | None = None
    fontSizeSuggested: bool | None = None
    weightedFontFamilySuggested: bool | None = None
    baselineOffsetSuggested: bool | None = None
    linkSuggested: bool | None = None


class AutoText(BaseModel):
    type: Type | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class Type(str, Enum):
    TYPE_UNSPECIFIED = "TYPE_UNSPECIFIED"
    PAGE_NUMBER = "PAGE_NUMBER"
    PAGE_COUNT = "PAGE_COUNT"


class PageBreak(BaseModel):
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class ColumnBreak(BaseModel):
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class FootnoteReference(BaseModel):
    footnoteId: str | None = None
    footnoteNumber: str | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class HorizontalRule(BaseModel):
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class Equation(BaseModel):
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None


class InlineObjectElement(BaseModel):
    inlineObjectId: str | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None


class Person(BaseModel):
    personId: str | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None
    personProperties: PersonProperties | None = None


class PersonProperties(BaseModel):
    name: str | None = None
    email: str | None = None


class RichLink(BaseModel):
    richLinkId: str | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    textStyle: TextStyle | None = None
    suggestedTextStyleChanges: dict[str, SuggestedTextStyle] | None = None
    richLinkProperties: RichLinkProperties | None = None


class RichLinkProperties(BaseModel):
    title: str | None = None
    uri: str | None = None
    mimeType: str | None = None


class ParagraphStyle(BaseModel):
    headingId: str | None = None
    namedStyleType: NamedStyleType | None = None
    alignment: Alignment | None = None
    lineSpacing: float | None = None
    direction: ContentDirection | None = None
    spacingMode: SpacingMode | None = None
    spaceAbove: Dimension | None = None
    spaceBelow: Dimension | None = None
    borderBetween: ParagraphBorder | None = None
    borderTop: ParagraphBorder | None = None
    borderBottom: ParagraphBorder | None = None
    borderLeft: ParagraphBorder | None = None
    borderRight: ParagraphBorder | None = None
    indentFirstLine: Dimension | None = None
    indentStart: Dimension | None = None
    indentEnd: Dimension | None = None
    tabStops: list[TabStop] | None = None
    keepLinesTogether: bool | None = None
    keepWithNext: bool | None = None
    avoidWidowAndOrphan: bool | None = None
    shading: Shading | None = None
    pageBreakBefore: bool | None = None


class NamedStyleType(str, Enum):
    NAMED_STYLE_TYPE_UNSPECIFIED = "NAMED_STYLE_TYPE_UNSPECIFIED"
    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"


class Alignment(str, Enum):
    ALIGNMENT_UNSPECIFIED = "ALIGNMENT_UNSPECIFIED"
    START = "START"
    CENTER = "CENTER"
    END = "END"
    JUSTIFIED = "JUSTIFIED"


class ContentDirection(str, Enum):
    CONTENT_DIRECTION_UNSPECIFIED = "CONTENT_DIRECTION_UNSPECIFIED"
    LEFT_TO_RIGHT = "LEFT_TO_RIGHT"
    RIGHT_TO_LEFT = "RIGHT_TO_LEFT"


class SpacingMode(str, Enum):
    SPACING_MODE_UNSPECIFIED = "SPACING_MODE_UNSPECIFIED"
    NEVER_COLLAPSE = "NEVER_COLLAPSE"
    COLLAPSE_LISTS = "COLLAPSE_LISTS"


class ParagraphBorder(BaseModel):
    color: OptionalColor | None = None
    width: Dimension | None = None
    padding: Dimension | None = None
    dashStyle: DashStyle | None = None


class DashStyle(str, Enum):
    DASH_STYLE_UNSPECIFIED = "DASH_STYLE_UNSPECIFIED"
    SOLID = "SOLID"
    DOT = "DOT"
    DASH = "DASH"


class TabStop(BaseModel):
    offset: Dimension | None = None
    alignment: TabStopAlignment | None = None


class TabStopAlignment(str, Enum):
    TAB_STOP_ALIGNMENT_UNSPECIFIED = "TAB_STOP_ALIGNMENT_UNSPECIFIED"
    START = "START"
    CENTER = "CENTER"
    END = "END"


class Shading(BaseModel):
    backgroundColor: OptionalColor | None = None


class SuggestedParagraphStyle(BaseModel):
    paragraphStyle: ParagraphStyle | None = None
    paragraphStyleSuggestionState: ParagraphStyleSuggestionState | None = None


class ParagraphStyleSuggestionState(BaseModel):
    headingIdSuggested: bool | None = None
    namedStyleTypeSuggested: bool | None = None
    alignmentSuggested: bool | None = None
    lineSpacingSuggested: bool | None = None
    directionSuggested: bool | None = None
    spacingModeSuggested: bool | None = None
    spaceAboveSuggested: bool | None = None
    spaceBelowSuggested: bool | None = None
    borderBetweenSuggested: bool | None = None
    borderTopSuggested: bool | None = None
    borderBottomSuggested: bool | None = None
    borderLeftSuggested: bool | None = None
    borderRightSuggested: bool | None = None
    indentFirstLineSuggested: bool | None = None
    indentStartSuggested: bool | None = None
    indentEndSuggested: bool | None = None
    keepLinesTogetherSuggested: bool | None = None
    keepWithNextSuggested: bool | None = None
    avoidWidowAndOrphanSuggested: bool | None = None
    shadingSuggestionState: ShadingSuggestionState | None = None
    pageBreakBeforeSuggested: bool | None = None


class ShadingSuggestionState(BaseModel):
    backgroundColorSuggested: bool | None = None


class Bullet(BaseModel):
    listId: str | None = None
    nestingLevel: int | None = None
    textStyle: TextStyle | None = None


class SuggestedBullet(BaseModel):
    bullet: Bullet | None = None
    bulletSuggestionState: BulletSuggestionState | None = None


class BulletSuggestionState(BaseModel):
    listIdSuggested: bool | None = None
    nestingLevelSuggested: bool | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None


class ObjectReferences(BaseModel):
    objectIds: list[str] | None = None


class SectionBreak(BaseModel):
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    sectionStyle: SectionStyle | None = None


class SectionStyle(BaseModel):
    columnProperties: list[SectionColumnProperties] | None = None
    columnSeparatorStyle: ColumnSeparatorStyle | None = None
    contentDirection: ContentDirection | None = None
    marginTop: Dimension | None = None
    marginBottom: Dimension | None = None
    marginRight: Dimension | None = None
    marginLeft: Dimension | None = None
    marginHeader: Dimension | None = None
    marginFooter: Dimension | None = None
    sectionType: SectionType | None = None
    defaultHeaderId: str | None = None
    defaultFooterId: str | None = None
    firstPageHeaderId: str | None = None
    firstPageFooterId: str | None = None
    evenPageHeaderId: str | None = None
    evenPageFooterId: str | None = None
    useFirstPageHeaderFooter: bool | None = None
    pageNumberStart: int | None = None
    flipPageOrientation: bool | None = None


class SectionColumnProperties(BaseModel):
    width: Dimension | None = None
    paddingEnd: Dimension | None = None


class ColumnSeparatorStyle(str, Enum):
    COLUMN_SEPARATOR_STYLE_UNSPECIFIED = "COLUMN_SEPARATOR_STYLE_UNSPECIFIED"
    NONE = "NONE"
    BETWEEN_EACH_COLUMN = "BETWEEN_EACH_COLUMN"


class SectionType(str, Enum):
    SECTION_TYPE_UNSPECIFIED = "SECTION_TYPE_UNSPECIFIED"
    CONTINUOUS = "CONTINUOUS"
    NEXT_PAGE = "NEXT_PAGE"


class Table(BaseModel):
    rows: int | None = None
    columns: int | None = None
    tableRows: list[TableRow] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    tableStyle: TableStyle | None = None


class TableRow(BaseModel):
    startIndex: int | None = None
    endIndex: int | None = None
    tableCells: list[TableCell] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    tableRowStyle: TableRowStyle | None = None
    suggestedTableRowStyleChanges: dict[str, SuggestedTableRowStyle] | None = None


class TableCell(BaseModel):
    startIndex: int | None = None
    endIndex: int | None = None
    content: list[StructuralElement] | None = None
    tableCellStyle: TableCellStyle | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None
    suggestedTableCellStyleChanges: dict[str, SuggestedTableCellStyle] | None = None


class TableCellStyle(BaseModel):
    rowSpan: int | None = None
    columnSpan: int | None = None
    backgroundColor: OptionalColor | None = None
    borderLeft: TableCellBorder | None = None
    borderRight: TableCellBorder | None = None
    borderTop: TableCellBorder | None = None
    borderBottom: TableCellBorder | None = None
    paddingLeft: Dimension | None = None
    paddingRight: Dimension | None = None
    paddingTop: Dimension | None = None
    paddingBottom: Dimension | None = None
    contentAlignment: ContentAlignment | None = None


class ContentAlignment(str, Enum):
    CONTENT_ALIGNMENT_UNSPECIFIED = "CONTENT_ALIGNMENT_UNSPECIFIED"
    CONTENT_ALIGNMENT_UNSUPPORTED = "CONTENT_ALIGNMENT_UNSUPPORTED"
    TOP = "TOP"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


class TableCellBorder(BaseModel):
    color: OptionalColor | None = None
    width: Dimension | None = None
    dashStyle: DashStyle | None = None


class SuggestedTableCellStyle(BaseModel):
    tableCellStyle: TableCellStyle | None = None
    tableCellStyleSuggestionState: TableCellStyleSuggestionState | None = None


class TableCellStyleSuggestionState(BaseModel):
    rowSpanSuggested: bool | None = None
    columnSpanSuggested: bool | None = None
    backgroundColorSuggested: bool | None = None
    borderLeftSuggested: bool | None = None
    borderRightSuggested: bool | None = None
    borderTopSuggested: bool | None = None
    borderBottomSuggested: bool | None = None
    paddingLeftSuggested: bool | None = None
    paddingRightSuggested: bool | None = None
    paddingTopSuggested: bool | None = None
    paddingBottomSuggested: bool | None = None
    contentAlignmentSuggested: bool | None = None


class TableRowStyle(BaseModel):
    minRowHeight: Dimension | None = None
    tableHeader: bool | None = None
    preventOverflow: bool | None = None


class SuggestedTableRowStyle(BaseModel):
    tableRowStyle: TableRowStyle | None = None
    tableRowStyleSuggestionState: TableRowStyleSuggestionState | None = None


class TableRowStyleSuggestionState(BaseModel):
    minRowHeightSuggested: bool | None = None


class TableStyle(BaseModel):
    tableColumnProperties: list[TableColumnProperties] | None = None


class TableColumnProperties(BaseModel):
    widthType: WidthType | None = None
    width: Dimension | None = None


class WidthType(str, Enum):
    WIDTH_TYPE_UNSPECIFIED = "WIDTH_TYPE_UNSPECIFIED"
    EVENLY_DISTRIBUTED = "EVENLY_DISTRIBUTED"
    FIXED_WIDTH = "FIXED_WIDTH"


class TableOfContents(BaseModel):
    content: list[StructuralElement] | None = None
    suggestedInsertionIds: list[str] | None = None
    suggestedDeletionIds: list[str] | None = None


class Header(BaseModel):
    headerId: str | None = None
    content: list[StructuralElement] | None = None


class Footer(BaseModel):
    footerId: str | None = None
    content: list[StructuralElement] | None = None


class Footnote(BaseModel):
    footnoteId: str | None = None
    content: list[StructuralElement] | None = None


class DocumentStyle(BaseModel):
    background: Background | None = None
    defaultHeaderId: str | None = None
    defaultFooterId: str | None = None
    evenPageHeaderId: str | None = None
    evenPageFooterId: str | None = None
    firstPageHeaderId: str | None = None
    firstPageFooterId: str | None = None
    useFirstPageHeaderFooter: bool | None = None
    useEvenPageHeaderFooter: bool | None = None
    pageNumberStart: int | None = None
    marginTop: Dimension | None = None
    marginBottom: Dimension | None = None
    marginRight: Dimension | None = None
    marginLeft: Dimension | None = None
    pageSize: Size | None = None
    marginHeader: Dimension | None = None
    marginFooter: Dimension | None = None
    useCustomHeaderFooterMargins: bool | None = None
    flipPageOrientation: bool | None = None


class Background(BaseModel):
    color: OptionalColor | None = None


class Size(BaseModel):
    height: Dimension | None = None
    width: Dimension | None = None


class SuggestedDocumentStyle(BaseModel):
    documentStyle: DocumentStyle | None = None
    documentStyleSuggestionState: DocumentStyleSuggestionState | None = None


class DocumentStyleSuggestionState(BaseModel):
    backgroundSuggestionState: BackgroundSuggestionState | None = None
    defaultHeaderIdSuggested: bool | None = None
    defaultFooterIdSuggested: bool | None = None
    evenPageHeaderIdSuggested: bool | None = None
    evenPageFooterIdSuggested: bool | None = None
    firstPageHeaderIdSuggested: bool | None = None
    firstPageFooterIdSuggested: bool | None = None
    useFirstPageHeaderFooterSuggested: bool | None = None
    useEvenPageHeaderFooterSuggested: bool | None = None
    pageNumberStartSuggested: bool | None = None
    marginTopSuggested: bool | None = None
    marginBottomSuggested: bool | None = None
    marginRightSuggested: bool | None = None
    marginLeftSuggested: bool | None = None
    pageSizeSuggestionState: SizeSuggestionState | None = None
    marginHeaderSuggested: bool | None = None
    marginFooterSuggested: bool | None = None
    useCustomHeaderFooterMarginsSuggested: bool | None = None
    flipPageOrientationSuggested: bool | None = None


class BackgroundSuggestionState(BaseModel):
    backgroundColorSuggested: bool | None = None


class SizeSuggestionState(BaseModel):
    heightSuggested: bool | None = None
    widthSuggested: bool | None = None


class NamedStyles(BaseModel):
    styles: list[NamedStyle] | None = None


class NamedStyle(BaseModel):
    namedStyleType: NamedStyleType | None = None
    textStyle: TextStyle | None = None
    paragraphStyle: ParagraphStyle | None = None


class SuggestedNamedStyles(BaseModel):
    namedStyles: NamedStyles | None = None
    namedStylesSuggestionState: NamedStylesSuggestionState | None = None


class NamedStylesSuggestionState(BaseModel):
    stylesSuggestionStates: list[NamedStyleSuggestionState] | None = None


class NamedStyleSuggestionState(BaseModel):
    namedStyleType: NamedStyleType | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None
    paragraphStyleSuggestionState: ParagraphStyleSuggestionState | None = None


class List(BaseModel):
    listProperties: ListProperties | None = None
    suggestedListPropertiesChanges: dict[str, SuggestedListProperties] | None = None
    suggestedInsertionId: str | None = None
    suggestedDeletionIds: list[str] | None = None


class ListProperties(BaseModel):
    nestingLevels: list[NestingLevel] | None = None


class NestingLevel(BaseModel):
    bulletAlignment: BulletAlignment | None = None
    glyphFormat: str | None = None
    indentFirstLine: Dimension | None = None
    indentStart: Dimension | None = None
    textStyle: TextStyle | None = None
    startNumber: int | None = None
    glyphType: GlyphType | None = None
    glyphSymbol: str | None = None


class BulletAlignment(str, Enum):
    BULLET_ALIGNMENT_UNSPECIFIED = "BULLET_ALIGNMENT_UNSPECIFIED"
    START = "START"
    CENTER = "CENTER"
    END = "END"


class GlyphType(str, Enum):
    GLYPH_TYPE_UNSPECIFIED = "GLYPH_TYPE_UNSPECIFIED"
    NONE = "NONE"
    DECIMAL = "DECIMAL"
    ZERO_DECIMAL = "ZERO_DECIMAL"
    UPPER_ALPHA = "UPPER_ALPHA"
    ALPHA = "ALPHA"
    UPPER_ROMAN = "UPPER_ROMAN"
    ROMAN = "ROMAN"


class SuggestedListProperties(BaseModel):
    listProperties: ListProperties | None = None
    listPropertiesSuggestionState: ListPropertiesSuggestionState | None = None


class ListPropertiesSuggestionState(BaseModel):
    nestingLevelsSuggestionStates: list[NestingLevelSuggestionState] | None = None


class NestingLevelSuggestionState(BaseModel):
    bulletAlignmentSuggested: bool | None = None
    glyphTypeSuggested: bool | None = None
    glyphFormatSuggested: bool | None = None
    glyphSymbolSuggested: bool | None = None
    indentFirstLineSuggested: bool | None = None
    indentStartSuggested: bool | None = None
    textStyleSuggestionState: TextStyleSuggestionState | None = None
    startNumberSuggested: bool | None = None


class NamedRanges(BaseModel):
    name: str | None = None
    namedRanges: list[NamedRange] | None = None


class NamedRange(BaseModel):
    namedRangeId: str | None = None
    name: str | None = None
    ranges: list[Range] | None = None


class Range(BaseModel):
    segmentId: str | None = None
    startIndex: int | None = None
    endIndex: int | None = None
    tabId: str | None = None


class InlineObject(BaseModel):
    objectId: str | None = None
    inlineObjectProperties: InlineObjectProperties | None = None
    suggestedInlineObjectPropertiesChanges: dict[str, SuggestedInlineObjectProperties] | None = None
    suggestedInsertionId: str | None = None
    suggestedDeletionIds: list[str] | None = None


class InlineObjectProperties(BaseModel):
    embeddedObject: EmbeddedObject | None = None


class EmbeddedObject(BaseModel):
    title: str | None = None
    description: str | None = None
    embeddedObjectBorder: EmbeddedObjectBorder | None = None
    size: Size | None = None
    marginTop: Dimension | None = None
    marginBottom: Dimension | None = None
    marginRight: Dimension | None = None
    marginLeft: Dimension | None = None
    linkedContentReference: LinkedContentReference | None = None
    embeddedDrawingProperties: EmbeddedDrawingProperties | None = None
    imageProperties: ImageProperties | None = None


class EmbeddedDrawingProperties(BaseModel):
    # No fields per spec
    pass


class ImageProperties(BaseModel):
    contentUri: str | None = None
    sourceUri: str | None = None
    brightness: float | None = None
    contrast: float | None = None
    transparency: float | None = None
    cropProperties: CropProperties | None = None
    angle: float | None = None


class CropProperties(BaseModel):
    offsetLeft: float | None = None
    offsetRight: float | None = None
    offsetTop: float | None = None
    offsetBottom: float | None = None
    angle: float | None = None


class EmbeddedObjectBorder(BaseModel):
    color: OptionalColor | None = None
    width: Dimension | None = None
    dashStyle: DashStyle | None = None
    propertyState: PropertyState | None = None


class PropertyState(str, Enum):
    RENDERED = "RENDERED"
    NOT_RENDERED = "NOT_RENDERED"


class LinkedContentReference(BaseModel):
    sheetsChartReference: SheetsChartReference | None = None


class SheetsChartReference(BaseModel):
    spreadsheetId: str | None = None
    chartId: int | None = None


class SuggestedInlineObjectProperties(BaseModel):
    inlineObjectProperties: InlineObjectProperties | None = None
    inlineObjectPropertiesSuggestionState: InlineObjectPropertiesSuggestionState | None = None


class InlineObjectPropertiesSuggestionState(BaseModel):
    embeddedObjectSuggestionState: EmbeddedObjectSuggestionState | None = None


class EmbeddedObjectSuggestionState(BaseModel):
    embeddedDrawingPropertiesSuggestionState: EmbeddedDrawingPropertiesSuggestionState | None = None
    imagePropertiesSuggestionState: ImagePropertiesSuggestionState | None = None
    titleSuggested: bool | None = None
    descriptionSuggested: bool | None = None
    embeddedObjectBorderSuggestionState: EmbeddedObjectBorderSuggestionState | None = None
    sizeSuggestionState: SizeSuggestionState | None = None
    marginLeftSuggested: bool | None = None
    marginRightSuggested: bool | None = None
    marginTopSuggested: bool | None = None
    marginBottomSuggested: bool | None = None
    linkedContentReferenceSuggestionState: LinkedContentReferenceSuggestionState | None = None


class EmbeddedDrawingPropertiesSuggestionState(BaseModel):
    # No fields per spec
    pass


class ImagePropertiesSuggestionState(BaseModel):
    contentUriSuggested: bool | None = None
    sourceUriSuggested: bool | None = None
    brightnessSuggested: bool | None = None
    contrastSuggested: bool | None = None
    transparencySuggested: bool | None = None
    cropPropertiesSuggestionState: CropPropertiesSuggestionState | None = None
    angleSuggested: bool | None = None


class CropPropertiesSuggestionState(BaseModel):
    offsetLeftSuggested: bool | None = None
    offsetRightSuggested: bool | None = None
    offsetTopSuggested: bool | None = None
    offsetBottomSuggested: bool | None = None
    angleSuggested: bool | None = None


class EmbeddedObjectBorderSuggestionState(BaseModel):
    colorSuggested: bool | None = None
    widthSuggested: bool | None = None
    dashStyleSuggested: bool | None = None
    propertyStateSuggested: bool | None = None


class LinkedContentReferenceSuggestionState(BaseModel):
    sheetsChartReferenceSuggestionState: SheetsChartReferenceSuggestionState | None = None


class SheetsChartReferenceSuggestionState(BaseModel):
    spreadsheetIdSuggested: bool | None = None
    chartIdSuggested: bool | None = None


class PositionedObject(BaseModel):
    objectId: str | None = None
    positionedObjectProperties: PositionedObjectProperties | None = None
    suggestedPositionedObjectPropertiesChanges: (
        dict[str, SuggestedPositionedObjectProperties] | None
    ) = None
    suggestedInsertionId: str | None = None
    suggestedDeletionIds: list[str] | None = None


class PositionedObjectProperties(BaseModel):
    positioning: PositionedObjectPositioning | None = None
    embeddedObject: EmbeddedObject | None = None


class PositionedObjectPositioning(BaseModel):
    layout: PositionedObjectLayout | None = None
    leftOffset: Dimension | None = None
    topOffset: Dimension | None = None


class PositionedObjectLayout(str, Enum):
    POSITIONED_OBJECT_LAYOUT_UNSPECIFIED = "POSITIONED_OBJECT_LAYOUT_UNSPECIFIED"
    WRAP_TEXT = "WRAP_TEXT"
    BREAK_LEFT = "BREAK_LEFT"
    BREAK_RIGHT = "BREAK_RIGHT"
    BREAK_LEFT_RIGHT = "BREAK_LEFT_RIGHT"
    IN_FRONT_OF_TEXT = "IN_FRONT_OF_TEXT"
    BEHIND_TEXT = "BEHIND_TEXT"


class SuggestedPositionedObjectProperties(BaseModel):
    positionedObjectProperties: PositionedObjectProperties | None = None
    positionedObjectPropertiesSuggestionState: PositionedObjectPropertiesSuggestionState | None = (
        None
    )


class PositionedObjectPropertiesSuggestionState(BaseModel):
    positioningSuggestionState: PositionedObjectPositioningSuggestionState | None = None
    embeddedObjectSuggestionState: EmbeddedObjectSuggestionState | None = None


class PositionedObjectPositioningSuggestionState(BaseModel):
    layoutSuggested: bool | None = None
    leftOffsetSuggested: bool | None = None
    topOffsetSuggested: bool | None = None


class SuggestionsViewMode(str, Enum):
    DEFAULT_FOR_CURRENT_ACCESS = "DEFAULT_FOR_CURRENT_ACCESS"
    SUGGESTIONS_INLINE = "SUGGESTIONS_INLINE"
    PREVIEW_SUGGESTIONS_ACCEPTED = "PREVIEW_SUGGESTIONS_ACCEPTED"
    PREVIEW_WITHOUT_SUGGESTIONS = "PREVIEW_WITHOUT_SUGGESTIONS"
