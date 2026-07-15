#!/bin/bash
mkdir -p /usr/share/color/icc
wget -O /tmp/FOGRA39.zip https://www.color.org/icc/FOGRA39.zip
unzip /tmp/FOGRA39.zip -d /usr/share/color/icc/
