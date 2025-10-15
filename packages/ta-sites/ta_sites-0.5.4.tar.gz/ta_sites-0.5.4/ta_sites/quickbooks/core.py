import logging
import os
import traceback
from time import sleep
from datetime import datetime, timedelta
from ..basic.core import SitesCore
from .grouped_row import GroupedRow
from SeleniumLibrary.errors import SeleniumLibraryException
from selenium.common.exceptions import StaleElementReferenceException


class QuickbooksCore(SitesCore):
    """
    Quickbooks object. Please Inheritance it.
    """

    def get_otp_code(self) -> str:
        """
        Please, modify this function in your code
        :return:
        """
        return ""

    def send_message_service_type_not_found(self, manager: str, customer_or_service: str) -> None:
        pass

    def send_message_invoice_added(self, manager: str, customer: str, invoice_number: str, total_rate: float) -> None:
        pass

    def send_message_estimate_added(self, manager: str, customer: str, estimate_number: str, total_rate: float) -> None:
        pass

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
                self.browser.set_window_size(1920, 1080)
                # self.browser.maximize_browser_window()

                self.wait_element('//input[@id="ius-signin-userId-input"]', timeout=30, is_need_screenshot=False)
                if self.does_element_displayed('//input[@id="ius-signin-userId-input"]'):
                    self.browser.input_text('//input[@id="ius-signin-userId-input"]', self.login)
                else:
                    self.browser.input_text('//input[@id="ius-userid"]', self.login)

                if self.does_element_displayed('//input[@id="ius-password"]'):
                    self.browser.input_text('//input[@id="ius-password"]', self.password)
                    self.browser.click_element_when_visible('//button[@id="ius-sign-in-submit-btn"]')
                else:
                    self.browser.click_element_when_visible('//button[@id="ius-identifier-first-submit-btn"]')

                    self.wait_element('//input[@data-testid="currentPasswordInput"]', 30, False)
                    if self.does_element_displayed('//input[@data-testid="currentPasswordInput"]'):
                        self.browser.input_text('//input[@data-testid="currentPasswordInput"]', self.password)
                        self.browser.click_element_when_visible(
                            '//button[@data-testid="passwordVerificationContinueButton"]'
                        )
                    else:
                        self.wait_element('//input[@id="ius-sign-in-mfa-password-collection-current-password"]')
                        self.browser.input_text(
                            '//input[@id="ius-sign-in-mfa-password-collection-current-password"]', self.password
                        )
                        self.browser.click_element_when_visible(
                            '//input[@id="ius-sign-in-mfa-password-collection-continue-btn"]'
                        )

                self.wait_element("//div[text()=\"Let's make sure you're you\"]", timeout=10, is_need_screenshot=False)
                if self.does_element_displayed("//div[text()=\"Let's make sure you're you\"]"):
                    self.browser.click_element_when_visible('//span[@id="ius-sublabel-mfa-email-otp"]')
                    if self.does_element_displayed('//input[@id="ius-mfa-options-submit-btn"]'):
                        self.browser.click_element_when_visible('//input[@id="ius-mfa-options-submit-btn"]')

                    self.wait_element('//input[@id="ius-mfa-confirm-code"]')
                    self.browser.input_text('//input[@id="ius-mfa-confirm-code"]', self.get_otp_code())
                    self.browser.click_element_when_visible('//input[@id="ius-mfa-otp-submit-btn"]')

                if self.browser.does_page_contain_element('//button[@id="ius-verified-user-update-btn-skip"]'):
                    self.browser.click_element_when_visible('//button[@id="ius-verified-user-update-btn-skip"]')

                self.wait_element('//*[@data-id="navigation-container"]')
                if self.does_element_displayed('//*[@data-id="navigation-container"]'):
                    self.base_url = self.get_base_url(self.browser.get_location())
                    self.is_site_available = True
                    return True
            except Exception as ex:
                logging.error(f"Login failed. Attempt {i}", "ERROR")
                logging.error(str(ex))
                traceback.print_exc()
                self.browser.capture_page_screenshot(os.path.join(self.output_folder, f"Login_failed_Attempt_{i}.png"))
                self.browser.close_browser()
        return False

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
            # self.__close_specific_windows('//button[@aria-label="Close"]')

            if self.browser.does_page_contain_element(xpath):
                try:
                    is_success = self.browser.find_element(xpath).is_displayed()
                except SeleniumLibraryException:
                    sleep(1)

        if not is_success and is_need_screenshot:
            now: datetime = datetime.now()
            logging.warning(f'[{now.strftime("%H:%M:%S")}] Element \'{xpath}\' not available')
            self.browser.capture_page_screenshot(
                os.path.join(self.output_folder, f'Element_not_available_{now.strftime("%H_%M_%S")}.png')
            )
            html_file: str = os.path.join(self.output_folder, f'Element_not_available_{now.strftime("%H_%M_%S")}.html')
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(self.browser.get_source())

        return is_success

    def __close_specific_windows(self, xpath: str) -> None:
        if self.browser.does_page_contain_element(xpath):
            elements: list = self.browser.find_elements(xpath)
            for element in elements:
                try:
                    if element.is_displayed():
                        logging.warning(
                            "A pop-up appeared and the bot closed it. Please validate the screenshot in the artifacts."
                        )
                        self.browser.capture_page_screenshot(
                            os.path.join(self.output_folder, f'Pop_up_{datetime.now().strftime("%H_%M_%S")}.png')
                        )
                        element.click()
                        self.browser.wait_until_element_is_not_visible(f"({xpath})[{elements.index(element) + 1}]")
                except (AssertionError, SeleniumLibraryException, StaleElementReferenceException):
                    sleep(1)

    def go_to_client_page(self, client_name: str) -> None:
        """
        Navigate to client page

        :param client_name: Client name
        :return: None
        """
        self.click_bunch_of_elements(['//span[text()="GO TO QUICKBOOKS"]', f'//span[text()="{client_name}"]'])
        self.wait_element(f'//div[contains(@class, "companyName") and text()="{client_name}"]')

    def open_add_invoice_page(self) -> None:
        """
        Open page 'Add invoice'
        """
        self.browser.go_to(f"{self.base_url}/app/homepage")

        self.click_bunch_of_elements(['//button[@data-id="global_create_button"]', '//a[@data-id="invoice"]'])

    def open_add_estimate_page(self) -> None:
        """
        Open page 'Add estimate'
        """
        self.browser.go_to(f"{self.base_url}/app/homepage")

        self.click_bunch_of_elements(['//button[@data-id="global_create_button"]', '//a[@data-id="estimate"]'])

    def open_invoices_page(self) -> None:
        """
        Check paid page
        """
        self.browser.go_to(f"{self.base_url}/app/homepage")
        self.click_bunch_of_elements(
            [
                '//span[text()="Sales"]/..',
                '//a[text()="Invoices"]',
                '//th[@data-column-id="date"]',
                '//div[contains(@class, "TextFieldWrapper")]//input[not(@data-automation-id)]',
                '//li[text()="Paid"]',
                '//div[contains(@class, "TextFieldWrapper")]//input[@data-automation-id="date-dropdown"]',
                '//li[text()="Last 3 months"]',
            ]
        )
        self.wait_element('//th[@data-column-id="date" and contains(@class, "sorted-desc")]', 5, False)
        if not self.browser.does_page_contain_element(
            '//th[@data-column-id="date" and contains(@class, "sorted-desc")]'
        ):
            self.browser.click_element_when_visible('//th[@data-column-id="date"]')
        self.wait_element('//div[@data-sale-status="PAID"]/../..', 15, False)

    def add_invoice(self, grouped_rows: list, is_prod: bool = False) -> (bool, str, str):
        """
        Returns the bool if the new invoice was created and sent.

        :param grouped_rows: List of invoice data:
            customer: Customer name, column Account from spreadsheet
            service: Service name, column Service Type from spreadsheet
            description: Description column from spreadsheet
            rate: Amount column from spreadsheet
            processing_fee: True if column 3% Markup from spreadsheet has value Yes
        :param is_prod: If true bot will perform all change
        :return: status (bool): Bool value indicate if new invoice was created and sent
        """
        self.open_add_invoice_page()

        first_row: GroupedRow = grouped_rows[0]
        customer: str = first_row.customer

        self.wait_element('//input[@aria-label="Select a customer"]')
        self.browser.input_text('//input[@aria-label="Select a customer"]', customer.replace("\\", "\\\\"))

        self.wait_element(f'//span[text()="Add new"]/../span[text()="{customer}"]', 10, False)

        xpath_customers: str = '//div[@aria-label="Select a customer"]/div[not(@aria-label)]//span[@class="mainLabel"]'
        customers: list = self.browser.find_elements(xpath_customers)
        if len(customers) > 1:
            for i in range(3):
                sleep(1)
                customers: list = self.browser.find_elements(xpath_customers)
                if len(customers) == 1:
                    break
        if not customers:
            customers: list = self.browser.find_elements('//span[@class="dijitComboBoxHighlightMatch"]')

        selected: bool = False
        for customer_id in customers:
            if str(customer_id.text).strip().lower() == customer.strip().lower():
                self.browser.click_element_when_visible(customer_id)
                selected = True
                break
        if not selected:
            for customer_id in customers:
                if customer.strip().lower() in str(customer_id.text).strip().lower():
                    self.browser.click_element_when_visible(customer_id)
                    selected = True
                    break
        if not selected:
            self.browser.capture_page_screenshot(
                os.path.join(self.output_folder, f'No_customer_{datetime.now().strftime("%H_%M_%S")}.png')
            )
            self.send_message_service_type_not_found(first_row.manager, customer)
            return False, "", ""

        index: int = 1
        total_rate: float = 0.0
        row: GroupedRow
        for row in grouped_rows:
            service: str = row.service
            description: str = row.description
            rate: float = row.rate
            total_rate += rate

            self.browser.click_element_when_visible(f'//td[text()="{index}"]')
            self.wait_element('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]')
            self.browser.input_text('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]', service)

            self.wait_element(
                f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]', 5, False
            )
            if not self.does_element_displayed(
                f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]'
            ):
                self.wait_element(f'//div/span/b[text()="{service}"]')
                if not self.does_element_displayed(f'//div/span/b[text()="{service}"]'):
                    self.browser.capture_page_screenshot(
                        os.path.join(self.output_folder, f'No_service_{datetime.now().strftime("%H_%M_%S")}.png')
                    )
                    self.send_message_service_type_not_found(first_row.manager, service)
                    return False, "", ""
                else:
                    self.browser.click_element_when_visible(f'//div/span/b[text()="{service}"]')
            else:
                self.browser.click_element_when_visible(
                    f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]'
                )

            self.browser.input_text('//textarea[@data-automation-id="input-description-txndetails"]', description)
            self.browser.input_text('//input[@data-automation-id="input-rateField"]', str(rate))
            index += 1

        total_rate = round(total_rate, 2)
        processing_fee: bool = first_row.processing_fee
        if processing_fee:
            processing_fee_name: str = "3% QuickBooks Processing Fee"
            self.browser.click_element_when_visible(f'//td[text()="{index}"]')
            self.wait_element('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]')
            self.browser.input_text(
                '//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]', processing_fee_name
            )

            self.wait_element(f'//div/span/b[text()="{processing_fee_name}"]')
            self.browser.click_element_when_visible(f'//div/span/b[text()="{processing_fee_name}"]')
            sleep(0.5)

            self.wait_element('//input[@data-automation-id="input-rateField"]')
            self.browser.input_text(
                '//input[@data-automation-id="input-rateField"]', str("%.2f" % (total_rate / 0.97 - total_rate))
            )

        self.wait_element(
            '//input[@data-automation-id="input-dropdown-terms-sales"]/..//div[contains(@class, "dropDownImage")]'
        )
        self.browser.click_element_when_visible(
            '//input[@data-automation-id="input-dropdown-terms-sales"]/..//div[contains(@class, "dropDownImage")]'
        )
        self.wait_element('//div[text()="Due on receipt"]')
        self.browser.click_element_when_visible('//div[text()="Due on receipt"]')

        invoice_date: str = self.browser.get_value('//input[@data-automation-id="input-creation-date-sales"]')
        invoice_number: str = "1234"
        if is_prod:
            self.browser.click_element_when_visible('//button[text()="Save and send"]')
            self.wait_element('//button[text()="Send and close"]')
            invoice_number = self.browser.get_text('//div[@data-qbo-bind="text: referenceNumber"]')
            self.browser.click_element_when_visible('//button[text()="Send and close"]')
        else:
            print("Dev test. The invoice was not saved")
            self.browser.capture_page_screenshot(
                os.path.join(
                    self.output_folder, f'Test_run-customer_{customer}-{datetime.now().strftime("%H_%M_%S")}.png'
                )
            )
            self.browser.click_element_when_visible('//i[@aria-label="Close"]')
            self.wait_element('//button[text()="Yes"]', 5)
            if self.does_element_displayed('//button[text()="Yes"]'):
                self.browser.click_element_when_visible('//button[text()="Yes"]')
        self.send_message_invoice_added(
            first_row.manager,
            first_row.customer,
            invoice_number,
            total_rate,
        )

        return True, invoice_date, invoice_number

    def open_customers_page(self) -> None:
        """
        Open Customers page
        """
        self.browser.go_to(f"{self.base_url}/app/homepage")
        self.click_bunch_of_elements(['//span[text()="Sales"]/..', '//a[text()="Customers"]'])
        self.wait_element('//li[contains(@class, "active")]/a[text()="Customers"]', 5, False)

    def add_new_customer(self, customer_name: str, first_name: str, last_name: str, email: str) -> bool:
        self.open_customers_page()

        self.wait_and_click('//span[text()="New customer"]/..')
        self.wait_element('//input[@name="companyName"]')

        self.browser.input_text('//input[@name="companyName"]', customer_name)
        self.browser.input_text('//input[@name="firstName"]', first_name)
        self.browser.input_text('//input[@name="lastName"]', last_name)
        self.browser.input_text('//input[@name="displayName"]', customer_name)
        self.browser.input_text('//input[@name="email"]', email)

        self.browser.click_element_when_visible('//button[@data-automation-id="saveButton"]')
        self.wait_element(f'//p[@data-qbo-bind="text: companyName" and text()="{customer_name}"]', 15, False)
        if self.does_element_displayed(f'//p[@data-qbo-bind="text: companyName" and text()="{customer_name}"]'):
            return True
        else:
            error: str = ""
            for alert in self.browser.find_elements('//div[@class="alert-content"]'):
                if alert.is_displayed():
                    error: str = alert.text
                    print(error)
                    break
            self.browser.click_element_when_visible('//button[@data-automation-id="customerCancelBtn"]')
            if "Please use a different name" in error:
                return True
        return False

    def add_estimate(self, grouped_rows: list, is_prod: bool = False) -> (bool, str, str):
        """
        Returns the bool if the new estimate was created and sent.

        :param grouped_rows: List of invoice data:
            customer: Customer name, column Account from spreadsheet
            service: Service name, column Service Type from spreadsheet
            description: Description column from spreadsheet
            rate: Amount column from spreadsheet
            processing_fee: True if column 3% Markup from spreadsheet has value Yes
        :param is_prod: If true bot will perform all change
        :return: status (bool): Bool value indicate if new estimate was created and sent
        """
        self.open_add_estimate_page()

        first_row: GroupedRow = grouped_rows[0]
        customer: str = first_row.customer

        self.wait_element('//input[@aria-label="Choose a customer"]')
        self.browser.input_text('//input[@aria-label="Choose a customer"]', customer.replace("\\", "\\\\"))

        self.wait_element(f'//span[text()="Add new"]/../span[text()="{customer}"]', 10, False)

        xpath_customers: str = '//div[@aria-label="Choose a customer"]/div[not(@aria-label)]//span[@class="mainLabel"]'
        customers: list = self.browser.find_elements(xpath_customers)
        if len(customers) > 1:
            for i in range(3):
                sleep(1)
                customers: list = self.browser.find_elements(xpath_customers)
                if len(customers) == 1:
                    break
        if not customers:
            customers: list = self.browser.find_elements('//span[@class="dijitComboBoxHighlightMatch"]')

        selected: bool = False
        for customer_id in customers:
            if str(customer_id.text).strip().lower() == customer.strip().lower():
                self.browser.click_element_when_visible(customer_id)
                selected = True
                break
        if not selected:
            for customer_id in customers:
                if customer.strip().lower() in str(customer_id.text).strip().lower():
                    self.browser.click_element_when_visible(customer_id)
                    selected = True
                    break
        if not selected:
            self.browser.capture_page_screenshot(
                os.path.join(self.output_folder, f'No_customer_{datetime.now().strftime("%H_%M_%S")}.png')
            )
            self.send_message_service_type_not_found(first_row.manager, customer)
            return False, "", ""

        index: int = 1
        total_rate: float = 0.0
        row: GroupedRow
        for row in grouped_rows:
            service: str = row.service
            description: str = row.description
            rate: float = row.rate
            total_rate += rate

            self.browser.click_element_when_visible(f'//td[text()="{index}"]')
            self.wait_element('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]')
            self.browser.input_text('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]', service)

            self.wait_element(
                f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]', 5, False
            )
            if not self.does_element_displayed(
                f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]'
            ):
                self.wait_element(f'//div/span/b[text()="{service}"]')
                if not self.does_element_displayed(f'//div/span/b[text()="{service}"]'):
                    self.browser.capture_page_screenshot(
                        os.path.join(self.output_folder, f'No_service_{datetime.now().strftime("%H_%M_%S")}.png')
                    )
                    self.send_message_service_type_not_found(first_row.manager, service)
                    return False, "", ""
                else:
                    self.browser.click_element_when_visible(f'//div/span/b[text()="{service}"]')
            else:
                self.browser.click_element_when_visible(
                    f'//div[@class="name"]/span[text()="{service}" and @class="dijitComboBoxHighlightMatch"]'
                )

            self.browser.input_text('//textarea[@data-automation-id="input-description-txndetails"]', description)
            self.browser.input_text('//input[@data-automation-id="input-rateField"]', str(rate))
            self.browser.input_text('//input[@data-automation-id="amountField"]', str(rate))
            index += 1

        total_rate = round(total_rate, 2)
        processing_fee: bool = first_row.processing_fee
        if processing_fee:
            processing_fee_name: str = "3% QuickBooks Processing Fee"
            self.browser.click_element_when_visible(f'//td[text()="{index}"]')
            self.wait_element('//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]')
            self.browser.input_text(
                '//input[contains(@id, "ItemComboBox") or @aria-label="ProductService"]', processing_fee_name
            )

            self.wait_element(f'//div/span/b[text()="{processing_fee_name}"]')
            self.browser.click_element_when_visible(f'//div/span/b[text()="{processing_fee_name}"]')

            self.browser.input_text(
                '//input[@data-automation-id="input-rateField"]', str("%.2f" % (total_rate / 0.97 - total_rate))
            )
            self.browser.input_text(
                '//input[@data-automation-id="amountField"]', str("%.2f" % (total_rate / 0.97 - total_rate))
            )

        self.wait_element('//input[@data-automation-id="input-creation-date-sales"]')
        self.browser.click_element_when_visible('//input[@data-automation-id="input-creation-date-sales"]')

        estimate_date: str = self.browser.get_value('//input[@data-automation-id="input-creation-date-sales"]')
        estimate_number: str = "1234"
        if is_prod:
            self.browser.click_element_when_visible('//button[text()="Save and send"]')
            self.wait_element('//button[text()="Send and close"]')
            estimate_number = self.browser.get_text('//div[@data-qbo-bind="text: referenceNumber"]')
            self.browser.click_element_when_visible('//button[text()="Send and close"]')
        else:
            print("Dev test. The invoice was not saved")
            self.browser.capture_page_screenshot(
                os.path.join(
                    self.output_folder, f'Test_run-customer_{customer}-{datetime.now().strftime("%H_%M_%S")}.png'
                )
            )
            self.browser.click_element_when_visible('//i[@aria-label="Close"]')
            self.wait_element('//button[text()="Yes"]', 5)
            if self.does_element_displayed('//button[text()="Yes"]'):
                self.browser.click_element_when_visible('//button[text()="Yes"]')
        self.send_message_estimate_added(
            first_row.manager,
            first_row.customer,
            estimate_number,
            total_rate,
        )

        return True, estimate_date, estimate_number
