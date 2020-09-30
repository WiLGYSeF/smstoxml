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


class TimelineFilter:
	def __init__(self):
		self.timeline = []

		self.condensed = False

		self.inclusive = True


	def addTimeRange(self, start, end, dateformat="%Y-%m-%d %H:%M:%S"):
		def convertToTime(x):
			if isinstance(x, int):
				return x
			else:
				try:
					return int(x)
				except:
					return int(time.mktime(time.strptime(x, dateformat)))

		startTime = convertToTime(start)
		endTime = convertToTime(end)

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

		# 0 for start time, 1 for end time
		insertarr(self.timeline, ( startTime, 0 ), cmpfunc, unique=True)
		insertarr(self.timeline, ( endTime, 1 ), cmpfunc, unique=True)
		self.condensed = False


	def condense(self):
		condensedTimeline = []
		idx = 0

		def traverse(idx):
			while idx < len(self.timeline) and self.timeline[idx][1] == 0:
				idx += 1

			while idx < len(self.timeline) and self.timeline[idx][1] == 1:
				end = self.timeline[idx][0]
				idx += 1

			last = None
			while idx < len(self.timeline) and self.timeline[idx][0] == end:
				last = self.timeline[idx]
				idx += 1

			if last is not None and last[1] == 0:
				return traverse(idx)
			return idx

		while idx < len(self.timeline):
			start = self.timeline[idx][0]
			end = None

			idx = traverse(idx + 1)
			end = self.timeline[idx - 1][0]

			condensedTimeline.append( ( start, 0 ) )
			condensedTimeline.append( ( end, 1 ) )

		self.timeline = condensedTimeline
		self.condensed = True


	def invert(self, minStart=0, maxEnd=2 ** 32 - 1):
		if not self.condensed:
			self.condense()

		inverted = TimelineFilter()
		inverted.inclusive = not self.inclusive
		inverted.condensed = True

		endTime = self.timeline[0][0]

		if endTime > minStart:
			inverted.addTimeRange(minStart, endTime)

		idx = 1
		while idx < len(self.timeline) - 1:
			startTime = self.timeline[idx][0]
			endTime = self.timeline[idx + 1][0]

			if startTime < endTime:
				inverted.addTimeRange(startTime, endTime)

			idx += 2

		endTime = self.timeline[-1][0]
		if endTime < maxEnd:
			inverted.addTimeRange(endTime, maxEnd)

		return inverted


	def __len__(self):
		return len(self.timeline)


	def inTimeline(self, time):
		if not self.condensed:
			self.condense()

		idx = 0
		while idx < len(self.timeline) - 1:
			if self.timeline[idx][0] < time and self.timeline[idx + 1][0] > time:
				return True
			if self.inclusive and (self.timeline[idx][0] == time or self.timeline[idx + 1][0] == time):
				return True
			idx += 2
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
