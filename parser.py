import bs4
import re


class Parser:
	SMS_RECEIVED = 1
	SMS_SENT = 2
	SMS_DRAFT = 3

	def __init__(self, data):
		#set true if search returns a match object
		self.smsXML = True if re.search(b'<smses(?: [^>]*)?>', data) else False

		if self.smsXML:
			data = escapeInvalidXmlCharacters(data)

		self.soup = bs4.BeautifulSoup(data.decode("utf-8"), "xml")


	def getFullContacts(self):
		contactList = self.getContacts()
		self.convertMmsContacts(contactList)
		self.renameUnknownContacts(contactList)

		return contactList


	def getContacts(self):
		contactList = {}

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				number = node["address"]
				ctname = node["contact_name"]

				#will override to latest contact name
				contactList[number] = ctname
		else:
			for call in self.soup.find_all("call"):
				number = call["number"]

				#will override to latest contact name
				contactList[number] = call["contact_name"]
		return contactList


	def count(self):
		counter = {}

		def incr(s, k, sent):
			obj = counter
			if isinstance(s, list):
				for p in s:
					if p not in obj:
						obj[p] = {}
					obj = obj[p]
			else:
				if s not in counter:
					counter[s] = {}
				obj = counter[s]

			if k not in obj:
				obj[k] = {
					"sent": 0,
					"received": 0,
				}

			obj[k]["sent" if sent else "received"] += 1

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				sent = int(node["msg_box" if node.name == "mms" else "type"]) == Parser.SMS_SENT
				numbers, contacts = self.splitMmsContacts(node["address"], node["contact_name"])

				for i in range(len(numbers)):
					incr([node.name, "numbers"], numbers[i], sent)
					incr([node.name, "contacts"], contacts[i], sent)
		else:
			for call in self.soup.find_all("call"):
				sent = int(call["type"]) == Parser.SMS_SENT

				incr(["call", "numbers"], call["number"], sent)
				incr(["call", "contacts"], call["contact_name"], sent)

		return counter


	def convertMmsContacts(self, contactList):
		ctItems = []
		for num, ctname in contactList.items():
			ctItems.append( (num, ctname) )

		for num, ctname in ctItems:
			numbers, contacts = self.splitMmsContacts(num, ctname)
			if len(numbers) > 1:
				for i in range(len(numbers)):
					contactList[numbers[i]] = contacts[i]
				del contactList[num]


	def splitMmsContacts(self, numbers, contacts):
		numberlist = []
		contactlist = []

		if "~" in numbers:
			numberlist.extend(numbers.split("~"))
			contactlist.extend(contacts.split(", "))

			while len(numberlist) >= len(contactlist):
				contactlist.append("(Unknown)")
		else:
			numberlist = [numbers]
			contactlist = [contacts]

		return numberlist, contactlist


	def renameUnknownContacts(self, contactList):
		ctItems = []
		unknownCount = 1
		for num, ctname in contactList.items():
			ctItems.append( (num, ctname) )

		for num, ctname in ctItems:
			if ctname == "(Unknown)":
				contactList[num] = "(Unknown %d)" % unknownCount
				unknownCount += 1


	def removeByFilter(self, clfilter, timefilter, removeFiltered=True, matchesAnyFilter=False):
		removed = False

		def inFilters(num, ctname, seconds):
			hasClFilter = clfilter is not None and len(clfilter) != 0
			hasTimeFilter = timefilter is not None and len(timefilter.timeline) != 0
			b = False

			if matchesAnyFilter:
				b = (hasClFilter and clfilter.hasNumberOrContact(num, ctname)) or (hasTimeFilter and timefilter.inTimeline(seconds))
			else:
				if hasClFilter:
					b = clfilter.hasNumberOrContact(num, ctname)
				if hasTimeFilter:
					if not hasClFilter:
						b = True
					b = b and timefilter.inTimeline(seconds)

			return b if removeFiltered else not b

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				num = node["address"]
				ctname = node["contact_name"]
				#time is stored in milliseconds since epoch
				seconds = int(node["date"]) // 1000

				if inFilters(num, ctname, seconds):
					node.decompose()
					removed = True
		else:
			for call in self.soup.find_all("call"):
				num = call["number"]
				ctname = call["contact_name"]
				#time is stored in milliseconds since epoch
				seconds = int(call["date"]) // 1000

				if inFilters(num, ctname, seconds):
					call.decompose()
					removed = True

		if removed:
			pass
			#self.updateRemove()


	def removeNoDuration(self, clfilter, timefilter):
		if self.smsXML:
			raise Exception("cannot remove no-duration calls from sms file")

		removed = False

		def inFilters(num, ctname, seconds):
			b = (clfilter is not None and clfilter.hasNumberOrContact(num, ctname)) or (timefilter is not None and timefilter.inTimeline(seconds))
			return b if doRemove else not b

		for call in self.soup.find_all("call"):
			#time is stored in milliseconds since epoch
			seconds = int(call["date"]) // 1000

			if inFilters(call["number"], call["contact_name"], seconds):
				continue

			if call["duration"] == "0":
				call.decompose()
				removed = True

		if removed:
			pass
			#self.updateRemove()


	def prettify(self, indent=2, tabs=False):
		lines = self.soup.prettify().split("\n")

		if self.hasStylesheet():
			if self.smsXML:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
			else:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')

		if tabs:
			c = 0
			while c < len(lines):
				line = lines[c]

				i = 0
				while i < len(line) and line[i] == " ":
					i += 1

				if i != 0:
					lines[c] = ("\t" * i) + line[i:]
				c += 1

			output = "\n".join(lines)
		else:
			if indent != 1:
				wspace = re.compile('^(\s*)', re.MULTILINE)
				output = wspace.sub("\\1" * indent, "\n".join(lines))
			else:
				output = "\n".join(lines)
		return output


	def hasStylesheet(self):
		for child in self.soup.children:
			if isinstance(child, bs4.element.XMLProcessingInstruction):
				if str(child).startswith("xml-stylesheet"):
					return True
		return False


	def __str__(self):
		lines = str(self.soup).split("\n")

		if not self.hasStylesheet():
			if self.smsXML:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
			else:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')
		return "\n".join(lines)


