# Hippo Digital Open ID Connect Identity Provider
This IDP is a new project to create a very lightweight yet flexible IDP primarily designed for use in environments where there is an existing LDAP directory, such as Active Directory or OpenLDAP.

## Setup

The IDP is deployed via Ansible.  Ansible can be deployed on the IDP itself and used to configure the host locally.

### Initial Deployment

#### Requirements

 - IDP Host
   - Ubuntu Server 16.04.1 or later
   - 1GB RAM
   - 1 CPU
   - 20GB Disk Space

   
#### Installing Ubuntu

Install Ubuntu server on a host with the following defaults:

 - Username: user1
 - Password: \<Choose a suitable password\>
 - ... (complete on train)

 
#### Initial Host Configuration

Install pre-requisites via the package manager

````
# Add the Ansible apt repo and install components
sudo apt-get install software-properties-common
sudo apt-add-repository ppa:ansible/ansible
sudo apt-get update
sudo apt-get install ssh python make sshpass ansible

# Pull the IDP source code from Git
git clone https://github.com/hippodigital/open-id-connect.git

# Register the host key
ssh user1@127.0.0.1   # Type *yes* to accept, then press *Ctrl+C*
````


## Run Ansible against the host

For the IDP server:

````
cd open-id-connect/ansible
make install-idp limit=127.0.0.1  # When prompted, enter the user1 password twice
````

For the LDAP server:

````
cd open-id-connect/ansible
make install-ldap limit=127.0.0.1  # When prompted, enter the user1 password twice
````

## IDP Server Configuration


### IDP Settings

The configuration will need to be altered to reflect the local environment setup.  

````
sudo vim /etc/hippo-idp/config.yml
````

The default config.yml is self-documented, but included here for completeness.

````
---
# Basic configuration for the IDP
issuer:
    # The base URL for the published IDP service, i.e. where clients will be pointed to
    address: https://login.hippo.digital


# URL for the LDAP GetUserDetails service
idservice:
    address: http://localhost:5001/getuserdetails


# Configuration for connection to the Redis host.  In single server configurations this
#  would normally be left in the default configuration of localhost:6379
sessionstore:
    address: localhost
    port: 6379


# Session configuration for the JW token
session:
    # The length of time in seconds that a login session will be valid for
    jwtexpiryseconds: 28800


# Configure the sub field of the token to be replaced with another ID field,
#  or remove to use the username as to sub
attributes:
    subject: id_number
````

### Configure Client(s)

Each consuming client will need to configured with a client ID and an associated secret key.  The secret key is only held on the consuming client, and the IDP stores and compares against a salted hash.

#### Create A Client Hash

This step only needs to be completed if you do not already have a client ID and secret.

The hash is made up of client-id.client-secret using SHA512. E.g.

````
my-client-1.47q6Flsmy"331&z
````
You can use an online service to create the hash from this string, e.g. [http://passwordsgenerator.net/sha512-hash-generator/](http://passwordsgenerator.net/sha512-hash-generator/)

Once you have the hash you need to ensure that it is in lower case.

#### Configuring the IDP with the client

Edit the /etc/idp/clients.yml file and update it with the required client details.

````
sudo vim /etc/hippo-idp/clients.yml
````
Under the **clients** section add a line for each consuming client.  Each line should be formatted as:

   *client-id: hash*

For example:

````
---
clients:
    # Hashes must be lower case
    my-client-1: c9dbb92643e15...457e3ef91b125047
````

### Configuring the Web Server

NGINX is used to host the web service and handle SSL termination.  It will need to be configured with the appropriate certificate, key and URL.

````
sudo vim /etc/nginx/sites-available/hippo-idp
````

It will be necessary to update the following fields to reflect your local environment:

* server\_name
* ssl\_certificate
* ssl\_certificate\_key

An example configuration file is here for completeness.

````
server {
    listen 443;
    server_name login.hippo.digital;

    ssl on;
    ssl_certificate /etc/idp/login.hippo.digital.pem;
    ssl_certificate_key /etc/idp/login.hippo.digital.key;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/var/idp/hippo-idp.sock;
    }
}
````

Add SSL Key and Certificate to the IDP.  The file names and paths need to match the NGINX configuration above.

