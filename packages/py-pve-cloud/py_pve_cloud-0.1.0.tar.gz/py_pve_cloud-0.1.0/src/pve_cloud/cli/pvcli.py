import argparse
import yaml
from proxmoxer import ProxmoxAPI
import os



def connect_cluster(args):
  # try load current dynamic inventory
  inv_path = os.path.expanduser("~/.pve-cloud-dyn-inv.yaml")
  if os.path.exists(inv_path):
    with open(inv_path, "r") as file:
      dynamic_inventory = yaml.safe_load(file)
  else:
    # initialize empty
    dynamic_inventory = {}
  
  # init cloud domain if not there
  if args.pve_cloud_domain not in dynamic_inventory:
    dynamic_inventory[args.pve_cloud_domain] = {}

  # connect to the passed host
  proxmox = ProxmoxAPI(
    args.pve_host, user="root", backend='ssh_paramiko'
  )

  # try get the cluster name
  cluster_name = None
  status_resp = proxmox.cluster.status.get()
  for entry in status_resp:
    if entry['id'] == "cluster":
      cluster_name = entry['name']
      break

  if cluster_name is None:
    raise Exception("Could not get cluster name")
  
  if cluster_name in dynamic_inventory[args.pve_cloud_domain] and not args.force:
    print(f"cluster {cluster_name} already in dynamic inventory")
    return
  
  # overwrite on force / create fresh
  dynamic_inventory[args.pve_cloud_domain][cluster_name] = {}
  
  # not present => add and safe the dynamic inventory
  cluster_hosts = proxmox.nodes.get()

  for node in cluster_hosts:
    node_name = node["node"]

    if node["status"] == "offline":
      print(f"skipping offline node {node_name}")
      continue
    
    # get the main ip
    ifaces = proxmox.nodes(node_name).network.get()
    node_ip_address = None
    for iface in ifaces:
      if 'gateway' in iface:
        if node_ip_address is not None:
          raise Exception(f"found multiple ifaces with gateways for node {node_name}")
        node_ip_address = iface.get("address")

    if node_ip_address is None:
      raise Exception(f"Could not find ip for node {node_name}")
    
    dynamic_inventory[args.pve_cloud_domain][cluster_name][node_name] = {
      "ansible_user": "root",
      "ansible_host": node_ip_address
    }

  with open(inv_path, "w") as file:
    yaml.dump(dynamic_inventory, file)


  
def main():
  parser = argparse.ArgumentParser(description="PVE general purpose cli for setting up.")

  base_parser = argparse.ArgumentParser(add_help=False)

  subparsers = parser.add_subparsers(dest="command", required=True)

  connect_cluster_parser = subparsers.add_parser("connect-cluster", help="Add an entire pve cluster to this machine for use.", parents=[base_parser])
  connect_cluster_parser.add_argument("--pve-host", type=str, help="PVE Host to connect to and add the entire cluster for the local machine.", required=True)
  # todo: try and get the pve cloud domain from the cluster in case it is already initialized.
  connect_cluster_parser.add_argument("--pve-cloud-domain", type=str, help="PVE Cloud domain the hosts are part of / should be initialized under.", required=True)
  connect_cluster_parser.add_argument("--force", action="store_true", help="Will readd the cluster if set.")
  connect_cluster_parser.set_defaults(func=connect_cluster)


  args = parser.parse_args()
  args.func(args)


if __name__ == "__main__":
  main()