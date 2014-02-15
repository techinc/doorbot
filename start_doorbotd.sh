#!/bin/bash
ERRLOG=/srv/doorbot/doorbot.err
cd "$(dirname "$0")"
su "$(stat -c "%U" user.db)" -c "while true; do python ./doorbotd.py && exit; sleep 5; done" >>"$ERRLOG" 2>&1 &
