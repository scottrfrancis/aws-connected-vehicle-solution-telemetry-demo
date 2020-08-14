# AWS Connected Vehicle Solution Telemetry Demo

This project is designed to be used in conjunction with the [AWS Connected Vehicle Solution](https://aws.amazon.com/solutions/implementations/aws-connected-vehicle-solution/). While the the Connected Vehicle Solution builds the cloud framework, this project creates a simulation of vechicle data that can be used to send data to the cloud.  This project will build

* An AWS IoT Greengrass Group and Core device
* A few AWS IoT Devices 


## Setup

Set up greengrass group, core, device, etc.

1. log in to Greengrass console (e.g. https://us-east-1.console.aws.amazon.com/iot/home?region=us-east-1#/greengrass/grouphub, but check region)
2. Click **Create Group**, **Use default group**
3. Use name `CMS-Demo-Cloud-Group`, Click **Next**, **Create group**
4. Click **Download these resources as tar.gz** -- saves in `Downloads` directory
---  Click **Choose your platform** -- opens in new tab/window ----
5. Click **Finish**


On the EC2 / Cloud9 instance, enter these commands in the terminal window:

```bash
wget https://d1onfpft10uf5o.cloudfront.net/greengrass-core/downloads/1.10.2/greengrass-linux-x86-64-1.10.2.tar.gz -O ~/greengrass-linux-x86-64-1.10.2.tar.gz
sudo tar xvf ~/greengrass-linux-x86-64-1.10.2.tar.gz -C /
sudo wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O /greengrass/certs/root.ca.pem

```

Upload the `tar.gz` setup file download previously during the group creation to the default directory of Cloud9 (usually, `/home/ubuntu/environment`)
1. select the 'environment' folder in the left file browser panel
2. choose File/Upload Local Files
3. Choose the tar.gz file from your `Downloads` or wherver you saved the {id}-setup.tar.gz package
4. Install the package from the terminal window with

```bash
cd ~/environment # or path-where-you-uploaded-the-package
sudo tar xvf *-setup.tar.gz -C /greengrass/ # substitute your {id} number if there is more than one such file
```

Add group and user 
```
sudo adduser --system ggc_user
sudo addgroup --system ggc_group
```


Start Greengrass:

```bash
sudo su -
cd /greengrass/ggc/core
./greengrassd start
```

## Create virtual telemetry device

1. clone repo: 
2. install sdk with `pip3 install awsiotsdk`
```
pip3 install awscrt
```


### add a device to the greengrass group

From the greengrass console,
1. select the 'CMS-Demo-Cloud-Group' if not already 
2. Click **Add Device**, **Create New Device**
3. Name the Thing 'CMS-Demo-Cloud-TCU', click **Next**, **Use Defaults**
4. Click **Download these resources as a tar.gz** and save the package in `Downloads` or wherever convenient
5. Click **Finish**
6. Deploy the group by clicking **Deploy** from the actions drop down
7. Use **Automatic Detection**
8. Wait for deployement complete -- may need to refresh page


Upload this package to the `environment/aws-connected-vechicle-solution-telemetry-demo` folder on the EC2/Cloud9 instance
1. Select the `aws-connected-vechicle-solution-telemetry-demo` folder from the lef side files panel
2. Choose File/Upload local files and select the {id}-setuo.tar.gz packge just downloaded

Expand the TCU thing setup package with
```bash
cd ~/environment/aws-connected-vechicle-solution-telemetry-demo
tar xvf *-setup.tar.gz
```

## Setup Subscriptions 

From the 'CMS-Demo-Cloud-Group' in the Greengrass section of the IoT Console:
1. Click **Subscriptions**, **Add Subscription**
2. Select **Devices** / **CMS-Demo-Cloud-TCU** for Source 
3. Select **Services** / **IoT Cloud** for Target, click **Next**
4. Enter '#' for Topic Filter and click **Next**
5. Click **Finish**
6. Choose **Deploy** from the Actions menu and wait for Deployment to be complete


## verify connectivity
From the IoT Console (panel to the left of the greengrass console):
1. Click **Test**
2. Enter '#' and click **Subscribe to Topic**

in the cloud9 terminal:
```
python3 ./basic_discovery.py -r /greengrass/certs/root.ca.pem -c *.cert.pem -k *.private.key -n 'CMS-Demo-Cloud-TCU'
```

Verify 'Hello World' received in Test Client on Console


