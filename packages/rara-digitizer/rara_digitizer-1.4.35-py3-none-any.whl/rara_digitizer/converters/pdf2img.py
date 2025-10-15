import io
import logging
import tempfile

import ocrmypdf
from pdf2image import convert_from_bytes

logger = logging.getLogger("rara-digitizer")


class PDFToCleanedIMGConverter:
    """
    Handles the pre-processing of objects requiring OCR, including deskewing and cleaning using OCRmyPDF.
    Converts cleaned objects into temporary image files for further processing.
    """

    def __init__(self) -> None:
        """
        Initializes the PDFToCleanedIMGConverter.
        """
        pass

    def clean_convert_document_to_temp_imgs(self, input_bytes: io.BytesIO) -> list[str]:
        """
        Runs deskewing and cleaning on the PDF/JPG/PNG using OCRmyPDF and saves each page as a temporary image file.

        Parameters
        ----------
        input_bytes : io.BytesIO
            The in-memory bytes of the input PDF or image.

        Returns
        -------
        list[str]
            List of file paths to the saved images.
        """
        cleaned_input_bytes = self._deskew_and_clean_with_ocrmypdf(input_bytes)
        page_image_paths = self._save_pdf_pages_as_temp_images(cleaned_input_bytes)
        return page_image_paths

    def _deskew_and_clean_with_ocrmypdf(
        self, input_pdf_bytes: io.BytesIO
    ) -> io.BytesIO:
        """
        Processes the PDF/JPG/PNG file with OCRmyPDF and creates an image-based PDF.

        Parameters
        ----------
        input_pdf_bytes : io.BytesIO
            The in-memory bytes of the input PDF or image.

        Returns
        -------
        io.BytesIO
            The in-memory bytes of the processed PDF.
        """
        input_pdf_bytes.seek(0)
        output_pdf_bytes = io.BytesIO()

        try:
            logger.info("Running OCRmyPDF cleaning without OCR on the in-memory input PDF.")
            ocrmypdf.ocr(
                input_pdf_bytes,
                output_pdf_bytes,
                deskew=True,
                force_ocr=True,
                output_type="pdf",
                clean_final=True,
                progress_bar=False,
                tesseract_timeout=0,
                optimize=0,
            )
            output_pdf_bytes.seek(0)
            return output_pdf_bytes
        except Exception:
            logger.warning(f"OCRmyPDF failed during PDF cleaning. Falling back to rasterization without cleaning.")
            input_pdf_bytes.seek(0)
            return input_pdf_bytes

    def _save_pdf_pages_as_temp_images(self, pdf_bytes: io.BytesIO) -> list[str]:
        """
        Converts the processed PDF to individual image files for each page and saves them as temporary files.

        Parameters
        ----------
        pdf_bytes : io.BytesIO
            The in-memory bytes of the processed PDF.

        Returns
        -------
        list[str]
            A list of file paths to the temporary image files for each page of the PDF.
        """
        images = convert_from_bytes(pdf_bytes.read(), dpi=300)
        temp_image_paths = []
        for page_number, img in enumerate(images, 1):
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            img.save(tmp, "PNG")
            tmp.close()
            temp_image_paths.append(tmp.name)

            logger.info(
                f"Saved temporary image for page {page_number} at {tmp.name}"
            )
        return temp_image_paths
