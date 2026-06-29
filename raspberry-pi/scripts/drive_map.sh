#!/bin/sh
# drive_map.sh — build the "drive started" thumbnail map (Google Static Maps).
# Source of truth in the repo; deployed to the Pi at /config/drive_map.sh
# (= /home/admin/homeassistant/drive_map.sh). Contains NO secret — it reads the
# API key at runtime from /config/.google_maps_key (mode 600, Pi-only, NOT in git).
# Args: $1 = start "lat,lon"   $2 = dest "lat,lon" (or "None,None"/empty = start only)
KEY=$(cat /config/.google_maps_key)
OUT=/config/www/drive_maps/last_drive.png
BASE="https://maps.googleapis.com/maps/api/staticmap?size=600x320&scale=2"

if [ -n "$2" ] && [ "$2" != "None,None" ]; then
  curl -s -o "$OUT" "${BASE}&markers=color:0x34A853%7Clabel:A%7C$1&markers=color:0xEA4335%7Clabel:B%7C$2&path=color:0x1A73E8CC%7Cweight:4%7C$1%7C$2&key=${KEY}"
else
  curl -s -o "$OUT" "${BASE}&zoom=15&markers=color:0x34A853%7Clabel:A%7C$1&key=${KEY}"
fi
