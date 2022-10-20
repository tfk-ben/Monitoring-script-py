import requests #lib to send http request
import os       #lib to get env vars
import yagmail  #lib to send mail
import schedule #lib to schedule the script
import paramiko #lib to ssh to the server

import boto3    #lib to reboot the server
from botocore.exceptions import ClientError
import time




EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

ip=""           # ip address of the instance
user=""         # username of the instance
key=""          #path of the key
instanceid=""
container_id =""


def send_notification(email_msg):
    with yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD) as smtp:       
        smtp.send(EMAIL_ADDRESS,"App is Down",email_msg)  #smtp.send(receiver_email_adress,Subject,email_msg)



def restart_app(): 
    #to restart the app
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())#auto confirme Yes

    ssh.connect(hostname=ip,username=user,key_filename=key )   
    #ssh.connect(hostname='adress ip',username='user we want to use', password='password' or key_filename='path of key')

    stdout = ssh.exec_command(f"docker start container {container_id}") # stdin is input , stdout is output , stderr is erreur msg
                                                                        # this command will start the down container again

    #print(stdout.readlines()) # so we can see the output of the terminal 
    ssh.close()
    print('App restarted') 



def reboot_ec2_instance():
    ec2 = boto3.client('ec2')

    try:
        ec2.reboot_instances(InstanceIds=[instanceid], DryRun=True)
        print("instance rebooted")
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print("You don't have permission to reboot instances.")
            raise

    try:
        response = ec2.reboot_instances(InstanceIds=[instanceid], DryRun=False)
        print('Success', response)
    except ClientError as e:
        print('Error', e)





def monitor_app():
    try:    
        response = requests.get('https://www.google.com/') #url of the website
        if response.status_code == 200:
            print('app is runing')
        else:
            print('App down , fix it')
            mssg='error message {response.status_code} \n Fix the issue'
            send_notification(mssg)
            restart_app()

    except Exception as ex :
        mssg='Applicaltion not accessible  Fix the issue'
        send_notification(mssg)
        reboot_ec2_instance()
        time.sleep(100)
        restart_app()


#schedule.every().day.at("1:00")
#schedule.every().monday.at("12:00")
#schedule.every().hour

schedule.every(5).minutes.do(monitor_app)
while True:                   #to lanche the programme 
    schedule.run_pending()
