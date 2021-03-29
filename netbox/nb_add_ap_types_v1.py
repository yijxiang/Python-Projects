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
nb_type_array = []
nb_dev_types = nb.dcim.device_types.all()
for x in nb_dev_types:
    type_model = x.model
    nb_type_array.append(type_model)

with open('ap_types.csv', 'r') as ap_types: # ADD interface template to Device type
    csv_reader = csv.DictReader(ap_types)
    for line in csv_reader:
        type_id = nb.dcim.device_types.get(model=f"{line['types']}")
        type_dict = dict(
        device_type = type_id.id,
        name = "0",
        type = "1000base-t",
        )

        create_int_template = nb.dcim.interface_templates.create(type_dict)
        #type_lwr = str.lower(line['types'])
        #if line['types'] not in nb_type_array:
#
        #    dev_dict = dict(
        #    manufacturer = 2,
        #    model = f"{line['types']}",
        #    slug = type_lwr,
        #    display_name = f"{line['types']}",
        #    is_full_depth = False,
#
        #    )
        #
        #    create_type = nb.dcim.device_types.create(dev_dict)
        #    print(f"Creating Device Type {line['types']}")
        #else:
        #    print(f"Device Type {line['types']} Already Exists in Netbox")

#        inv_dict = dict(
#            name = line['Device_Name'],
#            device_type = dev_type_id.id,
#            device_role = dev_role_id.id,
#            platform = dev_platform_id.id,
#            serial = line['Serial_Number'],
#            site = dev_site_code_id.id,
#            status = 'active',
#        )
#        if line['Device_Name'] not in nb_wlc_array:
#            create_device = nb.dcim.devices.create(inv_dict)
#            print(f"Creating Device {line['Device_Name']}" )
#        else:
#            print(f"Device {line['Device_Name']} Already Exists In Netbox!")