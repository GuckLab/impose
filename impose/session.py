import json
import pathlib
import warnings

import numpy as np

from .structure import StructureComposite, StructureCompositeStack
from .data import DataSource
from .formats import get_signature
from .util import equal_states
from ._version import version


class ImposeDataFileNotFoundError(FileNotFoundError):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(ImposeDataFileNotFoundError, self).__init__(*args, **kwargs)


class ImposeSessionSchemeCollect:
    """Holds all session information about collection"""

    def __init__(self, structure_composite_stack):
        """

        Parameters
        ----------
        structure_composite_stack: impose.structure.StrucureCompositeStack
            Empty structure composite stack
        """
        #: All open :class:`impose.data.DataSource` instances
        self.data_sources = []
        #: All :class:`impose.structure.StrucureComposite` instances
        #: in one :class:`impose.structure.StrucureCompositeStack`
        self.scs = structure_composite_stack

    def __getstate__(self):
        """Serialize the current state of the session"""
        st_ds = [ds.__getstate__() for ds in self.data_sources]
        state = {
            "data sources": st_ds,
        }
        return state

    def __setstate__(self, state):
        """Deserialize a state and apply it to this session"""
        self.data_sources.clear()
        for ss in state["data sources"]:
            ds = DataSource(ss["path"])
            ds.__setstate__(ss)
            self.data_sources.append(ds)

    @property
    def paths(self):
        """All open paths (corresponding to `self.data_sources`)"""
        return [ds.path for ds in self.data_sources]

    def append(self, path, data_source=None, structure_composite=None):
        """Append a dataset to the session

        Parameters
        ----------
        path: str or pathlib.Path
            Path to the data file
        data_source: impose.data.DataSource
            If not set, then a new `DataSource` is created using
            `path`.
        structure_composite: impose.structure.StructureComposite
            `StructureComposite` that will be added to `self.scs`.
            If not set, then an empty `StructureComposite` is
            created.
        """
        if data_source is None:
            data_source = DataSource(path)
        if structure_composite is None:
            structure_composite = StructureComposite()

        # Make sure we don't have any duplicate signatures
        for ds in self.data_sources:
            if ds.signature == data_source.signature:
                warnings.warn(
                    f"Prevented loading a duplicate dataset: {path}")
                break
        else:
            # We don't have this dataset already - append it
            self.data_sources.append(data_source)
            self.scs.append(structure_composite)

    def clear(self):
        """Clear the session"""
        self.data_sources.clear()
        self.scs.clear()


class ImposeSessionSchemeColocalize:
    """Holds all session information about colocalization"""

    def __init__(self, structure_composite_stack):
        """

        Parameters
        ----------
        structure_composite_stack: impose.structure.StrucureCompositeStack
            Empty structure composite stack
        """
        #: Input data images
        self.data_sources = []
        self.scs = structure_composite_stack
        self.strucure_composites_manual = []

    def __getstate__(self):
        """Serialize the current state of the session"""
        st_sc_man = [sc.__getstate__()
                     for sc in self.strucure_composites_manual]
        st_ds = [ds.__getstate__() for ds in self.data_sources]
        state = {
            "data sources": st_ds,
            "structure composites manual": st_sc_man,
        }
        return state

    def __setstate__(self, state):
        """Deserialize a state and apply it to this session"""
        self.clear()
        for ss in state["data sources"]:
            ds = DataSource(ss["path"])
            ds.__setstate__(ss)
            self.data_sources.append(ds)
        for sscm in state["structure composites manual"]:
            sc = StructureComposite()
            sc.__setstate__(sscm)
            self.strucure_composites_manual.append(sc)

    @property
    def paths(self):
        """All open paths (corresponding to `self.data_sources`)"""
        return [ds.path for ds in self.data_sources]

    def append(self, path, data_source=None, structure_composite=None):
        """Append a dataset to the session

        Parameters
        ----------
        path: str or pathlib.Path
            Path to the data file
        data_source: impose.data.DataSource
            If not set, then a new `DataSource` is created using
            `path`.
        structure_composite: impose.structure.StructureComposite
            If not set, then a mean `StructureComposite` is
            created from `self.scs`, the StructureCompositeStack
            passed to :func:`ImposeSessionSchemeColocalize.__init__`.
        """
        if data_source is None:
            data_source = DataSource(path)
        if structure_composite is None:
            structure_composite = self.scs.get_mean()
        structure_composite.set_scale(point_um=data_source.get_pixel_size()[0])
        self.data_sources.append(data_source)
        self.strucure_composites_manual.append(structure_composite)

    def clear(self):
        """Clear the session"""
        self.data_sources.clear()
        self.strucure_composites_manual.clear()

    def update_composite_structures(self):
        """Update all composite structures

        This function should be called whenever self.scs changes.
        """
        if self.data_sources:
            sc = self.scs.get_mean()
            # Check whether the structure changed and we have to reset
            # the current structures.
            if self.strucure_composites_manual:
                sc1 = self.strucure_composites_manual[0]
                if not sc.geometry_identical_to(sc1):
                    self.strucure_composites_manual.clear()
            for ii, ds in enumerate(self.data_sources):
                if ii >= len(self.strucure_composites_manual):
                    sci = sc.copy()
                    # x axis defines point size
                    sci.set_scale(point_um=ds.get_pixel_size()[0])
                    self.strucure_composites_manual.append(sci)
                else:
                    sci = self.strucure_composites_manual[ii]
                # make sure that color and label are correct
                # (this is not checked in `geometry_identical_to`
                for jj in range(len(sc)):
                    sci[jj].color = sc[jj].color
                    sci.change_layer_label(
                        sci[jj].label, sc[jj].label, force=True)


