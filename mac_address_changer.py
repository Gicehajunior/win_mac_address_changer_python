#!/usr/bin/env python

import subprocess
import regex as re
import string
import random
from time import sleep

# the registry path of network interfaces
network_interface_reg_path = r"HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e972-e325-11ce-bfc1-08002be10318}"

def generate_random_mac_address():
    """Generate and return a MAC address in the format of WINDOWS"""
    # uppercase the hexdigits
    uppercased_hexdigits = ''.join(set(string.hexdigits.upper()))

    # making second character to be either; 2, 4, A, or E
    return random.choice(uppercased_hexdigits) + random.choice("24AE") + "".join(random.sample(uppercased_hexdigits, k=10))

def wipe_off_mac_address(mac): 
    return "".join(c for c in mac if c in string.hexdigits).upper()  


def connected_adapters_mac_address(): 
    # return the connected mac addres
    connected_adapters_mac = [] 

    for potential_mac in subprocess.check_output("getmac").decode().splitlines(): 
        potential_mac_object_array = potential_mac.split()   

        if len(potential_mac_object_array) > 2 or len(potential_mac_object_array) == 0 or potential_mac_object_array[0] == "===================":
            pass
        else: 
            transport_name = potential_mac_object_array[1].replace("\\Device\\Tcpip_", "")
            connected_adapters_mac.append((potential_mac_object_array[0], transport_name)) 
 
    return connected_adapters_mac

def adapter_choice(connected_adapters_mac):  
    if len(connected_adapters_mac) <= 1: 
        return connected_adapters_mac[0]

    try:
        choice = int(input("Please choose the interface you want to change the MAC address:")) 
        return connected_adapters_mac[choice]
    except: 
        print("Not a valid choice, quitting...")
        exit()

def change_mac_address(adapter_transport_name, new_mac_address):
    # get available mac addresses from registry
    output = subprocess.check_output(f"reg QUERY " +  network_interface_reg_path.replace("\\\\", "\\")).decode()
    # print(output)

    for interface in re.findall(rf"{network_interface_reg_path}\\\d+", output): 
        adapter_index_from_adapter_list = int(interface.split("\\")[-1])

        interface_content = subprocess.check_output(f"reg QUERY {interface.strip()}").decode()
        # print(interface_content)
        
        if adapter_transport_name in interface_content:  
            subprocess.check_output(f"reg add {interface} /v NetworkAddress /d {new_mac_address} /f").decode()
            
            break
    
    return adapter_index_from_adapter_list

def refresh_adapter(adapter_index_from_adapter_list):
    # refresh adapter by disabling and enabling
    disable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index_from_adapter_list} call disable").decode()
    print("[+] Adapter is rebooting...")
    if disable_output:
        enable_output = subprocess.check_output(f"wmic path win32_networkadapter where index={adapter_index_from_adapter_list} call enable").decode()
        print("[+] Adapter restarted successfully.")
    
    return disable_output, enable_output


if __name__ == "__main__": 
    counter = 0
    while True:
        sleep(3600)
        counter += 1

        print(f"\n\n[*] System Mac address ready for change(Times now: {counter})!")
        new_mac_address = generate_random_mac_address() 
        
        connected_adapters_mac = connected_adapters_mac_address()

        old_mac_address, target_transport_name = adapter_choice(connected_adapters_mac)
        
        print("[*] Old MAC address:", old_mac_address)
        adapter_index_from_adapter_list_error = ''

        try:
            adapter_index_from_adapter_list = change_mac_address(target_transport_name, new_mac_address)
        except subprocess.CalledProcessError as e:
            adapter_index_from_adapter_list_error = e.output 

        if adapter_index_from_adapter_list_error:
            if adapter_index_from_adapter_list_error == "b''":
                print("Probably an encoding error!")
            else:
                print(f"Error Occurred: {adapter_index_from_adapter_list_error}")
        else:
            print("[+] Changed to:", new_mac_address)
            disable_output, enable_output = refresh_adapter(adapter_index_from_adapter_list) 
