# v2 +Create Console Cables if device exists in Netbox
# v3 +Tenant for IP Address 
# v4 +Tenant for Device, get nb_ts_ints after creating new object
import requests, json, re
import pynetbox
from tqdm import tqdm
import logging, argparse

parser=argparse.ArgumentParser(description="Lighthouse to Netbox Args")
parser.add_argument('--nb_token', required=True, help="Netbox Token")
parser.add_argument('--nb_url', required=True, help="Netbox URL")
parser.add_argument('--un', required=True, help="AD username")
parser.add_argument('--pw', required=True, help="AD password")
parser.add_argument('--lh_sessions', required=True, help="Lighthouse sessions API URL")
parser.add_argument('--lh_nodes', required=True, help="Lighthouse nodes API URL")

args = parser.parse_args()
un = args.un
pw = args.pw
nb_token = args.nb_token
nb_url = args.nb_url
lighthouse_url_sessions = args.lh_sessions
lighthouse_url_nodes = args.lh_nodes

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
    filename="terminal_servers.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

requests.packages.urllib3.disable_warnings()
session = requests.Session()
session.verify = False
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

#opengear token aquisition
data = { 'username' : un, 'password' : pw }
r = requests.post(lighthouse_url_sessions, data=json.dumps(data), verify=False)
token = json.loads(r.text)['session']

# Get nodes from lighthouse
headers = { 'Authorization' : 'Token ' + token }
nodes = requests.get(lighthouse_url_nodes, headers=headers, verify=False)
j = json.loads(nodes.text)

# Get existing terminal servers from netbox and create list of names and IPs
nb_ogs = []
nb_ts_ips = []
nb_og = nb.dcim.devices.filter(role='terminal_server')
for ts in nb_og:
    nb_ogs.append(ts.name)
    ts_str = str(ts.primary_ip)
    regex3 = r'(^.*)\/.'
    regmatch2 = re.match(regex3, ts_str)
    if regmatch2:
        new_ip2 = regmatch2.group(1)
        nb_ts_ips.append(new_ip2)

for item in tqdm(j['nodes'], desc='Terminal Servers'):
    nb_ts_ints = nb.dcim.interfaces.filter(device=item['name'])
    if item['name'] not in nb_ogs:
        for tag in item['tag_list']['tags']:
            if tag['name'] == "LOCATION":
                site_code = (tag['value'])

        ts_model_lwr = str.lower(item['model'])
        dev_type_id = nb.dcim.device_types.get(slug=ts_model_lwr)
        dev_role_id = nb.dcim.device_roles.get(slug='terminal_server')
        dev_platform_id = nb.dcim.platforms.get(slug='opengear')
        dev_site_code_id = nb.dcim.sites.get(name=site_code)

        ts_dict = dict(
        name = item['name'],
        device_type = dev_type_id.id,
        device_role = dev_role_id.id,
        platform = dev_platform_id.id,
        serial = item['serial_number'],
        site = dev_site_code_id.id,
        status = 'active',
        tenant = 1,
        )
        try:
            create_device = nb.dcim.devices.create(ts_dict)
            logger.info(f"Created Terminal Server {item['name']} in Netbox.")
            nb_ts_ints = nb.dcim.interfaces.filter(device=item['name']) # Get ints from newly created device
        except:
            logger.error(f"Tried and failed to create device {item['name']} in netbox.")
            continue
    else:
        logger.warning(f"Device {item['name']} Already Exists In Netbox!")
    
    for interface in item['interfaces']:
        if interface['name'] == "Network":
            interface_ip = interface['ipv4_addr']

    if interface_ip not in nb_ts_ips:
        ts_ip = str(interface_ip)
        nb_prefix = nb.ipam.prefixes.get(contains=ts_ip) #If error getting prefix, duplicate prefixes likely in netbox
        prefix_str = str(nb_prefix)
        regex1 = r'(^.*)(\/.[0-9])'
        regmatch = re.match(regex1, prefix_str)
        try:
            mask = regmatch.group(2)
            ip = f"{ts_ip}"+f"{mask}"
        except:
            logger.error(f"No IP or Prefix found for {item['name']}.")
    
        for interface in nb_ts_ints:
            if interface.name == "eth0":
                ip_dict = dict(
                address = ip,
                status = 'active',
                nat_outisde = 0,
                tags = ['ts_mgmt'],
                interface = interface.id,
                tenant = 1,
                )

                try:
                    create_ip = nb.ipam.ip_addresses.create(ip_dict)
                    logger.info(f"Created IP Address {ip} in Netbox.")
                except:
                    logger.error(f"Unable to create ip {ip}")
                    print(pynetbox.RequestError)

                b = nb.dcim.devices.get(name=f"{item['name']}")
                try:
                    nb_ts_ip = nb.ipam.ip_addresses.get(address=ip)
                except:
                    logger.error(f"Duplicate ip {ip} exists in Netbox!")
                    print(f"Duplicate ip {ip} exists in Netbox!")
                    
                dev_dict=dict(
                primary_ip4 = nb_ts_ip.id,
                )
                try:
                    b.update(dev_dict)
                    logger.info(f"Set Primary IP for {item['name']} in Netbox.")
                except:
                    logger.error(f"Unable to set Primary IP for {item['name']} in Netbox.")
    else:
        logger.warning(f"Primary IP {interface_ip} already exists in netbox")
    for interface in nb_ts_ints:
        if interface.name == "eth0":
            eth0 = nb.dcim.interfaces.get(interface.id)
            int_dict = dict(
            mac_address = item['mac_address'],
            )
            eth0.update(int_dict)
            logger.info(f"Updating/Adding MAC Address for {item['name']} {interface.name} {item['mac_address']}")
    nb_ts_ints2 = nb.dcim.console_server_ports.filter(device=item['name'])

    for port in tqdm(item['ports'], desc=f"{item['name']} Ports"):
        description = port['label']
        for con_port in nb_ts_ints2:
            if con_port.name == port['port_csid']:
                int2_dict = dict(
                description = description,
                )
                
                get_con_port = nb.dcim.console_server_ports.get(con_port.id)
                get_con_port.update(int2_dict)
                logger.info(f"Description {port['label']} added/updated for {item['name']} {con_port.name}.")
                ts_neighbor = nb.dcim.devices.get(name=f"{port['label']}")

                if ts_neighbor is not None:
                    ts_neighbor_name = str(ts_neighbor.name)
                    ts_neighbor_cports = nb.dcim.console_ports.filter(device=ts_neighbor_name)
                    for cport in ts_neighbor_cports:
                        if cport.name == "con0":
                            ts_neighbor_con0=nb.dcim.console_ports.get(cport.id)
                            label1 = f"{item['name']}"+"_"+f"{port['port_csid']}"+" - "+f"{ts_neighbor_name}"+"_"+"con0"
                            label2 = (label1[:98] + '..') if len(label1) > 100 else label1
                            cable_dict = dict(
                            termination_a_type = 'dcim.consoleserverport',
                            termination_a_id = con_port.id,
                            termination_b_type = 'dcim.consoleport',
                            termination_b_id = ts_neighbor_con0.id,
                            #type=optional,
                            status = 'connected',
                            label = label2, # maxLength 100 characters
                            )
                            try:
                                create_cable = nb.dcim.cables.create(cable_dict)
                                logger.info(f"Creating Cable for {item['name']} {con_port}")
                            except:
                                logger.warning(f"Console cable already exists for {item['name']} {con_port} or {ts_neighbor_name} con0")