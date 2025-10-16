
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from orangewidget import gui
from oasys.widgets import congruence
from oasys.util.oasys_util import ChemicalFormulaParser

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElementWithSurfaceShape

from syned.beamline.optical_elements.mirrors.mirror import Mirror


class OWMirror(OWOpticalElementWithSurfaceShape):

    name = "Mirror"
    description = "Syned: Mirror"
    icon = "icons/mirror.png"
    priority = 6

    coating_flag = 1
    coating_material = Setting("Pt")
    coating_thickness = Setting(0.0)

    def __init__(self):
        super().__init__()

    def draw_specific_box(self):

        self.tab_shape = oasysgui.createTabPage(self.tabs_setting, "Surface Shape")
        self.tab_mir = oasysgui.createTabPage(self.tabs_setting, "Mirror Setting")
        super().draw_specific_box(self.tab_shape)

        self.coating_box = oasysgui.widgetBox(self.tab_mir, "Coating", addSpace=True, orientation="vertical")

        gui.comboBox(self.coating_box, self, "coating_flag", label="Define coating", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.coating_subbox = oasysgui.widgetBox(self.coating_box, "", addSpace=True, orientation="vertical")
        oasysgui.lineEdit(self.coating_subbox, self, "coating_material", "Material [Chemical Formula]", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.coating_subbox, self, "coating_thickness", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_visibility()

    def set_visibility(self):
        self.coating_subbox.setVisible(self.coating_flag == 1)


    def get_optical_element(self):

        if self.coating_flag == 0:
            coating_material = None
            coating_thickness = None
        else:
            coating_material = self.coating_material
            coating_thickness = self.coating_thickness

        return Mirror(name=self.oe_name,
                      boundary_shape=self.get_boundary_shape(),
                      surface_shape=self.get_surface_shape(),
                      coating=coating_material,
                      coating_thickness=coating_thickness)

    def check_data(self):
        super().check_data()

        if self.coating_flag == 1:
            congruence.checkEmptyString(self.coating_material, "Coating Material")
            ChemicalFormulaParser.parse_formula(self.coating_material)
            congruence.checkStrictlyPositiveNumber(self.coating_thickness, "Coating Thickness")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWMirror()

    ow.show()
    a.exec_()
