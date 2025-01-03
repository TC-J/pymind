from typing import Self
import os
from pathlib import Path
import tempfile as tmp
import zipfile as zp
import pygit2
from semver import Version
from pygit2 import Oid, Commit, Signature, Index, Tree
from pygit2.repository import Repository
from pymind.util import ensure_path

def mind_initdir(
    dpath: Path | tmp.TemporaryDirectory | str
):
    """"create the template directory at dpath."""
    dpath = Path(dpath)

    if not dpath.exists():
        dpath.mkdir(parents=True, exist_ok=True)

    (dpath / Path("data")).mkdir(exist_ok=True)
    (dpath / Path("checkpoints")).mkdir(exist_ok=True)
    (dpath / Path("hyperparameters.yaml")).touch(exist_ok=True)
    (dpath / Path("training.py")).touch(exist_ok=True)
    (dpath / Path("initial.state_dict")).touch(exist_ok=True)
    (dpath / Path("dataset.py")).touch(exist_ok=True)
    (dpath / Path("model.py")).touch(exist_ok=True)
    (dpath / Path("versioning")).mkdir(exist_ok=True)

def mind_extract_file_to_dpath(
    fpath: str | Path, 
    to_dpath: str | Path
) -> Path:
    """extract the mind-file to a directory"""
    to_dpath = Path(to_dpath)
    to_dpath.mkdir(parents=True, exist_ok=True)
    with zp.ZipFile(fpath, 'r') as zip_ref:
        zip_ref.extractall(to_dpath)

def mind_extract_file_to_tmp(
    fpath
) -> tmp.TemporaryDirectory:
    to_dpath = tmp.TemporaryDirectory()
    mind_extract_file_to_dpath(
        fpath=fpath, 
        to_dpath=ensure_path(to_dpath)
    )
    return to_dpath

def mind_export(
    dpath: str | Path,
    fpath: str | Path
):
    dpath = Path(dpath)
    with zp.ZipFile(
        file=fpath, 
        mode='w', 
        compresslevel=9
    ) as zip_ref:
        for file in dpath.rglob('*'):
            zip_ref.write(
                filename=file,
                arcname=file.relative_to(dpath)
            )

def mind_get_all_tags(repo: Repository):
    tags = [ref for ref in repo.listall_references() if ref.startswith('refs/tags/')]
    tags.sort(reverse=True)
    return tags

def mind_commit(repo, refname, owner, engineer, msg, parents):
    repo.index.add_all()
    repo.index.write()
    return repo.create_commit(
        refname,
        pygit2.Signature("Owner", owner),
        pygit2.Signature("Engineer", engineer),
        msg,
        repo.index.write_tree(),
        parents
    )

def mind_version_tag(repo, version, oid, owner):
    repo.create_tag(
        version,
        oid,
        pygit2.GIT_OBJECT_COMMIT,
        Signature("Owner", owner),
        "Version " + version
    )

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
    _istmp = False

    def __init__(
        self,
        path: tmp.TemporaryDirectory | Path | str,
        init: bool = False,
        _istmp: bool = False
    ):
        path = ensure_path(path)

        # the path is a mind-file; extract it to a tmpdir.
        if path.is_file():
            self._basepath = \
                mind_extract_file_to_tmp(path)

            self._istmp = True
        # the path is not an existing directory; 
        # initialize the directory template.
        elif not path.exists():
            self._basepath = path
            mind_initdir(dpath=path)
        # the path is an existing mind-directory.
        else:
            if init:
                mind_initdir(dpath=path)
            self._basepath = Path(path)
        
    
    def export(self, fpath):
        mind_export(
            dpath=self._basepath,
            fpath=fpath
        )

    def __del__(self):
        if self._istmp:
            self._basepath.cleanup()

    @property
    def files(self):
        return [
            (Path(dpath) / Path(fname)).resolve() \
                for dpath, _, fnames \
                in os.walk(self.basepath) \
                for fname in fnames
        ]

    @property
    def basepath(self):
        return \
            Path(self._basepath) \
            if not isinstance(
                self._basepath,
                tmp.TemporaryDirectory
            ) else Path(self._basepath.name)

