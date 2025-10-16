import numpy

from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import ChemicalFormulaParser

from orangecontrib.syned.widgets.gui.ow_optical_element import OWOpticalElementWithSurfaceShape

from syned.beamline.optical_elements.crystals.crystal import Crystal, DiffractionGeometry
from orangewidget import gui

class OWCrystal(OWOpticalElementWithSurfaceShape):

    name = "Crystal"
    description = "Syned: Crystal"
    icon = "icons/crystal.png"
    priority = 7

    material = Setting("Si")
    miller_index_h = Setting(1)
    miller_index_k = Setting(1)
    miller_index_l = Setting(1)
    asymmetry_flag = Setting(0)
    asymmetry_angle = Setting(0.0)
    thickness_thin_or_thick = Setting(0)  # 0=thin, 1=thick
    thickness = Setting(0.0)
    diffraction_geometry = Setting(DiffractionGeometry.BRAGG)

    def __init__(self):
        super().__init__()

    def draw_specific_box(self):

        self.tab_shape = oasysgui.createTabPage(self.tabs_setting, "Surface Shape")
        self.tab_cry = oasysgui.createTabPage(self.tabs_setting, "Crystal Setting")

        super().draw_specific_box(self.tab_shape)

        self.crystal_box = oasysgui.widgetBox(self.tab_cry, "Crystal", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.crystal_box, self, "material", "Material [descriptor]", labelWidth=260, valueType=str, orientation="horizontal")


        oasysgui.lineEdit(self.crystal_box, self, "miller_index_h", "Miller Index h", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.crystal_box, self, "miller_index_k", "Miller Index j", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.crystal_box, self, "miller_index_l", "Miller Index l", labelWidth=260, valueType=int, orientation="horizontal")


        self.geometry_box = oasysgui.widgetBox(self.tab_cry, "Geometry", addSpace=True, orientation="vertical")
        gui.comboBox(self.geometry_box, self, "diffraction_geometry", label="Diffraction Geometry", labelWidth=350,
                     items=["Bragg", "Laue"],
                     sendSelectedValue=False, orientation="horizontal")


        # thickness
        self.thickness_box = oasysgui.widgetBox(self.tab_cry, "Thickness", addSpace=True, orientation="vertical")
        gui.comboBox(self.thickness_box, self, "thickness_thin_or_thick", label="Thickness model", labelWidth=350,
                     items=["Thin", "Thick"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.thickness_subbox = oasysgui.widgetBox(self.thickness_box, "", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(self.thickness_subbox, self, "thickness", "Thickness [m]", labelWidth=260, valueType=float, orientation="horizontal")

        # asymmetry
        self.asymmetry_box = oasysgui.widgetBox(self.tab_cry, "Asymmetry", addSpace=True, orientation="vertical")
        gui.comboBox(self.asymmetry_box, self, "asymmetry_flag", label="Asymetric cut", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_visibility,
                     sendSelectedValue=False, orientation="horizontal")

        self.asymmetry_subbox = oasysgui.widgetBox(self.asymmetry_box, "", addSpace=True, orientation="vertical")


        oasysgui.lineEdit(self.asymmetry_subbox, self, "asymmetry_angle", "Asymmetry Angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_visibility()

    def set_visibility(self):
        self.thickness_subbox.setVisible(self.thickness_thin_or_thick == 0)
        self.asymmetry_subbox.setVisible(self.asymmetry_flag == 1)

    def get_optical_element(self):

        if self.thickness_thin_or_thick == 1: #
            thickness = 1e5
        else:
            thickness = self.thickness

        if self.asymmetry_angle == 0:
            if self.diffraction_geometry == DiffractionGeometry.BRAGG:
                asymmetry_angle = 0.0
            elif self.diffraction_geometry == DiffractionGeometry.LAUE:
                asymmetry_angle = 90.0
        else:
            asymmetry_angle = self.asymmetry_angle

        return Crystal(name=self.oe_name,
                       boundary_shape=self.get_boundary_shape(),
                       surface_shape=self.get_surface_shape(),
                       material=self.material,
                       miller_index_h=self.miller_index_h,
                       miller_index_k=self.miller_index_k,
                       miller_index_l=self.miller_index_l,
                       diffraction_geometry=self.diffraction_geometry,
                       asymmetry_angle=numpy.radians(asymmetry_angle),
                       thickness=thickness)

    def check_data(self):
        super().check_data()

        congruence.checkEmptyString(self.material, "Material")
        ChemicalFormulaParser.parse_formula(self.material)
        if self.thickness_thin_or_thick == 0:
            congruence.checkStrictlyPositiveNumber(self.thickness, "Thickness")
        if self.asymmetry_flag == 1:
            congruence.checkNumber(self.asymmetry_angle, "Asymmetry angle")
        congruence.checkNumber(self.miller_index_h, "Miller index h")
        congruence.checkNumber(self.miller_index_k, "Miller index k")
        congruence.checkNumber(self.miller_index_l, "Miller index l")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    a = QApplication(sys.argv)
    ow = OWCrystal()

    ow.show()
    a.exec_()