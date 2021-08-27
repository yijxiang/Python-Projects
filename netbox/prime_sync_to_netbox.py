import requests, urllib3, pynetbox, logging, json
from requests.auth import HTTPBasicAuth
from functions import interfaceType, site_code_match
from pprint import pprint
from tqdm import tqdm
from rich import print
from secrets import prime_url, prime_user, prime_pw, nb_token, nb_url

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="logs/syncPrimeToNetbox.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("wlc_backup")

# prime_switches = []
# prime_routers = []
# netbox_switches = []
# netbox_routers = []
errors = []
name = []
missing_sn = []
nexus = []
other = []
unknown_platform = []
missing = []
unreachable = []
unsupported = []
changes = []

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

nbCiscoMfg = nb.dcim.manufacturers.get(slug="cisco")
nbAccessRole = nb.dcim.device_roles.get(slug='access')
nbICSAccessRole = nb.dcim.device_roles.get(slug='ics-access')
# nbDistibutionRole = nb.dcim.device_roles.get(slug='distribution')
# nbICSDistibutionRole = nb.dcim.device_roles.get(slug='ics-distribution')
dtna_tenant=nb.tenancy.tenants.get(slug='tenant')
iosxe_platform = nb.dcim.platforms.get(slug='iosxe')

#Filtering/Paging params https://developer.cisco.com/site/prime-infrastructure/documents/api-reference/rest-api-v3-8/v4/@id=paging-doc/
querystring = "?.full=true"
firstResult = "&.firstResult=1000" # paging
maxresults = "&.maxResults=1000"
device_name = "&deviceName=startsWith(SW)"  
vendor = "&vendor=startsWith(Raspberry)"
vlan = "&vlan=716"

# url = prime_url+"data/ClientDetails.json{}{}{}".format(querystring,vendor,vlan)
url = prime_url+"data/Devices.json{}{}{}".format(querystring,device_name,maxresults)
# url = prime_url+"data/AccessPointDetails.json{}{}{}".format(querystring,firstResult,maxresults)

basicAuth=HTTPBasicAuth(prime_user, prime_pw)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

response = requests.get(url, auth=basicAuth, verify=False).json()
# print(json.dumps(response, indent=2, sort_keys=True))


name_set = ['1', '2', '3', '4', '5', 'Switch 1', 'Switch 2', 'Switch 3', 'Switch 4', 'Switch 5',
    'Switch1 System', 'Switch2 System', 'Switch3 System'
    ]
s = set(name_set)

for entity in response['queryResponse']['entity']:
    switchFqdn = entity['devicesDTO']['deviceName']
    splitName = switchFqdn.split('.')
    switch_name = splitName[0]
    ip = entity['devicesDTO']['ipAddress']
    dtype = entity['devicesDTO']['deviceType']
    primeID = entity['devicesDTO']['@id']
    reachable = entity['devicesDTO']['reachability']

    try:
        swType = entity['devicesDTO']['softwareType']
    except:
        swType = "Unknown"
    try:
        model = entity['devicesDTO']['manufacturerPartNrs']['manufacturerPartNr']
    except:
        missingPartNbr = (f"{switch_name} has no manufacturerPartNr")
        logger.error(missingPartNbr)
        errors.append(missingPartNbr)

        # pprint(entity)
        continue

    if "ICS" in switch_name or "ics" in switch_name:
        roleId = nbICSAccessRole.id
    else:
        roleId = nbAccessRole.id

    if "Nexus" in dtype:
        nexus.append(entity)
        logger.info(f"Skipping Nexus Device \"{switch_name}\".")
        continue

    if dtype == 'Unsupported Cisco Device':
        unsupported.append(entity)
        logger.info(f"Skipping Unsupported Cisco Device \"{switch_name}\".")
        continue

    if reachable == "UNREACHABLE":
        logger.info(f"Skipping Unreachable Device \"{switch_name}\".")
        unreachable.append(entity)
        continue

    for switch in model:
        sw_num = str(switch['name'])
        sw_model = switch['partNumber']
        try:
            sw_sn = switch['serialNumber']
        except:
            msg = (f"{switch_name} {sw_num} serial number key not found.")
            missing_sn.append(msg)
            # pprint(entity)

        swData = {"primeID": primeID, "name": "", "model": sw_model, "dtype": dtype,
                    "sn": sw_sn, "platform": swType, "role": roleId, "vcPosition": ""}

        if len(model) == 1:
            swData['name'] = switch_name
            swData['ip'] = ip
            swData['vcPosition'] = 1
            name.append(swData)

        elif sw_num in s:

            if sw_num == '1' or sw_num == 'Switch 1' or sw_num == 'Switch1 System':
                swData['name'] = switch_name
                swData['ip'] = ip
                swData['vcPosition'] = 1
                name.append(swData)
            elif sw_num == '2' or sw_num == 'Switch 2' or sw_num == 'Switch2 System':
                switch_name2 = switch_name+"-2"
                swData['name'] = switch_name2
                swData['vcPosition'] = 2
                name.append(swData)
            elif sw_num == '3' or sw_num == 'Switch 3' or sw_num == 'Switch3 System':
                switch_name3 = switch_name+"-3"
                swData['name'] = switch_name3
                swData['vcPosition'] = 3
                name.append(swData)
            elif sw_num == '4' or sw_num == 'Switch 4':
                switch_name4 = switch_name+"-4"
                swData['name'] = switch_name4
                swData['vcPosition'] = 4
                name.append(swData)
            elif sw_num == '5' or sw_num == 'Switch 5':
                switch_name5 = switch_name+"-5"
                swData['name'] = switch_name5
                swData['vcPosition'] = 5
                name.append(swData)

        else:
            other.append(entity) #Other 
