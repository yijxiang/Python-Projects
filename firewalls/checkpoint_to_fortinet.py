from __future__ import print_function
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpapi import APIClient, APIClientArgs
from pyFMG import fortimgr
from pprint import pprint
from secrets import FG_HOST, FG_USER, FG_PASS, cp_host, cp_user, cp_pass
import logging

# https://community.checkpoint.com/t5/API-CLI-Discussion/Python-library-for-using-R80-management-server-APIs/td-p/40965

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename = "firewall.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("firewall")

adom_value='root'
pkg_value='default'

addrgrp=f'pm/config/adom/{adom_value}/obj/firewall/addrgrp'
fw_object=f'pm/config/adom/{adom_value}/obj/firewall/address'
services_obj=f'pm/config/adom/{adom_value}/obj/firewall/service/custom'
service_group=f'pm/config/adom/{adom_value}/obj/firewall/service/group'
fw_policy=f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy'

def main():
    api_server = cp_host
    username = cp_user
    domain = None # :param domain: [optional] The name, UID or IP-Address of the domain to login.

    if sys.stdin.isatty():
        password = cp_pass
    else:
        print("Attention! Your password will be shown on the screen!")
        password = input("Enter password: ")

    client_args = APIClientArgs(server=api_server)
    with APIClient(client_args) as client:
        
        if client.check_fingerprint() is False:
            print("Could not get the server's fingerprint - Check connectivity with the server.")
            exit(1)

        # login to server:
        login_res = client.login(username, password, domain=domain)
        logger.info(f"CheckPoint Login Status Code - {login_res.status_code}")
        if login_res.success is False:
            print("Login failed:\n{}".format(login_res.error_message))
            exit(1)

        #################################################################################
        #### CHECKPOINT API CALLS, USED IN BLOCKS BELOW, GROUPED HERE FOR VISIBILITY ####
        #################################################################################

        # networks = client.api_query('show-networks', details_level='full')
        # hosts = client.api_query('show-hosts', details_level='full')
        # groups = client.api_query('show-groups', details_level='full')  # Use api_query for lists when longer than 50 items, any list will work
        # wildcards = client.api_query("show-wildcards", details_level='full')
        # address_ranges = client.api_query("show-address-ranges", details_level='full')
        # dynamic_objects = client.api_query("show-dynamic-objects", details_level='full')
        # tcp_services = client.api_query('show-services-tcp', details_level='full')
        # udp_services = client.api_query('show-services-udp', details_level='full')
        # icmp_services = client.api_query('show-services-icmp', details_level='full')
        # sctp_services = client.api_query('show-services-sctp', details_level='full')
        # other_services = client.api_query('show-services-other', details_level='full')
        # show_access_rb = client.api_query('show-access-rulebase', details_level='full')


