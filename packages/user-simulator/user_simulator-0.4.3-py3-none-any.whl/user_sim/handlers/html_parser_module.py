import requests
import platform
import shutil
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from user_sim.handlers.image_recognition_module import image_description
from user_sim.utils import config
from user_sim.utils.register_management import save_register, load_register, hash_generate


logger = logging.getLogger('Info Logger')

wp_register_name = "webpage_register.json"


def is_driver_installed(driver_name: str) -> bool:
    """
    Check if a given driver is installed and available in the system PATH.

    Args:
        driver_name (str): The name of the driver executable to check (e.g., "chromedriver").

    Returns:
        bool: True if the driver is found in PATH, False otherwise.
    """
    return shutil.which(driver_name) is not None


def get_webdriver():
    """
    Initialize and return a Selenium WebDriver instance based on the current OS.

    Behavior:
        - Windows: Tries Microsoft Edge (msedgedriver). Falls back to auto-install if missing.
        - MacOS (Darwin): Uses Safari WebDriver.
        - Linux: Tries Firefox (geckodriver). Falls back to auto-install if missing.
        - Other/Unknown: Tries Chrome (chromedriver). Falls back to auto-install if missing.

    Returns:
        selenium.webdriver: A WebDriver instance ready to use.

    Raises:
        Exception: If no supported WebDriver can be initialized.
    """
    system = platform.system()

    if system == "Windows":
        print("Using Microsoft Edge on Windows")
        if is_driver_installed("msedgedriver"):
            return webdriver.Edge()
        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service)

    elif system == "Darwin":  # MacOS
        print("Using Safari on Mac")
        return webdriver.Safari()

    elif system == "Linux":
        print("Using Firefox on Linux")
        if is_driver_installed("geckodriver"):
                return webdriver.Firefox()
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service)

    else:
        print("Unknown system. Trying Chrome...")
        if is_driver_installed("chromedriver"):
            return webdriver.Chrome()
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service)


def is_dynamic_page(url: str) -> bool:
    """
    Determine if a webpage likely requires JavaScript rendering.

    The function fetches the page using `requests` with a standard User-Agent header.
    It assumes a page is dynamic if:
        - The response is successful but the visible text is very short.
        - The content-type is not standard HTML.

    Args:
        url (str): Target webpage URL.

    Returns:
        bool: True if the page is likely dynamic (JS-rendered), False otherwise.
    """
    min_text_length = 200
    headers = {"User-Agent": "Mozilla/5.0"}  # Simulate a real browser
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return False  # If the page does not respond, assume it's not JS

    # Check content type
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        logger.warning(f"Expected HTML, but got {content_type}")
        return False

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    # Check if there is little visible content
        text = soup.get_text(strip=True)

        if len(text) < min_text_length:  # Adjust threshold based on page type
            return True  # Probably uses JavaScript

    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        # todo: add error code
        return False

    return False  # The page has enough static content


def uses_ajax(url: str) -> bool:
    """
    Check if a webpage likely uses AJAX (fetch or XMLHttpRequest).

    This function inspects the raw HTML source for common AJAX keywords.
    It does not execute JavaScript, so results are only an approximation.

    Args:
        url (str): Target webpage URL.

    Returns:
        bool: True if AJAX patterns are detected, False otherwise.
    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    if response.status_code != 200:
        return False

    return "fetch" in response.text or "XMLHttpRequest" in response.text


def detect_scraping_method(url: str) -> str:
    """
    Decide the best scraping method for a given URL.

    - If the page is dynamic (little static text) or likely uses AJAX,
      returns 'selenium'.
    - Otherwise, returns 'requests'.

    Args:
        url (str): Target webpage URL.

    Returns:
        str: Either 'selenium' (for dynamic content) or 'requests' (for static HTML).
    """
    if is_dynamic_page(url) or uses_ajax(url):
        return "selenium"
    return "requests"


def describe_images_in_webpage(url: str, soup) -> str:
    """
    Extract and describe all images from a parsed webpage.

    Args:
        url (str): Base URL of the webpage, used to resolve relative image paths.
        soup (BeautifulSoup): Parsed HTML content of the page.

    Returns:
        str: Concatenated descriptions of all images found in the page.
    """
    image_descriptions = []
    for img_index, img in enumerate(soup.find_all("img")):
        try:
            src = img.get("src")
            if src:
                full_url = urljoin(url, src)
                description = image_description(full_url, detailed=False)
                image_descriptions.append(f"Image description {img_index}: {description}")

        except Exception as e:
            logger.error(f"Error describing image {img_index} on {url}: {e}")

    image_text = " ".join(image_descriptions)
    return image_text


def webpage_reader(url: str) -> str:
    """
    Fetches and processes the content of a webpage, using cache when available.

    Args:
        url (str): Webpage URL.

    Returns:
        str: Textual description of the page content, including images if detected.
    """
    if config.ignore_cache:
        register = {}
        logger.info("Cache will be ignored.")
    else:
        register = load_register(wp_register_name)

    wp_hash = hash_generate(content=url)

    def process_html(url: str) -> str | None:
        """Fetch and clean HTML content from a webpage."""
        method = detect_scraping_method(url)

        if method == "selenium":
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = get_webdriver()

            driver.get(url)
            page_source = driver.page_source
            driver.quit()

            try:
                soup = BeautifulSoup(page_source, "lxml")
            except Exception as e:
                logger.error(f"Error parsing JavaScript-rendered HTML: {e}")
                return None

        else:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                logger.error(f"Error accessing the page: {response.status_code}")
                return None

            # Ensure proper encoding
            response.encoding = response.apparent_encoding

            # Check if the response is actually HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                logger.warning(f"Expected HTML, but got {content_type}")
                return None

            try:
                soup = BeautifulSoup(response.text, "lxml")  # More robust parser
            except Exception as e:
                logger.error(f"Error parsing HTML: {e}")
                return None

        # Remove unnecessary elements
        for script in soup(["script", "style", "header", "footer", "nav", "aside"]):
            script.extract()

        text = soup.get_text(separator=" ", strip=True)
        images = describe_images_in_webpage(url, soup)
        description = f"(Web page content: {text + images} >>)"
        return description

    if wp_hash in register:
        if config.update_cache:
            output_text = process_html(url)
            if output_text is None:
                logger.error("Cache couldn't be updated due to web page error.")
                return f"(Web page content: web page couldn't be loaded.)"
            register[wp_hash] = output_text
            logger.info("Cache updated!")
        output_text = register[wp_hash]
        logger.info("Retrieved information from cache.")
    else:
        output_text = process_html(url)
        if output_text:
            register[wp_hash] = output_text
        else:
            output_text = f"(Web page content: web page couldn't be loaded.)"

    if config.ignore_cache:
        logger.info("PDF cache was ignored.")
    else:
        save_register(register, wp_register_name)
        logger.info("PDF cache was saved!")

    logger.info(output_text)
    return output_text
