"""These lines import the necessary modules.
 argparse is a standard library module for parsing command-line arguments, 
and openstack is presumably a module for interacting with OpenStack resources."""

import argparse
import keystoneauth1.exceptions
import openstack

import os

from dotenv import load_dotenv

load_dotenv()



# Global variables
USERNAME = 'batcsg1'
PUBLIC_NETWORK_NAME = 'public-net'
SUBNET_CIDR = '192.168.50.0/24'
IMAGE_NAME = 'ubuntu-minimal-22.04-x86_64'
FLAVOR_NAME = 'c1.c1r1'
SECURITY_GROUP = 'assignment2'
SERVER_ROLES = ['web', 'app', 'db']

def connect():
    '''Create a connection to the OpenStack environment.'''
 
    auth = {
        'auth_url': os.environ.get('OS_AUTH_URL'),
        'project_name': os.environ.get('OS_PROJECT_NAME'),
        'username': os.environ.get('OS_USERNAME'),
        'password': os.environ.get('OS_PASSWORD'),
        'user_domain_name': os.environ.get('OS_USER_DOMAIN_NAME', 'Default'),
    }
 
    try:
        conn = openstack.connect(**auth)
        print(f'Successfully authenticated as {auth["username"]} into project {auth["project_name"]}!')
    except keystoneauth1.exceptions.ClientException as e:
        print(f'Error: authentication failed: {e}')
        return None
    except openstack.exceptions.SDKException as e:
        print(f'Error: could not connect to OpenStack: {e}')
        return None
    except Exception as e:
        print(f'Error: unexpected error while connecting: {e}')
        return None
 
    return conn

"""This defines a function named create that will be responsible for creating 
OpenStack resources.
The run, stop, destroy, and status functions are similarly defined.
"""

def create():
    # Connect to OpenStack
    conn = connect()

    '''Create a set of OpenStack resources.'''
    
    # Define your OpenStack connection parameters (update with your values)
    auth = {
        'project_name': 'otago-polytechnic~1a8012',
        'username': 'batcsg1@student.op.ac.nz"',
        'password': 'AngerTranslation2',
        'user_domain_name': 'Default',
    }

    # ---------------------------------------------------------------
    # 1. Network + subnet
    # ---------------------------------------------------------------
    net_name = f'{USERNAME}-net'
    subnet_name = f'{USERNAME}-subnet'
    router_name = f'{USERNAME}-rtr'

    try:
        # Create the network 
        network = conn.network.find_network(net_name)
        if network is None:
            network = conn.network.create_network(name=net_name)
            print(f'Created network: {network.name} (ID: {network.id})')
        else:
            print(f'Network already exists: {network.name} (ID: {network.id})')

        # Create a subnet
        subnet = conn.network.find_subnet(subnet_name)
        if subnet is None:
            subnet = conn.network.create_subnet(
                name=subnet_name,
                network_id=network.id,
                ip_version=4,
                cidr=SUBNET_CIDR,
            )
            print(f'Created subnet: {subnet.name} (ID: {subnet.id})')
        else:
            print(f'Subnet already exists: {subnet.name} (ID: {subnet.id})')

        # ---------------------------------------------------------------
        # 2. Router, with gateway on public-net and interface on our subnet
        # ---------------------------------------------------------------
        # Find the public network
        public_net = conn.network.find_network(PUBLIC_NETWORK_NAME)
        if public_net is None:
            raise Exception(f'Public network "{PUBLIC_NETWORK_NAME}" not found')

        # Find the public router
        router = conn.network.find_router(router_name)
        if router is None:
            router = conn.network.create_router(
                name=router_name,
                external_gateway_info={'network_id': public_net.id},
            )
            print(f'Created router: {router.name} (ID: {router.id})')
        else:
            print(f'Router already exists: {router.name} (ID: {router.id})')
            if not router.external_gateway_info:
                router = conn.network.update_router(
                    router,
                    external_gateway_info={'network_id': public_net.id},
                )
                print(f'Set external gateway on router: {router.name}')

        # Only add the interface if this subnet isn't already attached
        router_ports = list(conn.network.ports(device_id=router.id))
        subnet_attached = any(
            fixed_ip['subnet_id'] == subnet.id
            for port in router_ports
            for fixed_ip in port.fixed_ips
        )
        if not subnet_attached:
            conn.network.add_interface_to_router(router, subnet_id=subnet.id)
            print(f'Attached subnet {subnet.name} to router {router.name}')
        else:
            print(f'Router {router.name} already has an interface on {subnet.name}')


        # ---------------------------------------------------------------
        # 3. Servers: web, app, db
        # ---------------------------------------------------------------

        # Find the flavour from specified flavour name
        flavor_obj = conn.compute.find_flavor(FLAVOR_NAME)
        if flavor_obj is None:
            raise Exception(f'Flavor "{FLAVOR_NAME}" not found')

        # Find the image for the new instances
        image_obj = conn.compute.find_image(IMAGE_NAME)
        if image_obj is None:
            raise Exception(f'Image "{IMAGE_NAME}" not found')

        # Find the security group
        security_group = conn.network.find_security_group(SECURITY_GROUP)
        if security_group is None:
            raise Exception(f'Security group "{SECURITY_GROUP}" not found')

        # Initialize the servers array as an empty list
        servers = {}

        # Create each of the server from the specified server roles
        for role in SERVER_ROLES:
            server_name = f'{USERNAME}-{role}'
            server = conn.compute.find_server(server_name)

            # If the server doesn't exist
            if server is None:
                server = conn.compute.create_server(
                    name=server_name,
                    flavor_id=flavor_obj.id,
                    image_id=image_obj.id,
                    networks=[{'uuid': network.id}],
                    security_groups=[{'name': SECURITY_GROUP}],
                )
                server = conn.compute.wait_for_server(server)
                print(f'Created server: {server.name} (ID: {server.id})')
            else:
                print(f'Server already exists: {server.name} (ID: {server.id})')
            servers[role] = server

        # Assign the created web server to a variable
        web_server = servers['web']

        # ---------------------------------------------------------------
        # 4. Floating IP, assigned to the web server
        # ---------------------------------------------------------------
        # Get the ID of the web server
        web_server = conn.compute.get_server(web_server.id)
        already_has_floating_ip = any(
            addr.get('OS-EXT-IPS:type') == 'floating'
            for addrs in (web_server.addresses or {}).values()
            for addr in addrs
        )

        # If the machine already has an assigned floating IP address
        if already_has_floating_ip:
            print(f'{web_server.name} already has a floating IP assigned')
        else:
            # Reuse an existing unattached floating IP on the public network
            # if one is available, otherwise create a new one.
            floating_ip = next(
                (
                    ip for ip in conn.network.ips(
                        floating_network_id=public_net.id, status='DOWN'
                    )
                    if ip.port_id is None
                ),
                None,
            )

            # Create the floating IP
            if floating_ip is None:
                floating_ip = conn.network.create_ip(
                    floating_network_id=public_net.id
                )
                print(f'Created floating IP: {floating_ip.floating_ip_address}')
            else:
                print(f'Reusing unattached floating IP: {floating_ip.floating_ip_address}')

            # Add the newly created floating IP to the web server
            conn.compute.add_floating_ip_to_server(
                web_server, floating_ip.floating_ip_address
            )

            print(f'Assigned floating IP {floating_ip.floating_ip_address} to {web_server.name}')

    except Exception as e:
        print(f'Error creating resources: {str(e)}')

