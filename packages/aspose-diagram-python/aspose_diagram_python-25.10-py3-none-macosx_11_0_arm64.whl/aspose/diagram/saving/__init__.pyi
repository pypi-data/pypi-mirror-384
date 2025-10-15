from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.diagram
import aspose.diagram.activexcontrols
import aspose.diagram.autolayout
import aspose.diagram.manipulation
import aspose.diagram.printing
import aspose.diagram.properties
import aspose.diagram.saving
import aspose.diagram.vba

class DiagramSaveOptions(SaveOptions):
    
    @overload
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def __init__(self, save_format : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def auto_fit_page_to_drawing_content(self) -> bool:
        raise NotImplementedError()
    
    @auto_fit_page_to_drawing_content.setter
    def auto_fit_page_to_drawing_content(self, value : bool) -> None:
        raise NotImplementedError()
    

class HTMLSaveOptions(RenderingSaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_tool_bar(self) -> bool:
        raise NotImplementedError()
    
    @save_tool_bar.setter
    def save_tool_bar(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def export_hidden_page(self) -> bool:
        raise NotImplementedError()
    
    @export_hidden_page.setter
    def export_hidden_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def save_title(self) -> bool:
        raise NotImplementedError()
    
    @save_title.setter
    def save_title(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def stream_provider(self) -> aspose.diagram.saving.IStreamProvider:
        raise NotImplementedError()
    
    @stream_provider.setter
    def stream_provider(self, value : aspose.diagram.saving.IStreamProvider) -> None:
        raise NotImplementedError()
    
    @property
    def save_as_single_file(self) -> bool:
        raise NotImplementedError()
    
    @save_as_single_file.setter
    def save_as_single_file(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def resolution(self) -> int:
        raise NotImplementedError()
    
    @resolution.setter
    def resolution(self, value : int) -> None:
        raise NotImplementedError()
    

class IPageSavingCallback:
    '''Control/Indicate progress of page saving process.'''
    
    def page_start_saving(self, args : aspose.diagram.saving.PageStartSavingArgs) -> None:
        '''Control/Indicate a page starts to be output.
        
        :param args: Info for a page starts saving process.'''
        raise NotImplementedError()
    
    def page_end_saving(self, args : aspose.diagram.saving.PageEndSavingArgs) -> None:
        '''Control/Indicate a page ends to be output.
        
        :param args: Info for a page ends saving process.'''
        raise NotImplementedError()
    

class IStreamProvider:
    '''Represents the exported stream provider.'''
    
    def init_stream(self, options : aspose.diagram.StreamProviderOptions) -> None:
        '''Gets the stream.'''
        raise NotImplementedError()
    
    def close_stream(self, options : aspose.diagram.StreamProviderOptions) -> None:
        '''Closes the stream.'''
        raise NotImplementedError()
    

class ImageSaveOptions(RenderingSaveOptions):
    
    def __init__(self, save_format : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    
    @property
    def image_brightness(self) -> float:
        raise NotImplementedError()
    
    @image_brightness.setter
    def image_brightness(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def image_color_mode(self) -> aspose.diagram.saving.ImageColorMode:
        raise NotImplementedError()
    
    @image_color_mode.setter
    def image_color_mode(self, value : aspose.diagram.saving.ImageColorMode) -> None:
        raise NotImplementedError()
    
    @property
    def image_contrast(self) -> float:
        raise NotImplementedError()
    
    @image_contrast.setter
    def image_contrast(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def jpeg_quality(self) -> int:
        raise NotImplementedError()
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def export_hidden_page(self) -> bool:
        raise NotImplementedError()
    
    @export_hidden_page.setter
    def export_hidden_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def resolution(self) -> float:
        raise NotImplementedError()
    
    @resolution.setter
    def resolution(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def scale(self) -> float:
        raise NotImplementedError()
    
    @scale.setter
    def scale(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def content_zoom(self) -> float:
        raise NotImplementedError()
    
    @content_zoom.setter
    def content_zoom(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def tiff_compression(self) -> aspose.diagram.saving.TiffCompression:
        raise NotImplementedError()
    
    @tiff_compression.setter
    def tiff_compression(self, value : aspose.diagram.saving.TiffCompression) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def same_as_pdf_conversion_area(self) -> bool:
        raise NotImplementedError()
    
    @same_as_pdf_conversion_area.setter
    def same_as_pdf_conversion_area(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def pixel_offset_mode(self) -> aspose.diagram.saving.PixelOffsetMode:
        raise NotImplementedError()
    
    @pixel_offset_mode.setter
    def pixel_offset_mode(self, value : aspose.diagram.saving.PixelOffsetMode) -> None:
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> aspose.diagram.saving.SmoothingMode:
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : aspose.diagram.saving.SmoothingMode) -> None:
        raise NotImplementedError()
    
    @property
    def compositing_quality(self) -> aspose.diagram.saving.CompositingQuality:
        raise NotImplementedError()
    
    @compositing_quality.setter
    def compositing_quality(self, value : aspose.diagram.saving.CompositingQuality) -> None:
        raise NotImplementedError()
    
    @property
    def interpolation_mode(self) -> aspose.diagram.saving.InterpolationMode:
        raise NotImplementedError()
    
    @interpolation_mode.setter
    def interpolation_mode(self, value : aspose.diagram.saving.InterpolationMode) -> None:
        raise NotImplementedError()
    

class PageEndSavingArgs(PageSavingArgs):
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @property
    def has_more_pages(self) -> bool:
        raise NotImplementedError()
    
    @has_more_pages.setter
    def has_more_pages(self, value : bool) -> None:
        raise NotImplementedError()
    

class PageSavingArgs:
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    

class PageSize:
    
    @overload
    def __init__(self, paper_size_format : aspose.diagram.saving.PaperSizeFormat) -> None:
        raise NotImplementedError()
    
    @overload
    def __init__(self, width : float, height : float) -> None:
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def paper_size_format(self) -> aspose.diagram.saving.PaperSizeFormat:
        raise NotImplementedError()
    
    @paper_size_format.setter
    def paper_size_format(self, value : aspose.diagram.saving.PaperSizeFormat) -> None:
        raise NotImplementedError()
    

class PageStartSavingArgs(PageSavingArgs):
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @property
    def is_to_output(self) -> bool:
        raise NotImplementedError()
    
    @is_to_output.setter
    def is_to_output(self, value : bool) -> None:
        raise NotImplementedError()
    

class PdfDigitalSignatureDetails:
    
    def __init__(self, certificate : Any, reason : str, location : str, signature_date : datetime, hash_algorithm : aspose.diagram.saving.PdfDigitalSignatureHashAlgorithm) -> None:
        raise NotImplementedError()
    
    @property
    def certificate(self) -> Any:
        raise NotImplementedError()
    
    @certificate.setter
    def certificate(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def reason(self) -> str:
        raise NotImplementedError()
    
    @reason.setter
    def reason(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def location(self) -> str:
        raise NotImplementedError()
    
    @location.setter
    def location(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def signature_date(self) -> datetime:
        raise NotImplementedError()
    
    @signature_date.setter
    def signature_date(self, value : datetime) -> None:
        raise NotImplementedError()
    
    @property
    def hash_algorithm(self) -> aspose.diagram.saving.PdfDigitalSignatureHashAlgorithm:
        raise NotImplementedError()
    
    @hash_algorithm.setter
    def hash_algorithm(self, value : aspose.diagram.saving.PdfDigitalSignatureHashAlgorithm) -> None:
        raise NotImplementedError()
    

class PdfEncryptionDetails:
    
    def __init__(self, user_password : str, owner_password : str, encryption_algorithm : aspose.diagram.saving.PdfEncryptionAlgorithm) -> None:
        raise NotImplementedError()
    
    @property
    def user_password(self) -> str:
        raise NotImplementedError()
    
    @user_password.setter
    def user_password(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def owner_password(self) -> str:
        raise NotImplementedError()
    
    @owner_password.setter
    def owner_password(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def permissions(self) -> aspose.diagram.saving.PdfPermissions:
        raise NotImplementedError()
    
    @permissions.setter
    def permissions(self, value : aspose.diagram.saving.PdfPermissions) -> None:
        raise NotImplementedError()
    
    @property
    def encryption_algorithm(self) -> aspose.diagram.saving.PdfEncryptionAlgorithm:
        raise NotImplementedError()
    
    @encryption_algorithm.setter
    def encryption_algorithm(self, value : aspose.diagram.saving.PdfEncryptionAlgorithm) -> None:
        raise NotImplementedError()
    

class PdfSaveOptions(RenderingSaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def compliance(self) -> aspose.diagram.saving.PdfCompliance:
        raise NotImplementedError()
    
    @compliance.setter
    def compliance(self, value : aspose.diagram.saving.PdfCompliance) -> None:
        raise NotImplementedError()
    
    @property
    def encryption_details(self) -> aspose.diagram.saving.PdfEncryptionDetails:
        raise NotImplementedError()
    
    @encryption_details.setter
    def encryption_details(self, value : aspose.diagram.saving.PdfEncryptionDetails) -> None:
        raise NotImplementedError()
    
    @property
    def page_saving_callback(self) -> aspose.diagram.saving.IPageSavingCallback:
        raise NotImplementedError()
    
    @page_saving_callback.setter
    def page_saving_callback(self, value : aspose.diagram.saving.IPageSavingCallback) -> None:
        raise NotImplementedError()
    
    @property
    def jpeg_quality(self) -> int:
        raise NotImplementedError()
    
    @jpeg_quality.setter
    def jpeg_quality(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> int:
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> int:
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def split_multi_pages(self) -> bool:
        raise NotImplementedError()
    
    @split_multi_pages.setter
    def split_multi_pages(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def export_hidden_page(self) -> bool:
        raise NotImplementedError()
    
    @export_hidden_page.setter
    def export_hidden_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def text_compression(self) -> aspose.diagram.saving.PdfTextCompression:
        raise NotImplementedError()
    
    @text_compression.setter
    def text_compression(self, value : aspose.diagram.saving.PdfTextCompression) -> None:
        raise NotImplementedError()
    
    @property
    def digital_signature_details(self) -> aspose.diagram.saving.PdfDigitalSignatureDetails:
        raise NotImplementedError()
    
    @digital_signature_details.setter
    def digital_signature_details(self, value : aspose.diagram.saving.PdfDigitalSignatureDetails) -> None:
        raise NotImplementedError()
    

class PrintSaveOptions(RenderingSaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    

class RenderingSaveOptions(SaveOptions):
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    

class SVGSaveOptions(RenderingSaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_size(self) -> aspose.diagram.saving.PageSize:
        raise NotImplementedError()
    
    @page_size.setter
    def page_size(self, value : aspose.diagram.saving.PageSize) -> None:
        raise NotImplementedError()
    
    @property
    def shapes(self) -> aspose.diagram.ShapeCollection:
        raise NotImplementedError()
    
    @shapes.setter
    def shapes(self, value : aspose.diagram.ShapeCollection) -> None:
        raise NotImplementedError()
    
    @property
    def area(self) -> Any:
        raise NotImplementedError()
    
    @area.setter
    def area(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def export_guide_shapes(self) -> bool:
        raise NotImplementedError()
    
    @export_guide_shapes.setter
    def export_guide_shapes(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.diagram.EmfRenderSetting:
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.diagram.EmfRenderSetting) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def export_hidden_page(self) -> bool:
        raise NotImplementedError()
    
    @export_hidden_page.setter
    def export_hidden_page(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def svg_fit_to_view_port(self) -> bool:
        raise NotImplementedError()
    
    @svg_fit_to_view_port.setter
    def svg_fit_to_view_port(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def export_element_as_rect_tag(self) -> bool:
        raise NotImplementedError()
    
    @export_element_as_rect_tag.setter
    def export_element_as_rect_tag(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_export_scale_in_matrix(self) -> bool:
        raise NotImplementedError()
    
    @is_export_scale_in_matrix.setter
    def is_export_scale_in_matrix(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_saving_image_separately(self) -> bool:
        raise NotImplementedError()
    
    @is_saving_image_separately.setter
    def is_saving_image_separately(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_saving_custom_line_pattern(self) -> bool:
        raise NotImplementedError()
    
    @is_saving_custom_line_pattern.setter
    def is_saving_custom_line_pattern(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def custom_image_path(self) -> str:
        raise NotImplementedError()
    
    @custom_image_path.setter
    def custom_image_path(self, value : str) -> None:
        raise NotImplementedError()
    

class SWFSaveOptions(SaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def viewer_included(self) -> bool:
        raise NotImplementedError()
    
    @viewer_included.setter
    def viewer_included(self, value : bool) -> None:
        raise NotImplementedError()
    

class SaveOptions:
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    

class TxtSaveOptions(SaveOptions):
    
    @overload
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def __init__(self, format : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    

class XAMLSaveOptions(SaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def stream_provider(self) -> aspose.diagram.saving.IStreamProvider:
        raise NotImplementedError()
    
    @stream_provider.setter
    def stream_provider(self, value : aspose.diagram.saving.IStreamProvider) -> None:
        raise NotImplementedError()
    

class XPSSaveOptions(SaveOptions):
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @staticmethod
    def create_save_options(save_format : aspose.diagram.SaveFileFormat) -> aspose.diagram.saving.SaveOptions:
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.diagram.SaveFileFormat:
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.diagram.SaveFileFormat) -> None:
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.diagram.IWarningCallback:
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.diagram.IWarningCallback) -> None:
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def save_foreground_pages_only(self) -> bool:
        raise NotImplementedError()
    
    @save_foreground_pages_only.setter
    def save_foreground_pages_only(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def export_hidden_page(self) -> bool:
        raise NotImplementedError()
    
    @export_hidden_page.setter
    def export_hidden_page(self, value : bool) -> None:
        raise NotImplementedError()
    

class CompositingQuality:
    
    INVALID : CompositingQuality
    DEFAULT : CompositingQuality
    HIGH_SPEED : CompositingQuality
    HIGH_QUALITY : CompositingQuality
    GAMMA_CORRECTED : CompositingQuality
    ASSUME_LINEAR : CompositingQuality

class ImageColorMode:
    
    NONE : ImageColorMode
    GRAYSCALE : ImageColorMode
    BLACK_AND_WHITE : ImageColorMode

class InterpolationMode:
    
    INVALID : InterpolationMode
    DEFAULT : InterpolationMode
    LOW : InterpolationMode
    HIGH : InterpolationMode
    BILINEAR : InterpolationMode
    BICUBIC : InterpolationMode
    NEAREST_NEIGHBOR : InterpolationMode
    HIGH_QUALITY_BILINEAR : InterpolationMode
    HIGH_QUALITY_BICUBIC : InterpolationMode

class PaperSizeFormat:
    
    CUSTOM : PaperSizeFormat
    A0 : PaperSizeFormat
    A1 : PaperSizeFormat
    A2 : PaperSizeFormat
    A3 : PaperSizeFormat
    A4 : PaperSizeFormat
    A5 : PaperSizeFormat
    A6 : PaperSizeFormat
    A7 : PaperSizeFormat
    B0 : PaperSizeFormat
    B1 : PaperSizeFormat
    B2 : PaperSizeFormat
    B3 : PaperSizeFormat
    B4 : PaperSizeFormat
    B5 : PaperSizeFormat
    B6 : PaperSizeFormat
    B7 : PaperSizeFormat
    C0 : PaperSizeFormat
    C1 : PaperSizeFormat
    C2 : PaperSizeFormat
    C3 : PaperSizeFormat
    C4 : PaperSizeFormat
    C5 : PaperSizeFormat
    C6 : PaperSizeFormat
    C7 : PaperSizeFormat
    LETTER : PaperSizeFormat
    LEGAL : PaperSizeFormat
    LEGAL13 : PaperSizeFormat
    TABLOID : PaperSizeFormat
    EXECUTIVE : PaperSizeFormat
    DL : PaperSizeFormat
    COM9 : PaperSizeFormat
    COM10 : PaperSizeFormat
    MONARCH : PaperSizeFormat

class PdfCompliance:
    
    PDF15 : PdfCompliance
    PDF_A1A : PdfCompliance
    PDF_A1B : PdfCompliance

class PdfDigitalSignatureHashAlgorithm:
    
    SHA1 : PdfDigitalSignatureHashAlgorithm
    SHA256 : PdfDigitalSignatureHashAlgorithm
    SHA384 : PdfDigitalSignatureHashAlgorithm
    SHA512 : PdfDigitalSignatureHashAlgorithm
    MD5 : PdfDigitalSignatureHashAlgorithm

class PdfEncryptionAlgorithm:
    
    RC4_40 : PdfEncryptionAlgorithm
    RC4_128 : PdfEncryptionAlgorithm

class PdfPermissions:
    
    DISALLOW_ALL : PdfPermissions
    PRINTING : PdfPermissions
    MODIFY_CONTENTS : PdfPermissions
    CONTENT_COPY : PdfPermissions
    MODIFY_ANNOTATIONS : PdfPermissions
    FILL_IN : PdfPermissions
    CONTENT_COPY_FOR_ACCESSIBILITY : PdfPermissions
    DOCUMENT_ASSEMBLY : PdfPermissions
    HIGH_RESOLUTION_PRINTING : PdfPermissions
    ALLOW_ALL : PdfPermissions

class PdfTextCompression:
    
    NONE : PdfTextCompression
    FLATE : PdfTextCompression

class PixelOffsetMode:
    
    INVALID : PixelOffsetMode
    DEFAULT : PixelOffsetMode
    HIGH_SPEED : PixelOffsetMode
    HIGH_QUALITY : PixelOffsetMode
    NONE : PixelOffsetMode
    HALF : PixelOffsetMode

class SmoothingMode:
    
    INVALID : SmoothingMode
    DEFAULT : SmoothingMode
    HIGH_SPEED : SmoothingMode
    HIGH_QUALITY : SmoothingMode
    NONE : SmoothingMode
    ANTI_ALIAS : SmoothingMode

class TiffCompression:
    
    NONE : TiffCompression
    RLE : TiffCompression
    LZW : TiffCompression
    CCITT3 : TiffCompression
    CCITT4 : TiffCompression

