import logging
from ..basic.core import SitesCore
import os
import traceback
from datetime import timedelta


class SalesforceCore(SitesCore):
    """
    Salesforce object. Please Inheritance it.
    """

    def get_mfa_code(self) -> str:
        """
        Please, modify this function in your code
        :return:
        """

        return ""

    def get_email_code(self) -> str:
        """
        Please, modify this function in your code
        :return:
        """

        return ""

    def login_to_site(self) -> bool:
        self.is_site_available = False
        self.browser.close_browser()

        if self.temp_folder:
            if not os.path.exists(self.temp_folder):
                os.mkdir(self.temp_folder)
            self.browser.set_download_directory(self.temp_folder, True)

        for i in range(1, 4):
            try:
                self.browser.open_chrome_browser(self.url)
                self.browser.set_browser_implicit_wait(timedelta(seconds=30))
                self.browser.set_window_size(1920, 1080)
                # self.browser.maximize_browser_window()

                self.wait_element('//input[@id="username"]')
                self.browser.input_text('//input[@id="username"]', self.login)
                self.browser.input_text('//input[@id="password"]', self.password)
                self.browser.click_element('//input[@id="Login" and @type="submit"]')

                self.wait_element('//input[@id="tc"]', timeout=5, is_need_screenshot=False)
                if self.does_element_displayed('//input[@id="tc"]'):
                    self.browser.input_text('//input[@id="tc"]', self.get_mfa_code())
                elif self.does_element_displayed('//input[@id="emc"]'):
                    self.browser.input_text('//input[@id="emc"]', self.get_email_code())

                if self.does_element_displayed('//input[@id="save"]'):
                    self.browser.click_element('//input[@id="save"]')

                self.wait_element('//button[@aria-label="Search"]')
                if self.browser.does_page_contain_element('//button[@aria-label="Search"]'):
                    self.base_url = self.get_base_url(self.browser.get_location())
                    self.is_site_available = True
                    return True
            except Exception as ex:
                logging.error(f"Login failed. Attempt {i}")
                logging.error(str(ex))
                traceback.print_exc()
                self.browser.capture_page_screenshot(os.path.join(self.output_folder, f"Login_failed_Attempt_{i}.png"))
                self.browser.close_browser()
        return False