Copy the .key and .pem files to /etc/hippo-idp as

* idp.url.key
* idp.url.pem

Secure the keys by applying root access only permissions

````
sudo chmod 0600 /etc/hippo-idp/idp.url.*
````


### Final Steps

Restart the IDP service and NGINX for changes to take effect.

````
sudo systemctl restart hippo-idp
sudo service nginx restart
````

### Testing the Configuration

You can conduct a basic test using CURL.

````
curl https://idp.url/login
````

On success you should see a reponse similar to:

````
{"error": "invalid_request"}
````

Alternatively, issuing a full request should result in a HTML response.

````
curl http://localhost:5000/login?redirect_uri=https://my-app\&response_type=code\&scope=openid\&client_id=moodle-1\&state=123
````



## Troubleshooting

### Log Files

A number of log files are held to assist with in-depth troubleshooting. 

* **/var/log/hippo-idp/uwsgi.log** - Details interaction between NGINX and the IDP process
* **/var/log/nginx/access.log** - Records successful queries, including 40x and 50x return states
* **/var/log/nginx/error.log** - Records errors that occur at the web server level
* **/home/idpservice/open-id-connect/idp/web/idp.log** - In-depth logging from the Python IDP code


## LDAP Server Configuration


### LDAP Settings

The configuration will need to be altered to reflect the local environment setup.  

````
sudo vim /etc/hippo-ldap/config.yml
````

The default config.yml is self-documented, but included here for completeness.

````
---
# Configuration for the LDAP directory where user objects are held
idstore:
    # IP address of the LDAP server
    address: 127.0.0.1

    # TCP port for the LDAP service
    port: 389

    # The service requires a low privileged (read only, search) service account to
    #  conduct an initial query against the directory upon user authentication

    # DN for the service account used to conduct user searches
    serviceaccountdn: 'cn=admin,dc=hd,dc=local'

    # Password for the service account used to conduct user searches
    serviceaccountpassword: 'Password1'


    # DN for the base OU under which all user objects are stored.  This will be used
    #  as the root for a search each time a user logs in
    basesearchdn: 'dc=hd,dc=local'


# List of attributes that need to be read for the user object and added to the claim as
#  part of the JW token passed to the consuming application
attributes:
    claims:
        sn: family_name
        givenName: given_name
        mail: email
        employeeNumber: id_number

````

### Configuring the Web Server

NGINX is used to host the web service and handle SSL termination.  It will need to be configured with the appropriate certificate, key and URL.

````
sudo vim /etc/nginx/sites-available/hippo-ldap
````

It will be necessary to update the following fields to reflect your local environment:

* server\_name
* ssl\_certificate
* ssl\_certificate\_key

An example configuration file is here for completeness.

````
server {
    listen 443;
    server_name login.hippo.digital;

    ssl on;
    ssl_certificate /etc/ldap/login.hippo.digital.pem;
    ssl_certificate_key /etc/ldap/login.hippo.digital.key;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/var/ldap/hippo-ldap.sock;
    }
}
````

Add SSL Key and Certificate to the IDP.  The file names and paths need to match the NGINX configuration above.

Copy the .key and .pem files to /etc/hippo-ldap as

* ldap.url.key
* ldap.url.pem

Secure the keys by applying root access only permissions

````
sudo chmod 0600 /etc/hippo-ldap/ldap.url.*
````


### Final Steps

Restart the IDP service and NGINX for changes to take effect.

````
sudo systemctl restart hippo-ldap
sudo service nginx restart
````

### Testing the Configuration

You can conduct a basic test using CURL.

````
curl -X POST https://ldap.url/getuserdetails
````

On success you should see a reponse similar to:

````
{"error": "invalid_request"}
````



## Troubleshooting

### Log Files

A number of log files are held to assist with in-depth troubleshooting. 

* **/var/log/hippo-ldap/uwsgi.log** - Details interaction between NGINX and the IDP process
* **/var/log/nginx/access.log** - Records successful queries, including 40x and 50x return states
* **/var/log/nginx/error.log** - Records errors that occur at the web server level
* **/home/ldapservice/open-id-connect/ldap/web/ldap.log** - In-depth logging from the Python IDP code
