import json
import time
from datetime import timedelta
from threading import Event, Thread

import requests
from RPA.Browser.Playwright import Playwright
from retry import retry
from fake_useragent import UserAgent

from .exceptions import VersantError, BadRequestError, WrongCredentialsError, BrowserError


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


class VersantRequestsCore:
    def __init__(self, login: str, password: str, url: str = "https://ecp.versanthealth.com/prelogin/login"):
        """
        VersantSuperiorRequestsCore object. Please Inheritance it.

        :param login: login for CentralReach site.
        :param password: password for CentralReach site.
        """
        self.session = requests.session()
        # usable user-agent
        self.user_agent = UserAgent().chrome
        # Login data
        self.__login = login
        self.__password = password
        self.__url = url

        self._transaction_id = ""  # Get from login response
        self._user_id = login

        # Get from local storage
        self._tax_id = ""
        self._bearer_token = ""
        self._bearer_token_type = ""
        self._bearer_token_expired_in = ""  # TODO implement refresh
        self._bearer_refresh_token = ""  # TODO implement refresh

        self._login_to_versant(self.__login, self.__password, self.__url)

    @staticmethod
    def __setup_browser(open_as_headless=True):
        """
        Open new browser and apply settings
        """
        from Browser import SupportedBrowsers

        browser = Playwright()
        browser.set_browser_timeout(timedelta(seconds=100))
        browser.new_browser(SupportedBrowsers.chromium, headless=open_as_headless, timeout=timedelta(seconds=120))
        browser.new_context(userAgent=UserAgent().chrome)
        browser.new_page()
        return browser

    @staticmethod
    def _is_json_response(response) -> bool:
        try:
            response.json()
            return True
        except json.decoder.JSONDecodeError:
            return False

    def check_response(
        self,
        response,
        mandatory_json: bool = False,
        exc_message: str = "",
        re_authorize: bool = True,
        check_resp_obj: bool = False,
    ) -> None:
        """
        This method check response and raise exception 'BadRequestError'
        If status code is 401 (unauthorized) then it will try login again
        :param response: response from request
        :param mandatory_json: bool, if True - it will check is response contain json data
        :param exc_message: text message which will be raise if response wrong
        :param re_authorize: bool, if True then it will try login again if status code is 401
        """
        if re_authorize and response.status_code == 401:
            self._login_to_versant(self.__login, self.__password, self.__url)
            raise BadRequestError(
                f"{exc_message}Status Code: {response.status_code} (Unauthorized request), "
                f"Json content: {response.json()}, Headers: {response.headers}"
            )

        if response.status_code != 200 or (mandatory_json and not self._is_json_response(response)):
            exc_message = exc_message + "\n" if exc_message else ""
            if self._is_json_response(response):
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, "
                    f"Json content: {response.json()}, Headers: {response.headers}"
                )
            else:
                raise BadRequestError(
                    f"{exc_message}Status Code: {response.status_code}, " f"Headers: {response.headers}"
                )
        if check_resp_obj:
            response_json = response.json()
            if "body" not in response_json:
                raise VersantError("Response doesn't contain body")

            if "responseObject" not in response_json["body"]:
                if "messages" in response_json["body"] and response_json["body"]["messages"]:
                    messages = []
                    for message in response_json["body"]["messages"]:
                        messages.append(
                            f"{message['errorIdentifier'] if 'errorIdentifier' in message else '-'}: "
                            f"{message['description']}"
                        )
                    messages_str = "\n".join(messages)
                    raise VersantError(
                        "Response doesn't contain 'responseObject', " f"error messages: \n{messages_str}"
                    )
                else:
                    raise VersantError("Response doesn't contain 'responseObject'")

    @retry(BrowserError, tries=2)
    def _login_to_versant(self, login: str, password: str, url: str):
        browser = None
        try:
            try:
                from Browser.utils.data_types import PageLoadStates

                browser = self.__setup_browser()
                browser.go_to(url=url, timeout=timedelta(seconds=180), wait_until=PageLoadStates.domcontentloaded)

                browser.wait_for_elements_state('//*[@id="username"]', timeout=timedelta(seconds=120))
                browser.fill_text('//*[@id="username"]', login)
                browser.fill_text('//*[@id="password"]', password)

                # To catch the response of the login, we start to wait until the click of the Login button
                response = {}

                def wait_for_response(ev: Event):
                    nonlocal response
                    login_url = "https://api.versanthealth.com/AccessManagementSecured/api/AccessManagement/Login"
                    response = browser.wait_for_response(login_url, timeout=timedelta(seconds=60))
                    ev.set()

                event = Event()

                t1 = Thread(target=wait_for_response, args=(event,))  # Start wait for response
                t1.start()

                time.sleep(1)
                browser.click('//button[@class="btn btn-light submit-button"]')  # Click of the Login button
                is_event_succ = event.wait(600.0)  # Wait while response is ready

                if not is_event_succ:
                    raise BrowserError("Timeout of 600 seconds reached on login.")

            except Exception as ex:
                raise BrowserError(f"Can't login to Versant. Exception: {ex}") from ex

            response_body = response["body"]["body"]
            if response_body["statuscode"] != "OK":
                if response_body["messages"]:
                    error_message: dict = response_body["messages"][0]
                    if error_message["code"] == "11.01.05":
                        raise WrongCredentialsError(
                            "Versant login attempt failed due to incorrect credentials. "
                            f"Details: {error_message['description']}"
                        )
                raise VersantError("Can't login to Versant")

            self._transaction_id = response["body"]["header"]["transactionid"]

            self._tax_id = json.loads(browser.local_storage_get_item("userDetails"))["taxId"]
            self._bearer_token = json.loads(browser.local_storage_get_item("bearerToken"))["access_token"]
            self._bearer_token_type = json.loads(browser.local_storage_get_item("bearerToken"))["token_type"]
            self._bearer_token_expired_in = json.loads(browser.local_storage_get_item("bearerToken"))["expires_in"]
            self._bearer_refresh_token = json.loads(browser.local_storage_get_item("bearerToken"))["refresh_token"]

            if not self._bearer_token:
                raise BadRequestError(
                    "Session doesn't contain the required cookie 'bearer-token' after logging into Versant"
                )

            # Check authorization
            try:
                self.get_office_locations_by_tax_id()
            except BadRequestError:
                raise BadRequestError("Session is unauthorized after login to Versant")
        finally:
            if browser is not None:
                browser.close_browser("CURRENT")

    @retry_if_bad_request
    def get_office_locations_by_tax_id(self):
        url = "https://api.versanthealth.com/ProviderService/GetOfficeLocationsByTaxId"
        response = self.session.post(url, headers=self.get_headers(), json=self.get_payload())

        exception_message = "Problems with getting office by tax id."
        self.check_response(response, mandatory_json=True, exc_message=exception_message)
        return response.json()

    def get_payload(self, body_payload: dict = {}) -> dict:
        return {
            "header": {"transactionId": self._transaction_id, "userId": self._user_id, "taxId": self._tax_id},
            "body": body_payload,
        }

    def get_headers(self, is_json=True, put_token=True, add_headers: dict = None) -> dict:
        """
        Prepare header object for request.

        :param is_json (bool): True if content-type should be json, else False.
        :param put_token (bool): True if 'csrf-token' should be added to headers, else False.
        :param add_headers (dict): dictionary with key-values that should be added to headers.
        """
        headers = {}
        if is_json:
            headers["Content-Type"] = "application/json"

        if put_token:
            headers["Authorization"] = f"{self._bearer_token_type} {self._bearer_token}"

        if add_headers:
            for key, value in add_headers.items():
                headers[key] = value
        return headers