def escapeInvalidXmlCharacters(data):
	regex = re.compile(b'&#(\d+|x[\dA-Fa-f]+);')
	newdata = bytearray()
	offset = 0

	for match in re.finditer(regex, data):
		if match.group(1)[0] == "x":
			num = int(match.group(1)[1:], 16)
		else:
			num = int(match.group(1))

		if isValidXML(num):
			newdata += data[offset:match.end()]
		else:
			newdata += data[offset:match.start()] + "&amp;#" + match.group(1) + ";"
		offset = match.end()
	newdata += data[offset:]

	return newdata


def unescapeEscapedAmpersands(data):
	regex = re.compile('body=("[^"]*(?:&amp;#)[^"]*"|\'[^\']*(?:&amp;#)[^\']*\')')
	newdata = ""
	offset = 0

	for match in re.finditer(regex, data):
		newdata += data[offset:match.start()] + data[match.start():match.end()].replace("&amp;#", "&#")
		offset = match.end()
	newdata += data[offset:]

	return newdata


def escapeBodyNewlines(data):
	regex = re.compile('body=("[^"]*\n[^"]*"|\'[^\']*\n[^\']*\')')
	newdata = ""
	offset = 0

	for match in re.finditer(regex, data):
		newdata += data[offset:match.start()] + data[match.start():match.end()].replace("\n", "&#10;")
		offset = match.end()
	newdata += data[offset:]

	return newdata


def isValidXML(c):
	return c == 0x09 or c == 0x0a or c == 0x0d or (c >= 0x20 and c <= 0xd7ff) or (c >= 0xe000 and c <= 0xfffd) or (c >= 0x10000 and c <= 0x10ffff)
