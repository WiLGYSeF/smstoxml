import bs4
import re


class Parser:
	def __init__(self, data):
		#set true if search returns a match object
		self.smsXML = True if re.search(r'<smses(?: [^>]*)?>', data) else False

		if self.smsXML:
			data = escapeInvalidXmlCharacters(data)

		self.soup = bs4.BeautifulSoup(data, "xml")


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


def escapeInvalidXmlCharacters(data):
	regex = re.compile(r'&#(\d+|x[\dA-Fa-f]+);')
	newdata = ""
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


def isValidXML(c):
	return c == 0x09 or c == 0x0a or c == 0x0d or (c >= 0x20 and c <= 0xd7ff) or (c >= 0xe000 and c <= 0xfffd) or (c >= 0x10000 and c <= 0x10ffff)
