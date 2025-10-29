#!/bin/bash
export FLASK_ENV=production
source .env.production
gunicorn -c gunicorn.conf.py wsgi:app