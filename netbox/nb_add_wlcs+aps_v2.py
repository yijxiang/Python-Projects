#v2 Get APs from WLC instead of CSV, Create HA WLC
import logging, netmiko, sys, time, re, pynetbox, requests, argparse, getpass, socket, os, subprocess
from secrets import nb_token, nb_url
from modules import site_code_match
from netaddr import IPAddress
from rich import print
from tqdm import tqdm

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="logs/wlc+ap_creation.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

parser=argparse.ArgumentParser(description="Create WLCs and APs in Netbox")
parser.add_argument('--wlc_ip', required=True, help="Management IP of WLC to add to NB")
args = parser.parse_args()

tenant=nb.tenancy.tenants.get(slug='tenant')
aireos_platform = nb.dcim.platforms.get(slug='aireos')
ap_role = nb.dcim.device_roles.get(slug='access-point')
wlc_role = nb.dcim.device_roles.get(slug='wlc')

wlcs_created = []
aps_created = []
nb_wlc_array = []
wlc_mgmt_ips_list = []

nb_wlcs = nb.dcim.devices.filter(role='wlc', has_primary_ip=True )

for wlc in nb_wlcs:
    wlc_serial = wlc.serial
    nb_wlc_array.append(wlc_serial)
    wlc_primary_ip = wlc.primary_ip.address[:-3]
    wlc_mgmt_ips_list.append(wlc_primary_ip)

wlc_ips = [args.wlc_ip]

wlc_un = input('Username: ')
wlc_pw = getpass.getpass()

devices = []
for ip in wlc_ips:  #Create Device Profiles for Netmiko to Connect
    cisco_wlc = {
    'device_type': 'cisco_wlc_ssh', 
    'ip': ip, 
    'username': wlc_un, 
    'password': wlc_pw,  
    }
    devices.append(cisco_wlc)

for device in devices:
    wlc_name_full = socket.gethostbyaddr(device['ip'])
    for a in wlc_name_full: #Get hostname from IP, remove .us164... via DNS Lookup
        regex1 = r'(WLC.*)\.us.*'
        regex2 = r'(wlc.*)\.us.*'
        b = str(a)
        regmatch1 = re.match(regex1, b)
        regmatch2 = re.match(regex2, b)
        if regmatch1:
            wlc_name = regmatch1.group(1)
        elif regmatch2:
            wlc_name = regmatch2.group(1).upper()
    wlc_name2 = "ap"+wlc_name[3:-3].lower() # strip first 3 and last 3 characters, make lowercase
    site_id = site_code_match(wlc_name2, nb_url, nb_token)

    logger.info(f"Connecting to {wlc_name} - {device['ip']}")
    print(f"Connecting to {wlc_name} - {device['ip']}")
    try:
        ch = netmiko.ConnectHandler(**device)    # connect to the device w/ netmiko
    except:
        logger.error(f"Failed to connect to {wlc_name} - {device['ip']}")
        logger.debug(f"Exception: {sys.exc_info()[0]}")

    prompt = ch.find_prompt()    # get the prompt as a string
    logger.debug(f"prompt: {prompt}")
    
    regex = r'^\((.*)\)[\s]>'            #matches wlc prompt for use with aireos
    regmatch = re.match(regex, prompt)
    if regmatch:                        #Use Device Prompt to Determine Hostname
        hostname = regmatch.group(1)
        logger.info(f"Working on {hostname}")
    else:
        logger.error("Hostname Not Found!")
        logger.debug(regmatch)

#### CREATE WLC IF NEEDED IN NETBOX ###

    show_udi = ch.send_command("show udi", use_textfsm=True)
    show_ap_summary = ch.send_command("show ap summary", use_textfsm=True)  # Get "show ap summary" from device in JSON
    time.sleep(1)
    show_interface_detailed_mgmt = ch.send_command("show interface detailed management", use_textfsm=True)
    wlc_sn = show_udi[0]['sn']

    if wlc_sn not in nb_wlc_array:
        wlc_model = str.lower(f"{show_udi[0]['pid']}")
        wlc_dev_type = nb.dcim.device_types.get(slug=wlc_model)
        
        # wlc_site_code = nb.dcim.sites.get(slug=site_id)
        #print(site_id)
        wlc_dict = dict(
            name = wlc_name,
            device_type = wlc_dev_type.id,
            device_role = wlc_role.id,
            platform = aireos_platform.id,
            serial = show_udi[0]['sn'],
            site = site_id,
            status = 'active',
            tenant = tenant.id,
        ) 
        try:
            create_device = nb.dcim.devices.create(wlc_dict)
            print(f"Creating Device {wlc_name} in Netbox Site {site_id}" )
            logger.info(f"Creating WLC {wlc_name} in Netbox Site {site_id}")
            wlcs_created.append(wlc_name)

        except pynetbox.RequestError as e:
            print(wlc_name, e.error)
            logger.error(wlc_name, e.error)
            continue
    else:
        print(f"Device {wlc_name} with SN {show_udi[0]['sn']} Already Exists In Netbox!")
        logger.warning(f"- Device {wlc_name} with SN {show_udi[0]['sn']} Already Exists In Netbox!")