def create():
    ''' Create a set of Openstack resources '''
    pass

def run():
    ''' Start  a set of Openstack virtual machines if they are not already running.
    '''
    pass

def stop():
    ''' Stop  a set of Openstack virtual machines if they are running.
    '''
    pass

def destroy():
    ''' Tear down the set of Openstack resources produced by the create action
    '''
    pass

def status():
    ''' Print a status report on the OpenStack virtual machines created by the create action.
    '''
    pass


### You should not modify anything below this line ###
if __name__ == '__main__':

    """Here, an ArgumentParser object is created from the argparse module. 
    This object will help parse command-line arguments."""
    parser = argparse.ArgumentParser()

    """This line adds a command-line argument named operation. 
    The help parameter provides a description of this argument 
    that will be displayed when the user runs the script with the --help option."""

    parser.add_argument('operation', help='One of "create", "run", "stop", "destroy", or "status"')
    
    """This line parses the command-line arguments 
    provided to the script and stores them in the args variable."""
    args = parser.parse_args()

    """This line extracts the value of the operation argument 
    (i.e., the user's choice of action) and assigns it to the operation variable."""
    operation = args.operation

    """This creates a dictionary called operations that maps each possible 
    operation (e.g., 'create') to its corresponding openstack function (e.g., create)."""
    operations = {
        'connect' : connect,
        'create'  : create,
        'run'     : run,
        'stop'    : stop,
        'destroy' : destroy,
        'status'  : status
        }

    """This line uses the get method of the operations dictionary to 
    retrieve the function corresponding to the user's chosen operation. 
    If the operation is not found in the dictionary, 
    it defaults to a lambda function that prints an error message."""

    action = operations.get(operation, lambda: print('{}: no such operation'.format(operation)))
    
    """Finally, this line calls the chosen function 
    (e.g., create(), run(), etc.) based on the user's input."""
    action()
