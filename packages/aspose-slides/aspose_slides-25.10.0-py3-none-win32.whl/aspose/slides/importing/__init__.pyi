﻿from typing import List, Optional, Dict, Iterable
import aspose.pycore
import aspose.pydrawing
import aspose.slides
import aspose.slides.ai
import aspose.slides.animation
import aspose.slides.charts
import aspose.slides.dom.ole
import aspose.slides.effects
import aspose.slides.excel
import aspose.slides.export
import aspose.slides.export.xaml
import aspose.slides.importing
import aspose.slides.ink
import aspose.slides.lowcode
import aspose.slides.mathtext
import aspose.slides.slideshow
import aspose.slides.smartart
import aspose.slides.spreadsheet
import aspose.slides.theme
import aspose.slides.util
import aspose.slides.vba
import aspose.slides.warnings

class ExcelWorkbookImporter:
    '''Provides functionality for importing content from an Excel workbook into a presentation.'''
    @overload
    @staticmethod
    def add_chart_from_workbook(shapes: IShapeCollection, x: float, y: float, workbook: aspose.slides.excel.IExcelDataWorkbook, worksheet_name: str, chart_index: int, embed_all_workbook: bool) -> aspose.slides.charts.IChart:
        '''Retrieves a chart from the specified Excel workbook and adds it to the end of the given shape collection at the specified coordinates.
        :param shapes: The shape collection to which the chart will be added.
        :param x: The X coordinate for positioning the chart.
        :param y: The Y coordinate for positioning the chart.
        :param workbook: The Excel workbook.
        :param worksheet_name: The name of the worksheet that contains the chart.
        :param chart_index: The zero-based index of the chart shape to insert. 
                    This index can be obtained using the :py:func:`aspose.slides.excel.IExcelDataWorkbook.get_charts_from_worksheet` method.
        :param embed_all_workbook: If ``true``, the entire workbook will be embedded in the chart; 
                    if ``false``, only the chart data will be embedded.
        :returns: The chart that was added to the shape collection.'''
        ...

    @overload
    @staticmethod
    def add_chart_from_workbook(shapes: IShapeCollection, x: float, y: float, workbook: aspose.slides.excel.IExcelDataWorkbook, worksheet_name: str, chart_name: str, embed_all_workbook: bool) -> aspose.slides.charts.IChart:
        '''Retrieves a chart from the specified Excel workbook and adds it to the end of the given shape collection at the specified coordinates.
        :param shapes: The shape collection to which the chart will be added.
        :param x: The X coordinate for positioning the chart.
        :param y: The Y coordinate for positioning the chart.
        :param workbook: The Excel workbook.
        :param worksheet_name: The name of the worksheet that contains the chart.
        :param chart_name: The name of the chart to be added.
        :param embed_all_workbook: If ``true``, the entire workbook will be embedded in the chart; 
                    if ``false``, only the chart data will be embedded.
        :returns: The chart that was added to the shape collection.'''
        ...

    @overload
    @staticmethod
    def add_chart_from_workbook(shapes: IShapeCollection, x: float, y: float, workbook_stream: io.RawIOBase, worksheet_name: str, chart_name: str, embed_all_workbook: bool) -> aspose.slides.charts.IChart:
        '''Retrieves a chart from the specified Excel workbook and adds it to the end of the given shape collection at the specified coordinates.
        :param shapes: The shape collection to which the chart will be added.
        :param x: The X coordinate for positioning the chart.
        :param y: The Y coordinate for positioning the chart.
        :param workbook_stream: A stream containing the workbook data.
        :param worksheet_name: The name of the worksheet that contains the chart.
        :param chart_name: The name of the chart to be added.
        :param embed_all_workbook: If ``true``, the entire workbook will be embedded in the chart; 
                    if ``false``, only the chart data will be embedded.
        :returns: The chart that was added to the shape collection.'''
        ...

    @overload
    @staticmethod
    def add_chart_from_workbook(shapes: IShapeCollection, x: float, y: float, workbook_path: str, worksheet_name: str, chart_name: str, embed_workbook: bool) -> aspose.slides.charts.IChart:
        '''Retrieves a chart from the specified Excel workbook and adds it to the end of the given shape collection at the specified coordinates.
        :param shapes: The shape collection to which the chart will be added.
        :param x: The X coordinate for positioning the chart.
        :param y: The Y coordinate for positioning the chart.
        :param workbook_path: The file path to the workbook containing the chart.
        :param worksheet_name: The name of the worksheet that contains the chart.
        :param chart_name: The name of the chart to be added.
        :param embed_workbook: If ``true``, the workbook will be embedded in the chart; 
                    if ``false``, the chart will link to the external workbook.
        :returns: The chart that was added to the shape collection.'''
        ...

    ...

