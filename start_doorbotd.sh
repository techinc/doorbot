#!/bin/bash

(
	cd "$(dirname "$0")"
	su "$(stat -c "%U" user.db)" -c "while true; do python ./doorbotd.py; sleep 5; done"
)&
