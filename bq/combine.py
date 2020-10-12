#! /usr/bin/python3.7
# -- coding: utf-8 -- **

import os
import time
import multiprocessing
import utils as utils

CHECKTIME = 5
Filepath = '../data/task_done.txt'

while True: ## poll and recon
    # wait for a poll
    time.sleep(CHECKTIME)

    # check for the last finished task
    f = open(Filepath)
    lines = f.readlines()
    last_line = lines[-1]
    num = last_line.split(" ")[0]
    f.close()
    print(f"Last finished task is: {num}.")

    # send a check request to task_log.py
    req = "polling"
    new_flag, log = utils.task_log(req, num)

    # start a recon task or wait for the next poll
    if new_flag:
        cmd, num, name, hospital, state, info = utils.divide_a_log(log)
        p1 = multiprocessing.Process(target=utils.run,args=(cmd,))
        p2 = multiprocessing.Process(target=utils.estimate,args=(num,name,hospital,state,info,))
        p1.start()
        p2.start()

    else:
        pass

    # wait for the next poll
    time.sleep(3*CHECKTIME)
    
