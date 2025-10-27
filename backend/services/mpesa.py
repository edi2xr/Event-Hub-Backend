import requests
import base64
from datetime import datetime
import os

class MpesaService:
    def __init__(self):
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET')
        self.business_short_code = os.environ.get('MPESA_SHORTCODE', '174379')
        self.passkey = os.environ.get('MPESA_PASSKEY')
        self.callback_url = os.environ.get('MPESA_CALLBACK_URL', 'https://your-domain.com/api/payments/callback')
        self.base_url = 'https://sandbox.safaricom.co.ke' if os.environ.get('MPESA_ENV') == 'sandbox' else 'https://api.safaricom.co.ke'

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        credentials = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers)
        return response.json().get('access_token')

    def generate_password(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
        return base64.b64encode(password_string.encode()).decode(), timestamp

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def query_transaction(self, checkout_request_id):
        access_token = self.get_access_token()
        password, timestamp = self.generate_password()
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()