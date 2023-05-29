ds389_test
============
Script for testing 389ds
=====

Table of contents
----------
* [Create and launch container with test schema](#Create and launch container with test schema)
* [Install dependencies for python](#Install dependencies for python)
* [Launch python scripts](#Launch python scripts)
* [Install Erlang](#Install Erlang)
* [Launch erlang scripts](#Launch erlang scripts)

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
Set HOST variable in main.py to ip address your ds389. And use `python3 main.py` command for start testing.

Install Erlang
--------------
Use `apt-get install erlang' for install latest version erlang for debian, or download and install older version from [Old version Erlang](https://www.erlang-solutions.com/downloads/).

Launch erlang scripts
---------------------
Use following commands for launch erlang srcipts
```
    chmod +x test389ds
    escript test389ds <ip address your ds389> 3389 test
```