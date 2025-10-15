#!/usr/bin/env python3
#
from __future__ import annotations
from enum import Enum
from convert_stream import ArrayString
import os.path
import pandas as pd


def contains(text: str, values: list[str], *, case: bool = True, iqual: bool = False) -> bool:
    if case:
        if iqual:
            for x in values:
                if text == x:
                    return True
        else:
            for x in values:
                if text in x:
                    return True
    else:
        if iqual:
            for x in values:
                if text.upper() == x.upper():
                    return True
        else:
            for x in values:
                if text.upper() in x.upper():
                    return True
    return False


class HeadItem(str):

    def __init__(self, text: str):
        super().__init__()
        self.text: str = text


class HeadValues(list):

    def __init__(self, head_items: list[HeadItem]):
        super().__init__(head_items)

    def contains(self, item: HeadItem | str, *, case: bool = True, iqual: bool = False) -> bool:
        return contains(item, self, case=case, iqual=iqual)

    def get(self, idx: int) -> HeadItem:
        return self[idx]

    def add_head(self, h: HeadItem):
        if isinstance(h, HeadItem):
            self.append(h)


class ColumnBody(list):

    def __init__(self, col_name: HeadItem | str, col_body: list[str] = []):
        super().__init__(col_body)
        if isinstance(col_name, str):
            col_name = HeadItem(col_name)
        self.col_name: HeadItem = col_name

    @property
    def length(self) -> int:
        return len(self)

    @property
    def is_empty(self) -> bool:
        return self.length == 0

    def __repr__(self):
        return f'{self.col_name}: {super().__repr__()}'

    def add_line(self, line: str):
        if isinstance(line, str):
            self.append(line)

    def add_lines(self, lines: list[str]):
        for line in lines:
            self.add_line(line)


class ColumnNames(Enum):

    NUM_LINE = 'LINHA'
    NUM_PAGE = 'PÁGINA'
    TEXT = 'TEXTO'
    FILE_PATH = 'ARQUIVO'
    FILE_NAME = 'NOME_ARQUIVO'


class TextTable(object):

    def __init__(self, items: list[ColumnBody] = []):
        self.items: list[ColumnBody] = items

    def __repr__(self):
        return f'{self.__class__.__name__}:\n{self.items})'

    @property
    def head(self) -> HeadValues:
        return HeadValues([x.col_name for x in self.items])

    @property
    def length(self) -> int:
        return len(self.items[0])

    @property
    def is_empty(self) -> bool:
        return self.length == 0

    def add_column(self, col: ColumnBody, *, replace: bool = False):
        if isinstance(col, ColumnBody):
            if self.head.contains(col.col_name, case=True, iqual=True):
                if replace:
                    idx_col = self.head.index(col.col_name)
                    self.items[idx_col] = col
            else:
                self.items.append(col)

    def extend_column(self, col: ColumnBody):
        if not self.head.contains(col.col_name, case=True, iqual=True):
            raise IndexError(f'Column {col.col_name} não existe em: {self.head}')
        idx = self.head.index(col.col_name)
        self.items[idx].extend(col)

    def to_array(self) -> ArrayString:
        return ArrayString(self.get_column(ColumnNames.TEXT.value))

    def to_dict(self) -> dict[HeadItem, ColumnBody]:
        v = {}
        for col in self.items:
            v[col.col_name] = col
        return v

    def to_data(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.to_dict())

    def get_column(self, name: str) -> ColumnBody | None:
        for col in self.items:
            if col.col_name == name:
                return col
        return None


def create_map_text(values: list[str], filepath: str, *, page_num: str = 'nan') -> TextTable:
    total = len(values)
    col_num_page = ColumnBody(ColumnNames.NUM_PAGE.value, [page_num] * total)
    col_num_lines = ColumnBody(ColumnNames.NUM_LINE.value, [f'{x+1}' for x in range(total)])
    colum_txt = ColumnBody(ColumnNames.TEXT.value, values)
    colum_filepath = ColumnBody(ColumnNames.FILE_PATH.value, [filepath] * total)
    colum_filename = ColumnBody(ColumnNames.FILE_NAME.value, [os.path.basename(filepath)] * total)
    return TextTable([col_num_page, col_num_lines, colum_txt, colum_filepath, colum_filename])




