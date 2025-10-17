import numpy

from orangewidget.settings import Setting
from oasys2.widget import gui as oasysgui
from oasys2.widget.util import congruence
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.beamline.shape import Toroid

from wofrysrw.beamline.optical_elements.mirrors.srw_toroidal_mirror import SRWToroidalMirror

from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWToroidallMirror(OWSRWMirror):

    name = "Toroidal Mirror"
    description = "SRW: Toroidal Mirror"
    icon = "icons/toroidal_mirror.png"
    priority = 5

    tangential_radius  = Setting(1.0)
    sagittal_radius = Setting(1.0)

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWToroidalMirror(tangential_radius=self.tangential_radius,
                                 sagittal_radius=self.sagittal_radius)

    def draw_specific_box(self):
        super().draw_specific_box()

        oasysgui.lineEdit(self.mirror_box, self, "tangential_radius", "Tangential Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.mirror_box, self, "sagittal_radius", "Sagittal Radius [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element.get_surface_shape(), Toroid):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Toroidal")

        rs, rt = optical_element.get_surface_shape().get_radii()

        self.tangential_radius = numpy.round(rt, 6)
        self.sagittal_radius = numpy.round(rs, 6)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.tangential_radius,  "Tangential Radius")
        congruence.checkStrictlyPositiveNumber(self.sagittal_radius, "Sagittal Radius")

add_widget_parameters_to_module(__name__)