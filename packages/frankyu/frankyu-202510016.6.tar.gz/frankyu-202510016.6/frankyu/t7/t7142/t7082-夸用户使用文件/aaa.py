aaa = r'''
sudo usermod -aG kelly frank

exec su -l $USER

sudo chown -R kelly:kelly /home/kelly

sudo chmod -R 775 /home/kelly	

sudo setfacl -R -m u:frank:rwx /home/kelly

exec su -l $USER

'''
