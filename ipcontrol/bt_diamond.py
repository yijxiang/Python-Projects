import requests, json, sys
from pprint import pprint

requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False
__author__ = "AUTHOR"

base_url = "https://IPCONTROL/URL:PORT" #DEV
api_base_url = base_url+'/inc-rest/api/v1/'
login_url = "/inc-rest/api/v1/login"
un = ""
pw = ""

#################
####  LOGIN  ####
#################

headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
creds = f"username={un}&password={pw}"
r = requests.post(base_url+login_url, data=creds, verify=False)

if r.status_code == 200:
    print("\nLogin Successful!!\n")
else:
    print("Login Failure!")
    sys.exit()
token = json.loads(r.text)['access_token']
headers.update({'Authorization' : 'Bearer ' + token})
headers.update({'Content-Type' : 'application/json'})

############################
####  GET DEVICE BY IP  ####
############################

# ip = ""
# payload = {"ipAddress": ip}

# device = requests.get(f"{api_base_url}Gets/getDeviceByIPAddr", headers=headers, params=payload, verify=False)
# s = device.status_code
# r = json.loads(device.text)
# if s == 400 and r['faultDetail'] == -120:
#     print("IT WORKED!!!")
#     print(s)
#     pprint(r)
# else:
#     print("keep trying")


##################################
####  GET DEVICE BY HOSTNAME  ####
##################################

# hostname = ""
# hostname_payload = {"hostname": hostname}

# device_by_hostname = requests.get(f"{api_base_url}Gets/getDeviceByHostname", headers=headers, params=hostname_payload, verify=False)
# s2 = device_by_hostname.status_code
# r2 = json.loads(device_by_hostname.text)
# # print(s2)
# # print(r2)
# if s2 == 400 and r2['faultDetail'] == -120:
#     print("IT WORKED!!!")
#     print(s2)
#     pprint(r2)
# else:
#     print("keep trying")

#############################
####  CREATE DHCP ENTRY  ####
#############################

# ip = ""
# hostname = ""
# domain = "t"
# master_dns_ip = ""
# device_type = "Server" #Workstation, Switch, etc

# lease_payload = str({
#     'inpDevice': {
#     'addressType': 'Static',
#     'aliases': [],
#     'container': '/IPAM/CORP/DE-P000-Demo/Office',
#     'description': 'TESTING APIs',
#     'deviceType': device_type,
#     # 'domainName': 'de000.corpintra.net.',
#     # 'domainType': 'INT',
#     # 'duid': '',
#     'hostname': hostname,
#     # 'id': 245687,
#     'interfaces': [{'addressType': ['Static'],
#                 'container': ['/IPAM/CORP/DE-P000-Demo/Office'],
#                 'excludeFromDiscovery': 'false',
#                 # 'id': 245689,
#                 'ipAddress': [ip],
#                 'name': 'Default',
#                 'relayAgentCircuitId': [None],
#                 'relayAgentRemoteId': [None],
#                 'sequence': 0,
#                 'virtual': [False]}],
#     'ipAddress': ip,
#     'userDefinedFields': ['owner_id=888', 'app_id=999']
#     }})

# create_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=lease_payload, verify=False)
# if create_device.status_code == 200:
#     print(f"Lease Status: {create_device.status_code}")
# else:
#     print(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")


#############################
####  UPDATE DHCP ENTRY  ####
#############################

# hostname = ""
# hostname_payload = {"hostname": hostname}

# device_by_hostname = requests.get(f"{api_base_url}Gets/getDeviceByHostname", headers=headers, params=hostname_payload, verify=False)
# s2 = device_by_hostname.status_code
# r2 = json.loads(device_by_hostname.text)
# int_id = r2['interfaces'][0]['id']
# dev_id = r2['id']
# # print(dev_id)
# # print(int_id)
# # pprint(r2)

# master_dns_ip = ""
# device_type = "Server" #Workstation, Switch, etc

