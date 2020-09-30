import bs4
import re


class Parser:
	def __init__(self, data):
		#set true if search returns a match object
		self.smsXML = True if re.search(b'<smses(?: [^>]*)?>', data) else False

		if self.smsXML:
			data = escapeInvalidXmlCharacters(data)

		self.soup = bs4.BeautifulSoup(data.decode("utf-8"), "xml")


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

		ctItems = []
		for num, ctname in contactList.items():
			ctItems.append( (num, ctname) )

		for num, ctname in ctItems:
			if "~" in num:
				numspl = num.split("~")
				ctnamespl = ctname.split(", ")

				if len(numspl) >= len(ctnamespl):
					for i in range(len(numspl)):
						if i < len(ctnamespl):
							ctsub = ctnamespl[i]
						else:
							ctsub = "(Unknown)"

						contactList[numspl[i]] = ctsub
					del contactList[num]

		return contactList


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

			output = "\n".join(lines).encode("utf-8")
		else:
			if indent != 1:
				wspace = re.compile(b'^(\s*)', re.MULTILINE)
				output = wspace.sub(b"\\1" * indent, "\n".join(lines).encode("utf-8"))
			else:
				output = "\n".join(lines).encode("utf-8")
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


def isValidXML(c):
	return c == 0x09 or c == 0x0a or c == 0x0d or (c >= 0x20 and c <= 0xd7ff) or (c >= 0xe000 and c <= 0xfffd) or (c >= 0x10000 and c <= 0x10ffff)
