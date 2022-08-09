"""Profile for er Version 1.0
https://github.com/oasis-tcs/openc2-ap-er/blob/working/oc2edr.md
Conformant to Conformance Clauses ?
"""
import json
import subprocess
import os
import time
from pathlib import Path
from yuuki import Actuator, OpenC2CmdFields, OpenC2RspFields, StatusCode

er = Actuator(nsid='er')
seconds = time.time()
localtime = time.ctime(seconds)
OS = "Mac"



#These functions will be changed when there is knowledge of the Actions or Targets involved in er

@er.pair('allow', 'domain_name', implemented=False)
def allow_domain_name(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    device = oc2_cmd.target.get("domain_name", None)
    if device is None:
        status_text = f'No Domain Name Specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    else:
        r = "Domain Name Allowed"

    return OpenC2RspFields(status=StatusCode.OK, results=r)


@er.pair('allow', 'device', implemented=True)
def allow_device(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    device = oc2_cmd.target.get("device", None)
    if device is None:
        status_text = f'No Device Specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    else:

        # checking device list and not finding specified device will produce 500 "Cannot access device"

        r = "Device Allowed"

    if c := device.pop("hostname", None):
        # put it somewhere we can use it
        r = "Device Allowed"+c
    if c := device.pop("idn_hostname", None):
        # put it somewhere we can use it
        r = "Device Allowed" + c
    if c := device.pop("device_id", None):
        # put it somewhere we can use it
        r = "Device Allowed" + c

    return OpenC2RspFields(status=StatusCode.OK, results=r)


@er.pair('allow', 'file', implemented=True)
def allow_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    file = oc2_cmd.target.get("file", None)
    if file is None:
        status_text = f'Cannot Access File'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    else:

        # if file cannot be accessed, status code 500 "Cannot access file"

        r = "File Allowed"

    if c := file.pop("name", None):
        # put it somewhere we can use it
        r = "File Allowed"+c
    if c := file.pop("path", None):
        # put it somewhere we can use it
        r = "File Allowed" + c
    if c := file.pop("hashes", None):
        # put it somewhere we can use it
        r = "File Allowed" + c

    return OpenC2RspFields(status=StatusCode.OK, results=r)


@er.pair('allow', 'ipv4_net', implemented=False)
def allow_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Target type not supported'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@er.pair('allow', 'ipv6_net', implemented=False)
def allow_ipv6_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
    found_keys = []
    found_other = []
    if isinstance(oc2_cmd.target['ipv6_connection'], dict):
        for key in oc2_cmd.target['ipv6_connection'].keys():
            if key in allowed_keys:
                found_keys.append(key)
            else:
                found_other.append(key)

    if len(found_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Any of {str(allowed_keys)} required for ipv6_connection')

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@er.pair('deny', 'domain_name', implemented=False)
def deny_domain_name(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Target type not supported'
    return OpenC2RspFields(status=501, status_text=status_text)


@er.pair('deny', 'file', implemented=True)
def file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    file = oc2_cmd.target.get("file", None)
    if file is None:
        status_text = f'Cannot access file'  #'No File Specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    else:
        # Logic for accessing and denying file
        r = "File Denied"

    if c := file.pop("name", None):
        # put it somewhere we can use it
        r = "File Denied"+c
    if c := file.pop("path", None):
        # put it somewhere we can use it
        r = "File Denied" + c
    if c := file.pop("hashes", None):
        # put it somewhere we can use it
        r = "File Denied" + c

    return OpenC2RspFields(status=StatusCode.OK, results=r)
    

@er.pair('deny', 'ipv4_net', implemented=False)
def deny_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Target type not supported'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@er.pair('deny', 'ipv6_net', implemented=False)
def deny_ipv6_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
    found_keys = []
    found_other = []
    if isinstance(oc2_cmd.target['ipv6_connection'], dict):
        for key in oc2_cmd.target['ipv6_connection'].keys():
            if key in allowed_keys:
                found_keys.append(key)
            else:
                found_other.append(key)

        if len(found_keys) < 1 or len(found_other) > 0:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                    status_text=f'Any of {str(allowed_keys)} required for ipv6_connection')

        else:
            # Execute a real function here to deny...
            return OpenC2RspFields(status=StatusCode.OK)
    else:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST)


@er.pair('contain', 'device', implemented=False)
def contain_device(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    device = oc2_cmd.target.get("device", None)
    if device is None:
        status_text = f'Cannot access device'  #'No Device Specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    containment = oc2_cmd.args.get("device_containment", None)
    if containment is None:
        status_text = f'Containment type argument not specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    allowed_keys = ['device_containment', 'permitted_addresses', 'duration', 'start_time', 'stop_time', 'response_requested', 'comment']
    found_keys = []
    found_other = []

    for x in oc2_cmd.args():
        if x in allowed_keys:
            found_keys.append(x)
        else:
            found_other.append(x)

    if len(found_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                   status_text=f'Any of {str(allowed_keys)} args expected, got {str(found_other)}')

    else:
        # Execute a real function here to deny...

        r = "Cannot Access Device"
        fields = ""

    if c := device.pop("hostname", None):
        # put it somewhere we can use it
        fields += "hostname: " + c + " "
        # Execute containment on this attribute

    if c := device.pop("idn_hostnane", None):
        # put it somewhere we can use it
        fields += "idn_hostname: " + c + " "
        # Execute containment on this attribute

    if c := device.pop("device_id", None):
        # put it somewhere we can use it
        fields += "device_id: " + c + " "
        # Execute containment on this attribute

    if fields.__len__() > 2:
        r = "Device Contained: "+fields

    return OpenC2RspFields(status=StatusCode.OK, results=r)


@er.pair('contain', 'file', implemented=False)
def contain_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    file = oc2_cmd.target.get("file", None)
    if file is None:
        status_text = f'No File Specified'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    else:
        r = "File Denied"

    if c := file.pop("name", None):
        # put it somewhere we can use it
        r = "File Denied"+c
    if c := file.pop("path", None):
        # put it somewhere we can use it
        r = "File Denied" + c
    if c := file.pop("hashes", None):
        # put it somewhere we can use it
        r = "File Denied" + c

    return OpenC2RspFields(status=StatusCode.OK, results=r)


@er.pair('create', 'registry_entry', implemented=False)
def create_registry_entry(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    # Not a Windows Device
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)


@er.pair('delete', 'file', implemented=True)
def delete_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    # Mock command execution currently
    status_text = f'Command Successful'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@er.pair('delete', 'registry_entry', implemented=False)
def delete_registry_entry(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    # Not a Windows Device
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
    

@er.pair('delete', 'service', implemented=True)
def delete_service(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    # Mock command execution currently
    status_text = f'Service deleted'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@er.pair('start', 'file', implemented=True)
def start_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    filename = oc2_cmd.target.get("filename", None)

    if filename is None:
        status_text = f'Cannot access file'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)
    elif file_path := os.path.join(Path(__file__).resolve().parent, "files/"+filename):

                    if os.path.exists(file_path):
                        with open(file_path, "r") as f:
                            f.close()
                    else:
                        return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="Cannot access file")   # "error performing er retrieval"

    # check for downstream device arg, if missing 500 "Downstream device argument not populated"
    downstream = oc2_cmd.args.get("downstream_device", None)
    if downstream is None:
        status_text = f'Downstream device argument not populated'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    if OS == "Mac":
        subprocess.call(['open', '-W', '-a', 'Terminal.app', 'python', '--args', filename])
        result = "Process "+filename+" was run: " # append subprocess results or code
    elif OS == "Windows":
        # different process for Windows
        return OpenC2RspFields(status=501, status_text="Command not supported")

    # Mock command execution currently
    status_text = f'Command Successful'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@er.pair('stop', 'device', implemented=True)
def stop_device(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
    

@er.pair('stop', 'process', implemented=False)
def stop_process(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    # out of order checks, but shows those checks properly while remaining unimplemented

    downstream = oc2_cmd.args.get("downstream_device", None)
    if downstream is None:
        status_text = f'Downstream device argument not populated'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    target_specifiers = oc2_cmd.get("Target", None)
    if target_specifiers is None:
        status_text = f'Process Target does not have any properties populated'
        return OpenC2RspFields(status=400, status_text=status_text)

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
        

@er.pair('stop', 'service', implemented=False)
def stop_service(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    # out of order checks, but shows those checks properly while remaining unimplemented

    downstream = oc2_cmd.args.get("downstream_device", None)
    if downstream is None:
        status_text = f'Downstream device argument not populated'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    target_specifiers = oc2_cmd.get("Target", None)
    if target_specifiers is None:
        status_text = f'Service Target does not have any properties populated'
        return OpenC2RspFields(status=400, status_text=status_text)

    status_text = f'Command Not Supported'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
    
    
@er.pair('restart', 'device', implemented=False)
def restart_device(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
    

@er.pair('restart', 'process', implemented=True)
def restart_process(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    #Mock command execution currently
    status_text = f'Process Started'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@er.pair('scan', 'device', implemented=False)
def scan_device(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    #args must support and may include scan_depth, periodic_scan

    depth_keys = ['shallow', 'deep']
    periodic_keys = ['enabled', 'disabled']
    found_depth_keys = []
    found_periodic_keys = []
    found_other = []
    if isinstance(oc2_cmd.args['scan_depth'], dict):
        for key in oc2_cmd.args['scan_depth'].keys():
            if key in depth_keys:
                found_depth_keys.append(key)
            else:
                found_other.append(key)

    if isinstance(oc2_cmd.target['periodic_scan'], dict):
        for key in oc2_cmd.target['periodic_scan'].keys():
            if key in periodic_keys:
                found_periodic_keys.append(key)
            else:
                found_other.append(key)

    if len(found_depth_keys)+len(found_periodic_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Unsuitable Scan Arguments: {str(found_other)}')

    # Mock command execution currently
    status_text = f'Device Scanned'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)


@er.pair('set', 'ipv4_net', implemented=False)
def set_ipv4_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    #Mock command execution
    #status_text = f'IPv4 Set'
    #return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)

    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
        

@er.pair('set', 'ipv6_net', implemented=False)
def set_ipv6_net(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    allowed_keys = ['src_addr', 'src_port', 'dst_addr', 'dst_port', 'protocol']
    found_keys = []
    found_other = []
    if isinstance(oc2_cmd.target['ipv6_connection'], dict):
        for key in oc2_cmd.target['ipv6_connection'].keys():
            if key in allowed_keys:
                found_keys.append(key)
            else:
                found_other.append(key)

    if len(found_keys) < 1 or len(found_other) > 0:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                               status_text=f'Any of {str(allowed_keys)} required for ipv6_connection')

    #Mock command execution currently
    status_text = f'IPv6 Set'
    return OpenC2RspFields(status=StatusCode.OK, status_text=status_text)
    
    
@er.pair('set', 'registry_entry', implemented=False)
def set_registry_entry(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    status_text = f'Command Not Implemented'
    return OpenC2RspFields(status=StatusCode.NOT_IMPLEMENTED, status_text=status_text)
    

@er.pair('set', 'account', implemented=True)
def set_account(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:
    account_fields = oc2_cmd.target.get("account", {})
    print(account_fields)

    downstream = oc2_cmd.args.get("downstream_device", None)
    if downstream is None:
        status_text = f'Downstream device argument not populated'
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST, status_text=status_text)

    if status:= getattr(oc2_cmd.args, "account_status", None):
        status = str.lower(status)
        print(status)
        if status == "enabled" or status == "disabled":

            #Mock Account Code Here
            if c := account_fields.pop("uid", None):
                for element in c:
                    er_file = os.path.join(Path(__file__).resolve().parent, "files/"+c)
                    #print("Opening file: "+er_file)
                    if os.path.exists(er_file):
                        with open(er_file, "w") as f:
                            f.write(status)
                            f.close()
                            g = {"status": str(status)}
                        return OpenC2RspFields(status=StatusCode.OK, results=g)
                    else:
                        return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="error performing er retrieval")
            else:
                return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                           status_text=f'account uid required')

        else:
            return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                                       status_text=f'account status required, got: '+status)

        pass
    else:
        return OpenC2RspFields(status=StatusCode.BAD_REQUEST,
                           status_text=f'account status required, found None')


@er.pair('update', 'file', implemented=True)
def update_file(oc2_cmd: OpenC2CmdFields) -> OpenC2RspFields:

    if c := oc2_cmd.target.get("filename", None):
        for element in c:
            er_file = os.path.join(Path(__file__).resolve().parent, "files/" + c)
            # print("Opening file: "+er_file)
            if os.path.exists(er_file):
                with open(er_file, "a") as f:
                    f.write("updated: "+localtime)
                    f.close()
                    result = {"status": "updated"+str(localtime)}
                return OpenC2RspFields(status=StatusCode.OK, results=result)
            else:
                return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="error performing update")
    else:
        return OpenC2RspFields(status=StatusCode.NOT_FOUND,
                               status_text=f'file not found')







"""
@er.pair('query', 'er', implemented=True)
def query_er(oc2_cmd: OpenC2CmdFields) ->OpenC2RspFields:

    query_fields = oc2_cmd.target.get("er", {})
    print(query_fields)

    if c := query_fields.pop("content", None):
        for element in c:
            if element == "cyclonedx":
                er_file = os.path.join(Path(__file__).resolve().parent, "files/CycloneExample.bom.1.3.json")
            elif element == "cyclone":
                er_file = os.path.join(Path(__file__).resolve().parent, "files/CycloneExample.bom.1.3.json")
            elif element == "spdx2":
                er_file = os.path.join(Path(__file__).resolve().parent, "files/SPDXJSONExample-v2.2.spdx.json")
            else:
                er_file = os.path.join(Path(__file__).resolve().parent, "files/SPDXJSONExample-v2.2.spdx.json")
    else:
        er_file = os.path.join(Path(__file__).resolve().parent, "files/SPDXJSONExample-v2.2.spdx.json")

    if os.path.exists(er_file):
        with open(er_file, "r") as f:
            print("Printing "+er_file)
            er: dict = json.load(f)
        return OpenC2RspFields(status=StatusCode.OK, results=er)
    return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="error performing er retrieval")
    
    
    
    
    
            er_file = os.path.join(Path(__file__).resolve().parent, "files/Registry" + c)
        # print("Opening file: "+er_file)
        if os.path.exists(er_file):
            with open(er_file, "a") as f:
                f.write("New Entry Created: "+localtime)
                f.close()
                result = {"New Entry Created": "Created"+str(localtime)}
            return OpenC2RspFields(status=StatusCode.OK, results=result)
        else:
            return OpenC2RspFields(status=StatusCode.NOT_FOUND, status_text="Error Creating Entry")
"""

