#TODO: this widget is valid for 1D and 2D wavefronts. Is there a better way to discriminate without duplicating widgets?

import os
from AnyQt.QtWidgets import QMessageBox

try:
    from silx.gui.dialog.DataFileDialog import DataFileDialog
except:
    print("Fail to import silx.gui.dialog.DataFileDialog: need silx >= 0.7")

from orangewidget import gui
from orangewidget.settings import Setting
from orangewidget.widget import Output

from oasys2.widget.widget import OWWidget, OWAction
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from orangecontrib.srw.util.srw_objects import SRWData
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront
from wofrysrw.util.srw_hdf5 import load_hdf5_2_wfr

class OWWavefrontFileReader(OWWidget):
    name = "SRW Wavefront File Reader"
    description = "Utility: SRW Wavefront File Reader"
    icon = "icons/file_reader.png"
    maintainer = "Manuel Sanchez del Rio"
    maintainer_email = "srio(@at@)esrf.eu"
    priority = 9
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    file_name = Setting("")
    data_path = Setting("")

    class Outputs:
        srw_data = Output("SRWData", SRWData, id="SRWData", default=True, auto_summary=False)

    def __init__(self):
        super().__init__()

        self.runaction = OWAction("Read Wavefront hdf5 File", self)
        self.runaction.triggered.connect(self.read_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(250)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "HDF5 Local File Selection", addSpace=True,
                                        orientation="vertical",width=570, height=100)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="vertical", width=550, height=50)

        self.le_file_name = oasysgui.lineEdit(figure_box, self, "file_name", "File Name",
                                                    labelWidth=190, valueType=str, orientation="horizontal")
        self.le_file_name.setFixedWidth(360)

        self.le_data_path = oasysgui.lineEdit(figure_box, self, "data_path", "Group (wavefront name)",
                                                    labelWidth=190, valueType=str, orientation="horizontal")
        self.le_data_path.setFixedWidth(360)

        gui.separator(left_box_1, height=20)

        button = gui.button(self.controlArea, self, "Browse File and Send Data", callback=self.read_file)
        button.setFixedHeight(45)
        gui.separator(self.controlArea, height=20)
        button = gui.button(self.controlArea, self, "Send Data", callback=self.send_data)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)


    def read_file(self):
        try:
            dialog = DataFileDialog(self)
            dialog.setFilterMode(DataFileDialog.FilterMode.ExistingGroup)

            path, filename = os.path.split(self.file_name)
            print("Setting path: ",path)
            dialog.setDirectory(path)

            # Execute the dialog as modal
            result = dialog.exec_()
            if result:
                print("Selection:")
                print(dialog.selectedFile())
                print(dialog.selectedUrl())
                print(dialog.selectedDataUrl().data_path())
                self.file_name = dialog.selectedFile()
                self.data_path = dialog.selectedDataUrl().data_path()
                self.send_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

    def send_data(self):
        try:
            congruence.checkEmptyString(self.file_name, "File Name")
            congruence.checkFile(self.file_name)
            native_srw_wavefront = load_hdf5_2_wfr(self.file_name, self.data_path)
            self.Outputs.srw_data.send(SRWData(srw_wavefront=SRWWavefront.decorateSRWWF(native_srw_wavefront)))
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

add_widget_parameters_to_module(__name__)

