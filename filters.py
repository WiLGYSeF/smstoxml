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

	def invert(self):
		inverted = ContactListFilter(self.contactList)

		ndiff = set()
		cdiff = set()

		if len(self.filterNumbers) != 0 and len(self.filterContacts) != 0:
			ndiff = self.numbersSet - self.filterNumbers
			cdiff = self.contactsSet - self.filterContacts

			#make sure the two sets don't contradict

			for c in self.filterContacts:
				for key, val in self.contactList.items():
					if val == c and key in ndiff:
						ndiff.remove(key)

			for n in self.filterNumbers:
				if self.contactList[n] in cdiff:
					cdiff.remove(self.contactList[n])

			if "(Unknown)" in cdiff:
				cdiff.remove("(Unknown)")

				for key, val in self.contactList.items():
					if val == "(Unknown)" and key not in self.filterNumbers:
						ndiff.add(key)
		elif len(self.filterNumbers) != 0:
			ndiff = self.numberSet - self.filterNumbers
		elif len(self.filterContacts) != 0:
			cdiff = self.contactSet - self.filterContacts

		for num in ndiff:
			inverted.addNumber(num)
		for ct in cdiff:
			inverted.addContact(ct)

		return inverted

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

class TimelineFilter:
	def __init__(self):
		self.timeline = [];

		self.condensed = False
		self.inclusive = True

	def addTimeRange(self, start, end):
		if self.condensed:
			self.expand()

		if isinstance(start, int):
			startTime = start
		else:
			try:
				startTime = int(start)
			except:
				startTime = int(time.mktime(time.strptime(start, "%Y-%m-%d %H:%M:%S")))

		if isinstance(end, int):
			endTime = end
		else:
			try:
				endTime = int(end)
			except:
				endTime = int(time.mktime(time.strptime(end, "%Y-%m-%d %H:%M:%S")))

		if startTime > endTime:
			raise Exception("filter time " + str(start) + " and " + str(end) + " is in wrong order")

		def cmpfunc(x, y):
			if x[0] < y[0]:
				return -1
			if x[0] > y[0]:
				return 1

			if x[1] > y[1]:
				return -1
			if x[1] < y[1]:
				return 1
			return 0

		insertarr(self.timeline, ( startTime, 0 ), cmpfunc, unique=True)
		insertarr(self.timeline, ( endTime, 1 ), cmpfunc, unique=True)

	def condense(self):
		if self.condensed:
			return

		condensed = []
		length = len(self.timeline)

		i = 0
		while i < length:
			startTime = self.timeline[i][0]

			if self.timeline[i][1] == 1 and i < length - 1 and self.timeline[i + 1][0] == startTime:
				condensed.append( (startTime, startTime) )
				i += 2
				continue

			i += 1

			while True:
				changed = False

				while i < length and self.timeline[i][1] == 0:
					changed = True
					i += 1

				while i < length - 1 and self.timeline[i + 1][1] == 1:
					changed = True
					i += 1

				while i < length - 1 and self.timeline[i][0] == self.timeline[i + 1][0]:
					changed = True
					i += 1

				if not changed or i == length:
					break

			if i == length:
				i -= 1

			endTime = self.timeline[i][0]

			condensed.append( (startTime, endTime) )
			i += 1

		self.timeline = condensed
		self.condensed = True

	def expand(self):
		if not self.condensed:
			return

		expanded = []
		length = len(self.timeline)

		i = 0
		while i < length:
			startTime = self.timeline[i][0]
			endTime = self.timeline[i][1]

			expanded.append( (startTime, 0) )
			expanded.append( (endTime, 1) )

		self.timeline = expanded
		self.condensed = False

	def invert(self):
		inverted = TimelineFilter()
		inverted.inclusive = not self.inclusive

		length = len(self.timeline)
		i = 0

		if not self.condensed:
			self.condense()

		while i < length:
			if i == 0:
				startTime = 0
				endTime = self.timeline[0][0]

				if endTime != 0:
					inverted.addTimeRange(0, max(endTime, 0))
			if i == length - 1:
				endTime = self.timeline[i][1]
				#end of time?
				uint32max = 2 ** 32 - 1

				if endTime != uint32max:
					inverted.addTimeRange(endTime, uint32max)
				break

			startTime = self.timeline[i][1]
			endTime = self.timeline[i + 1][0]

			if startTime < endTime:
				inverted.addTimeRange(startTime, endTime)

			i += 1

		return inverted

	def __len__(self):
		return len(self.timeline)

	def inTimeline(self, time):
		if not self.condensed:
			self.condense()

		time = int(time)

		for times in self.timeline:
			if time > times[0] and time < times[1]:
					return True

			if self.inclusive:
				if time == times[0] or time == times[1]:
					return True
			else:
				if times[0] == times[1] and time == time[0]:
					return True
		return False

def insertarr(arr, value, cmpfunc, unique=False):
	length = len(arr)
	low = 0
	high = length

	#insert into sorted array

	while low < high:
		mid = (low + high) // 2
		cval = cmpfunc(arr[mid], value)
		if cval < 0:
			low = mid + 1
		elif cval > 0:
			high = mid
		else:
			low = mid + 1
			break

	if not unique or low >= length or arr[low] != value:
		arr.insert(low, value)
