"""
Sychronize FortiManger with Netbox
Created by LU 06/2021
"""
import logging, sys, pynetbox, requests
from pyFMG import fortimgr
from secrets import prd_fmg_host, prd_fmg_un, prd_fmg_pw, nb_url, nb_token
from tqdm import tqdm
from rich import print
from modules import site_code_match
from netaddr import IPAddress

# nb_url = dev_nb_url
# nb_token = dev_nb_token

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="firewall.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("firewall")

tenant = nb.tenancy.tenants.get(slug='tenant_name')
fortios_platform = nb.dcim.platforms.get(slug='fortios')
fw_role = nb.dcim.device_roles.get(slug='firewall')
# nb_firewalls = nb.dcim.devices.filter(role='firewall', has_primary_ip=True, status='active')

# LOGIN TO FORTIMANAGER
fmg_instance = fortimgr.FortiManager(prd_fmg_host, prd_fmg_un, prd_fmg_pw, debug=False, use_ssl=True, disable_request_warnings=True, timeout=100)
fmg_login = fmg_instance.login()
logger.info(f"\rFortiManager Login Status: \"{fmg_login[1]['status']['message']}\"\r")

firewalls_created = []
firewalls_deleted = []
updates = []
errors = []

get_all_firewalls = fmg_instance.get('dvmdb/device')
# get_specific_firewall = fmg_instance.get('dvmdb/device/<FWNAME>')
# pp(get_specific_firewall)

