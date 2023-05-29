#!/bin/bash

function run()
{
    echo "ldap inited."
    ds
}

function init_with_run()
{
    echo "ldap init."
    init_data &
    ds
}

function init_data()
{
    chmod +x /data.init/ldap_init.sh
    echo "wait 10 seconds for ldap"
    sleep 10
    /data.init/ldap_init.sh
}

function ds
{
    #SLAPD_MXFAST=0 MALLOC_MMAP_THRESHOLD_=33554432 MALLOC_TRIM_THRESHOLD_=4069 MALLOC_ARENA_MAX=1 
    #dsctl -v localhost dbverify backend
    /usr/lib/dirsrv/dscontainer -r
}

if [ -f /data/inited ]; then
    run
else
    init_with_run
fi
