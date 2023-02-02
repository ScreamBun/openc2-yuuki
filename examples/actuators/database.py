"""internal test for os query use
"""
from os import path
from pathlib import Path
from configparser import ConfigParser
from osquery_orm import OsQueryDatabase
from peewee import ModelSelect

from oc2_arch import Actuator, OpenC2CmdFields, OpenC2RspFields, StatusCode

database = Actuator(nsid='database')

# Common OSQuery tables and their fields
CommonTables = ("arp_cache", "atom_packages", "azure_instance_metadata", "azure_instance_tags", "carbon_black_info",
                "carves", "chrome_extension_content_scripts", "chrome_extensions", "cpuid", "curl", "curl_certificate",
                "ec2_instance_metadata", "ec2_instance_tags", "etc_hosts", "etc_protocols", "etc_services", "example",
                "file", "firefox_addons", "groups", "hash", "intel_me_info", "interface_addresses", "interface_details",
                "kernel_info", "listening_ports", "logged_in_users", "os_version", "osquery_events",
                "osquery_extensions", "osquery_flags", "osquery_info", "osquery_packs", "osquery_registry",
                "osquery_schedule", "platform_info", "process_memory_map", "process_open_sockets", "processes",
                "python_packages", "routes", "secureboot", "ssh_configs", "startup_items", "system_info", "time",
                "uptime", "user_groups", "user_ssh_keys", "users", "ycloud_instance_metadata")
TableOverrides = {
    # Common Tables
    "ARPCache": "ARP_Cache",
    "EC2InstanceMetadata": "EC2_InstanceMetadata",
    "EC2InstanceTags": "EC2_InstanceTags",
    "OSVersion": "OS_Version",
    "SSHConfigs": "SSH_Configs",
    # Linux Tables
    "IPTables": "IP_Tables",
    # Windows Tables
    "CPUInfo": "CPU_Info",
    "DNSCache": "DNS_Cache",
    "IEExtensions": "IE_Extensions",
    "NTFSACLPermissions": "NTFS_ACL_Permissions",
    "NTFSJournalEvents": "NTFS_JournalEvents"
}
NameOverride = {
    "os": "OS"
}

config = ConfigParser()
act_dir = Path(__file__).resolve().parent
with open(path.join(act_dir, 'osquery_conf.ini'), "r") as f:
    config.read_file(f)
v = config['osquery']["socket"]
orm = OsQueryDatabase(f'{v}')
print("connecting to ORM at "+str(v))
orm.connect()


def getTableName(_name: str):
    fixed_name = []
    for c in _name.split("_"):
        fixed_name.append(NameOverride.get(c.lower(), c.capitalize()))
    return "".join(fixed_name)


@database.pair('query', 'database', implemented=True)
def query_database(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    query_fields = oc2_cmd.target.get("database", {})
    if (db := query_fields.pop("database", None)) and db == "system":

        if t := query_fields.pop("table", None):
            print(t)
            if t.lower() in CommonTables:
                name = getTableName(t)
                model = getattr(orm.tables._cross_platform, TableOverrides.get(name, name), None)
                if model is None:
                    return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text="table not found in DB")
                qry = model
            else:
                return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text="error performing db search, unexpected table")

            print(f"TEST -  {qry}")
            if filters := query_fields.pop("filters", None):
                fields = [getattr(model, f) for f in filters.get("fields", [])]
                qry = qry.select(*fields)

            qry = qry if isinstance(qry, ModelSelect) else model.select()
            if len(qry) > 0:
                return OpenC2RspFields(status=StatusCode.OK, results={"database": {t: [r.dict() for r in qry]}})
            return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="error performing osquery function")
        else:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text="error performing osquery function: no table given")
    else:
        return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text="error performing osquery function: target DB improperly specified.")

# else: return OpenC2RspFields(status_text="error performing db function, unknown arguments")


"""
@os_query.pair('query', 'os_version', implemented=True)
def query_os_version(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    result = orm.tables._cross_platform.OS_Version.select()
    if result.status.code != 0:
        return OpenC2RspFields("error performing osquery function")
    result=list(result)
    return OpenC2RspFields(status=StatusCode.OK, status_text=result)

older version from when we were returning multiple queries per command
@os_query.pair('query', 'file', implemented=True)
def query_os_version(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    result = ""
    for key in oc2_cmd.target:
        result.__add__(orm.tables._cross_platform.file.select(key, oc2_cmd.target.values()))
        if result.status.code != 0:
            return OpenC2RspFields("error performing osquery function")
    result = list(result)
    return OpenC2RspFields(status=StatusCode.OK, status_text=result)

"""