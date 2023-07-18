
from PyQt5.QtWidgets import QWidget, QPushButton, QDialog, QApplication
import serial, sys, re, csv, copy, os, time
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
# from pyqtgraph import GraphicsScene


class Fitments():
    '''the brush\pen\color\path\font saved here'''
   
    #modify the line and symbols for plotting
    curve_pen = pg.mkPen('r', width=1)     #define the line
    symbol_pen = pg.mkPen(color = (255, 0 ,0))   #define the symbol)

    #get path of resource
    upper_path = os.path.dirname(os.path.abspath(__file__))
    resource_path = upper_path + '\\' + 'resource\\' 

    def __init__(self) -> None:
        self.his_colors = []
        self.his_color_index = 0
        '''modify alterable colors for the new plots' line'''


    def alternate_colors(self):
        '''return alternate Qcolor object'''
        self.colors = QColor.colorNames()    #list with color's name
        self.c_color = sample(self.colors, 1)[0]     #random str from the list
        #make sure the last color is different with the new one
        self.his_color = copy.deepcopy(self.c_color)  
        self.his_colors.append(self.his_color)
    
        while self.c_color in self.his_colors:
            self.c_color = sample(self.colors, 1)[0]
            self.his_color_index += 1
        return self.c_color, self.his_color


class WinClibration(QWidget):
    ''' 
    the GUI for calibration
    '''
    def __init__(self) -> None:
        super(WinClibration, self).__init__()
        self.ui = Ui_Clibration() #instantiate the UI class
        self.ui.setupUi(self)
        self.resize(300, 248)
        

