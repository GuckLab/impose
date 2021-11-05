from collections import OrderedDict

import numpy as np

from ..geometry import shapes as gshapes
from ..util import equal_states

from .layer import StructureLayer


class StructureComposite:
    def __init__(self):
        self.layers = []

    def __contains__(self, sl):
        if isinstance(sl, str):
            try:
                self[sl]
            except KeyError:
                return False
            else:
                return True
        elif isinstance(sl, StructureLayer):
            return sl in self.layers
        else:
            raise ValueError(f"Expected str or StructureLayer, got '{sl}'")

    def __eq__(self, other):
        return equal_states(self.__getstate__(), other.__getstate__())

    def __getitem__(self, index):
        if isinstance(index, int):
            return self.layers[index]
        elif isinstance(index, str):
            for sl in self.layers:
                if sl.label == index:
                    return sl
            else:
                raise KeyError(f"Could not find layer '{index}'!")
        else:
            raise KeyError(f"Expected int or str, got '{index}'")

    def __iter__(self):
        return iter(self.layers)

    def __len__(self):
        return len(self.layers)

    def __getstate__(self):
        layers = []
        for ll in self.layers:
            layers.append(ll.__getstate__())
        return dict(layers=layers)

    def __setstate__(self, state):
        self.layers.clear()
        for lstate in state["layers"]:
            self.append(StructureLayer.from_state(lstate))

    def __str__(self):
        lstr = "".join(["\n - {}".format(ll) for ll in self.layers])
        return "StructureComposite:{}".format(lstr)

    def __repr__(self):
        rpr = f"<StructureComposite: ({len(self.layers)} layers) " \
            + f"at {hex(id(self))}>"
        return rpr

    @property
    def point_um(self):
        """Point size in microns"""
        if self.layers:
            return self.layers[0].point_um
        else:
            return None

    @property
    def position_um(self):
        """Return center position of the structure composite

        The center is computed from the center of the underlying
        structures layers.
        """
        cx = []
        cy = []
        for sl in self.layers:
            cxi, cyi = sl.position_um
            cx.append(cxi)
            cy.append(cyi)
        return np.mean(cx), np.mean(cy)

    def append(self, sl):
        """Append a structure layer"""
        assert isinstance(sl, StructureLayer)
        if self.layers:
            if self.layers[0].point_um != sl.point_um:
                raise ValueError("All StructureLayers in a StructureComposite "
                                 + "must have the same `point_um`!")
        for ll in self.layers:
            if ll.label == sl.label:
                raise ValueError("A layer with the label "
                                 + "'{}' already exists!".format(sl.label))
        self.layers.append(sl)

    def change_layer_label(self, old_label, new_label, force=False):
        """Change the label of a StructureLayer"""
        if old_label == new_label:
            # nothing to do
            return
        sl = self[old_label]
        if new_label in self and not force:
            # TODO: instead of blindly overriding, change the other label in
            #  "force" mode.
            raise ValueError("Layer with label '{}' already ".format(new_label)
                             + "exists!")
        else:
            # update the private StructureLayer label property
            sl._label = new_label

    def copy(self):
        sc = StructureComposite()
        for sl in self.layers:
            sc.append(sl.copy())
        return sc

    def extract_data(self, data_source, channels=None):
        """Extract the relevant data points from a data source

        Parameters
        ----------
        data_source: impose.data.DataSource
            Data source from which to extract data
        channels: list of str
            List of channel names for which to extract data

        Returns
        -------
        data: OrderedDict of dicts {str: np.ndarray}
            Nested dictionary. The outer dictionary has
            StructureLayer labels as keys and the inner
            dictionary has DataSource channel names as
            keys.
        """
        data = OrderedDict()
        for sl in self.layers:
            data[sl.label] = sl.extract_data(data_source, channels)
        return data

    def geometry_identical_to(self, other) -> bool:
        """Return `True` if the StrucureComposite has the same geometry"""
        assert isinstance(other, StructureComposite)
        try:
            sig1 = self.to_point_signature()
            sig2 = other.to_point_signature()
            return np.allclose(sig1, sig2)
        except IndexError:
            # something is wrong with the strucutre composites
            # (e.g. layers were removed).
            return False
        except ValueError:
            # np.allclose does not work for some reason.
            return False

    def index(self, sl):
        """Return the index of the given StructureLayer

        Parameters
        ----------
        sl: StructureLayer or str
            The StructureLayer instance or its label
        """
        if isinstance(sl, str):
            # user passed a string and not a StructureLayer
            sl = self[sl]
        for ii, sli in enumerate(self.layers):
            if sl is sli:
                return ii
        else:
            raise KeyError(f"Could not find layer '{sl}'!")

    def remove(self, sl):
        """Remove a StructureLayer

        Parameters
        ----------
        sl: StructureLayer or str
            The StructureLayer instance or its label
        """
        if isinstance(sl, str):
            # user passed a string and not a StructureLayer
            sl = self[sl]
        self.layers.remove(sl)

    def rotate(self, dphi, origin_um=None):
        """Rotate the compoiste

        Parameters
        ----------
        dphi: float
            rotation angle [rad]
        origin_um: tuple of floats
            x-y-coordinates of the center of rotation [µm]
        """
        if origin_um is None:
            origin_um = self.position_um
        for ll in self.layers:
            ll.rotate(dphi, origin_um)

    def set_scale(self, point_um):
        """Scale to new point size in microns"""
        for ls in self.layers:
            ls.set_scale(point_um)

    def to_point_signature(self):
        """Return geometry as representative points

        The signature is centered and rotated to simplify
        comparison.

        Returns
        -------
        sig: np.ndarray of shape (N, 3)
            Point signature. The first axis contains the signature
            points of all shapes. The second axis contains
            (x, y, fact, shape_index, layer_index).
        """
        signature = []
        for ii, ll in enumerate(self.layers):
            for px, py, fac, gid in ll.to_point_signature():
                signature.append([px, py, fac, gid, ii])
        signature = np.array(signature)
        # translate the signature to zero
        signature[:, 0] -= signature[0, 0]
        signature[:, 1] -= signature[0, 1]
        # rotate the signature so that COM is on-axis
        cx = np.mean(signature[:, 0])
        cy = np.mean(signature[:, 1])
        angle = -np.arctan2(cy, cx)
        rotated = gshapes.rotate_around_point(origin=(0, 0),
                                              points=signature[:, :2],
                                              angle=angle)
        signature[:, :2] = rotated
        return signature

    def translate(self, dr_um):
        """Translate the composite by dr_um = (dx, dy) [µm]"""
        for ll in self.layers:
            ll.translate(dr_um)
