import SeleniumLibrary.errors
import time
import os
import logging
from RPA.Browser.Selenium import Selenium
from urllib.parse import urlparse
from datetime import datetime, timedelta
from .exceptions import check_rpaframework_import

check_rpaframework_import()


class SitesCore:
    def __init__(
        self,
        login: str,
        password: str,
        auth_totp_key: str,
        url: str,
        timeout: int = 30,
        temp_folder: str = "",
        headless: bool = True,
    ):
        """
        Basic site core

        :param login: Login for the some sites
        :param password: Password for the some site
        :param url: URL for the some site
        :param otp_code: OTP code for the some site
        :param auth_totp_key: TOTP key for the some site
        :param timeout: Timeout for actions
        :param temp_folder: Path to temp folder (default download path)
        """
        self.url: str = url
        self.login: str = login
        self.password: str = password
        self.auth_totp_key: str = auth_totp_key
        self.browser: Selenium = Selenium()
        self.browser.timeout = timeout
        self.temp_folder = temp_folder
        self._headless = headless

        self.output_folder = os.path.join(os.environ.get("ROBOT_ROOT", os.getcwd()), "output")
        self.is_site_available: bool = False
        self.is_password_expired: bool = False
        self.base_url: str = self.get_base_url(self.url)

    @staticmethod
    def get_base_url(url: str) -> str:
        """
        Get base URL for concatenation in the future.

        :return: base URL (without / ending)
        """
        parsed_uri = urlparse(url)
        base_url: str = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return base_url

    def wait_element(self, xpath: str, timeout: int = 60, is_need_screenshot: bool = True) -> bool:
        """
        Wait element some time.

        :param xpath: Xpath of the element
        :param timeout: How long to wait if the item does not appear?
        :param is_need_screenshot: Do need to take a screenshot?
        :return: True if element found, else False
        """
        is_success: bool = False
        timer: datetime = datetime.now() + timedelta(seconds=timeout)

        while not is_success and timer > datetime.now():
            if self.browser.does_page_contain_element(xpath):
                try:
                    is_success = self.browser.find_element(xpath).is_displayed()
                except SeleniumLibrary.errors.ElementNotFound:
                    time.sleep(1)
        if not is_success and is_need_screenshot:
            now: datetime = datetime.now()
            logging.warning(f'[{now.strftime("%H:%M:%S")}] Element \'{xpath}\' not available')
            self.browser.capture_page_screenshot(
                os.path.join(self.output_folder, f'Element_not_available_{now.strftime("%H_%M_%S")}.png')
            )
        return is_success

    def does_element_displayed(self, xpath: str) -> bool:
        if self.browser.does_page_contain_element(xpath):
            return self.browser.find_element(xpath).is_displayed()
        return False

    def click(self, xpath: str) -> None:
        """
        Click on element via javascript

        :param xpath: Xpath of the element
        :return: None
        """
        self.browser.driver.execute_script("arguments[0].click();", self.browser.find_element(xpath))

    def wait_and_click(self, xpath: str, timeout: int = 60) -> bool:
        """
        Wait element and click on it.

        :param xpath: Xpath of the element.
        :param timeout: How long to wait if the item does not appear?
        :return: True if element appear and clicked.
        """
        if self.wait_element(xpath, timeout):
            self.browser.scroll_element_into_view(xpath)
            self.click(xpath)
            return True
        return False

    def click_bunch_of_elements(self, bunch_of_xpath: list) -> None:
        """
        Wait and click on bunch (list) of elements.

        :param bunch_of_xpath: List of Xpathes
        :return: None
        """
        xpath: str
        for xpath in bunch_of_xpath:
            self.wait_and_click(xpath)

    def open_new_tab(self) -> None:
        """
        Open new tab and switch back to current tab.

        :return: None
        """
        current_window_handle = self.browser.driver.current_window_handle
        self.browser.execute_javascript("window.open('" + self.url + "');")
        self.browser.switch_window(current_window_handle)
