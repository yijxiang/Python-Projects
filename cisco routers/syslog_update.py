import pynetbox, requests, logging, netmiko, sys
from tqdm import tqdm
from secrets import nb_token, nb_url, un, pw
from hvac_func import retrieve_secret

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings() 

nb = pynetbox.api(url=nb_url, token=nb_token) # Define Nebox API Call
nb.http_session = session

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename="logs/ManSyslogUpdate.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("Man")
logger.info("\n--  START OF SCRIPT  --")

Man = nb.dcim.devices.filter(tag="man", has_primary_ip=True, status='active')
logServerIP = "192.168.1.1"

logging.info("Checking These Devices For Splunk Syslog Config:")
for d in Man:
    logger.info(d.name)

updates = []
errors = []

secrets = retrieve_secret(un, pw, "shared", "devnet") # get creds from Vault
rtrUn = secrets['username']
rtrPw = secrets['password']

for r in tqdm(Man, desc="Checking For Syslog Receiver"):
    ip = r.primary_ip.address[:-3]

    #Create Device Profile for Netmiko to Connect
    if r.device_type.model == "C9504":
        netmikoDevType = "cisco_nxos_ssh"
    else:
        netmikoDevType = "cisco_ios"
    
    logger.info(f"Netmiko Connection Handler is \"{netmikoDevType}\".")

    ManRtr = {
        'device_type': netmikoDevType,
        'ip': ip,
        'username': rtrUn,
        'password': rtrPw
        }

    logger.info(f"Connecting to {r.name} - {ip}")

    try:
        net_connect = netmiko.ConnectHandler(**ManRtr)    # connect to the device w/ netmiko
    except:
        netmikoErrMsg1 = f"Failed to connect to {r.name} - {ip}."
        logger.error(netmikoErrMsg1)
        errors.append(netmikoErrMsg1)
        logger.debug(f"Exception: {sys.exc_info()[0]}")

    if r.device_type.model == "C9504":  #CORP20 NEXUS
        nexusShowLogging = net_connect.send_command(f"sho run | inc \"logging server {logServerIP}\"")
        logger.info(f"Sent Command: \"sho run | inc logging server {logServerIP}\"")
        logger.info(f"Response: \"{nexusShowLogging}\"")
        
        if f"logging server {logServerIP}" in nexusShowLogging:
            logger.info(f"NX-OS device {r.name} is already sending syslogs to Splunk.")
        else:
            logger.info(f"NX-OS device {r.name} needs to be updated.")
            nexusVrfCheck = net_connect.send_command("show vrf SECURITY")
            # logger.info(nexusVrfCheck)

            if "not found" in nexusVrfCheck: # Nexus Reponse is "% VRF SECURITY not found"
                logger.info(f"NX-OS device {r.name} does not have a SECURITY VRF.")
                nexusSyslogCmd = [f"logging server {logServerIP}"]
                nexusConfigSyslog = net_connect.send_config_set(nexusSyslogCmd)
                logger.warning(f"Configure Device: \n{nexusConfigSyslog}")
                nexusSaveConfig = net_connect.save_config()
                logger.warning(f"Save Config: \n{nexusSaveConfig}")
                nexusConfirmLogging = net_connect.send_command(f"sho run | inc \"logging server {logServerIP}\"")

                if f"logging server {logServerIP}" in nexusConfirmLogging:
                    nexusConfirmLoggingMsg1 =  (f"NX-OS device {r.name} is now sending syslogs to Splunk.")
                    logger.info(nexusConfirmLoggingMsg1)
                    updates.append(nexusConfirmLoggingMsg1)
                else:
                    nexusConfirmLoggingErr1 = f"Error adding syslog receiver to {r.name}."
                    logger.error(nexusConfirmLoggingErr1, nexusConfigSyslog)
                    errors.append(nexusConfirmLoggingErr1)

            else:
                logger.info(f"NX-OS device {r.name} is using VRF SECURITY.")
                nexusSyslogCmdVrf = [f"logging server {logServerIP} use-vrf SECURITY"]
                nexusConfigSyslogVrf = net_connect.send_config_set(nexusSyslogCmdVrf)
                logger.warning(f"Configure Device: \n{nexusConfigSyslogVrf}")
                nexusSaveConfigVrf = net_connect.save_config()
                logger.warning(f"Save Config: \n{nexusSaveConfigVrf}")
                nexusConfirmLoggingVrf = net_connect.send_command(f"sho run | inc \"logging server {logServerIP}\"")

                if f"logging server {logServerIP}" in nexusConfirmLoggingVrf: 
                    nexusConfirmLoggingVrfMsg2 = (f"NX-OS device {r.name} is now sending syslogs to Splunk using vrf SECURITY.")
                    logger.info(nexusConfirmLoggingVrfMsg2)
                    updates.append(nexusConfirmLoggingVrfMsg2)
                else:
                    nexusConfirmLoggingErr2 = f"Error adding syslog receiver to NX-OS device {r.name} for vrf SECURITY."
                    logger.error(nexusConfirmLoggingErr2, nexusConfigSyslogVrf)
                    errors.append(nexusConfirmLoggingErr2)

    else:
        iosShowLogging = net_connect.send_command(f"sho run | inc logging host {logServerIP}")
        logger.info(f"Sent Command: \"sho run | inc logging host {logServerIP}\"")
        logger.info(f"Response: \"{iosShowLogging}\"")

        if f"logging host {logServerIP}" in iosShowLogging: 
            logger.info(f"IOS device {r.name} is aleady sending syslogs to Splunk.")
        else:
            logger.info(f"IOS device {r.name} needs to be updated.")
            iosVrfCheck = net_connect.send_command("show vrf SECURITY")

            if "No VRF named SECURITY" in iosVrfCheck: # IOS Response is "% No VRF named SECURITY"
                logger.info(f"IOS device {r.name} does not have a SECURITY VRF.")
                iosSyslogCmd = [f"logging host {logServerIP}"]
                iosConfigSyslog = net_connect.send_config_set(iosSyslogCmd)
                logger.warning(f"Configure Device: \n{iosConfigSyslog}")
                iosSaveConfig = net_connect.save_config()
                logger.warning(f"Save Config: \n{iosSaveConfig}")
                iosConfirmLogging = net_connect.send_command(f"sho run | inc logging host {logServerIP}")

                if f"logging host {logServerIP}" in iosConfirmLogging: 
                    iosConfirmLoggingMsg1 = f"IOS Device {r.name} is now sending syslogs to Splunk."
                    logger.info(iosConfirmLoggingMsg1)
                    updates.append(iosConfirmLoggingMsg1)
                else:
                    iosConfirmLoggingErr1 = f"Error adding syslog receiver to IOS device {r.name}."
                    logger.error(iosConfirmLoggingErr1, iosConfigSyslog)
                    errors.append(iosConfirmLoggingErr1)
                    
            else:
                logger.info(f"IOS device {r.name} is using a SECURITY VRF.")
                iosSyslogCmdVrf = [f"logging host {logServerIP} vrf SECURITY"]
                iosConfigSyslogVrf = net_connect.send_config_set(iosSyslogCmdVrf)
                logger.warning(f"Configure Device: \n{iosConfigSyslogVrf}")
                iosSaveConfigVrf = net_connect.save_config()
                logger.warning(f"Save Config: \n{iosSaveConfigVrf}")
                iosConfirmLoggingVrf = net_connect.send_command(f"sho run | inc logging host {logServerIP}")

                if f"logging host {logServerIP}" in iosConfirmLoggingVrf:
                    iosConfirmLoggingVrfMsg2 =  f"IOS device {r.name} is now sending syslogs to Splunk."
                    logger.info(iosConfirmLoggingVrfMsg2)
                    updates.append(iosConfirmLoggingVrfMsg2)
                else:
                    iosConfirmLoggingVrfErr2 = f"Error adding syslog receiver to IOS device {r.name} using vrf SECURITY."
                    logger.error(iosConfirmLoggingVrfErr2)
                    errors.append(iosConfirmLoggingVrfErr2)
                    

if len(updates) > 0:
    print(f"Updated Devices: {len(updates)}")
    for u in updates:
        print(u)

if len(errors) > 0:
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(e)

logger.info("\n--  END OF SCRIPT  --")
print("Script Complete")
