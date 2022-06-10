#!/usr/bin/env bash
source ./.venv/bin/activate
hypercorn main:app --bind 0.0.0.0:3432 --certfile cert.pem --keyfile key.pem