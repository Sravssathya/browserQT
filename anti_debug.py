# -*- coding: utf-8 -*-
"""
Anti-debugging and anti-VM detection module for Tele Browser
"""

import os
import sys
import time
import psutil
import platform

def check_debugger():
    """
    Check if a debugger is attached to the process
    Returns True if debugger detected, exits application
    """
    try:
        # Check for common debugger processes on Linux
        debugger_processes = [
            'gdb', 'lldb', 'strace', 'ltrace', 'radare2', 'r2',
            'ida', 'ida64', 'x64dbg', 'ollydbg', 'windbg'
        ]
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if any(dbg in proc_name for dbg in debugger_processes):
                    print("Debugger detected! Exiting for security.", file=sys.stderr)
                    sys.exit(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check for ptrace (Linux-specific)
        if platform.system() == 'Linux':
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('TracerPid:'):
                            tracer_pid = int(line.split(':')[1].strip())
                            if tracer_pid != 0:
                                print("Debugger attached (TracerPid)! Exiting.", file=sys.stderr)
                                sys.exit(1)
            except:
                pass
        
        # Check for common debugging environment variables
        debug_env_vars = ['PYDEVD_LOAD_VALUES_ASYNC', 'PYCHARM_HOSTED', 'PYTHONBREAKPOINT']
        for var in debug_env_vars:
            if var in os.environ:
                print(f"Debug environment detected ({var})! Exiting.", file=sys.stderr)
                sys.exit(1)
                
    except Exception as e:
        # Silent fail - don't want to crash the app on detection errors
        pass
    
    return False


def check_vm():
    """
    Check if running in a virtual machine
    Returns True if VM detected, exits application
    """
    try:
        vm_indicators = []
        
        # Check CPU info for VM indicators (Linux)
        if platform.system() == 'Linux':
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read().lower()
                    vm_keywords = ['hypervisor', 'vmware', 'virtualbox', 'kvm', 'qemu', 'xen']
                    if any(keyword in cpuinfo for keyword in vm_keywords):
                        vm_indicators.append('cpuinfo')
            except:
                pass
        
        # Check DMI/SMBIOS info
        try:
            dmi_paths = [
                '/sys/class/dmi/id/product_name',
                '/sys/class/dmi/id/sys_vendor',
                '/sys/class/dmi/id/board_vendor',
                '/sys/class/dmi/id/bios_vendor'
            ]
            
            vm_vendors = ['vmware', 'virtualbox', 'qemu', 'kvm', 'xen', 'microsoft corporation', 'innotek']
            
            for path in dmi_paths:
                try:
                    with open(path, 'r') as f:
                        content = f.read().lower().strip()
                        if any(vendor in content for vendor in vm_vendors):
                            vm_indicators.append(f'dmi-{os.path.basename(path)}')
                except:
                    pass
        except:
            pass
        
        # Check for VM-specific devices
        if platform.system() == 'Linux':
            try:
                with open('/proc/scsi/scsi', 'r') as f:
                    scsi_info = f.read().lower()
                    if 'vbox' in scsi_info or 'vmware' in scsi_info or 'qemu' in scsi_info:
                        vm_indicators.append('scsi')
            except:
                pass
        
        # Check MAC address for VM vendors
        try:
            import re
            if platform.system() == 'Linux':
                result = os.popen('cat /sys/class/net/*/address 2>/dev/null').read()
                vm_mac_prefixes = [
                    '00:05:69', '00:0c:29', '00:1c:14', '00:50:56',  # VMware
                    '08:00:27',  # VirtualBox
                    '52:54:00',  # KVM/QEMU
                    '00:16:3e'   # Xen
                ]
                for prefix in vm_mac_prefixes:
                    if prefix.lower() in result.lower():
                        vm_indicators.append('mac-address')
                        break
        except:
            pass
        
        # If VM detected, exit
        if vm_indicators:
            print(f"Virtual Machine detected ({', '.join(vm_indicators)})! Exiting for security.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        # Silent fail
        pass
    
    return False


def anti_debug_loop():
    """
    Continuously monitor for debuggers and VMs in background thread
    Runs every 5 seconds
    """
    while True:
        try:
            check_debugger()
            check_vm()
            time.sleep(5)  # Check every 5 seconds
        except SystemExit:
            # Re-raise system exit to allow clean shutdown
            raise
        except Exception:
            # Continue monitoring even if checks fail
            pass
        

def initialize():
    """
    Initialize anti-debugging protections
    Called at application startup
    """
    check_debugger()
    check_vm()
    print("Security checks initialized.", file=sys.stderr)


# Run initial checks when module is imported
if __name__ != '__main__':
    # Only run on import, not when executed directly
    pass