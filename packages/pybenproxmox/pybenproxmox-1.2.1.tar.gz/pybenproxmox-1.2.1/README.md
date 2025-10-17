# pybenproxmox

![GitHub License](https://img.shields.io/github/license/DarkFlameBEN/pybenproxmox)
[![PyPI - Version](https://img.shields.io/pypi/v/pybenproxmox)](https://pypi.org/project/pybenproxmox/)
![python suggested version](https://img.shields.io/badge/python-3.12.5-red.svg)
![python minimum version](https://img.shields.io/badge/python(min)-3.10+-red.svg)
![platforms](https://img.shields.io/badge/Platforms-Linux%20|%20Windows%20|%20Mac%20-purple.svg)

## Introduction
PyBEN Proxmox repository is an easy to use python utility class for Proxmox server solution

## Installation
> python -m pip install pybenproxmox

## Use

### Cli module activation

Run for a full help printout:
```bash
python -m pybenproxmox -h
```

Example for use of global variables to get all vms:
 - pybenproxmox is the name of the module
 - pprint is a function to print the returned dict nicely in console
 - get_vms is a function to return all vms (or request a specific one)
```bash
set PROXMOX_HOST='1.1.1.1'
set PROXMOX_USER='root'
set PROXMOX_PASS='1234'

python -m pybenproxmox pprint get_vms
```

Example for passing variables directly:
 - pybenproxmox is the name of the module
 - get_vms is a function to return all vms (or request a specific one)
```bash
python -m pybenproxmox host=1.1.1.1 user=root password=1234 get_vms vm_id=123
```

### Python import ProxmoxCls class
```python
from pybenproxmox import ProxmoxCls

prox = ProxmoxCls(host='1.1.1.1', user='root', password='1234')
print(prox.get_vms())
```
Some of the included functions:
 - get_vms: Returns a full list of vms, or list with matching vms by id or name
 - clone_vms
 - migrate_vm_to_node
 - delete_vm
 - start_vm
 - stop_vm
 - snapshot handling
 - and more ...