# print(name[0:5])

for device in tqdm(name, desc="Checking Devices"):
    dname = device['name']
    get_nb_device_count = nb.dcim.devices.count(name__ie=dname)

    if get_nb_device_count == 0: # Create if device doesn't exist
        missing.append(device)
        # print(f"{device} Not In Netbox.")
    if get_nb_device_count > 1:
        nbDevCountMsg = f"Multiple Devices With Name \"{device}\" Exist In Netbox!"
        logger.error(nbDevCountMsg)
        errors.append(nbDevCountMsg)

missing_sorted = sorted(missing, key=lambda k: k['name'])
logger.info(f"Not Found In Netbox:  {len(missing_sorted)}")
# print(missing_sorted[0:5])

for item in tqdm(missing_sorted[0:4], desc="Adding Missing Devices"): # Use slice [0:10] to limit creation
    mName = item['name']
    mModel = item['model']
    mPrimeId = item['primeID']
    mPlatform = item['platform']
    mSerial = item['sn']
    mRole = item['role']
    mVcPosition = item['vcPosition']

    if 'ip' in item:
        mIp = item['ip']
    else:
        mIp = None

    func_name = 'ap'+mName[2:].lower()  #Modify device name to work with site_code_match function
    site_id = site_code_match(func_name, nb_url, nb_token)

    if site_id == False:
        site_id_msg = f"Site ID for \"{mName}\" Not Found.  Unable to Create \"{mName}\"!"
        logger.error(site_id_msg)
        errors.append(site_id_msg)
        # print(site_id_msg)
        continue
    else:
        item['nb_site_id'] = site_id
    
    mSiteId = item['nb_site_id']
    # pprint(item)

    if mPlatform == "Unknown":
        logger.error(f"entity['devicesDTO']['softwareType'] Not Found For \"{mName}\"")
        unknown_platform.append(item)
        continue
    
    if "Cisco" in dtype and "IOS" in mPlatform:
        modelCheck = nb.dcim.device_types.get(model=mModel)

        if modelCheck != None:  # If model exists in Netbox get ID, If not then create it.
            modelID = modelCheck.id
        else:
            mModelSlug = mModel.lower()
            model_dict = dict(
                manufacturer = nbCiscoMfg.id,
                model = mModel,
                slug = mModelSlug
            )
            try:
                newModel = nb.dcim.device_types.create(model_dict)
            except:
                devErrMsg = f"Failed Creating New Model Type \"{mModel}\" for \"{mName}\"."
                logger.error(devErrMsg, newModel)
                errors.append(devErrMsg)
                # print(devErrMsg)
                continue

            if str(newModel) == mModel: # If creation is successful response will be model value
                getNewModel = nb.dcim.device_types.get(model=mModel)
                modelID = getNewModel.id
                newModelMsg = (f"Created New Model \"{mModel}\".")
                logger.warning(newModelMsg)
                changes.apepnd(newModelMsg)
                # print(newModelMsg)
            else:
                newModelErr = (f"Failure Trying to Create New Model \"{mModel}\".")
                logger.error(newModelErr, str(newModel))
                errors.append(newModelErr)
                # print(newModelErr)
                continue

        deviceDict = dict(
            name = mName,
            device_type = modelID,
            device_role = mRole,
            platform = iosxe_platform.id,
            serial = mSerial,
            site = mSiteId,
            status = 'active',
            tenant = dtna_tenant.id
            )
        # pprint(deviceDict)
        
        try:
            createSwitch = nb.dcim.devices.create(deviceDict)
        except:
            createSwitchErr1 = f"Error While Creating Device \"{mName}\"."
            logger.error(createSwitchErr1)
            errors.append(createSwitchErr1)
            continue

        if str(createSwitch) == mName:
            createSwitchMsg1 = f"Device \"{mName}\" Created Successfully."
            logger.warning(createSwitchMsg1)
            changes.append(createSwitchMsg1)
        else:
            createSwitchErr2 = f"Error While Creating Device \"{mName}\". {createSwitch}"
            logger.error(createSwitchErr2)
            errors.append(createSwitchErr2)
            continue

        getSwitch = nb.dcim.devices.get(name=mName)
        if mVcPosition >= 2:
            chassisName = mName[:-2]
            vcName = nb.dcim.virtual_chassis.get(q=chassisName) #check for virtual chassis

            if vcName != None:
                getSwitch.virtual_chassis = vcName.id
                getSwitch.vc_position = mVcPosition
                saveVc = getSwitch.save()

                if saveVc == True:
                    saveVcMsg2 = f"Added device \"{mName}\" to virtual chassis \"{vcName}\" at postion \"{mVcPosition}\"."
                    logger.warning(saveVcMsg2)
                    changes.append(saveVcMsg2)
                else:
                    saveVcErr2 = f"Error adding device \"{mName}\" to virtual chassis \"{vcName}\" at postion \"{mVcPosition}\"."
                    logger.error(saveVcErr2, saveVc)
                    errors.append(saveVcErr2)

            elif vcName == None: # If Virtual Chassis Does Not Exist, Create It.
                masterSwitch = nb.dcim.devices.get(name__ie=chassisName)
                if masterSwitch != None:
                    vcDict = dict(master=masterSwitch.id)
                    createVc = nb.dcim.virtual_chassis.create(vcDict)

                    if str(createVc).upper() == chassisName.upper():
                        createVcMsg1 = f"Virtual Chassis \"{createVc.master.name}\" Created Successfully."
                        logger.warning(createVcMsg1)
                        changes.append(createVcMsg1)

                        getSwitch.virtual_chassis = createVc.id
                        getSwitch.vc_position = mVcPosition
                        saveVc = getSwitch.save()

                        if saveVc == True:
                            saveVcMsg = f"Switch \"{mName}\" VC Position set to \"{mVcPosition}\"."
                            logger.warning(saveVcMsg)
                            changes.append(saveVcMsg)
                        else:
                            saveVcErr = f"Failed to set VC Position for \"{mName}\"."
                            logger.error(saveVcErr, saveVc)
                            errors.append(saveVcErr)
                        
                        masterSwitch.vc_position = 1
                        saveVcMaster = masterSwitch.save()

                        if saveVcMaster == True:
                            saveVcMasterMsg = f"Switch \"{masterSwitch.name}\" VC Position set to 1."
                            logger.warning(saveVcMasterMsg)
                            changes.append(saveVcMasterMsg)
                        else:
                            saveVcErr = f"Failed to set VC Position for \"{masterSwitch.name}\"."
                            logger.error(saveVcErr, saveVc)
                            errors.append(saveVcErr)

                    else:
                        createVcErr1 = f"Error While Creating Virtual Chassis \"{mName}\". {createVc}"
                        logger.error(createVcErr1, createVc)
                        errors.append(createVcErr1)

                else:
                    masterSwitchMsg = f"The Primary Switch For the Virtual Chassis \"{chassisName}\" Does Not Exist. "
                    masterSwitchMsg += f"Skipping VC Creation for \"{getSwitch.name}\"."
                    logger.error(masterSwitchMsg)
                    errors.append(masterSwitchMsg)

        if mIp != None:

            getSwitchInts = nb.dcim.interfaces.filter(device_id=getSwitch.id) # get switch interfaces
            getSwitchInv = nb.dcim.inventory_items.filter(device_id=getSwitch.id) # get switch inventory
            
            nbIntList = []
            nbInvList = []

            for interface in getSwitchInts:
                nbIntList.append(interface.name)
            for inventory in getSwitchInv:
                nbInvList.append(inventory.serial)
                    
            primeInvDetailsURL = prime_url+f"data/InventoryDetails/{mPrimeId}.json"
            primeInvDetails = requests.get(primeInvDetailsURL, auth=basicAuth, verify=False).json()

            for inv in primeInvDetails['queryResponse']['entity']:  # parses DeviceDetail response
                for i in inv['inventoryDetailsDTO']['ethernetInterfaces']['ethernetInterface']:
                    name = i['name']
                    adminStatus = i['adminStatus']

                    if adminStatus == "UP":
                        status = True
                    elif adminStatus == "DOWN":
                        status = False

                    try:
                        intDescription = i['description']
                    except:
                        intDescription = ""

                    try:
                        mac = i['macAddress']['octets']
                        mac = mac[:2]+":"+mac[2:4]+":"+mac[4:6]+":"+mac[6:8]+":"+mac[8:10]+":"+mac[10:12]
                    except:
                        mac = ""

                    if name not in nbIntList:
                        intType = interfaceType(name)
                        intDict = dict(
                            name=name,
                            type=intType,  
                            device=getSwitch.id,
                            enabled=status,
                            description=intDescription,
                            mac_address=mac
                            )

                        createInt = nb.dcim.interfaces.create(intDict)
                        # print(createInt)
                        if str(createInt) == name:
                            createIntMsg1 = f"Interface \"{name}\" Created On Device \"{getSwitch.name}\"."
                            logger.warning(createIntMsg1)
                            changes.append(createIntMsg1)
                        else:
                            createIntErr1 = f"Error Creating Interface \"{name}\" On Device \"{getSwitch.name}\"."
                            logger.error(createIntErr1, createInt)
                            errors.append(createIntErr1)

                for k in inv['inventoryDetailsDTO']['vlanInterfaces']['vlanInterface']:
                    vlanStatus = k['adminStatus']
                    vlanName = k['portName']
                    # print(vlanName, vlanStatus)
                    if vlanName not in nbIntList:
                        if vlanStatus == "UP":
                            vStatus = True
                        elif vlanStatus == "DOWN":
                            vStatus = False
                        
                        vlanIntDict = dict(
                            name=vlanName,
                            type='virtual',  
                            device=getSwitch.id,
                            enabled=vStatus
                            )
                            
                        createVlanInt = nb.dcim.interfaces.create(vlanIntDict)
                        # print(createVlanInt)
                        if str(createVlanInt) == vlanName:
                            createVlanIntMsg1 = f"Interface \"{vlanName}\" Created On Device \"{getSwitch.name}\"."
                            logger.warning(createVlanIntMsg1)
                            changes.append(createVlanIntMsg1)
                        else:
                            createVlanIntErr1 = f"Error Creating Interface \"{vlanName}\" On Device \"{getSwitch.name}\"."
                            logger.error(createVlanIntErr1, createVlanInt)
                            errors.append(createVlanIntErr1)

                    else:
                        logger.info(f"Interface \"{vlanName}\" On Device \"{getSwitch.name}\" Already Exists.")

                for j in inv['inventoryDetailsDTO']['ipInterfaces']['ipInterface']:
                    ip2 = j['ipAddress']['address']
                    ipInterface = j['name']
                    cidr = j['prefixLength']
                    # print(ip2, ipInterface, cidr)
                    
                    if mIp == ip2:
                        devPrimaryIP = ip2+"/"+cidr
                        mgmtInterface = nb.dcim.interfaces.get(device=mName, name=ipInterface)

                        int_dict=dict(
                        address=devPrimaryIP,
                        status='active',
                        nat_outisde=0,
                        interface=mgmtInterface.id,
                        )
                        try:
                            create_ip=nb.ipam.ip_addresses.create(int_dict)
                            # print(create_ip)
                            if str(create_ip) == devPrimaryIP:
                                create_ip_msg = f"Created IP Address \"{devPrimaryIP}\" in Netbox!"
                                logger.warning(create_ip_msg)
                                changes.append(create_ip_msg)
                            else:
                                create_ip_err2 = f"Error Creating IP \"{devPrimaryIP}\" For Device \"{getSwitch.name}\"."
                                logger.error(create_ip_err2, create_ip)
                                errors.append(create_ip_err2)
                        except:
                            create_ip_err = f"\"{devPrimaryIP}\" already exists in Netbox!"
                            logger.error(create_ip_err, create_ip)
                            errors.append(create_ip_err)
                            continue
                        
                        getIP = nb.ipam.ip_addresses.get(address=ip2)
                        primaryIPDict=dict(primary_ip4=getIP.id)

                        try:
                            getSwitch.update(primaryIPDict)
                            primary_ip_msg = f"Set Primary IP For Device \"{mName}\" to \"{devPrimaryIP}\"."
                            logger.warning(primary_ip_msg)
                            changes.append(primary_ip_msg)
                        except:
                            logger.error(f'Unable to set primary IP for Device \"{mName}\" to \"{devPrimaryIP}\".')
                try:
                    for k in inv['inventoryDetailsDTO']['modules']['module']:
                        if "serialNr" in k:
                            moduleSN = k['serialNr']
                            moduleName = k['description']
                            moduleName = (moduleName[:48] + '..') if len(moduleName) > 48 else moduleName
                            modulePartID = k['productId']
                            moduleDescription = k['productName']

                            if moduleSN not in nbInvList: #Compare Device Inventory SN To Netbox Inventory SN
                                inv_dict=dict(
                                    device = getSwitch.id,
                                    name = moduleName,
                                    manufacturer = 2, # match netbox mfg id 2=Cisco
                                    part_id = modulePartID,
                                    serial = moduleSN,
                                    description = moduleDescription
                                )

                                try:
                                    createInvItem = nb.dcim.inventory_items.create(inv_dict)
                                    # print(createInvItem)
                                    if str(createInvItem) == moduleName:
                                        createInvItemMsg = "Created Inventory Item \"{}\" For Device \"{}\".".format(moduleName, mName)
                                        logger.warning(createInvItemMsg)
                                        changes.append(createInvItemMsg)
                                    else:
                                        createInvItemErr2 = f"Error Creating Inventory Item \"{moduleName}\" For Device \"{mName}\"."
                                        logger.error(createInvItemErr2, createInvItem)
                                        errors.append(createInvItemErr2)
                                except:
                                    createInvItemErr1 = f"Failed to create \"{moduleName}\" on device \"{mName}\"."
                                    logger.error(createInvItemErr1)
                                    errors.append(createInvItemErr1)
                            
                            else:
                                logger.info("Netbox Inventory Item {} Already Exists In {}!".format(moduleSN, mName))
                                
                except:
                    logger.info(f"No Modules Found For Device \"{getSwitch.name}\".")

                try:
                    for l in inv['inventoryDetailsDTO']['powerSupplies']['powerSupply']:
                        powerSN = l['serialNumber']
                        if powerSN not in nbInvList:
                            powerDescription = l['description']
                            powerPartID = l['productId']
                            powerName = l['name']
                            powerDict = dict(
                                device = getSwitch.id,
                                name = powerName,
                                manufacturer = 2, # match netbox mfg id 2=Cisco
                                part_id = powerPartID,
                                serial = powerSN,
                                description = powerDescription
                                )
                            try:
                                createPsItem = nb.dcim.inventory_items.create(powerDict)
                                if str(createPsItem) == powerName:
                                    createPsItemMsg = f"Created Inventory Item \"{powerName}\" For Device \"{getSwitch.name}\"."
                                    logger.warning(createPsItemMsg)
                                    changes.append(createPsItemMsg)
                                else:
                                    createPsItemErr2 = f"Error Creating Inventory Item \"{powerName}\" For Device \"{getSwitch.name}\"."
                                    logger.error(createPsItemErr2, createPsItem)
                                    errors.append(createPsItemErr2)

                            except:
                                createPsItemErr1 = f"Error Creating Inventory Item \"{powerName}\" For Device \"{getSwitch.name}\"."
                                logger.error(createPsItemErr1, createPsItem)
                                errors.append(createPsItemErr1)
                        
                        else:
                            logger.info(f"Inventory Item Already Exists In")

                except:
                    logger.info(f"No Power Supplies Present For Device \"{getSwitch.name}\".")
                            

