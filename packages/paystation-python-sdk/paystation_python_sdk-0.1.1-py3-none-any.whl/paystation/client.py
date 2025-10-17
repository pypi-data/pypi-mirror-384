"""
PayStation API client.
"""
import requests
from .exceptions import APIError

class PayStationClient:
    """
    A client for interacting with the PayStation API.
    """
    def __init__(self, merchant_id, password, sandbox=False):
        self.merchant_id = merchant_id
        self.password = password
        self.sandbox = sandbox
        # The documentation does not specify a sandbox URL.
        # Using the live URL, can be overridden if needed.
        self.base_url = "https://api.paystation.com.bd"

    def _get_api_url(self, endpoint):
        return f"{self.base_url}/{endpoint}"

    def _handle_response(self, response):
        response.raise_for_status()
        data = response.json()
        if data.get("status_code") != "200":
            raise APIError(data.get("status_code"), data.get("message"))
        return data

    def initiate_payment(self, invoice_number, payment_amount, callback_url, cust_name, cust_phone, cust_email, currency="BDT", pay_with_charge=None, reference=None, cust_address=None, checkout_items=None, opt_a=None, opt_b=None, opt_c=None):
        """
        Initiates a payment and returns the response from PayStation.
        """
        url = self._get_api_url("initiate-payment")
        payload = {
            "merchantId": self.merchant_id,
            "password": self.password,
            "invoice_number": str(invoice_number),
            "currency": currency,
            "payment_amount": payment_amount,
            "cust_name": cust_name,
            "cust_phone": cust_phone,
            "cust_email": cust_email,
            "callback_url": callback_url,
        }

        optional_params = {
            "pay_with_charge": pay_with_charge,
            "reference": reference,
            "cust_address": cust_address,
            "checkout_items": checkout_items,
            "opt_a": opt_a,
            "opt_b": opt_b,
            "opt_c": opt_c,
        }
        payload.update({k: v for k, v in optional_params.items() if v is not None})

        response = requests.post(url, data=payload)
        return self._handle_response(response)

    def check_transaction_status_by_invoice(self, invoice_number):
        """
        Checks the status of a transaction using the invoice number.
        """
        url = self._get_api_url("transaction-status")
        headers = {"merchantId": self.merchant_id}
        data = {"invoice_number": invoice_number}
        response = requests.post(url, headers=headers, data=data)
        return self._handle_response(response)

    def check_transaction_status_by_trx_id(self, trx_id):
        """
        Checks the status of a transaction using the transaction ID (v2).
        """
        url = self._get_api_url("v2/transaction-status")
        headers = {"merchantId": self.merchant_id}
        data = {"trxId": trx_id}
        response = requests.post(url, headers=headers, data=data)
        return self._handle_response(response)
