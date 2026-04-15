sudo nano /usr/local/bin/perfmax
sudo nano /usr/local/bin/perfnorm
replace loading part from above files to brightness snippet.

loading part:
if [ -f "/roms/launchimages/loading.gif" ] && [[ $(tty) != *"pts"* ]]; then
ffplay -x 1280 -y 720 /roms/launchimages/loading.gif & 
PROC=$!
(sleep 3s; kill -9 $PROC)
fi 

brightness snippet:
BRIGHT_PATH="/sys/class/backlight/backlight/brightness"
MIN=7
cur=$(cat "$BRIGHT_PATH" 2>/dev/null)
if [ -n "$cur" ] && [ "$cur" -lt "$MIN" ]; then
    echo $MIN > "$BRIGHT_PATH"
    echo $cur > "$BRIGHT_PATH"
fi