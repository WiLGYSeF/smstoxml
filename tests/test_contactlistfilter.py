import hashlib
import os
import unittest

import contactlistfilter


class ContactListFilterTest(unittest.TestCase):
    def test_has_number(self):
        clf = contactlistfilter.ContactListFilter()

        num = '0000000000'
        clf.addNumber(num)

        self.assertTrue(clf.hasNumber(num))
        self.assertFalse(clf.hasNumber('1234567890'))

        clf.addNumberExpr('1{10}')
        self.assertTrue(clf.hasNumber('1111111111'))

    def test_has_contact(self):
        clf = contactlistfilter.ContactListFilter()

        ct = 'abc'
        clf.addContact(ct)

        self.assertTrue(clf.hasContact(ct))
        self.assertFalse(clf.hasContact('Not Here'))

        clf.addContactExpr('ye{2}t')
        self.assertTrue(clf.hasContact('yeet'))

    def test_has_number_or_contact(self):
        clf = contactlistfilter.ContactListFilter()

        num = '0000000000'
        ct = 'abc'

        clf.addNumber(num)
        clf.addContact(ct)

        self.assertTrue(clf.hasNumberOrContact(num, ct))
        self.assertTrue(clf.hasNumberOrContact('1234567890', ct))
        self.assertTrue(clf.hasNumberOrContact(num, 'Not Here'))
        self.assertFalse(clf.hasNumberOrContact('1234567890', 'Not Here'))

    def test_is_empty(self):
        clf = contactlistfilter.ContactListFilter()
        self.assertTrue(clf.isEmpty())

        clf.addNumber('0000000000')
        self.assertFalse(clf.isEmpty())
