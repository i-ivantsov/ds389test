#!/bin/bash

function repeat()
{
    result=1
    wait=0
    for (( count=1; count<50; count++ ))
    do
        eval $1 > /dev/null
        result=$?
        if [[ $result -eq 0 ]]
        then
            if [[ $wait -eq 1 ]]
            then
                echo ""
            fi        
            echo $2
            break
        else
            wait=1
            if [[ $count -eq 1 ]]
            then
                echo -n "wait for ldap "
            else
                echo -n "."
                sleep 2
            fi
        fi
    done

    if [[ $result -ne 0 ]]; then
        echo ""
        echo "error: LDAP not initialized !"
        exit 1
    fi
}

if [ ! -f /data/inited ]; then
    DOMAIN_DN="dc=test,dc=net"
    DOMAIN_DB_NAME="test_net"

    # init ds389 storage
    repeat "dsconf localhost config replace nsslapd-dynamic-plugins=on" "nsslapd-dynamic-plugins=on"

    #repeat "dsconf localhost plugin memberof enable" "plugin memberof enable"
    #repeat "dsconf localhost plugin memberof set --skipnested on" "plugin memberof set --skipnested on"

    repeat "dsconf localhost plugin usn enable" "plugin usn enable"

    repeat "dsconf localhost plugin usn global on" "plugin usn global on"

    repeat "dsconf localhost plugin attr-uniq add --enabled on --attr-name customUniqueName \
        --subtree $DOMAIN_DN --across-all-subtrees on 'customUniqueName Attribute Uniqueness'" "plugin attribute uniqueness enable"

    #repeat "dsconf localhost config replace nsslapd-malloc-mxfast=0" "nsslapd-malloc-mxfast=0"

    #repeat "dsconf localhost config replace nsslapd-malloc-trim-threshold=4069" "nsslapd-malloc-trim-threshold=4069"

    #repeat "dsconf localhost config replace nsslapd-malloc-mmap-threshold=33554432" "nsslapd-malloc-mmap-threshold=33554432"

    echo -e "\nbasedn = $DOMAIN_DN" >> /data/config/container.inf

    # import schema
    repeat "ldapmodify -H LDAP://127.0.0.1:3389 -D 'cn=Directory Manager' -w $DS_DM_PASSWORD -f /data.init/schema.ldif" "schema created"

    # create database instance
    # !!! It's important to create instance after schema modification. 
    # !!! Otherwise domain uniqueIdentifier didn't get into the index and it couldn't be found by id!
    repeat "dsconf localhost backend create --suffix $DOMAIN_DN --be-name $DOMAIN_DB_NAME" "db created"
    repeat "ldapmodify -H LDAP://127.0.0.1:3389 -D 'cn=Directory Manager' -w $DS_DM_PASSWORD -f /data.init/struct.ldif" "structure created"

    touch /data/inited
fi

echo "ldap storage inited"
