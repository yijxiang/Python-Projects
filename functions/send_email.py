import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
    
def send_email(sender, to, cc, subject, body, body_format, file_path, file_list):
    """
    From, To and Cc need to be a comma separated string
    i.e 'username1@email.com, username2@email.com'
    Attachment variable needs to include relative path to file
    Body can be plain text or html. Format accordingly and match body_format variable
    Cc, filepath, file_list can be blank i.e. Cc=''
    """

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Cc'] = cc
    msg['Subject'] = subject
    text = body

    part1 = MIMEText(text, body_format)
    msg.attach(part1)

    ## ATTACHMENT PART OF THE CODE IS HERE
    for file in file_list:

        SourcePathName  = file_path + file 
        attachment = open(SourcePathName, 'rb')
        part = MIMEBase('application', "octet-stream")
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename={file}")
        msg.attach(part)

    server = smtplib.SMTP("mail.us164.corpintra.net")
    server.send_message(msg)
    server.quit()

"""
USAGE EXAMPLE:

from send_email import send_email

sender='FIRST.LAST@email.com'
to='FIRST.LAST@email.com'      #i.e 'FIRST.LAST@email.com, FIRST.LAST@email.com'
cc=''                            #'FIRST.LAST@email.com, FIRST.LAST@email.com'
subject='Test'                   #EMAIL SUBJECT
body='test'                      #EMAIL BODY TEXT
body_format='plain'              #OR USE 'html'
file_path=''                     #'./ENTER/PATH/IF/REQUIRED/'
file_list=''                     #['test_file1.txt', 'test_file2.txt']

email=send_email(sender, to, cc, subject, body, body_format, file_path, file_list)
"""