if get_all_firewalls[0] == 0:
    for fw in tqdm(get_all_firewalls[1][14:15], desc="Sync Firewalls With Netbox"): # 
        if fw['conn_status'] == 2:
            fw_con_msg = f"\"{fw['name']}\" Is Not Connected To FortiManager VM.  Skipping this FW."
            logger.info(fw_con_msg)
            continue

        fw_model = fw['platform_str']
        fw_ip = fw['ip']
        fw_desc = fw['desc']
        fw_mgmt_int = fw['mgmt_if']

        if fw['ha_slave'] != None:
            for a in fw['ha_slave']:
                if a['name'][-3:] == '-01': 
                    primary_fw_name = a['name']
                    primary_fw_sn = a['sn']
                if a['name'][-3:] == '-02':
                    ha_fw_name = a['name']
                    ha_fw_sn = a['sn']
        
        else:
            primary_fw_name = fw['name']
            primary_fw_sn = fw['sn']
            ha_fw_name = None
            ha_fw_sn = None

        logger.info(f"***  Working On \"{primary_fw_name}\"  ***")
        # print(primary_fw_name, primary_fw_sn, fw_model, fw_ip, fw_desc, ha_fw_name, ha_fw_sn)
        
        get_nb_fw = nb.dcim.devices.get(name=primary_fw_name)
        if get_nb_fw != None: # If FW Exists in Netbox
            if get_nb_fw.device_type.manufacturer.id == 1: # If FW is a checkpoint in Netbox
                delete_cp_fw = get_nb_fw.delete()
                if delete_cp_fw == True:
                    deleted_fw_msg = f"Decommissioned Checkpoint FW \"{primary_fw_name}\" Removed From Netbox"
                    logger.warning(deleted_fw_msg)
                    firewalls_deleted.append(deleted_fw_msg)

                else:
                    delete_fw_error = f"Issue Deleting Decomissioned Checkpoint FW \"{primary_fw_name}\" From Netbox. Skipping Creation Of New \"{primary_fw_name}\"!"
                    logger.error(delete_fw_error)
                    errors.append(delete_fw_error)
                    continue

            if get_nb_fw.device_type.manufacturer.id == 3: # If FW is a Fortinet in Netbox
                logger.info(f"\"{primary_fw_name}\" Is A Fortinet In Netbox.  Checking Serial # And Model.")

                if get_nb_fw.serial != primary_fw_sn: #If Serial Number Does Not Match, Update it
                    get_nb_fw.serial = primary_fw_sn
                    sn_save = get_nb_fw.save()

                    if sn_save == True:
                        sn_upate_msg = f"\"{primary_fw_name}\" Updated With SN# \"{primary_fw_sn}\"."
                        logger.warning(sn_upate_msg)
                        updates.append(sn_upate_msg)

                    else:
                        sn_save_error = f"Error Updating \"{primary_fw_name}\" With New SN# \"{primary_fw_sn}\"."
                        logger.error(sn_save_error)
                        errors.append(sn_save_error)

                else:
                    logger.info(f"\"{primary_fw_name}\" With Serial # \"{primary_fw_sn}\" Is Already Up To Date.")

                if get_nb_fw.device_type.model != fw_model:  # If Model Does Not Match, Update it
                    fw_model_lwr = str.lower(fw_model)
                    fw_dev_type = nb.dcim.device_types.get(slug=fw_model_lwr)

                    if fw_dev_type == None:
                        dev_type_msg = f"Device Type \"{fw_model}\" Not Found In Netbox! Unable To Update \"{primary_fw_name}\"!"
                        logger.error(dev_type_msg)
                        errors.append(dev_type_msg)
                        continue

                    get_nb_fw.device_type = fw_dev_type.id
                    model_save = get_nb_fw.save()

                    if model_save == True:
                        model_upate_msg = f"\"{primary_fw_name}\" Updated With Model \"{fw_model}\"."
                        logger.warning(model_upate_msg)
                        updates.append(model_upate_msg)

                    else:
                        model_save_error = f"Error Updating \"{primary_fw_name}\" Model \"{get_nb_fw.device_type.model}\" With New Model \"{fw_model}\"!"
                        logger.error(model_save_error)
                        errors.append(model_save_error)

                else:
                    logger.info(f"\"{primary_fw_name}\" Model \"{fw_model}\" Is Already Up To Date.")

        get_nb_fw2 = nb.dcim.devices.get(name=primary_fw_name)

        if get_nb_fw2 == None:
            fw_func_name = 'ap'+primary_fw_name[2:].lower()  #Modify FW name to work with site_code_match function
            site_id = site_code_match(fw_func_name, nb_url, nb_token)

            if site_id == False:
                site_id_msg = f"Site ID for \"{primary_fw_name}\" Not Found.  Unable to Create \"{primary_fw_name}\"!"
                logger.error(site_id_msg)
                errors.append(site_id_msg)
                continue

            fw_model_lwr = str.lower(fw_model)
            fw_dev_type = nb.dcim.device_types.get(slug=fw_model_lwr)

            if fw_dev_type == None:
                dev_type_msg = f"Device Type \"{fw_model}\" Not Found In Netbox! Unable To Create \"{primary_fw_name}\"!"
                logger.error(dev_type_msg)
                errors.append(dev_type_msg)
                continue

            fw_dict = dict(
                name = primary_fw_name,
                device_type = fw_dev_type.id,
                device_role = fw_role.id,
                platform = fortios_platform.id,
                serial = primary_fw_sn,
                site = site_id,
                status = 'active',
                tenant = tenant.id,
                )

            try:
                create_primary_fw = nb.dcim.devices.create(fw_dict)
                # print(f"Creating Device \"{primary_fw_name}\" in Netbox Site \"{site_id}\"" )
                logger.warning(f"Created Firewall \"{primary_fw_name}\" in Netbox Site \"{site_id}\".")
                firewalls_created.append(primary_fw_name)

            except pynetbox.RequestError as e:
                # print(primary_fw_name, e.error)
                logger.error(primary_fw_name, e)
                errors.append(f"Failed to created \"{primary_fw_name}\"!")
                continue

        get_ints = fmg_instance.get(f'/pm/config/device/{primary_fw_name}/global/system/interface')  # Get FW Ints From FMG
        get_primary_fw_nb = nb.dcim.devices.get(name=primary_fw_name)

        if get_primary_fw_nb != None: # If FW Exists in Netbox
            if get_primary_fw_nb.device_type.manufacturer.id == 3: # Verify Firewall in Fortinet in Netbox
                nb_interfaces = nb.dcim.interfaces.filter(device=primary_fw_name)  # Get FW Ints From Netbox
        
                int_list = []
                for i in nb_interfaces:
                    int_list.append(i.name)

                for a in get_ints[1]:
                    name = a['name']

                    if a['status'] == 0:
                        logger.info(f"Skipping Creation Of Disabled Interface \"{name}\" For \"{primary_fw_name}\".")

                    if a['status'] == 1 and name != 'modem' and name != 'ssl.root': # only create interfaces that are enabled and in use

                        try:
                            description = a['description']
                        except:
                            description = ""

                        try:
                            ip = a['ip']
                        except:
                            ip = "No IP"

                        status = a['status']
                        if status == 0: # 0 = Disabled in FMG
                            status = False
                        elif status == 1: # 1 = Enabled in FMG
                            status = True

                        type = a['type']
                        if type == 0 and (name == 'x1' or name == 'x2'): # 0 = Physical in FMG
                            type = '10gbase-x-sfpp'
                        elif type == 0:
                            type = '1000base-x-sfp'
                        elif type == 1: # 1 = VLAN in FMG
                            type = 'virtual'
                        elif type == 2: # 2 = Aggregate in FMG
                            type = 'lag'
                        elif type == 4: # 4 = Tunnel in FMG 
                            type = 'virtual'
                        elif type == 9: # 9 = Hardware Switch in FMG
                            type = 'virtual'
                        else:
                            type = 'virtual'

                        if ip != "No IP":
                            ip_address = ip[0]
                            sn_mask = ip[1]

                        else:
                            ip_address = '0.0.0.0'
                            sn_mask = '0.0.0.0'
                        # print(f"{a['name']}, {description}, {ip_address}, {sn_mask}, {status}, {type} ")

                        if name not in int_list:
                            logger.info(f"Interface \"{name}\" Not In Netbox For Device \"{primary_fw_name}\".")
                            int_dict=dict(
                                name=name,
                                type=type,  
                                device=get_primary_fw_nb.id,
                                enabled=status,
                                description=description,
                                #mac_address=mac_address
                                )

                            try:
                                create_interface = nb.dcim.interfaces.create(int_dict)
                                create_interface_msg = f"Interface \"{name}\" Created In Netbox For Device \"{primary_fw_name}\"."
                                logger.warning(create_interface_msg)
                                updates.append(create_interface_msg)

                            except:
                                create_interface_error = f"Error Creating Interface \"{name}\" On \"{primary_fw_name}\"!"
                                logger.error(create_interface_error)
                                errors.append(create_interface_error)

                        if name in int_list and ip_address != "0.0.0.0": # Interface exists in Netbox and FMG Interface IP is not 0.0.0.0
                            get_nb_int = nb.dcim.interfaces.get(name=name, device=primary_fw_name)

                            try:
                                get_new_int_ip = nb.ipam.ip_addresses.get(address=ip_address)

                            except ValueError as ve:
                                logger.error(f"\"{ip_address}\", {ve}")
                                errors.append(f"\"{ip_address}\", {ve}")
                                continue
                            
                            if get_new_int_ip == None:
                                get_int_ip_id = None
                            else:
                                get_int_ip_id = get_new_int_ip.interface.id
                            
                            if get_int_ip_id == get_nb_int.id:
                                logger.info(f"IP \"{ip_address}\" Is Correct For Interface \"{name}\" On \"{primary_fw_name}\".")
                            
                            else:
                                if get_new_int_ip != None:

                                    delete_int_ip = get_new_int_ip.delete()

                                    if delete_int_ip == True:
                                        delete_int_ip_msg = f"Old IP For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                        logger.warning(delete_int_ip_msg)
                                        updates.append(delete_int_ip_msg)

                                    else:
                                        delete_int_ip_error = f"Failed To Delete Old IP For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                        logger.error(delete_int_ip_error)
                                        errors.append(delete_int_ip_error)
                                        continue

                                if get_new_int_ip == None:    
                                    get_current_int_ip = nb.ipam.ip_addresses.get(interface=name, device=primary_fw_name)

                                    if get_current_int_ip == None:
                                        old_ip = '0.0.0.0'

                                    else:
                                        old_ip = get_current_int_ip.address
                                        delete_current_int_ip = get_current_int_ip.delete()

                                        if delete_current_int_ip == True:
                                            delete_current_int_ip_msg = f"Old IP \"{old_ip}\"For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                            logger.warning(delete_current_int_ip_msg)
                                            updates.append(delete_current_int_ip_msg)

                                        else:
                                            delete_current_int_ip_error = f"Failed To Delete Old IP For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                            logger.error(delete_current_int_ip_error)
                                            errors.append(delete_current_int_ip_error)
                                            continue

                                int_cidr = IPAddress(sn_mask).netmask_bits()
                                int_cidr_ip = (ip_address) + '/' + str(int_cidr)

                                int_ip_dict=dict(address=int_cidr_ip,
                                    status='active',
                                    nat_outisde=0,
                                    interface=get_nb_int.id
                                    )

                                try:
                                    create_new_int_ip = nb.ipam.ip_addresses.create(int_ip_dict)
                                    create_new_int_ip_msg = f"Created IP \"{int_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"."
                                    logger.warning(create_new_int_ip_msg)
                                    updates.append(create_new_int_ip_msg)

                                except:
                                    create_new_int_ip_error = f"Failed To Create IP \"{fw_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"!"
                                    logger.error(create_new_int_ip_error)
                                    errors.append(create_new_int_ip_error)

                        if name in int_list: # check each if interface description in Netbox matches FMG
                            get_int2 = nb.dcim.interfaces.get(name=name, device=primary_fw_name)
                            nb_int_description = get_int2.description

                            if description != nb_int_description:
                                get_int2.description = description
                                save_int_description = get_int2.save()

                                if save_int_description == True:
                                    save_int_description_msg = f"Interface Descritpion For \"{name}\" Changed From \"{nb_int_description}\" To \"{description}\" On \"{primary_fw_name}\"."
                                    logger.warning(save_int_description_msg)
                                    updates.append(save_int_description_msg)

                                else:
                                    save_int_description_error = f"Failed To Save Updated Description For Interface \"{name}\" On \"{primary_fw_name}\"!"
                                    logger.error(save_int_description_error)
                                    errors.append(save_int_description_error)
                                    continue

                            else:
                                logger.info(f"Description \"{description}\" For Interface \"{name}\" Is Already Correct On \"{primary_fw_name}\".")

                        try:
                            get_int_ip2 = nb.ipam.ip_addresses.get(interface=name, device=primary_fw_name)
                        except:
                            get_int_ip2 = 'mgmt_interface'

                        if name in int_list and ip_address == '0.0.0.0' and get_int_ip2 != None and name != fw_mgmt_int: # if interface exists in netbox and the FMG IP is not set but IP is set in Netbox
                            old_ip2 = get_int_ip2.address
                            delete_int_ip2 = get_int_ip2.delete()

                            if delete_int_ip2 == True:
                                delete_int_ip2_msg = f"Old IP \"{old_ip2}\" For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                logger.warning(delete_int_ip2_msg)
                                updates.append(delete_int_ip2_msg)

                            else:
                                delete_int_ip2_error = f"Failed To Delete Old IP For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Deleted."
                                logger.error(delete_int_ip2_error)
                                errors.append(delete_int_ip2_error)
                                continue

                        if ip_address != '0.0.0.0':
                            nb_interface = nb.dcim.interfaces.get(name=name, device=primary_fw_name)
                            cidr = IPAddress(sn_mask).netmask_bits()
                            fw_cidr_ip = (ip_address) + '/' + str(cidr)

                            try:
                                get_ip = nb.ipam.ip_addresses.get(address=ip_address)

                            except ValueError as ve:
                                logger.error(f"\"{ip_address}\", {ve}")
                                errors.append(f"\"{ip_address}\", {ve}")

                            if get_ip == None:
                                
                                ip_dict = dict(
                                    address=fw_cidr_ip,
                                    status='active',
                                    nat_outisde=0,
                                    interface=nb_interface.id
                                    )

                                try:
                                    create_nb_ip = nb.ipam.ip_addresses.create(ip_dict)
                                    create_nb_ip_msg = f"Created IP \"{fw_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"."
                                    logger.warning(create_nb_ip_msg)
                                    updates.append(create_nb_ip_msg)

                                except:
                                    create_nb_ip_error = f"Failed To Create IP \"{fw_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"!"
                                    logger.error(create_nb_ip_error)
                                    errors.append(create_nb_ip_error)

                            if fw_ip == ip_address: # check if IP is the VRRP or if it is Primary Management for non-redundant firewalls
                                get_vrrp_ip = nb.ipam.ip_addresses.get(address=fw_ip)

                                if get_vrrp_ip.role == None and fw['ha_slave'] != None:
                                    get_vrrp_ip.role = 41 # Static value for Netbox role id could be change to variable
                                    save_vrrp_ip = get_vrrp_ip.save()

                                    if save_vrrp_ip == True:
                                        save_vrrp_ip_msg = f"IP \"{fw_ip}\" For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Set As The VRRP Address."
                                        logger.warning(save_vrrp_ip_msg)
                                        updates.append(save_vrrp_ip_msg)
                                        get_vrrp_ip = nb.ipam.ip_addresses.get(address=fw_ip)

                                    else:
                                        save_vrrp_ip_error = f"Failed To Set IP \"{fw_ip}\" For Interface \"{name}\" On \"{primary_fw_name}\" As The VRRP Address"
                                        logger.error(save_vrrp_ip_error)
                                        errors.append(save_vrrp_ip_error)
                                        continue

                                try:
                                    vrrp_role_id = get_vrrp_ip.role.id
                                except:
                                    vrrp_role_id = None

                                if vrrp_role_id != 41 and fw['ha_slave'] != None:
                                    get_vrrp_ip.role = 41 # 41 is Static value for Netbox ip role id of VRRP
                                    save_vrrp_ip2 = get_vrrp_ip.save()

                                    if save_vrrp_ip2 == True:
                                        save_vrrp_ip_msg2 = f"IP \"{fw_ip}\" For Interface \"{name}\" On \"{primary_fw_name}\" Has Been Set As The VRRP Address."
                                        logger.warning(save_vrrp_ip_msg2)
                                        updates.append(save_vrrp_ip_msg2)

                                    else:
                                        save_vrrp_ip_error2 = f"Failed To Set IP \"{fw_ip}\" For Interface \"{name}\" On \"{primary_fw_name}\" As The VRRP Address"
                                        logger.error(save_vrrp_ip_error2)
                                        errors.append(save_vrrp_ip_error2)
                                        continue

                                else:
                                    logger.info(f"IP \"{fw_ip}\" Is Already Set To Role VRRP For Device \"{primary_fw_name}\".")

                                if fw['ha_slave'] != None:  # If FW IS redundant
                                    fw_mgmt_ip = a['management-ip'][0] # does not change when fw fails over on FMG 6.4.5
                                    fw_mgmt_mask = a['management-ip'][1]
                                    fw_mgmt_cidr = IPAddress(fw_mgmt_mask).netmask_bits()
                                    fw_mgmt_cidr_ip = (fw_mgmt_ip) + '/' + str(fw_mgmt_cidr)

                                    try:
                                        get_fw_mgmt_ip = nb.ipam.ip_addresses.get(address=fw_mgmt_ip)

                                    except ValueError as ve:
                                        logger.error(f"\"{fw_mgmt_ip}\", {ve}")
                                        errors.append(f"\"{fw_mgmt_ip}\", {ve}")

                                    if get_fw_mgmt_ip == None: # If IP does not exist in Netbox
                                        
                                        ip_dict = dict(
                                            address=fw_mgmt_cidr_ip,
                                            status='active',
                                            nat_outisde=0,
                                            interface=nb_interface.id
                                            )

                                        try:
                                            create_nb_fw_mgmt_ip = nb.ipam.ip_addresses.create(ip_dict)
                                            create_nb_fw_mgmt_ip_msg = f"Created IP \"{fw_mgmt_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"."
                                            logger.warning(create_nb_fw_mgmt_ip_msg)
                                            updates.append(create_nb_fw_mgmt_ip_msg)

                                        except:
                                            create_nb_fw_mgmt_ip_error = f"Failed To Create IP \"{fw_mgmt_cidr_ip}\" On Interface \"{name}\" For Device \"{primary_fw_name}\"!"
                                            logger.error(create_nb_fw_mgmt_ip_error)
                                            errors.append(create_nb_fw_mgmt_ip_error)

                                    logger.info(f"\"{fw_mgmt_ip}\" On Interface \"{name}\" Is The Primary IP For \"{primary_fw_name}\".")
                                    mask = fw_cidr_ip[-3:]
                                    octets = fw_ip.split('.')
                                    octets[3] = str(int(octets[3])+2)
                                    ha_fw_primary_ip = '.'.join(octets) # Create HA IP from VRRP IP
                                    ha_fw_cidr_ip = ha_fw_primary_ip+mask
                                    ha_fw_mgmt_int = name
                                    ha_int_type = type

                                    try:
                                        fw_primary_ip_addr = get_primary_fw_nb.primary_ip.address
                                    except:
                                        fw_primary_ip_addr = None

                                    if fw_primary_ip_addr != fw_mgmt_cidr_ip:  # If Current Primary IP Does Not Match FMG Primary IP

                                        primary_ip = nb.ipam.ip_addresses.get(address=fw_mgmt_ip)
                                        primary_ip_dict = dict(primary_ip4=primary_ip.id)

                                        try:
                                            update_ip = get_primary_fw_nb.update(primary_ip_dict)
                                            
                                        except pynetbox.RequestError as e:
                                            update_ip_error = f"Failed To Update Primary IP \"{fw_mgmt_ip}\" For \"{primary_fw_name}\"!\n \"{e}\"!"
                                            logger.error(update_ip_error)
                                            errors.append(update_ip_error)
                                            continue

                                        if update_ip == True:
                                            update_ip_msg = f"Primary IP For \"{primary_fw_name}\" Has Been Set To \"{fw_mgmt_ip}\"."
                                            logger.warning(update_ip_msg)
                                            updates.append(update_ip_msg)

                                        else:
                                            update_ip_error2 = f"Failed To Update Primary IP \"{fw_mgmt_ip}\" For \"{primary_fw_name}\"!"
                                            logger.error(update_ip_error2)
                                            errors.append(update_ip_error2)

                                    else:
                                        logger.info(f"Primary IP \"{fw_mgmt_ip}\" Is Already Correct For \"{primary_fw_name}\".")

                                if fw['ha_slave'] == None: # If firewall is not redundant set primary IP

                                    try:
                                        fw_primary_ip_addr = get_primary_fw_nb.primary_ip.address
                                    except:
                                        fw_primary_ip_addr = None

                                    if fw_primary_ip_addr != fw_cidr_ip:  # If Current Primary IP Does Not Match FMG Primary IP

                                        primary_ip = nb.ipam.ip_addresses.get(address=fw_ip)
                                        primary_ip_dict = dict(primary_ip4=primary_ip.id)

                                        try:
                                            update_ip = get_primary_fw_nb.update(primary_ip_dict)
                                            
                                        except pynetbox.RequestError as e:
                                            update_ip_error = f"Failed To Update Primary IP \"{fw_ip}\" For \"{primary_fw_name}\"!\n \"{e}\"!"
                                            logger.error(update_ip_error)
                                            errors.append(update_ip_error)
                                            continue

                                        if update_ip == True:
                                            update_ip_msg = f"Primary IP Has Been Set To \"{fw_ip}\" For \"{primary_fw_name}\"."
                                            logger.warning(update_ip_msg)
                                            updates.append(update_ip_msg)

                                        else:
                                            update_ip_error2 = f"Failed To Update Primary IP \"{fw_mgmt_ip}\" For \"{primary_fw_name}\"!"
                                            logger.error(update_ip_error2)
                                            errors.append(update_ip_error2)

                                    else:
                                        logger.info(f"Primary IP \"{fw_ip}\" Is Already Correct For \"{primary_fw_name}\".")

                for b in get_ints[1]:  # If Interface Is Bond, Add Members after all enabled interfaces are created
                    name = b['name']
                    if name == 'bond0' or name == 'bond1':
                        get_bond = nb.dcim.interfaces.get(name=name, device=primary_fw_name)
                        for member in b['member']:
                            get_member = nb.dcim.interfaces.get(name=member, device=primary_fw_name)

                            try: 
                                member_lag_id = get_member.lag.id
                            except:
                                member_lag_id = None

                            if get_member.lag == None or member_lag_id != get_bond.id:

                                get_member.lag = get_bond.id
                                save = get_member.save()

                                if save == True:
                                    lag_save_msg = f"Added \"{member}\" To LAG \"{name}\" On \"{primary_fw_name}\"."
                                    logger.warning(lag_save_msg)
                                    updates.append(lag_save_msg)

                                else:
                                    lag_save_error = f"Error Adding \"{member}\" To LAG \"{name}\" On \"{primary_fw_name}\"!"
                                    logger.error(lag_save_error)
                                    errors.append(lag_save_error)

                            else:
                                lag_msg = f"Port \"{member}\" Is Already Part Of The Correct LAG \"{name}\" On \"{primary_fw_name}\"."
                                logger.info(lag_msg)

