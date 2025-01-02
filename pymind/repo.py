from typing import Self

import os

from pathlib import Path

import tempfile as tmp

import zipfile as zp

from semver import Version

from pygit2 import Oid, Commit, Signature, Index, Tree
from pygit2.repository import Repository

def _pymind_initdir(
    dpath: Path | tmp.TemporaryDirectory | str
):
    """"create the template directory at dpath."""
    dpath = Path(dpath)

    if not dpath.exists():
        dpath.mkdir(parents=True, exist_ok=True)

    (dpath / Path("data")).mkdir(exist_ok=True)
    (dpath / Path("checkpoints")).mkdir(exist_ok=True)
    (dpath / Path("training.py")).touch()
    (dpath / Path("initial.state_dict")).touch()
    (dpath / Path("dataset.py")).mkdir(exist_ok=True)
    (dpath / Path("model.py")).touch()
    (dpath / Path(".vc")).mkdir(exist_ok=True)


def _pymind_extract_file_to_dpath(
    fpath: str | Path, 
    to_dpath: str | Path
) -> Path:
    """extract the mind-file to a directory"""
    pass


def _pymind_extract_file_to_tmp(
    fpath
) -> tmp.TemporaryDirectory:
    pass


def _pymind_export(dpath, fpath):
    pass


class MindDir:
    """
        Create or fetch the Mind directory instance; this 
        class is used to interact with the Mind directory.

        If the path is a mind-file, extract it to a temporary 
        directory. If the path is a mind-directory, use it 
        directly. If the path does not exist, create a new 
        mind-directory template.
    """
    _basepath: Path | tmp.TemporaryDirectory | None = None 
    _files = []
    _istmp = False
    _isnew = False

    def __init__(
        self,
        path: Path | str,
        _istmp: bool = False
    ):
        path = Path(path)

        # the path is a mind-file; extract it to a tmpdir.
        if path.isfile():
            self._basepath = _pymind_extract_file_to_tmp(path)
            self._istmp = True
        # the path is not an existing directory; 
        # initialize the directory template.
        elif not path.exists():
            self._basepath = path
            _pymind_initdir(dpath=path)
            self._isnew = True
        # the path is an existing mind-directory.
        else:
            self._basepath = Path(path)
        
        # get all the files in the directory, recursively.
        self._files = [(Path(dpath) / Path(fname)).resolve() for dpath, _, fnames in os.walk(self._basepath) for fname in fnames]


class MindObject(MindDir):
    _fpath: str | Path | None= None

    def __init__(
        self, 
        fpath: str | Path | None,
        dpath: str | Path | MindDir | None,
    ):
        """
            Create a MindObject instance.

            This is done by providing a mind-file and/or mind-directory.

            fpath can be None with an already extracted mind-directory.

            dpath can be provided without an fpath.

            both fpath and dpath can be provided to create or init the
            mind-directory AND the mind-file along with it.
        """
        # either fpath or dpath must be provided.
        assert fpath is not None or dpath is not None

        # an unextracted mind-file is provided;
        # so, extract it to a tmpdir.
        if dpath is None and fpath is not None:
            super().__init__(
                dpath=_pymind_extract_file_to_tmp(fpath)
                _istmp=False,
            )
        # an extracted mind-directory is provided 
        # without a mind-file; we will likely--at 
        # least could--create a mind-file, later.
        elif dpath is not None and fpath is not None:
            self._fpath = None

            dpath = Path(dpath)

            # the dpath does not exist; the template will
            # be created.
            if not dpath.exists():
                super.__init__(
                    dpath=dpath, 
                    _isnew=True
                )
            # the dpath exists.
            else:
                super.__init__(dpath=dpath)
        # an the mind-file and mind-directory paths are
        # provided.
        else: 
            self._fpath = Path(fpath)

            dpath
                
            super().__init__(dpath=dpath)


class Mind(Repository):
    """
        The Version-Controlled Mind. Provided as a 
        mind-file, an extracted mind-directory, or 
        a directory-path that does not yet exist--to 
        be initialized as a mind.
    """
    # this holds the mind-object instance 
    # for interacting with the mind-directory 
    # and mind-file.
    _object: MindObject = None

    def __init__(
        self, 
        mind: Path | str,
        owner_name: str,
    ):
        """
            Provide an extracted mind-directory, a
            directory-path that does not exist, 
            or a mind-file that does exist.
        """
        self.owner = owner_name
        
        mind = Path(mind)

        # mind-file provided.
        if mind.isfile():
            self._object = MindObject(fpath=mind, dpath=None)
        # mind-directory provided.
        elif mind:
            self._object = MindObject(fpath=None, dpath=mind)
            
        super().__init__(path=self._object._basepath)
        
        self.create_commit(
            reference_name="main", 
            author=Signature(
                name="Author Name",
                email=owner_name
            ), 
            commiter=Signature(
                name="Committer Name", 
                email=owner_name
            ),
            message="0.0.0",
            tree=self.TreeBuilder.write(),
        )
    
    
    def export(self, fpath: Path | str | None):
        assert fpath is not None \
            or self._object._fpath is not None
        
        _pymind_export(fpath if fpath is not None \
            else self._object._fpath, self._object._basepath)

        self._object._fpath = fpath if fpath is not None \
            else self._object._fpath
    

    def save(self, version: Version, engineer_name: str | None = None):
        """
            Save the current state of the mind 
            on the current variant.
        """
        # write all files to index.
        self.index.add_all()
        # commit the index to the head.
        oid = self.create_commit(
            reference_name=self.head.name,
            author=Signature(name="Owner", email=self.owner),
            commiter=Signature("Engineer", email=engineer_name)
            tree=self.index.write_tree(),
            parents=[self.head.target]
        )
    

    @property
    def variant(self):
        self.head
    
    
    @variant.setter
    def variant(self, name):
        ref = self.references.get(name)
        if ref is None:
            self.create_branch(
                name=name,
                commit=self.head.target
            )
        self.checkout(refname=ref.name)