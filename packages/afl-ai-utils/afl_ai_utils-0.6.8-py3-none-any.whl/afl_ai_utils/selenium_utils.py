from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from selenium.webdriver.chrome.options import Options
from random import randint
import time
import shutil


class SeleniumUtils:
    def __init__(self, min_wait_time, max_wait_time):
        self.min_wait_time = min_wait_time
        self.max_wait_time = max_wait_time

    def launch_browser(self,
                       url: str,
                       headless: bool,
                       local_identifier: [str, None],
                       prod_identifier: [str, None],
                       chrome_driver_path: [str, None],
                       file_download_folder_path: [str, None]):
        chrome_options = Options()
        # chrome_options.add_argument("start-maximized");
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        if file_download_folder_path:
            prefs = {"download.default_directory": file_download_folder_path,
                     "download.prompt_for_download": False,
                     "download.directory_upgrade": True,
                     "safebrowsing_for_trusted_sources_enabled": False,
                     "safebrowsing.enabled": False,
                     "profile.default_content_setting_values.notifications": 2}

            try:
                shutil.rmtree(file_download_folder_path)
                os.mkdir(file_download_folder_path)
            except Exception as e:
                os.mkdir(file_download_folder_path)
        else:
            prefs = {"profile.default_content_setting_values.notifications": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument('--disable-gpu')  # May be required for headless mode on some systems
            from fake_headers import Headers

            header = Headers(
                browser="chrome",  # Generate only Chrome UA
                os="win",  # Generate only Windows platform
                headers=False  # generate misc headers
            )
            customUserAgent = header.generate()['User-Agent']

            chrome_options.add_argument(f"user-agent={customUserAgent}")

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("detach", True)
        # if (prod_identifier in os.getcwd() or local_identifier in os.getcwd()) and chrome_driver_path is not None:
        #     service = Service(executable_path=chrome_driver_path)
        #     print("Using prod env ", chrome_driver_path)
        # else:
        #     service = Service()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        driver.maximize_window()  # For maximizing window
        driver.implicitly_wait(randint(self.min_wait_time, self.max_wait_time))
        time.sleep(randint(self.min_wait_time, self.max_wait_time))
        return driver