#### SET WLC PRIMARY IP ####

    for line in show_interface_detailed_mgmt:
        cidr = IPAddress(line['ip_netmask']).netmask_bits()
        IP = (line['ip_address']) + '/' + str(cidr)
        nb_interfaces = nb.dcim.interfaces.filter(device=f"{hostname}")
        mac_address = line['mac_address']

        for interface in nb_interfaces:
            if interface.name == f"{line['name']}":
                int_dict = dict(
                address=IP,
                status='active',
                nat_outisde=0,
                tags=['wlc_mgmt'],
                interface=interface.id,
                mac_address=mac_address,
            )
                if f"{line['ip_address']}" not in wlc_mgmt_ips_list:
                    create_int = nb.ipam.ip_addresses.create(int_dict)
                    logger.info(f"Creating IP Address {line['ip_address']} in Netbox!")
                else:
                    logger.warning(f"{line['ip_address']} already exists in Netbox!")
        
        b = nb.dcim.devices.get(name=f"{hostname}")
        try:
            wlc_ip = nb.ipam.ip_addresses.get(address=IP)
        except ValueError as e: 
            print(e)
        
        dev_dict = dict(
        primary_ip4 = wlc_ip.id,
        )
        try:
            b.update(dev_dict)
            logger.info(f"Updating Primary IP For Device {hostname}.")
        except:
            logger.error(f'Unable to set primary IP for Device {hostname}.')

#### CREATE INTERFACES WITH IP ADDRESSES ON WLC IN NETBOX ###

    try:
        device_name = nb.dcim.devices.get(name=hostname)  #Use Hostname to Acquire Netbox Device 
    except:
        e = pynetbox.RequestError
        print(e.error)
    nb_wlc_int_list = []
    nb_wlc_ints = nb.dcim.interfaces.filter(device_id=device_name.id)
    for interface in nb_wlc_ints:
        nb_wlc_int_list.append(interface.name)

    wlc_ints = ch.send_command("show interface summary", use_textfsm=True)
    #print(wlc_ints)
    for item in tqdm(wlc_ints, desc=f"{hostname} Create Interfaces"):
        if item['interface_name'] not in nb_wlc_int_list:
            #print(item['interface_name'])
            pattern1 = r'redundancy-port'
            pattern2 = r'service-port'
            if re.match(pattern1, item['interface_name']):
                type_value = "1000base-t"  #1gb ethernet fixed
            elif re.match(pattern2, item['interface_name']):
                type_value = "1000base-t"  #1gb ethernet fixed
            else:
                type_value='virtual'

            int_dict = dict(
            name=f"{item['interface_name']}",
            type=type_value,  
            device=device_name.id,
            #enabled=enabled,
            #description=description,
            #mac_address=mac_address,
            #form_factor=1200   # default
            )
            nb.dcim.interfaces.create(int_dict)
            logger.info(f"Created {item['interface_name']} on {hostname}.")
        else:
            logger.warning(f"Netbox Interface for {hostname}, ID {device_name.id}, interface {item['interface_name']} already exists")

    nb_wlc_ints2 = nb.dcim.interfaces.filter(device_id=device_name.id)    
    for item in tqdm(wlc_ints, desc=f'{hostname} Create Interface IPs'):
        wlc_int_detail = ch.send_command(f"show interface detailed {item['interface_name']}", use_textfsm=True)
        if (wlc_int_detail[0]['name'] == 'redundancy-management') and (wlc_int_detail[0]['ip_address'] != '0.0.0.0'):
            nb_prefix = nb.ipam.prefixes.get(site_id=site_id, contains=wlc_int_detail[0]['ip_address']) #If error getting prefix, duplicate prefixes likely in netbox
            prefix_str = str(nb_prefix)
            regex1 = r'(^.*)(\/.[0-9])'
            regmatch = re.match(regex1, prefix_str)
            mask = regmatch.group(2)
            ip = f"{wlc_int_detail[0]['ip_address']}"+f"{mask}"
            ip_check = nb.ipam.ip_addresses.get(address=ip)
            if ip_check is None:
                for int2 in nb_wlc_ints2:
                    if item['interface_name'] == int2.name:
                        ip_dict=dict(
                        address=ip,
                        status="active",
                        nat_outside=0,
                        interface=int2.id,
                        )
                        c = nb.ipam.ip_addresses.create(ip_dict)
                        logger.info(f"Created {ip} for {int2.name} on {hostname}.")
            else:
                logger.warning(f"{ip} already exists in Netbox")

        elif wlc_int_detail[0]['ip_netmask'] is not '':
            mask = wlc_int_detail[0]['ip_netmask']
            cidr = IPAddress(mask).netmask_bits()
            ip = (wlc_int_detail[0]['ip_address']) + '/' + str(cidr)
            ip_check = nb.ipam.ip_addresses.get(address=ip)
            if ip_check is None:
        
                for int2 in nb_wlc_ints2:
                    if item['interface_name'] == int2.name:
                        ip_dict = dict(
                        address=ip,
                        status="active",
                        nat_outside=0,
                        interface=int2.id,
                        )
    
                        c = nb.ipam.ip_addresses.create(ip_dict)
                        logger.info(f"Created {ip} for {int2.name} on {hostname}.")
            else:
                logger.warning(f"{ip} already exists in Netbox")