class ExternalResourceResolver:
    '''Callback class used to resolve external resources during Html, Svg documents import.'''
    def __init__(self):
        ...

    def resolve_uri(self, base_uri: str, relative_uri: str) -> str:
        '''Resolves the absolute URI from the base and relative URIs.
        :param base_uri: Base URI of linking objects
        :param relative_uri: Relative URI to the linked object.
        :returns: Absolute URI or None if the relative URI cannot be resolved.'''
        ...

    def get_entity(self, absolute_uri: str) -> io.RawIOBase:
        '''Maps a URI to an object containing the actual resource.
        :param absolute_uri: Absolute URI to the object.
        :returns: A :py:class:`io.RawIOBase` object or None if resource cannot be streamed.'''
        ...

    ...

class HtmlExternalResolver:
    '''Callback object used by HTML import routine to obtain referrenced objects such as images.'''
    def __init__(self):
        ...

    def resolve_uri(self, base_uri: str, relative_uri: str) -> str:
        '''Resolves the absolute URI from the base and relative URIs.
        :param base_uri: Base URI of linking objects
        :param relative_uri: Relative URI to the linked object.
        :returns: Absolute URI or None if the relative URI cannot be resolved.'''
        ...

    def get_entity(self, absolute_uri: str) -> io.RawIOBase:
        '''Maps a URI to an object containing the actual resource.
        :param absolute_uri: Absolute URI to the object.
        :returns: A :py:class:`io.RawIOBase` object or None if resource cannot be streamed.'''
        ...

    @property
    def as_i_external_resource_resolver(self) -> IExternalResourceResolver:
        ...

    ...

class IExternalResourceResolver:
    '''Callback interface used to resolve external resources during Html, Svg documents import.'''
    def resolve_uri(self, base_uri: str, relative_uri: str) -> str:
        '''Resolves the absolute URI from the base and relative URIs.
        :param base_uri: Base URI of linking objects
        :param relative_uri: Relative URI to the linked object.
        :returns: Absolute URI or None if the relative URI cannot be resolved.'''
        ...

    def get_entity(self, absolute_uri: str) -> io.RawIOBase:
        '''Maps a URI to an object containing the actual resource.
        :param absolute_uri: Absolute URI to the object.
        :returns: A :py:class:`io.RawIOBase` object or None if resource cannot be streamed.'''
        ...

    ...

class IHtmlExternalResolver:
    '''Callback interface used by HTML import routine to obtain referrenced objects such as images.'''
    def resolve_uri(self, base_uri: str, relative_uri: str) -> str:
        ...

    def get_entity(self, absolute_uri: str) -> io.RawIOBase:
        ...

    @property
    def as_i_external_resource_resolver(self) -> IExternalResourceResolver:
        ...

    ...

class PdfImportOptions:
    '''Represents the PDF import options'''
    def __init__(self):
        ...

    @property
    def detect_tables(self) -> bool:
        ...

    @detect_tables.setter
    def detect_tables(self, value: bool):
        ...

    ...

