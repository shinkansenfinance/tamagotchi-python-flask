#!/bin/sh
set -e
. /venv/bin/activate
flask --app tamagotchi init-db
flask --app tamagotchi run --host 0.0.0.0 --port 8000
