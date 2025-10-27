# Event-Hub-Backend

Backend API for Event Hub ticketing and payment system with M-Pesa integration.

## Features
- Event management
- M-Pesa payment integration
- Ticket generation and validation
- RESTful API endpoints

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize database:
```bash
python init_db.py
```

3. Seed sample events:
```bash
python seed_events.py
```

4. Configure M-Pesa credentials (copy .env.example to .env)

5. Run the application:
```bash
python app.py
```

## API Endpoints

### Events
- `GET /api/events/` - List all events
- `GET /api/events/{id}` - Get specific event

### Payments
- `POST /api/payments/initiate` - Initiate M-Pesa payment
- `GET /api/payments/status/{id}` - Check payment status
- `POST /api/payments/callback` - M-Pesa callback (internal)

### Tickets
- `POST /api/tickets/generate` - Generate tickets after payment
- `GET /api/tickets/validate/{code}` - Validate ticket
- `POST /api/tickets/use/{code}` - Mark ticket as used
- `GET /api/tickets/payment/{id}` - Get tickets by payment

## Documentation
- [Payment Integration Guide](docs/PAYMENT_INTEGRATION.md)
- [M-Pesa Setup Guide](docs/MPESA_SETUP.md)