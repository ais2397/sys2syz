#!/bin/bash

# This script sets up the environment required for the tool to run.

echo "Installing c2xml"
mkdir c2xml
wget -O c2xml.zip https://sourceforge.net/projects/c2xml/files/sources/c2xml_src_0_9/c2xml_src_0_9.zip/download
unzip c2xml.zip -d c2xml
rm c2xml.zip