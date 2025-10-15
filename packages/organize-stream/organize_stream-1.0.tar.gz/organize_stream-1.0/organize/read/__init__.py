#!/usr/bin/env python3

from __future__ import annotations
from io import BytesIO
from typing import Union

import pandas as pd
from convert_stream.image.img_object import ABCImageObject

from .text_map import (
    ColumnNames, HeadItem, HeadValues, ArrayString, ColumnBody, TextTable, contains, create_map_text
)
from convert_stream import (
    DocumentPdf, PageDocumentPdf, ConvertPdfToImages, ImageObject as ImObj, LibImage, DEFAULT_LIB_IMAGE
)
from ocr_stream import RecognizeImage, RecognizePdf, BinTesseract, TextRecognized, LibOcr, DEFAULT_LIB_OCR
from soup_files import Directory, File, InputFiles, LibraryDocs, ProgressBarAdapter


class ImageObject(ImObj):

    def __init__(
                self, img: Union[ABCImageObject, bytes, BytesIO, str, File], *,
                lib_image: LibImage = DEFAULT_LIB_IMAGE
            ) -> None:
        if isinstance(img, File):
            self.name_extension: str = img.extension()
        else:
            self.name_extension = None
        super().__init__(img, lib_image=lib_image)


def merge_text_table(text_list: list[TextTable]) -> pd.DataFrame:
    if len(text_list) == 0:
        return pd.DataFrame()
    list_data: list[pd.DataFrame] = []
    for tb in text_list:
        df = tb.to_data()
        list_data.append(df)
    final_df = pd.concat(list_data)
    return final_df


class Ocr(RecognizeImage):
    _instance = None  # armazena a instância única

    def __new__(cls, bin_tess: BinTesseract = BinTesseract(), *, lib_ocr: LibOcr = DEFAULT_LIB_OCR):
        if cls._instance is None:
            # Cria a instância uma única vez
            cls._instance = super(Ocr, cls).__new__(cls)
        return cls._instance

    def __init__(self, bin_tess: BinTesseract = BinTesseract(), *, lib_ocr: LibOcr = DEFAULT_LIB_OCR):
        # Evita reexecutar __init__ em chamadas subsequentes
        if not hasattr(self, "_initialized"):
            super().__init__(bin_tess, lib_ocr=lib_ocr)
            self._initialized = True


def recognize_images(
        images: list[ImageObject], *,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter()
) -> DocumentPdf:
    """
        Aplicar OCR em lista de imagens, e retornar um documento DocumentPdf() com as imagens embutidas.
    """
    pages_pdf: list[PageDocumentPdf] = []
    max_num: int = len(images)
    print()
    pbar.start()
    for _num, im in enumerate(images):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {im.name}',
        )
        tmp_doc = ocr.image_recognize(im).to_document()
        pages_pdf.extend(tmp_doc.to_pages())
        del tmp_doc
    pbar.stop()
    print()
    return DocumentPdf.create_from_pages(pages_pdf)


def read_image(
        image: File | ImageObject | bytes | BytesIO, *,
        file_path: str = None,
        ocr: Ocr = Ocr(),
) -> TextTable:
    if isinstance(image, File):
        if file_path is None:
            file_path = image.absolute()
    elif isinstance(image, ImageObject):
        pass
    elif isinstance(image, bytes):
        image = ImageObject.create_from_bytes(image)
    elif isinstance(image, BytesIO):
        image = ImageObject(image)
    else:
        raise ValueError('Use: File|DocumentPdf|bytes|ByesIO')

    if file_path is None:
        file_path = image.name
        if image.name_extension is not None:
            file_path = f'{file_path}{image.name_extension}'
    try:
        text_image: str = ocr.image_to_string(image)
        if (text_image is None) or (text_image == ''):
            mp = create_map_text(['nan'], file_path)
        else:
            mp = create_map_text(text_image.split('\n'), file_path)
    except Exception as err:
        print(err)
        mp = create_map_text(['nan'], file_path)
    return mp


def read_files_image(
        images_files: list[ImageObject], *,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter(),
) -> list[TextTable]:
    """
        Ler as imagens de um diretório e retorna list[TextMap]
    """

    list_table: list[TextTable] = []
    max_num: int = len(images_files)
    print()
    pbar.start()
    for _num, img in enumerate(images_files):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {img.name}',
        )
        list_table.append(read_image(img, ocr=ocr))
    return list_table


def read_directory_image(
        directory: Directory, *,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter(),
) -> list[TextTable]:
    """
        Ler as imagens de um diretório e retorna list[TextMap]
    """
    images_files: list[File] = InputFiles(directory).get_files(file_type=LibraryDocs.IMAGE)
    _data: list[TextTable] = []
    max_num: int = len(images_files)
    print()
    pbar.start()
    for _num, file_image in enumerate(images_files):
        pbar.update(
            ((_num + 1) / max_num) * 100,
            f'[OCR]: {_num + 1}/{max_num} {file_image.basename()}',
        )
        im = ImageObject(file_image)
        _data.append(read_image(im, ocr=ocr, file_path=file_image.absolute()))
    return _data


def read_document_pdf(
        document: DocumentPdf,
        file_path: str,
        apply_ocr: bool = False,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter(),
) -> list[TextTable]:
    """Extrair os textos de páginas PDF e retornar um objeto TextMap()"""
    if not isinstance(document, DocumentPdf):
        raise TypeError(f'file_pdf dev ser DocumentPdf() não {type(file_pdf)}')
    if apply_ocr:
        conv = ConvertPdfToImages.create(document)
        images: list[ImageObject] = conv.to_images()
        document: DocumentPdf = recognize_images(images, ocr=ocr, pbar=pbar)
    list_table = []
    pages_pdf = document.to_pages()
    for pg in pages_pdf:
        text_page = pg.to_string()
        if (text_page is None) or (text_page == '') or (text_page == 'nas'):
            current_mp = create_map_text(['nan'], file_path, page_num=f'{pg.number_page}')
        else:
            try:
                current_mp = create_map_text(text_page.split('\n'), file_path, page_num=f'{pg.number_page}')
            except Exception as err:
                print(err)
                current_mp = create_map_text(['nan'], file_path, page_num=f'{pg.number_page}')
        list_table.append(current_mp)
    return list_table


def read_file_pdf(
        file_pdf: File,
        apply_ocr: bool = False,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter(),
) -> list[TextTable]:
    """Extrair os textos de páginas PDF e retornar um objeto TextMap()"""
    if not isinstance(file_pdf, File):
        raise TypeError(f'file_pdf dev ser File() não {type(file_pdf)}')
    return read_document_pdf(
        DocumentPdf(file_pdf), file_pdf.absolute(), ocr=ocr, pbar=pbar, apply_ocr=apply_ocr
    )


def read_directory_pdf(
        directory: Directory, *,
        apply_ocr: bool = False,
        ocr: Ocr = Ocr(),
        pbar: ProgressBarAdapter = ProgressBarAdapter(),
) -> list[TextTable]:
    files_doc_pdf: list[File] = InputFiles(directory).get_files(file_type=LibraryDocs.PDF)
    _text_maps: list[TextTable] = []
    for f_pdf in files_doc_pdf:
        _current_maps = read_file_pdf(f_pdf, apply_ocr=apply_ocr, ocr=ocr, pbar=pbar)
        _text_maps.extend(_current_maps)
    return _text_maps
