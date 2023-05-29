ds389_test
============
Script for testing 389ds
=====

Table of contents
----------
* [Create and launch container with test schema](#сreate-and-launch-container-with-test-schema)
* [Install dependencies for python](#install-dependencies-for-python)
* [Launch python scripts](#launch-python-scripts)
* [Install Erlang](#install-erlang)
* [Launch erlang scripts](#launch-erlang-scripts)

Create and launch container with test schema
--------------------------------------------
Dockerfile, schema, and supporting scripts are located in the Scripts. Use the following command to run:
```
    chmod +x start.sh
    ./start.sh
```

Installing dependencies for python
----------------------------------
```
     sudo apt-get install python3-pip
     python3 -m pip install --upgrade pip
     python3 -m pip install ldap3 paramiko
```

Launch python scripts
---------------------
Set `HOST` variable in `main.py` to ip address your ds389. Set `SSH_PORT, SSH_LOGIN, SSH_PWD` for dbomn loggin over ssh. And use `python3 main.py` command for start testing.

Install Erlang
--------------
Use `apt-get install erlang` for install latest version erlang for debian, or download and install older version from [Old version Erlang](https://www.erlang-solutions.com/downloads/).
For example in debian use [Erlang 23.2.3](https://packages.erlang-solutions.com/erlang/debian/pool/esl-erlang_23.2.3-1~debian~buster_amd64.deb).

Launch erlang scripts
---------------------
Use following commands for launch erlang srcipts
```
    chmod +x test389ds
    escript test389ds <ip address your ds389> 3389 test
```
