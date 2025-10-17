import os

import orangecanvas.resources as resources

from syned_gui.error_profile.abstract_dabam_height_profile import OWAbstractDabamHeightProfile

from orangewidget.widget import Output
from oasys2.widget.util.widget_objects import OasysPreProcessorData, OasysErrorProfileData, OasysSurfaceData
import oasys2.widget.util.widget_util as OU
from oasys2.canvas.util.canvas_util import add_widget_parameters_to_module

class OWdabam_height_profile(OWAbstractDabamHeightProfile):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; lrebuffi@anl.gov"
    priority = 5
    category = ""
    keywords = ["dabam_height_profile"]

    class Outputs:
        dabam_output      = OWAbstractDabamHeightProfile.Outputs.dabam_output
        preprocessor_data = Output(name="PreProcessor Data",
                                   type=OasysPreProcessorData,
                                   id="PreProcessor Data",
                                   default=True, auto_summary=False)

    usage_path = os.path.join(resources.package_dirname("orangecontrib.syned.widgets.tools"), "misc", "dabam_height_profile_usage.png")

    def __init__(self):
        super().__init__()

    def get_usage_path(self):
        return self.usage_path

    def write_error_profile_file(self):
        if not (self.heigth_profile_file_name.endswith("hd5") or self.heigth_profile_file_name.endswith("hdf5") or self.heigth_profile_file_name.endswith("hdf")):
            self.heigth_profile_file_name += ".hdf5"

        OU.write_surface_file(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.Outputs.preprocessor_data.send(OasysPreProcessorData(error_profile_data=OasysErrorProfileData(surface_data=OasysSurfaceData(xx=self.xx,
                                                                                                                                    yy=self.yy,
                                                                                                                                    zz=self.zz,
                                                                                                                                    surface_data_file=self.heigth_profile_file_name),
                                                                                                      error_profile_x_dim=dimension_x,
                                                                                                      error_profile_y_dim=dimension_y)))

add_widget_parameters_to_module(__name__)
