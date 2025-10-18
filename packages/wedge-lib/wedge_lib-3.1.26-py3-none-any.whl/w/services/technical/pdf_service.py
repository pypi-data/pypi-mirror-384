from io import BytesIO
from pathlib import Path
from typing import List, Union

from django.template.loader import render_to_string
from weasyprint import HTML

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService

# Note: The 'pypdf' package needs to be installed for the pdf2text and merge methods to work
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover
    PdfReader = None
    PdfWriter = None


class PdfService(AbstractService):
    @classmethod
    def merge(
        cls, pdf_files: List[str], output_filename: str = None
    ) -> Union[None, BytesIO]:
        """
        Merge multiple PDF files into a single PDF.

        Args:
            pdf_files (List[str]): List of paths to PDF files to merge
            output_filename (str, optional): Path to save the merged PDF.
                                            If None, returns the merged PDF as bytes.

        Returns:
            Union[None, bytes]: If output_filename is provided, returns None after writing the file.
                               Otherwise, returns the merged PDF as bytes.

        Raises:
            RuntimeError: If pypdf is not installed, if the list is empty, or if any file doesn't exist
        """
        # Check if PdfWriter is available
        if PdfWriter is None:  # pragma: no cover
            raise RuntimeError(
                "The 'pypdf' package is not installed. "
                "Please install it to use this method."
            )

        # Check if the list is empty
        if not pdf_files:
            raise RuntimeError("Cannot merge an empty list of PDF files")

        for pdf_file in pdf_files:
            FilesystemService.check_file_exists(pdf_file)

        # Create a PDF writer
        merger = PdfWriter()

        # Add each PDF to the writer
        for pdf_file in pdf_files:
            merger.append(pdf_file)

        if output_filename:
            FilesystemService.create_missing(output_filename)
            merged_pdf = output_filename
        else:
            merged_pdf = BytesIO()

        merger.write(merged_pdf)
        merger.close()

        if output_filename:
            return None
        return merged_pdf

    @classmethod
    def generate(cls, content) -> bytes:
        """
        Generate PDF binary data.

        Args:
            content (str|dict): message or template (as dict) :
                    {"template_name": <str>, "context": <dict> }

        Returns:
            bytes: pdf binary data
        """
        return cls._generate(content)

    @classmethod
    def write_file(cls, filename, content) -> None:
        """
        Create a PDF file.

        Args:
            filename (str): output file path
            content (str|dict): message or template (as dict) :
                {"template_name": <str>, "context": <dict> }

        Returns:
            None
        """
        FilesystemService.check_dir_exists(str(Path(filename).parent))
        return cls._generate(content, filename)

    @classmethod
    def pdf2text(cls, filename) -> str:
        """
        Extract text from a PDF file.
        Args:
            filename (str): path to the PDF file
        Returns:
            str: extracted text from the PDF
        Raises:
            RuntimeError: if the file doesn't exist, is not a valid PDF, or if the pypdf package is not installed
        """
        # Check if PdfReader is available
        if PdfReader is None:  # pragma: no cover
            raise RuntimeError(
                "The 'pypdf' package is not installed. "
                "Please install it to use this method."
            )

        # Check if the file exists
        FilesystemService.check_file_exists(filename)

        try:
            pdf_binary = FilesystemService.read_binary_file(filename)
            reader = PdfReader(BytesIO(pdf_binary))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

    @classmethod
    def _generate(cls, content, filename=None) -> Union[None, bytes]:
        """
        Generate PDF binary data.

        Args:
            content (str|dict): message or template (as dict) :
                    {"template_name": <str>, "context": <dict> }

        Returns:
            bytes: pdf binary data
        """
        if not content:
            raise RuntimeError("Can't generate pdf binary with empty content provided")

        # html content
        if isinstance(content, dict):
            content = render_to_string(**content)
        html = HTML(string=content)
        pdf = html.write_pdf(filename)

        return pdf