#todo Add routers
# for m in inv['inventoryDetailsDTO']['cdpNeighbors']['cdpNeighbor']:
if len(unknown_platform) > 0:
    print(f"\n[bold]Platform Type Missing In Prime: {len(missing_sn)}[/bold]")
    for unk in unknown_platform:
        print(unk)

if len(missing_sn) > 0:
    missing_sn.sort()
    print(f"\n[bold]Serial # Missing In Prime: {len(missing_sn)}[/bold]")
    for missing in missing_sn:
        print(missing)

if len(unreachable) > 0:
    fmt = "{:<25}{:<35}{:<48}{:<20}"
    header = ("Name", "Model", "Type", "IP")
    print(f"\n[bold]Unreachable Devices Exluded From Script: {len(unreachable)}[/bold]")
    print(fmt.format(*header))
    for un in unreachable:
        model = un['devicesDTO']['manufacturerPartNrs']['manufacturerPartNr'][0]['name']
        switchFqdn = un['devicesDTO']['deviceName']
        splitName = switchFqdn.split('.')
        switch_name = splitName[0]
        ip = un['devicesDTO']['ipAddress']
        dtype = un['devicesDTO']['deviceType']
        print(fmt.format(switch_name, model, dtype, ip))

if len(unsupported) > 0:
    fmt = "{:<25}{:<35}{:<48}{:<20}"
    header = ("Name", "Model", "Type", "IP")
    print(f"\n[bold]Unsupported Devices Exluded From Script: {len(unsupported)}[/bold]")
    print(fmt.format(*header))
    for unsup in unsupported:
        model = unsup['devicesDTO']['manufacturerPartNrs']['manufacturerPartNr'][0]['name']
        switchFqdn = unsup['devicesDTO']['deviceName']
        splitName = switchFqdn.split('.')
        switch_name = splitName[0]
        ip = unsup['devicesDTO']['ipAddress']
        dtype = unsup['devicesDTO']['deviceType']
        print(fmt.format(switch_name, model, dtype, ip))

