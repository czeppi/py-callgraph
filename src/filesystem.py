from pathlib import Path


class Dir:

    @property
    def name(self):
        raise Exception('abstract class')
        
    @property
    def parent(self):
        raise Exception('abstract class')

    def iter_children(self):
        raise Exception('abstract class')

    def iter_subdirs(self):
        raise Exception('abstract class')
            
    def iter_files(self):
        raise Exception('abstract class')
        
    def get_subdir(self, dname):
        raise Exception('abstract class')
        
    def get_file(self, fname):
        raise Exception('abstract class')
        
    def has_subdir(self, dname):
        raise Exception('abstract class')
        
    def has_file(self, fname):
        raise Exception('abstract class')
        
     
class File:

    def __str__(self) -> str:
        raise Exception('abstract class')

    @property
    def name(self):
        raise Exception('abstract class')

    @property
    def stem(self):
        raise Exception('abstract class')

    @property
    def suffix(self):
        raise Exception('abstract class')

    @property
    def dir_(self):
        raise Exception('abstract class')

    @property
    def mtime(self):
        raise Exception('abstract class')

    @property
    def size(self):
        raise Exception('abstract class')

    def read(self):
        raise Exception('abstract class')


class VirtualDir(Dir):

    def __init__(self, name, parent_dir):
        self._name = name
        self._parent_dir = parent_dir
        self._sub_dirs = {}
        self._files = {}
        
    def __str__(self):
        if self._parent_dir:
            return self._parent_dir + '/' + self._name
        else:
            return self._name
        
    def add_subdir(self, subdir_name):     
        if subdir_name in self._sub_dirs:
            raise Exception('{} already exists in {}'.format(subdir_name, self._name))
        new_subdir = VirtualDir(subdir_name, self)
        self._sub_dirs[subdir_name] = new_subdir
        return new_subdir
            
    def add_file(self, file_name, file_buf):     
        if file_name in self._files:
            raise Exception('{} already exists in {}'.format(file_name, self._name))
        new_file = VirtualFile(file_name, self, file_buf)
        self._files[file_name] = new_file
        return new_file
        
    @property
    def name(self):
        return self._name
        
    @property
    def parent_dir(self):
        return self._parent_dir
        
    def iter_children(self):
        yield from self._sub_dirs.values()
        yield from self._files.values()

    def iter_subdirs(self):
        yield from self._sub_dirs.values()
            
    def iter_files(self):
        yield from self._files.values()
        
    def get_subdir(self, dname):
        return self._sub_dirs.get(dname, None)
        
    def get_file(self, fname):
        return self._files.get(fname, None)
        
    def has_subdir(self, dname):
        return dname in self._sub_dirs
        
    def has_file(self, fname):
        return fname in self._files

        
class VirtualFile(File):

    def __init__(self, name, dir_, file_buf):
        self._name = name
        self._dir = dir_
        self._buf = None
        self._mtime = None
        self._size = len(file_buf)
        self._buf = file_buf
        
    def __str__(self):
        return str(self._dir) + '/' + self._name
        
    @property
    def name(self):
        return self._name
        
    @property
    def stem(self):
        return self._name.split('.')[0]
        
    @property
    def suffix(self):
        return self._name.split('.')[-1]

    @property
    def mtime(self):
        return self._mtime

    @property
    def size(self):
        return self._size

    @property
    def dir_(self):
        return self._dir
        
    def read(self):
        return self._buf
        
        
class RegularDir(Dir):

    def __init__(self, dpath):
        self._dpath = dpath
        
    def __str__(self):
        return str(self._dpath)
        
    @property
    def name(self):
        return self._dpath.name

    def iter_children(self):
        for x in self._dpath.iterdir():
            if x.is_file():
                yield RegularFile(x)
            elif x.is_dir():
                yield RegularDir(x)

    def iter_subdirs(self):
        for x in self._dpath.iterdir():
            if x.is_dir():
                yield RegularDir(x)
            
    def iter_files(self):
        for x in self._dpath.iterdir():
            if x.is_file():
                yield RegularFile(x)
        
    def get_subdir(self, subdir_name):
        sub_dpath = self._dpath / subdir_name
        if sub_dpath.exists() and sub_dpath.is_dir():
            return RegularDir(sub_dpath)
        
    def get_file(self, file_name):
        fpath = self._dpath / file_name
        if fpath.exists() and fpath.is_file():
            return RegularFile(fpath)
        
    def has_subdir(self, subdir_name):
        subdir_path = self._dpath / subdir_name
        return subdir_path.exists()
        
    def has_file(self, file_name):
        file_path = self._dpath / file_name
        return file_path.exists()
        
        
class RegularFile(File):
    
    def __init__(self, fpath: Path):
        self._fpath = fpath.absolute()

    def __str__(self):
        return str(self._dpath)
                
    @property
    def name(self):
        return self._fpath.name
        
    @property
    def stem(self):
        return self._fpath.stem
        
    @property
    def suffix(self):
        return self._fpath.suffix

    @property
    def mtime(self):
        return self._fpath.stat().st_mtime
        
    @property
    def size(self):
        return self._fpath.stat().st_size

    @property
    def dir_(self):
        return RegularDir(self._fpath.parent)

    def read(self):
        with self._fpath.open('r') as fh:
            self._buf = fh.read()
        return self._buf
        
        
# class DirComparer:

    # def __init__(self, old_dir, new_dir):
        # self._old_dir = old_dir
        # self._new_dir = new_dir
        
    # def iter_new_subdirs(self):
        # for x in self._new_dir.iter_subdirs():
            # if not self._old_dir.has_subdir(x.name):
                # yield x
                
    # def iter_removed_subdirs(self):
        # pass
        
    # def iter_common_subdirs(self):
        # pass
        
    # def iter_new_files(self):
        # pass
        
    # def iter_removed_files(self):
        # pass
        
    # def iter_changed_files(self):
        # for f1 in self._new_dir.iter_files():
            # f2 = self._old_dir.get_file(f1.name)
            # if f2 is None:
                # continue
            # if f1.mtime != f2.mtime or f1.size != f2.size:
                # yield f1, f2
