aaa = r'''
sudo apt install  firewalld

sudo systemctl start firewalld


sudo systemctl enable firewalld

sudo firewall-cmd --zone=public --add-port=777/tcp --permanent
sudo firewall-cmd --zone=public --add-port=777/udp --permanent
sudo firewall-cmd --reload

sudo firewall-cmd --zone=public --list-ports


sudo firewall-cmd --zone=public --add-port=7778/tcp --permanent
sudo firewall-cmd --zone=public --add-port=7778/udp --permanent

sudo firewall-cmd --zone=public --add-port=7777/tcp --permanent

sudo firewall-cmd --zone=public --add-port=7777/udp --permanent


/usr/local/conda/bin/jupyter-lab



sudo firewall-cmd --zone=public --add-port=8501/tcp --permanent

sudo firewall-cmd --zone=public --add-port=8501/udp --permanent
8501



'''
