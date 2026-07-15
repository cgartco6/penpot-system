#!/bin/bash
INPUT="$1"
OUTPUT="$2"
rsvg-convert -f pdf -o temp.pdf "$INPUT"
gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -dPDFX -dPDFXSet -sColorConversionStrategy=CMYK -sOutputFile="$OUTPUT" temp.pdf
