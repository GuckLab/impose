import pathlib
import shutil
import tempfile

import numpy as np
import pytest

import impose.data
import impose.structure
from impose import session


data_path = pathlib.Path(__file__).parent / "data"


def test_session_base():
    """Open a test session and extract data"""
    path = data_path / "brillouin.impose-session"
    ses = session.ImposeSession()
    ses.load(path)

    assert len(ses.scs) == 1
    cds = ses.collect.data_sources[0]
    assert cds.shape == (1, 51, 71)
    assert cds.metadata["stack"]["channel hues"]["intensity"] == 63
    assert ses.scs.composites[0][0].label == "central canal"

    # simple data extraction
    e1 = ses.scs.composites[0].extract_data(cds)
    assert np.allclose(e1["central canal"]["BrillouinShift"].mean(),
                       43.84349249591004,
                       atol=1e-14, rtol=0)

    # we only rotated the central canal in that session in the colocalization
    l1 = ses.scs.composites[0]["central canal"]
    l2 = ses.colocalize.strucure_composites_manual[0]["central canal"]
    # get the shape (Circle)
    s1 = l1.geometry[0][0]
    s2 = l2.geometry[0][0]
    assert np.allclose(s1.x, s2.x, rtol=0, atol=1e-13)
    assert np.allclose(s1.y, s2.y, rtol=0, atol=1e-13)
    assert np.allclose(s1.r, s2.r, rtol=0, atol=1e-13)


def test_session_clear():
    """Clear a session"""
    path = data_path / "brillouin.impose-session"
    ses = session.ImposeSession()
    ses.load(path)

    # clear it
    ses.clear()

    # assert that it is empty
    assert len(ses.scs) == 0
    assert len(ses.collect.paths) == 0
    assert len(ses.collect.data_sources) == 0
    assert ses.collect.scs is ses.scs
    assert len(ses.colocalize.paths) == 0
    assert len(ses.colocalize.data_sources) == 0
    assert len(ses.colocalize.strucure_composites_manual) == 0
    assert ses.colocalize.scs is ses.scs


def test_session_extract_mask_cutout_pattern():
    path = data_path / "brillouin_cutout.impose-session"
    ses = session.ImposeSession()
    ses.load(path)

    # render the first structure composite for collect
    ds = ses.collect.data_sources[0]
    sc_collect = ses.scs[0]
    data_collect = sc_collect.extract_data(ds)
    cutout_collect = data_collect["circ-square-cutout"]["BrillouinShift"]
    assert cutout_collect[0] == 44.313336748020845
    assert np.allclose(np.mean(cutout_collect), 44.334714982678264,
                       atol=1e-14, rtol=0)

    # render the first structure composite for colocalize
    sc_coloc = ses.colocalize.strucure_composites_manual[0]
    data_coloc = sc_coloc.extract_data(ds)
    cutout_coloc = data_coloc["circ-square-cutout"]["BrillouinShift"]
    assert cutout_coloc[0] == 44.78100818790851
    assert np.allclose(np.mean(cutout_coloc), 44.55154338598099,
                       atol=1e-14, rtol=0)


def test_session_find_file_signature():
    tmp = pathlib.Path(tempfile.mkdtemp("impose_test"))
    path_d = tmp / "brillouin.h5"
    path_s = tmp / "test.impose-session"
    shutil.copy2(data_path / "brillouin.h5", path_d)
    ses = session.ImposeSession()
    ses.collect.append(path_d)
    ses.save(path_s)
    path_d.unlink()
    # try to load the session
    ses2 = session.ImposeSession()
    with pytest.raises(FileNotFoundError,
                       match="sig '627ccaa50d2b7447ebf64796e10f8794'"):
        ses2.load(path_s)
    # adding the search path to a directory with the original file should work
    ses2.load(path_s, search_paths=[data_path])


def test_session_find_file_signature_recursive_1():
    tmp1 = pathlib.Path(tempfile.mkdtemp("impose_test"))
    tmp2 = pathlib.Path(tempfile.mkdtemp("impose_test"))
    path_d = tmp1 / "brillouin.h5"
    path_s = tmp2 / "test.impose-session"
    shutil.copy2(data_path / "brillouin.h5", path_d)
    ses = session.ImposeSession()
    ses.collect.append(path_d)
    ses.save(path_s)
    # Don't delete the file, but put it in a subdirectory, which will
    # be searched recursively.
    newdir = tmp1 / "a" / "nested" / "directory"
    newdir.mkdir(parents=True)
    path_d.rename(newdir / path_d.name)
    # loading the session will work, because `tmp1` is where the original
    # file is located and that is added to the search path automatically.
    ses2 = session.ImposeSession()
    ses2.load(path_s)


