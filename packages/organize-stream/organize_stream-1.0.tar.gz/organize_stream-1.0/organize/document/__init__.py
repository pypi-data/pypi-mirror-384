#!/usr/bin/env python3
from __future__ import annotations
from typing import Union
from organize.find import SearchableText, DocumentFinder
from organize.read import (
    TextTable, ColumnBody, ColumnNames, read_directory_pdf, read_directory_image,
    read_file_pdf, read_document_pdf, read_image, read_files_image, merge_text_table, contains
)
from soup_files import File, Directory, ProgressBarAdapter
from convert_stream import DocumentPdf, ArrayString, ImageObject
import pandas as pd
import shutil

FindItem = Union[str, list[str]]

_bad_chars: list[str] = [
    '.', '!', ':', '?', '(', ')', '{', '}',
    '+', '#', '@', '<', '>', '/', '¢', ':',
]


def fmt_str_file(filename: str) -> str:
    for c in _bad_chars:
        filename = filename.replace(c, '')
    while '--' in filename:
        filename = filename.replace('--', '-')
    return filename


def move_list_files(mv_items: dict[str, list[File]], *, replace: bool = False) -> None:
    total_file = len(mv_items['src'])
    for idx, file in enumerate(mv_items['src']):
        if not file.exists():
            print(f'[PULANDO]: {idx + 1} Arquivo não encontrado {file.absolute()}')
        if mv_items['dest'][idx].exists():
            if not replace:
                print(f'[PULANDO]: {idx+1} O arquivo já existe {mv_items["dest"][idx].absolute()}')
                continue
        print(f'Movendo: {idx+1}/{total_file} {file.absolute()}')
        try:
            shutil.move(file.absolute(), mv_items['dest'][idx].absolute())
        except Exception as e:
            print(f'{e}')


class DocumentTextExtract(object):
    """
        Extrair texto de arquivos, e converter em Excel/DataFrame
    """

    def __init__(self):
        self.tb_list: list[TextTable] = []
        self.pbar: ProgressBarAdapter = ProgressBarAdapter()

    @property
    def is_empty(self) -> bool:
        return len(self.tb_list) == 0

    @property
    def finder(self) -> DocumentFinder:
        return DocumentFinder(self.tb_list)

    def add_directory_pdf(self, dir_pdf: Directory, *, apply_ocr: bool = False):
        self.tb_list.extend(read_directory_pdf(dir_pdf, apply_ocr=apply_ocr, pbar=self.pbar))

    def add_directory_image(self, dir_image: Directory):
        self.tb_list.extend(read_directory_image(dir_image, pbar=self.pbar))

    def add_file_pdf(self, file_pdf: File, apply_ocr: bool = False):
        self.tb_list.extend(read_file_pdf(file_pdf, pbar=self.pbar, apply_ocr=apply_ocr))

    def add_file_image(self, file_image: File):
        self.tb_list.append(read_image(file_image))

    def add_image(self, image: ImageObject):
        if not isinstance(image, ImageObject):
            raise TypeError('Image must be an ImageObject')
        self.tb_list.append(read_image(image))

    def add_document(self, document: DocumentPdf, *, apply_ocr: bool = False):
        self.tb_list.extend(
            read_document_pdf(document, document.name, pbar=self.pbar, apply_ocr=apply_ocr)
        )

    def to_data(self) -> pd.DataFrame:
        _data: list[pd.DataFrame] = []
        for m in self.tb_list:
            _data.append(m.to_data())
        if len(_data) > 0:
            return pd.concat(_data)
        return pd.DataFrame()

    def to_excel(self, file: File) -> None:
        self.to_data().to_excel(file.absolute(), index=False)


