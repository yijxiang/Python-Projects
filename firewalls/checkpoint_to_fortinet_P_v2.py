from __future__ import print_function
import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpapi import APIClient, APIClientArgs
from pyFMG import fortimgr
from pprint import pprint
from secrets import FG_HOST, FG_USER, FG_PASS, cp_host, cp_user, cp_pass
from tqdm import tqdm
from rich.console import Console
from rich.table import Table

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename = "firewallH.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("firewall")

table = Table(title="Firewall Rules", show_lines=True)
table.add_column("Row #", justify="center", style="cyan", no_wrap=True)
table.add_column("Name", justify="left", style="magenta")
table.add_column("Source", justify="left", style="yellow")
table.add_column("Destinaion", justify="left", style="green")
table.add_column("Service", justify="left", style="blue")
table.add_column("Action", justify="left", style="red")
table.add_column("Comment", justify="left", style="magenta")

adom_value='' #Target FortiManager ADOM 
pkg_value=''
rule_base_name=''

fw_object=f'pm/config/adom/{adom_value}/obj/firewall/address'
fw_policy=f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy'

def main():
    api_server = cp_host
    username = cp_user

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

        # LOGIN TO CHECKPOINT SERVER:
        login_res = client.login(username, password) # Standalone deployment

        logger.info(f"CheckPoint Login Status Code - {login_res.status_code}")
        if login_res.success is False:
            print("Login failed:\n{}".format(login_res.error_message))
            exit(1)

        # LOGIN TO FORTIMANAGER SERVER:
        fmg_instance = fortimgr.FortiManager(FG_HOST, FG_USER, FG_PASS, debug=False, use_ssl=True, disable_request_warnings=True, timeout=100)
        fmg_login = fmg_instance.login()
        logger.info(f"FortiManager Login Status: {fmg_login[1]['status']['message']}")

        policy = client.api_call('show-access-rulebase', payload={'name': rule_base_name}) # WORKING!!!!!
        pprint(policy)
        print("\n")
        for item in tqdm(policy.data['rulebase'], desc="Moving FW Rules"):

            rule_num = item['rule-number']
            rule_name = item['name']
            rule_comment = item['comments']
            source_list = []
            dest_list = []
            service_list = []

            for a in policy.data['objects-dictionary']:

                for source in item['source']:
                    if source == a['uid']:
                        src_name = a['name']
                        if src_name == 'Any':
                            src_name = 'all'
                            source_list.append(src_name)
                        else:
                            source_list.append(src_name)
                
                for dest in item['destination']:
                    if dest == a['uid']:
                        dest_name = a['name']
                        if dest_name == 'Any':
                            dest_name = 'all'
                            dest_list.append(dest_name)
                        else:
                            dest_list.append(dest_name)

                for service in item['service']:
                    if service == a['uid'] :
                        svc_name = a['name']
                        if svc_name == 'Any':
                            svc_name = 'ALL'
                        service_list.append(svc_name)

                if item['action'] == a['uid']:
                    action_name = a['name']
                    if action_name == 'Accept':
                        action_name = 'accept'
                    elif action_name == 'Drop':
                        action_name = 'deny'

            table.add_row(str(rule_num), rule_name, str(source_list), str(dest_list), str(service_list), action_name, rule_comment)

        print("\n")
        console = Console()
        console.print(table)
        print("\n")     


        #############################
        ####  ADD FIREWALL Rule  ####
        #############################

        #     data = {
        #     "action": action_name,
        #     "comments": rule_comment,
        #     "dstaddr": dest_list, #["all"],
        #     "dstintf": ["any"],
        #     "logtraffic": "disable",
        #     "name": rule_name,
        #     "schedule": ["always"],
        #     "service": service_list, #["ALL"],
        #     "srcaddr": source_list, #["all"],
        #     "srcintf": ["any"],
        #     "status": "enable"
        # }

        #     add_rule=fmg_instance.add(fw_policy, **data)

        #     if add_rule[0] == -10131:
        #         logger.error(f"One or more group members of policy: \'{rule_name}\' does not exist!") 
        #     elif add_rule[0] == -9998:
        #         logger.error(f"{add_rule[1]['status']['message']}, Duplicate Rule Named: \'{rule_name}\' NOT Created!")
        #     elif add_rule[0] == 0:
        #         logger.info(f"Rule #: \'{add_rule[1]['policyid']}\', Name: \'{rule_name}\' Created Successfuly")
        #     else:
        #         logger.error("Some other Error Occured.")

        # fmg_instance.logout()

if __name__ == "__main__":
    main()