#### ADD ACCESS POINTS TO NETBOX ####
    nb_aps = nb.dcim.devices.filter(site_id=site_id, role='access-point')
    nb_ap_sn_array = []
    nb_ap_ips_array = []
    for ap in nb_aps:
        ap_serial = ap.serial
        nb_ap_sn_array.append(ap_serial)
        ap_primary_ip = ap.primary_ip.address[:-3]
        nb_ap_ips_array.append(ap_primary_ip)
    show_ap_summary = ch.send_command(f"show ap summary", use_textfsm=True)
    nb_ap_array = []

    for ap in tqdm(show_ap_summary, desc=f"Adding APs connected to {hostname}"):
        show_ap_config = ch.send_command(f"show ap config general {ap['ap_name']}", use_textfsm=True)
        if show_ap_config[0]['serial_number'] not in nb_ap_sn_array:
            type_lwr = str.lower(f"{ap['ap_model']}")
            ap_type = nb.dcim.device_types.get(slug=type_lwr)
            site_id = site_code_match(f"{ap['ap_name']}", nb_url, nb_token)
            #print(site_id)
            inv_dict = dict(
                name = ap['ap_name'],
                device_type = ap_type.id,
                device_role = ap_role.id,
                platform = aireos_platform.id,
                serial = show_ap_config[0]['serial_number'],
                site = site_id,
                status = 'active',
                tenant = tenant.id,
            )        
            try:
                create_device = nb.dcim.devices.create(inv_dict)
                logger.info(f"Creating AP {ap['ap_name']} in Netbox Site ID {site_id}" )
                aps_created.append(ap['ap_name'])
            except pynetbox.RequestError as e:
                logger.error(ap['ap_name'], e.error)
                print(f"--- Dict Error for AP {ap['ap_name']} ---")
                print(ap['ap_name'], e.error)
                continue
        else:
            logger.warning(f"Device {ap['ap_name']} with SN {show_ap_config[0]['serial_number']} Already Exists In Netbox!")

#### ADD ACCESS POINT PRIMARY IPs IN NETBOX ####

        if f"{ap['ip']}" not in nb_ap_ips_array:
            cidr = IPAddress(show_ap_config[0]['netmask']).netmask_bits()
            IP = (ap['ip']) + '/' + str(cidr)
            nb_interfaces = nb.dcim.interfaces.filter(device=f"{ap['ap_name']}")

            for interface in nb_interfaces:
                if interface.name == "GigabitEthernet0":
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
            mac_address=f"{ap['mac']}",
            #enabled=enabled,
            )

            b = nb.dcim.interfaces.get(interface.id)
            #print(b.id)
            b.update(int_dict)
            logger.info(f"Updating Device {ap['ap_name']} with MAC {ap['mac']} and desciption Gig 0.")
            create_int=nb.ipam.ip_addresses.create(ip_dict)
            logger.info(f"Creating IP Address {IP} in Netbox!")

            b = nb.dcim.devices.get(name=f"{ap['ap_name']}")
            ap_ip = nb.ipam.ip_addresses.get(address=IP)
            
            dev_dict = dict(
            primary_ip4=ap_ip.id,
            )
    
            try:
                b.update(dev_dict)
                logger.info(f"Updating Primary IP For Device {ap['ap_name']}.")
            except:
                print('Unable to set Primary IP')
                logger.error('Unable to set Primary IP')
                continue

        else:
            logger.warning(f"{ap['ip']} already exists in Netbox!")

