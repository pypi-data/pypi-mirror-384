#!/usr/bin/env python3

__version__ = '1.0'
from .read import (
    ImageObject, TextTable, contains, create_map_text, merge_text_table,
    ColumnNames, ColumnBody, HeadItem, HeadValues
)
from .find import SearchableText, DocumentFinder
from .document import OrganizeDocuments, DocumentTextExtract

