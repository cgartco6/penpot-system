#!/bin/bash
INPUT="$1"
OUTPUT="$2"
tifficc -c -e /usr/share/color/icc/FOGRA39.icc "$INPUT" "$OUTPUT"
