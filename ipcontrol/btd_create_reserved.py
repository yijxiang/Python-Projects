#!/usr/bin/python

import requests, json, sys, logging, os
from tqdm import tqdm
from getpass import getpass
requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False
__author__="AUTHOR"

logging.basicConfig(
                    format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
                    filename="logs/create_reserved_btd.log", datefmt='%m/%d/%Y - %H:%M:%S'
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


###############
#### LOGIN ####
###############

login_url = "/inc-rest/api/v1/login"

un = input('Username: ')
pw = getpass(prompt='Password: ')

headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
creds = f"username={un}&password={pw}"
r = requests.post(base_url+login_url, data=creds, verify=False)

if r.status_code == 200:
    print("\nLogin Successful!!\n")
    logger.info("Login Successful!!")
else:
    print("Login Failure!")
    logger.critical("Login Failure!")
    sys.exit()
token = json.loads(r.text)['access_token']
headers.update({'Authorization' : 'Bearer ' + token})
headers.update({'Content-Type' : 'application/json'})


#################################################
####  CREATE MULTIPLE RESERVED DHCP ENTRIES  ####
#################################################

ip = "192.168.5.5"           # USE IP 1 BELOW WHERE YOU WANT FIRST ENTRY TO BE
octets = ip.split(".")

new_entry_count = 5           # QUANTITY OF NEW ENTRIES TO MAKE
type_of_device = 'Server'     # SEE IPCONTROL FOR FULL LIST OF POSSIBLE DEVICE TYPES
logger.info(f"Attempting to create {new_entry_count} reserved {type_of_device} entries.")

pbar = tqdm(desc='Creating Reserved Entries', total=new_entry_count)

a = 0
while a < new_entry_count:

    a = a+1
    octets[3] = str(int(octets[3])+1)
    ip = ".".join(octets)

    lease_payload = str({
        'inpDevice': {
        'addressType': 'Reserved',
        'deviceType': type_of_device,
        'interfaces': [{'addressType': ['Reserved'],
                    'excludeFromDiscovery': 'false',
                    'ipAddress': [ip],
                    'name': 'Default',
                    }],
        'ipAddress': ip,
        }})

    create_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=lease_payload, verify=False)
    
    if create_device.status_code == 200:
        pbar.update(1)
        r = json.loads(create_device.text)
        # print(f"Created Reserved Entry For: {r[0]['ipAddress']}")
        logger.info(f"Created Reserved Entry For: {r[0]['ipAddress']}")
    else:
        pbar.update(1)
        # print(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")
        logger.error(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")

pbar.close()

########################################
####  CREATE SINGLE RESERVED ENTRY  ####
########################################

# ip = "192.168.5.4"

# lease_payload = str({
#     'inpDevice': {
#     'addressType': 'Reserved',
#     'deviceType': "Server",
#     'interfaces': [{'addressType': ['Reserved'],
#                 'excludeFromDiscovery': 'false',
#                 'ipAddress': [ip],
#                 'name': 'Default',
#                 }],
#     'ipAddress': ip,
#     }})

# create_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=lease_payload, verify=False)
# if create_device.status_code == 200:
#     print(f"Lease Status: {create_device.status_code}")
# else:
#     print(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")