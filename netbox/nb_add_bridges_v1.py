#v1 Add Wireless Bridges From CSV Files
import logging, netmiko, getpass, sys, re, pynetbox, requests, csv
from secrets import nb_token, nb_url
from modules import site_code_match
from tqdm import tqdm

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

wlc_un = input('Username: ')
wlc_pw = getpass.getpass()

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
    filename="/home/luylaki/netbox/netmiko-pynetbox/logs/bridge_creation.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

dtna_tenant = nb.tenancy.tenants.get(slug='dtna')
ios_platform = nb.dcim.platforms.get(slug='ios')
bridge_role = nb.dcim.device_roles.get(slug='bridge')

nb_bridge_array = []  # Bridge Serial Numbers
nb_bridges = nb.dcim.devices.filter(role='bridge')
for device in nb_bridges:
    bridge_name = device.name
    nb_bridge_array.append(bridge_name)

with open('wrls_bridges.csv', 'r') as bridge_export:
    csv_reader = csv.DictReader(bridge_export)
    for line in csv_reader:
        if line['ap_name'] not in nb_bridge_array:
            cisco_bridge = {
            'device_type': 'cisco_ios', 
            'ip': line['ip'], 
            'username': wlc_un, 
            'password': wlc_pw,  
            }
            logger.info(f"Connecting to {line['ap_name']} - {cisco_bridge['ip']}")
            print(f"Connecting to {line['ap_name']} - {cisco_bridge['ip']}")
            try:
                net_connect = netmiko.ConnectHandler(**cisco_bridge)    # connect to the device w/ netmiko
            except:
                logger.error(f"Failed to connect to {line['ap_name']} - {cisco_bridge['ip']}")
                logger.debug(f"Exception: {sys.exc_info()[0]}")
            
            bridge_inv = net_connect.send_command("show inventory", use_textfsm=True)
            
            type_lwr = str.lower(f"{line['type']}")
            bridge_type = nb.dcim.device_types.get(slug=type_lwr)
            scm_name = "ap"+line['ap_name'][2:].lower()
            site_id = site_code_match(scm_name, nb_url, nb_token)
            #print(site_id)
            inv_dict = dict(
                name = line['ap_name'],
                device_type = bridge_type.id,
                device_role = bridge_role.id,
                platform = ios_platform.id,
                serial = bridge_inv[0]['sn'],
                site = site_id,
                status = 'active',
                tenant = dtna_tenant.id,
            )        
            try:
                create_device = nb.dcim.devices.create(inv_dict)
                print(f"Creating Device {line['ap_name']} in Netbox Site ID {site_id}" )
                logger.info(f"Creating AP {line['ap_name']} in Netbox Site ID {site_id}")
            
            except:
                print(f"---Dict Error for AP {line['ap_name']}")
                logger.error(f"---Dict Error for AP {line['ap_name']}")
        else:
            print(f"Device {line['ap_name']} Already Exists In Netbox!")
            logger.error(f"Device {line['ap_name']} Already Exists In Netbox!")    
            continue
        
#### CREATE INTERFACES WITH IP ADDRESSES ON Bridge IN NETBOX ###

        try:
            device_name = nb.dcim.devices.get(name=line['ap_name'])  #Use Hostname to Acquire Netbox Device 
        except:
            e = pynetbox.RequestError
            print(e.error)
        nb_wlc_int_list = []
        nb_wlc_ints = nb.dcim.interfaces.filter(device_id=device_name.id)
        for interface in nb_wlc_ints:
            nb_wlc_int_list.append(interface.name)

        bridge_ints = net_connect.send_command("show interfaces", use_textfsm=True)
        for item in tqdm(bridge_ints, desc=f"{line['ap_name']} Create Interfaces"):
            if item['interface'] not in nb_wlc_int_list:
                #print(item['interface'])
                pattern1 = r'BVI1'
                pattern2 = r'Dot11Radio1.'
                pattern3 = r'Dot11Radio0.'
                pattern4 = r'GigabitEthernet0.'
                pattern5 = r'GigabitEthernet1.'
                pattern6 = r'GigabitEthernet'
                pattern8 = r'Dot11Radio0'
                pattern9 = r'Dot11Radio1'
                pattern10 = r'Virtual'

                if re.match(pattern1, item['interface']):
                    type_value = "1000base-t"  #1gb ethernet fixed
                elif re.match(pattern2, item['interface']):
                    type_value = "virtual"  
                elif re.match(pattern3, item['interface']):
                    type_value = "virtual"  
                elif re.match(pattern4, item['interface']):
                    type_value = "virtual"  
                elif re.match(pattern5, item['interface']):
                    type_value = "virtual"  
                elif re.match(pattern6, item['interface']):
                    type_value = "1000base-t"  
                elif re.match(pattern8, item['interface']):
                    type_value = "ieee802.11g"  
                elif re.match(pattern9, item['interface']):
                    type_value = "ieee802.11a"  
                elif re.match(pattern10, item['interface']):
                    type_value = "virtual"  
                else:
                    type_value = 'virtual'

                mac_address = item['address']
                if item['protocol_status']  == 'up':
                    enable_status = True
                else:
                    enable_status = False

                int_dict = dict(
                name=f"{item['interface']}",
                type=type_value,  
                device=device_name.id,
                enabled=enable_status,
                #description=description,
                mac_address=mac_address,
                #form_factor=1200   # default
                )
                nb.dcim.interfaces.create(int_dict)
                logger.info(f"Created {item['interface']} on {line['ap_name']}.")
            else:
                logger.warning(f"Netbox Interface for {line['ap_name']}, ID {device_name.id}, interface {item['interface']} already exists")

        nb_wlc_ints2 = nb.dcim.interfaces.filter(device_id=device_name.id)    
        for item in tqdm(bridge_ints, desc=f"{line['ap_name']} Create Interface IPs"):
            if item['interface'] == 'BVI1':
                ip = f"{item['ip_address']}"
                ip_check = nb.ipam.ip_addresses.get(address=ip)
                if ip_check is None:
                    for int2 in nb_wlc_ints2:
                        if item['interface'] == int2.name:
                            ip_dict=dict(
                            address=ip,
                            status="active",
                            nat_outside=0,
                            interface=int2.id,
                            tenant=dtna_tenant.id,
                            tags=['bridge_mgmt'],
                            )
                            c = nb.ipam.ip_addresses.create(ip_dict)
                            logger.info(f"Created {ip} for {int2.name} on {line['ap_name']}.")

                            try:
                                bridge_ip = nb.ipam.ip_addresses.get(address=ip)
                            except ValueError as e: 
                                print(e)

                            dev_dict = dict(
                            primary_ip4 = bridge_ip.id,
                            )
                            try:
                                bridge = nb.dcim.devices.get(name=line['ap_name'])
                                bridge.update(dev_dict)
                                logger.info(f"Updating Primary IP For Device {line['ap_name']}.")
                            except:
                                logger.error(f"Unable to set primary IP for Device {line['ap_name']}.")
                else:
                    logger.warning(f"{bridge_ip} already exists in Netbox")
