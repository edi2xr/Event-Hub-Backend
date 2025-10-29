from flask import Blueprint, request, jsonify
from database import db
from backend.models.models import Payment, Event, PaymentStatus, Subscription
from backend.services.mpesa import MpesaService
from datetime import datetime, timedelta
import uuid

bp = Blueprint('payments', __name__, url_prefix='/api/payments')
mpesa = MpesaService()

@bp.route('/initiate', methods=['POST'])
def initiate_payment():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['phone_number', 'event_id', 'quantity']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get event details
    event = Event.query.get(data['event_id'])
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Check ticket availability
    if event.available_tickets < data['quantity']:
        return jsonify({'error': 'Not enough tickets available'}), 400
    
    # Calculate total amount with 5% commission
    base_amount = event.price * data['quantity']
    commission = base_amount * 0.05
    total_amount = base_amount + commission
    
    # Create payment record
    payment = Payment(
        amount=total_amount,
        phone_number=data['phone_number'],
        event_id=data['event_id'],
        quantity=data['quantity']
    )
    db.session.add(payment)
    db.session.commit()
    
    # Initiate M-Pesa STK push
    try:
        mpesa_response = mpesa.stk_push(
            phone_number=data['phone_number'],
            amount=total_amount,
            account_reference=f"EVENT{event.id}",
            transaction_desc=f"Ticket for {event.name}"
        )
        
        if mpesa_response.get('ResponseCode') == '0':
            payment.checkout_request_id = mpesa_response.get('CheckoutRequestID')
            db.session.commit()
            
            return jsonify({
                'payment_id': payment.id,
                'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                'message': 'Payment initiated successfully'
            }), 200
        else:
            payment.status = PaymentStatus.FAILED
            db.session.commit()
            return jsonify({'error': 'Payment initiation failed'}), 400
            
    except Exception as e:
        payment.status = PaymentStatus.FAILED
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@bp.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    
    if not data.get('phone_number'):
        return jsonify({'error': 'Phone number required'}), 400
    
    subscription = Subscription(
        phone_number=data['phone_number'],
        amount=200.0,
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(subscription)
    db.session.commit()
    
    try:
        mpesa_response = mpesa.stk_push(
            phone_number=data['phone_number'],
            amount=200,
            account_reference="SUBSCRIPTION",
            transaction_desc="Event Hub Subscription - 200 KES"
        )
        
        if mpesa_response.get('ResponseCode') == '0':
            subscription.checkout_request_id = mpesa_response.get('CheckoutRequestID')
            db.session.commit()
            
            return jsonify({
                'subscription_id': subscription.id,
                'checkout_request_id': mpesa_response.get('CheckoutRequestID'),
                'message': 'Subscription payment initiated'
            }), 200
        else:
            subscription.status = PaymentStatus.FAILED
            db.session.commit()
            return jsonify({'error': 'Payment initiation failed'}), 400
            
    except Exception as e:
        subscription.status = PaymentStatus.FAILED
        db.session.commit()
        return jsonify({'error': str(e)}), 500

@bp.route('/complimentary', methods=['POST'])
def create_complimentary_ticket():
    data = request.get_json()
    
    if not all(k in data for k in ['event_id', 'owner_phone', 'recipient_phone', 'quantity']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    event = Event.query.get(data['event_id'])
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    # Verify ownership
    if data['owner_phone'] != event.owner_phone:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check ticket availability
    if event.available_tickets < data['quantity']:
        return jsonify({'error': 'Not enough tickets available'}), 400
    
    try:
        # Create complimentary payment record (amount = 0)
        payment = Payment(
            amount=0.0,
            phone_number=data['recipient_phone'],
            event_id=data['event_id'],
            quantity=data['quantity'],
            status=PaymentStatus.COMPLETED,
            mpesa_receipt_number='COMPLIMENTARY'
        )
        db.session.add(payment)
        
        # Update ticket availability
        event.available_tickets -= data['quantity']
        db.session.commit()
        
        return jsonify({
            'message': f'Complimentary tickets sent to {data["recipient_phone"]}',
            'payment_id': payment.id,
            'quantity': data['quantity']
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/status/<int:payment_id>', methods=['GET'])
def payment_status(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    # Query M-Pesa for transaction status if still pending
    if payment.status == PaymentStatus.PENDING and payment.checkout_request_id:
        try:
            mpesa_response = mpesa.query_transaction(payment.checkout_request_id)
            if mpesa_response.get('ResultCode') == '0':
                payment.status = PaymentStatus.COMPLETED
                payment.mpesa_receipt_number = mpesa_response.get('MpesaReceiptNumber')
                db.session.commit()
        except Exception:
            pass
    
    return jsonify({
        'payment_id': payment.id,
        'status': payment.status.value,
        'amount': payment.amount,
        'mpesa_receipt_number': payment.mpesa_receipt_number
    })

@bp.route('/callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    
    try:
        callback_data = data.get('Body', {}).get('stkCallback', {})
        checkout_request_id = callback_data.get('CheckoutRequestID')
        result_code = callback_data.get('ResultCode')
        
        payment = Payment.query.filter_by(checkout_request_id=checkout_request_id).first()
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        if result_code == 0:
            # Payment successful
            payment.status = PaymentStatus.COMPLETED
            callback_metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
            
            for item in callback_metadata:
                if item.get('Name') == 'MpesaReceiptNumber':
                    payment.mpesa_receipt_number = item.get('Value')
            
            # Update event ticket availability
            event = Event.query.get(payment.event_id)
            event.available_tickets -= payment.quantity
            
        else:
            # Payment failed
            payment.status = PaymentStatus.FAILED
        
        db.session.commit()
        return jsonify({'message': 'Callback processed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500