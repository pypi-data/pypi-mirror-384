import json
import time
from datetime import timedelta, datetime

import requests
from RPA.Browser.Selenium import Selenium
from requests import Response
from retry import retry

from .exceptions import BadRequestError, AlwaysCareOtpCodeError


def retry_if_bad_request(func):
    attempt = 1
    tries = 3

    @retry(exceptions=BadRequestError, tries=tries, delay=1, backoff=2)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BadRequestError as ex:
            nonlocal attempt
            print(f"Bad request Attempt {attempt}...", "WARN")
            attempt = attempt + 1 if attempt < tries else 1
            raise ex

    return wrapper


class AlwaysCareRequestsCore:
    def __init__(self, login: str, password: str, url: str = "https://unumvisionpwp.skygenusasystems.com/PWP/Landing"):
        """
        AlwaysCareRequestsCore object. Please Inheritance it.

        :param login: login for CentralReach site.
        :param password: password for CentralReach site.
        """
        self.session = requests.session()
        # Login data
        self.__login = login
        self.__password = password
        self.__url = url

        self._session_xsrf_token = ""  # Get after login

        self._login_to_always_care(self.__login, self.__password, self.__url)

    def get_otp_code(self) -> str:
        """
        Please, modify this function in your code
        :return:
        """
        raise NotImplementedError("The method for getting the otp must be implemented in the descendant class")

    @retry((BadRequestError, AlwaysCareOtpCodeError), tries=2)
    def _login_to_always_care(self, login: str, password: str, url: str):
        browser = Selenium()
        try:
            browser.set_selenium_timeout(value=timedelta(seconds=60))
            browser.open_available_browser(url=url, headless=True)

            browser.wait_until_element_is_visible('//input[@id="UserName"]', timeout=timedelta(seconds=60))

            browser.input_text_when_element_is_visible('//input[@id="UserName"]', login)
            browser.input_text_when_element_is_visible('//input[@id="Password"]', password)
            browser.click_element_when_visible('//button[@id="LoginBlockButton"]')

            # Waiting for otp code page
            browser.wait_until_element_is_visible('//*[@id="VerificationCodeTextBox"]', timeout=timedelta(seconds=60))

            code = self.get_otp_code()
            browser.input_text_when_element_is_visible('//*[@id="VerificationCodeTextBox"]', code)
            browser.click_element_when_visible('//button[@id="SubmitButton"]')

            try:
                browser.wait_until_element_is_visible(
                    '//form[@id="eligibility-search-form"]', timeout=timedelta(seconds=60)
                )
            except AssertionError as ex:
                if browser.is_element_visible('//*[text()="Invalid verification code."]'):
                    raise AlwaysCareOtpCodeError("Invalid verification code for Always Care.")
                raise ex

            # Check and get cookies
            timeout_time = datetime.now() + timedelta(seconds=30)
            while datetime.now() < timeout_time:
                try:
                    # Set cookies
                    for name, value in browser.get_cookies(as_dict=True).items():
                        self.session.cookies.set(name, value)

                    # Save csrf-token
                    try:
                        self._session_xsrf_token = self.session.cookies["XSRF-TOKEN"]
                    except KeyError:
                        raise BadRequestError(
                            "Session doesn't contain the required cookie 'XSRF-TOKEN' after logging into Always Care"
                        )

                    # Check authorization
                    self.get_locations(re_authorize=False)
                    break
                except BadRequestError:
                    browser.reload_page()
                    browser.wait_until_element_is_visible('//*[text()="Invalid verification code."]')
                    time.sleep(5)
                    continue
            else:
                raise BadRequestError("Session is unauthorized after login to Always Care")
        finally:
            browser.close_browser()

    def _logout(self):
        if self._session_xsrf_token:
            self.session.get("https://unumvisionpwp.skygenusasystems.com/Account/LogOff")
            self._session_xsrf_token = ""

    def __del__(self):
        try:
            self._logout()
        except Exception:
            pass

    def get_headers(self, is_json=True, put_token=True, add_headers: dict = None) -> dict:
        """
        Prepare header object for request.

        :param is_json (bool): True if content-type should be json, else False.
        :param put_token (bool): True if 'csrf-token' should be added to headers, else False.
        :param add_headers (dict): dictionary with key-values that should be added to headers.
        """
        headers = {}
        if is_json:
            headers["Content-Type"] = "application/json;charset=UTF-8"

        if put_token:
            headers["X-XSRF-TOKEN"] = self._session_xsrf_token

        if add_headers:
            for key, value in add_headers.items():
                headers[key] = value
        return headers

    @staticmethod
    def _is_json_response(response) -> bool:
        try:
            result = response.json()
            if not isinstance(result, dict):
                return False
            return True
        except json.decoder.JSONDecodeError:
            return False

    def check_response(
        self, response: Response, mandatory_json: bool = False, exc_message: str = "", re_authorize: bool = True
    ) -> None:
        """
        This method check response and raise exception 'BadRequestError'
        If status code is 401 (unauthorized) then it will try login again
        :param response: response from request
        :param mandatory_json: bool, if True - it will check is response contain json data
        :param exc_message: text message which will be raise if response wrong
        :param re_authorize: bool, if True then it will try login again if status code is 401
        """

        exc_message = exc_message + "\n" if exc_message else ""

        def raise_bad_request_error():
            if self._is_json_response(response):
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, "
                    f"Json content: {response.json()}, Headers: {response.headers}"
                )
            else:
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, " f"Headers: {response.headers}"
                )

        if re_authorize and response.status_code == 401:
            self._login_to_always_care(self.__login, self.__password, self.__url)
            raise BadRequestError(
                f"{exc_message}Status Code: {response.status_code} (Unauthorized request), "
                f"Json content: {response.json()}, Headers: {response.headers}"
            )

        if response.status_code != 200 or (mandatory_json and not self._is_json_response(response)):
            if re_authorize:
                self._login_to_always_care(self.__login, self.__password, self.__url)
            raise_bad_request_error()

        # Always Care case
        if response.status_code == 200 and self._is_json_response(response):
            if "statusCode" in response.json() and response.json()["statusCode"] == 500:
                if re_authorize:
                    self._login_to_always_care(self.__login, self.__password, self.__url)
                raise_bad_request_error()

    @retry_if_bad_request
    def get_locations(self, re_authorize=True):
        payload = {
            "GET_LOCATION": True,
            "GET_PROVIDER": True,
            "USE_COOKIE_FOR_PROVIDER": True,
        }
        url = "https://unumvisionpwp.skygenusasystems.com/DropList/GetSearchCriteriaDropdowns"

        response = self.session.get(url=url, headers=self.get_headers(put_token=True), json=payload)

        exception_message = "Problems with getting locations."
        self.check_response(response, mandatory_json=True, exc_message=exception_message, re_authorize=re_authorize)

        return response.json()

    @retry_if_bad_request
    def get_member_eligibility_search(
        self,
        provider_id: int,
        location_id: int,
        birth_date: datetime,
        service_date: datetime,
        first_name: str = None,
        last_name: str = None,
        subscriber_id: str = None,
    ):
        payload = {
            "LAST_NAME": last_name,
            "FIRST_NAME": first_name,
            "DOB": birth_date.strftime("%m/%d/%Y"),
            "SUBSCRIBER_ID": subscriber_id,
            "DATE_OF_SERVICE": service_date.strftime("%m/%d/%Y"),
            "LOCATION_ID": location_id,
            "PROVIDER_ID": provider_id,
            "SSN": "",
            "Log": True,
        }
        url = "https://unumvisionpwp.skygenusasystems.com/Welcome/MemberEligibilitySearch/"
        response = self.session.post(url, headers=self.get_headers(put_token=True), json=payload)

        exception_message = "Problems with getting member eligibility search result."
        self.check_response(response, mandatory_json=True, exc_message=exception_message)

        return response.json()
