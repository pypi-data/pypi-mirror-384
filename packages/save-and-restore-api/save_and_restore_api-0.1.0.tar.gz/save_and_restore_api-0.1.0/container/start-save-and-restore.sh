#!/usr/bin/env bash
set -x

python create_env_file.py
sudo docker compose -f save-and-restore.yml up -d
python wait_for_startup.py
