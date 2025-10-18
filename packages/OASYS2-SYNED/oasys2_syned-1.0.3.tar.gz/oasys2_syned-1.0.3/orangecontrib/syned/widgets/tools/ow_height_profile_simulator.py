import os, numpy

import orangecanvas.resources as resources

from syned_gui.error_profile.abstract_height_profile_simulator import OWAbstractHeightErrorProfileSimulator

from orangewidget.widget import Output
from oasys2.widget.util.widget_objects import OasysPreProcessorData, OasysErrorProfileData, OasysSurfaceData
import oasys2.widget.util.widget_util as OU
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

class OWHeightProfileSimulator(OWAbstractHeightErrorProfileSimulator):
    name = "Height Profile Simulator"
    id = "height_profile_simulator"
    description = "Calculation of mirror surface height profile"
    icon = "icons/simulator.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 4
    category = ""
    keywords = ["height_profile_simulator"]

    class Outputs:
        preprocessor_data = Output(name="PreProcessor Data",
                                   type=OasysPreProcessorData,
                                   id="PreProcessor Data",
                                   default=True, auto_summary=False)
        dabam_output = Output(name="DABAM 1D Profile",
                              type=numpy.ndarray,
                              id="DABAM 1D Profile",
                              default=True, auto_summary=False)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.syned.widgets.tools"), "misc", "height_error_profile_usage.png")

    def __init__(self):
        super().__init__()

    def get_usage_path(self):
        return self.usage_path

    def write_error_profile_file(self):
        if not (self.heigth_profile_file_name.endswith("h5") or self.heigth_profile_file_name.endswith("hdf5") or self.heigth_profile_file_name.endswith("hdf")):
            self.heigth_profile_file_name += ".hdf5"

        OU.write_surface_file(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.Outputs.preprocessor_data.send(OasysPreProcessorData(error_profile_data=OasysErrorProfileData(surface_data=OasysSurfaceData(xx=self.xx,
                                                                                                           yy=self.yy,
                                                                                                           zz=self.zz,
                                                                                                           surface_data_file=self.heigth_profile_file_name),
                                                                                 error_profile_x_dim=dimension_x,
                                                                                 error_profile_y_dim=dimension_y)))
        self.send_1Dprofile()

    def send_1Dprofile(self):
        if self.yy is None: raise Exception("No Profile Selected")
        profile1D = numpy.zeros((self.yy.size, 2))
        profile1D[:, 0] = self.yy
        profile1D[:, 1] = self.zz[: , self.zz.shape[1] // 2]

        self.Outputs.dabam_output.send(profile1D)

add_widget_parameters_to_module(__name__)