def test_session_find_file_signature_recursive_2():
    tmp1 = pathlib.Path(tempfile.mkdtemp("impose_test"))
    tmp2 = pathlib.Path(tempfile.mkdtemp("impose_test"))
    path_d = tmp1 / "brillouin.h5"
    path_s = tmp2 / "test.impose-session"
    shutil.copy2(data_path / "brillouin.h5", path_d)
    ses = session.ImposeSession()
    ses.collect.append(path_d)
    ses.save(path_s)
    # This time put it in a subdirectory where the session file is.
    newdir = tmp2 / "a" / "nested" / "directory"
    newdir.mkdir(parents=True)
    path_d.rename(newdir / path_d.name)
    # loading the session will work, because `tmp2` is where the session
    # file is located and that is added to the search path automatically.
    ses2 = session.ImposeSession()
    ses2.load(path_s)


@pytest.mark.parametrize("filename", list(data_path.glob("*.impose-session")))
def test_session_load_all(filename):
    path = data_path / filename
    ses = session.ImposeSession()
    ses.load(path)


def test_session_populate_simple_collect():
    """Create a new session from scratch and populate collect"""
    path = data_path / "brillouin.h5"
    ses = session.ImposeSession()
    ses.collect.append(path)
    assert ses.collect.paths[0].samefile(path)
    assert len(ses.collect.paths) == 1
    assert ses.collect.data_sources[0].path.samefile(path)
    assert len(ses.collect.data_sources) == 1
    assert len(ses.scs) == 1
    assert len(ses.scs[0]) == 0


def test_session_populate_simple_colocalize():
    """Create a new session from scratch and populate colocalize"""
    path = data_path / "brillouin.h5"
    ses = session.ImposeSession()
    ses.collect.append(path)
    ses.colocalize.append(path)
    assert ses.colocalize.paths[0].samefile(path)
    assert len(ses.colocalize.paths) == 1
    assert ses.colocalize.data_sources[0].path.samefile(path)
    assert len(ses.colocalize.data_sources) == 1
    assert len(ses.scs) == 1
    assert len(ses.scs[0]) == 0


def test_session_save():
    """Save and load a session"""
    path = data_path / "brillouin.impose-session"
    ses1 = session.ImposeSession()
    ses1.load(path)
    # save it
    psav = pathlib.Path(tempfile.mkdtemp("impose_test")) / "tst.impose-session"
    ses1.save(psav)
    # load it again
    ses2 = session.ImposeSession()
    ses2.load(psav)
    # check that states match
    assert ses1 == ses2


def test_session_signature_fail():
    """Check whether wrong signatures leads to FileNotFoundError"""
    path = data_path / "brillouin.impose-session"
    text = path.read_text()
    tp = pathlib.Path(tempfile.mkdtemp("impose_test")) / "tst.impose-session"
    tp.write_text(text.replace("627ccaa50d2b7447ebf64796e10f8794", "invalid"))

    ses1 = session.ImposeSession()
    with pytest.raises(
            FileNotFoundError,
            match=r"Could not find file 'brillouin.h5' \(sig 'invalid'\)!"):
        ses1.load(tp)


def test_session_workflow():
    """Create a new session from scratch and extract some data"""
    path = data_path / "brillouin.h5"
    ses = session.ImposeSession()
    # set up data source
    ds = impose.data.DataSource(path)
    point_um = ds.get_pixel_size()[0]  # impose convention
    # set up collect
    rect = impose.geometry.shapes.Rectangle(x=30,
                                            y=20,
                                            a=10,
                                            b=5,
                                            phi=0,
                                            point_um=point_um)
    sl = impose.structure.StructureLayer(label="peter",
                                         point_um=point_um,
                                         geometry=[(rect, 1)]
                                         )
    sc = impose.structure.StructureComposite()
    sc.append(sl)
    ses.collect.append(path, structure_composite=sc)

    # setup colocalize
    ses.colocalize.append(path, structure_composite=None)
    assert ses.colocalize.strucure_composites_manual[0] == sc

    # add something to collect (StructureCompositeStack)
    rect2 = impose.geometry.shapes.Rectangle(x=20,
                                             y=10,
                                             a=8,
                                             b=10,
                                             phi=0,
                                             point_um=point_um)
    sl2 = impose.structure.StructureLayer(label="hans",
                                          point_um=point_um,
                                          geometry=[(rect2, -2)]
                                          )
    sc.append(sl2)

    # now update colocalize
    assert ses.colocalize.strucure_composites_manual[0] != sc
    ses.colocalize.update_composite_structures()
    assert ses.colocalize.strucure_composites_manual[0] == sc

    # save the session
    psav = pathlib.Path(tempfile.mkdtemp("impose_test")) / "tst.impose-session"
    ses.save(psav)

    # load it again
    ses2 = session.ImposeSession()
    ses2.load(psav)

    # check that states match
    assert ses == ses2
