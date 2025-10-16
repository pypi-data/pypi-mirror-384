from wofrysrw.util.srw import SRWLMagFldC, SRWLMagFld3D, array

from syned.storage_ring.magnetic_structure import MagneticStructure
from wofrysrw.storage_ring.srw_magnetic_structure import SRWMagneticStructure

# from original SRW Example 01, by Oleg Chubar (BNL)
def AuxReadInMagFld3D(filePath, sCom):
    f = open(filePath, 'r')
    f.readline()  # 1st line: just pass

    xStart = float(f.readline().split(sCom, 2)[1])  # 2nd line: initial X position [m]; it will not actually be used
    xStep = float(f.readline().split(sCom, 2)[1])  # 3rd line: step vs X [m]
    xNp = int(f.readline().split(sCom, 2)[1])  # 4th line: number of points vs X
    yStart = float(f.readline().split(sCom, 2)[1])  # 5th line: initial Y position [m]; it will not actually be used
    yStep = float(f.readline().split(sCom, 2)[1])  # 6th line: step vs Y [m]
    yNp = int(f.readline().split(sCom, 2)[1])  # 7th line: number of points vs Y
    zStart = float(f.readline().split(sCom, 2)[1])  # 8th line: initial Z position [m]; it will not actually be used
    zStep = float(f.readline().split(sCom, 2)[1])  # 9th line: step vs Z [m]
    zNp = int(f.readline().split(sCom, 2)[1])  # 10th line: number of points vs Z

    totNp = xNp * yNp * zNp

    locArBx = array('d', [0] * totNp)
    locArBy = array('d', [0] * totNp)
    locArBz = array('d', [0] * totNp)

    for i in range(totNp):
        curLineParts = f.readline().split('\t')
        if len(curLineParts) == 3:
            locArBx[i] = float(curLineParts[0].strip())
            locArBy[i] = float(curLineParts[1].strip())
            locArBz[i] = float(curLineParts[2].strip())

    f.close()

    xRange = xStep
    if xNp > 1: xRange = (xNp - 1) * xStep
    yRange = yStep
    if yNp > 1: yRange = (yNp - 1) * yStep
    zRange = zStep
    if zNp > 1: zRange = (zNp - 1) * zStep

    return SRWLMagFld3D(locArBx, locArBy, locArBz, xNp, yNp, zNp, xRange, yRange, zRange, 1)

class SRW3DMagneticStructure(MagneticStructure, SRWMagneticStructure):

    def __init__(self,
                 file_name="",
                 comment_character="#",
                 interpolation_method=1):
        MagneticStructure.__init__(self)

        self.file_name = file_name
        self.comment_character = comment_character
        self.interpolation_method=interpolation_method

    def get_SRWMagneticStructure(self):
        return AuxReadInMagFld3D(self.file_name, self.comment_character)

    def get_SRWLMagFldC(self):
        magnetic_field_container = SRWLMagFldC()  # Container
        magnetic_field_container.allocate(1)  # Magnetic Field consists of 1 part

        magnetic_field_container.arMagFld[0] = self.get_SRWMagneticStructure()
        magnetic_field_container.arMagFld[0].interp = self.interpolation_method
        magnetic_field_container.arXc[0] = self.horizontal_central_position
        magnetic_field_container.arYc[0] = self.vertical_central_position
        magnetic_field_container.arZc[0] = self.longitudinal_central_position

        magnetic_field_container.arMagFld[0].nRep = 1

        return magnetic_field_container

    @classmethod
    def get_default_initial_z(cls, file_name, comment_character="#", longitudinal_central_position=0):
        return longitudinal_central_position - 0.5*AuxReadInMagFld3D(file_name, comment_character).rz

    @classmethod
    def get_source_length(cls, file_name, comment_character="#"):
        return AuxReadInMagFld3D(file_name, comment_character).rz

    def to_python_code(self, data=None):
        text_code  = self.to_python_code_aux()
        text_code += "magnetic_field_container = SRWLMagFldC()" + "\n"
        text_code += "magnetic_field_container.allocate(1)" + "\n"
        text_code += "magnetic_field_container.arMagFld[0] = magnetic_structure" + "\n"
        text_code += "magnetic_field_container.arMagFld[0].interp = " + str(self.interpolation_method) + "\n"
        text_code += "magnetic_field_container.arXc[0] = " + str(self.horizontal_central_position) + "\n"
        text_code += "magnetic_field_container.arYc[0] = " + str(self.vertical_central_position) + "\n"
        text_code += "magnetic_field_container.arZc[0] = " + str(self.longitudinal_central_position) + "\n"

        return text_code

    def to_python_code_aux(self):
        text_code = "def AuxReadInMagFld3D(filePath, sCom):" + "\n" + \
                    "    f = open(filePath, 'r')" + "\n" + \
                    "    f.readline()  # 1st line: just pass" + "\n\n" + \
                    "    xStart = float(f.readline().split(sCom, 2)[1])  # 2nd line: initial X position [m]; it will not actually be used" + "\n" + \
                    "    xStep  = float(f.readline().split(sCom, 2)[1])  # 3rd line: step vs X [m]" + "\n" + \
                    "    xNp = int(f.readline().split(sCom, 2)[1])  # 4th line: number of points vs X" + "\n" + \
                    "    yStart = float(f.readline().split(sCom, 2)[1])  # 5th line: initial Y position [m]; it will not actually be used" + "\n" + \
                    "    yStep = float(f.readline().split(sCom, 2)[1])  # 6th line: step vs Y [m]" + "\n" + \
                    "    yNp = int(f.readline().split(sCom, 2)[1])  # 7th line: number of points vs Y" + "\n" + \
                    "    zStart = float(f.readline().split(sCom, 2)[1])  # 8th line: initial Z position [m]; it will not actually be used" + "\n" + \
                    "    zStep = float(f.readline().split(sCom, 2)[1])  # 9th line: step vs Z [m]" + "\n" + \
                    "    zNp = int(f.readline().split(sCom, 2)[1])  # 10th line: number of points vs Z" + "\n" + \
                    "    totNp = xNp * yNp * zNp" + "\n" + \
                    "    locArBx = array('d', [0] * totNp)" + "\n" + \
                    "    locArBy = array('d', [0] * totNp)" + "\n" + \
                    "    locArBz = array('d', [0] * totNp)" + "\n\n" + \
                    "    for i in range(totNp):" + "\n" + \
                    "        curLineParts = f.readline().split('\t')" + "\n" + \
                    "        if len(curLineParts) == 3:" + "\n" + \
                    "            locArBx[i] = float(curLineParts[0].strip())" + "\n" + \
                    "            locArBy[i] = float(curLineParts[1].strip())" + "\n" + \
                    "            locArBz[i] = float(curLineParts[2].strip())" + "\n" + \
                    "    f.close()" + "\n" + \
                    "    xRange = xStep" + "\n" + \
                    "    if xNp > 1: xRange = (xNp - 1) * xStep" + "\n" + \
                    "    yRange = yStep" + "\n" + \
                    "    if yNp > 1: yRange = (yNp - 1) * yStep" + "\n" + \
                    "    zRange = zStep" + "\n" + \
                    "    if zNp > 1: zRange = (zNp - 1) * zStep" + "\n" + \
                    "    return SRWLMagFld3D(locArBx, locArBy, locArBz, xNp, yNp, zNp, xRange, yRange, zRange, 1)\n\n"

        text_code += "magnetic_structure = AuxReadInMagFld3D(\"" + str(self.file_name) + "\",\"" + str(self.comment_character) + "\")" + "\n"

        return text_code