if len(nexus) > 0:
    fmt = "{:<25}{:<35}{:<48}{:<20}"
    header = ("Name", "Model", "Type", "IP")
    print(f"\n[bold]Nexus Devices Exluded From Script: {len(nexus)}[/bold]")
    print(fmt.format(*header))
    for non in nexus:
        model = non['devicesDTO']['manufacturerPartNrs']['manufacturerPartNr'][0]['name']
        switchFqdn = non['devicesDTO']['deviceName']
        splitName = switchFqdn.split('.')
        switch_name = splitName[0]
        ip = non['devicesDTO']['ipAddress']
        dtype = non['devicesDTO']['deviceType']
        print(fmt.format(switch_name, model, dtype, ip))
        # print(f"{switch_name}, {model}, {dtype}, {ip}")

if len(other) > 0:
    fmt = "{:<25}{:<35}{:<48}{:<20}"
    header = ("Name", "Model", "Type", "IP")
    print(f"\n[bold]Other Devices Exluded From Script: {len(other)}[/bold]")
    print(fmt.format(*header))
    for oth in other:
        model = oth['devicesDTO']['manufacturerPartNrs']['manufacturerPartNr'][0]['name']
        switchFqdn = oth['devicesDTO']['deviceName']
        splitName = switchFqdn.split('.')
        switch_name = splitName[0]
        ip = oth['devicesDTO']['ipAddress']
        dtype = oth['devicesDTO']['deviceType']
        print(fmt.format(switch_name, model, dtype, ip))
        # print(f"{switch_name}, {model}, {dtype}, {ip}")

if len(errors) > 0:
    print(f"\n[bold red]Errors: {len(errors)}[/bold red]")
    for error in errors:
        print(error)

if len(changes) > 0:
    print(f"\n[bold]Changes: {len(changes)}[/bold]")
    for change in changes:
        print(change)