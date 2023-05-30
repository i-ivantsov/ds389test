ds389_test
============
Script for testing 389ds
=====

# Table of contents
----------
* [1. Create and launch container with test schema](#1-create-and-launch-container-with-test-schema)
* [2. Start script](#2-start-script)
* > [2.1 Python script](#2.1-python-script)
* >> [2.1.1 Pre-requirements](#2.1.1-pre-requirements)
* >> [2.1.2 Set-up variables](#2.1.2-set-up-variables)
* >> [2.1.3 Launch](#2.1.3-launch)
* > [2.2 Erlang script](#2.2-erlang-script)
* >> [2.2.1 Pre-requirements](#2.2.1-pre-requirements)
* >> [2.2.2 Launch](#2.2.2-launch)

# 1. Create and launch container with test schema
--------------------------------------------
Dockerfile, schema and helper scripts are located in `Scripts` folder. Use the following command to start ds389 up:
```
    cd Schema
    chmod +x start.sh
    ./start.sh
```

# 2. Start script
-------------------
Either `Python` or `Erlang` script can be used.

## 2.1 Python script
### 2.1.1 Pre-requirements
--------------------------------------------
```
     sudo apt-get install python3-pip
     python3 -m pip install --upgrade pip
     python3 -m pip install ldap3 paramiko
```

### 2.1.2 Set-up variables
--------------------------
Some changes are required to be made in `main.py`:

Set `HOST` variable to ip address of ds389;

Set `DBMON_LOG_MODE` to either `"ssh"`, `"local"` or `"off"`. In case of python script and ds389 server are running on the same machine prefer `local`. If you run script separately use `"ssh"` and be sure to change `SSH_PORT`, `SSH_LOGIN` and `SSH_PWD` variables respectively. If no logging required then left it to `"off"`. Default value is `"local"`.

### 2.1.3 Launch
----------------
Run `main.py` with the following command:

```
python3 main.py
```

## 2.2 Erlang script
--------------------
### 2.2.1 Pre-requirements
----------------------
Install `erlang` package via package manager (e.g. for debian use `apt-get install erlang`) or download manually from [here](https://www.erlang-solutions.com/downloads/).
For example in Debian (Buster) the latest avaliable version is [23.2.3](https://packages.erlang-solutions.com/erlang/debian/pool/esl-erlang_23.2.3-1~debian~buster_amd64.deb).

### 2.2.2 Launch
----------------
Run `test389ds` with the following command:

```
    chmod +x test389ds
    escript test389ds <ip address of ds389> 3389 test
```