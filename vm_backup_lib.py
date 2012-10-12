#!/usr/local/bin/python

#
# Citrix XenServer 5.5 VM Backup Library
# This script contains functions used by the VM backup script
#
# @version      1.0
# @created      22/05/2012
#
# @author       Alexander Blakov
# @email        thexobbitt@gmail.com
#

import subprocess
import os.path
from datetime import datetime
from vm_backup_cfg import *


#
# log_message
# Add message to the log
# @use log_message('message')
# @param string message
# @return void
#

def log_message(message):
    if log_enable == 'YES':
        log_file = open(log_path, 'a')
        log_file.write('%s\t%s\n' % (datetime.now(), message))
        log_file.close()
    else:
        pass


#
# start_logging
# Starts logging
# @use start_logging()
# @return void
#

def start_logging():
    log_message('')
    log_message('Starting VM Backup.')
    log_message('------------------------------------------')


#
# stop_logging
# Stops logging
# @use stop_logging()
# @return void
#

def stop_logging():
    log_message('------------------------------------------')
    log_message('VM Backup Ended.')


#
# set_running_vms
# Set running VMs in backup list
# @use set_running_vms()
# @return tuple
#

def set_running_vms():
    log_message('Get running VMs.')

    try:
        running_vms = subprocess.check_output(['xe', 'vm-list', '-s', host, '-u', user, '-pw', pasw, 'power-state=running', 'is-control-domain=false'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        log_message('Get running VMs failed: %s' % e.output.replace('\n', ' '))
        raise Exception(e.output.replace('\n', ' '))
    else:
        running_vms = running_vms.split('\n\n\n')[:-1]
        log_message('Set running VMs.')
        vm_backup_list = list()
        for vm in running_vms:
            vm_info = vm.replace(' ', '').split('\n')
            vm_backup_list.append(vm_info[0].split(':')[1])
        vm_backup_list = tuple(vm_backup_list)

    return vm_backup_list


#
# set_all_vms
# Set all VMs in backup list
# @use set_all_vms()
# @return tuple
#

def set_all_vms():
    log_message('Get all VMs.')

    try:
        all_vms = subprocess.check_output(['xe', 'vm-list', '-s', host, '-u', user, '-pw', pasw, 'is-control-domain=false'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        log_message('Get all VMs failed: %s' % e.output.replace('\n', ' '))
        raise Exception(e.output.replace('\n', ' '))
    else:
        all_vms = all_vms.split('\n\n\n')[:-1]
        log_message('Set all VMs.')
        vm_backup_list = list()
        for vm in all_vms:
            vm_info = vm.replace(' ', '').split('\n')
            vm_backup_list.append(vm_info[0].split(':')[1])
        vm_backup_list = tuple(vm_backup_list)

    return vm_backup_list


#
# backup_vm_list
# Backup VMs in vm_backup_list
# @use backup_vm_list(vm_backup_list)
# @return void
#

def backup_vm_list(vm_backup_list):
    log_message('Initialise backup of VM list.')

    for uuid in vm_backup_list:
        try:
            backup_vm(uuid)
        except Exception:
            log_message('VM %s backup failed!' % uuid)
        else:
            log_message('VM %s backup succeeded!' % uuid)


#
# backup_vm
# Backup a VM
# @use backup_vm(uuid)
# @param string uuid
# @return void
#

def backup_vm(uuid):
    log_message('Backup VM %s.' % uuid)

    try:
        vm_label = get_vm_label(uuid)
    except Exception, e:
        log_message('get_vm_label failed: %s' % e[0])
        raise e
    else:
        log_message('get_vm_label succeeded: %s' % vm_label)

    snapshot_name = '%s_snapshot' % vm_label
    export_name = '%s-%s%s' % (vm_label, datetime.now().strftime(date_format), backup_ext)

    try:
        snapshot = snapshot_vm(uuid, snapshot_name)
    except Exception, e:
        log_message('snapshot_vm failed: %s' % e[0])
        raise e
    else:
        log_message('snapshot_vm succeeded!')

    try:
        remove_template(snapshot)
    except Exception, e:
        log_message('remove_template failed: %s' % e[0])
        raise e
    else:
        log_message('remove_template succeeded!')

    try:
        disable_ha(snapshot)
    except Exception, e:
        log_message('disable_ha failed: %s' % e[0])
        raise e
    else:
        log_message('disable_ha succeeded!')

    try:
        export_vm(snapshot, export_name)
    except Exception, e:
        log_message('export_vm failed: %s' % e[0])
        raise e
    else:
        log_message('export_vm succeeded!')

    try:
        delete_vm(snapshot)
    except Exception, e:
        log_message('delete_vm failed: %s' % e[0])
        raise e
    else:
        log_message('delete_vm succeeded!')


#
# get_vm_label
# Return a VM label
# @use get_vm_label(uuid)
# @param string uuid
# @return string
#

def get_vm_label(uuid):
    log_message('Get VM label for %s.' % uuid)

    try:
        get_vm_label = subprocess.check_output(['xe', 'vm-param-get', '-s', host, '-u', user, '-pw', pasw, 'param-name=name-label', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        vm_label = get_vm_label.replace(' ', '_').lstrip('(').rstrip(')\n')

    return vm_label


#
# get_vm_vdi
# Return a VM VDI uuid
# @use get_vm_vdi(uuid)
# @param string uuid
# @return string
#

def get_vm_vdi(uuid):
    log_message('Get VDI %s.' % uuid)

    try:
        vm_vbds = get_vm_vbds(uuid)
    except Exception, e:
        log_message('get_vm_vbds failed:' % e[0])
        raise e

    # for every uuid we must get it type, if type is 'Disk' then check if it is Snapshot, if it is Snapshot then add it to delete list.
    vdi_uuids = list()
    for uuid in vm_vbds:
        log_message('VBD %s.' % uuid)
        try:
            vbd_type = get_vbd_type(uuid)
        except Exception, e:
            log_message('get_vbd_type failed: %s' % e[0])
            raise e
        else:
            if vbd_type != 'CD':
                try:
                    vdi_list = get_vbd_vdi_list(uuid)
                except Exception, e:
                    log_message('get_vbd_vdi_list failed: %s' % e[0] )
                    raise e
                else:
                    for vdi_uuid in vdi_list:
                        log_message('VDI: %s.' % vdi_uuid)
                        try:
                            vdi_snapshot = check_vdi_is_snapshot(vdi_uuid)
                        except Exception, e:
                            log_message('check_vdi_is_snapshot failed: %s' % e[0])
                            raise e
                        else:
                            if vdi_snapshot == 'true':
                                log_message('Add VDI to deletion list: %s.' % vdi_uuid)
                                vdi_uuids.append(vdi_uuid)
            else:    
                log_message('VDI is a CD, skipping: %s.' % uuid )

    vdi_uuids = tuple(vdi_uuids)

    return vdi_uuids


#
# get_vm_vbds
# Return a VM VBD uuid list
# @use get_vm_vbd(uuid)
# @param string uuid
# @return tuple
#

def get_vm_vbds(uuid):
    log_message('Get VBD(s) of %s.' % uuid)

    try:
        all_vm_vbds = subprocess.check_output(['xe', 'vbd-list', '-s', host, '-u', user, '-pw', pasw, 'vm-uuid=%s' % uuid, 'params=uuid'], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        all_vm_vbds = all_vm_vbds.split('\n\n\n')[:-1]
        vm_vbds = list()
        for vbd in all_vm_vbds:
            vbd_info = vbd.replace(' ', '').split('\n')
            vm_vbds.append(vbd_info[0].split(':')[1])
        vm_vbds = tuple(vm_vbds)

    return vm_vbds


#
# get_vbd_type
# Return VBD type
# @use get_vbd_type(uuid)
# @param string uuid
# @return string
#

def get_vbd_type(uuid):
    log_message('Get VBD type of %s.' % uuid)

    try:
        vbd_type = subprocess.check_output(['xe', 'vbd-param-get', '-s', host, '-u', user, '-pw', pasw, 'param-name=type', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        vbd_type = vbd_type.rstrip('\n')

    return vbd_type


#
# get_vbd_vdi_list
# Return VDI uuids for VBD
# @use get_vbd_vdi_list(uuid)
# @param string uuid
# @return tuple
#

def get_vbd_vdi_list(uuid):
    log_message('Get VBD VDI list.')

    try:
        vdi_info = subprocess.check_output(['xe', 'vdi-list', '-s', host, '-u', user, '-pw', pasw, 'vbd-uuids=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        vdi_info = vdi_info.split('\n\n\n')[:-1]
        vdi_list = list()
        for vdi in vdi_info:
            vdi_params = vdi.replace(' ', '').split('\n')
            vdi_list.append(vdi_params[0].split(':')[1])
        vdi_list = tuple(vdi_list)

    return vdi_list


#
# check_vdi_is_snapshot
# Check a VDI is for a snapshot
# @use check_vdi_is_snapshot(uuid)
# @param string uuid
# @return boolean
#

def check_vdi_is_snapshot(uuid):
    log_message('Checking if %s is snapshot.' % uuid)

    try:
        is_snapshot = subprocess.check_output(['xe', 'vdi-param-get', '-s', host, '-u', user, '-pw', pasw, 'param-name=is-a-snapshot', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        is_snapshot = is_snapshot.rstrip('\n')

    return is_snapshot


#
# snapshot_vm
# Snapshot a VM with quiesce if possible
# @use snapshot_vm(uuid, label)
# @param string uuid
# @param string label
# @return string
# 

def snapshot_vm(uuid, label):
    log_message('Snapshotting VM %s.' % uuid)

    try:
        snapshot_uuid = snapshot_vm_quiesce(uuid, label)
    except Exception, e:
        log_message('Quiesce snapshot failed: %s' % e[0])
        log_message ('Attempting normal snapshot.')
        try:
            snapshot_uuid = snapshot_vm_normal(uuid, label)
        except Exception, e:
            log_message('Normal snapshot failed:  %s' % e[0])
            raise e

    return snapshot_uuid


#
# snapshot_vm_normal
# Snapshot a VM
# @use snapshot_vm_normal(uuid, label)
# @param string uuid
# @param string label
# @return string
#


def snapshot_vm_normal(uuid, label):
    log_message('Snapshot %s as %s.' % (uuid, label))

    try:
        snapshot = subprocess.check_output(['xe', 'vm-snapshot', '-s', host, '-u', user, '-pw', pasw, 'vm=%s' % uuid, 'new-name-label=%s' % label], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        snapshot = snapshot.rstrip('\n')

    return snapshot


#
# snapshot_vm_quiesce
# Snapshot a VM with quiesce
# @use snapshot_vm_quiesce(uuid, label)
# @param string uuid
# @param string label
# @return string
#

def snapshot_vm_quiesce(uuid, label): 
    log_message('Snapshot with quiesce %s as %s.' % (uuid, label))

    try:
        snapshot = subprocess.check_output(['xe', 'vm-snapshot-with-quiesce', '-s', host, '-u', user, '-pw', pasw, 'vm=%s' % uuid, 'new-name-label=%s' % label], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
    else:
        snapshot = snapshot.rstrip('\n')

    return snapshot


#
# export_vm
# Export a VM to a destination file
# @use export_vm(uuid, filename)
# @param string uuid
# @param string filename
# @return string
#

def export_vm(uuid, filename): 
    log_message('Export VM %s as %s.' % (uuid, filename))

    try:
        export_vm = subprocess.check_output(['xe', 'vm-export', '-s', host, '-u', user, '-pw', pasw, 'vm=%s' % uuid, 'filename=%s' % os.path.join(backup_dir, filename)], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))


#
# disable_ha
# Disable high availability
# @use disable_ha(uuid)
# @param string uuid
# @return boolean
#

def disable_ha(uuid): 
    log_message('Disable HA %s.' % (uuid))

    try:
        disable_ha = subprocess.check_output(['xe', 'template-param-set', '-s', host, '-u', user, '-pw', pasw, 'ha-always-run=false', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))


#
# remove_template
# Remove template param from VM
# @use remove_template(uuid)
# @param string uuid
# @return boolean
#

def remove_template(uuid): 
    log_message('Remove template status %s.' % uuid)

    try:
        remove_template = subprocess.check_output(['xe', 'template-param-set', '-s', host, '-u', user, '-pw', pasw, 'is-a-template=false', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))


#
# delete_vm
# Delete a VM
# @use delete_vm(uuid)
# @param string uuid
# @return boolean
#

def delete_vm(uuid):
    log_message('Delete VM %s.' % uuid)

    try:
        vdi_uuids = get_vm_vdi(uuid)
    except Exception, e:
        log_message('Cannot get VDI uuid: %s' % e[0])
        raise e
    else:
        if len(vdi_uuids) > 0:
            for vdi_uuid in vdi_uuids:
                try:
                    destroy_vdi(vdi_uuid)
                except Exception, e:
                    log_message('Cannot destroy: %s' % e[0])
                    raise e
                else:
                    log_message('VDI destroyed: %s.' % vdi_uuid)

    try:
        uninstall_vm(uuid)
    except Exception, e:
        log_message('Cannot uninstall VM: %s' % e[0])
        raise e


#
# uninstall_vm
# Uninstall (remove) a VM
# @use uninstall_vm(uuid)
# @param string uuid
# @return boolean
#

def uninstall_vm(uuid):
    log_message('Uninstall VM %s.' % (uuid))

    try:
        uninstall_vm = subprocess.check_output(['xe', 'vm-uninstall', '-s', host, '-u', user, '-pw', pasw, 'force=true', 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))


#
# destroy_vdi
# Destroy a VDI
# @use destroy_vdi(uuid)
# @param string uuid
# @return boolean
#

def destroy_vdi(uuid):
    log_message('Destroy VDI %s.' % uuid)

    try:
        destroy_vdi = subprocess.check_output(['xe', 'vdi-destroy', '-s', host, '-u', user, '-pw', pasw, 'uuid=%s' % uuid], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        raise Exception(e.output.replace('\n', ' '))
