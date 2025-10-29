from flask import Blueprint, request, jsonify
from models import Ticket, Event, PaymentStatus, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth import role_required
from extension import db
import requests
import base64
from datetime import datetime
import os

payments_bp = Blueprint('payments', __name__)

class MpesaService:
    def __init__(self):
        self.consumer_key = os.environ.get('MPESA_CONSUMER_KEY', 'uWdCJRpKfhl1n9O3glfHa3jtmIQTYBBW82qYNxMzRHGYHuTx')
        self.consumer_secret = os.environ.get('MPESA_CONSUMER_SECRET', '8dXMT15CFXNTDsTNcKXtKxo4MI4Fhuf3egAgs4gydTkuTnVFQBhCl1pGHCmJevCX')
        self.business_short_code = os.environ.get('MPESA_SHORTCODE', '174379')
        self.passkey = os.environ.get('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
        self.callback_url = os.environ.get('MPESA_CALLBACK_URL', 'https://your-domain.com/api/payments/callback')
        self.base_url = 'https://sandbox.safaricom.co.ke'

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        
        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
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
            "Amount": int(round(float(amount))),
            "PartyA": phone_number,
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

mpesa = MpesaService()

@payments_bp.post('/initiate/<ticket_id>')
@jwt_required()
def initiate_payment(ticket_id):
    current_user_id = get_jwt_identity()
    ticket = Ticket.query.get(ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if ticket.payment_status != PaymentStatus.PENDING:
        return jsonify({'error': 'Payment already processed'}), 400
    
    event = Event.query.get(ticket.event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    try:
        mpesa_response = mpesa.stk_push(
            phone_number=ticket.payment_phone,
            amount=ticket.total_amount,
            account_reference=f"TICKET{ticket.id[:8]}",
            transaction_desc=f"Ticket for {event.title}"
        )
        
        if mpesa_response.get('ResponseCode') == '0':
            return jsonify({
                'ticket_id': ticket.id,
                'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                'message': 'Payment initiated successfully'
            }), 200
        else:
            return jsonify({'error': 'Payment initiation failed'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payments_bp.get('/status/<ticket_id>')
@jwt_required()
def payment_status(ticket_id):
    current_user_id = get_jwt_identity()
    ticket = Ticket.query.get(ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'ticket_id': ticket.id,
        'status': ticket.payment_status.value,
        'amount': ticket.total_amount,
        'mpesa_receipt': ticket.mpesa_receipt
    })

@payments_bp.post('/callback')
def mpesa_callback():
    data = request.get_json()
    
    try:
        callback_data = data.get('Body', {}).get('stkCallback', {})
        result_code = callback_data.get('ResultCode')
        
        # Extract ticket ID from account reference
        account_ref = callback_data.get('AccountReference', '')
        if account_ref.startswith('TICKET'):
            ticket_partial_id = account_ref[6:]  # Remove 'TICKET' prefix
            ticket = Ticket.query.filter(Ticket.id.like(f'{ticket_partial_id}%')).first()
            
            if not ticket:
                return jsonify({'error': 'Ticket not found'}), 404
            
            if result_code == 0:
                # Payment successful
                ticket.payment_status = PaymentStatus.COMPLETED
                callback_metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
                
                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        ticket.mpesa_receipt = item.get('Value')
                
            else:
                # Payment failed
                ticket.payment_status = PaymentStatus.FAILED
            
            ticket.save()
            return jsonify({'message': 'Callback processed'}), 200
        
        return jsonify({'error': 'Invalid account reference'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500