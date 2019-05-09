#!/bin/bash

cd ./WebServer
nohup ./core/repo_watcher.py >>./repo_watcher.log 2>&1 &
nohup ./core/testrun_watcher.py >> ./testrun_watcher.log 2>&1 &
nohup gunicorn -b 0.0.0.0:8080 core.core:app >> ./gunicorn.log 2>&1 &