class MainWindowMge(QWidget):
    '''Main GUI Window'''

    def __init__(self) -> None:
        super(MainWindowMge, self).__init__()
        #initiate the UI
        self.st = Fitments()    #instance the style class "Ftiments"
        self.ui = Ui_MainWindow()   
        self.ui.setupUi(self)
        self.resize(1220, 628)
        self.ui.pushButton.clicked.connect(self.click_start)    #defination for button "Stop"
        self.ui.pushButton_10.clicked.connect(self.click_stop)    #defination for button "Stop"
        self.ui.pushButton_7.clicked.connect(self.port_connect)  #connect button7 to 连接
        self.ui.pushButton_7.setIcon(QIcon(Fitments.resource_path + 'GRAY BALL.ico'))    #set the default icon for “连接”
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
        my_logo = QPixmap(Fitments.resource_path + 'log1.png')
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

        #plot setting
        self.y_value = [0]  # y data

        self.graphs = self.ui.graphicsView  #instance the graphicslayoutwidget
        self.graphs.setBackground('w')  #set white background
        #modify the style of axis
        _text_style = pg.mkPen({'color':'black'})
        self.l_style = pg.AxisItem('left')  #initiate the AxisItem
        # ref https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/axisitem.html
        self.l_style.setStyle(tickFont=QFont('Arial', 8))  
        self.l_style.setTextPen(_text_style)

        self.b_style = pg.AxisItem('bottom')
        self.b_style.setStyle(tickFont=QFont('Arial', 8))
        self.b_style.setTextPen(_text_style)

        self.main_plotItem = self.graphs.addPlot()  # adding PlotItem to graphics
        self.main_plotItem.setAutoPan(y=True)
        self.main_plotItem.setAxisItems({'left':self.l_style, 'bottom':self.b_style}) #set the aixs' style
        self.main_plotItem.setMenuEnabled(False)    #disable the right clicking
        self.timeCurve = self.main_plotItem.plot(self.y_value, pen = Fitments.curve_pen, symbolPen=Fitments.symbol_pen,\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))   #instance the PlotDataItem

        # to upload the plot by timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(0)   #50 means 50 millsecond
        self.timer.timeout.connect(lambda: self.timeCurve.setData(self.y_value))
        self.timer.start()

        self.his_color_index = -1    #+1 everytime when you click button "新增"
        self.his_colors = []    #append 1 color everytime when you click button "新增"

        #the current row for adding plotting
        self.c_row = 0


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
            self.ui.pushButton.setIcon(QIcon(Fitments.resource_path+'stop.ico'))   #set stop icon for button
            self.ui.pushButton_7.setEnabled(False)  #set "连接/断开" unclickabel

            if not self.graphs.getItem(0,0):    #if all plot deleted
                self.main_plotItem = self.graphs.addPlot()  # adding PlotItem to graphics
                self.main_plotItem.setAxisItems({'left':self.l_style, 'bottom':self.b_style}) #set the aixs' style

                self.timeCurve = self.main_plotItem.plot(self.y_value, pen = Fitments.curve_pen, symbolPen=Fitments.symbol_pen,\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))   #instance the PlotDataItem
                # self.timeCurve.setMenuEnabled()
        else:
            self.T1.terminate()
            self.ui.pushButton.setText('开始')
            self.ui.pushButton.setIcon(QIcon(Fitments.resource_path + 'Play.ico'))
            self.ui.pushButton_7.setEnabled(True)   #enable the button "连接"
            self.ui.pushButton_10.setEnabled(True)  #enable the button "新增"

    def click_stop(self):
        '''When click the 结束 button, end thread1'''
        self.T1.terminate()
        self.ui.pushButton_10.setEnabled(True)
        self.ui.pushButton.setEnabled(True)
        

    def click_setup(self):
        '''when click the 复位 button, clear data'''  
        self.T1.terminate() #stop to updata the serial data 
        self.timer.stop()   #stop the timer   
        self.y_value.clear()
        self.plot_data_index = 0 
        self.c_row = 0
        self.data_pool.clear()
        self.graphs.clear()  #from the graphiclayoutWidget remove all items
        #reset the main plot Item to the graphicLayoutWidge
        time.sleep(0.1)
        self.main_plotItem = self.graphs.addPlot()  # adding PlotItem to graphics
        self.main_plotItem.setMenuEnabled(False)    #disable the right clicking
        self.timeCurve = self.main_plotItem.plot(self.y_value, pen = Fitments.curve_pen, symbolPen=Fitments.symbol_pen,\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))   #instance the PlotDataItem
        time.sleep(0.5)
        _text_style = pg.mkPen({'color':'black'})
        self.l_style = pg.AxisItem('left')  #initiate the AxisItem
        # ref https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/axisitem.html
        self.l_style.setStyle(tickFont=QFont('Arial', 10))  
        self.l_style.setTextPen(_text_style)

        self.b_style = pg.AxisItem('bottom')
        self.b_style.setStyle(tickFont=QFont('Arial', 10))
        self.b_style.setTextPen(_text_style)
        self.main_plotItem.setAxisItems({'left':self.l_style, 'bottom':self.b_style}) #set the aixs' style
        self.T1.start() #start the updata from serial
        self.timer.start()  #start to updata the main plot


        #if the "连接" 状态，点击复位后不能再断开，因为进程报错
        self.ui.pushButton_7.setEnabled(False)
        #set the button "开始/停止" 
        self.ui.pushButton.setChecked(True)
        self.ui.pushButton.setText('停止')
        self.ui.pushButton.setIcon(QIcon(Fitments.resource_path+'stop.ico'))   #set stop icon for button
        #set the button "新增"
        self.ui.pushButton_10.setEnabled(False)

        
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
        self.main_plotItem.plot(result, pen = pg.mkPen('lightseagreen', width=2), symbolPen=pg.mkPen(color = 'lightseagreen'),\
        symbol='h', symbolSize=1, sybolBrush=('0, 0, 0'))
        self.main_plotItem.setMenuEnabled(False)    #disable the right clicking


    def curve_compare(self):
        '''plot a new curve of dynamic data, keep the original curve of history static data'''

        ori_data = copy.deepcopy(self.y_value)
        self.y_value = []   #clear the history data
        
        '''get alternate color from Fitments'''
        c_color = self.st.alternate_colors()[0]
        his_color = self.st.alternate_colors()[1]

        self.c_row += 1
        ori_plot = self.graphs.addPlot(col = 0, row=self.c_row) # adding PlotItem to graphics
        

        #link the Yaxi together with the mainplotItem, ref:https://pyqtgraph.readthedocs.io/en/latest/api_reference/graphicsItems/viewbox.html
        ori_view_box = ori_plot.getViewBox()    #get the ViewBox object
        main_view_box = self.main_plotItem.getViewBox()    #get the ViewBox object
        ori_view_box.linkView(main_view_box.YAxis, main_view_box)  
        #set the style of aix for ori plot
        ls = pg.AxisItem('left', textPen=pg.mkPen({'color':'black'}))
        ls.setStyle(tickFont=QFont('Arial', 8))
        bs = pg.AxisItem('bottom', textPen=pg.mkPen({'color':'black'}))
        bs.setStyle(tickFont=QFont('Arial', 8))
        ori_plot.setAxisItems({'left':ls, 'bottom':bs})
        ori_plot.setMenuEnabled(False)    #disable the right clicking


        oriCurve = ori_plot.plot(ori_data, pen = pg.mkPen({'color':his_color, 'width':3}), symbolPen=Fitments.symbol_pen,\
        symbol='h', symbolSize=2, sybolBrush=('0, 0, 0'))   #plotting the data to plotItem with alternate color

        self.timeCurve.setPen({'color':c_color, 'width':4}) #reset the color of dynamic plotting


        self.T1.start() #updata data from serial 


     
        # self.timer.timeout.connect(lambda: new_plot.setData(self.y_value)) #updata curve of new plotting

        '''button logic cotrol'''
        self.ui.pushButton_10.setEnabled(False) #disable the button "新增"
        self.ui.pushButton.setChecked(True)  #set the button "开始" to "停止"
        self.ui.pushButton.setText("停止")
        self.ui.pushButton.setIcon(QIcon(Fitments.resource_path + 'stop.ico'))   #set stop icon for button

    def port_connect(self):
        # connecte the parameters connect to the GUI
        self.portx = self.ui.comboBox_2.currentText()
        self.bandx = int(re.search(r'\d+', self.ui.comboBox.currentText()).group())
        if self.ui.pushButton_7.isChecked():  #button un clicked  '

            try:
                self.comSerial = serial.Serial(port=self.portx, baudrate=self.bandx,\
                                            timeout=1, bytesize=8)
                self.ui.pushButton_7.setIcon(QIcon(Fitments.resource_path + 'Aqua Ball Green.ico'))    #set the green icon for “连接”
                self.ui.pushButton_7.setText('断开')
                self.ui.pushButton.setEnabled(True)
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print (message)
                print('## Connection failed, Plese check the wire and parameters')

        else:    #button clicked, port opnning
            self.comSerial.close()
            self.ui.pushButton_7.setIcon(QIcon(Fitments.resource_path + 'GRAY BALL.ico'))    #set the green icon for “连接”
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

    '''to solve the axis unexpected offset problem
    solution1:    
    # ref: https://pyqtgraph.readthedocs.io/en/latest/getting_started/how_to_use.html?highlight=mkqapp#hidpi-displays
    '''
    QApplication.setHighDpiScaleFactorRoundingPolicy(QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    #solution2:(don't work for me)
    #https://cloud.tencent.com/developer/ask/sof/107827481?from=16139


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