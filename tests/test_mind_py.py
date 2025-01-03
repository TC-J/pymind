import copy
import inspect
import os
from pathlib import Path
import shutil
import tempfile
import pytest
import semver
from pymind.repo import Mind, MindDir, MindObject
from pymind.util import rmtree


@pytest.fixture(params=["eg0", "eg1"])
def root_path(request):
    path = Path(request.param)
    yield path
    rmtree(path)


@pytest.fixture(params=["eg0", "eg1"])
def minddir(request):
    path = Path(request.param)
    yield MindDir(path=path)
    shutil.rmtree(path)


@pytest.fixture(params=["eg0", "eg1"])
def mindobject(request, minddir):
    mo = MindObject(
        fpath=minddir.basepath.name + ".mind",
        dpath=minddir.basepath
    )
    yield mo
    mo.mind_file.unlink()


class TestMind:
    def test_minddir(self, minddir):
        # the directory exists.
        assert minddir.basepath.exists()
        # the directory has all the template files.
        assert len(minddir.files) >= 5
        ##### 
        ##### check all that all the template directories 
        ##### exist.
        #####
        assert (minddir.basepath / Path("versioning")).exists()
        assert (minddir.basepath / Path("checkpoints")).exists()
        assert (minddir.basepath / Path("data")).exists()
        path = Path(minddir.basepath.name + ".mind")
        # export the mind-dir to a mind-file.
        minddir.export(path)
        # check to see mind-file was created.
        assert path.exists() and path.is_file()
        # delete the mind-file.
        path.unlink()
    

    def test_minddir_from_empty_dir(self):
        path = Path("eg_init.d")
        mdir = MindDir(path, init=True)
        assert len(mdir.files) >= 5
        shutil.rmtree(path)


    def test_mindobject(self, mindobject):
        # the directory exists.
        assert Path(mindobject.basepath).exists()
        # the template files exist.
        assert len(mindobject.files) >= 5
        # the mind-file exists.
        assert mindobject.mind_file.exists()
        #####
        ##### check that the directory exports and that
        ##### a new, equivalent mind-dir can be extracted.
        #####
        new_mf_path = Path("new_" + mindobject.basepath.name + ".mind")
        mindobject.export(new_mf_path)
        new_mo = MindObject(fpath=new_mf_path)
        assert all(
            a == b for a, b in zip(
                [p.name for p in mindobject.files], 
                [p.name for p in new_mo.files]
            )
        )
        new_mf_path.unlink()


    def test_mind(self, root_path: Path):
        md = MindDir(path=root_path)

        mind = Mind(root_path, owner="TC-J")
        # check latest version.
        assert mind.latest.__str__() == "0.0.0"

        # check basepath.
        assert mind.basepath == root_path
        assert mind.basepath.exists()

        # check template files were created.
        assert len(mind.files) >= 5
        ### write to model.py and save it.
        model_fpath = root_path / Path("model.py")

        model_fpath.write_text("a")
        mind.save_prerelease("TC-J")
        assert mind.latest == "0.0.0-rc.1"

        model_fpath.write_text("b")
        mind.save_build("TC-J")
        assert mind.latest == "0.0.0-rc.1+build.1"

        model_fpath.write_text("c")
        mind.save_patch("TC-J")
        assert mind.latest == "0.0.1"

        model_fpath.write_text("d")
        mind.save_minor("TC-J")
        assert mind.latest == "0.1.0"

        model_fpath.write_text("e")
        mind.save_major("TC-J")
        assert mind.latest == "1.0.0"