#######################
####  FORTIMANAGER ####
#######################

        fmg_instance = fortimgr.FortiManager(FG_HOST, FG_USER, FG_PASS, debug=False, use_ssl=True, disable_request_warnings=True, timeout=100)
        fmg_login = fmg_instance.login()
        logger.info(f"FortiManager Login Status: {fmg_login[1]['status']['message']}")


        ####################################
        ####  ADD FIREWALL HOST OBJECT  ####
        ####################################

        # hosts = client.api_query('show-hosts', details_level='full')
        
        # for host in hosts.data:

        #     name = host['name']
        #     address = host['ipv4-address']
        #     comment = host['comments']
        #     data = {
        #                 'allow-routing': 0,
        #                 'associated-interface': 'any',
        #                 'name': name,
        #                 'subnet': [address, '255.255.255.255'],
        #                 'type': 0,
        #                 'comment': comment
        #             }
        #     add_object = fmg_instance.add(fw_object, **data)

            # if add_object[0] == -6:
            #     logger.error(f"Error Adding Object {add_object[1]['status']['message']}")
            # elif add_object[0] == -2:
            #     logger.warning(f"{add_object[1]['status']['message']}, Duplicate Object Named: \'{data['name']}\' NOT Created!")
            # elif add_object[0] == 0:
            #     logger.info(f"Object \'{add_object[1]['name']}\' Created Successfuly")

        #######################################
        ####  ADD FIREWALL NETWORK OBJECT  ####
        #######################################

        # networks = client.api_query('show-networks', details_level='full')

        # for network in networks.data:
        #     if 'subnet4' in network: # Only get ipv4 objects

        #         name = network['name']
        #         address = network['subnet4']
        #         mask = network['subnet-mask']
        #         comment = network['comments']
        #         data = {
        #                     'allow-routing': 0,
        #                     'associated-interface': 'any',
        #                     'name': name,
        #                     'subnet': [address, mask],
        #                     'type': 0,
        #                     'comment': comment
        #                 }
        #         add_object = fmg_instance.add(fw_object, **data)

        #         # print(add_object)
        #         if add_object[0] == -6:
        #             logger.error(f"Error Adding Object {add_object[1]['status']['message']}")
        #         elif add_object[0] == -2:
        #             logger.warning(f"{add_object[1]['status']['message']}, Duplicate Object Named: \'{data['name']}\' NOT Created!")
        #         elif add_object[0] == 0:
        #             logger.info(f"Object \'{add_object[1]['name']}\' Created Successfuly")
        #     else:
        #         continue


        #################################
        ####  ADD IPV4 GROUP OBJECT  ####
        #################################

        # groups = client.api_query('show-groups', details_level='full')

        # for group in groups.data:
        #     grp_members = []
        #     grp_name = group['name']
        #     comment = group['comments']

        #     specific_group = client.api_call('show-group', {'name': grp_name})
        #     members = specific_group.data['members']
        #     for member in members:
        #         grp_members.append(member['name'])

        #     ipv4_grp_data = {'allow-routing': 0,
        #                     'color': 0,
        #                     'comment': comment,
        #                     'dynamic_mapping': None,
        #                     'exclude': 0,
        #                     # 'exclude-member': [],
        #                     'member': grp_members,
        #                     'name': grp_name,
        #                     'tagging': None,
        #                     'visibility': 1
        #                     }
        #     add_ipv4_grp = fmg_instance.add(addrgrp, **ipv4_grp_data)
        #     if add_ipv4_grp[0] == -6:
        #         logger.error(f"Error Adding Group Object {add_ipv4_grp[1]['status']['message']}")
        #     elif add_ipv4_grp[0] == -2:
        #         logger.warning(f"{add_ipv4_grp[1]['status']['message']}, Duplicate Group Object Named: \'{grp_name}\' NOT Created!")
        #     elif add_ipv4_grp[0] == 0:
        #         logger.info(f"Group Object \'{add_ipv4_grp[1]['name']}\' Created Successfuly")

        ##############################
        ####  TCP SERVICE OBJECT  ####
        ##############################

        # tcp_services = client.api_query('show-services-tcp', details_level='full')

        # for service in tcp_services.data:
        #     comment = service['comments']
        #     name = service['name']
        #     tcp_port = service['port']


        #     tcp_data = {
        #         'app-category': [],
        #         'app-service-type': 0,
        #         'application': [],
        #         'category': [],
        #         'check-reset-range': 3,
        #         'color': 0,
        #         'comment': comment,
        #         'helper': 1,
        #         'iprange': '0.0.0.0',
        #         'name': name,
        #         #'obj seq': 28,
        #         'protocol': 5,
        #         'proxy': 0,
        #         'sctp-portrange': [],
        #         'session-ttl': '0',
        #         'tcp-halfclose-timer': 0,
        #         'tcp-halfopen-timer': 0,
        #         'tcp-portrange': [tcp_port],
        #         'tcp-timewait-timer': 0,
        #         'udp-idle-timer': 0,
        #         'udp-portrange': [],
        #         'visibility': 1}

        #     add_tcp_svc = fmg_instance.add(services_obj, **tcp_data)
        #     if add_tcp_svc[0] == -6:
        #         logger.error(f"Error Adding Group Object {add_tcp_svc[1]['status']['message']}")
        #     elif add_tcp_svc[0] == -2:
        #         logger.warning(f"{add_tcp_svc[1]['status']['message']}, Duplicate Group Object Named: \'{name}\' NOT Created!")
        #     elif add_tcp_svc[0] == 0:
        #         logger.info(f"Group Object \'{add_tcp_svc[1]['name']}\' Created Successfuly")
        #     else:
        #         logger.info(f"Error Creating SVC Object \'{name}\' {add_tcp_svc[1]['status']['message']}")

            # '''
            # Mostly works but a couple services errored:
            #     'unknown_protocol_tcp'
            #     'tcp-high-ports'
            # '''

        ##############################
        ####  UDP SERVICE OBJECT  ####
        ##############################

        # udp_services = client.api_query('show-services-udp', details_level='full')

        # for udp_service in udp_services.data:
        #     comment = udp_service['comments']
        #     name = udp_service['name']
        #     udp_port = udp_service['port']


        #     udp_data = {
        #         'app-category': [],
        #         'app-service-type': 0,
        #         'application': [],
        #         'category': [],
        #         'check-reset-range': 3,
        #         'color': 0,
        #         'comment': comment,
        #         'helper': 1,
        #         'iprange': '0.0.0.0',
        #         'name': name,
        #         'protocol': 5,
        #         'proxy': 0,
        #         'sctp-portrange': [],
        #         'session-ttl': '0',
        #         'tcp-halfclose-timer': 0,
        #         'tcp-halfopen-timer': 0,
        #         'tcp-portrange': [],
        #         'tcp-timewait-timer': 0,
        #         'udp-idle-timer': 0,
        #         'udp-portrange': [udp_port],
        #         'visibility': 1}

        #     add_udp_svc = fmg_instance.add(services_obj, **udp_data)
        #     if add_udp_svc[0] == -6:
        #         logger.error(f"Error Adding Group Object {add_udp_svc[1]['status']['message']}")
        #     elif add_udp_svc[0] == -2:
        #         logger.warning(f"{add_udp_svc[1]['status']['message']}, Duplicate Group Object Named: \'{name}\' NOT Created!")
        #     elif add_udp_svc[0] == 0:
        #         logger.info(f"Group Object \'{add_udp_svc[1]['name']}\' Created Successfuly")
        #     else:
        #         logger.info(f"Error Creating SVC Object \'{name}\' {add_udp_svc[1]['status']['message']}")

            # '''
            # Mostly works but a couple services errored:
            #     'unknown_protocol_udp'
            #     'udp-high-ports'
            # '''


        ###############################
        ####  ICMP SERVICE OBJECT  ####
        ###############################

        ####  NOT TESTED ####

        # icmp_services = client.api_query('show-services-icmp', details_level='full')

        # for icmp_service in icmp_services.data:
        #     comment = icmp_service['comments']
        #     name = icmp_service['name']
        #     icmp_port = icmp_service['port']


        #     icmp_data = {
        #         'app-category': [],
        #         'app-service-type': 0,
        #         'application': [],
        #         'category': [],
        #         'check-reset-range': 3,
        #         'color': 0,
        #         'comment': comment,
        #         'helper': 1,
        #         'iprange': '0.0.0.0',
        #         'name': name,
        #         'protocol': 5,
        #         'proxy': 0,
        #         'sctp-portrange': [],
        #         'session-ttl': '0',
        #         'tcp-halfclose-timer': 0,
        #         'tcp-halfopen-timer': 0,
        #         'tcp-portrange': [],
        #         'tcp-timewait-timer': 0,
        #         'udp-idle-timer': 0,
        #         'udp-portrange': [icmp_port],
        #         'visibility': 1}

        #     add_icmp_svc = fmg_instance.add(services_obj, **icmp_data)
        #     if add_icmp_svc[0] == -6:
        #         logger.error(f"Error Adding Group Object {add_icmp_svc[1]['status']['message']}")
        #     elif add_icmp_svc[0] == -2:
        #         logger.warning(f"{add_icmp_svc[1]['status']['message']}, Duplicate Group Object Named: \'{name}\' NOT Created!")
        #     elif add_icmp_svc[0] == 0:
        #         logger.info(f"Group Object \'{add_icmp_svc[1]['name']}\' Created Successfuly")
        #     else:
        #         logger.info(f"Error Creating SVC Object \'{name}\' {add_icmp_svc[1]['status']['message']}")



        ####################################
        ####  ADD SERVICE GROUP OBJECT  ####
        ####################################

        svc_grps = client.api_query('show-service-groups', details_level='full')
        # specific_svc_group = client.api_call('show-service-group', {'name': 'AOL_Messenger'})
        # print(specific_svc_group)
        

        for svc_grp in svc_grps.data:
            svc_grp_members = []
            svc_grp_name = svc_grp['name']
            svc_grp_comment = svc_grp['comments']

            specific_svc_group = client.api_call('show-service-group', {'name': svc_grp_name})
            members = specific_svc_group.data['members']
            for member in members:
                svc_grp_members.append(member['name'])

            svc_grp_data = {'color': 0,
                            'comment': svc_grp_comment,
                            'member': svc_grp_members,
                            'name': svc_grp_name,
                            'proxy': 0
                            }
            add_svc_grp = fmg_instance.add(service_group, **svc_grp_data)
            if add_svc_grp[0] == -6:
                logger.error(f"Error Adding Service Group Object {add_svc_grp[1]['status']['message']}")
            elif add_svc_grp[0] == -2:
                logger.warning(f"{add_svc_grp[1]['status']['message']}, Duplicate Service Group Object Named: \'{svc_grp_name}\' NOT Created!")
            elif add_svc_grp[0] == 0:
                logger.info(f"Service Group Object \'{add_svc_grp[1]['name']}\' Created Successfuly")
            else:
                logger.error(f"Error Creating Service Group Object \'{svc_grp_name}\' {add_svc_grp}") #[1]['status']['message']



        fmg_instance.logout()

if __name__ == "__main__":
    main()