class OrganizeDocuments(object):

    def __init__(self, table_files: pd.DataFrame):
        self.table_files: pd.DataFrame = table_files
        self.pbar: ProgressBarAdapter = ProgressBarAdapter()

    def move_where_contains_text(
                self,
                find_txt: str,
                out_dir: Directory, *,
                case: bool = False,
                iqual: bool = False
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas nos documentos.
        O arquivo é movido de diretório quando determinada ocorrência é encontrada, preservando
        o nome original.
        """
        df = self.table_files[[ColumnNames.TEXT.value, ColumnNames.FILE_PATH.value]].astype('str')
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}

        if case:
            if iqual:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnNames.TEXT.value]}'
                    if find_txt == txt_in_file:
                        src_file = File(f'{row[ColumnNames.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
            else:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnNames.TEXT.value]}'
                    if find_txt in txt_in_file:
                        src_file = File(f'{row[ColumnNames.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
        else:
            if iqual:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnNames.TEXT.value]}'
                    if find_txt.upper() == txt_in_file.upper():
                        src_file = File(f'{row[ColumnNames.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
            else:
                for idx, row in df.iterrows():
                    txt_in_file = f'{row[ColumnNames.TEXT.value]}'
                    if find_txt.upper() in txt_in_file.upper():
                        src_file = File(f'{row[ColumnNames.FILE_PATH.value]}')
                        dest_file = out_dir.join_file(src_file.basename())
                        mv_items['src'].append(src_file)
                        mv_items['dest'].append(dest_file)
        move_list_files(mv_items)

    def move_where_math_text(
                self,
                find_txt: str,
                out_dir: Directory, *,
                separator: str = ' ',
                include_all_text: bool = False,
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas nos documentos.
        O arquivo é movido de diretório quando determinada ocorrência é encontrada, preservando
        o nome original.
        """
        values_text = self.table_files[ColumnNames.TEXT.value].astype('str').values.tolist()
        values_files = self.table_files[ColumnNames.FILE_PATH.value].astype('str').values.tolist()
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}

        for idx, txt_in_file in enumerate(values_text):

            if find_txt.upper() in txt_in_file.upper():
                src_file = File(values_files[idx])
                # filtrar a string apagando os caracteres que antecedem o padrão informado.
                try:
                    arr = ArrayString(txt_in_file.split(separator))
                    if not include_all_text:
                        new_file_name = arr.get_next(find_txt)
                    else:
                        new_file_name = arr.get_next_all(find_txt)
                        if len(new_file_name) == 0:
                            print(f'{__class__.__name__} Falha ao obter filename')
                            continue
                        elif len(new_file_name) == 1:
                            new_file_name = new_file_name[0]
                        else:
                            new_file_name = separator.join(new_file_name)
                except Exception as e:
                    print(e)
                else:
                    if new_file_name is None:
                        print(f'{__class__.__name__} Falha, filename is None')
                        continue
                    new_file_name = fmt_str_file(new_file_name)
                    mv_items['src'].append(src_file)
                    mv_items['dest'].append(out_dir.join_file(f'{new_file_name}{src_file.extension()}'))
        move_list_files(mv_items)

    def move_where_math_column(
                self,
                df: pd.DataFrame,
                out_dir: Directory, *,
                col_find: str,
                col_new_name: str,
                cols_in_name: list[str] = [],
            ) -> None:
        """
            Mover arquivos conforme as ocorrências de texto encontradas na tabela/DataFrame df.
        o nome do novo arquivo será igual à ocorrência de texto da coluna 'col_find', podendo
        estender o nome com elementos de outras colunas, tais colunas podem ser informadas (opcionalmente)
        no parâmetro cols_in_name.
            Ex:
        Suponha que a tabela para renomear aquivos tenha a seguinte estrutura:

        A      B        C
        maça   Cidade 1 xxyyy
        banana Cidade 2 yyxxx
        mamão  Cidade 3 xyxyx

        Se passarmos os parâmetros col_find='A' e col_new_name='A' e o texto banana for
        encontrado no(s) documento, o novo nome do arquivo será banana. Caso incluir o parâmetro
        cols_in_name=['B'] o novo nome do arquivo será banana-Cidade 2 ou
        banana-Cidade 2-yyxxx (se incluir cols_in_name=['B', 'C']).

        """
        values_find = df[col_find].astype('str').values.tolist()
        values_new_name = df[col_new_name].astype('str').values.tolist()
        text_in_docs = self.table_files[ColumnNames.TEXT.value].astype('str').values.tolist()
        text_file_names = self.table_files[ColumnNames.FILE_PATH.value].astype('str').values.tolist()
        mv_items: dict[str, list[File]] = {'src': [], 'dest': []}
        if len(cols_in_name) > 0:
            cols_include_names: list[list[str]] = []
            for c in cols_in_name:
                values_include: list[str] = df[c].astype('str').values.tolist()
                cols_include_names.append(values_include)

        for num, txt in enumerate(values_find):
            for num_idx, txt_doc in enumerate(text_in_docs):
                if txt in txt_doc:
                    src_file = File(text_file_names[num_idx])
                    output_file = values_new_name[num]
                    if len(cols_in_name) > 0:
                        new = ''
                        for element in cols_include_names:
                            new = f'{new}-{element[num]}'
                        output_file = f'{output_file}-{new}'
                    output_file = fmt_str_file(output_file)
                    mv_items['src'].append(src_file)
                    mv_items['dest'].append(out_dir.join_file(f'{output_file}{src_file.extension()}'))
        move_list_files(mv_items)

