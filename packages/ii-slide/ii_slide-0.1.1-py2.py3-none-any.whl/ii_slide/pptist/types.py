

from enum import Enum


class SlideType(Enum):
    COVER = "cover"
    CONTENT = "content"
    CONTENTS = "contents"
    TRANSITION = "transition"
    TABLE_OF_CONTENT = "table_of_content"
    CHAPTER = "chapter"
    END = "end"
    BACKGROUND = "background"


class ElementType(Enum):
    TEXT = "text"
    IMAGE = "image"
    SHAPE = "shape"
    LINE = "line"


class TextType(Enum):
    """Text element types that map to textType field in PPTist"""
    TITLE = "title"
    SUBTITLE = "subtitle"
    BODY = "body"
    ITEM = "item"
    ITEM_TITLE = "itemTitle"
    AUTHOR = "author"
    DATE = "date"
    CONTACT = "contact"
    PART_NUMBER = "partNumber"