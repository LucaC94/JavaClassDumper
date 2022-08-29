#!/bin/sh

JADX_ZIP="jadx_latest.zip"
JADX_DIR="jadx"

latest=$(curl -s https://api.github.com/repos/skylot/jadx/releases/latest | grep -m 1 browser_download_url | cut -d '"' -f 4 | tr -d '\n')
wget "$latest" -O $JADX_ZIP
unzip jadx_latest.zip -d $JADX_DIR > /dev/null
rm jadx_latest.zip