class ImposeSession:
    """Holds all session information about an impose session"""

    def __init__(self):
        #: :class:`impose.structure.StructureCompositeStack`;
        #: contains all the user-defined instances of
        #: :class:`impose.structure.StructureComposite`.
        #: It is managed in
        # :const:`impose.session.ImposeSession.collect`.
        self.scs = StructureCompositeStack()
        #: :class:`impose.session.ImposeSessionSchemeCollect`;
        #: contains relevant information about user-defined
        #: datasets and -generated `StructureComposite`s.
        self.collect = ImposeSessionSchemeCollect(self.scs)
        #: :class:`impose.session.ImposeSessionSchemeColocalize`;
        #: contains information about applying the stack in
        #: :const:`impose.session.ImposeSession.scs` to new
        #: data.
        self.colocalize = ImposeSessionSchemeColocalize(self.scs)

    def __eq__(self, other):
        return equal_states(self.__getstate__(), other.__getstate__())

    def __getstate__(self):
        """Serialize the current state of the session"""
        state = {
            "structure composite stack": self.scs.__getstate__(),
            "collection": self.collect.__getstate__(),
            "colocalization": self.colocalize.__getstate__(),
        }
        return state

    def __setstate__(self, state):
        """Deserialize a state and apply it to this session"""
        self.scs.__setstate__(state["structure composite stack"])
        self.collect.__setstate__(state["collection"])
        self.colocalize.__setstate__(state["colocalization"])

    @staticmethod
    def check_json_paths(odict, search_paths=None):
        """Try to retrieve non-existent paths in a session"""
        if search_paths is None:
            sps = []
        else:
            sps = [pathlib.Path(sp) for sp in search_paths]
        if "path" in odict:
            # Path in a DataSource state
            sig = odict["metadata"].get("signature")
            path = pathlib.Path(odict["path"])
            odict["path"] = ImposeSession.find_file(
                name=path.name,
                search_paths=[path.parent] + sps,
                signature=sig)
        return odict

    @staticmethod
    def find_file(name, search_paths, signature=None):
        """Find a data file

        Parameters
        ----------
        name: str or pathlib.Path
            The original path or file name
        search_paths: list of pathlib.Path
            Directories where to search for `path`
        signature: str
            Optional data file signature (defined in the `formats`
            submodule)

        Returns
        -------
        new_path: pathlib.Path
            The actual path
        """
        for sp in search_paths:
            for pp in sp.rglob(name):
                if signature is None:
                    # signature check not possible
                    return pp
                elif signature == get_signature(pp):
                    # only return signature if we have a match
                    return pp
        else:
            raise ImposeDataFileNotFoundError(
                name,
                "Could not find file '{}'".format(name)
                + (f" (sig '{signature}')" if signature is not None else "")
                + "!"
            )

    def clear(self):
        """Clear the session"""
        self.scs.clear()
        self.collect.clear()
        self.colocalize.clear()

    def load(self, path, search_paths=None):
        """Replace the current session with a session stored on disk"""
        if search_paths is None:
            search_paths = []
        path = pathlib.Path(path)
        search_paths.append(path.parent)
        with pathlib.Path(path).open("r") as fd:
            state = json.load(
                fd,
                object_hook=lambda x:
                    ImposeSession.check_json_paths(x, search_paths))
            self.__setstate__(state)

    def save(self, path):
        """Save the current session to a file on disk"""
        with pathlib.Path(path).open("w") as fd:
            state = self.__getstate__()
            state["impose"] = {"version": version}
            json.dump(state, fd,
                      ensure_ascii=False,
                      allow_nan=True,
                      indent=1,
                      cls=JSONEncoderFromNumpy,
                      )


class JSONEncoderFromNumpy(json.JSONEncoder):
    """JSONEncoder that handles numpy dtypes"""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return super(JSONEncoderFromNumpy, self).default(obj)