######################
####  HA FIREWALL ####
######################

        if ha_fw_name != None:
            get_nb_ha_fw = nb.dcim.devices.get(name=ha_fw_name)
            if get_nb_ha_fw != None: # If FW Exists in Netbox
                if get_nb_ha_fw.device_type.manufacturer.id == 1: # If FW is a checkpoint in Netbox
                    delete_cp_ha_fw = get_nb_ha_fw.delete()

                    if delete_cp_ha_fw == True:
                        deleted_ha_fw_msg = f"Decommissioned Checkpoint FW \"{ha_fw_name}\" Removed From Netbox"
                        logger.warning(deleted_ha_fw_msg)
                        firewalls_deleted.append(ha_fw_name)

                    else:
                        delete_ha_fw_error = f"Issue Deleting Decomissioned Checkpoint FW \"{ha_fw_name}\" From Netbox. Skipping Creation Of New \"{ha_fw_name}\"!"
                        logger.error(delete_ha_fw_error)
                        errors.append(delete_ha_fw_error)
                        continue

                if get_nb_ha_fw.device_type.manufacturer.id == 3: # If FW is a Fortinet in Netbox
                    logger.info(f"\"{ha_fw_name}\" Is A Fortinet In Netbox.  Checking Serial # And Model.")

                    if get_nb_ha_fw.serial != ha_fw_sn: #If Serial Number Does Not Match, Update it
                        get_nb_ha_fw.serial = ha_fw_sn
                        ha_sn_save = get_nb_ha_fw.save()

                        if ha_sn_save == True:
                            ha_sn_upate_msg = f"\"{ha_fw_name}\" Updated With SN# \"{ha_fw_sn}\"."
                            logger.warning(ha_sn_upate_msg)
                            updates.append(ha_sn_upate_msg)

                        else:
                            ha_sn_save_error = f"Error Updating \"{ha_fw_name}\" With New SN# \"{ha_fw_sn}\"!"
                            logger.error(ha_sn_save_error)
                            errors.append(ha_sn_save_error)

                    else:
                        logger.info(f"\"{ha_fw_name}\" Serial # \"{ha_fw_sn}\" Is Already Up To Date.")

                    if get_nb_ha_fw.device_type.model != fw_model:  # If Model Does Not Match, Update it
                        ha_fw_model_lwr = str.lower(fw_model)
                        ha_fw_dev_type = nb.dcim.device_types.get(slug=fw_model_lwr)

                        if ha_fw_dev_type == None:
                            ha_dev_type_msg = f"Device Type \"{fw_model}\" Not Found In Netbox! Unable To Update \"{ha_fw_name}\"!"
                            logger.error(ha_dev_type_msg)
                            errors.append(ha_dev_type_msg)
                            continue

                        get_nb_ha_fw.device_type = ha_fw_dev_type.id
                        ha_model_save = get_nb_ha_fw.save()

                        if ha_model_save == True:
                            ha_model_upate_msg = f"\"{ha_fw_name}\" Updated With Model \"{fw_model}\"."
                            logger.warning(ha_model_upate_msg)
                            updates.append(ha_model_upate_msg)
                            
                        else:
                            ha_model_save_error = f"Error Updating \"{ha_fw_name}\" Model \"{get_nb_ha_fw.device_type.model}\" With New Model \"{fw_model}\"."
                            logger.error(ha_model_save_error)
                            errors.append(ha_model_save_error)

                    else:
                        logger.info(f"\"{ha_fw_name}\" Model \"{fw_model}\" Is Already Up To Date.")

                    try:
                        ha_fw_primary_nb_ip = get_nb_ha_fw.primary_ip.address
                    except:
                        ha_fw_primary_nb_ip = None

                    if ha_fw_primary_nb_ip != ha_fw_cidr_ip:

                        try:
                            get_ha_ip = nb.ipam.ip_addresses.get(address=ha_fw_primary_ip)
                            # print(get_ip)
                        except ValueError as ve:
                            logger.error(f"\"{ip_address}\", {ve}")
                            errors.append(f"\"{ip_address}\", {ve}")
                            continue

                        if get_ha_ip == None:
                            logger.info(f"Primary IP \"{ip_address}\" Not In Netbox.")
                            ha_nb_interface = nb.dcim.interfaces.get(name=ha_fw_mgmt_int, device=ha_fw_name)

                            if ha_nb_interface == None:
                                logger.info(f"Mgmt Interface \"{ha_fw_mgmt_int}\" Missing From \"{ha_fw_name}\".")
                                ha_mgmt_int_dict=dict(
                                    name=ha_fw_mgmt_int,
                                    type=ha_int_type,
                                    device=get_nb_ha_fw.id,
                                    enabled=True,
                                    description="Management Interface"
                                    )

                                try:
                                    ha_create_interface = nb.dcim.interfaces.create(ha_mgmt_int_dict)
                                    ha_create_interface_msg = f"Created Interface \"{ha_fw_mgmt_int}\" On \"{ha_fw_name}\"."
                                    logger.warning(ha_create_interface_msg)
                                    updates.append(ha_create_interface_msg)
                                    ha_nb_interface = nb.dcim.interfaces.get(name=ha_fw_mgmt_int, device=ha_fw_name)
                                except:
                                    ha_create_interface_error = f"Error Creating Interface \"{ha_fw_mgmt_int}\" On \"{ha_fw_name}\"!"
                                    logger.error(ha_create_interface_error)
                                    errors.append(ha_create_interface_error)
                                    continue

                            ha_ip_dict = dict(
                                address=ha_fw_cidr_ip,
                                status='active',
                                nat_outisde=0,
                                interface=ha_nb_interface.id
                                )

                            try:
                                ha_create_nb_ip = nb.ipam.ip_addresses.create(ha_ip_dict)
                                ha_create_nb_ip_msg = f"Created IP \"{ha_fw_cidr_ip}\" On Interface \"{ha_fw_mgmt_int}\" For Device \"{ha_fw_name}\"."
                                logger.warning(ha_create_nb_ip_msg)
                                updates.append(ha_create_nb_ip_msg)
                                get_ha_ip = nb.ipam.ip_addresses.get(address=ha_fw_cidr_ip[:-3])

                            except:
                                ha_create_nb_ip_error = f"Failed To Create IP \"{ha_fw_cidr_ip}\" On Interface \"{ha_fw_mgmt_int}\" For Device \"{ha_fw_name}\"!"
                                logger.error(ha_create_nb_ip_error)
                                errors.append(ha_create_nb_ip_error)
                                continue

                            ha_primary_ip_dict = dict(primary_ip4=get_ha_ip.id)

                            try:
                                ha_update_ip = get_nb_ha_fw.update(ha_primary_ip_dict)

                            except pynetbox.RequestError as e:
                                ha_update_ip_error = f"Failed To Update Primary IP \"{ha_fw_name}\" For \"{ha_fw_name}\"!\n \"{e}\"!"
                                logger.error(ha_update_ip_error)
                                errors.append(ha_update_ip_error)

                            if ha_update_ip == True:
                                ha_update_ip_msg = f"Primary IP For \"{ha_fw_name}\" Has Been Set To \"{ha_fw_cidr_ip}\"."
                                logger.warning(ha_update_ip_msg)
                                updates.append(ha_update_ip_msg)

                            else:
                                ha_update_ip_error2 = f"Failed To Update Primary IP \"{ha_fw_cidr_ip}\" For \"{ha_fw_name}\"!"
                                logger.error(ha_update_ip_error2)
                                errors.append(ha_update_ip_error2)

                    else:
                        logger.info(f"Primary IP \"{ha_fw_cidr_ip}\" Is Already Correct For \"{ha_fw_name}\".")

            else:
                logger.info(f"\"{ha_fw_name}\" Is Not In Netbox!")

                ha_fw_func_name = 'ap'+ha_fw_name[2:].lower()  #Modify FW name to work with site_code_match function
                ha_site_id = site_code_match(ha_fw_func_name, nb_url, nb_token)

                if ha_site_id == False:
                    ha_site_id_msg = f"Site ID For \"{ha_fw_name}\" Not Found.  Unable To Create \"{ha_fw_name}\"!"
                    logger.error(ha_site_id_msg)
                    errors.append(ha_site_id_msg)
                    continue

                ha_fw_model_lwr = str.lower(fw_model)
                ha_fw_dev_type = nb.dcim.device_types.get(slug=ha_fw_model_lwr)

                if ha_fw_dev_type == None:
                    ha_dev_type_msg = f"Device Type \"{fw_model}\" Not Found In Netbox! Unable To Create \"{ha_fw_name}\"!"
                    logger.error(ha_dev_type_msg)
                    errors.append(ha_dev_type_msg)
                    continue

                ha_fw_dict = dict(
                    name = ha_fw_name,
                    device_type = ha_fw_dev_type.id,
                    device_role = fw_role.id,
                    platform = fortios_platform.id,
                    serial = ha_fw_sn,
                    site = ha_site_id,
                    status = 'active',
                    tenant = tenant.id
                    )

                try:
                    create_ha_fw = nb.dcim.devices.create(ha_fw_dict)
                    logger.warning(f"Created Firewall \"{ha_fw_name}\" In Netbox Site \"{ha_site_id}\".")
                    firewalls_created.append(ha_fw_name)

                except pynetbox.RequestError as e:
                    logger.error(ha_fw_name, e)
                    errors.append(f"Failed To Create \"{ha_fw_name}\"!")
                    continue

                get_nb_ha_fw2 = nb.dcim.devices.get(name=ha_fw_name)

                ha_mgmt_int_dict = dict(
                    name=ha_fw_mgmt_int,
                    type=ha_int_type,
                    device=get_nb_ha_fw2.id,
                    enabled=True,
                    description="Management Interface"
                    )

                try:
                    ha_create_interface = nb.dcim.interfaces.create(ha_mgmt_int_dict)
                    ha_create_interface_msg = f"Created Interface \"{ha_fw_mgmt_int}\" On \"{ha_fw_name}\"."
                    logger.warning(ha_create_interface_msg)
                    updates.append(ha_create_interface_msg)
                    ha_nb_interface = nb.dcim.interfaces.get(name=ha_fw_mgmt_int, device=ha_fw_name)

                except:
                    ha_create_interface_error = f"Error Creating Interface \"{ha_fw_mgmt_int}\" On \"{ha_fw_name}\"!"
                    logger.error(ha_create_interface_error)
                    errors.append(ha_create_interface_error)
                    continue

                ha_ip_dict = dict(
                    address=ha_fw_cidr_ip,
                    status='active',
                    nat_outisde=0,
                    interface=ha_nb_interface.id
                    )

                try:
                    ha_create_nb_ip = nb.ipam.ip_addresses.create(ha_ip_dict)
                    ha_create_nb_ip_msg = f"Created IP \"{ha_fw_cidr_ip}\" On \"{ha_fw_name}\" Interface \"{ha_fw_mgmt_int}\"."
                    logger.warning(ha_create_nb_ip_msg)
                    updates.append(ha_create_nb_ip_msg)
                    get_ha_ip = nb.ipam.ip_addresses.get(address=ha_fw_cidr_ip)

                except:
                    ha_create_nb_ip_error = f"Failed To Create IP \"{ha_fw_cidr_ip}\" On \"{ha_fw_name}\" Interface \"{ha_fw_mgmt_int}\"!"
                    logger.error(ha_create_nb_ip_error)
                    errors.append(ha_create_nb_ip_error)
                    continue

                ha_primary_ip_dict = dict(primary_ip4=get_ha_ip.id)

                try:
                    ha_update_ip = get_nb_ha_fw2.update(ha_primary_ip_dict)

                except pynetbox.RequestError as e:
                    ha_update_ip_error = f"Failed To Update Primary IP \"{ha_fw_name}\" For \"{ha_fw_name}\"!\n \"{e}\"!"
                    logger.error(ha_update_ip_error)
                    errors.append(ha_update_ip_error)

                if ha_update_ip == True:
                    ha_update_ip_msg = f"Primary IP For \"{ha_fw_name}\" Has Been Set To \"{ha_fw_cidr_ip}\"."
                    logger.warning(ha_update_ip_msg)
                    updates.append(ha_update_ip_msg)

                else:
                    ha_update_ip_error2 = f"Failed To Update Primary IP \"{ha_fw_cidr_ip}\" For \"{ha_fw_name}\"!"
                    logger.error(ha_update_ip_error2)
                    errors.append(ha_update_ip_error2)

        else:
            logger.info(f"\"{primary_fw_name}\" Is Not Redundant.")

else:
    print('Error Collecting Devices From FortiManager!')
    print(f"Error Code: {get_all_firewalls[0]}")
    sys.exit()

fmg_logout=fmg_instance.logout()

if len(firewalls_deleted) > 0:
    print("\nFirewalls Deleted:")
    for fw in firewalls_deleted:
        print(fw)

if len(firewalls_created) > 0:
    print("\nFirewalls Created:")
    for fw in firewalls_created:
        print(fw)

if len(updates) > 0:
    print("\nFirewall Updates:")
    for update in updates:
        print(update)

if len(errors) > 0:
    print("\nErrors:")
    for error in errors:
        print(error)

print("\nScript Complete :smiley: \n")
logger.info("Script Complete!")
