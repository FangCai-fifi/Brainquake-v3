#! /usr/bin/python3.7
# -- coding: utf-8 -- **

import sys
import os
import time
import nibabel as nib
import numpy as np

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import skimage
from skimage import measure
import scipy
from scipy import ndimage
import sklearn
from sklearn.mixture import GaussianMixture

import PyQt5
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QFileDialog, QSlider, QGraphicsScene, QListWidget

from Ui_form1 import Ui_EEP
import eePipeline

DIR = f"/Users/fangcai/Documents/PYTHON"

class MyFigure(FigureCanvas):

    def __init__(self, width=5, height=3, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super(MyFigure,self).__init__(self.fig)
        self.axes = self.fig.add_subplot(111, projection='3d')
    
    def plotScatter(self, x, y, z):
        self.axes.scatter(x, y, z, marker='.')
        self.axes.set_title('3D Electrodes')
        self.axes.set_xlim(0, 256)
        self.axes.set_ylim(0, 256)
        self.axes.set_zlim(0, 256)
    
    def plotLabels(self, labels, num):
        color = ['r','g','b','k','m','c','y','rosybrown','lightcoral','maroon']
        for i in np.arange(1, num+1):
            xs, ys, zs = np.where(labels==i)
            self.axes.scatter(xs, ys, zs, c=color[np.mod(i,10)], marker='.', label=f"{i}")
            #ax.voxels(xs,ys,zs)
        self.axes.set_xlim(0, 256)
        self.axes.set_ylim(0, 256)
        self.axes.set_zlim(0, 256)
        self.axes.set_title('Clustered 3D Electrodes')
        self.axes.legend()
    
    def plotSelLabel(self, labels, num):
        color = ['r','g','b','k','m','c','y','rosybrown','lightcoral','maroon']
        for i in np.arange(0, len(num)):
            xs, ys, zs = np.where(labels==num[i])
            if xs.shape[0] > 0:
                self.axes.scatter(xs, ys, zs, c=color[np.mod(num[i],10)], marker='.', label=f"{num[i]}")
        self.axes.set_xlim(0, 256)
        self.axes.set_ylim(0, 256)
        self.axes.set_zlim(0, 256)
        self.axes.set_title('Selected Label(s)')
        self.axes.legend()

class Align(QThread):  

    progress = pyqtSignal(str)

    def __init__(self):
        super(Align, self).__init__()
    
    def run(self, iter=10):   
        CT_dir = f"{DIR}/{self.patient}_test/CT"
        mri_dir = f"{DIR}/{self.patient}_test/{self.patient}/mri"
        
        ## Registration
        log_progress = 'Registering...'
        self.progress.emit(log_progress)
        # eePipeline.align(
        #     inp = f"{CT_dir}/{self.patient}CT.nii.gz",
        #     ref = f"{mri_dir}/orig.nii.gz",
        #     xfm = f"{CT_dir}/fslresults/{self.patient}invol2refvol.mat",
        #     out = f"{CT_dir}/fslresults/{self.patient}outvol.nii.gz",
        #     dof = 12,
        #     searchrad = True,
        #     bins = 256,
        #     interp = None,
        #     cost = "mutualinfo",
        #     sch = None,
        #     wmseg = None,
        #     init = None,
        #     finesearch = None,
        # )
        time.sleep(1)
        
        ## Masking
        log_progress = 'Masking...'
        self.progress.emit(log_progress)
        CTreg = os.path.join(f"{CT_dir}/fslresults", f"{self.patient}outvol.nii.gz")
        mask = os.path.join(mri_dir, f"mask.mgz")
        img_ct = nib.load(CTreg)
        img_mask = nib.load(mask)
        data_ct = img_ct.get_fdata()
        data_mask = img_mask.get_fdata()
        # eroding the mask
        data_mask_ero = ndimage.morphology.binary_erosion(data_mask, iterations=iter)
        # masking
        data_ct[data_mask_ero==0] = 0
        data_ct[data_ct<0] = 0
        img0 = nib.Nifti1Image(data_ct, img_ct.affine)
        nib.save(img0, os.path.join(f"{CT_dir}/fslresults", f"{self.patient}intracranial.nii.gz"))
        time.sleep(1)
        log_progress = 'Done!'
        self.progress.emit(log_progress)

class Label(QThread):

    data = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self):
        super(Label, self).__init__()

    def run(self):
        ## finding connected components
        data_elec = np.copy(self.data_ct)
        data_elec[self.data_ct < self.thre] = 0
        data_elec[self.data_ct >= self.thre] = 1
        labels, num = measure.label(data_elec, return_num = True)
        
        elec_data = {'labels': labels, 'num': num}
        self.data.emit(elec_data)
        self.finished.emit()