# update_payload = str({
#     'inpDevice': {
#     'addressType': 'Static',
#     'aliases': ["alias11", "alias12"],
#     'container': '/IPAM/CORP/DE-P000-Demo/Office',
#     'description': 'Update Again Testing 3',
#     'deviceType': device_type,
#     'domainName': 'de000.corpintra.net.',
#     'domainType': 'INT',
#     'hostname': hostname,
#     'id': r2['id'],
#     'interfaces': [{
#                 'addressType': ['Static'],
#                 'container': [r2['container']],
#                 'excludeFromDiscovery': 'false',
#                 'id': r2['interfaces'][0]['id'],
#                 'ipAddress': [r2["ipAddress"]],
#                 'name': 'Default',
#                 'relayAgentCircuitId': [None],
#                 'relayAgentRemoteId': [None],
#                 'sequence': 0,
#                 'virtual': [False]
#                     }],
#     'ipAddress': r2["ipAddress"],
#     'userDefinedFields': ['owner_id=80', 'app_id=90']
#     }})

# create_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=update_payload, verify=False)
# if create_device.status_code == 200:
#     r = json.loads(create_device.text)
#     addr_type = r[0]['addressType']
#     print(f"Lease Status: {create_device.status_code}")
#     print(addr_type)
#     # pprint(json.loads(create_device.text))
# elif create_device.status_code == 500:
#     print(create_device.status_code)
# else:
#     print(f"Failed - Status Code: {create_device.status_code}, Message: {create_device.text}")



############################################
####  CREATE NEXT AVAILABLE DHCP ENTRY  ####
############################################
'''
The following parameters are required: ipAddress, devicetype. 
Note the ipAddress must be specified in the main structure, 
not within the interfaces structure. 
You can also specify a hostname. 
Specify resourceRecordFlag if you want resource records to be created for the device.
Specify container if the IP address is in overlapping space. 
All other parameters are ignored.
'''

# hostname = "Next_Avail"

# next_available_payload = str({
#     "inpDevice": {
#     "hostname": hostname,
#     "deviceType": "Server",
#     "addressType": "Static",
#     "ipAddress": "192.168.2.2",
#     "resourceRecordFlag": "true",
#     }})

# create_next_available = requests.post(f"{api_base_url}IncUseNextReservedIPAddress/useNextReservedIPAddress", headers=headers, data=next_available_payload, verify=False)
# s = create_next_available.status_code
# r = json.loads(create_next_available.text)
# print(s)
# print(r)

###############################
####  CREATE DNS A RECORD  ####
###############################

# ip = ""
# hostname = ""

# a_record_payload = str({
#     "inpRR": {
#     "TTL": "",
#     "comment": "",
#     "data": ip,
#     "domain": f"{domain}.",
#     "domainType": "INT",
#     "ipAddress": ip,
#     "owner": hostname,
#     "pendingDeployment": True,
#     "resourceRecClass": "IN",
#     "resourceRecType": "A"
#     }})

# create_a_record = requests.post(f"{api_base_url}Imports/importDeviceResourceRecord", headers=headers, data=a_record_payload, verify=False)
# print(f"A Record Status: {create_a_record.status_code}")


#################################
####  CREATE DNS PTR RECORD  ####
#################################

# ip = ""
# hostname = ""
# domain = "de000.corpintra.net"
# octets = ip.split('.')

# ptr_record_payload = str({
#     "inpRR": {
#     "TTL": "",
#     "comment": "",
#     "data": f"{hostname}.{domain}.",
#     "domain": f"{octets[2]}.{octets[1]}.{octets[0]}.in-addr.arpa",
#     "domainType": "INT",
#     "ipAddress": ip,
#     "owner": octets[3],
#     "pendingDeployment": True,
#     "resourceRecClass": "IN",
#     "resourceRecType": "PTR"
#     }})

# create_a_record = requests.post(f"{api_base_url}Imports/importDeviceResourceRecord", headers=headers, data=ptr_record_payload, verify=False)
# print(f"PTR Record Status: {create_a_record.status_code}")


