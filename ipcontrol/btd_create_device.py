#!/usr/bin/python

'''
CREATE NEXT AVAILABLE DEVICE

SWAGGER DOCS LOCATED HERE:

https://IPCONTROL.URL:PORT/inc-rest/api/docs/index.html

'''

import requests, json, sys, logging, os, datetime
from tqdm import tqdm
from create_excel import create_excel

requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False
__author__ = "AUTHOR"

logging.basicConfig(
                    format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
                    filename="logs/create_ips_btd.log", datefmt='%m/%d/%Y - %H:%M:%S'
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

master_dns_ip = ""


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


#################
####  BEGIN  ####
#################

data = []

new_entry_details = [
    {"subnet_ip": "192.168.2.0", "hostname": "Test_120", "device_type": "Server", "owner_id_num": "777", "app_id_num": "", "description": "", "aliases": []},
    {"subnet_ip": "192.168.2.0", "hostname": "Test_119", "device_type": "Switch", "owner_id_num": "", "app_id_num": "555", "description": "This will be the description", "aliases": ["1alias"]}
    ]

for entry in tqdm(new_entry_details, desc="Creating DHCP/DNS Entries"):

    subnet_ip = entry["subnet_ip"]
    hostname = entry["hostname"]
    device_type = entry["device_type"]
    owner_id_num = entry["owner_id_num"]
    app_id_num = entry["app_id_num"]
    description = entry["description"]
    alias = entry["aliases"]

    failed_data_row = {"Status": "", "Hostname": hostname, "Description": description}

    #TRY TO GET DEVICE BY HOSTNAME TO CHECK FOR DUPLICATES

    hostname_payload = {"hostname": hostname}

    device_by_hostname = requests.get(f"{api_base_url}Gets/getDeviceByHostname", headers=headers, params=hostname_payload, verify=False)
    s = device_by_hostname.status_code
    r = json.loads(device_by_hostname.text)

    if s == 400 and r['faultDetail'] == -120:

        #IF GET FAILS, HOSTNAME IS UNIQUE, CONTINUE TO CREATE NEXT AVAILABLE

        logger.info(f"Hostname \'{hostname}\' is available.")

        next_available_payload = str({
            "inpDevice": {
            "hostname": hostname,
            "deviceType": device_type,
            "addressType": "Static",
            "ipAddress": subnet_ip,
            "resourceRecordFlag": "true",
            }})

        create_next_available = requests.post(f"{api_base_url}IncUseNextReservedIPAddress/useNextReservedIPAddress", headers=headers, data=next_available_payload, verify=False)
        s2 = create_next_available.status_code
        r2 = json.loads(create_next_available.text)

        if s2 == 200:

            #IF CREATE NEXT AVAILABLE IS SUCCESSFUL, GET NEWLY CREATED OBJECT ID SO ENTRY CAN BE UPDATED

            logger.info(f"Next Available IP Assigned Successfully.  IP: {r2['result']}")

            ip_created = r2['result']
            payload = {"ipAddress": ip_created}
            device = requests.get(f"{api_base_url}Gets/getDeviceByIPAddr", headers=headers, params=payload, verify=False)
            s3 = device.status_code
            r3 = json.loads(device.text)

            if s3 == 200:

                #UPDATE DEVICE WITH ALIAS, DESCRIPTION, OWNER ID, APP ID

                update_device_payload = str({
                    'inpDevice': {
                    'addressType': r3['addressType'],
                    'aliases': alias,
                    'container': r3['container'],
                    'description': description,
                    'deviceType': r3['deviceType'],
                    'domainName': r3['domainName'],
                    'domainType': r3['domainType'],
                    'hostname': r3['hostname'],
                    'id': r3['id'],
                    'interfaces': [{
                        'addressType': r3['interfaces'][0]['addressType'],
                        'container': [r3['container']],
                        'excludeFromDiscovery': 'false',
                        'id': r3['interfaces'][0]['id'],
                        'ipAddress': [r3["ipAddress"]],
                        'name': 'Default',
                        'relayAgentCircuitId': [None],
                        'relayAgentRemoteId': [None],
                        'sequence': 0,
                        'virtual': [False]
                        }],
                    'ipAddress': r3["ipAddress"],
                    'userDefinedFields': [f"owner_id={owner_id_num}", f"app_id={app_id_num}"]
                    }})

                update_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=update_device_payload, verify=False)

                if update_device.status_code == 200:
                    # print(json.loads(update_device.text))
                    logger.info(f"Updated Details for Device: {ip_created}")
                    r4 = json.loads(update_device.text)

                    d_ip = r4[0]['ipAddress']
                    hn = r4[0]['hostname']
                    desc = r4[0]['description']
                    al = str(r4[0]['aliases'])[1:-1]
                    udf = str(r4[0]['userDefinedFields'])[1:-1]
                    d_id = r4[0]['id']
                    dtype = r4[0]['deviceType']
                    atype = r4[0]['addressType']
                    dom = r4[0]['domainName']

                    success_data_row = {
                        "Status": "Success!", "Address": d_ip, "Hostname": hn, 
                        "Aliases": al, "Description": desc, "Device Type": dtype, 
                        "Address Type": atype, "Domain": dom, "Owner/APP": udf, "IPControl ID #": d_id
                        }
                    data.append(success_data_row)

                else:
                    # print(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")
                    logger.error(f"Failed - Status Code: {update_device.status_code}, Message: {update_device.text}")
                    failed_data_row.update({"Status": "Partial Success - Unable to Update"})
                    data.append(failed_data_row)
                    continue

        elif s2 == 400 and r2['faultDetail'] == -23:
            logger.error(f"No Reserved IPs for device type {device_type} available for host \'{hostname}\'.")
            failed_data_row.update({"Status": "Failed - No IPs Available"})
            data.append(failed_data_row)
            continue

        else:
            print(f"Some other error occured when getting Host \'{hostname}\', See logs for details")
            logger.error(f"Error - Status Code: {s2}, Message: {r2}")
            failed_data_row.update({"Status": "Failed - Unknown Error Occured"})
            data.append(failed_data_row)
            continue

    elif s == 200:
        # print(f"Device with hostname {hostname} already exists!")
        logger.warning(f"Device with hostname \'{hostname}\' already exists!")
        failed_data_row.update({"Status": "Failed - Duplicate Hostname"})
        data.append(failed_data_row)
        continue

    else:
        print(f"Some other error occured when getting Host \'{hostname}\', See logs for details")
        logger.error(f"Error creating \'{hostname}\', MESSAGE: {r}")
        failed_data_row.update({"Status": "Failed - Unknown Error Occured"})
        data.append(failed_data_row)
        continue

    
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
else:
    logger.error(f"Push Task Failed.  Status Code: {create_dns_push_task.status_code}, Message: {response_body}")


#############################
####  CREATE SPEADSHEET  ####
#############################

timestamp = datetime.datetime.now().strftime("%m.%d.%Y-%I.%M.%S%p") # File timestamp example 10.19.2020-11.59.43AM
file_name = f"IPs Created {timestamp}"
file_path = '/mnt/c/wsl_outputs/btdiamond/'
sheet_name = 'IP Creation Details'
new_spreadsheet = create_excel(data, file_name, file_path, sheet_name)
print(new_spreadsheet)


##############################
####  DETLETE DHCP ENTRY  ####
##############################

# ip = ""
# payload = str({"inpDev": {"ipAddress": ip}})

# delete_device = requests.delete(f"{api_base_url}Deletes/deleteDevice", headers=headers, data=payload, verify=False)
# pprint(json.loads(delete_device.text))