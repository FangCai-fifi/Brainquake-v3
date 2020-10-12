#! /usr/bin/python3.7
# -- coding: utf-8 -- **

import os
import time

Filepath = '../data/task_log.txt'
Filepath2 = '../data/task_done.txt'
Filename1 = 'task_log.txt'
Filename2 = 'task_done.txt'
CHECKTIME = 10

def read_a_log(num=None, name=None, hospital=None):
    """A function to open the task log and read the log content

    Parameter
    ---------
    num : str, optional
        to carry the object number '#xxxx' of the request
    name : str, optional
        the patient name
    hospital : str, optional
        the hospital name, where the patient comes from
    
    Output
    ------
    log_read : str
        the log line(s) picked
    i : int
        how many logs are returned
    """
    
    if (num == None and name == None and hospital == None):
        raise IOError('Please type in at least one piece of info about the patient(s) you ask!')

    else:
    
        f = open(Filepath, 'r')
        lines = f.readlines()
        log_read = ""
        i = 0
        for line in lines:
            if (hospital == None) or (hospital in line):
                if (name == None) or (name in line):
                    if (num == None) or (num in line):
                        log_read += line
                        i = i + 1
        f.close()
        
    # print(log_read)
    return log_read, i
    

def write_a_log(num=None, name=None, hospital=None, state=None, info=None):
    """A function to write or update a task log content
    
    Parameter
    ---------
    num : str, optional
        to carry the object number '#xxxx' of the request
    name : str, optional
        the patient name
    hospital : str, optional
        the hospital name, where the patient comes from
    state : str, optional
        the tast state, "finished", "running" or "wait"
    info : float, optional
        a number btw 0 and 1 to carry the progress rate of the request

    """

    if (num == None and name == None):
        raise IOError('Please at least type in a patient\'s name or number!')

    else:
        f = open(Filepath, 'r+')
        lines = f.readlines()
        # print(lines)
        i = 0
        for line in lines:
            i = i + 1
            if (name == None) or (name in line):
                if (num == None) or (num in line):
                    parts = line.split(' ')
                    parts[3] = state
                    parts[4] = str(info)+"\n"
                    lines[i-1] = " ".join(parts)
        # print(lines)
        f.seek(0)
        f.truncate() # Here we need an improvement!
        f.writelines(lines)
        f.close()
    return

def add_a_log(name, hospital):
    """A function to add a new task to the log

    Parameter
    ---------
    name : str
        a new patient name
    hospital : str
        the hospital where the patient comes from

    """
    if (name == None or hospital == None):
        raise IOError('Please type in both the patient name and the hospital name!')

    else:
        f = open(Filepath, 'r+')
        number_max = f.readlines()[-1].split(' ')[0]
        # print(number_max)
        num_val = int(number_max[1:]) + 1
        # print(num)
        number_new = "#" + "%04d" % num_val
        # print(number_new)
        line_new = "\n" + " ".join([number_new, name, hospital, "wait", "0"])
        # print(line_new)
        f.write(line_new)
        f.close()

    return

def pick_a_log(num):
    """A function to check polling and if available, pick the first waiting task and return its number

    Parameter
    ---------
    num : str
        to carry the object number '#xxxx' of the request, after which we check the following states

    Output
    ------
    log_read : str
        if available, the next task to start
    new_flag : bool
        whether there is a new task to start

    """
    num_val = int(num[1:]) + 1
    number_next = "#" + "%04d" % num_val

    f = open(Filepath, 'r+')
    lines = f.readlines()
    i = 0
    for line in lines:
        if not (number_next in line): # the finished task is already the last one
            new_flag = 0
            log_read = ""

        else: # the next task is in the line
            parts = line.split(" ")
            if parts[3] == "wait":
                if i < 3:
                    new_flag = 1
                    log_read = line
                    break
                else:
                    new_flag = 0
                    log_read = ""
                    break

            else:
                if parts[3] == "running":
                    i = i + 1
                num_val = int(number_next[1:]) + 1
                number_next = "#" + "%04d" % num_val

    return new_flag, log_read

