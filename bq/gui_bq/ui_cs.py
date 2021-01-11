#! /usr/bin/python3.7
# -- coding: utf-8 -- **

import sys
import socket
import time
import pickle
import os
import tqdm
import utils_cs

import PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog
import tkinter as tk
from tkinter import filedialog

from form import Ui_BrainQuake_v3

HEADERSIZE = 10
SEPARATOR = '<SEPARATOR>'
BUFFER_SIZE = 4096
host = '166.111.152.123'
port = 6669

class Worker(QThread): # Multi-thread module

    progressBarValue = pyqtSignal(int)
    log = pyqtSignal(str)

    def __init__(self):
        super(Worker, self).__init__()

    def run(self):
        self.s1 = utils_cs.create_socket(host, port)
        time.sleep(1)
        self.task_type = '1'
        utils_cs.text_send(self.s1, self.task_type)
        self.filesize = os.path.getsize(self.pat_filepath)
        
        # sending a T1 file
        time.sleep(1)
        self.s1.send(f'{self.filename}{SEPARATOR}{self.filesize}'.encode())
        time.sleep(1)
        # progress = tqdm.tqdm(range(self.filesize), f'Sending {self.filename}', unit="B", unit_scale=True, unit_divisor=1024)
        with open(self.pat_filepath, "rb") as f:
            j = 0
            # for _ in progress:
            while True:
                # read the bytes from the file
                bytes_read = f.read(BUFFER_SIZE)
                j = j + 1
                i = int(100*j*BUFFER_SIZE/self.filesize)
                if not bytes_read: # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                self.s1.sendall(bytes_read)
                # progress.update(len(bytes_read))
                self.progressBarValue.emit(i)      
        f.close()
        self.s1.close()
        # receive a msg
        # time.sleep(1)
        self.s2 = utils_cs.create_socket(host, port)
        log_read = utils_cs.text_recv(self.s2)
        self.log.emit(log_read)
        self.s2.close()

class Checker(QThread):

    logs = pyqtSignal(str)

    def __init__(self):
        super(Checker, self).__init__()

    def run(self):
        self.s1 = utils_cs.create_socket(host, port)
        time.sleep(1)
        self.task_type = '2'
        utils_cs.text_send(self.s1, self.task_type)
        self.s1.close()

        # send a request to check
        self.s2 = utils_cs.create_socket(host, port)
        time.sleep(1)
        if self.name == '<name>':
            self.name = 'None'
        if self.number == '<number>':
            self.number = 'None'
        self.req = 'client'
        self.state = 'None'
        self.info = 'None'
        self.check_log = ' '.join([self.number, self.name, self.hospital, self.state, self.info])
        print(self.check_log)
        utils_cs.text_send(self.s2, self.check_log)
        logs = utils_cs.text_recv(self.s2)
        # print(logs)
        self.logs.emit(logs)
        self.s2.close()

class MyPyQT_Form(QtWidgets.QWidget, Ui_BrainQuake_v3, Worker, Checker):

    def __init__(self):
        super(MyPyQT_Form, self).__init__()
        self.setupUi(self)
        self.progressBar.setValue(0)
        self.thread_1 = Worker()
        self.thread_1.progressBarValue.connect(self.Progress)
        self.thread_1.log.connect(self.Log_pre)
        self.comboBox_2.setEditable(True)
        self.comboBox_3.setEditable(True)
        self.namelist = []
        self.numberlist = []
        self.thread_2 = Checker()
        self.thread_2.logs.connect(self.Logs_pre)
        
    def Browse(self):
        self.directory = QFileDialog.getOpenFileName(self, "getOpenFileName", "./", "All Files (*);;Nifti Files (*.nii.gz)")
        self.Filepath = self.directory[0]
        self.Filename = self.directory[0].split('/')[-1]
        self.Patname = self.directory[0].split('/')[-1].split('.')[0]
        self.textBrowser.setText(self.Filepath)
        self.textBrowser_21.setText(self.Filename)  
        self.thread_1.pat_name = self.Patname 
        self.thread_1.filename = self.Filename
        self.thread_1.pat_filepath = self.Filepath  
        self.progressBar.setValue(0) 

    def Upload(self):
        self.thread_1.start()

    def Progress(self, i):
        self.progressBar.setValue(i)
    
    def Log_pre(self, log_read):
        self.textBrowser_21.setText(log_read)
        number = log_read.split(' ')[0]
        name = log_read.split(' ')[1]
        self.numberlist.append(number)
        self.comboBox_3.addItems(self.numberlist)
        self.namelist.append(name)
        self.comboBox_2.addItems(self.namelist)

    def Check(self):
        self.thread_2.number = self.comboBox_3.currentText()
        self.thread_2.name = self.comboBox_2.currentText()
        self.thread_2.hospital = self.comboBox_4.currentText()
        self.thread_2.start()
    
    def Logs_pre(self, logs):
        self.textBrowser_2.setText(logs)

    def Name(self):
        pass

    def Id(self):
        pass

    def Hos(self):
        pass

    def PreView(self):
        pass
    
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,'本程序',"Quit?",QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            os._exit(0)
        else:
            event.ignore()

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    my_pyqt_form = MyPyQT_Form()
    my_pyqt_form.show()
    sys.exit(app.exec_())      