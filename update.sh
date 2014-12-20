#!/bin/bash

git pull
sudo pip install -r requirements.txt
sudo kill -9 `ps -elf | grep uwsgi.sock | grep -v sudo | grep -v grep | awk '{print $4}'`
bash run.sh
