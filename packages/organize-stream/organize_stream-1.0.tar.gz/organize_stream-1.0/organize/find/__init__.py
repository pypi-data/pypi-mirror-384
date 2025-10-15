#!/usr/bin/env python3

from __future__ import annotations
import os.path
import pandas as pd
from soup_files import File, Directory, JsonConvert, ProgressBarAdapter
from organize.read import ColumnNames, HeadItem, HeadValues, ColumnBody, TextTable
from convert_stream import ArrayString


class SearchableText(object):

    default_elements: dict[HeadItem, ColumnBody] = {
        HeadItem(ColumnNames.NUM_PAGE.value): ColumnBody(ColumnNames.NUM_PAGE.value),
        HeadItem(ColumnNames.NUM_LINE.value): ColumnBody(ColumnNames.NUM_LINE.value),
        HeadItem(ColumnNames.TEXT.value): ColumnBody(ColumnNames.TEXT.value),
        HeadItem(ColumnNames.FILE_PATH.value): ColumnBody(ColumnNames.FILE_NAME.value),
        HeadItem(ColumnNames.FILE_NAME.value): ColumnBody(ColumnNames.FILE_NAME.value),
    }

    default_columns: HeadValues = HeadValues(
        [
            HeadItem(ColumnNames.NUM_PAGE.value),
            HeadItem(ColumnNames.NUM_LINE.value),
            HeadItem(ColumnNames.TEXT.value),
            HeadItem(ColumnNames.FILE_PATH.value),
            HeadItem(ColumnNames.FILE_NAME.value),
        ]
    )

    def __init__(self):
        
        self.elements: dict[HeadItem, ColumnBody] = {
            HeadItem(ColumnNames.NUM_PAGE.value): ColumnBody(ColumnNames.NUM_PAGE.value),
            HeadItem(ColumnNames.NUM_LINE.value): ColumnBody(ColumnNames.NUM_LINE.value),
            HeadItem(ColumnNames.TEXT.value): ColumnBody(ColumnNames.TEXT.value),
            HeadItem(ColumnNames.FILE_PATH.value): ColumnBody(ColumnNames.FILE_NAME.value),
            HeadItem(ColumnNames.FILE_NAME.value): ColumnBody(ColumnNames.FILE_NAME.value),
        }

    def __repr__(self):
        return f'SearchableText\nHead: {self.head}\nBody: {self.body}'

    def is_empty(self) -> bool:
        return len(self.elements[HeadItem(ColumnNames.TEXT.value)]) == 0

    @property
    def head(self) -> HeadValues:
        return HeadValues([HeadItem(x) for x in list(self.elements.keys())])

    @property
    def body(self) -> list[ColumnBody]:
        return [ColumnBody(HeadItem(_k), self.elements[_k]) for _k in self.elements.keys()]

    @property
    def first(self) -> dict[str, str]:
        if self.is_empty():
            return {}
        cols: HeadValues = self.head
        _first = {}
        for col in cols:
            _first[col] = self.elements[col][0]
        return _first

    @property
    def last(self) -> dict[str, str]:
        if self.is_empty():
            return {}
        cols = self.head
        _last = {}
        for col in cols:
            _last[col] = self.elements[col][-1]
        return _last

    @property
    def length(self) -> int:
        return len(self.elements[HeadItem(ColumnNames.TEXT.value)])

    @property
    def files(self) -> ColumnBody:
        return self.elements[HeadItem(ColumnNames.FILE_PATH.value)]

    def get_item(self, idx: int) -> dict[str, str]:
        cols: HeadValues = self.head
        try:
            _item = {}
            for col in cols:
                _item[col] = self.elements[col][idx]
            return _item
        except Exception as err:
            print(err)
            return {}

    def get_column(self, name: str) -> ColumnBody:
        return self.elements[HeadItem(name)]

    def add_line(self, text: str, *, num_line: str, file: str, num_page: str) -> None:
        self.elements[HeadItem(ColumnNames.NUM_PAGE.value)].add_line(num_page)
        self.elements[HeadItem(ColumnNames.NUM_LINE.value)].append(num_line)
        self.elements[HeadItem(ColumnNames.TEXT.value)].append(text)
        self.elements[HeadItem(ColumnNames.FILE_PATH.value)].append(file)
        self.elements[HeadItem(ColumnNames.FILE_NAME.value)].append(os.path.basename(file))

    def clear(self) -> None:
        for _k in self.elements.keys():
            self.elements[_k].clear()

    def to_string(self) -> str:
        """
            Retorna o texto da coluna TEXT em formato de string
        ou 'nas' em caso de erro nas = Not a String
        """
        try:
            return ' '.join(self.elements[HeadItem(ColumnNames.TEXT.value)])
        except Exception as e:
            print(e)
            return 'nan'

    def to_data_frame(self) -> pd.DataFrame:
        return pd.DataFrame.from_dict(self.elements)

    def to_file_json(self, file: File):
        """Exporta os dados da busca para arquivo .JSON"""
        dt = JsonConvert.from_dict(self.elements).to_json_data()
        dt.to_file(file)

    def to_file_excel(self, file: File):
        """Exporta os dados da busca para arquivo .XLSX"""
        self.to_data_frame().to_excel(file.absolute(), index=False)

    @classmethod
    def create(cls, df: pd.DataFrame) -> SearchableText:
        default = cls.default_elements
        default[HeadItem(ColumnNames.NUM_PAGE.value)] = ColumnBody(
            ColumnNames.NUM_PAGE.value, df[ColumnNames.NUM_PAGE.value].values.tolist(),
        )
        default[HeadItem(ColumnNames.NUM_LINE.value)] = ColumnBody(
            ColumnNames.NUM_LINE.value, df[ColumnNames.NUM_LINE.value].values.tolist()
        )
        default[HeadItem(ColumnNames.TEXT.value)] = ColumnBody(
            ColumnNames.TEXT.value, df[ColumnNames.TEXT.value].values.tolist()
        )
        default[HeadItem(ColumnNames.FILE_PATH.value)] = ColumnBody(
            ColumnNames.FILE_PATH.value, df[ColumnNames.FILE_PATH.value].values.tolist()
        )
        default[HeadItem(ColumnNames.FILE_NAME.value)] = ColumnBody(
            ColumnNames.FILE_NAME.value, df[ColumnNames.FILE_NAME.value].values.tolist()
        )
        df_fmt = df.drop(columns=cls.default_columns).astype('str')
        new_columns: list[str] = df_fmt.columns.tolist()

        for col in new_columns:
            default[HeadItem(col)] = ColumnBody(col, df_fmt[col].values.tolist())
        _s = cls()
        _s.elements = default
        return _s


