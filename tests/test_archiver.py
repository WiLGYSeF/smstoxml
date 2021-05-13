import hashlib
import os
import unittest

import archiver

NAME = 'name'
DATA = 'data'
FILEDATA = [{NAME: 'test.txt', DATA: b'This is a test'}, {NAME: 'aaa.txt', DATA: b'abcdefghijklmnopqrstuvwxyz'}]

MD5SUM_TAR = 'd9c40a73b8c87d10e1fa7e0db19611bd'
MD5SUM_TGZ = 'ff8b4549ff0cce06fe188b779d19de1c'
MD5SUM_ZIP = '608155f1b80c75d063862d380222083e'


class ArchiverTest(unittest.TestCase):
    def setUp(self):
        pass

    def create_compare(self, ar, fhash):
        for f in FILEDATA:
            ar.addFile(f[NAME], f[DATA])
        ar.close()

        with open(ar.name, 'rb') as f:
            data = f.read()
        os.remove(ar.name)

        self.assertEqual(hashlib.md5(data).hexdigest(), fhash)

    def test_tar_archive(self):
        self.create_compare(archiver.Archiver('tmp.tar', type_='tar'), MD5SUM_TAR)

    def test_tgz_archive(self):
        self.create_compare(archiver.Archiver('tmp.tgz', type_='tgz'), MD5SUM_TGZ)

    def test_zip_archive(self):
        self.create_compare(archiver.Archiver('tmp.zip', type_='zip'), MD5SUM_ZIP)

    def test_tar_guess_archive(self):
        self.create_compare(archiver.Archiver('tmp.tar'), MD5SUM_TAR)

    def test_tgz_guess_archive(self):
        self.create_compare(archiver.Archiver('tmp.tgz'), MD5SUM_TGZ)

    def test_zip_guess_archive(self):
        self.create_compare(archiver.Archiver('tmp.zip'), MD5SUM_ZIP)
