from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

from syned.beamline.shape import Plane
from wofrysrw.beamline.optical_elements.mirrors.srw_plane_mirror import SRWPlaneMirror
from orangecontrib.srw.widgets.gui.ow_srw_mirror import OWSRWMirror

class OWSRWPlaneMirror(OWSRWMirror):

    name = "Plane Mirror"
    description = "SRW: Plane Mirror"
    icon = "icons/plane_mirror.png"
    priority = 4

    def __init__(self):
        super().__init__()

    def get_mirror_instance(self):
        return SRWPlaneMirror()

    def receive_shape_specific_syned_data(self, optical_element):
        if not isinstance(optical_element.get_surface_shape(), Plane):
            raise Exception("Syned Data not correct: Mirror Surface Shape is not Plane")

add_widget_parameters_to_module(__name__)