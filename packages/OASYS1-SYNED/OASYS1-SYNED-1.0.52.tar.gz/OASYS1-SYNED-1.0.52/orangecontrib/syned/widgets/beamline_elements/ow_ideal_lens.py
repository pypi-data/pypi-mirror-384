from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElement

from syned.beamline.optical_elements.ideal_elements.ideal_lens import IdealLens

class OWIdealLens(OWOpticalElement):

    name = "Ideal Lens"
    description = "Syned: Ideal Lens"
    icon = "icons/ideal_lens.png"
    priority = 5

    focal_x = Setting(0.0)
    focal_y = Setting(0.0)

    def __init__(self):
        super().__init__()

    def draw_specific_box(self):

        self.filter_box = oasysgui.widgetBox(self.tab_bas, "Ideal Lens Setting", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.filter_box, self, "focal_x", "Horizontal Focal Length [m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.filter_box, self, "focal_y", "Vertical Focal Length [m]", labelWidth=260, valueType=float, orientation="horizontal")


    def get_optical_element(self):
        return IdealLens(name=self.oe_name,
                         focal_x=self.focal_x,
                         focal_y=self.focal_y)

    def check_data(self):
        super().check_data()

        congruence.checkStrictlyPositiveNumber(self.focal_x, "Horizontal Focal Length")
        congruence.checkStrictlyPositiveNumber(self.focal_y, "Vertical Focal Length")


