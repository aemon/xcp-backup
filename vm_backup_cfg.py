#!/usr/local/bin/python

#
# Citrix XenServer 5.5 VM Backup Config
# This script contains config settings used by the VM backup script
#
# @version      1.0
# @created      22/05/2012
#
# @author       Alexander Blakov
# @email        thexobbitt@gmail.com
#

#
# Settings
#

# Set authentification information

host = ''
user = ''
pasw = ''


# Set log path

log_path = '/home/vm_backup.log'


# Enable logging
# Remove to disable logging

log_enable = 'YES'


# Local backup directory
# You can link this to a Windows CIFS share using the blog article

backup_dir = '/backup/'


# Backup extension
# .xva is the default Citrix template/vm extension

backup_ext = '.xva'


# Which VMs to backup. Possible values are:
# 'all' - Backup all VMs
# 'running' - Backup all running VMs
# 'list' - Backup all VMs in the backup list (see below)
# 'none' - Don't backup any VMs

backup_vms = 'none'


# VM backup list
# Only VMs in this list will be backed up when backup_vms='list'

# Example:
# vm_backup_list = ('2844954f-966d-3ff4-250b-638249b66313', )


# Current Date
# This is appended to the backup file name and the format can be changed here
# Default format: '%Y-%m-%d_%H-%M-%S'

date_format = '%Y-%m-%d_%H-%M-%S'
