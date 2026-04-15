#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
    exec sudo -- "$0" "$@"
fi

CURR_TTY="/dev/tty1"
APP_NAME="Battery Info"

printf "\033c" > "$CURR_TTY"
printf "\e[?25l" > "$CURR_TTY"
dialog --clear
export TERM=linux

# Font selection based on joystick presence
if [[ ! -e "/dev/input/by-path/platform-odroidgo2-joypad-event-joystick" ]]; then
    setfont /usr/share/consolefonts/Lat7-TerminusBold20x10.psf.gz
else
    setfont /usr/share/consolefonts/Lat7-Terminus24x12.psf.gz
fi

printf "\033c" > "$CURR_TTY"
printf "Reading Battery...\nPlease wait..." > "$CURR_TTY"

ExitMenu() {
    printf "\033c" > "$CURR_TTY"
    printf "\e[?25h" > "$CURR_TTY"
    pkill -f "gptokeyb -1 BatteryInfo.sh" || true
    if [[ ! -e "/dev/input/by-path/platform-odroidgo2-joypad-event-joystick" ]]; then
        setfont /usr/share/consolefonts/Lat7-Terminus24x12.psf.gz
    fi
    exit 0
}

GetVoltage() {
    local VOLTAGE_RAW=""

    for path in \
        /sys/class/power_supply/battery/voltage_now \
        /sys/class/power_supply/BAT0/voltage_now \
        /sys/class/power_supply/BAT1/voltage_now \
        /sys/class/power_supply/rk817-battery/voltage_now; do
        if [ -f "$path" ]; then
            VOLTAGE_RAW=$(cat "$path" 2>/dev/null)
            break
        fi
    done

    if [ -z "$VOLTAGE_RAW" ]; then
        echo "unavailable"
        return 1
    fi

    awk "BEGIN {printf \"%.3f\", $VOLTAGE_RAW/1000000}"
}

GetCapacity() {
    local CAPACITY=""

    for path in \
        /sys/class/power_supply/battery/capacity \
        /sys/class/power_supply/BAT0/capacity \
        /sys/class/power_supply/rk817-battery/capacity; do
        if [ -f "$path" ]; then
            CAPACITY=$(cat "$path" 2>/dev/null)
            break
        fi
    done

    if [ -z "$CAPACITY" ]; then
        echo "unavailable"
        return 1
    fi

    echo "$CAPACITY"
}

GetBatteryBar() {
    local PCT=$1
    local BAR_WIDTH=20
    local FILLED=$(awk "BEGIN {printf \"%d\", $PCT/100*$BAR_WIDTH}")
    local EMPTY=$(( BAR_WIDTH - FILLED ))
    local BAR=""
    for ((i=0; i<FILLED; i++)); do BAR+="#"; done
    for ((i=0; i<EMPTY; i++));  do BAR+="-"; done
    echo "[$BAR]"
}

GetChargeStatus() {
    local STATUS="Unknown"
    for path in \
        /sys/class/power_supply/battery/status \
        /sys/class/power_supply/BAT0/status \
        /sys/class/power_supply/rk817-battery/status; do
        if [ -f "$path" ]; then
            STATUS=$(cat "$path" 2>/dev/null)
            break
        fi
    done
    echo "$STATUS"
}

ShowBattery() {
    setfont /usr/share/consolefonts/Lat7-Terminus20x10.psf.gz

    local VOLTAGE
    VOLTAGE=$(GetVoltage)

    local CAPACITY
    CAPACITY=$(GetCapacity)

    local PCT=0
    local BAR=""

    if [ "$VOLTAGE" = "unavailable" ]; then
        V_DISPLAY="  • Voltage     : N/A"
        PCT=0
    else
        V_DISPLAY="  • Voltage     : ${VOLTAGE} V"
        PCT=$(awk "BEGIN {
            v=$VOLTAGE
            vmin=3.4
            vmax=4.1
            if (v < vmin) v = vmin
            if (v > vmax) v = vmax
            pct = (v - vmin) / (vmax - vmin) * 100
            printf \"%.0f\", pct
        }")
    fi

    if [ "$CAPACITY" = "unavailable" ]; then
        CAP_DISPLAY="  • Capacity    : N/A"
    else
        CAP_DISPLAY="  • Capacity    : ${CAPACITY}%"
    fi

    local PCT_INT=$(printf "%.0f" "$PCT")
    BAR=$(GetBatteryBar "$PCT_INT")
    local CHARGE_STATUS=$(GetChargeStatus)

    dialog --backtitle "$APP_NAME" --msgbox "\
    ----------------Battery-------------------
$V_DISPLAY
  • Interpolated: ${PCT_INT}%
$CAP_DISPLAY
  • Status      : ${CHARGE_STATUS}

  ${BAR} ${PCT_INT}%
" 14 50 > "$CURR_TTY"
}

# --- Launch ---
sudo chmod 666 "$CURR_TTY"
printf "\e[?25l" > "$CURR_TTY"
clear > "$CURR_TTY"
dialog --clear
trap ExitMenu EXIT

sudo chmod 666 /dev/uinput
export SDL_GAMECONTROLLERCONFIG_FILE="/opt/inttools/gamecontrollerdb.txt"
pgrep -f gptokeyb | sudo xargs kill -9 2>/dev/null
/opt/inttools/gptokeyb -1 "BatteryInfo.sh" -c "/opt/inttools/keys.gptk" > /dev/null 2>&1 &

# --- Start ---
ShowBattery
