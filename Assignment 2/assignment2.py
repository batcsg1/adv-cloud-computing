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
        'project_domain_name': os.environ.get('OS_PROJECT_DOMAIN_NAME', 'Default'),
        'username': os.environ.get('OS_USERNAME'),
        'password': os.environ.get('OS_PASSWORD'),
        'region_name': os.environ.get('OS_REGION_NAME', 'nz-hlz-1'),
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
    '''Create a set of OpenStack resources.'''

    print('Executing the `create` function')

    # Connect to OpenStack
    conn = connect()
    if conn is None:
        return

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

        # Declare keypair name and path

        KEYPAIR_NAME = f'{USERNAME}-keypair'
        SSH_KEY_PATH = os.path.expanduser(f'~/.ssh/{KEYPAIR_NAME}')

        # ---------------------------------------------------------------
        # Key pair, used to SSH into the web server
        # ---------------------------------------------------------------
        keypair = conn.compute.find_keypair(KEYPAIR_NAME)
        if keypair is None:
            keypair = conn.compute.create_keypair(name=KEYPAIR_NAME)

            # The private key is only ever returned once, at creation time -
            # OpenStack never stores it, so it has to be saved right now or it's gone.
            os.makedirs(os.path.dirname(SSH_KEY_PATH), mode=0o700, exist_ok=True)
            with open(SSH_KEY_PATH, 'w') as f:
                f.write(keypair.private_key)
            os.chmod(SSH_KEY_PATH, 0o600)  # SSH refuses to use a key with looser permissions

            print(f'Created key pair: {keypair.name} (private key saved to {SSH_KEY_PATH})')
        else:
            print(f'Key pair already exists: {keypair.name}')

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

            if server is None:
                server = conn.compute.create_server(
                    name=server_name,
                    flavor_id=flavor_obj.id,
                    image_id=image_obj.id,
                    networks=[{'uuid': network.id}],
                    security_groups=[{'name': SECURITY_GROUP}],
                    key_name=keypair.name,   # now applied to web, app, and db
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
        port = next(conn.network.ports(device_id=web_server.id), None)
        if port is None:
            raise Exception(f'No network port found for server {web_server.name}')

        conn.network.update_ip(floating_ip, port_id=port.id)

        print(f'Assigned floating IP {floating_ip.floating_ip_address} to {web_server.name}')

    except Exception as e:
        print(f'Error creating resources: {str(e)}')



def run():
    ''' Start  a set of Openstack virtual machines if they are not already running.
    '''
    print('Executing the `run` function')

    conn = connect()
    if conn is None:
        return

    for role in SERVER_ROLES:
        server_name = f'{USERNAME}-{role}'
        try:
            server = conn.compute.find_server(server_name)
            if server is None:
                print(f'Error: server "{server_name}" does not exist')
                continue

            server = conn.compute.get_server(server.id)

            if server.status == 'ACTIVE':
                print(f'{server.name} is already running')
            else:
                conn.compute.start_server(server)
                conn.compute.wait_for_server(server, status='ACTIVE')
                print(f'Started server: {server.name}')

        except Exception as e:
            print(f'Error starting server {server_name}: {str(e)}')

def stop():
    ''' Stop  a set of Openstack virtual machines if they are running.
    '''
    print('Executing the `stop` function')

    conn = connect()
    if conn is None:
        return

    for role in SERVER_ROLES:
        server_name = f'{USERNAME}-{role}'
        try:
            server = conn.compute.find_server(server_name)
            if server is None:
                print(f'Error: server "{server_name}" does not exist')
                continue

            server = conn.compute.get_server(server.id)

            if server.status == 'SHUTOFF':
                print(f'{server.name} is already stopped')
            else:
                conn.compute.stop_server(server)
                conn.compute.wait_for_server(server, status='SHUTOFF')
                print(f'Stopped server: {server.name}')

        except Exception as e:
            print(f'Error stopping server {server_name}: {str(e)}')

def destroy():
    ''' Tear down the set of Openstack resources produced by the create action
    '''

    print('Executing the `destroy` function')

    conn = connect()
    if conn is None:
        return

    KEYPAIR_NAME = f'{USERNAME}-keypair'

    net_name = f'{USERNAME}-net'
    subnet_name = f'{USERNAME}-subnet'
    router_name = f'{USERNAME}-rtr'

    try:
        # ---------------------------------------------------------------
        # 1. Capture the web server's floating IP address before we delete
        #    the server (once the server is gone we lose the association).
        # ---------------------------------------------------------------
        web_server_name = f'{USERNAME}-web'
        web_server = conn.compute.find_server(web_server_name)
        floating_ip_address = None

        if web_server is not None:
            web_server = conn.compute.get_server(web_server.id)
            for addrs in (web_server.addresses or {}).values():
                for addr in addrs:
                    if addr.get('OS-EXT-IPS:type') == 'floating':
                        floating_ip_address = addr['addr']

        # ---------------------------------------------------------------
        # 2. Servers: web, app, db
        # ---------------------------------------------------------------

        # Delete the servers specified in the create() function
        for role in SERVER_ROLES:
            server_name = f'{USERNAME}-{role}'
            server = conn.compute.find_server(server_name)
            if server is None:
                print(f'Server does not exist: {server_name}')
                continue
            conn.compute.delete_server(server, ignore_missing=True)
            conn.compute.wait_for_delete(server)
            print(f'Deleted server: {server_name}')

        # ---------------------------------------------------------------
        # Key pair
        # ---------------------------------------------------------------
        try:
            keypair = conn.compute.find_keypair(KEYPAIR_NAME)
            if keypair is None:
                print(f'Key pair does not exist: {KEYPAIR_NAME}')
            else:
                conn.compute.delete_keypair(keypair, ignore_missing=True)
                print(f'Deleted key pair: {KEYPAIR_NAME}')
        except Exception as e:
            print(f'Error deleting key pair {KEYPAIR_NAME}: {str(e)}')
            

        # ---------------------------------------------------------------
        # 3. Floating IP 
        # ---------------------------------------------------------------

        # Delete the Floating IP
        if floating_ip_address is not None:
            floating_ip = next(
                (ip for ip in conn.network.ips()
                 if ip.floating_ip_address == floating_ip_address),
                None,
            )
            if floating_ip is not None:
                conn.network.delete_ip(floating_ip, ignore_missing=True)
                print(f'Deleted floating IP: {floating_ip_address}')
        else:
            print('No floating IP to delete')

        # ---------------------------------------------------------------
        # 4. Router - detach interface and clear gateway before deleting
        # ---------------------------------------------------------------
        try:
            router = conn.network.find_router(router_name)
            if router is None:
                print(f'Router does not exist: {router_name}')
                return

            subnet = conn.network.find_subnet(subnet_name)
            router_ports = conn.network.ports(device_id=router.id) if subnet is not None else []
            subnet_attached = subnet is not None and any(
                fixed_ip['subnet_id'] == subnet.id
                for port in router_ports
                for fixed_ip in port.fixed_ips
            )

            if subnet_attached:
                conn.network.remove_interface_from_router(router, subnet_id=subnet.id)
                print(f'Removed subnet {subnet_name} interface from router {router_name}')

            if router.external_gateway_info:
                conn.network.update_router(router, external_gateway_info=None)
                print(f'Cleared external gateway on router {router_name}')

            conn.network.delete_router(router, ignore_missing=True)
            print(f'Deleted router: {router_name}')
        except Exception as e:
            print(f'Error deleting router {router_name}: {str(e)}')

        # ---------------------------------------------------------------
        # 5. Subnet
        # ---------------------------------------------------------------
        subnet = conn.network.find_subnet(subnet_name)

        # Delete the subnet
        if subnet is not None:
            conn.network.delete_subnet(subnet, ignore_missing=True)
            print(f'Deleted subnet: {subnet_name}')
        else:
            print(f'Subnet does not exist: {subnet_name}')

        # ---------------------------------------------------------------
        # 6. Network
        # ---------------------------------------------------------------

        # Delete the netwrok
        network = conn.network.find_network(net_name)
        if network is not None:
            conn.network.delete_network(network, ignore_missing=True)
            print(f'Deleted network: {net_name}')
        else:
            print(f'Network does not exist: {net_name}')

    except Exception as e:
        print(f'Error destroying resources: {str(e)}')

def status():
    '''Print a status report on the OpenStack virtual machines created by
    the create action.'''

    print('Executing the `status` function')

    conn = connect()
    if conn is None:
        return

    for role in SERVER_ROLES:
        server_name = f'{USERNAME}-{role}'
        try:
            server = conn.compute.find_server(server_name)
            if server is None:
                print(f'{server_name}: does not exist')
                continue

            server = conn.compute.get_server(server.id)

            floating_ips = [
                addr['addr']
                for addrs in (server.addresses or {}).values()
                for addr in addrs
                if addr.get('OS-EXT-IPS:type') == 'floating'
            ]
            floating_ip_str = ', '.join(floating_ips) if floating_ips else 'none'

            print(
                f'{server.name}: status={server.status}, '
                f'flavor={server.flavor.get("original_name", server.flavor.get("id"))}, '
                f'floating IP={floating_ip_str}'
            )

        except Exception as e:
            print(f'Error getting status for {server_name}: {str(e)}')


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
