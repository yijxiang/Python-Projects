#!/usr/bin/python

import requests, json, sys, os, subprocess, logging
from getpass import getpass
from tqdm import tqdm
from datetime import datetime
from create_excel_v2 import create_excel_v2

__author__ = "AUTHOR"

requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False

logging.basicConfig(
                    format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
                    filename="logs/delete_ips_btd.log", datefmt='%m/%d/%Y - %H:%M:%S'
                    )
logger = logging.getLogger("bt_diamond")

try:
    os.mkdir("./logs")  # make directory relative to script location if it doesn't exist
    print("\n-- Directory ./logs was created and the log file generated now will be stored there. --\n")
except OSError as e:
    msg = e
    # print("-- Directory ./logs already exists and log file generated now will be stored there. --\n")


btd_url = "https://IPCONTROL:PORT" #DEV
api_base_url = btd_url+'/inc-rest/api/v1/'

master_dns_ip = ""


###############
#### LOGIN ####
###############

login_url = btd_url+"/inc-rest/api/v1/login"
un = ""
pw = ""

# un = input('Username: ')
# pw = getpass(prompt='Password: ')

headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
creds = f"username={un}&password={pw}"
r = requests.post(login_url, data=creds, verify=False)

if r.status_code == 200:
    print("\nLogin Successful!!\n")
    logger.info("Login Successful!")
else:
    print("Login Failure!")
    logger.error("Login Failure!")
    sys.exit()

token = json.loads(r.text)['access_token']
headers.update({'Authorization' : 'Bearer ' + token})
headers.update({'Content-Type' : 'application/json'})


#############################
####  DETLETE DHCP ENTRY ####
#############################

devices = [
    {"ip": "192.168.9.8", "hostname": "WLCNAME"},
    {"ip": "192.168.9.9", "hostname": "test_99"},
    {"ip": "192.168.9.10", "hostname": "Test_7"}
    ]

errors = []
data = []
data2 = []

