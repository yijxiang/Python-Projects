############### VERSION 2 ###########################
#Uses Netbox for inventory

"""
Created by: Louis Uylaki
Project: Wireless Rogue Splunk Technical APP
Date: 12/2020

"""
# encoding = utf-8

import os
import sys
import time
import datetime
import requests
import socket
import re
import ntc_templates
import netmiko
import pynetbox
from modules import classify_rogue


def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # username = definition.parameters.get('username', None)
    # password = definition.parameters.get('password', None)
    pass

def collect_events(helper, ew):
    
    event_time = 0
    wlc_un = helper.get_arg('username')
    wlc_pw = helper.get_arg('password')
    nb_url = 'https://netbox.com/'
    nb_token = helper.get_arg('netbox_token')
    
    requests.packages.urllib3.disable_warnings()
    session = requests.Session()
    session.verify = False
    nb = pynetbox.api(url=nb_url, token=nb_token)
    nb.http_session = session
    
    try: 
        nb_wlcs=nb.dcim.devices.filter(role='wlc', has_primary_ip=True, status='active', tag='wrls_rogues', name='WLC-01')
        helper.log_info("Netbox WLC Collection Complete!")
    except:
        helper.log.error("Failed to get WLCs from Netbox!")
        sys.exit()
    
    for wlc in nb_wlcs:
        wlc_ip=wlc.primary_ip.address[:-3]
        wlc_name=wlc.name
    
        #Create Device Profiles for Netmiko to Connect
        cisco_wlc = {
        'device_type': 'cisco_wlc_ssh', 
        'ip': wlc_ip, 
        'username': wlc_un, 
        'password': wlc_pw
        }
    
        site_code_name = wlc_name[3:-3] # strip first 3 and last 3 characters
        helper.log_info(f"Connecting to {wlc_name} - {wlc_ip}.")
        try:
            net_connect = netmiko.ConnectHandler(**cisco_wlc)    # connect to the device w/ netmiko
        except:
            helper.log_error(f"Failed to connect to {wlc_name} - {device['ip']}.")
            helper.log_debug(f"Exception: {sys.exc_info()[0]}")
    
        wlc_r_sum = net_connect.send_command("show rogue ap summary", use_textfsm=True)
        helper.log_info(f"Sending command - show rogue ap summary to {wlc_name}.")
        time.sleep(1)
        wlc_advanced_sum_b = net_connect.send_command("show advanced 802.11b summary", use_textfsm=True)
        helper.log_info(f"Sending command - show advanced 802.11b summary to {wlc_name}.")
        time.sleep(1)

        wlc_advanced_sum_a = net_connect.send_command("show advanced 802.11a summary", use_textfsm=True)
        helper.log_info(f"Sending command - show advanced 802.11a summary to {wlc_name}.")
        time.sleep(1)

        for item in wlc_r_sum:
            mac_address=item['mac_address']
            rogue_clients=item['rogue_clients']
            det_aps=item['det_aps']
            highest_rssi=item['highest_rssi_det_ap']
            rssi1=item['rssi_one']
            channel1=item['channel_one']
            rogue_mac=mac_address  # Send command for each rogue in summary output
            
            this_cmd = net_connect.send_command("show rogue ap detailed "+f"{rogue_mac}", use_textfsm=True)
            helper.log_info(f"Sending command - show rogue ap detailed {rogue_mac} to {wlc_name}.")
            
            if this_cmd == "Rogue requested does not exist\n" or this_cmd == "\nRogue requested does not exist\n":
                helper.log_warning(f"Rogue {rogue_mac} no longer exists on {wlc_name}.")
                continue
    
            else:
                try:
                    ssid=this_cmd[1]['ssid']
                except:
                    helper.log_warning(f"Currently no detailed info for {rogue_mac} on {wlc_name}.")
                    continue
                last_seen=this_cmd[0]['last_seen']
                first_seen=this_cmd[0]['first_seen']
                classification = classify_rogue(ssid)
                for radio_b in wlc_advanced_sum_b:
                    if radio_b['mac_address'] == highest_rssi:
                        highest_rssi=radio_b['ap_name']
                for radio_a in wlc_advanced_sum_a:
                    if radio_a['mac_address'] == highest_rssi:
                        highest_rssi=radio_a['ap_name']
        
                data={"MAC_Address": mac_address,"SSID": ssid, "Classification": classification, 
                "Rogue_Clients": rogue_clients, "Det_APs": det_aps, "Strongest_Det_AP": highest_rssi, 
                "Channel": channel1, "RSSI": rssi1, "Last_Seen": last_seen, "First_Seen": first_seen, }
                a=0
                for item in this_cmd[1:]:
                    a+=1
                    data[f'Detecting_AP_{a}'] = item['reporting_ap_name']
                    data[f'RSSI_{a}'] = item['rssi']
                    
                data4=str(data).replace("{", "").replace("}", "\"").replace("'", "").replace(": ", "=\"").replace(", ", "\" ")
                event = helper.new_event(data4, time=format(event_time,'.3f'), host=wlc_name, index='test', source=wlc_name, sourcetype="wireless:rogue:details", done=True, unbroken=True)
                ew.write_event(event)



