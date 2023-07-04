
import re
from PyQt5.QtWidgets import QWidget
import serial, sys, time
import serial.tools.list_ports
import pyqtgraph as pg
# import pyqtgraph.opengl as gl
from pyqtgraph import PlotWidget
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets
from QLed import QLed
from MainWindow import Ui_MainWindow 
from CalibrationWindow import Ui_Clibration
'''debug: receive_his normal, data_poll error'''

class WinClibration(QWidget):
    ''' 
    the GUI for calibration
    '''
    def __init__(self) -> None:
        super(WinClibration, self).__init__()
        self.ui = Ui_Clibration() #instantiate the UI class
        self.ui.setupUi(self)
        self.resize(612, 407)
        

class MainWindowMge(QWidget):
    '''Main GUI Window'''
    def __init__(self) -> None:
        super(MainWindowMge, self).__init__()
        self.ui = Ui_MainWindow()   #initiate the UI
        self.ui.setupUi(self)
        self.resize(1680, 968)
        self.ui.pushButton.clicked.connect(self.click_start)    #defination for button "Stop"
        self.ui.pushButton_10.clicked.connect(self.click_stop)    #defination for button "Stop"
        self.ui.pushButton_7.clicked.connect(self.port_connect)  #connect button7 to 连接
        #port and bandx connection
        self.ui.comboBox.currentIndexChanged.connect(self.port_chosse)
        self.ui.comboBox_2.currentIndexChanged.connect(self.bandx_choose)

        self.ui.comboBox_2.setCurrentIndex(5)  #modify the default opion
        self.ui.comboBox.setCurrentIndex(6)

        '''initialize some parameters for serial'''

        
        self.timeout = 1    #for serial
        self.comSerial = None   #for serial
        self.data_pool = []     #the list recived from serial
        self.receive_data = ''
        self.receive_his = '' 
        self.data_count = len(self.data_pool)
        self.plot_data_index = 0 #for data_y update
        self.find_serial()


#modified part of the original code↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
        self.y = [0]  # y data
        self.ui.graphicsView.setBackground('w')
        self.pen = pg.mkPen(color = (255,255,255))     #define the line
        self.symbol_pen = pg.mkPen(color = (255, 0 ,0))   #define the symbol)
        self.view_set = pg.ViewBox(border=self.symbol_pen)
        self.timeCurve = self.ui.graphicsView.plot(self.y, pen = self.pen, symbolPen=self.symbol_pen,\
        symbol='h', symbolSize=3, sybolBrush=('0, 0, 0'))
        

        # to upload the plot by timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1)   #50 means 50 millsecond
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()
    
    def update_plot_data(self):
        global CURENT_DATA
        '''define the source data to update the graph'''
        self.timeCurve.setData(self.y)


    def bandx_choose(self):
        '''connecte the band to the choosen option of com_box1'''
        return self.comboBox_2.currentText()
    
    def port_chosse(self):
        '''connecte the port to the choosen option of com_box2'''
        return self.comboBox.currentText()
    
    def click_start(self):
        '''when click the 开始 button, start thread1 whick recieve data 
        and deal with the data structure'''
        
        self.T1 = Thread1()
        self.T1.start()
        MainWindowMge.ui.pushButton.setEnabled(False)

    def click_stop(self):
        '''When click the 结束 button, end thread1'''
        self.T1.terminate()
        self.pushButton_10.setEnabled(True)
        self.pushButton.setEnabled(True)
    
    def click_setup(self):
        '''when click the 复位 button, clear data'''
        self.y.clear()
        self.plot_data_index = 0 
        self.data_pool.clear()
        self.timeCurve.setData(0)


    #modify some parameters for serial

    def port_connect(self):
        # connecte the parameters connect to the GUI
        self.portx = self.ui.comboBox_2.currentText()
        self.bandx = int(re.search(r'\d+', self.ui.comboBox.currentText()).group())
        try:
            self.comSerial = serial.Serial(port=self.portx, baudrate=self.bandx,\
                                        timeout=self.timeout, bytesize=8)
            self.ui.led.value = True
            self.ui.pushButton_7.setEnabled(False)
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print (message)
            print('## Connection failed, Plese check the wire and parameters')

    def find_serial(self):
        '''Check the ports, if found, print out'''
        port_list = list(serial.tools.list_ports.comports()) 
        if len(port_list) == 0:
            print('>> No port found')
        else:
            for i in range(0, len(port_list)):
                print(port_list[i]) 


class Thread1(QThread):
    '''recieve data from serial port'''

    def __init__(self) -> None:
        super().__init__()

    def run(self): 
        print("receiveData")
        while True:
            MyMainWindow.receive_data = MyMainWindow.comSerial.read_all().decode("utf-8")
            time.sleep(0.01) #to advoid the split error: '4520' -> '452','0'
            MyMainWindow.receive_his += MyMainWindow.receive_data #for debug
            if MyMainWindow.receive_data and MyMainWindow.receive_data != ',':    #if data is ',' skip for this loop
                data_split = MyMainWindow.receive_data.split(',')  #transfer ['0000','58'] to ['0000','58']
                if '' in data_split:  #advoid valueERROR when '' is not in the list
                    data_split.remove('')  #remove the miltiple '' created from split the lastest 'aaaa,' 
                if '' in data_split:  #for debug
                    print()
                data_trim = [int(x) for x in data_split]
                MyMainWindow.data_pool.extend(data_trim)
                MyMainWindow.data_count = len(MyMainWindow.data_pool)
            if MyMainWindow.plot_data_index < MyMainWindow.data_count:
                MyMainWindow.y.append(MyMainWindow.data_pool[MyMainWindow.plot_data_index])   #data from serial port
                MyMainWindow.plot_data_index += 1   #every loop putin the next data into data_y

            #for debug        
            if len(MyMainWindow.y) > 3:
                current_data_y = MyMainWindow.y[-1]
                last_data_y = MyMainWindow.y[-2]
                if last_data_y > current_data_y:
                    print()

class Thread2(QThread):
    '''send data to serial port'''

    def __init__(self) -> None:
        super().__init__()
    def run(self):
        '''to calibration, send data'''
        while True:
            send_data = input()
            if send_data:
                self.comSerial.write(send_data.encode('UTF-8'))
                print('发送数据：%s' % send_data)

#modified part of the original code↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑







if __name__ == "__main__":

    #main window
    App = QtWidgets.QApplication(sys.argv)
    MyMainWindow = MainWindowMge()
    MyMainWindow.show()
    
    #clibration window
    MyClibraionWindow = WinClibration()

    MyMainWindow.ui.pushButton_3.clicked.connect(MyClibraionWindow.show)
    App.exec_()