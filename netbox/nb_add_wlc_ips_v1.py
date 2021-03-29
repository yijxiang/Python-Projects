#v2 Limit length of name field
import pprint
import logging
import sys
import re 
from secrets import nb_token, nb_url
import json
import pynetbox
import requests
from netaddr import IPAddress
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
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session
devices = [] # Empty array to store devices
ips = []

nb_ips = nb.ipam.ip_addresses.all()

for x in nb_ips:   #Loop Thru IPs Removing CIDR Notation
    new_ip1 = x.address
    regex3 = r'(^.*)\/.'
    regmatch2 = re.match(regex3, new_ip1)
    if regmatch2:
        new_ip2 = regmatch2.group(1)
        ips.append(new_ip2)            #Add Scrubbed IPs to List
    else:
        print("error")

with open('wlc_export.csv', 'r') as wlc_export:
    csv_reader = csv.DictReader(wlc_export)
    for line in csv_reader:
        cidr = IPAddress(line['NETMASK']).netmask_bits()
        IP = (line['IP_Address']) + '/' + str(cidr)
        nb_interfaces = nb.dcim.interfaces.filter(device=f"{line['Device_Name']}")

        for interface in nb_interfaces:
            if interface.name == f"{line['Int_Name']}":
                int_dict = dict(
                address=IP,
                status='active',
                nat_outisde=0,
                tags=['wlc_mgmt'],
                interface=interface.id,
            )
                if f"{line['IP_Address']}" not in ips:
                    create_int = nb.ipam.ip_addresses.create(int_dict)
                    print(f"Creating IP Address {line['IP_Address']} in Netbox!")
                else:
                    print(f"{line['IP_Address']} already exists in Netbox!")
        
        b = nb.dcim.devices.get(name=f"{line['Device_Name']}")
        wlc_ip = nb.ipam.ip_addresses.get(address=IP)
        
        dev_dict = dict(
        primary_ip4=wlc_ip.id,
        )
        try:
            b.update(dev_dict)
            print(f"Updating Primary IP For Device {line['Device_Name']}.")
        except:
            print('error')
