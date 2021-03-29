#v2 Limit length of name field
#v3 revise IP collection process
import pprint
import getpass
import logging
import sys
import re 
from netmiko import ConnectHandler
from secrets import nb_token, nb_url
import json
import pynetbox
import requests
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

un = input('Username: ')
pw = getpass.getpass()

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger("wlc_backup")

devices = []
device_ip_array = []
ips = []

#filter1 = 'role=("\'access\'", "\'distribution\'")"
#ios_sw_rtr = ('access', 'distribution'))
ios_sw_rtr = nb.dcim.devices.filter(name='SW')
#print(ios_sw_rtr)
for ip in ios_sw_rtr:
    device_ip_array.append(ip.primary_ip)
#print(device_ip_array)
for x in device_ip_array:   #Loop Thru IPs Removing CIDR Notation
    x_str = str(x)
    regex3 = r'(^.*)\/.'
    regmatch2 = re.match(regex3, x_str)
    if regmatch2:
        new_ip2 = regmatch2.group(1)
        ips.append(new_ip2)            #Add Scrubbed IPs to List
    else:
        print(f"Error getting ip for device, no Primary IP is set. - value= {x}")
#print(ips)

for ip in ips:                        #Create Device Profiles for Netmiko to Connect
    cisco = {
       'device_type': 'cisco_ios', 
       'ip': ip, 
       'username': un, 
       'password': pw,  
    }
    devices.append(cisco)
#print(f"The devices are {devices}")  # Will show PW in Plain Text.
for device in devices:                                #Loop Thru Device List
    logger.info(f"Connecting to {device['ip']}")
    try:
        net_connect = netmiko.ConnectHandler(**device)    # connect to the device w/ netmiko
    except:
        logger.error(f"Failed to connect to {device['ip']}")
        logger.debug(f"Exception: {sys.exc_info()[0]}")
        continue
        
    prompt = net_connect.find_prompt()    # get the prompt as a string
    #print(f"- The prompt is {prompt}")
    logger.debug(f"prompt: {prompt}")
    
    regex = r'(^.*)#'  #regex = r'^\((.*)\)[\s]>' #matches wlc prompt for use with aireos

    regmatch = re.match(regex, prompt)
    if regmatch:                                #Use Device Prompt to Determine Hostname
        hostname = regmatch.group(1)
        logger.info(f"Working on {hostname}")
    else:
        logger.error("Hostname Not Found!")
        logger.debug(regmatch)

    this_cmd = net_connect.send_command("show inventory", use_textfsm=True)  # Get "show inventory" from device in JSON

    #print("- The 'Show Inventory' from device {} in JSON: {}".format(hostname, this_cmd))
    device_name = nb.dcim.devices.get(name=hostname)  #Use Hostname to Acquire Netbox Device ID
    #device_name = nb.dcim.devices.get(name='RTRDLPDCG-01')
    device_id = nb.dcim.devices.get(device_name.id)
    #print(f"- The device ID from Netbox is: {device_id.id}")
    nb_device_inv = (nb.dcim.inventory_items.filter(device_id=device_id.id))    #Collect Inventory List of Device in Netbox
    nb_inv = []
    for x in nb_device_inv:
        nb_inv.append(x.serial)
    #print("- The inventory serial #s from Netbox device {} are: \n {}".format(hostname, nb_inv))
    for item in this_cmd:
        logger.info(f"Checking Inventory Item: {item['sn']}")
        item_name = item['name']
        name = (item_name[:48] + '..') if len(item_name) > 48 else item_name
        inv_dict = dict(
            device = device_id.id,
            name = name,
            manufacturer = 2, # match netbox mfg id 2=Cisco
            part_id = item['pid'],
            serial = item['sn'],
            description = item['descr'],
        )
        item2 = item['sn']
        
        if item2 in nb_inv:                 #Compare Device Inventory SN To Netbox Inventory SN
            logger.info("-- Netbox Inventory Item {} Already Exists In {}!".format(item['sn'], hostname))
        else:
            logger.info("** Creating Netbox Inventory Item: {} In Device {}**".format(item['sn'], hostname))
            nb.dcim.inventory_items.create(inv_dict)      #Create Inventory Item If Not There Already

print("Finished Creating Netbox Inventory Items for:")
for ip in ips:
    print(f"- {ip}")
