#v2 Create emptly log file
import logging
import sys
import re 
from secrets import nb_token, nb_url
from modules import site_code_match
import json
import pynetbox
import requests
import csv
import datetime

try:
    import netmiko
except:
    print("Error Netmiko not installed - https://github.com/ktbyers/netmiko")
    sys.exit()
session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger("wlc_backup")

nb_tenant=nb.tenancy.tenants.get(slug='dtna')
dev_platform_id = nb.dcim.platforms.get(slug='aireos')
dev_role_id = nb.dcim.device_roles.get(slug='access-point')

nb_ap_array = []
nb_aps = nb.dcim.devices.filter(role='access-point')
for device in nb_aps:
    ap_name=device.serial
    nb_ap_array.append(ap_name)

with open('ap_export.csv', 'r') as ap_export:
    csv_reader = csv.DictReader(ap_export)
    for line in csv_reader:
        filetime1 = datetime.datetime.now().strftime("%m/%d/%y-%H:%M:%S") # File timestamp

        if line['AP_SN'] not in nb_ap_array:
            type_lwr = str.lower(f"{line['AP_Model']}")
            dev_type_id = nb.dcim.device_types.get(slug=type_lwr)
            site_id = site_code_match(f"{line['AP_Name']}")
            #print(site_id)
            inv_dict = dict(
                name = line['AP_Name'],
                device_type = dev_type_id.id,
                device_role = dev_role_id.id,
                platform = dev_platform_id.id,
                serial = line['AP_SN'],
                site = site_id,
                status = 'active',
                tenant = nb_tenant.id,
            )        
            try:
                create_device = nb.dcim.devices.create(inv_dict)
                print(f"Creating Device {line['AP_Name']} in Netbox Site ID {site_id}" )
                print(
                f"+ {filetime1} - Creating AP {line['AP_Name']} in Netbox Site ID {site_id}", file=open("/home/luylaki/netbox/netmiko-pynetbox/ap_creation.log", "a")
            )
            except:
                print(f"---Dict Error for AP {line['AP_Name']}")
                print(
                f"- {filetime1} ---Dict Error for AP {line['AP_Name']}", file=open("/home/luylaki/netbox/netmiko-pynetbox/ap_creation.log", "a")
            )
                continue
        else:
            print(f"Device {line['AP_Name']} with SN {line['AP_SN']} Already Exists In Netbox!")
            print(
            f"- {filetime1} - Device {line['AP_Name']} with SN {line['AP_SN']} Already Exists In Netbox!", file=open("/home/luylaki/netbox/netmiko-pynetbox/ap_creation.log", "a")
            )