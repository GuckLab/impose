from collections import OrderedDict

from bmlab.session import Session, get_valid_source, get_session_file_path,\
    BmlabInvalidFileError, is_session_file
from bmlab.controllers import EvaluationController
import h5py
import numpy as np
import errno

from ..util import hashfile, hashobj


def load_h5(path):
    """Load .h5 files exported from BrillouinEvaluation (legacy Matlab)
     or BrillouinAcquisition/bmlab

    Please see :func:`impose.formats.load` for more information.
    """
    try:
        # Load data with bmlab
        session = Session.get_instance()
        session.set_file(path)
        evc = EvaluationController()

        rep_keys = session.file.repetition_keys()

        channels = OrderedDict()
        for rep_key in rep_keys:
            session.set_current_repetition(rep_key)
            keys = session.evaluation_model().get_parameter_keys()

            # If the file contains multiple repetitions, we
            # prepend the repetition key
            key_prefix = ''
            if len(rep_keys) > 1:
                key_prefix = 'rep-' + rep_key + '_'
            for key in keys:
                data, positions, dimensionality, labels =\
                    evc.get_data(key)
                channels[key_prefix + key] = data

        session.clear()

        # create a unique signature for this dataset
        p1 = get_valid_source(path)
        p2 = get_session_file_path(p1)
        h1 = hashfile(p1, blocksize=65536, count=1)
        # bmlab can open source data files without
        # associated session files, so we need to check
        # for this case explicitly.
        if is_session_file(p2):
            h2 = hashfile(p2, blocksize=65536, count=1)
        else:
            # The provided data is all-NaN in this case,
            # which does not help much for Impose.
            # So we raise an error for now. This might change,
            # once bmlab can also provide
            # brightfield or fluorescence images.
            raise FileNotFoundError(
                errno.ENOENT,
                f"The bmlab session file {p2} is missing.",
                p2
            )
        signature = hashobj((h1, h2))

        chan = sorted(channels)
        if len(chan) > 0:
            meta = {
                "pixel size x": calc_pixel_size(positions, 0),
                "pixel size y": calc_pixel_size(positions, 1),
                "pixel size z": calc_pixel_size(positions, 2),
                "shape": channels[chan[0]].shape,
                "signature": signature,
            }
    except BmlabInvalidFileError as err:
        try:
            # Fall-back to load BrillouinEvaluation exported h5 file
            with h5py.File(path, "r") as h5:
                # Data
                chkeys = sorted(h5.keys())
                # find axis order
                k0 = chkeys[0]
                # sometimes this is str and sometimes bytes
                axes = np.string_(h5[k0].attrs["axisOrder"]).decode("utf-8")
                xid = axes.index("X")
                yid = axes.index("Y")
                zid = axes.index("Z")

                channels = OrderedDict()
                for chan in chkeys:
                    dslice = h5[chan][:]
                    if len(dslice.shape) != 3:
                        raise ValueError(
                            "Invalid number of dimensions in "
                            "'{}'. ".format(path)
                            + "Please verify the original Brillouin dataset.")
                    channels[chan] = dslice.transpose(xid, yid, zid)

                # Metadata
                meta = {
                    "pixel size x": np.array(h5.attrs["scaleX"]).item(),
                    "pixel size y": np.array(h5.attrs["scaleY"]).item(),
                    "pixel size z": np.array(h5.attrs["scaleZ"]).item(),
                    "shape": channels[chkeys[0]].shape,
                }
        # If we get a ValueError from loading the legacy Matlab file,
        # we pass it on,
        # since we then at least know it was supposed to be a Matlab file.
        except ValueError as e:
            raise e
        # We re-raise the exception from bmlab here,
        # because the Matlab import is just a legacy option
        # and we likely wanted to import a file from BMicro/bmlab
        # (which failed).
        except BaseException:
            raise err

    return channels, meta


def calc_pixel_size(positions, axis):
    s = [0, 0, 0]
    s[axis] = slice(0, 2, 1)
    if positions[axis].shape[axis] > 1:
        return abs(np.diff(positions[axis][tuple(s)]))[0]
    return float('nan')
