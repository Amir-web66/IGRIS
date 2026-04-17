#!/bin/bash
node server.js &
sleep 1
xdg-open http://localhost:3737 2>/dev/null || open http://localhost:3737