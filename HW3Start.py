# -*- coding: utf-8 -*-
"""
Created on Tue Sep 26 22:23:23 2017

@author: Austin
"""


import sys
from PyQt5.QtWidgets import (QWidget, QTreeView, QMessageBox, QHBoxLayout, 
                             QFileDialog, QLabel, QSlider, QCheckBox, 
                             QLineEdit, QVBoxLayout, QApplication, QPushButton,
                             QTableWidget, QTableWidgetItem,QSizePolicy,
                             QGridLayout,QGroupBox)
from PyQt5.QtCore import Qt, QTimer, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5 import QtWidgets
import numpy as np
from scipy import stats
import statistics
import math
#import collections
import PyQt5
from scipy.stats import lognorm

import os
 
from matplotlib.backends import qt_compat
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import matplotlib.mlab as mlab

#to do:
    #fix chi sq
    #remove open function

rcParams.update({'figure.autolayout': True})

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        FigureCanvas.mpl_connect(self,'button_press_event', self.export)
        
    def export(self,event):
        filename = "ExportedGraph.pdf"
        self.fig.savefig(filename)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Saved a copy of the graphics window to {}".format(filename))
        #msg.setInformativeText("This is additional information")
        msg.setWindowTitle("Saved PDF File")
        msg.setDetailedText("The full path of the file is \n{}".format(os.path.abspath(os.getcwd())))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setWindowModality(Qt.ApplicationModal)
        msg.exec_()
        print("Exported PDF file")
        
