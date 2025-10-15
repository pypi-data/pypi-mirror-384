import base64
import functools
import locale
import io
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from shell_lib.shell_lib import FS_ENCODING, Shell, PathInfo, quote_sh
from shell_lib.powershell import pwsh, quote_pwsh

IS_WINDOWS = (sys.platform == 'win32')
IS_KNOWN_PYTHON_VERSION = (sys.version_info < (3, 15))

def optional_exception(exception_type, expected_message):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except exception_type as e:
                self.assertIn(expected_message, str(e))
                print((f"\n{func.__name__} raised expected exception: "
                       f"{exception_type} {e}"))
        return wrapper
    return decorator

def path_noop(path) -> Path:
    assert isinstance(path, Path)
    return path

def path2bytes(path) -> bytes:
    assert isinstance(path, Path)
    s = str(path)
    return s.encode(sys.getfilesystemencoding())

class TestShellFileOperations(unittest.TestCase):
    def setUp(self):
        """
        Set up a temporary directory and a Shell instance for testing.
        """
        Shell._CURRENT_OS = None
        self.sh = Shell()
        self.test_dir = Path(tempfile.mkdtemp())
        self.file_path = self.test_dir / 'test_file.txt'
        self.dir_path = self.test_dir / 'test_dir'
        self.sub_file_path = self.dir_path / 'sub_file.txt'

        # Create some files and directories for testing
        with open(self.file_path, 'wb') as f:
            f.write(b"Hello, World!")
        os.makedirs(self.dir_path, exist_ok=True)
        with open(self.sub_file_path, 'wb') as f:
            f.write(b"Sub file content.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    # --- File and Directory Operations API Tests ---
    def test_home_dir(self):
        self.assertTrue(isinstance(self.sh.home_dir(), Path))

    def test_path_converts_to_pathlib(self):
        for func in (path_noop, str, path2bytes):
            path = func(self.file_path)
            self.assertEqual(self.sh.path(path), self.file_path)

        if IS_KNOWN_PYTHON_VERSION:
            # need to convert bytes path to str
            with self.assertRaises(TypeError):
                Path(b'abc')

    def test_create_remove_dir(self):
        dir = self.test_dir / 'new_dir'
        for func in (path_noop, str, path2bytes):
            self.sh.create_dir(func(dir))
            self.assertTrue(os.path.isdir(dir))
            self.sh.remove_dir(func(dir))
            self.assertFalse(os.path.exists(dir))

        # ------- path is file ----------
        # create
        with self.assertRaises(FileExistsError):
           self.sh.create_dir(self.file_path)
        self.assertFalse(os.path.isdir(self.file_path))

        # remove
        with self.assertRaises(NotADirectoryError):
            self.sh.remove_dir(self.file_path)
        self.assertTrue(os.path.isfile(self.file_path))

    def test_create_dir_multi_level(self):
        dir = self.test_dir / 'a' / 'b' / 'c'
        self.sh.create_dir(dir)
        self.assertTrue(os.path.isdir(dir))

        with self.assertRaises(FileExistsError):
            self.sh.create_dir(dir)

        self.sh.create_dir(dir, exist_ok=True)

    def test_create_dir_exist_ok(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.create_dir(self.dir_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.create_dir(self.dir_path, exist_ok=False)
        with self.assertRaises(FileExistsError):
            self.sh.create_dir(self.file_path, exist_ok=False)

        self.sh.create_dir(self.dir_path, exist_ok=True)
        self.assertTrue(os.path.isdir(self.dir_path))

        # no exist
        new_dir = self.test_dir / 'new_dir'
        self.sh.create_dir(new_dir, exist_ok=True)
        self.assertTrue(os.path.isdir(new_dir))

    def test_remove_types(self):
        # remove_file, path is dir
        with self.assertRaises(IsADirectoryError):
            self.sh.remove_file(self.dir_path)

        # remove_dir, path is file
        with self.assertRaises(NotADirectoryError):
            self.sh.remove_dir(self.file_path)

    def test_remove_dir_ignore_missing(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.remove_dir(self.dir_path, True)

        # exist
        self.sh.remove_dir(self.dir_path, ignore_missing=True)
        self.assertFalse(os.path.exists(self.dir_path))

        # no exist
        non_existent_dir = self.test_dir / 'non_existent_dir'
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_dir(non_existent_dir, ignore_missing=False)

        self.sh.remove_dir(non_existent_dir, ignore_missing=True)
        self.assertFalse(os.path.exists(non_existent_dir))

    def test_remove_file(self):
        for i in range(3):
            with open(self.dir_path / str(i), 'wb') as f:
                f.write(b'123')

        for i, func in enumerate((path_noop, str, path2bytes)):
            path = self.dir_path / str(i)
            self.sh.remove_file(func(path))
            self.assertFalse(os.path.exists(path))

    def test_remove_file_ignore_missing(self):
        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.remove_file(self.dir_path, True)

        # exist
        self.sh.remove_file(self.file_path, ignore_missing=True)
        self.assertFalse(os.path.exists(self.file_path))

        # no exist
        non_existent_file = self.test_dir / 'non_existent_file.txt'
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_file(non_existent_file, ignore_missing=False)

        self.sh.remove_file(non_existent_file, ignore_missing=True)
        self.assertFalse(os.path.exists(non_existent_file))

    def test_clear_dir(self):
        # is file
        with self.assertRaises(NotADirectoryError):
            self.sh.clear_dir(self.file_path)
        # not exist
        with self.assertRaises(FileNotFoundError):
            self.sh.clear_dir(self.test_dir / 'not_exist')
        # remove_dir() also raise FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_dir(self.test_dir / 'not_exist')

        # create the dir to be linked
        target_dir = self.test_dir / 'symlink_target_dir'
        self.sh.create_dir(target_dir)
        self.assertTrue(os.path.isdir(target_dir))
        self.assertFalse(os.path.islink(target_dir))

        # create the dir to be tested
        dir = self.test_dir / 'test_clear_dir'
        self.sh.copy_dir(self.dir_path, dir)
        self.assertTrue(os.path.isdir(dir))
        self.assertFalse(os.path.islink(dir))

        for func in (path_noop, str, path2bytes):
            # sub dir
            sub_dir = dir / 'sub_dir_in_test_clear_dir'
            self.sh.create_dir(sub_dir)
            self.assertTrue(os.path.isdir(sub_dir))

            # file in sub-dir
            sub_dir_file = sub_dir / 'file1.txt'
            with open(sub_dir_file, 'wb') as f:
                f.write(b'123')
            self.assertTrue(os.path.isfile(sub_dir_file))
            self.assertFalse(os.path.islink(sub_dir_file))

            # symlink in sub-dir
            dir_symlink = dir / 'symlink'
            try:
                os.symlink(target_dir, dir_symlink, target_is_directory=True)
            except OSError as e:
                print("Can't create symlink in test_clear_dir", e)
            else:
                self.assertTrue(os.path.isdir(dir_symlink))
                self.assertTrue(os.path.islink(dir_symlink))
                self.assertFalse(os.path.isfile(dir_symlink))
                fi = self.sh.get_path_info(dir_symlink)
                self.assertTrue(fi.is_dir)
                self.assertTrue(fi.is_link)
                self.assertFalse(fi.is_file)
                self.assertTrue(self.sh.is_dir(dir_symlink))
                self.assertTrue(self.sh.is_link(dir_symlink))
                self.assertFalse(self.sh.is_file(dir_symlink))

            # clear
            self.sh.clear_dir(func(dir))
            self.assertTrue(os.path.isdir(dir))
            self.assertFalse(os.path.exists(sub_dir))
            self.assertFalse(os.path.exists(sub_dir_file))
            self.assertFalse(os.path.exists(dir_symlink))

    def test_src_not_exist(self):
        # all raise FileNotFoundError
        src = self.test_dir / 'not_exist_path'
        dst = self.test_dir / 'dst'
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_file(src)
        with self.assertRaises(FileNotFoundError):
            self.sh.remove_dir(src)
        with self.assertRaises(FileNotFoundError):
            self.sh.clear_dir(src)
        with self.assertRaises(FileNotFoundError):
            self.sh.copy_file(src, dst)
        with self.assertRaises(FileNotFoundError):
            self.sh.copy_dir(src, dst)
        with self.assertRaises(FileNotFoundError):
            self.sh.move_file(src, dst)
        with self.assertRaises(FileNotFoundError):
            self.sh.move_dir(src, dst)
        with self.assertRaises(FileNotFoundError):
            self.sh.rename_file(src, dst)
        with self.assertRaises(FileNotFoundError):
            self.sh.rename_dir(src, dst)

    def test_dst_is_existing_file(self):
        src = self.dir_path
        dst = self.file_path

        sh = self.sh
        # all _dir methods raise FileExistsError
        with self.assertRaises(FileExistsError):
            sh.copy_dir(src, dst)
        with self.assertRaises(FileExistsError):
            sh.copy_dir(src, dst, remove_existing_dst=True)
        with self.assertRaises(FileExistsError):
            sh.move_dir(src, dst)
        with self.assertRaises(FileExistsError):
            sh.move_dir(src, dst, remove_existing_dst=True)
        with self.assertRaises(FileExistsError):
            sh.rename_dir(src, dst)

    def test_dst_is_existing_dir(self):
        class Prepare:
            src_file = self.file_path
            src_dir  = self.test_dir / 'src_dir'
            src_dir_file = src_dir / 'src_dir_file.txt'

            src_file_bak = self.test_dir / 'src_file.bak'
            src_dir_bak  = self.test_dir / 'src_dir.bak'

            dst_a = self.test_dir / 'a'
            dst_a_b = dst_a / 'b'

            def __enter__(p):
                if not src_file.exists():
                    self.sh.copy_file(p.src_file_bak, p.src_file)
                if not src_dir.exists():
                    self.sh.copy_dir(p.src_dir_bak, p.src_dir)
                self.sh.remove_dir(p.dst_a, ignore_missing=True)
                self.sh.create_dir(p.dst_a)
                return self

            def __exit__(p, exc_type, exc_val, exc_tb):
                pass

            @classmethod
            def init(cls):
                self.sh.create_dir(cls.src_dir)
                with open(cls.src_dir_file, 'wb') as f:
                    f.write(b'src_dir_file')
                self.sh.copy_file(cls.src_file, cls.src_file_bak)
                self.sh.copy_dir(cls.src_dir, cls.src_dir_bak)

        Prepare.init()
        src_file = Prepare.src_file
        src_dir = Prepare.src_dir
        dst_a = Prepare.dst_a
        dst_a_b = Prepare.dst_a_b

        # Destionation type
        #  a is an existing dir
        #  a/b is a not existing path
        # * means use remove_existing_dst=True
        #               a    a/b
        # copy_file     yes  yes
        # copy_dir      no   yes
        # copy_dir *    yes  yes
        # move_file     yes  yes
        # move_dir      no   yes
        # move_dir *    yes  yes
        # rename_file   no   yes
        # rename_dir    no   yes

        # copy_file
        with Prepare():
            self.sh.copy_file(src_file, dst_a)
        with Prepare():
            self.sh.copy_file(src_file, dst_a_b)
        # copy_dir
        with Prepare():
            with self.assertRaises(FileExistsError):
                self.sh.copy_dir(src_dir, dst_a)
        with Prepare():
            self.sh.copy_dir(src_dir, dst_a, remove_existing_dst=True)
        with Prepare():
            self.sh.copy_dir(src_dir, dst_a_b)
        # move_file
        with Prepare():
            self.sh.move_file(src_file, dst_a)
        with Prepare():
            self.sh.move_file(src_file, dst_a_b)
        # move_dir
        with Prepare():
            with self.assertRaises(FileExistsError):
                self.sh.move_dir(src_dir, dst_a)
        with Prepare():
            self.sh.move_dir(src_dir, dst_a, remove_existing_dst=True)
        with Prepare():
            self.sh.move_dir(src_dir, dst_a_b)
        # rename file
        with Prepare():
            with self.assertRaises(FileExistsError):
                self.sh.rename_file(src_file, dst_a)
        with Prepare():
            self.sh.rename_file(src_file, dst_a_b)
        # rename dir
        with Prepare():
            with self.assertRaises(FileExistsError):
                self.sh.rename_dir(src_dir, dst_a)
        with Prepare():
            self.sh.rename_dir(src_dir, dst_a_b)

    def test_copy_file(self):
        # src is dir
        src_dir = self.test_dir / 'created_dir'
        self.sh.create_dir(src_dir)
        self.assertTrue(os.path.isdir(src_dir))
        with self.assertRaises(IsADirectoryError):
            self.sh.copy_file(src_dir, self.dir_path)

        # dst is dir
        self.sh.copy_file(self.file_path, self.dir_path)
        self.assertTrue(os.path.isfile(self.file_path))
        self.assertTrue(os.path.isfile(self.dir_path / 'test_file.txt'))

        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / f'{i}.txt'
            self.sh.copy_file(func(self.file_path), func(dst))
            self.assertTrue(os.path.isfile(self.file_path))
            self.assertTrue(os.path.isfile(dst))
            with open(dst, 'rb') as f:
                self.assertEqual(f.read(), b"Hello, World!")

    def test_copy_file_remove_existing_dst(self):
        dst_path = self.test_dir / 'copied_file.txt'
        with open(dst_path, 'w') as f:
            f.write('copied_file')

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.copy_file(self.file_path, dst_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.copy_file(self.file_path, dst_path, remove_existing_dst=False)

        self.sh.copy_file(self.file_path, dst_path, remove_existing_dst=True)
        with open(dst_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # no exist
        no_exist_path = self.test_dir / 'newfile.txt'
        self.sh.copy_file(self.file_path, no_exist_path, remove_existing_dst=True)
        with open(no_exist_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

    def test_copy_dir(self):
        # src is file
        with self.assertRaises(NotADirectoryError):
            self.sh.copy_dir(self.file_path, self.dir_path)

        # dst is file
        with self.assertRaises(FileExistsError):
            self.sh.copy_dir(self.dir_path, self.file_path)

        # dst is existing dir
        created_dir = self.test_dir / 'created_dir'
        self.sh.create_dir(created_dir)
        self.assertTrue(os.path.isdir(created_dir))
        with self.assertRaises(FileExistsError):
            self.sh.copy_dir(self.dir_path, created_dir)

        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / str(i)
            self.sh.copy_dir(func(self.dir_path), func(dst))
            self.assertTrue(os.path.isdir(self.dir_path))
            self.assertTrue(os.path.isfile(self.sub_file_path))
            self.assertTrue(os.path.isdir(dst))
            self.assertTrue(os.path.isfile(dst / 'sub_file.txt'))

    def test_copy_dir_remove_existing_dst(self):
        dst_path = self.test_dir / 'copied_dir'
        os.makedirs(dst_path, exist_ok=True)
        with open(dst_path / 'existing.txt', 'w') as f:
            f.write('existing content')

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.copy_dir(self.dir_path, dst_path, remove_existing_dst=False)
        self.assertTrue(os.path.isdir(self.dir_path))
        self.assertTrue(os.path.isfile(self.sub_file_path))
        self.assertTrue(os.path.isfile(dst_path / 'existing.txt'))
        self.assertFalse(os.path.exists(dst_path / 'sub_file.txt'))

        # overwrite
        self.sh.copy_dir(self.dir_path, dst_path, remove_existing_dst=True)
        self.assertTrue(os.path.isdir(self.dir_path))
        self.assertTrue(os.path.isfile(self.sub_file_path))
        self.assertTrue(os.path.isdir(dst_path))
        self.assertTrue(os.path.isfile(dst_path / 'sub_file.txt'))
        self.assertFalse(os.path.exists(dst_path / 'existing.txt'))

        # no exist
        no_exist_path = self.test_dir / 'new_dir'
        self.sh.copy_dir(self.dir_path, no_exist_path, remove_existing_dst=True)
        self.assertTrue(os.path.isdir(self.dir_path))
        self.assertTrue(os.path.isfile(self.sub_file_path))
        self.assertTrue(os.path.isdir(no_exist_path))
        self.assertTrue(os.path.isfile(no_exist_path / 'sub_file.txt'))

    def test_move_file(self):
        # src is dir
        with self.assertRaises(IsADirectoryError):
            self.sh.move_file(self.dir_path, self.test_dir / 'fail')
        self.assertTrue(os.path.isdir(self.dir_path))

        # dst is dir
        src_file = self.test_dir / 'src_file'
        with open(src_file, 'wb') as f:
            f.write(b'123')
        self.assertTrue(os.path.isfile(src_file))
        dst_dir = self.test_dir / 'dst_dir'
        self.sh.create_dir(dst_dir)
        self.assertTrue(os.path.isdir(dst_dir))
        self.sh.move_file(src_file, dst_dir)
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.isfile(self.test_dir / 'dst_dir' / 'src_file'))

        src = self.file_path
        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / f'{i}.txt'
            self.sh.move_file(func(src), func(dst))
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.isfile(dst))
            with open(dst, 'rb') as f:
                self.assertEqual(f.read(), b"Hello, World!")
            src = dst

    def test_move_file_remove_existing_dst(self):
        dst_path = self.test_dir / 'moved_file.txt'
        with open(dst_path, 'w') as f:
            f.write('moved_file')

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.move_file(self.file_path, dst_path, True)

        # exist
        with self.assertRaises(FileExistsError):
            self.sh.move_file(self.file_path, dst_path, remove_existing_dst=False)

        # overwrite
        self.sh.move_file(self.file_path, dst_path, remove_existing_dst=True)
        self.assertFalse(os.path.exists(self.file_path))
        with open(dst_path, 'r') as f:
            self.assertEqual(f.read(), "Hello, World!")

        # no exist
        no_exist_path = self.test_dir / 'newfile.txt'
        self.sh.move_file(dst_path, no_exist_path, remove_existing_dst=True)
        self.assertFalse(os.path.exists(dst_path))
        self.assertTrue(os.path.isfile(no_exist_path))

    def test_move_dir(self):
        # src is file
        with self.assertRaises(NotADirectoryError):
            self.sh.move_dir(self.file_path, self.dir_path)
        self.assertTrue(os.path.isfile(self.file_path))

        # dst is file
        with self.assertRaises(FileExistsError):
            self.sh.move_dir(self.dir_path, self.file_path)
        self.assertTrue(os.path.isfile(self.file_path))

        # dst is existing dir
        created_dir = self.test_dir / 'created_dir'
        self.sh.create_dir(created_dir)
        self.assertTrue(os.path.isdir(created_dir))
        with self.assertRaises(FileExistsError):
            self.sh.move_dir(self.dir_path, created_dir)

        src = self.dir_path
        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / str(i)
            self.sh.move_dir(func(src), func(dst))
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.isdir(dst))
            self.assertTrue(os.path.isfile(dst / 'sub_file.txt'))
            src = dst

    def test_move_dir_remove_existing_dst(self):
        src = self.test_dir / 'src'
        dst = self.test_dir / 'dst'
        os.makedirs(src)
        os.makedirs(dst)

        # keyword only arg
        with self.assertRaises(TypeError):
            self.sh.move_dir(src, dst, True)

        # exist
        self.sh.move_dir(src, dst, remove_existing_dst=True)
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.isdir(src))

        # no exist
        self.sh.create_dir(src)
        self.sh.remove_dir(dst)
        self.sh.move_dir(src, dst, remove_existing_dst=True)
        self.assertTrue(os.path.exists(dst))
        self.assertFalse(os.path.isdir(src))

    def test_move_dir_no_remove_existing_dst(self):
        # exist
        src = self.test_dir / 'src'
        dst = self.test_dir / 'dst'
        os.makedirs(src)
        os.makedirs(dst)
        with self.assertRaises(FileExistsError):
            self.sh.move_dir(src, dst, remove_existing_dst=False)

        # no exist
        self.sh.remove_dir(dst)
        self.sh.move_dir(src, dst, remove_existing_dst=False)
        self.assertFalse(os.path.exists(src))
        self.assertTrue(os.path.isdir(dst))

    def test_move_dir_remove_existing_dst_types(self):
        for i, func in enumerate((path_noop, str, path2bytes)):
            src = self.test_dir / 'src_dir'
            src_file = src / 'file.txt'
            dst = self.test_dir / 'dst_dir'
            os.makedirs(src, exist_ok=True)
            with open(src_file, 'w', encoding='ascii') as f:
                f.write(str(i))
            os.makedirs(dst, exist_ok=True)

            self.sh.move_dir(func(src), func(dst), remove_existing_dst=True)
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.isdir(dst))
            self.assertTrue(os.path.isfile(dst / 'file.txt'))
            with open(dst / 'file.txt', 'r', encoding='ascii') as f:
                self.assertEqual(f.read(), str(i))
            self.sh.clear_dir(dst)
            self.assertTrue(os.path.isdir(dst))

    def test_rename_file(self):
        # src is dir
        with self.assertRaises(IsADirectoryError):
            self.sh.rename_file(self.dir_path, self.test_dir / 'fail1')
        self.assertTrue(os.path.isdir(self.dir_path))

        # dst is dir
        dir_dst = self.test_dir / 'created_dir'
        self.sh.create_dir(dir_dst)
        self.assertTrue(os.path.isdir(dir_dst))
        with self.assertRaises(FileExistsError):
            self.sh.rename_file(self.file_path, dir_dst)
        self.assertTrue(os.path.isfile(self.file_path))

        # dst is existing file
        exist_path = self.test_dir / 'exists.txt'
        with open(exist_path, 'wb') as f:
            f.write(b'123')
        with self.assertRaises(FileExistsError):
            self.sh.rename_file(self.file_path, exist_path)
        self.assertTrue(os.path.isfile(self.file_path))

        # no exist src
        with self.assertRaises(FileNotFoundError):
            self.sh.rename_file(self.test_dir / 'fail2', self.test_dir / 'filename')
        self.assertFalse(os.path.isfile(self.test_dir / 'filename'))

        src = self.file_path
        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / f'renamed_file_{i}.txt'
            self.sh.rename_file(func(src), func(dst))
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.isfile(dst))
            with open(dst, 'rb') as f:
                self.assertEqual(f.read(), b"Hello, World!")
            src = dst

    def test_rename_dir(self):
        # src is file
        with self.assertRaises(NotADirectoryError):
            self.sh.rename_dir(self.file_path, self.dir_path)
        self.assertTrue(os.path.isfile(self.file_path))

        # dst is file
        dst_file = self.test_dir / 'created_file'
        with open(dst_file, 'wb') as f:
            f.write(b'123')
        self.assertTrue(os.path.isfile(dst_file))
        with self.assertRaises(FileExistsError):
            self.sh.rename_dir(self.dir_path, dst_file)
        self.assertTrue(os.path.isdir(self.dir_path))

        # dst is exsiting dir
        dir_dst = self.test_dir / 'created_dir'
        self.sh.create_dir(dir_dst)
        self.assertTrue(os.path.isdir(dir_dst))
        with self.assertRaises(FileExistsError):
            self.sh.rename_dir(self.dir_path, dir_dst)
        self.assertTrue(os.path.isdir(self.dir_path))

        # no exist
        with self.assertRaises(FileNotFoundError):
            self.sh.rename_dir(self.test_dir / 'fail', self.dir_path / 'dst_dir')

        src = self.dir_path
        for i, func in enumerate((path_noop, str, path2bytes)):
            dst = self.test_dir / f'renamed_dir_{i}'
            self.sh.rename_dir(func(src), func(dst))
            self.assertFalse(os.path.exists(src))
            self.assertTrue(os.path.isdir(dst))
            self.assertTrue(os.path.isfile(dst / 'sub_file.txt'))
            src = dst

    def test_get_file_size(self):
        sh = self.sh
        # not exist
        with self.assertRaises(FileNotFoundError):
            sh.get_file_size(self.test_dir / 'not_exist')
        # is dir
        with self.assertRaises(IsADirectoryError):
            sh.get_file_size(self.dir_path)

        path = self.test_dir / 'len_bytes.txt'
        LEN = 123
        with open(path, 'wb') as f:
            f.write(b'a' * LEN)
        for func in (path_noop, str, path2bytes):
            self.assertEqual(sh.get_file_size(func(path)), LEN)

    def test_get_path_info_for_file(self):
        # file
        info = self.sh.get_path_info(self.file_path)
        self.assertIsInstance(info, PathInfo)
        self.assertEqual(info.path, str(self.file_path))
        self.assertIsInstance(info.size, int)
        self.assertTrue(info.is_file)
        self.assertFalse(info.is_dir)
        self.assertFalse(info.is_link)
        self.assertIs(info.is_readable, True)
        self.assertIs(info.is_writable, True)
        self.assertEqual(type(info.is_executable), bool)

        # dir
        info = self.sh.get_path_info(self.dir_path)
        self.assertIsInstance(info, PathInfo)
        self.assertEqual(info.path, str(self.dir_path))
        self.assertIsInstance(info.size, int)
        self.assertFalse(info.is_file)
        self.assertTrue(info.is_dir)
        self.assertFalse(info.is_link)
        self.assertIs(info.is_readable, True)
        self.assertIs(info.is_writable, True)
        self.assertEqual(type(info.is_executable), bool)

        # not existing
        with self.assertRaises(FileNotFoundError):
            self.sh.get_path_info(self.test_dir / "not_existing")

        self.assertRegex(repr(info),
                         (r"PathInfo\(path=.*?, size=.*?, "
                          r"ctime=.*?, mtime=.*?, atime=.*?, "
                          r"is_dir=.*?, is_file=.*?, is_link=.*?, "
                          r"is_readable=.*?, is_writable=.*?, is_executable=.*?\)"))

        with self.assertRaises(FileNotFoundError):
            self.sh.get_path_info(self.test_dir / 'non_existent')

        # symlink for file
        symlink_file = self.test_dir / 'symlink_file'
        try:
            os.symlink(self.file_path, symlink_file, target_is_directory=False)
        except OSError as e:
            print("Can't create file symlink in test_get_path_info_for_file", e)
        else:
            # os.path.is*
            self.assertTrue(os.path.isfile(symlink_file))
            self.assertTrue(os.path.islink(symlink_file))
            self.assertFalse(os.path.isdir(symlink_file))
            # get_path_info
            pi = self.sh.get_path_info(symlink_file)
            self.assertTrue(pi.is_file)
            self.assertTrue(pi.is_link)
            self.assertFalse(pi.is_dir)
            # sh.is_*
            self.assertTrue(self.sh.is_file(symlink_file))
            self.assertTrue(self.sh.is_link(symlink_file))
            self.assertFalse(self.sh.is_dir(symlink_file))
            # sh.get_file_size
            with open(self.file_path, 'rb') as f:
                size = len(f.read())
            self.assertEqual(pi.size, size)
            self.assertEqual(self.sh.get_file_size(symlink_file), size)

        # symlink for dir
        symlink_dir = self.test_dir / 'symlink_dir'
        try:
            os.symlink(self.dir_path, symlink_dir, target_is_directory=True)
        except OSError as e:
            print("Can't create dir symlink in test_get_path_info_for_file", e)
        else:
            self.assertTrue(os.path.isdir(symlink_dir))
            self.assertTrue(os.path.islink(symlink_dir))
            self.assertFalse(os.path.isfile(symlink_dir))
            pi = self.sh.get_path_info(symlink_dir)
            self.assertTrue(pi.is_dir)
            self.assertTrue(pi.is_link)
            self.assertFalse(pi.is_file)
            self.assertTrue(self.sh.is_dir(symlink_dir))
            self.assertTrue(self.sh.is_link(symlink_dir))
            self.assertFalse(self.sh.is_file(symlink_dir))

    def test_get_path_info_types(self):
        for func in (path_noop, str, path2bytes):
            pi = self.sh.get_path_info(func(self.file_path))
            self.assertTrue(pi.is_file)
            self.assertFalse(pi.is_link)

    def test_list_dir(self):
        for func in (path_noop, str, path2bytes):
            contents = self.sh.list_dir(func(self.test_dir))
            if func is not path2bytes:
                self.assertIn('test_file.txt', contents)
                self.assertIn('test_dir', contents)
            else:
                self.assertIn(b'test_file.txt', contents)
                self.assertIn(b'test_dir', contents)

        # not exist
        with self.assertRaises(FileNotFoundError):
            self.sh.list_dir(self.test_dir / 'non_existent')

        # path is file
        with self.assertRaises(NotADirectoryError):
            self.sh.list_dir(self.file_path)

    def test_walk_dir(self):
        for func in (path_noop, str, path2bytes):
            contents = list(self.sh.walk_dir(func(self.test_dir)))
            self.assertEqual(len(contents), 2)
            self.assertEqual(type(contents[0]), tuple)
            self.assertEqual(len(contents[0]), 2)
            tmp = [item[1] for item in contents]
            if func is not path2bytes:
                self.assertEqual(type(contents[0][0]), str)
                self.assertIn('test_file.txt', tmp)
                self.assertIn('sub_file.txt', tmp)
            else:
                self.assertEqual(type(contents[0][0]), bytes)
                self.assertIn(b'test_file.txt', tmp)
                self.assertIn(b'sub_file.txt', tmp)

        # not exist
        with self.assertRaises(FileNotFoundError):
            list(self.sh.walk_dir(self.test_dir / 'non_existent'))

        # path is file
        with self.assertRaises(NotADirectoryError):
            list(self.sh.walk_dir(self.file_path))

        # top_down
        contents = list(self.sh.walk_dir(self.test_dir, top_down=True))
        tmp = [item[1] for item in contents]
        self.assertEqual(tmp, ['test_file.txt', 'sub_file.txt'])

        contents = list(self.sh.walk_dir(self.test_dir, top_down=False))
        tmp = [item[1] for item in contents]
        self.assertEqual(tmp, ['sub_file.txt', 'test_file.txt'])

    def test_cd_context_manager(self):
        def rp_cwd():
            return os.path.realpath(os.getcwd())
        original_cwd = rp_cwd()

        for func in (path_noop, str, path2bytes):
            with self.sh.cd(func(self.dir_path)):
                self.assertEqual(rp_cwd(), os.path.realpath(self.dir_path))
            self.assertEqual(rp_cwd(), original_cwd)

        # None
        with self.sh.cd(None):
            self.assertEqual(rp_cwd(), original_cwd)
            self.sh.cd(self.dir_path)
            self.assertEqual(rp_cwd(), os.path.realpath(self.dir_path))
        self.assertEqual(rp_cwd(), original_cwd)

        # exception
        try:
            with self.sh.cd(self.test_dir):
                self.assertEqual(rp_cwd(), os.path.realpath(self.test_dir))
                raise ValueError("Test Exception")
        except ValueError:
            pass
        self.assertEqual(rp_cwd(), original_cwd)

    def test_path_exists(self):
        # Path/str/bytes types tested below
        self.assertTrue(self.sh.path_exists(self.dir_path))
        self.assertTrue(self.sh.path_exists(self.file_path))
        self.assertFalse(self.sh.path_exists(self.test_dir / 'non_existent'))

    def test_is_file(self):
        # not exist
        self.assertIs(self.sh.is_file(self.test_dir / 'not_exist'), False)

        for func in (path_noop, str, path2bytes):
            self.assertTrue(self.sh.is_file(func(self.file_path)))
            self.assertTrue(self.sh.path_exists(func(self.file_path)))
            self.assertFalse(self.sh.is_file(func(self.dir_path)))
            self.assertTrue(self.sh.path_exists(func(self.dir_path)))

    def test_is_dir(self):
        # not exist
        self.assertIs(self.sh.is_dir(self.test_dir / 'not_exist'), False)

        for func in (path_noop, str, path2bytes):
            self.assertTrue(self.sh.is_dir(func(self.dir_path)))
            self.assertTrue(self.sh.path_exists(func(self.dir_path)))
            self.assertFalse(self.sh.is_dir(func(self.file_path)))
            self.assertTrue(self.sh.path_exists(func(self.file_path)))

    def test_is_link(self):
        # not exist
        self.assertIs(self.sh.is_link(self.test_dir / 'not_exist'), False)

        for func in (path_noop, str, path2bytes):
            self.assertFalse(self.sh.is_link(func(self.dir_path)))
            self.assertTrue(self.sh.path_exists(func(self.dir_path)))
            self.assertFalse(self.sh.is_link(func(self.file_path)))
            self.assertTrue(self.sh.path_exists(func(self.file_path)))

    def test_split_path(self):
        for func in (path_noop, str, path2bytes):
            parent_dir, filename = self.sh.split_path(func(self.file_path))
            if func is not path2bytes:
                self.assertEqual(parent_dir, str(self.test_dir))
                self.assertEqual(filename, 'test_file.txt')
            else:
                self.assertEqual(parent_dir, path2bytes(self.test_dir))
                self.assertEqual(filename, b'test_file.txt')

        self.assertTrue(self.sh.split_path(self.file_path)[1], 'test_file.txt')
        self.assertTrue(self.sh.split_path(self.dir_path)[1], 'test_dir')

    def test_join_path(self):
        for func in (path_noop, str, path2bytes):
            part1 = func(self.test_dir)
            part2 = func(Path('test_file.txt'))
            joined = self.sh.join_path(part1, part2)
            self.assertTrue(os.path.isfile(joined))
            if func is not path2bytes:
                self.assertEqual(type(joined), str)
                self.assertEqual(self.file_path, Path(joined))
            else:
                self.assertEqual(type(joined), bytes)
                self.assertEqual(self.file_path, Path(joined.decode(FS_ENCODING)))

        # empty
        with self.assertRaises(TypeError):
            self.sh.join_path()

class TestShellOtherOperations(unittest.TestCase):
    def setUp(self):
        Shell._CURRENT_OS = None
        self.sh = Shell()

    def test_set_attr(self):
        with self.assertRaises(AttributeError):
            self.sh.aaa = 123
        with self.assertRaises(AttributeError):
            self.sh.OS_Linux = 123
        with self.assertRaises(AttributeError):
            delattr(self.sh, 'cd')

    @patch('subprocess.run')
    def test_call_executes_shell_command(self, mock_run):
        self.sh("echo hello")
        mock_run.assert_called_once()
        self.assertTrue(mock_run.call_args[0][0].startswith('echo hello'))

    @patch('subprocess.run')
    def test_safe_run_executes_securely(self, mock_run):
        self.sh.safe_run(['ls', '-l'])
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args[0][0], ['ls', '-l'])

    @patch('subprocess.run', side_effect=subprocess.CalledProcessError(90, 'cmd'))
    @patch('sys.exit')
    def test_context_manager_exits_on_error(self, mock_exit, mock_run):
        tmp = sys.stderr
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')
        try:
            with self.sh:
                self.sh("bad command")
        except subprocess.CalledProcessError:
            pass
        finally:
            sys.stderr.close()
            sys.stderr = tmp
        mock_exit.assert_called_once_with(90)

    @patch('subprocess.run')
    def test_sh_quote(self, mock_run):
        if sys.version_info >= (3, 14, 0, 'beta', 1):
            locals = {'sh': self.sh}
            py_code = """\
DIR = "shell_lib'"
sh(t'dir {DIR}')
"""
            exec(py_code, locals=locals)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            if IS_WINDOWS:
                self.assertEqual(args, '''dir "shell_lib'"''')
            else:
                self.assertEqual(args, 'dir ' + shlex.quote("shell_lib'"))

        s1 = """"abc" > 'def' & ‘123’"""
        if IS_WINDOWS:
            s2 = '''"""abc"" > 'def' & ‘123’"'''
            self.assertEqual(quote_sh(s1), s2)
        else:
            self.assertEqual(quote_sh(s1), shlex.quote(s1))

    @patch('subprocess.run')
    def test_powershell_run(self, mock_run):
        CMD = 'dir shell_lib'
        pwsh(CMD)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]

        b = CMD.encode('utf-16le')
        b64 = base64.standard_b64encode(b).decode('ascii')
        cmd1 = f'pwsh -EncodedCommand {b64}'
        cmd2 = f'powershell -EncodedCommand {b64}'
        self.assertIn(args, (cmd1, cmd2))

    @patch('subprocess.run')
    def test_powershell_quote(self, mock_run):
        if sys.version_info >= (3, 14, 0, 'beta', 1):
            locals = {'pwsh': pwsh}
            py_code = """\
DIR = "shell_lib'"
pwsh(t'dir {DIR}')
"""
            exec(py_code, locals=locals)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]

            b = "dir 'shell_lib'''".encode('utf-16le')
            b64 = base64.standard_b64encode(b).decode('ascii')
            cmd1 = f'pwsh -EncodedCommand {b64}'
            cmd2 = f'powershell -EncodedCommand {b64}'
            self.assertIn(args, (cmd1, cmd2))

        s1 = """"abc" > 'def' & ‘123’"""
        s2 = """'"abc" > ''def'' & ‘‘123’’'"""
        self.assertEqual(quote_pwsh(s1), s2)

    @patch('subprocess.run')
    def test_powershell_run_file(self, mock_run):
        CMD = ['file.ps1']
        pwsh.run_file(CMD)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertTrue(args[0] in ('pwsh', 'powershell'))
        self.assertEqual(args[1], '-File')
        self.assertEqual(args[2:], CMD)

    @patch('subprocess.run')
    def test_powershell_run_file_params(self, mock_run):
        CMD = ['file.ps1', 'abc', '-param1', '123']
        pwsh.run_file(CMD)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertTrue(args[0] in ('pwsh', 'powershell'))
        self.assertEqual(args[1], '-File')
        self.assertEqual(args[2:], CMD)

    # --- Script Control API Mocked Tests ---
    @patch('builtins.input', side_effect=['invalid', '4', '0', '2 '])
    def test_ask_choice(self, mock_input):
        choice = self.sh.ask_choice("Choose an option:",
                                    "Option 1", "Option 2", "Option 3")
        self.assertEqual(choice, 2)
        self.assertEqual(mock_input.call_count, 4)

    def test_ask_choice_raises_error_with_no_choices(self):
        with self.assertRaises(ValueError):
            self.sh.ask_choice("Choose an option:")

    @patch('builtins.input', side_effect=['xxx', 'yes',
                                          '', ' YeS ',
                                          '1', 'y ',
                                          'ys', ' Y'])
    def test_ask_yes_no_yes(self, mock_input):
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertTrue(self.sh.ask_yes_no("Do you agree?"))
        self.assertEqual(mock_input.call_count, 8)

    @patch('builtins.input', side_effect=['xxx', 'no',
                                          '', ' No ',
                                          '1', 'n ',
                                          'not', ' N'])
    def test_ask_yes_no_no(self, mock_input):
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertFalse(self.sh.ask_yes_no("Do you agree?"))
        self.assertEqual(mock_input.call_count, 8)

    @patch('builtins.input', side_effect=['d.3.2', '', '1.3.2',
                                          'abc ', ' 1.3.2 '])
    def test_ask_regex_input(self, mock_input):
        m = self.sh.ask_regex_input("Input version", r"\s*(\d+\.\d+\.\d+)\s*")
        self.assertEqual(m.group(1), '1.3.2')

        m = self.sh.ask_regex_input("Input version",
                                 r"\s*(\d+\.\d+\.\d+)\s*",
                                 print_pattern=True)
        self.assertEqual(m.group(1), '1.3.2')
        self.assertEqual(mock_input.call_count, 5)

        with self.assertRaises(TypeError):
            self.sh.ask_regex_input("title")
        with self.assertRaises(Exception):
            self.sh.ask_regex_input("title", r"(abc")

    def test_ask_password(self):
        # hard to test, it only invokes stdlib function.
        with self.assertRaises(TypeError):
            self.sh.ask_password(b'123')

    @patch('sys.exit')
    def test_exit(self, mock_exit):
        self.sh.exit(91)
        mock_exit.assert_called_once_with(91)

    # --- Utility and OS-specific Tests ---
    # Pass on Simplified Chinese Windows 10 and Ubuntu 24.04.
    @optional_exception(UnicodeError, '')
    def test_get_set_env_non_ascii(self):
        sh = self.sh
        K = '环境变量shell-lib'
        V = '环境变量值'
        # non-ascii env name works for posix (inside process), windows.
        orig = sh.get_env(K)
        self.assertEqual(orig, os.getenv(K))
        with sh.set_env(K, V):
            self.assertEqual(sh.get_env(K), V)
            self.assertEqual(os.getenv(K), V)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

        cmd = f"import os;print(os.getenv('{K}'),end='',flush=1)"

        # on posix, non-ascii env name works for: shell=False
        with sh.set_env(K, V):
            ret = sh.safe_run([sys.executable, '-c', cmd], print_output=False)
            self.assertEqual(ret.stdout, V)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

        # on posix, non-ascii env name doesn't work for: shell=True
        # posix env name only accept (a-z, A-Z, 0-9, _)
        # otherwise, child process can't see the env.
        if sh.is_os(sh.OS_Windows):
            with sh.set_env(K, V):
                ret = sh(f'{sys.executable} -c "{cmd}"', print_output=False)
                self.assertEqual(ret.stdout, V)
            self.assertEqual(sh.get_env(K), orig)
            self.assertEqual(os.getenv(K), orig)

    def test_get_set_env(self):
        sh = self.sh
        K = 'SHELL_LIB_TEST_KEY'
        V = 'SHELL_LIB_TEST_VALUE'
        DEFAULT = 'default_value'
        sh.set_env(K, V)
        self.assertEqual(sh.get_env(K), V)
        self.assertEqual(sh.get_env(K, DEFAULT), V)
        self.assertEqual(os.getenv(K), V)
        for _ in range(2):
            sh.set_env(K, None)
            self.assertEqual(sh.get_env(K), None)
            self.assertEqual(sh.get_env(K, DEFAULT), DEFAULT)
            self.assertEqual(os.getenv(K), None)

        TEST_2_K = 'SHELL_LIB_TEST_2_K'
        TEST_2_V = 'SHELL_LIB_TEST_2_V'
        self.assertEqual(sh.get_env(TEST_2_K), os.getenv(TEST_2_K))
        os.environ[TEST_2_K] = TEST_2_V
        self.assertEqual(sh.get_env(TEST_2_K), TEST_2_V)

        TEST_3_K = 'SHELL_LIB_TEST_3_K'
        TEST_3_V = 'SHELL_LIB_TEST_3_V'
        self.assertEqual(sh.get_env(TEST_3_K), os.getenv(TEST_3_K))
        os.putenv(TEST_3_K, TEST_3_V)
        self.assertEqual(sh.get_env(TEST_3_K), TEST_3_V)

        SUB_K = "SHELL_LIB_SUB_key"
        SUB_V = "SHELL-LIB-SUB-value"
        sh.set_env(SUB_K, SUB_V)

        # subprocess, shell=False
        ret = sh.safe_run(
                [sys.executable, '-c',
                 f'import os;print(os.getenv("{SUB_K}"),end="",flush=1)'],
                print_output=False)
        self.assertEqual(ret.stdout, SUB_V)

        # subprocess, shell=True
        ret = sh(
            f'''{sys.executable} -c "import os;print(os.getenv('{SUB_K}'),end='',flush=1)"''',
            print_output=False)
        self.assertEqual(ret.stdout, SUB_V)

        # wrong type
        with self.assertRaises(TypeError):
            sh.get_env(b'bytes')
        with self.assertRaises(TypeError):
            sh.get_env(123)
        with self.assertRaises(TypeError):
            sh.get_env('A', 'B', 'C')

        with self.assertRaises(TypeError):
            sh.set_env(b'bytes', V)
        with self.assertRaises(TypeError):
            sh.set_env(K, b'bytes')
        with self.assertRaises(TypeError):
            sh.set_env(123, V)
        with self.assertRaises(TypeError):
            sh.set_env(K, 123)
        with self.assertRaises(TypeError):
            sh.set_env('A', 'B', 'C')
        with self.assertRaises(TypeError):
            sh.set_env(key='A', value='B')

    def test_set_env_context_manager_k_v(self):
        sh = self.sh
        K = 'SHELL_LIB_TEST_KEY'
        V1 = 'SHELL_LIB_TEST_VALUE_1'
        V2 = 'SHELL_LIB_TEST_VALUE_2'
        V3 = 'SHELL_LIB_TEST_VALUE_3'

        # V1, V2, V3
        orig = os.getenv(K)
        with sh.set_env(K, V1):
            self.assertEqual(sh.get_env(K), V1)
            self.assertEqual(os.getenv(K), V1)
            with sh.set_env(K, V2):
                self.assertEqual(sh.get_env(K), V2)
                self.assertEqual(os.getenv(K), V2)
                with sh.set_env(K, V3):
                    self.assertEqual(sh.get_env(K), V3)
                    self.assertEqual(os.getenv(K), V3)
                self.assertEqual(sh.get_env(K), V2)
                self.assertEqual(os.getenv(K), V2)
            self.assertEqual(sh.get_env(K), V1)
            self.assertEqual(os.getenv(K), V1)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

        # None, V2, None
        orig = os.getenv(K)
        with sh.set_env(K, None):
            self.assertEqual(sh.get_env(K), None)
            self.assertEqual(os.getenv(K), None)
            with sh.set_env(K, V2):
                self.assertEqual(sh.get_env(K), V2)
                self.assertEqual(os.getenv(K), V2)
                with sh.set_env(K, None):
                    self.assertEqual(sh.get_env(K), None)
                    self.assertEqual(os.getenv(K), None)
                self.assertEqual(sh.get_env(K), V2)
                self.assertEqual(os.getenv(K), V2)
            self.assertEqual(sh.get_env(K), None)
            self.assertEqual(os.getenv(K), None)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

        # None, None, None
        orig = os.getenv(K)
        with sh.set_env(K, None):
            self.assertEqual(sh.get_env(K), None)
            self.assertEqual(os.getenv(K), None)
            with sh.set_env(K, None):
                self.assertEqual(sh.get_env(K), None)
                self.assertEqual(os.getenv(K), None)
                with sh.set_env(K, None):
                    self.assertEqual(sh.get_env(K), None)
                    self.assertEqual(os.getenv(K), None)
                self.assertEqual(sh.get_env(K), None)
                self.assertEqual(os.getenv(K), None)
            self.assertEqual(sh.get_env(K), None)
            self.assertEqual(os.getenv(K), None)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

    def test_set_env_context_manager_dict(self):
        sh = self.sh
        K1 = 'SHELL_LIB_TEST_dict_k_1'
        V1 = 'SHELL_LIB_TEST_dict_v_1'
        K2 = 'SHELL_LIB_TEST_dict_k_2'
        V2 = 'SHELL_LIB_TEST_dict_v_2'
        K3 = 'SHELL_LIB_TEST_dict_k_3'
        V3 = None

        sh.set_env(K2, "1234")
        sh.set_env(K3, "abcd")
        orig_1 = sh.get_env(K1)
        orig_2 = sh.get_env(K2)
        orig_3 = sh.get_env(K3)
        with sh.set_env({K1: V1, K2: V2, K3: V3}):
            self.assertEqual(sh.get_env(K1), V1)
            self.assertEqual(os.getenv(K1), V1)

            self.assertEqual(sh.get_env(K2), V2)
            self.assertEqual(os.getenv(K2), V2)

            self.assertEqual(sh.get_env(K3), V3)
            self.assertEqual(os.getenv(K3), V3)
        self.assertEqual(sh.get_env(K1), orig_1)
        self.assertEqual(sh.get_env(K2), orig_2)
        self.assertEqual(sh.get_env(K3), orig_3)

    def test_setenv_not_use_os_environ(self):
        sh = self.sh
        K = 'SHELL_LIB_TEST_NUOE_k'
        V = 'SHELL_LIB_TEST_NUOE_v'
        orig = sh.get_env(K)
        self.assertEqual(orig, os.getenv(K))

        # not use os.environ to set
        os.putenv(K, V)
        self.assertEqual(sh.get_env(K), V)
        if IS_KNOWN_PYTHON_VERSION:
            self.assertEqual(os.getenv(K), orig)

        # unset
        sh.set_env(K, None)
        self.assertEqual(sh.get_env(K), orig)
        self.assertEqual(os.getenv(K), orig)

    def test_redirected_stdout(self):
        K = 'SHELL_LIB_TEST_KEY'
        V = 'SHELL_LIB_TEST_VALUE'

        f = io.StringIO()
        with redirect_stdout(f):
            self.sh.set_env(K, V)
        self.assertIn(f"Set environment variable '{K}' to '{V}'.",
                      f.getvalue())

    def test_os_constants(self):
        a = ['OS_Windows', 'OS_Cygwin',
             'OS_Linux', 'OS_macOS', 'OS_Unix', 'OS_Unix_like']
        b = [one for one in dir(self.sh)
                 if one.startswith('OS_')]
        a.sort()
        b.sort()
        self.assertEqual(a, b)

        self.assertEqual(self.sh.OS_Windows, 4)
        self.assertEqual(self.sh.OS_Cygwin, 8)
        self.assertEqual(self.sh.OS_Linux, 16)
        self.assertEqual(self.sh.OS_macOS, 32)
        self.assertEqual(self.sh.OS_Unix, 64)
        self.assertEqual(self.sh.OS_Unix_like,
                         self.sh.OS_Cygwin | self.sh.OS_Linux |
                         self.sh.OS_macOS | self.sh.OS_Unix)
        self.assertEqual(self.sh._ALL_OS_BITS,
                         self.sh.OS_Windows | self.sh.OS_Cygwin |
                         self.sh.OS_Linux | self.sh.OS_macOS |
                         self.sh.OS_Unix)

        with self.assertRaises(AttributeError):
            self.sh.OS_Windows = 123
        with self.assertRaises(AttributeError):
            del self.sh.OS_Linux
        # invalid bits
        with self.assertRaises(ValueError):
            self.sh.is_os(1)
        with self.assertRaises(ValueError):
            self.sh.is_os(2)
        with self.assertRaises(ValueError):
            self.sh.is_os(128)

    def test_z1_is_os(self):
        os = ['OS_Windows', 'OS_Cygwin',
              'OS_Linux', 'OS_macOS', 'OS_Unix', 'OS_Unix_like']
        os = [i for i in os if self.sh.is_os(getattr(self.sh, i))]
        print('sh.is_os():', os)

        # mock tests
        Shell._CURRENT_OS = None
        with patch('sys.platform', 'win32'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Windows))
            self.assertFalse(self.sh.is_os(self.sh.OS_Cygwin))
            self.assertFalse(self.sh.is_os(self.sh.OS_macOS))
            self.assertFalse(self.sh.is_os(self.sh.OS_Unix_like))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'linux'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Linux))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Windows))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'darwin'):
            self.assertTrue(self.sh.is_os(self.sh.OS_macOS))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Linux))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'cygwin'):
            self.assertTrue(self.sh.is_os(self.sh.OS_Cygwin))
            self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
            self.assertFalse(self.sh.is_os(self.sh.OS_Windows))

        Shell._CURRENT_OS = None
        with patch('sys.platform', 'freebsd'):
            with patch('os.name', 'posix'):
                self.assertTrue(self.sh.is_os(self.sh.OS_Unix))
                self.assertTrue(self.sh.is_os(self.sh.OS_Unix_like))
                self.assertFalse(self.sh.is_os(self.sh.OS_Linux))

    def test_z2_get_preferred_encoding(self):
        enc = self.sh.get_preferred_encoding()
        self.assertEqual(type(enc), str)
        print('sh.get_preferred_encoding():', enc)

    def test_z3_get_locale_encoding(self):
        enc = self.sh.get_locale_encoding()
        self.assertEqual(type(enc), str)
        if sys.version_info >= (3, 11, 0, 'beta', 1):
            self.assertEqual(enc, locale.getencoding())
        print('sh.get_locale_encoding():', enc)

    def test_z4_get_filesystem_encoding(self):
        enc = self.sh.get_filesystem_encoding()
        self.assertEqual(type(enc), str)
        self.assertEqual(enc, sys.getfilesystemencoding())
        print('sh.get_filesystem_encoding():', enc)

    def test_z5_get_hostname(self):
        sh = self.sh

        # HOSTNAME_TYPE_Host
        name1 = sh.get_hostname(sh.HOSTNAME_TYPE_Host)
        self.assertEqual(type(name1), str)
        self.assertEqual(name1, sh.get_hostname())
        print('sh.get_hostname(sh.HOSTNAME_TYPE_Host):', name1)

        # HOSTNAME_TYPE_FQDN
        name2 = sh.get_hostname(sh.HOSTNAME_TYPE_FQDN)
        self.assertEqual(type(name2), str)
        print('sh.get_hostname(sh.HOSTNAME_TYPE_FQDN):', name2)

        self.assertEqual(sh.HOSTNAME_TYPE_Host, 1)
        self.assertEqual(sh.HOSTNAME_TYPE_FQDN, 2)
        with self.assertRaises(ValueError):
            sh.get_hostname(3)
        with self.assertRaises(AttributeError):
            sh.HOSTNAME_TYPE_Host = 5
        with self.assertRaises(AttributeError):
            del sh.HOSTNAME_TYPE_Host

    @optional_exception(RuntimeError, 'Unable to get')
    def test_z6_get_username(self):
        username = self.sh.get_username()
        self.assertEqual(type(username), str)
        print('sh.get_username():', username)
        print('sh.home_dir():', self.sh.home_dir())

    @optional_exception(RuntimeError, 'Unable to get')
    def test_z7_is_elevated(self):
        ret = self.sh.is_elevated()
        self.assertEqual(type(ret), bool)
        print('sh.is_elevated():', ret)

if __name__ == '__main__':
    unittest.main()