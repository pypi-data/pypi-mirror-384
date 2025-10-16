import fitz
import base64
import re
import logging
import os
import requests
from urllib.parse import urlparse
from user_sim.utils import config
from user_sim.utils.register_management import save_register, load_register, hash_generate
from user_sim.handlers.image_recognition_module import image_description

logger = logging.getLogger('Info Logger')
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, "../.."))
pdfs_dir = config.pdfs_path
pdf_register_name = "pdf_register.json"


def pdf_reader(pdf: str) -> str:
    """
    Extract text and image descriptions from a PDF file, with caching support.

    Args:
        pdf (str): Path to the PDF file.

    Returns:
        str: A string containing the extracted text and image descriptions,
             formatted with page numbers. If cached, returns the cached result.

    Notes:
        - Uses `image_description()` to describe images embedded in the PDF.
        - Caching behavior depends on `config.ignore_cache` and `config.update_cache`.
        - Each page is prefixed with "Page nª{page_number}" in the output.
    """
    if config.ignore_cache:
        register = {}
        logger.info("Cache will be ignored.")
    else:
        register = load_register(pdf_register_name)

    pdf_hash = hash_generate(content_type="pdf", content=pdf)

    def process_pdf(pdf_file: str) -> str:
        doc = fitz.open(pdf_file)
        plain_text = ""
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            plain_text += f"Page nª{page_number}: {page.get_text()} "

            images = page.get_images(full=True)
            if images:
                plain_text += f"Images in this page: "
                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_base64 = base64.b64encode(image_bytes)
                    description = image_description(image_base64, detailed=False, url=False)
                    plain_text += f"Image description {img_index + 1}: {description}"
        return f"(PDF content: {plain_text} >>)"

    if pdf_hash in register:
        if config.update_cache:
            output_text = process_pdf(pdf)
            register[pdf_hash] = output_text
            logger.info("Cache updated!")
        output_text = register[pdf_hash]
        logger.info("Retrieved information from cache.")

    else:
        output_text = process_pdf(pdf)
        register[pdf_hash] = output_text

    if config.ignore_cache:
        logger.info("PDF cache was ignored.")
    else:
        save_register(register, pdf_register_name)
        logger.info("PDF cache was saved!")

    logger.info(output_text)
    return output_text


def get_pdf(url: str) -> str | None:
    """
    Download a PDF from a given URL and save it locally.

    Args:
        url (str): The URL pointing to the PDF file.

    Returns:
        str | None: The local path to the saved PDF file if successful,
        or None if the content is not a PDF.
        In case of connection issues, returns an error message string.

    Behavior:
        - Detects PDFs by checking the `Content-Type` header.
        - Attempts to extract filename from the `Content-Disposition` header,
          otherwise uses the last part of the URL or defaults to `pdf_download.pdf`.
        - Saves the file under `<project_root>/data/pdfs/`.
        - Creates the directory if it does not exist.

    Notes:
        - Adds a `User-Agent` header to mimic a browser.
        - Supports PDFs with or without filename metadata in the response headers.
    """
    # response = requests.get(url)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return f"Error accessing the page: {response.status_code}"

    response.encoding = response.apparent_encoding
    content_type = response.headers.get("Content-Type", "")

    filename = None
    content_disposition = response.headers.get('Content-Disposition', '')

    if 'application/pdf' in content_type:
        extension = ".pdf"

        pdfs_dir = os.path.join(project_root, "data/pdfs")

        if not os.path.exists(pdfs_dir):
            os.makedirs(pdfs_dir)

        if 'filename=' in content_disposition:
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)

        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = 'pdf_download'
            if extension and not filename.endswith(extension):
                filename += extension

        full_path = os.path.join(pdfs_dir, filename)
        content = response.content

        with open(full_path, 'wb') as f:
            f.write(content)

        return full_path

    else:
        return None


def pdf_processor(pdf_url: str) -> str | None:
    """
    Process a PDF from a URL by downloading and extracting its content.

    Args:
        pdf_url (str): URL pointing to the PDF file.

    Returns:
        str | None: Extracted text and image descriptions from the PDF,
        or None if the URL is invalid or not a PDF.
    """
    if pdf_url is None:
        return pdf_url
    else:
        pdf_path = get_pdf(pdf_url)
        if pdf_path is not None:
            description = pdf_reader(pdf_path)
            return description