def divide_a_log(log):
    parts = log.split(" ")
    num = parts[0]
    name = parts[1]
    hospital = parts[2]
    state = parts[3]
    info = parts[4]
    if num == "None":
        num = None
    if name == "None":
        name = None
    if hospital == "None":
        hospital = None
    if state == "None":
        state = None
    if info == "None":
        info = None
    filename = str(name)
    filepath = Filepath + str(name) + 'T1.nii.gz'
    cmd = f"nohup recon-all -i {filepath} -s {filename} -all -openmp 8 &>logfile"    
    cmd = f"python test.py"
    return cmd, num, name, hospital, state, info

def run(cmd):
    """
    Print the command and execute a command string on the shell (on bash).
    
    Parameters
    ----------
    cmd : str
        Command to be sent to the shell.
    """

    print(f"Running shell command: {cmd}")
    os.system(cmd)
    return

def estimate(num, name, hospital, state, info):
    while True:
        time.sleep(2*CHECKTIME)
        # receive a signal from a starting recon.py
        f = open('recon-all-status.log', 'r')
        lines = f.readlines()
        if (lines[-1].split(' ')[3] == 'finished'):
            # Here the task has finished
            fin = 1
            task_log(req='freesurfer', num=num, state='finished', info=1)
            write_to_done(req='freesurfer', num=num, name=name, hospital=hospital, state='finished', info=1)
            break
        else:
            start_time = lines[1].split(' ')[-5:-1]
            last_time = lines[-1].split(' ')[-5:-1]
            print(start_time)
            print(last_time)
            # calculate the time rest
            info = 0.88
            task_log(req='freesurfer', num=num, state='running', info=info)     
        
    return

def write_to_done(req, num, name, hospital, state, info):
    """A function to write or update a task log content
    
    Parameter
    ---------
    num : str, optional
        to carry the object number '#xxxx' of the request
    name : str, optional
        the patient name
    hospital : str, optional
        the hospital name, where the patient comes from
    state : str, optional
        the tast state, "finished", "running" or "wait"
    info : float, optional
        a number btw 0 and 1 to carry the progress rate of the request

    """

    if (num == None and name == None):
        raise IOError('Please at least type in a patient\'s name or number!')

    else:
        f = open(Filepath2, 'a+')
        line = '\n' + num + ' ' + name + ' ' + hospital + ' ' + state + ' ' + str(info)
        f.write(line)
        f.close()
    return

def task_log(req, num=None, name=None, hospital=None, state=None, info=None):
    
    if req == "client":
        logs, i = read_a_log(num, name, hospital)
        if i > 0: # we've found sth.
            print(f"Here are what we've checked!")
            print(logs)
            return logs, i

        else: # find nothing
            ## here we should ask for the patient's data from either client or dataset.
            print(f"Patient {num} {name} from {hospital} has not been found! Check out your input or please upload the patient's data! [y/n]")
            reply = input()
            if reply == "y":
                add_a_log(name, hospital)
                logs, i = read_a_log(name, hospital)
                print(f"Patient {name} from {hospital} has been added to the task line!")
                print(f"Here are what we've checked!")
                print(logs)
            return logs, i
    
    elif req == "freesurfer":
        if state == "finished":
            write_a_log(num, name, hospital, state, info)
            print(f"{req} has finished a task {num}!")
            # new_flag, log = pick_a_log(num)
            # if new_flag:
            #     print(f"A task {log} will be sent to {req} program!")
            #     ## call recon.py !!!
            #     num_next = log.split(" ")[0]
            #     write_a_log(num_next, state="running", info=0)
            # else:
            #     print(f"No new task is available!")
            # return new_flag, log
            return

        else: # state == "running"
            write_a_log(num, name, hospital, state, info)
            print(f"Log {num} has been updated!")
            return
    
    elif req == "polling":
        new_flag, log = pick_a_log(num)
        if new_flag:
            print(f"A task {log} has been detected by {req}!")
            # Here we should call a freesurfer program!
            return new_flag, log

        else:
            print(f"No task has been detected by {req}!")
            return new_flag, log
    
    else:
        raise IOError('Error: An unidentified request!')
