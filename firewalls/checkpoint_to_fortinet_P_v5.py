from __future__ import print_function
import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpapi import APIClient, APIClientArgs
from pyFMG import fortimgr
from pprint import pprint
from secrets import FMG_HOST, FMG_USER, FMG_PASS, pcp_host, pcp_user, pcp_pass
from tqdm import tqdm
from rich.console import Console
from rich.table import Table

logging.basicConfig(format='[%(levelname)s] %(asctime)s %(message)s', level=logging.INFO, 
filename = "firewallH.log", datefmt='%m/%d/%Y - %H:%M:%S')
logger = logging.getLogger("firewall")

table = Table(title="Firewall Rules", show_lines=True)
table.add_column("Section Name", justify="left", style="white")
table.add_column("Row #", justify="center", style="cyan", no_wrap=True)
table.add_column("Status", justify="center", style="blue")
table.add_column("Name", justify="left", style="magenta")
table.add_column("Source", justify="left", style="yellow")
table.add_column("Destinaion", justify="left", style="green")
table.add_column("Service", justify="left", style="blue")
table.add_column("Action", justify="left", style="red")
table.add_column("Comment", justify="left", style="magenta")

adom_value = '' #Target FortiManager ADOM 
pkg_value = ''
rule_base_name = ''
limit = '150'

fw_object = f'pm/config/adom/{adom_value}/obj/firewall/address'
fw_policy = f'pm/config/adom/{adom_value}/pkg/{pkg_value}/firewall/policy'

def main():
    api_server = pcp_host
    username = pcp_user
    domain = "" #Source Checkpoint  domain/CMA

    if sys.stdin.isatty():
        password = pcp_pass
    else:
        print("Attention! Your password will be shown on the screen!")
        password = input("Enter password: ")

    client_args = APIClientArgs(server=api_server)
    with APIClient(client_args) as client:
        
        if client.check_fingerprint() is False:
            print("Could not get the server's fingerprint - Check connectivity with the server.")
            exit(1)

        # LOGIN TO CHECKPOINT SERVER:
        #login_res = client.login(username, password) # Standalone deployment
        login_res = client.login(username, password, domain=domain) # MDS deployment

        logger.info(f"CheckPoint Login Status Code - {login_res.status_code}")
        if login_res.success is False:
            print("Login failed:\n{}".format(login_res.error_message))
            exit(1)

        # LOGIN TO FORTIMANAGER
        fmg_instance = fortimgr.FortiManager(FMG_HOST, FMG_USER, FMG_PASS, debug=False, use_ssl=True, disable_request_warnings=True, timeout=100)
        fmg_login = fmg_instance.login()
        logger.info(f"FortiManager Login Status: {fmg_login[1]['status']['message']}")

        # GET CHECKPOINT POLICY
        policy = client.api_call('show-access-rulebase', payload={'name': rule_base_name, 'limit': limit}) # USE API_CALL NOT API_QUERY
        #pprint(policy)
        
        # PARSE POLICY RESPONSE JSON AND ADAPT TO FORTINET FORMAT
        for section in tqdm(policy.data['rulebase'], desc="Sections"):
            section_name = section['name']
            table.add_row(section_name)

            for item in tqdm(section['rulebase'], desc=f"Moving Rules For Section {section_name}"): 
                rule_num = item['rule-number']
                rule_comment = item['comments']
                rule_log = item['track']['type']

                try: 
                    rule_name = item['name'][:35]
                except:
                    rule_name = ''    

                rule_status = item['enabled']
                if rule_status == True:
                    rule_status = 'enable'
                elif rule_status == False:
                    rule_status = 'disable'

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

                    if rule_log == a['uid']:
                        log_status = a['name']
                        if log_status == 'Log':
                            log_status = 'all'
                        elif log_status == 'None':
                            log_status = 'disable'        

                table.add_row("", str(rule_num), str(rule_status), rule_name, str(source_list), str(dest_list), str(service_list), action_name, rule_comment)

        # DISPLAY POLICY IN RICH TABLE TO VERIFY PROPER PARSING AND FORMATTING COMMENT OUT WHEN WRITING TO FMG
        # print("\n")
        # console = Console()
        # console.print(table)
        # print("\n")     


        #####################################
        ####  ADD FIREWALL RULES TO FMG  ####
        #####################################

                data = {
                "action": action_name,
                "comments": rule_comment,
                "dstaddr": dest_list, #["all"],
                "dstintf": ["any"],
                'global-label': section_name,
                "logtraffic": log_status,
                "name": rule_name,
                "schedule": ["always"],
                "service": service_list, #["ALL"],
                "srcaddr": source_list, #["all"],
                "srcintf": ["any"],
                "status": rule_status
                }

                add_rule = fmg_instance.add(fw_policy, **data)
                #print(add_rule)

                if add_rule[0] == -10131:
                    logger.error(f"Rule #: \'{rule_num}\', One or more group members of policy: \'{rule_name}\' does not exist!") 
                elif add_rule[0] == -9998:
                    logger.error(f"Rule #: \'{rule_num}\', Duplicate Rule Named: \'{rule_name}\' NOT Created!")
                elif add_rule[0] == 0:
                    logger.info(f"Rule #: \'{rule_num}\', Name: \'{rule_name}\' Created Successfuly")
                else:
                    logger.error(F"Some other Error Occured. {add_rule}")

        fmg_instance.logout()

if __name__ == "__main__":
    main()