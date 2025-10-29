 step please# Email Integration for Leader Subscriptions - TODO List

## Step 1: Update Dependencies
- [x] Add Flask-Mail to requirements.txt for email sending capability.

## Step 2: Configure Email in App
- [x] Update app.py to initialize Flask-Mail and add SMTP config variables from environment.

## Step 3: Add Email Utility Function
- [x] Update utils.py to add send_subscription_email function for sending the notification email.

## Step 4: Integrate Email in Subscription Endpoint
- [x] Update auth.py to call the email function after successful subscription activation in /subscribe endpoint.

## Step 5: Install Dependencies
- [x] Run pip install -r requirements.txt to install Flask-Mail.

## Step 6: Test the Implementation
- [x] Verified app imports successfully without circular import errors.
- [x] Verified app creation successful without database connection errors.
- [x] Verified auth blueprint imports successfully.
- [x] Verified email utility function imports successfully.
- [ ] Test the /subscribe endpoint to ensure subscription works and email is sent (requires setting up environment variables for email: MAIL_USERNAME, MAIL_PASSWORD, etc., and actual SMTP server; not performed to avoid sending real emails).
- [ ] Verify no regressions in the auth flow (app starts without errors, import successful).
