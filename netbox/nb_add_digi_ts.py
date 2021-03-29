#v2 Create emptly log file
import logging, sys, re, pynetbox, requests, csv, socket, os, subprocess
from tqdm import tqdm
from secrets import nb_token, nb_url

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="logs/digi_creation.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger=logging.getLogger("wlc_backup")

dtna_tenant = nb.tenancy.tenants.get(slug='TENANT')
ts_role = nb.dcim.device_roles.get(slug='terminal_server')
generic_digi_type = nb.dcim.device_types.get(slug='generic-digi')

nb_ts_ips = []
nb_ts_array = []
nb_ts = nb.dcim.devices.filter(role='terminal_server')
for device in nb_ts:
    ts_name = device.name
    nb_ts_array.append(ts_name)
    try:
        ts_ip = device.primary_ip.address[:-3]
        nb_ts_ips.append(ts_ip)
    except:
        logger.info(f"Device {ts_name} doesn't have a Primary IP Address.")

with open('csv_files/digi_ts.csv', 'r') as ts_export, open(os.devnull, 'w') as DEVNULL:
    csv_reader = csv.DictReader(ts_export)
    for line in tqdm(csv_reader, desc="Create Digis"):
        digi_name = line['name'].upper()
        digi_ip = line['ip']
        digi_site_name = line['site_name']
        if line['description'] is not None:
            digi_description = line['description']
        else:
            digi_description = ""
        try:
            subprocess.check_call(
                ['ping', '-c', '1', '-w', '2', digi_ip],
                stdout=DEVNULL,  # suppress output
                stderr=DEVNULL
            )
            is_up = True
        except subprocess.CalledProcessError:
            is_up = False

        if (digi_name not in nb_ts_array and is_up == True):
            digi_site = nb.dcim.sites.get(name=digi_site_name)
            inv_dict = dict(
                name=digi_name,
                device_type=generic_digi_type.id,
                device_role=ts_role.id,
                site=digi_site.id,
                comments=digi_description,
                status='active',
                tenant=dtna_tenant.id,
                )        
            try:
                create_device = nb.dcim.devices.create(inv_dict)
                print(f"Creating Digi {digi_name} in Netbox Site {digi_site_name }")
                logger.info(f"Creating Digi {digi_name} in Netbox Site {digi_site_name}")
            except pynetbox.RequestError as e:
                print(f"---Dict Error for Digi {digi_name}\n {e}")
                logger.error(f"Dict Error for Digi {digi_name}\n {e}")
        else:
            print(f"Device {digi_name} Already Exists In Netbox or is unreachable! Pingable? {is_up}")
            logger.warning(f"Device {digi_name} Already Exists In Netbox or is unreachable! Pingable? {is_up}")
    n = 0
    for line in tqdm(csv_reader, desc="Create Digi IPs"):
        digi_name = line['name'].upper()
        digi_ip = line['ip']
        m = n+1

        try:
            subprocess.check_call(
                ['ping', '-c', '1', '-w', '2', digi_ip],  #-c is count -w is timeout
                stdout=DEVNULL,  # suppress output
                stderr=DEVNULL
            )
            is_up = True
        except subprocess.CalledProcessError:
            is_up = False

        if (digi_ip not in nb_ts_ips and is_up == True):
            try:
                nb_prefix = nb.ipam.prefixes.get(contains=digi_ip) #If error getting prefix, duplicate prefixes likely in netbox
            except:
                print(f"Item {m} - Prefix for IP {digi_ip} is not in Netbox.")
                sys.exit()
            #print(ts_ip, nb_prefix)
            prefix_str = str(nb_prefix)
            regex1 = r'(^.*)(\/.[0-9])'
            regmatch = re.match(regex1, prefix_str)
            try:
                mask = regmatch.group(2)
                ip = f"{digi_ip}"+f"{mask}"
                #print(ip)
            except:
                logger.error(f"No Prefix found for {digi_name} {digi_ip}.")
                sys.exit()
            
            digi_eth0 = nb.dcim.interfaces.get(device=digi_name, name='eth0')

            ip_dict = dict(
                address=ip,
                status='active',
                nat_outisde=0,
                tags=['ts_mgmt'],
                interface=digi_eth0.id,
                tenant=dtna_tenant.id,
                )
            try:
                create_ip = nb.ipam.ip_addresses.create(ip_dict)
                logger.info(f"Created IP Address {ip} in Netbox.")
            except:
                logger.error(f"Unable to create ip {ip}")
                print(pynetbox.RequestError)
            b = nb.dcim.devices.get(name=digi_name)
            try:
                nb_ts_ip = nb.ipam.ip_addresses.get(address=ip)
            except:
                logger.error(f"Duplicate ip {ip} exists in Netbox!")
                print(f"Duplicate ip {ip} exists in Netbox!")
            dev_dict = dict(
            primary_ip4 = nb_ts_ip.id,
            )
            try:
                b.update(dev_dict)
                logger.info(f"Set Primary IP for {digi_name} in Netbox.")
            except:
                logger.error(f"Unable to set Primary IP for {digi_name} in Netbox.")
        else:
            logger.warning(f"Primary IP {digi_ip} for device {digi_name} already exists in netbox or is unreachable. Pingable? {is_up}")