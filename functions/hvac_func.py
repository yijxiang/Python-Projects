import hvac, requests

requests.packages.urllib3.disable_warnings()

#####################################################
#  CREATE NEW SECRET AND KEY VALUE PAIRS INSIDE IT  #
#####################################################
'''
WILL ALSO UPDATE OR ADD KV VALUES TO SECRET.
RUNNING AGAIN OR MAKING CHANGES WILL INCREMENT 
TO THE NEXT VERSION WITH V2 DATABASE.
'''

def create_secret1(un, pw, mount_point, path, key1, value1):  # Create Secret with 1 KV Pair
    client = hvac.Client(url='https://53.242.34.25:8200', verify=False)
    login_response = client.auth.radius.login(
        un, pw,
        use_token = True,
        mount_point = 'radius/config'
    )
    token = login_response['auth']['client_token']
    client = hvac.Client(url='https://53.242.34.25:8200', token=token, verify=False)

    secret_dict = {}
    secret_dict[key1] = value1
    create_response=client.secrets.kv.v2.create_or_update_secret(
    mount_point = mount_point,
    path = path,
    secret = secret_dict)
    return create_response


def create_secret2(un, pw, mount_point, path, key1, value1, key2, value2):  # Create Secret with 2 KV Pairs
    client = hvac.Client(url='https://53.242.34.25:8200', verify=False)
    login_response = client.auth.radius.login(
        un, pw,
        use_token = True,
        mount_point = 'radius/config'
    )
    token = login_response['auth']['client_token']
    client = hvac.Client(url='https://53.242.34.25:8200', token=token, verify=False)
    
    secret_dict = {}
    secret_dict[key1] = value1
    secret_dict[key2] = value2
    create_response=client.secrets.kv.v2.create_or_update_secret(
    mount_point = mount_point,
    path = path,
    secret = secret_dict)
    return create_response


#########################################
#  PATCH EXISTING SECRET KEYS OR VALUES #
#   WILL CREATE A NEW VERSION WITH V2   #
#########################################

def patch_secret(un, pw, mount_point, path, key1, value1):  
    client = hvac.Client(url='https://53.242.34.25:8200', verify=False)
    login_response = client.auth.radius.login(
        un, pw,
        use_token = True,
        mount_point = 'radius/config'
    )
    token = login_response['auth']['client_token']
    client = hvac.Client(url='https://53.242.34.25:8200', token=token, verify=False)
    secret_dict = {}
    secret_dict[key1] = value1
    patch=client.secrets.kv.v2.patch(
    mount_point=mount_point,
    path=path,
    secret=secret_dict)
    return patch


#################################################
#   READ SECRET AND KEY VALUE PAIRS INSIDE IT   #
#################################################

def retrieve_secret(un, pw, mount_point, path):
    client = hvac.Client(url='https://53.242.34.25:8200', verify=False)
    login_response = client.auth.radius.login(
        un, pw,
        use_token = True,
        mount_point = 'radius/config'
    )
    token = login_response['auth']['client_token']
    client = hvac.Client(url='https://53.242.34.25:8200', token=token, verify=False)
    read_response = client.secrets.kv.read_secret_version(mount_point=mount_point, path=path)
    return read_response['data']['data']


#############################################
#   DELETE SECRET AND ALL KEY VALUE PAIRS   #
#############################################

def delete_secret(un, pw, mount_point, path):
    client = hvac.Client(url='https://53.242.34.25:8200', verify=False)
    login_response = client.auth.radius.login(
        un, pw,
        use_token = True,
        mount_point = 'radius/config'
    )
    token = login_response['auth']['client_token']
    client = hvac.Client(url='https://53.242.34.25:8200', token=token, verify=False)
    delete_response = client.secrets.kv.v2.delete_metadata_and_all_versions(mount_point=mount_point, path=path)
    return delete_response


##########################################
#   UPDATE METADATA FOR SECRETS ENGINE   #
##########################################

### read
# secrets_path_metadata = client.secrets.kv.v2.read_secret_metadata(
#     mount_point='',
#     path=''
# )
# pprint(secrets_path_metadata)

### update
# client.secrets.kv.v2.update_metadata(
#     mount_point='',
#     path='',
#     max_versions=20
# )