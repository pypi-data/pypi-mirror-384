from wofrysrw.storage_ring.srw_light_source import SRWLightSource
from wofrysrw.storage_ring.magnetic_structures.srw_3d_magnetic_structure import SRW3DMagneticStructure
from wofrysrw.storage_ring.srw_electron_beam import SRWElectronBeam

class SRW3DLightSource(SRWLightSource):

    def __init__(self,
                 name="Undefined",
                 electron_beam=SRWElectronBeam(),
                 magnet_magnetic_structure=SRW3DMagneticStructure()):

        super().__init__(name,
                         electron_beam=electron_beam,
                         magnetic_structure=magnet_magnetic_structure)
