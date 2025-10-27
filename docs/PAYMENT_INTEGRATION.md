# Payment Integration Guide

## Overview
The Event Hub backend integrates with M-Pesa for payment processing using the STK Push API.

## API Endpoints

### 1. Initiate Payment
**POST** `/api/payments/initiate`

**Request Body:**
```json
{
  "phone_number": "254712345678",
  "event_id": 1,
  "quantity": 2
}
```

**Response:**
```json
{
  "payment_id": 1,
  "checkout_request_id": "ws_CO_123456789",
  "message": "Payment initiated successfully"
}
```

### 2. Check Payment Status
**GET** `/api/payments/status/{payment_id}`

**Response:**
```json
{
  "payment_id": 1,
  "status": "completed",
  "amount": 5000.0,
  "mpesa_receipt_number": "OEI2AK4Q16"
}
```

### 3. M-Pesa Callback
**POST** `/api/payments/callback`

This endpoint receives M-Pesa payment confirmations automatically.

## Payment Flow

1. **Frontend** calls `/api/payments/initiate` with user details
2. **Backend** creates payment record and initiates M-Pesa STK push
3. **User** completes payment on their phone
4. **M-Pesa** sends callback to `/api/payments/callback`
5. **Backend** updates payment status and generates tickets
6. **Frontend** polls `/api/payments/status/{id}` to check completion

## Error Handling

- **400**: Missing required fields or insufficient tickets
- **404**: Event or payment not found
- **500**: M-Pesa API errors or server issues

## Frontend Integration

```javascript
// Initiate payment
const initiatePayment = async (phoneNumber, eventId, quantity) => {
  const response = await fetch('/api/payments/initiate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone_number: phoneNumber,
      event_id: eventId,
      quantity: quantity
    })
  });
  return response.json();
};

// Check payment status
const checkPaymentStatus = async (paymentId) => {
  const response = await fetch(`/api/payments/status/${paymentId}`);
  return response.json();
};
```