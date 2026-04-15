#!/bin/bash
BRIGHT_PATH="/sys/class/backlight/backlight/brightness"
MIN=7

while true; do
    cur=$(cat "$BRIGHT_PATH" 2>/dev/null)
    if [ -n "$cur" ] && [ "$cur" -lt "$MIN" ]; then
        echo $MIN > "$BRIGHT_PATH"
    fi
    sleep 1
done