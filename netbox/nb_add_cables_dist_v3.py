# v2 - modify logger.error and logger.info lines, pattern match for C9500-48Y
# v3 - remove verbose terminal output, use tqdm instead
import pprint
import getpass
import logging
import sys
import re 
from tqdm import tqdm
import colorama
import datetime
from netmiko import ConnectHandler
from secrets import nb_token, nb_url
from modules import int_pattern
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

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
    filename="/home/luylaki/netbox/netmiko-pynetbox/logs/cables.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

devices = []
device_ip_array = []
ips = []
nb_neighbors = []
host_list = []

ios_dist = nb.dcim.devices.filter(role='distribution', site='SITE')
#ios_dist = nb.dcim.devices.filter(name='RTRBPDCg-01')
try:
    print("Collecting Devices From Netbox. This may take a few minutes")
    #ios_sw_rtr = nb.dcim.devices.all()
    ios_sw_rtr = nb.dcim.devices.filter(role=('access', 'distribution', 'wlc', 'access-point'), site='SITE')
    print("Netbox Device Collection Complete!")
except:
    print("Failed getting devices from Netbox!")
    e = pynetbox.RequestError
    print(e.error)
    sys.exit()

for x in ios_sw_rtr:
    nb_neighbors.append(x.name)
#print(ios_sw_rtr)
for ip in ios_dist:
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
        logger.error(f"Error getting ip for device, no Primary IP is set. - value= {x}")
        print(f"Error getting ip for device, no Primary IP is set. - value= {x}")
        continue
#print(ips)

for ip in ips:                        #Create Device Profiles for Netmiko to Connect
    cisco = {
       'device_type': 'cisco_ios', 
       'ip': ip, 
       'username': un, 
       'password': pw,  
    }
    devices.append(cisco)

for device in tqdm(devices, desc='Devices', position=0):
    #filetime1 = datetime.datetime.now().strftime("%m/%d/%y-%H:%M:%S") # File timestamp                                #Loop Thru Device List
    #print(f"{filetime1} - Connecting to {device['ip']}")
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
        host_list.append(hostname)
    else:
        logger.error("Hostname Not Found!")
        logger.debug(regmatch)
    try:
        device_name = nb.dcim.devices.get(name=hostname)  #Use Hostname to Acquire Netbox Device ID
    except:
        e = pynetbox.RequestError
        print(e)
        continue
    this_cmd = net_connect.send_command("show cdp neighbor", use_textfsm=True)  # Get "show cdp neighbor" from device in JSON

    nb_interfaces = nb.dcim.interfaces.filter(device_id=device_name.id)

    a_side = []
    nb_cables = nb.dcim.cables.filter(device_id=device_name.id)
    for cable in nb_cables:
        str_term_a = str(cable.termination_a)
        a_side.append(str_term_a)

    nb_int_array = []
    for interface in nb_interfaces:
        nb_int_array.append(interface.name)
        
    for x in tqdm(this_cmd, desc=f"{hostname} Neighbors", position=1):
        neighbor_split = re.split(r'\.',f"{x['neighbor']}")
        neighbor_name = neighbor_split[0]
        #print(neighbor_name)
        if neighbor_name in nb_neighbors:
            #print(x['neighbor_interface'])
            local_int = int_pattern(f"{x['local_interface']}")
            neighbor_int = int_pattern(f"{x['neighbor_interface']}")
            #print(local_int, neighbor_int)
            
            for interface in nb_interfaces:
                if local_int == interface.name:
                    local_int_id = interface.id
                    #print(f"The Local Int Id for device {hostname} interface {local_int} is {local_int_id}")

            n_device_name = nb.dcim.devices.get(name=neighbor_name)  #Use Hostname to Acquire Netbox Device ID
            #n_device_id = nb.dcim.devices.get(n_device_name.id)
            n_nb_interfaces = nb.dcim.interfaces.filter(device_id=n_device_name.id)
            n_nb_int_array = []
            for nb_neighbor_int in n_nb_interfaces:
                n_nb_int_array.append(nb_neighbor_int.name)
                if neighbor_int == nb_neighbor_int.name:
                    neighbor_int_id = nb_neighbor_int.id
                    #print(f"The Neighbor Int Id for device {neighbor_name} interface {neighbor_int} is {neighbor_int_id}")

            if (local_int in nb_int_array and neighbor_int in n_nb_int_array):
                label1 = f"{hostname}"+"_"+f"{x['local_interface']}"+" - "+f"{neighbor_name}"+"_"+f"{x['neighbor_interface']}"
                label = (label1[:98] + '..') if len(label1) > 100 else label1
                #print(f"The label will be {label}")
                                
            else:
                logger.error(f"Interface  {hostname} - {local_int} or {neighbor_name} - {neighbor_int} not present in Netbox!")
                #print(f"Error - Interface  {hostname} - {local_int} or {neighbor_name} - {neighbor_int} not present in Netbox!")
                continue

            #print(a_side)
            if local_int not in a_side: # Attempt to make cable if termination_a doesn't exist
                #print(f"{local_int} not in a_side array. Cable does not already exist")
                cable_dict = dict(
                termination_a_type='dcim.interface',
                termination_a_id=local_int_id,
                termination_b_type='dcim.interface',
                termination_b_id=neighbor_int_id,
                #type=optional,
                status='connected',
                label=label, # maxLength 100 characters
                )
                #print(cable_dict)
                try:
                    create_cable = nb.dcim.cables.create(cable_dict)
                    logger.info(f"Created Cable {label}")
                    #print(f"Created Cable {label}")
                except:
                    logger.error(f"Tried but Unable to create cable for {hostname} port {local_int} with {neighbor_name} port {neighbor_int}")
                    #print(f"Error - Tried but Unable to create cable for {hostname} port {local_int} with {neighbor_name} port {neighbor_int}")
                    #e = pynetbox.RequestError
                    #print(e)
            else:
                logger.warning(f"Cable Connection Aleady Exists for Interface {local_int} on Device {hostname}")
                #print(f"Cable Connection Aleady Exists for Interface {local_int} on Device {hostname}")
        else:
            logger.error(f"Neighbor {neighbor_name} does not exist in nb_neighbors=[] array!")
            #print(f"Error - Neighbor {neighbor_name} does not exist in nb_neighbors=[] array!")
            continue

print("Finished Creating Netbox Cables for:")
for name in host_list:
    print(f"- {name}")