############### VERSION 1 #################################

#!/usr/bin/env python3.7
# encoding = utf-8

import os
import sys
import time
import datetime
import socket
import re
import netmiko
import json
from modules import classify_rogue

#sys.path.append('/opt/splunk/etc/apps/TA-wireless-rogues/bin/')

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''

def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    # This example accesses the modular input variable
    # username = definition.parameters.get('username', None)
    # password = definition.parameters.get('password', None)
    pass

def collect_events(helper, ew):
    event_time = 0
    
    wlc_ip = "192.168.2.5"
    
    wlc_ips=[wlc_ip]
    regex1 = r'(WLC.*)\.us.*'
    regex2 = r'(wlc.*)\.us.*'
    
    wlc_un = helper.get_arg('username')
    wlc_pw = helper.get_arg('password')
    
    devices=[]
    for ip in wlc_ips:  #Create Device Profiles for Netmiko to Connect
        cisco_wlc = {
        'device_type': 'cisco_wlc_ssh', 
        'ip': ip, 
        'username': wlc_un, 
        'password': wlc_pw,  
        }
        devices.append(cisco_wlc)
    
    for device in devices:
        data2=[]
        wlc_name_full=socket.gethostbyaddr(device['ip'])
        for a in wlc_name_full: #Get hostname from IP, remove .us164... via DNS Lookup
            regex1 = r'(WLC.*)\.us.*'
            regex2 = r'(wlc.*)\.us.*'
            b=str(a)
            regmatch1 = re.match(regex1, b)
            regmatch2 = re.match(regex2, b)
            if regmatch1:
                wlc_name = regmatch1.group(1)
            elif regmatch2:
                wlc_name = regmatch2.group(1).upper()
        site_code_name = wlc_name[3:-3] # strip first 3 and last 3 characters
    
        helper.log_info(f"Connecting to {wlc_name} - {device['ip']}")
        try:
            net_connect = netmiko.ConnectHandler(**device)    # connect to the device w/ netmiko
        except:
            helper.log_error(f"Failed to connect to {wlc_name} - {device['ip']}")
            helper.log_debug(f"Exception: {sys.exc_info()[0]}")
    
        wlc_r_sum = net_connect.send_command("show rogue ap summary", use_textfsm=True)
        helper.log_info("sending command - show rogue ap summary")
        time.sleep(1)
        wlc_advanced_sum_b = net_connect.send_command("show advanced 802.11b summary", use_textfsm=True)
        helper.log_info("sending command - show advanced 802.11b summary")
        time.sleep(1)

        wlc_advanced_sum_a = net_connect.send_command("show advanced 802.11a summary", use_textfsm=True)
        helper.log_info("sending command - show advanced 802.11a summary")
        time.sleep(1)

        for item in wlc_r_sum:
            mac_address=item['mac_address']
            rogue_clients=item['rogue_clients']
            det_aps=item['det_aps']
            highest_rssi=item['highest_rssi_det_ap']
            rssi1=item['rssi_one']
            channel1=item['channel_one']
    
            rogue_mac=mac_address  # Send command for each rogue in summary output
            this_cmd = net_connect.send_command("show rogue ap detailed "+f"{rogue_mac}", use_textfsm=True)
            helper.log_info(f"sending command - show rogue ap detailed {rogue_mac}")
            
            if this_cmd == "Rogue requested does not exist\n" or this_cmd == "\nRogue requested does not exist\n":
                helper.log_warning(f"Rogue {rogue_mac} no longer exists")
                continue
    
            else:
                try:
                    ssid=this_cmd[1]['ssid']
                except:
                    helper.log_warning(f"Currently no detailed info for {rogue_mac}.")
                    continue
                last_seen=this_cmd[0]['last_seen']
                first_seen=this_cmd[0]['first_seen']
                classification = classify_rogue(ssid)
                for radio_b in wlc_advanced_sum_b:
                    if radio_b['mac_address'] == highest_rssi:
                        highest_rssi=radio_b['ap_name']
                for radio_a in wlc_advanced_sum_a:
                    if radio_a['mac_address'] == highest_rssi:
                        highest_rssi=radio_a['ap_name']
        #todo will need to add try for 802.11abgn radios where 2800 series aps are used.
                data={"MAC_Address": mac_address,"SSID": ssid, "Classification": classification, 
                "Rogue_Clients": rogue_clients, "Det-APs": det_aps, "Strongest_Det_AP": highest_rssi, 
                "Channel": channel1, "RSSI": rssi1, "Last_Seen": last_seen, "First_Seen": first_seen, }
                a=0
                for item in this_cmd[1:]:
                    a+=1
                    data[f'Detecting_AP_{a}'] = item['reporting_ap_name']
                    data[f'RSSI_{a}'] = item['rssi']
                    
                    

                data4=str(data).replace("{", "").replace("}", "").replace("'", "").replace(": ", "=\"").replace(",", "\"")
        
                event = helper.new_event(data4, time=format(event_time,'.3f'), host=wlc_name, index='test', source=wlc_name, sourcetype="wireless:rogues", done=True, unbroken=True)
                ew.write_event(event)
    
    
        
        
        
        
        
        
        
    """Implement your data collection logic here
    
    # The following examples get the arguments of this input.
    # Note, for single instance mod input, args will be returned as a dict.
    # For multi instance mod input, args will be returned as a single value.
    opt_username = helper.get_arg('username')
    opt_password = helper.get_arg('password')
    # In single instance mode, to get arguments of a particular input, use
    opt_username = helper.get_arg('username', stanza_name)
    opt_password = helper.get_arg('password', stanza_name)

    # get input type
    helper.get_input_type()

    # The following examples get input stanzas.
    # get all detailed input stanzas
    helper.get_input_stanza()
    # get specific input stanza with stanza name
    helper.get_input_stanza(stanza_name)
    # get all stanza names
    helper.get_input_stanza_names()

    # The following examples get options from setup page configuration.
    # get the loglevel from the setup page
    loglevel = helper.get_log_level()
    # get proxy setting configuration
    proxy_settings = helper.get_proxy()
    # get account credentials as dictionary
    account = helper.get_user_credential_by_username("username")
    account = helper.get_user_credential_by_id("account id")
    # get global variable configuration
    global_userdefined_global_var = helper.get_global_setting("userdefined_global_var")

    # The following examples show usage of logging related helper functions.
    # write to the log for this modular input using configured global log level or INFO as default
    helper.log("log message")
    # write to the log using specified log level
    helper.log_debug("log message")
    helper.log_info("log message")
    helper.log_warning("log message")
    helper.log_error("log message")
    helper.log_critical("log message")
    # set the log level for this modular input
    # (log_level can be "debug", "info", "warning", "error" or "critical", case insensitive)
    helper.set_log_level(log_level)

    # The following examples send rest requests to some endpoint.
    response = helper.send_http_request(url, method, parameters=None, payload=None,
                                        headers=None, cookies=None, verify=True, cert=None,
                                        timeout=None, use_proxy=True)
    # get the response headers
    r_headers = response.headers
    # get the response body as text
    r_text = response.text
    # get response body as json. If the body text is not a json string, raise a ValueError
    r_json = response.json()
    # get response cookies
    r_cookies = response.cookies
    # get redirect history
    historical_responses = response.history
    # get response status code
    r_status = response.status_code
    # check the response status, if the status is not sucessful, raise requests.HTTPError
    response.raise_for_status()

    # The following examples show usage of check pointing related helper functions.
    # save checkpoint
    helper.save_check_point(key, state)
    # delete checkpoint
    helper.delete_check_point(key)
    # get checkpoint
    state = helper.get_check_point(key)

    # To create a splunk event
    helper.new_event(data, time=None, host=None, index=None, source=None, sourcetype=None, done=True, unbroken=True)
    """

    '''
    # The following example writes a random number as an event. (Multi Instance Mode)
    # Use this code template by default.
    import random
    data = str(random.randint(0,100))
    event = helper.new_event(source=helper.get_input_type(), index=helper.get_output_index(), sourcetype=helper.get_sourcetype(), data=data)
    ew.write_event(event)
    '''

    '''
    # The following example writes a random number as an event for each input config. (Single Instance Mode)
    # For advanced users, if you want to create single instance mod input, please use this code template.
    # Also, you need to uncomment use_single_instance_mode() above.
    import random
    input_type = helper.get_input_type()
    for stanza_name in helper.get_input_stanza_names():
        data = str(random.randint(0,100))
        event = helper.new_event(source=input_type, index=helper.get_output_index(stanza_name), sourcetype=helper.get_sourcetype(stanza_name), data=data)
        ew.write_event(event)
    '''
