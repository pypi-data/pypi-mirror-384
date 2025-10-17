#!/usr/bin/env sh

pkill wsgidav
rclone config create webdav-local webdav url=http://127.0.0.1:8977 user=test pass=toto
mkdir -p /tmp/webdav_root
rm -r /tmp/webdav_root/*
solidipes init /tmp/webdav_root
mkdir /tmp/webdav_root/data
SOLIDIPES_SRC_PATH=$(python -c "import solidipes;import os;print(os.path.join(os.path.dirname(solidipes.__file__), '..'))")
find "$SOLIDIPES_SRC_PATH/tests/assets" -type f -exec cp '{}' /tmp/webdav_root/data/ ';'
find solidipes/tests/assets -type f -exec cp '{}' /tmp/webdav_root/data/ ';'
find /tmp/webdav_root/data/
nohup wsgidav --config tests/wsgidav.yaml &
sleep 2
if [[ -f nohup.out ]]; then
    tail -f nohup.out
fi
