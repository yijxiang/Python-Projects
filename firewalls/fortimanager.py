from os import getpgrp
from pyFMG import fortimgr
from pprint import pprint
from secrets import FG_HOST, FG_USER, FG_PASS
import logging

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename = "firewall.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("firewall")

# addrgrp = 'pm/config/global/obj/firewall/addrgrp'
addrgrp = 'pm/config/adom/root/obj/firewall/addrgrp'
fw_object = 'pm/config/adom/root/obj/firewall/address'

# with fortimgr.FortiManager('53.220.248.105', 'admin', 'admin', debug=True, use_ssl=False, disable_request_warnings=True, timeout=100) as fmg_instance:
#     customers = fmg_instance.get('')
#     print(customers)

fmg_instance = fortimgr.FortiManager(FG_HOST, FG_USER, FG_PASS, debug=False, use_ssl=True, disable_request_warnings=True, timeout=100)
fmg_login = fmg_instance.login()
logger.info(f"FortiManager Login Status: {fmg_login[1]['status']['message']}")

# get_objects = fmg_instance.get('pm/config/adom/root/obj/firewall/address')
# # get_addrgrp = fmg_instance.get(addrgrp)
# pprint(get_objects)
# get_services = fmg_instance.get('pm/config/adom/root/obj/firewall/service/custom')
# specific_svc_grp = fmg_instance.get('pm/config/adom/root/obj/firewall/service/group', filter=["name", "==", "Email Access"])

# pprint(specific_svc_grp)
# for service in get_services[1]:
#     print(service['name'], service['protocol'])
# put_something = fmg_instance.add('pm/config/adom/{adom}/obj/firewall/address'.format(adom="root"), allow__routing=0, associated__interface='any', name='add_obj_name2', subnet=["192.168.40.0", "255.255.255.0"], type=0, comment='API address obj addition')

# commit = fmg_instance.commit_changes("root")
# print(commit)
'''
protocol values
1 = ICMP
2 = IP
5 = TCP/UDP/SCTP
6 = ICMP6
11 = ALL

'''

# pprint(get_something)

# for item in get_something[1]:
#     if item['type'] == 0:
#         print(item['name'], item['subnet'])
#     elif item['type'] == 2:
#         print(item['name'], item['fqdn'])

###############################
####  ADD FIREWALL OBJECT  ####
###############################

# data = {
#             'allow-routing': 0,
#             'associated-interface': 'any',
#             'name': 'test_addr_object3_LU',
#             'subnet': ['10.1.3.0', '255.255.255.255'],
#             'type': 0,
#             'comment': 'API Testing'
#         }
# add_object = fmg_instance.add(fw_object, **data)

# # print(add_object)
# if add_object[0] == -6:
#     logger.error(f"Error adding object {add_object[1]['status']['message']}")
# elif add_object[0] == -2:
#     logger.warning(f"{add_object[1]['status']['message']}, Duplicate Object Named: \'{data['name']}\' NOT Created!")
# elif add_object[0] == 0:
#     logger.info(f"Object \'{add_object[1]['name']}\' Created Successfuly")

#################################
####  ADD IPv4 Group OBJECT  ####
#################################

# ipv4_grp_data = {'allow-routing': 0,
#                 'color': 0,
#                 'comment': 'Made With Python',
#                 'dynamic_mapping': None,
#                 'exclude': 0,
#                 # 'exclude-member': [],
#                 'member': ['test_addr_object_LU',
#                             'test_addr_object2_LU',
#                             'test_addr_object3_LU'
#                             ],
#                 'name': 'LU_Test_Group',
#                 'tagging': None,
#                 'visibility': 1
#                 }
# add_ipv4_grp = fmg_instance.add(addrgrp, **ipv4_grp_data)
# pprint(add_ipv4_grp)


####  ADD RULE  ####

adom_value = 'root'
pkg_value = 'test'
policy_name = ''
fw_policy = f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy'


rule_data = {
            "action": "accept",
            "comments": "api_test",
            "dstaddr": ["all"],
            "dstintf": ["any"],
            # 'inspection-mode': 'flow',
            "logtraffic": "disable",
            "name": "API_Test",
            # 'nat': 'disable',
            # 'obj seq': 3,
            # 'policyid': 2,
            "schedule": ["always"],
            "service": ["ALL"],
            "srcaddr": ["all"],
            "srcintf": ["any"],
            "status": "enable"
            # 'users': [],
        }


# get_policy = fmg_instance.get(f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy') #WORKS, GETS FULL POLICY
# pprint(get_policy)
# get_policy = fmg_instance.get(f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy/2') # WORKS, GET SPECIFIC RULE IN POLICY
# pprint(get_policy)
# get_policy = fmg_instance.get(f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/interface-policy') # no interface policies exist
# pprint(get_policy)

add_rule = fmg_instance.add(f'pm/config/adom/{adom_value}/pkg/test/firewall/policy', **rule_data)
print(add_rule)
# get_pkgs = fmg_instance.get('pm/pkg/adom/root', data={})
# print(get_pkgs)
# get_pkg = fmg_instance.get('pm/pkg/adom/root/default', data={})
# print(get_pkg)

fmg_logout = fmg_instance.logout()