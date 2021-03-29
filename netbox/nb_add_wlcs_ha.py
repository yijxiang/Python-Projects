# Add HA WLCS
import logging, netmiko, sys, pynetbox, requests, os, getpass, subprocess
from secrets import nb_token, nb_url
from rich import print
from tqdm import tqdm

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="logs/ha_wlc_creation.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

wlc_un = input('Username: ')
wlc_pw = getpass.getpass()

dtna_tenant = nb.tenancy.tenants.get(slug='TENANT')
aireos_platform = nb.dcim.platforms.get(slug='aireos')
wlc_role = nb.dcim.device_roles.get(slug='wlc')

wlcs_created = []
nb_wlc_array = [] #WLC SERIAL #s
wlc_mgmt_ips_list = []
wlc_names = []

nb_wlcs = nb.dcim.devices.filter(role='wlc', has_primary_ip=True)

for wlc in nb_wlcs:
    wlc_serial = wlc.serial
    nb_wlc_array.append(wlc_serial)
    wlc_primary_ip = wlc.primary_ip.address[:-3]
    wlc_mgmt_ips_list.append(wlc_primary_ip)
    wlc_name= wlc.name
    wlc_names.append(wlc_name)
    
for wlc in tqdm(nb_wlcs, desc='Creating HA WLCs'):
    wlc_full_name = wlc.name
    wlc_name = wlc.name[:-2]
    if wlc_full_name[-2:] == 'HA':
        print(f"{wlc_full_name} already exists in Netbox!")
        logger.warning(f"{wlc_full_name} already exists in Netbox!")
    else:
        ha_wlc_name = wlc_name+"HA"
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
        # print(ping_response)
        #and then check the response...
        if  is_up == True:
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
            tenant = dtna_tenant.id,
            )        

            try:
                create_device = nb.dcim.devices.create(wlc_dict)
                print(f"Creating Device {ha_wlc_name} in Netbox Site {wlc.site.name}" )
                logger.info(f"Creating WLC {ha_wlc_name} in Netbox Site {wlc.site.name}")
                wlcs_created.append(ha_wlc_name)

            except pynetbox.RequestError as e:
                print(ha_wlc_name, e.error)
                logger.error(ha_wlc_name, e.error)
                continue
            
            #### SET WLC PRIMARY IP ####


            ip = ha_wlc_ip + mask
            nb_interfaces = nb.dcim.interfaces.filter(device=f"{ha_wlc_name}")
            # mac_address = line['mac_address']
    
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
print("Script Complete :smiley:")
