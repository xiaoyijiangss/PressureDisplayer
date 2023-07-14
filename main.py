from PyQt5.QtWidgets import QWidget, QPushButton
import serial, sys, re, csv, copy
from random import sample
from tkinter import filedialog
import serial.tools.list_ports
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
from PyQt5.QtCore import QThread
from PyQt5 import QtCore, QtWidgets
# from qt_material import apply_stylesheet
from MainWindow import Ui_MainWindow
from CalibrationWindow import Ui_Clibration


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
        #initiate the UI
        self.ui = Ui_MainWindow()   
        self.ui.setupUi(self)
        self.resize(1680, 968)
        self.ui.pushButton.clicked.connect(self.click_start)    #defination for button "Stop"
        self.ui.pushButton_10.clicked.connect(self.click_stop)    #defination for button "Stop"
        self.ui.pushButton_7.clicked.connect(self.port_connect)  #connect button7 to 连接
        self.ui.pushButton_7.setIcon(QIcon('GRAY BALL.ico'))    #set the default icon for “连接”
        self.ui.pushButton_7.setCheckable(True)     #turn to switch button "连接"

        self.ui.pushButton.setCheckable(True)   #turn to switch button "开始"
        self.ui.pushButton.setIconSize(QtCore.QSize(24, 24))    #set the size of "开始" ico
        self.ui.pushButton.clicked.connect(self.click_start)
        self.ui.pushButton_11.clicked.connect(self.import_csv)  #connect to button11 "导入"
        self.ui.pushButton_9.clicked.connect(self.click_export) #connect the button9 “导出”

        # self.ui.pushButton_10.setCheckable(True)    #turn to switch button "新增"
        self.ui.pushButton_10.setDisabled(True) #"新增" button set as disable, enabled by button "停止"
        self.ui.pushButton_10.clicked.connect(self.curve_compare)   #connect the button10 "新增"


        #modify the logo
        my_logo = QPixmap('log1.png')
        self.ui.label_3.setPixmap(my_logo)


        #port and bandx connection
        self.ui.comboBox.currentIndexChanged.connect(self.port_chosse)  #translate the port selected in GUI to Serial
        self.ui.comboBox_2.currentIndexChanged.connect(self.bandx_choose)   #translate the bandx selected in GUI to Serial
        self.ui.comboBox_2.setCurrentIndex(6)  #modify the default opion
        self.ui.comboBox.setCurrentIndex(6)
        self.ui.pushButton_2.clicked.connect(self.click_setup)  #connect button2 复位

        self.comSerial = None   #for serial
        self.data_pool = []     #the list recived from serial
        self.receive_data = ''

        self.data_count = len(self.data_pool)
        self.plot_data_index = 0 #for data_y update
        MainWindowMge.find_serial() #for developers, print serial status
        self.T1 = Thread1() #Qthread, recieve the data from serial


        #modify the style of axis
        _text_style = pg.mkPen({'color':'black'})
        _l_style = pg.AxisItem('left')  #initiate the AxisItem
        _l_style.setStyle(tickFont=QFont('Arial', 10))  # ref https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/axisitem.html
        _l_style.setTextPen(_text_style)

        _b_style = pg.AxisItem('bottom')
        _b_style.setStyle(tickFont=QFont('Arial', 10))
        _b_style.setTextPen(_text_style)
        # self.ui.graphicsView is PlotWidget, ref https://pyqtgraph.readthedocs.io/en/latest/api_reference/widgets/plotwidget.html
        self.main_plotItem = self.ui.graphicsView.getPlotItem()  # get the PlotItem
        self.main_plotItem.setAxisItems({'left':_l_style, 'bottom':_b_style})

        #plot setting
        self.y_value = [0]  # y data
        self.ui.graphicsView.setBackground('w')

        _pen = pg.mkPen('r', width=1)     #define the line
        _symbol_pen = pg.mkPen(color = (255, 0 ,0))   #define the symbol)
        self.timeCurve = self.ui.graphicsView.plot(self.y_value, pen = _pen, symbolPen=_symbol_pen,\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))


        # to upload the plot by timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)   #50 means 50 millsecond
        self.timer.timeout.connect(lambda: self.timeCurve.setData(self.y_value))
        self.timer.start()

        self.his_color_index = -1    #+1 everytime when you click button "新增"
        self.his_colors = []    #append 1 color everytime when you click button "新增"

    def bandx_choose(self):
        '''connecte the band to the choosen option of com_box1'''
        return self.ui.comboBox_2.currentText()
    
    def port_chosse(self):
        '''connecte the port to the choosen option of com_box2'''
        return self.ui.comboBox.currentText()
    
    def click_start(self):
        '''when click the 开始 button, start thread1 whick recieve data 
        and deal with the data structure'''
        if self.ui.pushButton.isChecked():
            self.T1.start()
            self.ui.pushButton.setText('停止')
            self.ui.pushButton.setIcon(QIcon('stop.ico'))   #set stop icon for button
            self.ui.pushButton_7.setEnabled(False)  #set "连接/断开" unclickabel
            cur_dataItems = self.main_plotItem.listDataItems()  #list all the curve of the plotItem
            if cur_dataItems == []: #if reseted, all the dataItem will be removed
                self.main_plotItem.addItem(self.timeCurve)
        else:
            self.T1.terminate()
            self.ui.pushButton.setText('开始')
            self.ui.pushButton.setIcon(QIcon('Play.ico'))
            self.ui.pushButton_7.setEnabled(True)   #enable the button "连接"
            self.ui.pushButton_10.setEnabled(True)  #enable the button "新增"

    def click_stop(self):
        '''When click the 结束 button, end thread1'''
        self.T1.terminate()
        self.ui.pushButton_10.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
    
    def click_setup(self):
        '''when click the 复位 button, clear data'''       
        self.y_value.clear()
        self.plot_data_index = 0 
        self.data_pool.clear()
        self.main_plotItem.clear()  #from the main PlotItem remove all items

    def click_export(self):
        '''export function, with a dialog to choose formation as .csv or .png to export'''
        export_dia = QtWidgets.QDialog(MyMainWindow)
        export_dia.setGeometry(120, 120, 250, 220)
        
        dia_btn1 = QPushButton(export_dia)
        dia_btn1.setText('导出表格')
        dia_btn1.move(30, 100)
        dia_btn1.clicked.connect(lambda: export_dia.accept())

        dia_btn2 = QPushButton(export_dia)
        dia_btn2.setText('导出图片')
        dia_btn2.move(150, 100)
        dia_btn2.clicked.connect(lambda: export_dia.reject())

        export_dia.accepted.connect(self.export_csv)    #export the csv file
        exporter = pg.exporters.ImageExporter(self.ui.graphicsView.scene())
        export_dia.rejected.connect(lambda: exporter.export('monitor.png')) #export the png file

        export_dia.setWindowTitle("导出选项")
        export_dia.setSizeGripEnabled(False)
        export_dia.exec()

    def export_csv(self): 
        '''export a csv file with data recieved from the serial port'''
        with open('monitor.csv', 'w', newline='') as f:
            ex_data = [[i] for i in self.data_pool]
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(ex_data)

    def import_csv(self):
        '''choose the csv file and plot data of it'''
        self.T1.terminate() # stop the serial data translation
        self.click_setup()
        self.timer.stop()
        file_name = filedialog.askopenfilename(initialdir='D://software_development_workplace//',\
                                     filetypes=[('CSV', '*.csv')])
        with open(file_name, 'r') as f:
            reader = csv.reader(f)
            result_str = list(reader)
            result = [float(i) for [i] in result_str]
        self.ui.graphicsView.plot(result, pen = pg.mkPen('y', width=3), symbolPen=pg.mkPen(color = (255, 0 ,0)),\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))

    def curve_compare(self):
        '''plot a new curve of dynamic data, keep the original curve of history static data'''


        ori_data = copy.deepcopy(self.y_value)

        '''modify alterable colors for the new plots' line'''
        
        colors = QColor.colorNames()    #list with color's name
        c_color = sample(colors, 1)[0]     #random str from the list
        his_color = copy.deepcopy(c_color)  #make sure the last color is different with the new one
        self.his_colors.append(his_color)
        
        while c_color in self.his_colors:
            c_color = sample(colors, 1)[0]

        self.his_color_index += 1
        self.ori_dataItem = pg.PlotDataItem(ori_data, pen=pg.mkPen({'color': self.his_colors[self.his_color_index]}, width=3))   #instance a plotDataItem with original data
        self.main_plotItem.addItem(self.ori_dataItem)   #add the original curve to widget
        self.T1.start() #updata data from serial 

        self.y_value = []   #clear the history data 
        self.new_dataItem = pg.PlotDataItem(self.y_value, pen = pg.mkPen({'color': c_color[0], 'width': 5}))
        self.main_plotItem.addItem(self.new_dataItem)
        self.timer.timeout.connect(lambda: self.new_dataItem.setData(self.y_value)) #updata curve of new plotting

        '''button logic cotrol'''
        self.ui.pushButton_10.setEnabled(False) #disable the button "新增"
        self.ui.pushButton.setChecked(True)  #set the button "开始" to "停止"
        self.ui.pushButton.setText("停止")
        self.ui.pushButton.setIcon(QIcon('stop.ico'))   #set stop icon for button


    def port_connect(self):
        # connecte the parameters connect to the GUI
        self.portx = self.ui.comboBox_2.currentText()
        self.bandx = int(re.search(r'\d+', self.ui.comboBox.currentText()).group())
        if self.ui.pushButton_7.isChecked():  #button un clicked  '

            try:
                self.comSerial = serial.Serial(port=self.portx, baudrate=self.bandx,\
                                            timeout=1, bytesize=8)
                # self._led.value = True
                # icon1 = QIcon()
                # icon1.addPixmap(QPixmap('Aqua Ball Green.ico'), mode=QIcon.Disabled)    #have to set the mode, or the icon will trun to gray automticly cause we set the button to disabled
                # self.ui.pushButton_7.setIcon(icon1)    #set the green icon for "连接"
                # self.ui.pushButton_7.setEnabled(False)
                self.ui.pushButton_7.setIcon(QIcon('Aqua Ball Green.ico'))    #set the green icon for “连接”
                self.ui.pushButton_7.setText('断开')
                self.ui.pushButton.setEnabled(True)
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print (message)
                print('## Connection failed, Plese check the wire and parameters')


        else:    #button clicked, port opnning
            self.comSerial.close()
            self.ui.pushButton_7.setIcon(QIcon('GRAY BALL.ico'))    #set the green icon for “连接”
            self.ui.pushButton_7.setText('连接')
            self.ui.pushButton.setEnabled(False)

    @staticmethod
    def find_serial():
        '''Check the ports, if found, print out'''
        port_list = list(serial.tools.list_ports.comports()) 
        if len(port_list) == 0:
            print('>> No port found')
        else:
            for i in range(0, len(port_list)):
                print(port_list[i]) 


