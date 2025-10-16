from orangewidget import gui

from orangewidget.widget import Input, Output
from oasys2.widget.widget import OWWidget
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangecontrib.srw.util.srw_objects import SRWData

class OWToWofryWavefront2d(OWWidget):
    name = "To Wofry Wavefront 2D"
    id = "toWofryWavefront2D"
    description = "To Wofry Wavefront 2D"
    icon = "icons/to_wofry_wavefront_2d.png"
    priority = 21
    category = ""
    keywords = ["wise", "gaussian"]

    class Inputs:
        srw_data = Input("SRWData", SRWData, default=True, auto_summary=False)

    class Outputs:
        wavefront = Output("GenericWavefront2D", object, default=True, auto_summary=False)

    CONTROL_AREA_WIDTH = 605

    srw_data = None

    want_main_area = 0

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setFixedHeight(self.geometry().height())
        self.setFixedWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        label = gui.label(self.controlArea, self, "From SRW Wavefront To Wofry Wavefront")
        label.setStyleSheet("color: darkblue; font-weight: bold; font-style: italic; font-size: 14px")

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_wavefront, height=45)

    @Inputs.srw_data
    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.srw_data = input_data

            self.convert_wavefront()

    def convert_wavefront(self):
        try:
            if not self.srw_data is None:
                self.Outputs.wavefront.send(self.srw_data.get_srw_wavefront().toGenericWavefront())
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

add_widget_parameters_to_module(__name__)