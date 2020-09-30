import time


class ContactListFilter:
	def __init__(self, contactList):
		self.contactList = contactList

		self.numberSet = set(contactList)
		self.contactSet = set(list(map(lambda x: contactList[x], contactList)))

		self.filterNumbers = set()
		self.filterContacts = set()

		self.matchUnknownNumbers = False


	def addNumber(self, number):
		if number not in self.numberSet:
			raise Exception(number + " not found")

		self.filterNumbers.add(number)


	def addContact(self, contact):
		if contact not in self.contactSet:
			raise Exception(contact + " not found")

		self.filterContacts.add(contact)


	def hasNumber(self, number):
		if self.matchUnknownNumbers and len(number) == 0:
			return True

		return number in self.filterNumbers


	def hasContact(self, contact):
		return contact in self.filterContacts


	def hasNumberOrContact(self, number, contact):
		return self.hasNumber(number) or self.hasContact(contact)


	def getNumbersLength(self):
		return len(self.filterNumbers)


	def getContactsLength(self):
		return len(self.filterContacts)


	def __len__(self):
		return self.getNumbersLength() + self.getContactsLength()

