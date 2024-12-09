#!/bin/bash

# Run the Python script in the background via nohup; log terminal prints to home dir file
nohup python3 -u /home/katavga/code/safe-meme/gee_acquire_data.py > ~/gee_acquire_data.log 2>&1 &

# Confirm successful script instantiation
echo "Script is running in the background. Logs are being written to ~/gee_acquire_data.log"

# Verify that the process is running
ps -ef | grep gee_acquire_data.py | grep -v grep