################################
####  CREATE DNS PUSH TASK  ####
################################

# task_payload = str({
#     "ip": master_dns_ip,
#     "priority": True
#     })

# create_dns_push_task = requests.post(f"{api_base_url}TaskInvocation/dnsDDNSChangedRRs", headers=headers, data=task_payload, verify=False)
# response_body = json.loads(create_dns_push_task.text)

# if create_dns_push_task.status_code == 200:
#     print(f"Task Status: {create_dns_push_task.status_code}, Task ID: {response_body['result']}")
# else:
#     print(f"Push Task Failed.  Status Code: {create_dns_push_task.status_code}, Message: {response_body}")


####################################################
####  CREATE MULTIPLE DHCP ENTRIES FROM A LIST  ####
####################################################

# ips = ["", ""]
# a = 5
# for ip in ips:
#     a = a+1
#     hostname = f"test_{a}"
#     payload = str({
#         'inpDevice': {
#         'addressType': 'Dynamic DHCP',
#         'aliases': [],
#         'container': '/IPAM/CORP/DE-P000-Demo/Office',
#         'description': 'TESTING APIs',
#         'deviceType': 'Access-Point',
#         # 'domainName': 'de000.corpintra.net.',
#         # 'domainType': 'INT',
#         # 'duid': '',
#         'hostname': hostname,
#         # 'id': 245687,
#         'interfaces': [{'addressType': ['Dynamic DHCP'],
#                     'container': ['/IPAM/CORP/DE-P000-Demo/Office'],
#                     'excludeFromDiscovery': 'false',
#                     # 'id': 245689,
#                     'ipAddress': [ip],
#                     'name': 'Default',
#                     'relayAgentCircuitId': [None],
#                     'relayAgentRemoteId': [None],
#                     'sequence': 0,
#                     'virtual': [False]}],
#         'ipAddress': ip
#         # 'userDefinedFields': ['owner_id=', 'app_id=']
#         }})

#     create_device = requests.post(f"{api_base_url}Imports/importDevices", headers=headers, data=payload, verify=False)
#     print(f"IP: {ip} - Status: {create_device.status_code}")


##############################
####  DETLETE DHCP ENTRY  ####
##############################

# ip = ""
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

hostname = ""
# hostname_payload = {"hostname": hostname}

# device_by_hostname = requests.get(f"{api_base_url}Gets/getDeviceByHostname", headers=headers, params=hostname_payload, verify=False)
# s2 = device_by_hostname.status_code
# r2 = json.loads(device_by_hostname.text)
# # print(s2)
# pprint(r2)

ip = ""
payload = str({"inpDev": {"ipAddress": ip}})

delete_device = requests.delete(f"{api_base_url}Deletes/deleteDevice", headers=headers, data=payload, verify=False)
print(delete_device.status_code)
pprint(json.loads(delete_device.text))

restorable_init_payload=str({
    "filter": f"IPAddress={ip}",

    "pageSize": 0,
    "firstResultPos": 0
    })

restorable_device_init = requests.post(f"{api_base_url}Exports/initExportDeviceRestoreList", headers=headers, data=restorable_init_payload, verify=False)
print(restorable_device_init.status_code)
print(restorable_device_init.text)

restorable_list_payload = str({
    "context": 
        json.loads(restorable_device_init.text)
    })

restorable_device_list = requests.post(f"{api_base_url}Exports/exportDeviceRestoreList", headers=headers, data=restorable_list_payload, verify=False)
print(restorable_device_list.status_code)
print(restorable_device_list.text)
# print(json.loads(restorable_device_list.text)[0]['restoreId'])

restore_id = json.loads(restorable_device_list.text)[0]['restoreId']

restore_payload = str({"inpDevice": {"restoreId": restore_id}})

restore_device = requests.post(f"{api_base_url}Imports/restoreDeletedDevice", headers=headers, data=restore_payload, verify=False)
print(restore_device.status_code)
print(restore_device.text)