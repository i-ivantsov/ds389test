FROM 389ds/dirsrv:2.4

RUN zypper --non-interactive mr -d repo-openh264 && zypper --non-interactive install openldap2-client jemalloc && zypper clean
ENV LD_PRELOAD=/usr/lib64/libjemalloc.so.2
ENV DS_DM_PASSWORD="test"

RUN mkdir -p /data.init

COPY ./ldap_init.sh /data.init
COPY ./struct.ldif /data.init
COPY ./schema.ldif /data.init
COPY ./start_389ds.sh /data.init

CMD [ "/data.init/start_389ds.sh" ]