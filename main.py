import itertools, uuid, random, time, paramiko, os, datetime

from ldap3 import Server, Connection, MODIFY_ADD, SAFE_SYNC, SUBTREE
from multiprocessing.dummy import Pool

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

# Dbmon logging params
DBMON_LOG_MODE = "local" # "ssh" | "local" | "off"

# If DBMON_LOG_MODE = "ssh" be sure to change variables below
SSH_PORT = 22
SSH_LOGIN = "admin"
SSH_PWD = "admin"

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
    ensure_log_dir_exists()

    conns = open_connection(CONNECTION_COUNT)

    try:
        log("Starting tests...")
        groups = gen_attrs(OBJECT_COUNT, GROUP_PREFIX)
        _t1, group_ids = tc(f"{OBJECT_COUNT} groups created",
                            insert, conns, GROUP, groups)
    
        for i in range(1, ITER_COUNT+1):
            dbmon_log(f"before_{i}.log")
            log(f"Start iteration {i}")
            t2, _res2 = tc(f"Iteration {i} finished",
                           run_iteration, conns, group_ids, i)
        
        _t3, _res3 = tc(f"{OBJECT_COUNT} groups deleted",
                        delete, conns, groups)
        dbmon_log(f"after_del_groups.log")

        log("All tests are done!")
    except Exception as e:
        log(f"Error: {e}")
    finally:
        close_connection(conns)

def run_iteration(conns, group_ids, iter):
    obj_name = f"{OBJECT_PREFIX}({iter})"
    entries = gen_attrs(OBJECT_COUNT, obj_name)
    _t1, object_ids = tc(f"{OBJECT_COUNT} objects created",
                         insert, conns, OBJECT, entries)
    dbmon_log(f"after_ins_{iter}.log")

    _t2, _res2 = tc(f"{OBJECT_COUNT} groups linked with {MEMBER_COUNT} objects",
                    modify, conns, group_ids, object_ids, MEMBER_COUNT)
    dbmon_log(f"after_upd_{iter}.log")

    _t3, _res3 = tc(f"{OBJECT_COUNT} objects deleted",
                    delete, conns, entries)
    dbmon_log(f"after_del_obj_{iter}.log")

def insert(conns, type, attrs):
    args = zip(itertools.cycle(conns), itertools.repeat(type), attrs)
    return pmap(ldap_add, args)

def modify(conns, groups, entries, count):
    attrs = insert_members(groups, entries, count)
    args = zip(itertools.cycle(conns), *zip(*attrs))
    return pmap(ldap_modify, args)

def delete(conns, entries):
    args = zip(itertools.cycle(conns), entries)
    return pmap(ldap_delete, args)

def ldap_add(conn, object_class, attrs):
    uuid = attrs[UUID]
    dn = build_dn(attrs)
    
    return uuid if conn.add(dn, object_class, attrs) else None

def ldap_modify(conn, group_id, upd_attrs):
    search_attrs = [MEMBER, UUID, OBJECT_CLASS]
    member_ids = uuids_from_attrs(upd_attrs)
    entries = search_by_id(conn, [group_id] + member_ids, search_attrs)
    group_dn = find_group_dn(group_id, entries)
    _parents = search_parent(conn, group_id, search_attrs)

    return conn.modify(group_dn, upd_attrs)

def ldap_delete(conn, attr):
    dn = build_dn(attr)

    return conn.delete(dn)

def ldap_search(conn, filter, search_scope=SUBTREE, attrs=None):
    status, _result, response, _ = conn.search(ROOT_DN, filter, search_scope, attributes=attrs)
    return response if status else False

def uuids_from_attrs(attrs):
    _modify_op, uuids = attrs[MEMBER][0]
    return uuids

def search_by_id(conn, uuids, attrs=None):
    filter_attrs = map(lambda id: eq_filter(UUID, id), uuids)
    filter = or_filter(filter_attrs)
    return ldap_search(conn, filter, attrs=attrs)

def find_group_dn(group_id, entries):
    return list(filter(lambda e: e[ATTRIBUTES][UUID] == group_id, entries))[0][DN]

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
    return build_filter("&", attrs)

def or_filter(attrs):
    return build_filter("|", attrs)

def not_filter(attrs):
    return build_filter("!", attrs)

def build_filter(op, attrs):
    return f"({op}{''.join(attrs)})"

def build_dn(attrs):
    return f"{attrs[CN]},{ROOT_DN}"

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
    return [conn.unbind() for conn in connections]

def pmap(f, args):
    with Pool(CONNECTION_COUNT) as pool:
        return pool.starmap(f, args)

def gen_attrs(count, name):
    return [{CN: gen_name(name, x), UUID: gen_uuid()} for x in range(1, count+1)]

def gen_name(name, iter):
    return f"{CN}={name}-{iter}"

def gen_uuid():
    return str(uuid.uuid4())

def tc(msg, f, *args):
    start = time.time()
    result = f(*args)
    end = time.time()

    dt = end - start
    log(f"{msg} in {dt:.4f} sec")

    return dt, result

def log(msg):
    now = datetime.datetime.now()
    print(f"{now}: {msg}")

def dbmon_log(filename):
    cmd = f"docker exec {CONTAINER_NAME} dsconf localhost monitor dbmon"
    file_path = f"{LOG_DIR}{filename}"
    response = None

    if DBMON_LOG_MODE == "ssh":
        ssh_con = ssh_connection()

        try:
            _stdin, stdout, _stderr = ssh_con.exec_command(cmd)
            outlines = stdout.readlines()
            response = "".join(outlines)
        except Exception as e:
            log(f"Error: {e}")
        finally:
            ssh_con.close()
    elif DBMON_LOG_MODE == "local":
        response = os.popen(cmd).read()
    elif DBMON_LOG_MODE == "off":
        return
    else:
        log("DBMON_LOG_MODE can be either 'ssh' | 'local' | 'off'")

    write_to_file(file_path, response)

def ssh_connection():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, SSH_PORT, SSH_LOGIN, SSH_PWD)

    return ssh

def write_to_file(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)

def ensure_log_dir_exists():
    return os.makedirs(os.path.dirname(LOG_DIR), exist_ok=True) if DBMON_LOG_MODE != "off" else None

main()