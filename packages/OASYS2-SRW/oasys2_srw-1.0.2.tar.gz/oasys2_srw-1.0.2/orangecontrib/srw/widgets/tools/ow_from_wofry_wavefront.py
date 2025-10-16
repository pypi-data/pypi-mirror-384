from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Input, Output

from oasys2.widget import gui as oasysgui
from oasys2.widget.widget import OWWidget
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangecontrib.srw.util.srw_objects import SRWData

from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class OWFromWofryWavefront2d(OWWidget):
    name = "From Wofry Wavefront 2D"
    id = "fromWofryWavefront2D"
    description = "from Wofry Wavefront 2D"
    icon = "icons/from_wofry_wavefront_2d.png"
    priority = 20
    category = ""
    keywords = ["wise", "gaussian"]

    class Inputs:
        wofry_data = Input("Wofry Data", object, default=True, auto_summary=False)

    class Outputs:
        srw_data = Output("SRWData", SRWData, default=True, auto_summary=False)

    CONTROL_AREA_WIDTH = 405

    want_main_area = 0

    z = Setting(10.0)

    Rx = Setting(10.0)
    dRx = Setting(0.001)

    Ry = Setting(10.0)
    dRy = Setting(0.001)

    wavefront = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setFixedHeight(200)
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        box = oasysgui.widgetBox(self.controlArea, "SRW Wavefront Setting", addSpace=False, orientation="vertical", height=130)

        oasysgui.lineEdit(box, self, "z", "Longitudinal position of the wavefront",labelWidth=250, valueType=float, orientation="horizontal")

        box = oasysgui.widgetBox(box, "", addSpace=False, orientation="horizontal", height=70)

        box_1 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=60)
        box_2 = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", height=60)

        oasysgui.lineEdit(box_1, self, "Rx", "Rx",labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_1, self, "dRx", "dRx",labelWidth=50, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(box_2, self, "Ry", "Ry",labelWidth=50, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_2, self, "dRy", "dRy",labelWidth=50, valueType=float, orientation="horizontal")

        gui.button(self.controlArea, self, "Convert", callback=self.convert_wavefront, height=45)

    @Inputs.wofry_data
    def set_input(self, wofry_data):
        self.setStatusMessage("")

        if not wofry_data is None:
            self.wavefront = wofry_data.get_wavefront() # from wofry data

            self.convert_wavefront()

    def convert_wavefront(self):
        if not self.wavefront is None:
            try:
                self.Outputs.srw_data.send(SRWData(srw_wavefront=SRWWavefront.fromGenericWavefront(self.wavefront,
                                                                                                   z=self.z,
                                                                                                   Rx=self.Rx,
                                                                                                   dRx=self.dRx,
                                                                                                   Ry=self.Ry,
                                                                                                   dRy=self.dRy)))
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

add_widget_parameters_to_module(__name__)