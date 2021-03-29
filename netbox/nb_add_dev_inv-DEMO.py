from pprint import pprint
import getpass
import logging
import sys
import re 
from netmiko import ConnectHandler
from secrets import nb_token, nb_url
import json
import pynetbox
import requests
from colorama import Fore, Style

try:
    import netmiko
except:
    print("Error Netmiko not installed - https://github.com/ktbyers/netmiko")
    sys.exit()
session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()

un = input('Username: ')
pw = getpass.getpass()

ips = ["192.168.9.9"]
#ips = [] # Empty array to store IPs

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO)
logger = logging.getLogger("wlc_backup")
devices = [] # Empty array to store devices

nb = pynetbox.api(url=nb_url, token=nb_token) #imported values from secrets.py

nb.http_session = session
#nb_ips = nb.ipam.ip_addresses.all() # Obtain IP List From Netbox
#
#for x in nb_ips:   #Loop Thru IPs Removing CIDR Notation
#    new_ip1 = x.address
#    regex3 = r'(^.*)\/.'
#    regmatch2 = re.match(regex3, new_ip1)
#    if regmatch2:
#        new_ip2=regmatch2.group(1)
#        ips.append(new_ip2)            #Add Scrubbed IPs to List
#    else:
#        print("error")
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
    print(f"{Fore.GREEN}- The prompt is {Fore.CYAN}{Style.BRIGHT}{prompt}{Style.RESET_ALL} ")
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

    print("{}- The 'Show Inventory' from device {}{}{}{}{} in JSON is:\n {}{}{}{}".format(Fore.GREEN, Fore.CYAN, Style.BRIGHT, hostname, Style.RESET_ALL, Fore.GREEN, Fore.CYAN, Style.BRIGHT, this_cmd, Style.RESET_ALL))
    print(f"{Fore.GREEN}- The same data displayed with Pretty Print:{Fore.CYAN}{Style.BRIGHT}")
    pprint(this_cmd)
    print(f"{Style.RESET_ALL}")
    device_name = nb.dcim.devices.get(name=hostname)  #Use Hostname to Acquire Netbox Device ID
    device_id = nb.dcim.devices.get(device_name.id)
    print(f"{Fore.GREEN}- The device ID from Netbox is: {Fore.CYAN}{Style.BRIGHT}{device_id.id}{Style.RESET_ALL}")
    nb_device_inv = (nb.dcim.inventory_items.filter(device_id=device_id.id))    #Collect Inventory List of Device in Netbox
    nb_inv = []
    for x in nb_device_inv:
        nb_inv.append(x.serial)
    print("{}- The inventory serial #s from Netbox device {}{}{}{}{} are: \n {}{}{}{}".format(Fore.GREEN, Fore.CYAN, Style.BRIGHT, hostname, Style.RESET_ALL, Fore.GREEN, Fore.CYAN, Style.BRIGHT, nb_inv, Style.RESET_ALL))
    for item in this_cmd:
        logger.info(f"Checking Inventory Item: {item['sn']}")
        inv_dict = dict(
            device = device_id.id,
            name = item['name'],
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

print(f"{Fore.GREEN}Finished Creating Netbox Inventory Items For:")
for ip in ips:
    print(f"- {Fore.CYAN}{Style.BRIGHT}{ip}")
