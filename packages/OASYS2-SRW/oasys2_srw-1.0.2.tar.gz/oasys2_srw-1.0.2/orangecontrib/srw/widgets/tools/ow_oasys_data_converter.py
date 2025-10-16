import os

from orangewidget import gui
from orangewidget.widget import Input, Output
from oasys2.widget.widget import OWWidget
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from oasys2.widget.util.widget_objects import OasysPreProcessorData, OasysSurfaceData

from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWErrorProfileData
import orangecontrib.srw.util.srw_util as SU

class OWOasysDataConverter(OWWidget):
    name = "Oasys Surface Data Converter"
    id = "oasysDataConverter"
    description = "Oasys Surface Data Converter"
    icon = "icons/oasys_data_converter.png"
    priority = 0
    category = ""
    keywords = ["wise", "gaussian"]

    class Inputs:
        preprocessor_data = Input("Oasys PreProcessor Data", OasysPreProcessorData, default=False, auto_summary=False)
        surface_data      = Input("Oasys Surface Data", OasysSurfaceData, default=False, auto_summary=False)

    class Outputs:
        preprocessor_data = Output("PreProcessor Data", SRWPreProcessorData, default=True, auto_summary=False)

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    oasys_data = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)


        label = gui.label(self.controlArea, self, "From Oasys Surface To SRW Surface")
        label.setStyleSheet("color: darkblue; font-weight: bold; font-style: italic; font-size: 14px")

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_surface, height=45)

    @Inputs.preprocessor_data
    def set_preprocessor_data(self, preprocessor_data):
        self.set_input(preprocessor_data)

    @Inputs.surface_data
    def set_surface_data(self, surface_data):
        self.set_input(surface_data)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.oasys_data = input_data

            self.convert_surface()

    def convert_surface(self):
        if not self.oasys_data is None:
            try:
                if isinstance(self.oasys_data, OasysPreProcessorData):
                    error_profile_data = self.oasys_data.error_profile_data
                    surface_data = error_profile_data.surface_data
                    error_profile_data_file = surface_data.surface_data_file

                    filename, file_extension = os.path.splitext(error_profile_data_file)

                    if (file_extension==".hd5" or file_extension==".hdf5" or file_extension==".hdf" or file_extension==".h5"):
                        error_profile_data_file = filename + "_srw.dat"

                    SU.write_error_profile_file(surface_data.zz, surface_data.xx, surface_data.yy, error_profile_data_file)

                    self.Outputs.preprocessor_data.send(SRWPreProcessorData(error_profile_data=SRWErrorProfileData(error_profile_data_file=error_profile_data_file,
                                                                                                                   error_profile_x_dim=error_profile_data.error_profile_x_dim,
                                                                                                                   error_profile_y_dim=error_profile_data.error_profile_y_dim)))
                elif isinstance(self.oasys_data, OasysSurfaceData):
                    surface_data_file = self.oasys_data.surface_data_file

                    filename, file_extension = os.path.splitext(surface_data_file)

                    if (file_extension==".hd5" or file_extension==".hdf5" or file_extension==".hdf" or file_extension==".h5"):
                        surface_data_file = filename + "_srw.dat"

                    SU.write_error_profile_file(self.oasys_data.zz, self.oasys_data.xx, self.oasys_data.yy, surface_data_file)

                    error_profile_x_dim = abs(self.oasys_data.xx[-1] - self.oasys_data.xx[0])
                    error_profile_y_dim = abs(self.oasys_data.yy[-1] - self.oasys_data.yy[0])

                    self.Outputs.preprocessor_data.send(SRWPreProcessorData(error_profile_data=SRWErrorProfileData(error_profile_data_file=surface_data_file,
                                                                                                                   error_profile_x_dim=error_profile_x_dim,
                                                                                                                   error_profile_y_dim=error_profile_y_dim)))

            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception

add_widget_parameters_to_module(__name__)