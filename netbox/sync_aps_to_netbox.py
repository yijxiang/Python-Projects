'''
Get WLCs from Netbox, run show AP Summary on WLCs.
For each AP check if AP Name Exists, if not create the AP.
If AP already exists, validate Serial #, Device Type, MAC, & IP.
Update AP in NB if any values are different.
'''
###todo pytest
import logging, netmiko, sys, time, pynetbox, requests, argparse
from netaddr import IPAddress
from rich import print
from tqdm import tqdm
from functions import site_code_match

parser = argparse.ArgumentParser(description="Sync APs to Netbox Args")
parser.add_argument('--nb_token', required=True, help="Netbox Token")
parser.add_argument('--nb_url', required=True, help="Netbox URL")
parser.add_argument('--un', required=True, help="AD username")
parser.add_argument('--pw', required=True, help="AD password")

args = parser.parse_args()
wlc_un = args.un
wlc_pw = args.pw
nb_token = args.nb_token
nb_url = args.nb_url

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="ap_update.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("ap_update")

tenant=nb.tenancy.tenants.get(slug='TENANT_NAME')
aireos_platform = nb.dcim.platforms.get(slug='aireos')
ap_role = nb.dcim.device_roles.get(slug='access-point')
nb_wlcs = nb.dcim.devices.filter(role='wlc', has_primary_ip=True, status='active' )

wlcs_with_aps = []
aps_created = []
ap_updates = []
errors = []

for wlc in nb_wlcs:
    wlc_name = wlc.name
    
    if wlc_name[-3:] == "-01" and "GST" not in wlc_name and "MBL" not in wlc_name:
        wlcs_with_aps.append(wlc)


######################################################
#### Create Device Profile for Netmiko to Connect ####
######################################################

for wlc in tqdm(wlcs_with_aps, desc="WLCs"):
    wlc_ip = wlc.primary_ip.address[:-3]
    wlc_name = wlc.name
    cisco_wlc = {
        'device_type': 'cisco_wlc_ssh', 
        'ip': wlc_ip, 
        'username': wlc_un, 
        'password': wlc_pw,  
        }

    logger.info(f"Connecting to {wlc_name} - {wlc_ip}")

    try:
        ch = netmiko.ConnectHandler(**cisco_wlc)    # connect to the device w/ netmiko
    except:
        logger.error(f"Failed to connect to {wlc_name} - {wlc_ip}")
        logger.error(f"Skipping APs on WLC {wlc_name}. Unable to SSH.")
        logger.debug(f"Exception: {sys.exc_info()[0]}")
        continue

    logger.info(f"Working on {wlc_name}")

    show_ap_summary = ch.send_command("show ap summary", use_textfsm=True)  # Get "show ap summary" from device in JSON
    logger.info("Sending Command: \"show ap summary\"")
    time.sleep(1)


