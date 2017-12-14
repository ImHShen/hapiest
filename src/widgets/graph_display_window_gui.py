from PyQt5 import QtGui, QtWidgets, uic, QtCore, Qt
from utils.hapiest_util import *
from PyQt5.QtChart import *
from utils.log import *


class GraphDisplayWindowGui(QtWidgets.QWidget):
    def __init__(self):
        super(GraphDisplayWindowGui, self).__init__()
        uic.loadUi('layouts/graph_display_window.ui', self)
        self.chart = None
        self.chart_view = None

        self.reset.clicked.connect(self.__on_zoom_reset_click)
        self.set_viewport.clicked.connect(self.__on_set_viewport_pressed)

        self.xmax.valueChanged.connect(lambda v: self.__on_xmax_changed(v))
        self.xmin.valueChanged.connect(lambda v: self.__on_xmin_changed(v))
        self.ymax.valueChanged.connect(lambda v: self.__on_ymax_changed(v))
        self.ymin.valueChanged.connect(lambda v: self.__on_ymin_changed(v))

        self.grabGesture(QtCore.Qt.PanGesture)
        self.grabGesture(QtCore.Qt.PinchGesture)
        self.installEventFilter(self)

        self.axisy = None
        self.axisx = None
        self.view_xmin = None
        self.view_xmax = None
        self.view_ymin = None
        self.view_ymax = None
        self.chart = None

        self.show()

    def eventFilter(self, source, event):
        self.sceneEvent(event)
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def set_chart_title(self):
        pass

    def add_graph(self, x, y, title="", xtitle="", ytitle=""):
        series = QLineSeries()
        for i in range(0, x.size):
            series.append(x[i], y[i])
        self.series = series
        series.setUseOpenGL(True)

        self.chart = QChart()
        self.chart.addSeries(series)
        self.chart.setTitle(title)
        self.setWindowTitle(title)

        if self.axisy:
            self.chart.removeAxis(self.axisy)
            self.chart.removeAxis(self.axisx)

        self.axisx = QValueAxis()
        self.axisx.setTickCount(5)
        self.axisx.setTitleText(xtitle)
        self.chart.addAxis(self.axisx, QtCore.Qt.AlignBottom)
        self.series.attachAxis(self.axisx)

        self.axisy = QValueAxis()
        self.axisy.setTitleText(ytitle)
        self.axisy.setTickCount(5)
        self.chart.addAxis(self.axisy, QtCore.Qt.AlignLeft)
        self.series.attachAxis(self.axisy)

        if self.view_xmin:
            if self.view_xmin > self.axisx.min():
                self.view_xmin = self.axisx.min()
        else:
            self.view_xmin = self.axisx.min()
        if self.view_ymin:
            if self.view_ymin > self.axisy.min():
                self.view_ymin = self.axisy.min()
        else:
            self.view_ymin = self.axisy.min()

        if self.view_xmax:
            if self.view_xmax < self.axisx.max():
                self.view_xmax = self.axixs.max()
        else:
            self.view_xmax = self.axisx.max()
        if self.view_ymax:
            if self.view_ymax < self.axisy.max():
                self.view_ymax = self.axisy.max()
        else:
            self.view_ymax = self.axisy.max()

        self.chart.legend().hide()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRubberBand(QChartView.RectangleRubberBand)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.chart_view)
        self.loading_label.setDisabled(True)
        self.graph_container.setLayout(layout)

    def __on_zoom_reset_click(self):
        """
        *Sets the screen focus to maximum values of y and x.*
        """
        if self.chart:
            self.axisx.setRange(self.view_xmin, self.view_xmax)
            self.axisy.setRange(self.view_ymin, self.view_ymax)

    def __on_xmax_changed(self, value):
        """
        *Params: self, value. Checks to make sure that the values are proper. If the value passed in is
        smaller than the already established x min value, then the x min value is set to be the value -1 and the x max is set to be value passed into the method
        """
        return
        min = self.xmin.value()
        if value < min:
            self.xmax.setValue(value)
            self.xmin.setValue(value - 1)

    def __on_xmin_changed(self, value):
        """
        *If the value of the number passed in is larger than the currently established max value for x, then the min value is set to be the value passed in , and the max is set to be the value passed into the method + 1.*
        """
        return
        max = self.xmax.value()
        if value > max:
            self.xmin.setValue(value)
            self.xmax.setValue(value + 1)

    def __on_ymax_changed(self, value):
        """
        *Sets the value for y max, if the value passed in is smaller than the current y min, then the y max is set to y min, and y min is set to the value passed into the method .*
        """
        return
        min = self.ymin.value()
        if value < min:
            self.ymax.setValue(min)
            self.ymin.setValue(value)

    def __on_ymin_changed(self, value):
        """
        *Sets the value for y min, if the value passed in is larger than current y max, then the value of y min is set to be the value of y max, and the y max value is set as the value passed into the method.*
        """
        return
        max = self.ymax.value()
        if value > max:
            self.ymin.setValue(max)
            self.ymax.setValue(value)

    def __on_set_viewport_pressed(self):
        """
        *Handles the changing in a viewport for graphing view .*
        """
        if self.chart == None:
            return

        xmin = self.xmin.value()
        xmax = self.xmax.value()
        ymin = self.ymin.value()
        ymax = self.ymax.value()

        if xmin == xmax or ymin == ymax:
            return
        if xmin > xmax:
            t = xmin
            xmin = xmax
            xmax = t
            self.xmin.setValue(xmin)
            self.xmax.setValue(xmax)
        if ymin > ymax:
            t = ymin
            ymin = ymax
            ymax = t
            self.ymin.setValue(ymin)
            self.xmin.setValue(ymax)

        self.axisx.setRange(xmin, xmax)
        self.axisy.setRange(ymin, ymax)

    def sceneEvent(self, event):
        """
        *Event handler for graph.*
        """
        if event.type() == QtCore.QEvent.Gesture:
            self.gestureEvent(event)

    def gestureEvent(self, event):
        """
        *Event handler for graph, for additonal information see documentation on PyQt QGestureEvent.*
        """
        return  # Ignore touch events...
        gesture = event.gesture(QtCore.Qt.PanGesture)
        if gesture:
            delta = gesture.delta()
            self.chart.scroll(-delta.x(), delta.y())
            return True

        gesture = event.gesture(QtCore.Qt.PinchGesture)
        if gesture:
            if gesture.changeFlags().__iand__(QtWidgets.QPinchGesture):
                self.chart.zoom(gesture.scaleFactor())
            return True
        return False