class MindObject(MindDir):
    """
        This is an object for managing the mind. The
        object is an extracted mind-directory and/or
        mind-file.

    """
    _fpath: str | Path | None= None

    def __init__(
        self, 
        fpath: str | Path | None = None,
        dpath: str | Path | None = None
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

        fpath = Path(fpath) if fpath is not None else fpath

        dpath = Path(dpath) if dpath is not None else dpath

        # given: fpath.
        # an unextracted mind-file is provided;
        # so, extract it to a tmpdir.
        if dpath is None and fpath is not None:
            super().__init__(
                path=mind_extract_file_to_tmp(fpath),
                _istmp=False
            )
        # given: dpath, fpath
        # an extracted mind-directory is provided 
        # without a mind-file; we will likely--at 
        # least could--create a mind-file, later.
        elif dpath is not None and fpath is not None:
            self._fpath = fpath

            dpath = Path(dpath)

            # the dpath does not exist; the template will
            # be created.
            if not dpath.exists():
                super().__init__(
                    path=dpath, 
                    _isnew=True
                )
            # the dpath exists.
            else:
                super().__init__(path=dpath)
            
            # the fpath does not exist; create a
            # mind-file.
            if not fpath.exists():
                self.export(fpath=fpath)
        # given: dpath.
        # an extracted mind-file is provided; use
        # it directly.
        else:
            super().__init__(path=dpath)
    
    @property
    def mind_file(self):
        return self._fpath \
            if not isinstance(self._fpath, tmp.TemporaryDirectory) \
            else Path(self._fpath.name)

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
        owner: str,
    ):
        """
            Provide an extracted mind-directory, a
            directory-path that does not exist, 
            or a mind-file that does exist.
        """
        self.owner = owner
        
        mind = Path(mind)

        # mind-file provided.
        if mind.is_file():
            self._object = MindObject(fpath=mind, dpath=None)
        # mind-directory provided.
        else:
            self._object = MindObject(fpath=None, dpath=mind)
        
        vcpath = self._object.basepath / Path("versioning")

        if not (vcpath / Path("objects")).exists():
            repo = pygit2.init_repository(
                path=vcpath, 
                workdir_path="../",
                flags=pygit2.GIT_REPOSITORY_INIT_NO_DOTGIT_DIR\
                    | pygit2.GIT_REPOSITORY_INIT_MKDIR
            )

            mind_commit(
                repo=repo,
                refname="HEAD",
                owner=self.owner,
                engineer=self.owner,
                msg="Base Template",
                parents=[]
            )

        super().__init__(path=vcpath, flags=pygit2.GIT_REPOSITORY_OPEN_NO_DOTGIT)
            
        mind_version_tag(
            repo=self,
            version="0.0.0",
            oid=self.head.target,
            owner=self.owner
        )
    
    def export(self, fpath: Path | str | None):
        assert fpath is not None \
            or self._object._fpath is not None
        
        mind_export(fpath if fpath is not None \
            else self._object._fpath, self._object._basepath)

        self._object._fpath = fpath if fpath is not None \
            else self._object._fpath
    
    def save(self, version: Version, engineer: str | None = None):
        """
            Save the current state of the mind 
            on the current variant.
        """
        # commit the index to the head.
        commit_oid = mind_commit(
            repo=self,
            refname=self.head.name,
            engineer=engineer,
            msg=f"Version {version}",
            parents=[self.head.target]
        )

        # tag the commit with the version.
        mind_version_tag(
            repo=self,
            version=version,
            oid=commit_oid,
        )
        
    def save_build(self, engineer: str | None = None):
        self.save(
            version=self.latest.bump_build(),
            engineer=engineer
        )

    def save_prelease(self, engineer: str | None = None):
        self.save(
            version=self.latest.bump_prerelease(),
            engineer=engineer
        )
    
    def save_patch(self, engineer: str | None = None):
        self.save(
            version=self.latest.bump_patch(),
            engineer=engineer
        )

    def save_minor(self, engineer: str | None = None):
        self.save(
            version=self.latest.bump_patch(),
            engineer=engineer
        )

    def save_major(self, engineer: str | None = None):
        self.save(
            version=self.latest.bump_major(),
            engineer=engineer
        )
    
    @property
    def latest(self) -> Version:
        return Version.parse(mind_get_all_tags(self)[0])


    @property
    def mind_object(self):
        return self._object

    @property
    def mind_file(self):
        return self.object.mind_file

    @property
    def basepath(self):
        return self.object.basepath
    
    @property
    def files(self):
        return self.object.files
    
    
    @property
    def tags(self) -> list[str]:

        return mind_get_all_tags(self)
