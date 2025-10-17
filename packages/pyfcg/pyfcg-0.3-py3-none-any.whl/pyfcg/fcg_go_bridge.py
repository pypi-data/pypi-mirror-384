####################
# Bridge to FCG Go #
####################

import os
import platform
import time

import wget
import subprocess
import atexit
from platformdirs import user_data_dir
from pathlib import Path
import socket
import shutil

import pyfcg.agent
from urllib.error import HTTPError

__all__ = [
    'init',  
    'download_fcg_go',
    'fcg_go_available',
    'launch_fcg_go',
    'next_available_socket',
    'socket_available',
    'shutdown_fcg_go',
    ]

# Global variables #
####################

platform = platform.system()
server_address = 'localhost' #: 
server_port = None #: 
fcg_go_process = None #:
fcg_go_initialized = False


def init(address=server_address, port=None, directory=None, launch=True, fcg_go_version="latest", force_download=False):
    """Establish a connection with FCG Go, downloading it if necessary."""

    global fcg_go_initialized
    if fcg_go_initialized:
        return 'FCG already active.'
    else:
        # Setting server_port and server_address
        global server_address, server_port
        server_address = address

        if port and launch:
            # Launch at given port if socket available, else error
            if socket_available(address, port):
                server_port = port
            else:
                raise Exception("Socket " + address + ":" + str(port) + " already in use.")
        elif port and not launch:
            # Set server_port to port that was specified
            server_port = port
        elif not port and launch:
            # Launch at next available socket
            server_port = next_available_socket(address, port=9600)
        elif not port and not launch:
            # set server_port to default 9600
            server_port = 9600

        if directory is None:
            directory = user_data_dir(appname="FCG Go", version=fcg_go_version)

        if launch:
            # Check whether FCG Go is available on the system, if so launch, else download, unzip, launch
            if fcg_go_available(directory) and not force_download:
                if fcg_go_process and not fcg_go_process.poll():
                    print('FCG Go has already been launched.')
                else:
                    launch_fcg_go(directory, address, server_port)
                    fcg_go_initialized = True
            else:
                if force_download:
                    print(f'(Re)installing version "{fcg_go_version}" of FCG Go...')
                else:
                    print("FCG Go not yet installed. Proceeding with installation...")

                zipfile = download_fcg_go(directory, version=fcg_go_version)
                if zipfile:
                    unzip(zipfile, directory)
                if fcg_go_available(directory):
                    launch_fcg_go(directory, address, server_port)
                    fcg_go_initialized = True
                else:
                    print("This version of FCG Go could not be located or downloaded.")


def download_fcg_go(target_directory=None, url=None, version="latest"):
    """Download FCG Go"""
    # Set url
    if url is None:
        url = 'https://emergent-languages.org/fcg-go/'
        
        # If a version was specified, add it to the url
        if version != "latest":
            url += f'{version}/'
        
        # Get platform-specific zip
        if platform == 'Darwin':
            url += 'fcg-go-macos.zip'
        elif platform == 'Linux':
            url += 'fcg-go-linux.zip'
        elif platform == 'Windows':
            url += 'fcg-go-windows.zip'

    # Download
    try:
        # If no target_directory was specified, default to user-specific data dir for this version of FCG Go
        if target_directory is None:
            target_directory = user_data_dir(appname="FCG Go", version=version)

        # If targetdirectory already exists, delete it.
        if os.path.isdir(target_directory):
            shutil.rmtree(target_directory)

        os.makedirs(target_directory)

        print('Downloading FCG Go...', end=" ")
        file = wget.download(url, out=target_directory)
        print('Done.')

    except HTTPError as exception:
        shutil.rmtree(target_directory)
        file = None
        print("HTTPError")

    return file


def fcg_go_available(target_directory):
    """Check whether FCG Go is available on the system."""
    file_name = "" 
    if platform == 'Darwin':
        file_name = '/FCG Go.app'
    elif platform == 'Linux':
        file_name = "/FCG Go"
    elif platform == 'Windows':
        file_name = "\\FCG Go.exe"
    
    if os.path.exists(target_directory + file_name):
        return True
    else:
        return None


def unzip(zip_file, target_directory):
    """Unzip zip_file into target_directory"""
    print('Extracting FCG Go...')
    if platform == 'Darwin' or platform == 'Linux':
        os.system(f'unzip "{zip_file}" -d "{target_directory}"')
    elif platform == 'Windows':
        os.system(f'tar -xf "{Path(zip_file).resolve()}" -C "{Path(target_directory).resolve()}"')
    print('Done.')
    return target_directory


def launch_fcg_go(directory, address, port):
    """Launch FCG Go"""
    if platform == 'Darwin':
        fcg_go_path = os.path.join(directory, 'FCG Go.app', 'Contents', 'MacOS','FCG Go')
    elif platform == 'Linux':
        fcg_go_path = os.path.join(directory, "FCG Go")
    elif platform == 'Windows':
        fcg_go_path = Path(os.path.join(directory, "FCG Go.exe")).resolve()

    global fcg_go_process
    fcg_go_process = subprocess.Popen([fcg_go_path,
                                       '--port', str(port), 
                                       '--address', address])
    
    if fcg_go_process.poll():
        print("Connection to FCG Go failed (subprocess could not be started successfully).")
        return False
    else:
        time.sleep(2)
        # Shut down FCG Go when Python session is exited
        atexit.register(shutdown_fcg_go)
        return True
    

def next_available_socket(address="localhost", port=9600):
    """Returns the port number of the next available socket."""
    if socket_available(address, port):
        return port
    else:
        return next_available_socket(address, port= port + 1)


def socket_available(address="localhost", port=9600):
    "Returns True if socket is available, false otherwise."
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex((address, port)) == 0:
            return False
        else:
            return True


def shutdown_fcg_go():
    """Shut down FCG Go."""
    global fcg_go_process
    fcg_go_process.terminate()
    fcg_go_process = None

