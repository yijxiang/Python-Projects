from secrets import nb_token, nb_url
import pynetbox
import requests
from tqdm import tqdm

session = requests.Session()
session.verify = False
requests.packages.urllib3.disable_warnings()
nb = pynetbox.api(url=nb_url, token=nb_token)
nb.http_session = session

try:
    print('Collecting Devices From Netbox. This may take a few minutes.')
    aps = nb.dcim.devices.filter(role='access-point')

except:
    e = pynetbox.RequestError
    print(e)

for ap in tqdm(aps):
    ap_ints = nb.dcim.interfaces.filter(device=ap)
    for interface in ap_ints:
        if interface.name == '0':
            int_dict = dict(
            name='GigabitEthernet0',    
            )
            b = nb.dcim.interfaces.get(interface.id)
            b.update(int_dict)
            #print(f"Updating interface name for {ap}.")
        #else:
            #print(f"Interface name for {ap} already updated.")