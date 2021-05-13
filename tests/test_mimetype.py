import unittest

import mimetype


class MimetypeTest(unittest.TestCase):
    def test_guess_mimetype_extension_dict(self):
        self.assertEqual(mimetype.guessExtension('image/jpeg'), 'jpg')

    def test_guess_mimetype_extension_guess(self):
        self.assertEqual(mimetype.guessExtension('application/zip'), 'zip')

    def test_guess_mimetype_extension_fail(self):
        self.assertIsNone(mimetype.guessExtension('???'))
