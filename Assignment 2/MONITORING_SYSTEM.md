## Monitoring System

The monitoring system for the fleet of machines created in Assignment 2, will consist of Prometheus and Grafana.
Prometheus Node Exporter will be used to scrape data from all the machines, while Prometheus will serve as the central monitoring platform, collecting that scraped data. Prometheus Alert Manager will be configured to forward Prometheus alerts to a channel on a Team via a Microsoft Teams webhook. Grafana will be used to collect the Prometheus-gathered data in a rich and modern visualization format.

## Setup

On each machine the following commands need to be run to prepare for the
setup of Puppet, which will deploy the monitoring system and its components.

### Hostfile setup

- Create the `/etc/hosts` file on each machine.

```bash
sudo tee -a /etc/hosts << EOF
192.168.50.27 batcsg1-web.op.ac.nz batcsg1-web
192.168.50.26 batcsg1-app.op.ac.nz batcsg1-app
192.168.50.175 batcsg1-db.op.ac.nz batcsg1-db
EOF
```
### Key-based SSH setup

From your host add these following lines to your SSH config

```bash
tee -a ~/.ssh/config ~ << EOF
Host batcsg1-web
    HostName 202.49.242.203 # Floating IP
    User ubuntu
    IdentityFile ~/.ssh/batcsg1-keypair

Host batcsg1-app batcsg1-db
    HostName %h
    User ubuntu
    IdentityFile ~/.ssh/batcsg1-keypair
    ProxyJump batcsg1-web
EOF
```

### Install base packages

- Install required packages on the web server

```bash
ssh batcsg1-web # Run from the `sb-vm`
```

```bash
sudo apt update
sudo apt install -y iputils-ping git vim nano
```
- Install required packages on the `app` and `db` servers

```bash
ssh batcsg1-app # Run from the `sb-vm` in a second window


```bash
ssh batcsg1-db # Run from the `sb-vm` in a third window
```

- Run on the `eb`, `db` and `app` machines

```bash
sudo apt update
sudo apt install -y iputils-ping git vim nano
```

### Installing Puppet

- Install `puppetserver` and `puppet-agent` on `batcsg1-web`

```bash
wget https://apt.puppet.com/puppet8-release-jammy.deb
sudo dpkg -i puppet8-release-jammy.deb
sudo apt update
sudo apt install -y puppetserver puppet-agent
echo 'export PATH=$PATH:/opt/puppetlabs/bin' | sudo tee -a /etc/profile.d/puppet.sh
source /etc/profile.d/puppet.sh
echo 'Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/puppetlabs/bin"' | sudo tee /etc/sudoers.d/puppet
```

- Install `puppet-agent` on `batcsg1-db` and `batcsg1-app`


```bash
wget https://apt.puppet.com/puppet8-release-jammy.deb
sudo dpkg -i puppet8-release-jammy.deb
sudo apt update
sudo apt install -y puppet-agent
echo 'export PATH=$PATH:/opt/puppetlabs/bin' | sudo tee -a /etc/profile.d/puppet.sh
source /etc/profile.d/puppet.sh
echo 'Defaults secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/opt/puppetlabs/bin"' | sudo tee /etc/sudoers.d/puppet
```

### Configuring Puppet

- Setup the certificate name on each machine to be set to the **FQDN**

```bash
sudo puppet config set certname $(hostname -f) --section main
```

- Set an aggresively small memory cap for Puppetserver on the `web` machine

```bash
sudo sed -i 's/^JAVA_ARGS=.*/JAVA_ARGS="-Xms256m -Xmx512m"/' /etc/default/puppetserver
sudo systemctl daemon-reload
```
- Allocate **1G** swap as a safety buffer on the `web` machine

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h   # confirm swap shows up
```



- On the all machines local Puppet agents, set the `web` server to be the Puppet server

```bash
sudo puppet config set server batcsg1-web.op.ac.nz --section main
```

- On the `web` machine enable and start the Puppet server

```bash
sudo systemctl enable --now puppetserver
```

- On all the machines start and enable the Puppet agent

```bash
sudo systemctl enable --now puppet
```

- On the `db` and `app` machines run the agent to generate a CSR

```bash

sudo puppet agent -t
```

- On the `web` server, sign the incoming certificateds from the `app` and `db` machines

```bash
sudo puppetserver ca list --all
```