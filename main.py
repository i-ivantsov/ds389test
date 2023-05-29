import itertools, uuid, random, time, paramiko, os, datetime

from ldap3 import Server, Connection, MODIFY_ADD, SAFE_SYNC, SUBTREE
from multiprocessing.dummy import Pool as ThreadPool

# 389ds connection
HOST = "172.18.106.239"
PORT = 3389
USER = "cn=Directory Manager"
PASSWORD = "test"
ROOT_DN = "dc=test,dc=net"

# Schema params
DN = "dn"
CN = "cn"
OBJECT_CLASS = "objectClass"
ATTRIBUTES = "attributes"
NSTOBSTONE_ATTR = "nsTombstone"

GROUP = "customGroup"
OBJECT = "customObject"
MEMBER = "customMember"
UUID = "customUUID"

# Ssh connection (dbmon logging)
SSH_PORT = 22
SSH_LOGIN = "rateladmin"
SSH_PWD = "1111"
LOG_DIR = "logs/"
CONTAINER_NAME = "c389ds"

# Script params
ITER_COUNT = 100
CONNECTION_COUNT = 25
OBJECT_COUNT = 10_000
MEMBER_COUNT = 20

GROUP_PREFIX = "Group"
OBJECT_PREFIX = "Obj"

def main():
    os.makedirs(os.path.dirname(LOG_DIR), exist_ok=True)

    conns = open_connection(CONNECTION_COUNT)

    try:
        groups = gen_attrs(OBJECT_COUNT, GROUP_PREFIX)
        _t1, group_ids = tc(f"{OBJECT_COUNT} groups created in",
                        insert, conns, GROUP, groups)
    
        for i in range(1, ITER_COUNT+1):
            dbmon_log(f"before_{i}.log")
            print(f"Start iteration {i}")
            t2, _res2 = tc(f"Iteration {i} finished in",
                         run_iteration, conns, group_ids, i)
        
        _t3, _res3 = tc(f"{OBJECT_COUNT} groups deleted in",
                        delete, conns, groups)
        dbmon_log(f"after_del_groups.log")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        close_connection(conns)

def run_iteration(conns, group_ids, iter):
    obj_name = f"{OBJECT_PREFIX}({iter})-"
    entries = gen_attrs(OBJECT_COUNT, obj_name)
    _t1, object_ids = tc(f"{OBJECT_COUNT} objects created in",
                    insert, conns, OBJECT, entries)
    dbmon_log(f"after_ins_{iter}.log")

    _t2, _res2 = tc(f"{OBJECT_COUNT} groups linked with {MEMBER_COUNT} objects in",
                    modify, conns, group_ids, object_ids, MEMBER_COUNT)
    dbmon_log(f"after_upd_{iter}.log")

    _t3, _res3 = tc(f"{OBJECT_COUNT} objects deleted in",
                    delete, conns, entries)
    dbmon_log(f"after_del_obj_{iter}.log")

def insert(conns, type, attrs):
    f = lambda conn, attrs: [ldap_add(conn, type, attrs)]
    args = zip(itertools.cycle(conns), attrs)
    return flatten(pmap(f, args))

def modify(conns, groups, entries, count):
    attrs = insert_members(groups, entries, count)

    f = lambda conn, group_id, attrs: [ldap_modify(conn, group_id, attrs)]
    args = zip(itertools.cycle(conns), *list(zip(*attrs)))
    return pmap(f, args)

def delete(conns, entries):
    f = lambda conn, dn: [ldap_delete(conn, dn)]
    args = zip(itertools.cycle(conns), entries)
    pmap(f, args)

def ldap_add(conn, object_class, attrs):
    cn = attrs[CN]
    dn = full_dn(cn)
    uuid = attrs[UUID]
    
    return uuid if conn.add(dn, object_class, attrs) else None

def ldap_modify(conn, group_id, upd_attrs):
    search_attrs = [MEMBER, UUID, OBJECT_CLASS]

    member_ids = uuids_from_attrs(upd_attrs)
    entries = search_by_id(conn, [group_id] + member_ids, search_attrs)
    group_dn = list(map(lambda y: y[DN], filter(lambda x: x[ATTRIBUTES][UUID] == group_id, entries)))[0]
    _parents = search_parent(conn, group_id, search_attrs)

    return conn.modify(group_dn, upd_attrs)

def uuids_from_attrs(attrs):
    _, uuids = attrs[MEMBER][0]
    return uuids

def search_by_id(conn, uuids, attrs=None):
    filter_attrs = map(lambda id: eq_filter(UUID, id), uuids)
    filter = or_filter(filter_attrs)
    return ldap_search(conn, filter, attrs=attrs)

def search_parent(conn, id, attrs=None):
    filter = and_filter([
        eq_filter(OBJECT_CLASS, GROUP),
        not_filter([eq_filter(OBJECT_CLASS, NSTOBSTONE_ATTR)]),
        eq_filter(MEMBER, id)
    ])
    return ldap_search(conn, filter, attrs=attrs)

def eq_filter(k, v):
    return f"({k}={v})"

def and_filter(attrs):
    return f"(&{''.join(attrs)})"

def or_filter(attrs):
    return f"(|{''.join(attrs)})"

def not_filter(attrs):
    return f"(!{''.join(attrs)})"

def ldap_search(conn, filter, search_scope=SUBTREE, attrs=None):
    status, _result, response, _ = conn.search(ROOT_DN, filter, search_scope, attributes=attrs)
    return response if status else False

def ldap_delete(conn, attr):
    cn = attr["cn"]
    dn = full_dn(cn)

    return conn.delete(dn)

def full_dn(cn):
    return f"{cn},{ROOT_DN}"

def insert_members(groups, entries, count):
    attrs = list()

    for g in groups:
        rand_uuids = select_rand(entries, count)
        attrs.append((g, {MEMBER: [(MODIFY_ADD, rand_uuids)]}))

    return attrs

def select_rand(entries, count):
    return random.sample(entries, count)

def open_connection(count):
    conns = []

    for _ in range(count):
        server = Server(HOST, port=PORT)
        connection = Connection(server, user=USER, password=PASSWORD, client_strategy=SAFE_SYNC, auto_bind=True)
        conns.append(connection)

    return conns

def close_connection(connections):
    [conn.unbind() for conn in connections]

def pmap(f, args):
    pool = ThreadPool(CONNECTION_COUNT)
    res = pool.starmap(f, args)
    pool.close()
    pool.join()

    return res

def gen_attrs(count, name):
    entries = [{CN: f"{CN}={name}{x}", UUID: gen_uuid()} for x in range(count)]
    return entries

def gen_uuid():
    return str(uuid.uuid4())

def tc(msg, f, *args):
    start = time.time()
    result = f(*args)
    end = time.time()

    dt = end - start
    now = datetime.datetime.now()
    print(f"{now}: {msg} {dt:.4f} sec")

    return dt, result

def flatten(arr):
    return list(itertools.chain.from_iterable(arr))

def dbmon_log(filename):
    cmd = f"docker exec {CONTAINER_NAME} dsconf localhost monitor dbmon"
    file_path = f"{LOG_DIR}{filename}"

    ssh_con = ssh_connection()

    try:
        _stdin, stdout, _stderr = ssh_con.exec_command(cmd)
        outlines = stdout.readlines()
        resp = "".join(outlines)

        write_to_file(file_path, resp)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh_con.close()

def ssh_connection():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, SSH_PORT, SSH_LOGIN, SSH_PWD)

    return ssh

def write_to_file(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)

main()