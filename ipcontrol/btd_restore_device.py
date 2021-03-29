#!/usr/bin/python

import requests, json, sys, logging, os
from tqdm import tqdm
from datetime import datetime
from create_excel_v2 import create_excel_v2
from pprint import pprint

requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False
__author__ = "Louis Uylaki"

logging.basicConfig(
                    format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
                    filename="logs/restore_ips_btd.log", datefmt='%m/%d/%Y - %H:%M:%S'
                    )
logger = logging.getLogger("bt_diamond")

try:
    os.mkdir("./logs")  # make directory relative to script location if it doesn't exist
    print("\n-- Directory ./logs was created and the log file generated now will be stored there. --\n")
except OSError as e:
    msg = e
    # print("-- Directory ./logs already exists and log file generated now will be stored there. --\n")


base_url = "https://IPCONTROL:PORT" #DEV
api_base_url = base_url+'/inc-rest/api/v1/'

master_dns_ip = "" #DEV


###############
#### LOGIN ####
###############

login_url = "/inc-rest/api/v1/login"
un = ""
pw = ""

# un = input('Username: ')
# pw = getpass(prompt='Password: ')

headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
creds = f"username={un}&password={pw}"
r = requests.post(base_url+login_url, data=creds, verify=False)

if r.status_code == 200:
    print("\nLogin Successful!!\n")
    logger.info("Login Successful!!")
else:
    print("Login Failure!")
    logger.error("Login Failure!")
    sys.exit()
token = json.loads(r.text)['access_token']
headers.update({'Authorization' : 'Bearer ' + token})
headers.update({'Content-Type' : 'application/json'})


##############################
####  DETLETE DHCP ENTRY  ####
##############################

# ip = "192.168.9.9"
# payload = str({"inpDev": {"ipAddress": ip}})

# delete_device = requests.delete(f"{api_base_url}Deletes/deleteDevice", headers=headers, data=payload, verify=False)
# pprint(json.loads(delete_device.text))


################################
#### RESTORE DELETED DEVICE ####
################################

'''
All users may filter the list based on IP Address, hostname, block name, container, address type, device type, or IP address range.

The exportDeviceRestoreList API enables you to issue a request to retrieve a list of devices that have been deleted and may be 
eligible for restoring. Before invoking the exportDeviceRestoreList operation, you must use initExportDeviceRestoreList to 
initialize the API. The response returned from the init operation becomes the input to this operation.
'''
data1 = []
# hostname = "Test_115"
# hostname_payload={"hostname": hostname}

# device_by_hostname = requests.get(f"{api_base_url}Gets/getDeviceByHostname", headers=headers, params=hostname_payload, verify=False)
# s2 = device_by_hostname.status_code
# r2 = json.loads(device_by_hostname.text)
# print(s2)
# pprint(r2)

# ip="192.168.9.12"

# delete_payload = str({"inpDev": {"ipAddress": ip}})
# delete_device = requests.delete(f"{api_base_url}Deletes/deleteDevice", headers=headers, data=delete_payload, verify=False)
# print(delete_device.status_code)
# pprint(json.loads(delete_device.text))

# restorable_init_payload = str({
#     "filter": f"IPAddress={ip}",

#     "pageSize": 0,
#     "firstResultPos": 0
#     })

# restorable_device_init = requests.post(f"{api_base_url}Exports/initExportDeviceRestoreList", headers=headers, data=restorable_init_payload, verify=False)
# print(restorable_device_init.status_code)
# print(restorable_device_init.text)

# restorable_list_payload = str({
#     "context": 
#         json.loads(restorable_device_init.text)
#     })

# restorable_device_list = requests.post(f"{api_base_url}Exports/exportDeviceRestoreList", headers=headers, data=restorable_list_payload, verify=False)
# print(restorable_device_list.status_code)
# print(restorable_device_list.text)
# print(json.loads(restorable_device_list.text)[0]['restoreId'])

# restore_list = json.loads(restorable_device_list.text)
# # pprint(restore_list)
# for deleted_item in restore_list:
#     restore_id = deleted_item['restoreId']
# print(restore_id)

# restore_id = 20590  # Created 10:52am 3/11/21  ( RESTORE SUCCESSFUL 3/15/21 )
# restore_id = 20597  # Created 10:54am 3/11/21 
restore_id = 20622

restore_payload = str({"inpDevice": {"restoreId": restore_id}})
restore_device = requests.post(f"{api_base_url}Imports/restoreDeletedDevice", headers=headers, data=restore_payload, verify=False)
# print(restore_device.status_code)
# print(restore_device.text)

if restore_device.status_code == 200:
    logger.info(f"Restore Entry Success! Restore ID: {restore_id}")
    data1.append({"Restore Entry Status": "Success!"})

elif restore_device.status_code == 400:
    b = json.loads(restore_device.text)
    restore_error = b['faultString']
    logger.error(f"Restore Entry Status: {restore_error}")
    data1.append({"Restore Entry Status": "Failed", "Error Message": restore_error})

else:
    logger.critical(f"Error: {restore_device.text}")
    data1.append({"Restore Entry Status": "Failed", "Error Message": restore_device.text})


################################
####  CREATE DNS PUSH TASK  ####
################################

data2 = []

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
file_name = f"IPs Restored {timestamp}"
file_path = '/mnt/c/wsl_outputs/btdiamond/'
sheet_name1 = 'IP Restore Status'
sheet_name2 = 'DNS Push Task'
sheet_names = [sheet_name1, sheet_name2]
datas = [data1, data2]

new_spreadsheet = create_excel_v2(datas, file_name, file_path, sheet_names)
print(new_spreadsheet)