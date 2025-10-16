import os

import orangecanvas.resources as resources

from orangewidget.widget import Output
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module
from oasys2.widget import gui as oasysgui

from syned_gui.error_profile.abstract_dabam_height_profile import OWAbstractDabamHeightProfile

from orangecontrib.srw.util.srw_objects import SRWPreProcessorData, SRWErrorProfileData
import orangecontrib.srw.util.srw_util as SU

class OWdabam_height_profile(OWAbstractDabamHeightProfile):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 2
    category = ""
    keywords = ["dabam_height_profile"]

    class Outputs:
        dabam_output      = OWAbstractDabamHeightProfile.Outputs.dabam_output
        preprocessor_data = Output(name="PreProcessor Data",
                                   type=SRWPreProcessorData,
                                   id="PreProcessor Data",
                                   default=True, auto_summary=False)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.srw.widgets.gui"), "misc", "dabam_height_profile_usage.png")

    def __init__(self):
        super().__init__()

        if not self.heigth_profile_file_name is None:
            if self.heigth_profile_file_name.endswith("hdf5"):
                self.heigth_profile_file_name = self.heigth_profile_file_name[:-4] + "dat"

    def get_usage_path(self):
        return self.usage_path

    def selectFile(self):
        self.le_heigth_profile_file_name.setText(oasysgui.selectSaveFileFromDialog(self, "Save as Output File",
                                                                                   default_file_name="mirror_error_profile.dat",
                                                                                   file_extension_filter="SRW Data Files (*.dat)"))


    def write_error_profile_file(self):
        SU.write_error_profile_file(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.Outputs.dabam_output.send(SRWPreProcessorData(error_profile_data=SRWErrorProfileData(error_profile_data_file=self.heigth_profile_file_name,
                                                                                                  error_profile_x_dim=dimension_x,
                                                                                                  error_profile_y_dim=dimension_y)))

add_widget_parameters_to_module(__name__)