#######################################
####  ADD ACCESS POINTS TO NETBOX  ####
#######################################

    for ap in tqdm(show_ap_summary, desc=f"Adding/Updating APs connected to {wlc_name}"):
        ap_name = ap['ap_name']
        logger.info(f"Checkin if AP {ap_name} exists and if all values are correct in Netbox")
        ap_model = ap['ap_model']
        ap_mac = ap['mac'].upper()
        ap_ip = ap['ip']
        type_lwr = str.lower(f"{ap_model}")
        ap_type = nb.dcim.device_types.get(slug=type_lwr)

        show_ap_config = ch.send_command(f"show ap config general {ap_name}", use_textfsm=True)
        ap_serial = show_ap_config[0]['serial_number']
        cidr_netmask = IPAddress(show_ap_config[0]['netmask']).netmask_bits()

        get_nb_ap_count = nb.dcim.devices.count(name=ap_name)

        if get_nb_ap_count == 0: # Create if AP Name doesn't exist
            site_id = site_code_match(f"{ap_name}", nb_url, nb_token)
            if site_id == False: # Check site_code_match function response, if no match continue
                logger.error(f"Unable to find Site ID for AP \"{ap_name}\". Skipping this AP.")
                errors.append(f"Unable to find Site ID for AP \"{ap_name}\". Skipping this AP.")
                continue
            
            inv_dict = dict(
                name = ap_name,
                device_type = ap_type.id,
                device_role = ap_role.id,
                platform = aireos_platform.id,
                serial = ap_serial,
                site = site_id,
                status = 'active',
                tenant = tenant.id,
                )

            try:
                create_device = nb.dcim.devices.create(inv_dict)
                logger.warning(f"Created AP \"{ap_name}\" in Netbox Site ID# \"{site_id}\"." )
                aps_created.append(ap_name)
            except pynetbox.RequestError as e:
                logger.error(ap_name, e.error)
                print(f"--- Dict Error for AP {ap_name} ---")
                print(ap_name, e.error)
                continue

            try:
                get_new_ip = nb.ipam.ip_addresses.get(address=ap_ip) # Check if AP IP already exists in Netbox, if so skip to next AP
            except ValueError as f:
                logger.error(f"{ap_ip}: {f}")
                errors.append(f"{ap_ip}: {f}")
                continue

            if get_new_ip == None: # if True, ip does not exist in Netbox
                logger.info(f"New IP \"{ap_ip}\" is not already in Netbox.  This is good.")

            if get_new_ip != None:
                err_msg = f"IP \"{ap_ip}\" for AP \"{ap_name}\" is already in use in Netbox."
                logger.error(err_msg)
                errors.append(err_msg)
                continue

            get_mgmt_int = nb.dcim.interfaces.get(device=ap_name, name="GigabitEthernet0")
            get_mgmt_int.mac_address = ap_mac
            get_mgmt_int.description = "Gig 0"
            save_mgmt_int = get_mgmt_int.save()

            if save_mgmt_int == True:
                logger.warning(f"Added MAC \"{ap_mac}\" and description \"Gig 0\" to \"{ap_name}\" interface GigabitEthernet0.")
            else:
                logger.error(f"Unable to update Interface MAC for \"{ap_name}\". \n Save Status: {save_mgmt_int}")
                errors.append(f"Unable to update Interface MAC for \"{ap_name}\". \n Save Status: {save_mgmt_int}")
            
            IP = (ap_ip) + '/' + str(cidr_netmask)
            ip_dict = dict(
                address=IP,
                status='active',
                nat_outisde=0,
                tags=['ap_mgmt'],
                interface=get_mgmt_int.id,
                )

            try:
                create_ip = nb.ipam.ip_addresses.create(ip_dict)
                logger.warning(f"Created IP Address \"{IP}\" in Netbox!")
            except:
                err_msg = f"Failed while trying to create ip \"{IP}\" in Netbox!"
                logger.error(err_msg)
                errors.append(err_msg)

            get_created_ip = nb.ipam.ip_addresses.get(address=ap_ip)
            get_created_ap = nb.dcim.devices.get(name=ap_name)
            dev_dict = dict(primary_ip4=get_created_ip.id)

            try:
                get_created_ap.update(dev_dict) # Set Primary IP for Device.
                logger.warning(f"Updated Primary IP For Device \"{ap_name}\".")
            except:
                err_msg = f"Unable to set Primary IP \"{ap_ip}\" for \"{ap_name}\""
                logger.error(err_msg)
                errors.append(err_msg)
                continue        

        if get_nb_ap_count == 1: # Validate all values if AP exists in Netbox
            get_nb_ap = nb.dcim.devices.get(name=ap_name)
            get_nb_ap_int = nb.dcim.interfaces.get(device=ap_name, name="GigabitEthernet0")

            if get_nb_ap.primary_ip != None:
                ap_primary_ip = get_nb_ap.primary_ip.address[:-3]
            else:
                ap_primary_ip = "no_ip"

            if get_nb_ap.serial != ap_serial:
                logger.warning(f"Serial # for AP \"{ap_name}\" does not match and will be updated.")
                old_serial = get_nb_ap.serial
                get_nb_ap.serial = ap_serial
                save = get_nb_ap.save()
                if save == True:
                    msg1 = f"Serial # for AP \"{ap_name}\" was updated from \"{old_serial}\" to \"{ap_serial}\"."
                    logger.warning(msg1)
                    ap_updates.append(msg1)
                else:
                    err_msg1 = f"Unable to update Serial # for AP \"{ap_name}\"."
                    logger.warning(err_msg1)
                    errors.append(err_msg1)

            if get_nb_ap.device_type.model != ap_model:
                logger.warning(f"Device Type for AP \"{ap_name}\" does not match and will be updated.")
                old_model = get_nb_ap.device_type.model
                get_nb_ap.device_type = ap_type.id
                save = get_nb_ap.save()
                if save == True:
                    msg2 = f"Device Type for AP \"{ap_name}\" was updated from \"{old_model}\" to \"{ap_model}\"."
                    logger.warning(msg2)
                    ap_updates.append(msg2)
                else:
                    err_msg2 = f"Unable to update Device Type for AP \"{ap_name}\"."
                    logger.warning(err_msg2)
                    errors.append(err_msg2)

            if ap_primary_ip != ap_ip:
                logger.warning(f"Primary IP Address \"{ap_primary_ip}\" for AP \"{ap_name}\" in Netbox does not match current device IP \"{ap_ip}\" and will be updated.")
                
                try:
                    get_new_ip = nb.ipam.ip_addresses.get(address=ap_ip) # Check if AP IP already exists in Netbox
                except ValueError as f:
                    logger.error(get_new_ip, f)
                    errors.append(get_new_ip, f)
                    continue
                
                if get_new_ip == None: # If statement is True, ip does not exist in Netbox
                    logger.info(f"New IP {ap_ip} is NOT already in Netbox.  This is good.")
                if get_new_ip != None:
                    in_use_on_device = get_new_ip.interface.device.name
                    err_msg = f"New IP \"{ap_ip}\" for AP \"{ap_name}\" is already used in Netbox by \"{in_use_on_device}\"."
                    logger.error(err_msg)
                    errors.append(err_msg)
                    delete_new_ip_already_in_use = get_new_ip.delete()

                    if delete_new_ip_already_in_use == True:
                        msg6 = f"New IP \"{ap_ip}\" for AP \"{ap_name}\" was deleted.  It was previously assigned to \"{in_use_on_device}\"."
                        logger.warning(msg6)
                        ap_updates.append(msg6)

                old_ip = ap_primary_ip 
                if old_ip != "no_ip":
                    try:
                        get_old_ip = nb.ipam.ip_addresses.get(address=old_ip)
                    except ValueError as f:
                        logger.error(old_ip, f)
                        errors.append(old_ip, f)
                        continue
                
                    delete_old_ip = get_old_ip.delete()
                    if delete_old_ip == True:
                        msg5 = f"Old ip \"{old_ip}\" for \"{ap_name}\" has been deleted."
                        logger.warning(msg5)
                        ap_updates.append(msg5)
                    else:
                        err_msg5 = f"Unable to delete old IP \"{old_ip}\" for AP \"{ap_name}\"."
                        logger.warning(err_msg5)
                        errors.append(err_msg5)
                        continue

                IP = (ap_ip) + '/' + str(cidr_netmask)
                ip_dict = dict(
                    address=IP,
                    status='active',
                    nat_outisde=0,
                    tags=['ap_mgmt'],
                    interface=get_nb_ap_int.id,
                    )

                try:
                    create_ip = nb.ipam.ip_addresses.create(ip_dict)
                    msg3 = f"Created IP Address \"{IP}\" in Netbox!"
                    logger.warning(msg3)
                    ap_updates.append(msg3)
                except:
                    err_msg3 = f"Failed while trying to create IP \"{IP}\" in Netbox!"
                    logger.error(err_msg3)
                    errors.append(err_msg3)

                get_created_ip = nb.ipam.ip_addresses.get(address=ap_ip)
                get_created_ap = nb.dcim.devices.get(name=ap_name)
                dev_dict = dict(primary_ip4=get_created_ip.id)

                try:
                    get_created_ap.update(dev_dict)
                    msg4 = f"Updated Primary IP For Device \"{ap_name}\" from \"{old_ip}\" to \"{ap_ip}\"."
                    logger.warning(msg4)
                    ap_updates.append(msg4)
                except:
                    err_msg4 = f"Unable to set Primary IP \"{ap_ip}\" for \"{ap_name}\""
                    logger.error(err_msg4)
                    errors.append(err_msg4)

            if get_nb_ap_int.mac_address != ap_mac:
                logger.warning(f"MAC Address for AP \"{ap_name}\" does not match and will be updated.")
                old_mac = get_nb_ap_int.mac_address
                get_nb_ap_int.mac_address = ap_mac
                save = get_nb_ap_int.save()
                if save == True:
                    msg = f"Mac Address for AP \"{ap_name}\" was updated from \"{old_mac}\" to \"{ap_mac}\"."
                    logger.warning(msg)
                    ap_updates.append(msg)
                else:
                    err_msg = f"Unable to update Mac Address for AP \"{ap_name}\"."
                    logger.warning(err_msg)
                    errors.append(err_msg)
            
        if get_nb_ap_count > 1:
            err_msg = f"Duplicate APs with name \"{ap_name}\" exist in Netbox!"
            logger.error(err_msg)
            errors.append(err_msg)
            continue

print("\r")
if len(aps_created) > 0:
    print("APs Created:")
    for ap in aps_created:
        print(ap)

print("\r")
if len(ap_updates) > 0:
    print("AP Updates:")
    for ap in ap_updates:
        print(ap)

print("\r")
if len(errors) > 0:
    print("Errors:")
    for error in errors:
        print(error)

print("\nScript Complete :smiley: \n")
logger.info("Script Complete!")