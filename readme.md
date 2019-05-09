# Online Judge for someone

## Setup Guide for the Web Server

```bash
sudo apt-get install -y git python-pip postgresql postgresql-server-dev-9.5 libpq-dev python-dev python-setuptools gunicorn tmux
sudo -H -u postgres psql
postgres=# CREATE USER compiler2017 WITH PASSWORD 'mypassword';
postgres=# CREATE DATABASE compiler2017;
postgres=# GRANT ALL PRIVILEGES ON DATABASE compiler2017 to compiler2017;
postgres=# \q

git clone https://github.com/lgkm39/acm-compiler-judge.git
cd acm-compiler-judge
sudo -H pip install -r requirements.txt
cd WebServer
./maintenance.py initdb
./maintenance.py initdb <random_token>
./maintenance.py makedirs
```

# Setup Guide for Judge Server
```bash
sudo apt-get -y install apt-transport-https ca-certificates curl python-dev python-setuptools software-properties-common tmux
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y git python-pip docker-ce libpq-dev python-dev
sudo usermod -aG docker $USER

cd JudgeServer/docker-image
docker build -t acm-compiler-judge:latest -f production.Dockerfile .
```

## Run Web Server

```bash
# run core
cd WebServer
./core/repo_watcher.py
./core/testrun_watcher.py

# run web
cd WebServer
gunicorn -b 0.0.0.0:6002 core.core:app  # for production run
./core/core.py                          # for debug run

# maintenance
cd WebServer
./maintenance.py <COMMAND>
```

## Run Judge Server

```bash
cd JudgeServer
./judge.py <NAME>
```

## Add Testcase
```bash
cd WebServer
./test.py
```

## Something else...

mistakes about psycopg2

user mushroom

user GCC -O0

user GCC -O1

user GCC -O2

**remember make directory for JudgeServer**

