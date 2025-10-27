# M-Pesa Setup Guide

## Prerequisites
1. Safaricom Developer Account
2. M-Pesa API credentials
3. SSL certificate for production callback URL

## Getting M-Pesa Credentials

### 1. Create Safaricom Developer Account
- Visit [developer.safaricom.co.ke](https://developer.safaricom.co.ke)
- Register and verify your account
- Create a new app

### 2. Get API Credentials
From your app dashboard, note down:
- **Consumer Key**
- **Consumer Secret** 
- **Business Short Code** (use 174379 for sandbox)
- **Passkey**

### 3. Environment Variables
Create a `.env` file in your project root:

```bash
# M-Pesa Configuration
MPESA_CONSUMER_KEY=your_consumer_key_here
MPESA_CONSUMER_SECRET=your_consumer_secret_here
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey_here
MPESA_CALLBACK_URL=https://yourdomain.com/api/payments/callback
MPESA_ENV=sandbox  # or 'production'

# Database
DATABASE_URL=sqlite:///eventhub.db
SECRET_KEY=your-secret-key-here
```

## Testing with Sandbox

### Test Phone Numbers
Use these Safaricom test numbers for sandbox:
- `254708374149`
- `254711082300` 
- `254733000000`

### Test Amounts
- Any amount between 1-70000 KES
- Use whole numbers only

## Production Setup

### 1. SSL Certificate
- Obtain SSL certificate for your domain
- Configure HTTPS for callback URL

### 2. Callback URL
- Must be publicly accessible
- Must use HTTPS in production
- Should handle POST requests with M-Pesa callback data

### 3. Go Live Process
1. Complete Safaricom's go-live requirements
2. Update `MPESA_ENV=production`
3. Use production shortcode and credentials
4. Test with real phone numbers and amounts

## Troubleshooting

### Common Issues
1. **Invalid credentials**: Verify consumer key/secret
2. **Callback timeout**: Ensure URL is accessible
3. **Invalid phone number**: Use correct format (254XXXXXXXXX)
4. **Amount validation**: Use integers only, no decimals

### Testing Checklist
- [ ] Credentials configured correctly
- [ ] Callback URL accessible
- [ ] Phone number format correct
- [ ] Amount is valid integer
- [ ] SSL certificate valid (production)

## Security Notes
- Never commit credentials to version control
- Use environment variables for all sensitive data
- Validate all callback data before processing
- Implement rate limiting for payment endpoints