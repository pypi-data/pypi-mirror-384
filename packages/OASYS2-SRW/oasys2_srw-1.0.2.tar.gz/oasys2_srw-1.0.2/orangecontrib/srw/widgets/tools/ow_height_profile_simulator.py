import os

import orangecanvas.resources as resources

from orangewidget.widget import Output
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget import gui as oasysgui
from syned_gui.error_profile.abstract_height_profile_simulator import OWAbstractHeightErrorProfileSimulator

from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWErrorProfileData
import orangecontrib.srw.util.srw_util as SU

class OWheight_profile_simulator(OWAbstractHeightErrorProfileSimulator):
    name = "Height Profile Simulator"
    id = "height_profile_simulator"
    description = "Calculation of mirror surface height profile"
    icon = "icons/simulator.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 1
    category = ""
    keywords = ["height_profile_simulator"]

    class Outputs:
        preprocessor_data = Output(name="PreProcessor Data",
                                   type=SRWPreProcessorData,
                                   id="PreProcessor Data",
                                   default=True, auto_summary=False)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "height_error_profile_usage.png")

    def __init__(self):
        super().__init__()

        if not self.heigth_profile_file_name is None:
            if self.heigth_profile_file_name.endswith("hdf5"):
                self.heigth_profile_file_name = self.heigth_profile_file_name[:-4] + "dat"

    def get_usage_path(self):
        return self.usage_path

    def write_error_profile_file(self):
        SU.write_error_profile_file(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.Outputs.preprocessor_data.send(SRWPreProcessorData(error_profile_data=SRWErrorProfileData(error_profile_data_file=self.heigth_profile_file_name,
                                                                                                       error_profile_x_dim=dimension_x,
                                                                                                       error_profile_y_dim=dimension_y)))

    def selectFile(self):
        self.le_heigth_profile_file_name.setText(oasysgui.selectSaveFileFromDialog(self, "Save as Output File",
                                                                                   default_file_name="mirror_error_profile.dat",
                                                                                   file_extension_filter="SRW Data Files (*.dat)"))

add_widget_parameters_to_module(__name__)
