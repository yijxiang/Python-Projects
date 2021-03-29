import requests, datetime, smtplib
from PIL import Image
from io import BytesIO
from fpdf import FPDF
from rich import print as rprint
from secrets import librenms_token, librenms_url
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# GETS GRAPH IMAGE
# Gi0/0/5 24 hour
url = f'{librenms_url}devices/14/ports/Gi0%2F0%2F5/port_bits' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token, 'Content-Type': 'image/png'}
r = requests.get(url, headers=headers)
i = Image.open(BytesIO(r.content))
i.save('test2.png')

# Gi0/0/5 7 day
url = f'{librenms_url}devices/14/ports/Gi0%2F0%2F5/port_bits?from=-604800&to=-300' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token, 'Content-Type': 'image/png'}
r = requests.get(url, headers=headers)
i = Image.open(BytesIO(r.content))
i.save('test3.png')

# Gi0/0/5 port details
url = f'{librenms_url}ports/18234' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token}
r = requests.get(url, headers=headers)
r = r.json()
int_name = r['port'][0]['ifDescr']
int_desc = r['port'][0]['ifAlias']

# Te2/1/7 24 hour
url = f'{librenms_url}devices/28/ports/Te2%2F1%2F7/port_bits' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token, 'Content-Type': 'image/png'}
r = requests.get(url, headers=headers)
i = Image.open(BytesIO(r.content))
i.save('test4.png')

# Te2/1/7 7 day
url = f'{librenms_url}devices/28/ports/Te2%2F1%2F7/port_bits?from=-604800&to=-300' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token, 'Content-Type': 'image/png'}
r = requests.get(url, headers=headers)
i = Image.open(BytesIO(r.content))
i.save('test5.png')

# Te2/1/7 port details
url = f'{librenms_url}ports/1315' # Device Name or LibreNMS ID Number.
headers = {'X-Auth-Token': librenms_token}
r = requests.get(url, headers=headers)
r = r.json()
int_name2 = r['port'][0]['ifDescr']
int_desc2 = r['port'][0]['ifAlias']

filetime1 = datetime.datetime.now().strftime("%m.%d.%Y-%I.%M.%S%p") # File timestamp example 10.19.2020-11.59.43AM
filename = "Circuit_Utilization_"+filetime1+".pdf"

# CREATE PDF!

class PDF(FPDF):
    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')
pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_xy(0, 0)
pdf.set_font('arial', 'B', 12)
pdf.cell(60, 10, "", 0, 1, 'A')
pdf.cell(100, 10, "RTR-01 Internet Utilization", 0, 1, 'A')
pdf.set_font('arial', "", 10)
pdf.cell(85, 5, f"Port: {int_name}", 0, 1, 'A')
pdf.cell(85, 5, f"Circuit: {int_desc}", 0, 3, 'A')
pdf.ln(5)
pdf.set_font('arial', "", 8)
pdf.cell(40, 2, "Last 24 Hours", 0, 1, 'A')
pdf.image('test2.png', x = None, y = None, w = 185, h = 0, type = '', link = 'http://libnms/device/device=14/tab=port/port=18234')
pdf.ln(5)
pdf.cell(40, 2, "Last 7 Days", 0, 1, 'A')
pdf.image('test3.png', x = None, y = None, w = 185, h = 0, type = '', link = 'http://libnms/device/device=14/tab=port/port=18234')
#PAGE 2 BEGINS
pdf.add_page()
pdf.set_font('arial', 'B', 12)
pdf.cell(60, 10, "", 0, 1, 'A')
pdf.cell(100, 10, "RTR-01 MAN Utilization", 0, 1, 'A')
pdf.set_font('arial', "", 10)
pdf.cell(85, 5, f"Port: {int_name2}", 0, 1, 'A')
pdf.cell(85, 5, f"Circuit: {int_desc2}", 0, 3, 'A')
pdf.ln(5)
pdf.set_font('arial', "", 8)
pdf.cell(40, 2, "Last 24 Hours", 0, 1, 'A')
pdf.image('test4.png', x = None, y = None, w = 185, h = 0, type = '', link = 'http://libnms/device/device=14/tab=port/port=1315')
pdf.ln(5)
pdf.cell(40, 2, "Last 7 Days", 0, 1, 'A')
pdf.image('test5.png', x = None, y = None, w = 185, h = 0, type = '', link = 'http://libnms/device/device=14/tab=port/port=1315')
pdf.output(f'/mnt/c/wsl_outputs/{filename}', 'F')
rprint(f"\nReport {filename} Generated")

# Send report as email
SourcePathName  = '/mnt/c/wsl_outputs/' + filename 
recipients = ['EMAIL1@EMAIL.COM', 'EMAIL2@EMAIL.COM']
msg = MIMEMultipart()
msg['From'] = 'LibreNMS_Reports@DOMAIN.com'
msg['To'] = ", ".join(recipients)
msg['Subject'] = 'Circuit Utilization Report'
body = ('Hello,<br><br>The current circuit utilization report is attached. '
'Have a great day!<br><br>'
'Thank you,<br><br>'
'SIGNATURE')

msg.attach(MIMEText(body, 'html')) #or use text and change body formating tags
## ATTACHMENT PART OF THE CODE IS HERE
attachment = open(SourcePathName, 'rb')
part = MIMEBase('application', "octet-stream")
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', f"attachment; filename={filename}")
msg.attach(part)
server = smtplib.SMTP("SMTP.DOMAIN.COM")  ### put your relevant SMTP here   #('smtp.office365.com', 587)
server.send_message(msg)
print('\nSending Email to '+ msg['To']+"\n")
server.quit()