class Thread1(QThread):
    '''recieve data from serial port, updata to self.y_value'''

    def __init__(self) -> None:
        super().__init__()

    def run(self): 
        print(">> receiveData")
        while True:
            MyMainWindow.receive_data = MyMainWindow.comSerial.readline().decode("utf-8")
            # MyMainWindow.receive_data = MyMainWindow.comSerial.read_all().decode("utf-8")
            # time.sleep(0.01) #to advoid the split error: '4520' -> '452','0'
            # MyMainWindow.receive_his += MyMainWindow.receive_data #for debug
            if MyMainWindow.receive_data and MyMainWindow.receive_data != ',':    #if data is ',' skip for this loop
                data_split = MyMainWindow.receive_data.split(',')  #transfer ['0000','58'] to ['0000','58']
                if '' in data_split:  #advoid valueERROR when '' is not in the list
                    data_split.remove('')  #remove the miltiple '' created from split the lastest 'aaaa,' 

                data_trim = [float(x) for x in data_split]
                MyMainWindow.data_pool.extend(data_trim)
                MyMainWindow.data_count = len(MyMainWindow.data_pool)
            if MyMainWindow.plot_data_index < MyMainWindow.data_count and MyMainWindow.data_pool != []:
                MyMainWindow.y_value.append(MyMainWindow.data_pool[MyMainWindow.plot_data_index])   #data from serial port
                MyMainWindow.plot_data_index += 1   #every loop putin the next data into data_y

            #for debug        
            # if len(MyMainWindow.y_value) > 3:
            #     current_data_y = MyMainWindow.y_value[-1]
            #     last_data_y = MyMainWindow.y_value[-2]
            #     if last_data_y > current_data_y:
            #         print()

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
    App.setAttribute(QtCore.Qt.AA_Use96Dpi) #to solve the problem that plot's aixes displayed uncorrectly if move the Mainwindow to sencond monitor.
    # apply_stylesheet(App, theme='dark_cyan.xml')
    MyMainWindow = MainWindowMge()
    MyMainWindow.show()
    
    #clibration window
    MyClibraionWindow = WinClibration()

    MyMainWindow.ui.pushButton_3.clicked.connect(MyClibraionWindow.show)
    App.exec_()