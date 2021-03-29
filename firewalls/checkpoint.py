from __future__ import print_function
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from cpapi import APIClient, APIClientArgs
from pprint import pprint

cp_host=''
cp_user=''
cp_pass=''

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
        

        # The API client, would look for the server's certificate SHA1 fingerprint in a file.
        # If the fingerprint is not found on the file, it will ask the user if he accepts the server's fingerprint.
        # In case the user does not accept the fingerprint, exit the program.
        if client.check_fingerprint() is False:
            print("Could not get the server's fingerprint - Check connectivity with the server.")
            exit(1)

        # login to server:
        login_res = client.login(username, password)

        if login_res.success is False:
            print("Login failed:\n{}".format(login_res.error_message))
            exit(1)

        # add a rule to the top of the "Network" layer
        # rule_name = input("Enter the name of the access rule: ")
        # add_rule_response = client.api_call("add-access-rule",
        #                                     {"name": rule_name, "layer": "Network", "position": "top"})

        # all_groups_obj = client.api_query('show-groups', details_level='full')
        # print(all_groups_obj)
        # for grp in all_groups_obj.data:
        #     print(grp['name'])


        # for group in all_groups_obj.data:
        #     grp_members = []
        #     grp_name = group['name']
        #     specific_group = client.api_call('show-group', {'name': grp_name})

        #     comment = specific_group.data['comments']
        #     members = specific_group.data['members']
        #     print(comment)


        # specific_group = client.api_call('show-group', {'name': 'g-Office'})
        # members = specific_group.data['members']
        # print(members)
        
        # tcp_services = client.api_query('show-services-tcp', details_level='full')
        # udp_services = client.api_query('show-services-udp', details_level='full')
        # icmp_services = client.api_query('show-services-icmp', details_level='full')
        # sctp_services = client.api_query('show-services-sctp', details_level='full')
        # other_services = client.api_query('show-services-other', details_level='full')
        # # pprint(f"TCP:\n{tcp_services.data[0]}, \nUDP:\n{udp_services.data[0]}, \nICMP:\n{icmp_services.data[0]}, \nSCTP:\n{sctp_services.data[0]}, \nOTHER:\n{other_services.data[0]}")
        # print("TCP\n")
        # pprint(tcp_services.data[0])
        # print("UDP\n")
        # pprint(udp_services.data[0])
        # print("ICMP\n")
        # pprint(icmp_services.data[0])
        # # print("SCTP\n")
        # # pprint(f"SCTP:\n{sctp_services.data[0]}")
        # print("OTHER\n")
        # pprint(other_services.data[0])
        # # pprint(tcp_services.data[0])


        # specific_tcp_svc = client.api_call('show-service-tcp', {'name': 'Napster_Client_6600-6699'})
        # pprint(specific_tcp_svc)

        # svc_grps = client.api_query('show-service-groups', details_level='full')
        # print(svc_grps)
        # for group in svc_grps.data:
        #     print(group['name'])
        # specific_svc_group = client.api_call('show-service-group', {'name': 'AOL_Messenger'})
        # print(specific_svc_group)
                # grp_members.append(member['name'])
        # specific_group = client.api_call('show-group', {'name': 'g-Other'})
        # members=specific_group.data['members']
        # pprint(members)
        # for item in members:
        #     print(item['name'])

        show_access_rb=client.api_query('show-access-rulebase', details_level='full')
        pprint(show_access_rb)


        # networks = client.api_query('show-networks')
        # for network in networks.data:
        #     pprint(network['subnet4'])
        # grp_members = []
        # # pprint(specific_group)
        # members=specific_group.data['members']
        # # pprint(members)
        # for member in members:
        #     grp_members.append(member['name'])
        # print(grp_members)

        
        # if add_rule_response.success:

        #     print("The rule: '{}' has been added successfully".format(rule_name))

        #     # publish the result
        #     publish_res = client.api_call("publish", {})
        #     if publish_res.success:
        #         print("The changes were published successfully.")
        #     else:
        #         print("Failed to publish the changes.")
        # else:
        #     print("Failed to add the access-rule: '{}', Error:\n{}".format(rule_name, add_rule_response.error_message))


if __name__ == "__main__":
    main()