for device in tqdm(devices, desc="Deleting IPs"):
    payload1 = {"ipAddress": device['ip']}
    
    try:
        btd_device = requests.get(f"{api_base_url}Gets/getDeviceByIPAddr", headers=headers, params=payload1, verify=False)
        r = json.loads(btd_device.text)
        alias = str(r['aliases'])[1:-1]
        host_name = r['hostname']
        description = r['description']
        addr_type = r['addressType']
        dev_type = r['deviceType']
        domain = r['domainName']
        custom_fields = str(r['userDefinedFields'])[1:-1]
        # owner_id = r['userDefinedFields'][0]
        # app_id = r['userDefinedFields'][1]
        id = r['id']

        data_row = {
        "Status": "", "Address": device['ip'], "Hostname - Provided": device['hostname'], 
        "Hostname - Actual": host_name, "Aliases": alias, "Description": description, "Device Type": dev_type, 
        "Address Type": addr_type, "Domain": domain, "Owner/APP": custom_fields, "IPControl ID #": id, "Restore ID #": ""
        }

    except:

        data_row = {
        "Status": "Unchanged - Item NOT Found", "Address": device['ip'], "Hostname - Provided": device['hostname'], 
        }
        data.append(data_row)

        logger.error(f"IP {device['ip']} not found in IPContol.  The Current Entry will NOT be deleted.")
        errors.append(f"IP {device['ip']} - not found in IPControl.")
        continue

    with open(os.devnull, 'w') as DEVNULL:
        try:
            subprocess.check_call(
                    ['ping', '-c', '1', device['ip']],
                    stdout=DEVNULL,  # suppress output
                    stderr=DEVNULL
                    )
            first_ping = True
            is_up = True
            logger.warning(f"1st Ping Status: ICMP Ping Response Recieved from IP {device['ip']}")
        except:
            first_ping = False
            logger.info(f"1st Ping Status: NO ICMP Ping Response From IP {device['ip']}")

        if first_ping == False:
            try:
                subprocess.check_call(
                    ['ping', '-c', '1', device['ip']],
                    stdout=DEVNULL,  # suppress output
                    stderr=DEVNULL
                    )
                is_up = True
                logger.warning(f"2nd Ping Status: ICMP Ping Response Recieved from IP {device['ip']}")
            except subprocess.CalledProcessError:
                is_up = False
                logger.info(f"2nd Ping Status: NO ICMP Ping Response From IP {device['ip']}")

    if is_up == False:

        if host_name == device['hostname']:

            # DELETE DEVICE

            payload2 = str({"inpDev": {"ipAddress": device['ip']}})
            delete_device = requests.delete(f"{api_base_url}Deletes/deleteDevice", headers=headers, data=payload2, verify=False)
            response_text = json.loads(delete_device.text)
            data_row.update({"Status": "Removed"})
            logger.info(f"IP {device['ip']} has been deleted.  IPControl Message: {response_text}")

            # GENERATE RESTORE ID

            restorable_init_payload = str({
                "filter": f"IPAddress={device['ip']}",
                "pageSize": 0,
                "firstResultPos": 0
                })

            restorable_device_init = requests.post(f"{api_base_url}Exports/initExportDeviceRestoreList", headers=headers, data=restorable_init_payload, verify=False)
            # print(restorable_device_init.status_code)
            # print(restorable_device_init.text)

            restorable_list_payload = str({
                "context": 
                    json.loads(restorable_device_init.text)
                })

            restorable_device_list = requests.post(f"{api_base_url}Exports/exportDeviceRestoreList", headers=headers, data=restorable_list_payload, verify=False)
            # print(restorable_device_list.status_code)
            # print(restorable_device_list.text)

            restore_list = json.loads(restorable_device_list.text)
            # pprint(restore_list)
            for deleted_item in restore_list:
                restore_id=deleted_item['restoreId']

            data_row.update({"Restore ID #": restore_id})
            data.append(data_row)

        else:
            data_row.update({"Status": "Unchanged - Hostname Mismatch"})
            data.append(data_row)

            logger.warning(f"Hostname for {device['ip']} does not match.  The Current Entry will NOT be deleted.")
            errors.append(f"IP {device['ip']} - Hostname mismatch.")

    else:
        data_row.update({"Status": "Unchanged - Ping Response Received"})
        data.append(data_row)

        logger.warning(f"IP {device['ip']} responded to a ping.  The Current Entry will NOT be deleted")
        errors.append(f"IP {device['ip']} - Received ICMP Response.")


################################
####  CREATE DNS PUSH TASK  ####
################################

task_payload = str({
    "ip": master_dns_ip,
    "priority": True
    })

create_dns_push_task = requests.post(f"{api_base_url}TaskInvocation/dnsDDNSChangedRRs", headers=headers, data=task_payload, verify=False)
response_body = json.loads(create_dns_push_task.text)

if create_dns_push_task.status_code == 200:
    # print(f"Task Status: {create_dns_push_task.status_code}, Task ID: {response_body['result']}")
    logger.info(f"DNS Push Task Status: {create_dns_push_task.status_code}, Task ID: {response_body['result']}")
    data2.append({"DNS Update Status Code": create_dns_push_task.status_code, "DNS Update Task ID": response_body['result']})
else:
    logger.error(f"Push Task Failed.  Status Code: {create_dns_push_task.status_code}, Message: {response_body}")
    data2.append({"DNS Update Status Code": create_dns_push_task.status_code, "DNS Update Failure Message": str(response_body)})


#############################
####  CREATE SPEADSHEET  ####
#############################

timestamp = datetime.now().strftime("%m.%d.%Y-%I.%M.%S%p") # example 10.19.2020-11.59.43AM
file_name = f"IPs Removed {timestamp}"
file_path = '/mnt/c/wsl_outputs/btdiamond/'
sheet_name1 = 'IP Removal Status'
sheet_name2 = 'DNS Update Task'
sheet_names = [sheet_name1, sheet_name2]
datas = [data, data2]

new_spreadsheet = create_excel_v2(datas, file_name, file_path, sheet_names)
print(new_spreadsheet)


######################################
####  DISPLAY ERRORS IN TERMINAL  ####
######################################

if errors is not None:
    print("The following objects were not deleted:\n")
    for error in errors:
        print(error)
    print("\n")