"""
----------------------------------------------------------------------
>>> Author       : Junshan Yin  
>>> Last Updated : 2025-10-13
----------------------------------------------------------------------
"""

import zipfile
import os, time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def unzip_file(zip_path: str, unzip_folder: str):
    """
    Args:
        zip_path (str): Path to the ZIP file to extract.
        dest_folder (str, optional): Folder to extract files into. 
            If None, the function will create a folder with the same 
            name as the ZIP file (without extension).

    Examples:
        >>> zip_path = "./downloads/data.zip"
        >>> unzip_folder = "./exp_data/data"
        >>> unzip_file(zip_path, unzip_folder)
    """

    if unzip_folder is None:
        unzip_folder = os.path.splitext(os.path.basename(zip_path))[0]

    os.makedirs(unzip_folder, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(unzip_folder)

    print(f"✅ Extracted '{zip_path}' to '{os.path.abspath(unzip_folder)}'")


# =============================================================
#                   JIANGUOYUN (NUTSTORE) CHROME VERSION
# =============================================================

from selenium.webdriver.chrome.options import Options as ChromeOptions
class JianguoyunDownloaderChrome:
    """ Example:
    >>> url = "https://www.jianguoyun.com/p/DSQqUq8QqdHDDRiy6I0GIAA"
    >>> downloader = JianguoyunDownloaderChrome(url)
    >>> downloader.run()
    """
    def __init__(self, url, download_path="./exp_data"):
        self.url = url
        self.download_path = os.path.abspath(download_path)
        os.makedirs(self.download_path, exist_ok=True)

        self.chrome_options = ChromeOptions()
        prefs = {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        self.chrome_options.add_experimental_option("prefs", prefs)
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")
        # Uncomment for headless mode:
        # self.chrome_options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=self.chrome_options)

    def open_page(self):
        print(f"🌐 Opening page: {self.url}")
        self.driver.get(self.url)
        print(f"✅ Page loaded: {self.driver.title}")

    def click_download_button(self):
        """Find and click the 'Download' button (supports English and Chinese)."""
        print("🔍 Searching for the download button...")
        wait = WebDriverWait(self.driver, 30)

        try:
            # Match both English 'Download' (case-insensitive) and Chinese '下载'
            xpath = (
                "//span[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //button[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //a[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //span[contains(text(),'下载')]"
                " | //button[contains(text(),'下载')]"
                " | //a[contains(text(),'下载')]"
            )

            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

            # Click using JavaScript to avoid overlay or interaction issues
            self.driver.execute_script("arguments[0].click();", button)
            print(f"✅ Download button clicked. Files will be saved to: {self.download_path}")

            # If the cloud service opens a new tab, switch to it
            time.sleep(3)
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("📂 Switched to the new download tab.")

        except Exception as e:
            print("❌ Failed to find or click the download button:", e)
            raise


    def wait_for_downloads(self, timeout=3600):
        print("⏳ Waiting for downloads to finish...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            downloading = [f for f in os.listdir(self.download_path) if f.endswith(".crdownload")]
            if not downloading:
                print("✅ Download completed!")
                return
            time.sleep(2)
        print("⚠️ Timeout: download not completed within 1 hour")

    def close(self):
        self.driver.quit()
        print("🚪 Browser closed.")

    def run(self):
        print('*' * 60)
        try:
            self.open_page()
            self.click_download_button()
            self.wait_for_downloads()
        except Exception as e:
            print("❌ Error:", e)
        finally:
            self.close()
        print('*' * 60)


# =============================================================
#                   JIANGUOYUN (NUTSTORE) FIREFOX VERSION
# =============================================================

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service

class JianguoyunDownloaderFirefox:
    """ Example:
    >>> url = "https://www.jianguoyun.com/p/DSQqUq8QqdHDDRiy6I0GIAA"
    >>> downloader = JianguoyunDownloaderFirefox(url)
    >>> downloader.run()
    """
    def __init__(self, url, download_path="./exp_data"):
        self.url = url
        self.download_path = os.path.abspath(download_path)
        os.makedirs(self.download_path, exist_ok=True)

        options = FirefoxOptions()
        options.add_argument("--headless")
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", self.download_path)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk",
                            "application/zip,application/octet-stream,application/x-zip-compressed,multipart/x-zip")
        options.set_preference("pdfjs.disabled", True)

        service = Service("/snap/bin/geckodriver")
        self.driver = webdriver.Firefox(service=service, options=options)

    def open_page(self):
        print(f"🌐 Opening page: {self.url}")
        self.driver.get(self.url)
        print(f"✅ Page loaded: {self.driver.title}")

    def click_download_button(self):
        """Find and click the 'Download' button (supports English and Chinese)."""
        print("🔍 Searching for the download button...")
        wait = WebDriverWait(self.driver, 30)

        try:
            # Match both English 'Download' (case-insensitive) and Chinese '下载'
            xpath = (
                "//span[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //button[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //a[contains(translate(text(),'DOWNLOAD下载','download下载'),'download')]"
                " | //span[contains(text(),'下载')]"
                " | //button[contains(text(),'下载')]"
                " | //a[contains(text(),'下载')]"
            )

            button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

            # Click using JavaScript to avoid overlay or interaction issues
            self.driver.execute_script("arguments[0].click();", button)
            print(f"✅ Download button clicked. Files will be saved to: {self.download_path}")

            # If the cloud service opens a new tab, switch to it
            time.sleep(3)
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                print("📂 Switched to the new download tab.")

        except Exception as e:
            print("❌ Failed to find or click the download button:", e)
            raise

    def wait_for_download(self, timeout=3600):
        """Wait until all downloads are finished (auto-detects browser type)."""
        print("⏳ Waiting for downloads to finish...")
        start_time = time.time()

        # Determine the temporary file extension based on the browser type
        temp_ext = ".crdownload" if "chrome" in self.driver.capabilities["browserName"].lower() else ".part"

        while time.time() - start_time < timeout:
            downloading = [f for f in os.listdir(self.download_path) if f.endswith(temp_ext)]
            if not downloading:
                print("✅ Download completed!")
                return True
            time.sleep(2)


    def close(self):
        print("🛑 Closing browser...")
        self.driver.quit()

    def run(self):
        print('*' * 60)
        try:
            self.open_page()
            self.click_download_button()
            self.wait_for_download(timeout=3600)
        except Exception as e:
            print("❌ Error:", e)
        finally:
            self.close()
        print('*' * 60)

def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


