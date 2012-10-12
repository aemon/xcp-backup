#!/usr/local/bin/python

#
# Citrix XenServer 5.5 VM Backup Script
# This script provides online backup for Citrix Xenserver 5.5 virtual machines
#
# @version      1.0
# @created      22/05/2012
#
# @author       Alexander Blakov
# @email        thexobbitt@gmail.com
#


# Load functions and config

from vm_backup_cfg import backup_vms
from vm_backup_lib import *


# Start logging

start_logging()


# Switch backup_vms to set the VM uuids we are backing up in vm_backup_list

if backup_vms == 'all':
    log_message('Backup All VMs.')
    try:
        vm_backup_list = set_all_vms()
    except Exception, e:
        exit('Get all VMs failed: %s' % e[0])
elif backup_vms == 'running':
    log_message('Backup running VMs.')
    try:
        vm_backup_list = set_running_vms()
    except Exception, e:
        exit('Get running VMs failed: %s' % e[0])
elif backup_vms == 'list':
    log_message('Backup list VMs.')
else:
    log_message('Backup no VMs.')
    exit('Backup no VMs')


# Backup VMs

try:
    backup_vm_list(vm_backup_list)
except Exception, e:
    log_message('Backup VMs failed: %s' % e[0])
else:
    log_message('Backup VMs succeeded!')


# End logging

stop_logging()