class DocumentFinder(object):

    def __init__(self, text_maps: list[TextTable]):
        self.text_maps: list[TextTable] = text_maps

        # Coluna que contem o texto usado como filtro em cada linha da busca
        self._col_name_filter: str = 'FILTRO'
        # Coluna que contem o texto de filtro adicional
        self._col_include_filter: str = 'FILTRO ADICIONAL'

    def add_table(self, item: TextTable) -> None:
        self.text_maps.append(item)

    def find(self, text: str) -> SearchableText:
        _data = []
        s = SearchableText()
        for text_map in self.text_maps:
            arr = text_map.to_array()
            _current_idx = arr.index(text)
            if _current_idx is not None:
                text_dict: dict[HeadItem | str, ColumnBody] = text_map.to_dict()
                s.add_line(
                    text=text_dict[ColumnNames.TEXT.value][_current_idx],
                    num_line=text_dict[ColumnNames.NUM_LINE.value][_current_idx],
                    file=text_dict[ColumnNames.FILE_PATH.value][_current_idx],
                    num_page=text_dict[ColumnNames.NUM_PAGE.value][_current_idx],
                )
                break
        return s

    def find_all(self, text: str) -> SearchableText:
        _data = []
        s = SearchableText()
        for tb in self.text_maps:
            arr: ArrayString = tb.to_array()
            _current_idx: int = arr.index(text)
            if _current_idx is not None:
                s.add_line(
                    text=tb.get_column(ColumnNames.TEXT.value)[_current_idx],
                    num_line=tb.get_column(ColumnNames.NUM_LINE.value)[_current_idx],
                    file=tb.get_column(ColumnNames.FILE_PATH.value)[_current_idx],
                    num_page=tb.get_column(ColumnNames.NUM_PAGE.value)[_current_idx],
                )
        return s

    def find_from_data(self, df: pd.DataFrame, *, col_filter: str, col_new_filter: str = None) -> SearchableText:
        """
            Filtrar vários textos em documentos/arquivos, incluindo dois tipos de filtros simultaneos.

        :df: DataFrame com os textos a serem usados como filtro apartir da coluna indicada
        :col_filter: string da coluna que contém os textos a serem filtrados
        :col_new_filter: string da coluna que contém um filtro adicional (opcional)

        @type df: pd.DataFrame
        @type col_filter: str
        @type col_new_filter: str
        @rtype: SearchableText
        """
        if col_new_filter is not None:
            df = df[[col_filter, col_new_filter]].dropna(subset=[col_filter]).astype('str')
        else:
            df = df[[col_filter]].dropna(subset=[col_filter]).astype('str')

        list_data = []
        for i, row in df.iterrows():
            _searchable = self.find_all(f'{row[col_filter]}').to_data_frame()
            if not _searchable.empty:
                if col_new_filter is not None:
                    new_searchable = self.find_all(f'{row[col_new_filter]}').to_data_frame()
                    if not new_searchable.empty:
                        _searchable = pd.concat([_searchable, new_searchable])
                        _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                        _searchable[self._col_include_filter] = [row[col_new_filter]] * len(_searchable)
                    else:
                        _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                        _searchable[self._col_include_filter] = ['nan'] * len(_searchable)
                else:
                    _searchable[self._col_name_filter] = [row[col_filter]] * len(_searchable)
                    _searchable[self._col_include_filter] = ['nan'] * len(_searchable)
                list_data.append(_searchable)

        if len(list_data) > 0:
            return SearchableText.create(pd.concat(list_data))
        return SearchableText()

