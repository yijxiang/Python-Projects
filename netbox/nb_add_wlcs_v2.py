#v2 Limit length of name field
import logging
import sys
import re 
from secrets import nb_token, nb_url
import json
import pynetbox
import requests
import csv

try:
    import netmiko
except:
    print("Error Netmiko not installed - https://github.com/ktbyers/netmiko")
    sys.exit()
session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger("wlc_backup")
wlcs = [] # Empty array to store devices

nb = pynetbox.api(url=nb_url, token=nb_token)

nb.http_session = session
nb_wlc_array = []
nb_wlcs = nb.dcim.devices.filter(role='wlc')
for device in nb_wlcs:
    wlc_name=device.name
    nb_wlc_array.append(wlc_name)

with open('wlc_export.csv', 'r') as wlc_export:
    csv_reader = csv.DictReader(wlc_export)
    for line in csv_reader:

        dev_type_id = nb.dcim.device_types.get(slug=f"{line['Device_Type']}")
        dev_role_id = nb.dcim.device_roles.get(slug='wlc')
        dev_platform_id = nb.dcim.platforms.get(slug='aireos')
        dev_site_code_id = nb.dcim.sites.get(name=f"{line['Site_Code']}")

        inv_dict=dict(
            name = line['Device_Name'],
            device_type = dev_type_id.id,
            device_role = dev_role_id.id,
            platform = dev_platform_id.id,
            serial = line['Serial_Number'],
            site = dev_site_code_id.id,
            status = 'active',
        )
        if line['Device_Name'] not in nb_wlc_array:
            create_device=nb.dcim.devices.create(inv_dict)
            print(f"Creating Device {line['Device_Name']}" )
        else:
            print(f"Device {line['Device_Name']} Already Exists In Netbox!")