class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself frequently with a new plot."""
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.axes.set_xlabel("X Label")
        self.axes.set_ylabel("Y Label")
        self.axes.set_title("Title")
             
    def plot_histogram(self,data_array,bins):
        data_label="Temperature"
        title="Probability Density Function Plots"
        self.axes.cla() #Clear axes
        self.axes.hist(data_array,bins=bins,
                       normed=True,label="Emperical",
                       edgecolor='b',color='y')
        self.axes.set_xlabel(data_label)
        self.axes.set_ylabel("Estimated Prob. Density Funct.")
        self.axes.set_title(title)
        self.axes.legend(shadow=True)
        self.draw()
        print("Finished Drawing Normalized Histogram.")
          
    def plot_normal(self,mu,sigma):
        xmin,xmax = self.axes.get_xlim()
        x = np.linspace(mu-3*sigma,mu+3*sigma, 100)
        y = mlab.normpdf(x, mu, sigma)
        self.axes.plot(x,y,label="Normal")
        self.axes.legend(shadow=True)
        self.draw()
        print("Finished Drawing Normal Distribution.")

        
class StatCalculator(QtWidgets.QMainWindow):#(QWidget):
    def __init__(self):
        super().__init__()

        # Upon startup, run a user interface routine
        self.init_ui()
              
    def init_ui(self):
        #Builds GUI
        self.setGeometry(200,200,1000,800)
        main_widget=QWidget()
        #majorWidget=QWidget()
        self.setCentralWidget(main_widget)#(majorWidget)
        
        openFile = QtWidgets.QAction(QIcon('Open-icon.png'),'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        #openFile.triggered.connect(self.openingFile)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        self.setWindowTitle('Bounding Data - Austin V')
        self.activateWindow()
        self.raise_()
        self.show()

        #super().__init__()#super(StatCalculator, self).__init__(self)
        self.load_button = QPushButton('Load Data',self)
        self.load_button.clicked.connect(self.simpLoad)

        #headers
        self.sumStat = QLabel("====Summary Statistics====")
        self.confInv = QLabel("====Confidence Interval====")
        self.bndLim = QLabel("====Upper Bounds on Variance====")
        
        #updated objects
        self.count_label = QLabel("Count: Not Computed Yet",self)     
        self.mean_label = QLabel("Mean: Not Computed Yet",self)
        self.stdDev_label = QLabel("Standard Deviation: Not Computed Yet",self)
        self.stdErr_label = QLabel("Standard Error: Not Computed Yet",self)
        self.var_label = QLabel("Variance: Not Computed Yet",self)
        self.tval_label = QLabel("Student-t Value: Not Computed Yet",self)
        self.lowmean_label = QLabel("Mean Lower Bound (t): Not Computed Yet",self)
        self.highmean_label = QLabel("Mean Upper Bound (t): Not Computed Yet",self)
        self.lowbnd_label=QLabel("Mean Lower Bound (norm): Not Computed Yet",self)
        self.highbnd_label=QLabel("Mean Upper Bound (norm): Not Computed Yet",self)
        self.lowbndmc_label=QLabel("Mean Lower Bound (monte): Not Computed Yet",self)
        self.highbndmc_label=QLabel("Mean Upper Bound (monte): Not Computed Yet",self)        
        self.chisq_label = QLabel("Chi Squared: Not Computed Yet",self)
        self.maxvar_label = QLabel("Maximum Variance: Not Computed Yet",self)
        self.maxstd_label = QLabel("Maximum Standard Deviation: Not Computed Yet",self)
        #Set up a Table to display data
        self.data_table = QTableWidget()
        #self.data_table.itemSelectionChanged.connect(self.compute_stats)
        
        self.main_widget = QWidget(self)
        self.graph_canvas = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
        
        #Define where the widgets go in the window
        #We start by defining some boxes that we can arrange
        
        #Create a GUI box to put all the table and data widgets in
        table_box = QGroupBox("Data Table")
        #Create a layout for that box using the vertical
        table_box_layout = QVBoxLayout()
        #Add the widgets into the layout
        self.inst1 = QLabel("1) Select desired cells in table")
        self.inst2 = QLabel("2) Set desired alpha confidence (0-1) in lower right")
        self.inst3 = QLabel("3) Click Calculate button at lower right. Calculations take several seconds.")
        #table_box_layout.addWidget(self.load_button)
        table_box_layout.addWidget(self.inst1)
        table_box_layout.addWidget(self.inst2)
        table_box_layout.addWidget(self.inst3)
        table_box_layout.addWidget(self.data_table)
        #setup the layout to be displayed in the box
        table_box.setLayout(table_box_layout)
        
        #entry = QTableWidgetItem("{}".format(row_values[col]))
        self.data_table.setRowCount(4)
        self.data_table.setColumnCount(1)
        self.data_table.setItem(-1, 1, QTableWidgetItem("{}".format(0.763)))
        self.data_table.setItem(0, 1, QTableWidgetItem("{}".format(0.720)))
        self.data_table.setItem(1, 1, QTableWidgetItem("{}".format(0.751)))
        self.data_table.setItem(2, 1, QTableWidgetItem("{}".format(0.743)))

        
        #repeat the box layout for Statistics
        stats_box = QGroupBox("Summary Statistics")
        stats_box_layout = QVBoxLayout()
        stats_box_layout.addWidget(self.sumStat)
        stats_box_layout.addWidget(self.count_label)
        stats_box_layout.addWidget(self.mean_label)
        stats_box_layout.addWidget(self.stdDev_label)
        stats_box_layout.addWidget(self.stdErr_label)
        stats_box_layout.addWidget(self.var_label)
        stats_box.setLayout(stats_box_layout)
        stats_box_layout.addWidget(self.confInv)
        stats_box_layout.addWidget(self.tval_label)
        stats_box_layout.addWidget(self.lowmean_label)
        stats_box_layout.addWidget(self.highmean_label)
        stats_box_layout.addWidget(self.lowbnd_label)
        stats_box_layout.addWidget(self.highbnd_label)        
        stats_box_layout.addWidget(self.lowbndmc_label)
        stats_box_layout.addWidget(self.highbndmc_label) 
        stats_box_layout.addWidget(self.bndLim)
        stats_box_layout.addWidget(self.chisq_label)
        stats_box_layout.addWidget(self.maxvar_label)
        stats_box_layout.addWidget(self.maxstd_label)

 
        # Create textbox
        self.textbox = QLineEdit(self)
        self.textbox.move(20, 20)
        self.textbox.resize(280,40)
        self.textbox.setObjectName("alpha")
 
        # Create a button in the window
        self.button = QPushButton('Calculate bound values with new Alpha', self)
        self.button.move(20,80)
 
        # connect button to function on_click
        self.button.clicked.connect(self.compute_stats)
        self.show()
        self.alpha_label = QLabel("Input a significance between 0 and 1",self)
        
        tPlot = QGroupBox("Confidence Selection")
        distribution_box_layout= QVBoxLayout()
        distribution_box_layout.addWidget(self.alpha_label)
        distribution_box_layout.addWidget(self.textbox)
        distribution_box_layout.addWidget(self.button)
        tPlot.setLayout(distribution_box_layout)

        #Now we can set all the previously defined boxes into the main window
        grid_layout = QGridLayout()
        grid_layout.addWidget(table_box,0,0) 
        grid_layout.addWidget(stats_box,0,1)
        #grid_layout.addWidget(self.graph_canvas,0,1) 
        grid_layout.addWidget(tPlot,1,1)
                
        main_widget.setLayout(grid_layout)

    def openingFile(self):
        fname, _filter = QFileDialog.getOpenFileName(self, 'Open file', 'C:')
        self.load_data(fname)
        
    def simpLoad(self):
        #for this example, we'll hard code the file name.
        #fileName = "Historical Temperatures from Moose Wyoming.csv"
        self.load_data('Historical Temperatures from Moose Wyoming.csv')#fileName)
           
    def load_data(self, fileName):   
       try:
           self.data_table.setRowCount(0)
       except:
           pass
       header_row = 1 

       #load data file into memory as a list of lines
       #print('{}'.format(fileName))    
#==============================================================================
#         try:
#             with open(fileName,'r') as data_file:
#                  self.data_lines = data_file.readlines()
#              
#             print("Opened {}".format(fileName))
#             print(self.data_lines[1:10]) #for debugging only
#              
#             #Set the headers
#             #parse the lines by stripping the newline character off the end
#             #and then splitting them on commas.
#             data_table_columns = self.data_lines[header_row].strip().split(',')
#             self.data_table.setColumnCount(len(data_table_columns))
#             self.data_table.setHorizontalHeaderLabels(data_table_columns)
#              
#             #fill the table starting with the row after the header
#             current_row = -1
#             for row in range(header_row+1, len(self.data_lines)):
#                 row_values = (self.data_lines[row].strip().split(','))
#                 current_row +=1
#                 self.data_table.insertRow(current_row)
#                 #Populate the row with data
#                 for col in range(len(data_table_columns)):
#                     entry = QTableWidgetItem("{}".format(row_values[col]))
#                     self.data_table.setItem(current_row,col,entry)
#             print("Filled {} rows.".format(row))
#         except:
#             pass
#==============================================================================

        
    def monte(self, alpha, count, mean, var, stdDev,stdErr):
        #=$F$2+TINV(RAND(),$E$2)*(-1^CEILING(RAND()*2,1))*$I$2+TINV(RAND(),$E$2-1)*(-1^CEILING(RAND()*2,1))*SQRT(($E$2-1)*$G$2/CHIINV(RAND(),$E$2-1))
        array=[]
        for i in range(1, 10000):
            array.append(mean+stats.t.ppf(np.random.rand(), count)*stdErr+stats.t.ppf(np.random.rand(), count-1)*((count-1)*var/stats.chi2.isf(np.random.rand(), count-1))**0.5)
        array.sort()
        #print(array)
        downrange=int((alpha*10000))
        uprange=int((1-alpha)*10000)
            
        print(array[(downrange)])   #looks like returns array[0] and array[10000]]
        print(array[(uprange)])
        return [array[int(downrange)], array[int(uprange)]]
        
    def compute_stats(self):
        #setup array
        alpha=float(self.textbox.text())
        #print (alpha)
        if alpha>0 and alpha<1:
            item_list=[]
            items = self.data_table.selectedItems()
            #items=allItems[~np.isnan(allItems)] #mask for nan, pull true vals into new array
            for item in items:
                try:
                    item_list.append(float(item.text()))
                except:
                    pass
            
            if len(item_list) > 1: #Check to see if there are 2 or more samples
                data_array = np.asarray(item_list)
                data_array = np.asarray(item_list)
                mean_value = np.mean(data_array)
                length=len(item_list)
                stdDev=np.std(data_array)
                stdErr=stdDev/(length**0.5)
                #variance=np.var(data_array)
                #stutsingle=stats.t.ppf(1-alpha, length)
                stutdouble=stats.t.ppf(1-alpha/2, length)
                lowmean=mean_value-stutdouble*stdDev
                highmean=mean_value+stutdouble*stdDev
    
                
            if len(item_list)>2:
                varVal=statistics.variance(item_list)
                chisqleft=stats.chi2.ppf(alpha, length-1)#, mean_value, varVal)
                maxVar=(length-1)*(varVal)/chisqleft
                maxStdDev=maxVar**0.5
                lowbnd=stats.norm.ppf(alpha/2, mean_value, stdDev)
                highbnd=stats.norm.ppf(1-alpha/2, mean_value, stdDev)
                lowbndmc, highbndmc=self.monte(alpha, length, mean_value, varVal, stdDev,stdErr)
            else:
                varVal=0
                
                
            try:
                #first number ,n, in {n:pf} is index of call in format()
                self.count_label.setText("Count = {:0.6f}".format(length))     
                self.mean_label.setText("Mean = {:0.6f}".format(mean_value))
                self.stdDev_label.setText("StdDev = {:0.6f}".format(stdDev))
                self.stdErr_label.setText("StdErr = {:0.6f}".format(stdErr))
                self.var_label.setText("Variance = {:0.6f}".format(varVal))
                self.tval_label.setText("Student-t Value = {:0.6f}".format(stutdouble))
                self.lowmean_label.setText("Mean Lower Bound (t) = {:0.6f}".format(lowmean))
                self.highmean_label.setText("Mean Upper Bound (t) = {:0.6f}".format(highmean))
                self.lowbnd_label.setText("Mean Lower Bound (norm) = {:0.6f}".format(lowbnd))
                self.highbnd_label.setText("Mean Upper Bound (norm) = {:0.6f}".format(highbnd))
                self.lowbndmc_label.setText("Mean Lower Bound (monte) = {:0.6f}".format(lowbndmc))
                self.highbndmc_label.setText("Mean Upper Bound (monte) = {:0.6f}".format(highbndmc))            
                self.chisq_label.setText("Chi-Squared Value = {:0.6f}".format(chisqleft))
                self.maxvar_label.setText("Maximum Variance = {:0.6f}".format(maxVar))
                self.maxstd_label.setText("Maximum StdDev = {:0.6f}".format(maxStdDev))
#==============================================================================
#                 if length<100:
#                     bins=math.floor(length/2)
#                 else:
#                     bins=50
#                 self.graph_canvas.plot_histogram(data_array, bins) 
#==============================================================================
    
                    #add more distributions here
            except:
                pass


if __name__ == '__main__':
    #Start the program this way according to https://stackoverflow.com/questions/40094086/python-kernel-dies-for-second-run-of-pyqt5-gui
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    execute = StatCalculator()
    sys.exit(app.exec_())