class EEP(QtWidgets.QWidget, Ui_EEP, Align, Label):

    def __init__(self):
        super(EEP, self).__init__()
        self.setupUi(self)
        self.ero = 10
        self.thread_1 = Align()
        self.thread_1.progress.connect(self.show_progress)
        self.thread_2 = Label()
        self.thread_2.data.connect(self.save_data)
        self.thread_2.finished.connect(self.elecPlot)

    def choose_a_CTfile(self):
        self.directory_ct = QFileDialog.getOpenFileName(self, "getOpenFileName", "./", "All Files (*);;Nifti Files (*.nii.gz)")
        self.Filepath_ct = self.directory_ct[0]
        self.Filename_ct = self.directory_ct[0].split('/')[-1]
        self.Patname_ct = self.directory_ct[0].split('/')[-1].split('.')[0].split('C')[0]
        self.textBrowser.setText(self.Filepath_ct)
        self.textBrowser_3.setText(self.Patname_ct)
        
    def choose_a_T1file(self):
        self.directory_t1 = QFileDialog.getOpenFileName(self, "getOpenFileName", "./", "All Files (*);;Nifti Files (*.nii.gz)")
        self.Filepath_t1 = self.directory_t1[0]
        self.Filename_t1 = self.directory_t1[0].split('/')[-1]
        self.Patname_t1 = self.directory_t1[0].split('/')[-1].split('.')[0].split('T')[0]
        self.textBrowser_2.setText(self.Filepath_t1)
        self.textBrowser_3.setText(self.Patname_t1)

    def compute_EEP(self):
        assert self.Patname_ct == self.Patname_t1, 'Not the same patient!'
        self.thread_1.patient = self.Patname_ct
        self.thread_1.start()

    def show_progress(self, log_progress):
        self.textBrowser_6.setText(log_progress)

    def choose_a_brain(self):
        self.directory_br = QFileDialog.getOpenFileName(self, "getOpenFileName", "./", "All Files (*);;Nifti Files (*.nii.gz)")
        self.Filepath_br = self.directory_br[0]
        self.Filename_br = self.directory_br[0].split('/')[-1]
        # self.Patname = self.directory_br[0].split('/')[-1].split('.')[0].split('C')[0]
        self.textBrowser_4.setText(self.Filepath_br)

    def choose_an_elecfile(self):
        ## 此处需改进，配准完后可以自动将file加载进来
        self.directory_ctcra = QFileDialog.getOpenFileName(self, "getOpenFileName", "./", "All Files (*);;Nifti Files (*.nii.gz)")
        self.Filepath_ctcra = self.directory_ctcra[0]
        self.Filename_ctcra = self.directory_ctcra[0].split('/')[-1]
        # self.Patname = self.directory_br[0].split('/')[-1].split('.')[0].split('C')[0]
        self.textBrowser_5.setText(self.Filepath_ctcra)

        self.CTcranial = nib.load(self.Filepath_ctcra)
        self.data_ctcra = self.CTcranial.get_fdata()
        
        ## 此处有bug，加入未选中文件的判断
        self.maxval = np.max(self.data_ctcra)
        self.minval = np.min(self.data_ctcra)
        self.horizontalSlider.setMinimum(self.minval)
        self.horizontalSlider.setMaximum(self.maxval)
        self.val = 0.2 * self.maxval
        self.horizontalSlider.setValue(self.val)
        self.x, self.y, self.z = np.where(self.data_ctcra > self.val)
        self.display()
    
    def save_data(self, elec_data):
        self.labels = elec_data['labels']
        self.num = elec_data['num']
        self.numlist = np.arange(1, self.num+1)
    
    def display(self, type=1, labelsPlot=np.zeros((256,256,256)), numPlot=0):
        self.F = MyFigure(width=4, height=3, dpi=100)
        if type == 1:
            self.F.plotScatter(x=self.x, y=self.y, z=self.z)
        elif type == 2:
            self.F.plotLabels(labels=labelsPlot, num=numPlot)
        elif type == 3:
            self.F.plotSelLabel(labels=self.labels, num=self.items)
        self.scene = QGraphicsScene()  #创建一个场景
        self.scene.addWidget(self.F)   #将图形元素添加到场景中
        self.graphicsView.setScene(self.scene) #将创建添加到图形视图显示窗口
        self.graphicsView.show()       #显示

    def setThreshold(self):
        self.val = self.horizontalSlider.value()
        self.x, self.y, self.z = np.where(self.data_ctcra > self.val)
        self.display(type=1)

    def assign_labels(self):
        self.thread_2.data_ct = self.data_ctcra
        self.thread_2.thre = self.val
        self.thread_2.start()
    
    def elecPlot(self):
        # set list widget
        self.listWidget.clear()
        for i in np.arange(1, self.num+1):
            self.listWidget.addItem(f"{str(i)}")
        self.listWidget.setWindowTitle('Electrodes Labels')
        self.listWidget.show()
        self.display(type=2, labelsPlot=self.labels, numPlot=self.num)
        
    def clicked(self):
        # self.item = self.listWidget.selectedItems()[-1]
        items = self.listWidget.selectedItems()
        self.items = []
        for item in items:
            item = int(item.text())
            self.items.append(item)
        # print(int(item.text()))
        # print(len(items))
    
    # def dclicked(self):
    #     self.listWidget.editItem()

    def view_labels(self):
        self.clicked()
        self.display(type=3)

    def combine_labels(self):
        self.clicked()
        minlabel = np.min(self.items)
        for item in self.items:
            self.labels[self.labels==item] = minlabel
            # if item != minlabel:
            #     self.numlist.remove(item)
        self.num = self.num - len(self.items) + 1
        self.display(type=2, labelsPlot=self.labels, numPlot=self.num)
        # self.display(type=3, labelsPlot=self.labels, num=self.numlist)
    
    def delete_labels(self):
        listItems=self.listWidget.selectedItems()
        # self.clicked()
        if not listItems: return
        # if not self.items: return
        # for item in self.items:      
        for item in listItems:
            self.listWidget.takeItem(self.listWidget.row(item))
            self.labels[self.labels==int(item.text())] = 0
            # self.listWidget.takeItem(self.listWidget.row(str(item)))
            # self.labels[self.labels==item] = 0
        self.num = self.num - len(listItems)
        # self.num = self.num - len(self.items)

    def divide_labels(self):
        self.clicked()
        for item in self.items:
            self.data_elec1 = np.copy(self.data_ctcra)
            self.data_elec1[np.where(self.labels!=item)] = 0
            xs, ys, zs = np.where(self.data_elec1 != 0)
            X = np.transpose(np.vstack((xs,ys,zs)))
            model = GaussianMixture(n_components=2, init_params='random').fit(X)
            X1 = X[model.predict(X)==0]
            X2 = X[model.predict(X)==1]
            self.item = item
        self.data_elec1[X1[:,0], X1[:,1], X1[:,2]] = 1
        self.data_elec1[X2[:,0], X2[:,1], X2[:,2]] = 2
        self.listWidget.addItem(str(self.num+1))
        self.labels[self.data_elec1==2] = self.num + 1
        self.num = self.num + 1
        self.display(type=2, labelsPlot=self.data_elec1, numPlot=2)

    def save_an_elecList(self):
        self.display(type=2, labelsPlot=self.labels, numPlot=self.num)
        # np.save(f"{DIR}/{self.Patname_ct}_test/{self.Patname_ct}labels.npy", self.labels)

    def graph_0(self):
        pass

    def graph_1(self):
        pass

    def graph_2(self):
        pass

    def graph_3(self):
        pass

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self,'本程序',"Quit?",QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            os._exit(0)
        else:
            event.ignore()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = EEP()
    widget.show()
    sys.exit(app.exec_())