### ADD HA WLC TO NETBOX ###

    wlc = nb.dcim.devices.get(name=wlc_name)
    wlc_full_name = wlc.name
    wlc_name = wlc.name[:-2]
    ha_wlc_name = wlc_name+"HA"
    if wlc_full_name[-2:] == 'HA':
        print(f"{wlc_full_name} already exists in Netbox!")
        logger.warning(f"{wlc_full_name} already exists in Netbox!")
    else:
        
        wlc_primary_ip = wlc.primary_ip.address[:-3]
        mask = wlc.primary_ip.address[-3:]
        octets = wlc_primary_ip.split('.')
        octets[3] = str(int(octets[3])+3)
        separator = '.'
        ha_wlc_ip = separator.join(octets)
        # print(ha_wlc_ip)
        # print(f"Need to Create {ha_wlc_name} with ip {ha_wlc_ip} and mask {mask}")
        with open(os.devnull, 'w') as DEVNULL:
            try:
                subprocess.check_call(
                    ['ping', '-c', '1', ha_wlc_ip],
                    stdout=DEVNULL,  # suppress output
                    stderr=DEVNULL
                )
                is_up = True
            except subprocess.CalledProcessError:
                is_up = False

        if is_up == True:
            # print(hostname, 'is up!')
            cisco_wlc = {
            'device_type': 'cisco_wlc_ssh', 
            'ip': ha_wlc_ip, 
            'username': wlc_un, 
            'password': wlc_pw,  
            }

            try:
                ch = netmiko.ConnectHandler(**cisco_wlc)    # connect to the device w/ netmiko
            except:
                logger.error(f"Failed to connect to {wlc_name} - {ha_wlc_ip}")
                logger.debug(f"Exception: {sys.exc_info()[0]}")

            show_udi = ch.send_command("show udi", use_textfsm=True)
            ha_wlc_sn = show_udi[0]['sn']

            wlc_dict = dict(
            name = ha_wlc_name,
            device_type = wlc.device_type.id,
            device_role = wlc_role.id,
            platform = aireos_platform.id,
            serial = show_udi[0]['sn'],
            site = wlc.site.id,
            status = 'active',
            tenant = tenant.id,
            )        

            try:
                create_device = nb.dcim.devices.create(wlc_dict)
                print(f"Creating Device {ha_wlc_name} in Netbox Site {wlc.site.name}" )
                logger.info(f"Creating WLC {ha_wlc_name} in Netbox Site {wlc.site.name}")
                wlcs_created.append(ha_wlc_name)

            except pynetbox.RequestError as e:
                print(ha_wlc_name, e.error)
                logger.error(ha_wlc_name, e.error)
                
            
            #### SET HA WLC PRIMARY IP ####

            ip = ha_wlc_ip + mask
            nb_interfaces = nb.dcim.interfaces.filter(device=f"{ha_wlc_name}")
            # mac_address=line['mac_address']
    
            for interface in nb_interfaces:
                if interface.name == "redundancy-management":
                    int_dict = dict(
                    address=ip,
                    status='active',
                    nat_outisde=0,
                    tags=['wlc_mgmt'],
                    interface=interface.id,
                    # mac_address=mac_address,
                )
                    if f"{ha_wlc_ip}" not in wlc_mgmt_ips_list:
                        create_int = nb.ipam.ip_addresses.create(int_dict)
                        logger.info(f"Creating IP Address {ha_wlc_ip} in Netbox!")
                    else:
                        logger.warning(f"{ha_wlc_ip} already exists in Netbox!")
            
            b = nb.dcim.devices.get(name=f"{ha_wlc_name}")
            try:
                wlc_ip = nb.ipam.ip_addresses.get(address=ip)
            except ValueError as e: 
                print(e)
            
            dev_dict = dict(
            primary_ip4=wlc_ip.id,
            tenant=tenant,
            )
            try:
                b.update(dev_dict)
                logger.info(f"Updating Primary IP For Device {ha_wlc_name}.")
            except:
                logger.error(f'Unable to set primary IP for Device {ha_wlc_name}.')
    

        else:
            print(f"{ha_wlc_name} - {ha_wlc_ip} is not reachable!")
            logger.error(f"{ha_wlc_name} - {ha_wlc_ip} is not reachable!")

print("WLCs created:")
for wlc in wlcs_created:
    print(wlc)
print('\n')
print("APs created:")
for ap in aps_created:
    print(ap)
print('\n')
print("Script Complete :smiley:")
        # Connect Interfaces