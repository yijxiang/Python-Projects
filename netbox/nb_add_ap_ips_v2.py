#v2 restructured loops so IP must need to be added for anything else to occur
#v2 will not update as is unless IP needs to be created
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

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger("wlc_backup")
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session
devices = [] # Empty array to store devices
ips = []

nb_ips = nb.ipam.ip_addresses.filter(tag='ap_mgmt')

for x in nb_ips:   #Loop Thru IPs Removing CIDR Notation
    new_ip1=x.address
    regex3 = r'(^.*)\/.'
    regmatch2 = re.match(regex3, new_ip1)
    if regmatch2:
        new_ip2=regmatch2.group(1)
        ips.append(new_ip2)            #Add Scrubbed IPs to List
    else:
        print("error")

with open('ap_export.csv', 'r') as ap_export:
    csv_reader = csv.DictReader(ap_export)
    for line in csv_reader:
        if f"{line['IP_Address']}" not in ips:
            cidr = IPAddress(line['NETMASK']).netmask_bits()
            IP = (line['IP_Address']) + '/' + str(cidr)
            nb_interfaces = nb.dcim.interfaces.filter(device=f"{line['AP_Name']}")

            for interface in nb_interfaces:
                if interface.name == "0":
                    b = nb.dcim.interfaces.get(interface.id)

            ip_dict = dict(
            address=IP,
            status='active',
            nat_outisde=0,
            tags=['ap_mgmt'],
            interface=interface.id,
            )

            int_dict = dict(
            description="Gig 0",
            mac_address=f"{line['Ethernet_MAC']}",
            #enabled=enabled,
            )

            b = nb.dcim.interfaces.get(interface.id)
            #print(b.id)
            b.update(int_dict)
            print(f"Updating Device {line['AP_Name']} with MAC {line['Ethernet_MAC']} and desciption Gig 0.")
            create_int = nb.ipam.ip_addresses.create(ip_dict)
            print(f"Creating IP Address {line['IP_Address']} in Netbox!")

            b = nb.dcim.devices.get(name=f"{line['AP_Name']}")
            ap_ip = nb.ipam.ip_addresses.get(address=IP)
            
            dev_dict = dict(
            primary_ip4 = ap_ip.id,
            )
    
            try:
                b.update(dev_dict)
                print(f"Updating Primary IP For Device {line['AP_Name']}.")
            except:
                print('Unable to set Primary IP')
                continue

        else:
            print(f"{line['IP_Address']} already exists in Netbox!")