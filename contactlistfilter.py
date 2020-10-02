import re


class ContactListFilter:
	def __init__(self, contactList):
		self.contactList = contactList

		self.numberSet = set(contactList)
		self.contactSet = set(map(lambda x: contactList[x], contactList))

		self.filterNumbers = set()
		self.filterContacts = set()

		self.filterNumbersRegex = []
		self.filterContactsRegex = []

	def addNumber(self, number):
		#if number not in self.numberSet:
		#	raise Exception(number + " not found")
		self.filterNumbers.add(number)


	def addNumberExpr(self, expr):
		self.filterNumbersRegex.append(re.compile(expr))


	def addContact(self, contact):
		#if contact not in self.contactSet:
		#	raise Exception(contact + " not found")
		self.filterContacts.add(contact)


	def addContactExpr(self, expr):
		self.filterContactsRegex.append(re.compile(expr))


	def hasNumber(self, number):
		if number in self.filterNumbers:
			return True

		for expr in self.filterNumbersRegex:
			if expr.match(number):
				return True
		return False


	def hasContact(self, contact):
		if contact in self.filterContacts:
			return True

		for expr in self.filterContactsRegex:
			if expr.match(contact):
				return True
		return False


	def hasNumberOrContact(self, number, contact):
		return self.hasNumber(number) or self.hasContact(contact)


	def isEmpty(self):
		return len(self.filterNumbers) + len(self.filterNumbersRegex) + len(self.filterContacts) + len(self.filterContactsRegex) == 0
