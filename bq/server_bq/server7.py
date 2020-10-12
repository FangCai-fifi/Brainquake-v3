#! /usr/bin/python3.7
# -- coding: utf-8 -- **

import sys
import socket
import time
import pickle
import os
import tqdm
import utils
import utils_scs

HEADERSIZE = 10
SEPARATOR = '<SEPARATOR>'
BUFFER_SIZE = 4096
host = '0.0.0.0'
port = 6669


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind((socket.gethostname(), 1241))
s.bind((host, port))
s.listen(5)
task_flag = 0 # whether a task is on
fs_flag = 0 # whether a task is done

while True: # Our server is always working on

    # Now we are listening on port 6669.
    clientsocket, address = s.accept()
    print(f'Connection from {address} has been established.')

    while True:
        # receive a task request: new task or check
        task = utils_scs.text_recv(clientsocket)
        print(f'task: {task}')

        if task == '1': # task 1: reconstruction
    
            task_flag = 1 # a task starts here
            fs_flag = 0 # a freesurfer recon task has not been completed
            # receive a T1 file
            number = utils_scs.file_recv(clientsocket)
            print('T1 file received')
            # here we read the log
            log, i = utils.read_a_log(num=number)
            clientsocket, address = s.accept()
            print(f'Connection from {address} has been established.')
            time.sleep(1)
            utils_scs.text_send(clientsocket, log)
            clientsocket.close()
            fs_flag = 1 # a freesurfer recon task has been completed
            break

        elif task == '2': # task 2: check
            clientsocket.close()
            clientsocket, address = s.accept()
            print(f'Connection from {address} has been established.')
            time.sleep(1)
            check_log = utils_scs.text_recv(clientsocket)
            # print(check_log)
            [num, name, hospital, state, info] = check_log.split(' ')
            if num == 'None':
                num = None
            if name == 'None':
                name = None
            logs, i = utils.task_log(req='client', num=num, name=name, hospital=hospital)
            print(logs)
            time.sleep(1)
            utils_scs.text_send(clientsocket, logs)
            time.sleep(2)
            clientsocket.close()
            break