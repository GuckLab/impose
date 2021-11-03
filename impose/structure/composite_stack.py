import numpy as np

from ..util import equal_states

from .composite import StructureComposite


class StructureCompositeStack:
    def __init__(self):
        self.composites = []

    def __add__(self, stack):
        new = StructureCompositeStack()
        for sc in self:
            new.append(sc)
        for sc in stack:
            new.append(sc)
        return new

    def __eq__(self, other):
        return equal_states(self.__getstate__(), other.__getstate__())

    def __getitem__(self, index):
        return self.composites[index]

    def __iter__(self):
        return iter(self.composites)

    def __iadd__(self, stack):
        for sc in stack:
            self.append(sc)
        return self

    def __len__(self):
        return len(self.composites)

    def __getstate__(self):
        composites = []
        for sc in self.composites:
            composites.append(sc.__getstate__())
        return dict(composites=composites)

    def __setstate__(self, state):
        self.clear()
        for scstate in state["composites"]:
            sc = StructureComposite()
            sc.__setstate__(scstate)
            self.append(sc)

    @property
    def position_um(self):
        """Return center position of the structure composite stack

        The center is computed from the center of the underlying
        structures composites.
        """
        cx = []
        cy = []
        for sc in self.composites:
            cxi, cyi = sc.position_um
            cx.append(cxi)
            cy.append(cyi)
        return np.mean(cx), np.mean(cy)

    def append(self, sc):
        """Append a structure layer"""
        assert isinstance(sc, StructureComposite)
        self.composites.append(sc)

    def clear(self):
        self.composites.clear()

    def get_mean(self):
        """Return the mean composite structure of the composite stack"""
        if len(self) == 0:
            return StructureComposite()
        elif len(self) == 1:
            return self.composites[0].copy()
        else:
            raise NotImplementedError("Averaging not implemented yet!")

    def rotate(self, dphi, origin_um=None):
        """Rotate the compoiste stack

        Parameters
        ----------
        dphi: float
            rotation angle [rad]
        origin_um: tuple of floats
            x-y-coordinates of the center of rotation [µm]
        """
        if origin_um is None:
            origin_um = self.position_um
        for sc in self.composites:
            sc.rotate(dphi, origin_um)

    def translate(self, dr_um):
        """Translate the composite stack by dr_um = (dx, dy) [µm]"""
        for sc in self.composites:
            sc.translate(dr_um)
