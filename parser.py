import base64
import bs4
import io
import mimetypes
from PIL import Image
import re
import sys
import tarfile
import zipfile

class Parser:
	SMS_RECEIVED = 1
	SMS_SENT = 2
	SMS_DRAFT = 3

	def __init__(self, data):
		self.smsXML = True if re.search(r'<smses(?: [^>]*)?>', data) else False

		if self.smsXML:
			data = escapeInvalidXmlCharacters(data)
			data = escapeBodyNewlines(data)

		self.soup = bs4.BeautifulSoup(data, "xml")

	def getContacts(self):
		contacts = {}
		unknownnumbers = 1

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				num, ctname = self.spljoinNumbers(node["address"], node["contact_name"])

				if len(num) == 0:
					unknown = "(Unknown%d)" % unknownnumbers
					unknownnumbers += 1

				#will override to latest contact name
				contacts[num] = ctname
		else:
			for call in self.soup.find_all("call"):
				num = call["number"]

				if len(num) == 0:
					num = "(Unknown%d)" % unknownnumbers
					unknownnumbers += 1

				#will override to latest contact name
				contacts[num] = call["contact_name"]

		return contacts

	def count(self):
		#ctcount = {}
		numcount = {}
		mmscount = {}
		unknownnumbers = 1

		def incrEntry(d, k, b):
			if k not in d:
				d[k] = [0, 0]
			if b:
				d[k][0] += 1
			else:
				d[k][1] += 1

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				if node.name == "mms":
					sent = int(node["msg_box"]) == Parser.SMS_SENT
				else:
					sent = int(node["type"]) == Parser.SMS_SENT

				#incrEntry(ctcount, node["contact_name"], sent)

				number, _ = self.spljoinNumbers(node["address"], node["contact_name"])
				if len(number) == 0:
					number = "(Unknown%d)" % unknownnumbers
					unknownnumbers += 1

				incrEntry(numcount, number, sent)

				if node.name == "mms":
					incrEntry(mmscount, number, sent)
		else:
			for call in self.soup.find_all("call"):
				sent = int(call["type"]) == Parser.SMS_SENT

				#incrEntry(ctcount, call["contact_name"], sent)

				number = call["number"]
				if len(number) == 0:
					number = "(Unknown%d)" % unknownnumbers
					unknownnumbers += 1

				incrEntry(numcount, number, sent)

		#return (ctcount, numcount, mmscount)
		return (numcount, mmscount)

	def removeByFilter(self, clfilter, timefilter):
		removed = False

		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				#time is stored in milliseconds since epoch
				seconds = int(node["date"]) // 1000

				if clfilter.hasNumberOrContact(node["address"], node["contact_name"]) or timefilter.inTimeline(seconds):
					node.decompose()
					removed = True
		else:
			for call in self.soup.find_all("call"):
				#time is stored in milliseconds since epoch
				seconds = int(call["date"]) // 1000

				if clfilter.hasNumberOrContact(call["number"], call["contact_name"]) or timefilter.inTimeline(seconds):
					call.decompose()
					removed = True

		if removed:
			self.updateRemove()

	def replaceNumber(self, contact, number, timefilter):
		if self.smsXML:
			for node in self.soup.find_all(["sms", "mms"]):
				#time is stored in milliseconds since epoch
				seconds = int(node["date"]) // 1000

				if len(timefilter) != 0 and not timefilter.inTimeline(seconds):
					continue

				if node.name == "mms":
					numbers, contacts = self.splitNumbers(node["address"], node["contact_name"])

					for i in range(len(contacts)):
						if contacts[i] == contact:
							numbers[i] = number_class
							break

					numberstr, contactstr = self.joinNumbers(numbers, contacts)
					node["address"] = numberstr
					node["contact_name"] = contactstr
				elif node["contact_name"] == contact:
					node["address"] = number
		else:
			for call in self.soup.find_all("call"):
				#time is stored in milliseconds since epoch
				seconds = int(call["date"]) // 1000

				if len(timefilter) != 0 and not timefilter.inTimeline(seconds):
					continue

				if call["contact_name"] == contact:
					call["number"] = number

	def splitNumbers(self, numberstr, contactstr):
		numbers = numberstr.split("~")
		contacts = contactstr.split(", ")

		diff = len(numbers) - len(contacts)
		for i in range(diff):
			contacts.append("(Unknown)")

		return ( numbers, contacts )

	def joinNumbers(self, numbers, contacts):
		return ( "~".join(numbers), ", ".join(contacts))

	def spljoinNumbers(self, numbers, contacts):
		n, c = self.splitNumbers(numbers, contacts)
		return self.joinNumbers(n, c)

	def removeNoDuration(self, clfilter, timefilter):
		if self.smsXML:
			raise Exception("cannot remove no-duration calls from sms file")

		removed = False

		for call in self.soup.find_all("call"):
			#time is stored in milliseconds since epoch
			seconds = int(call["date"]) // 1000

			if clfilter.hasNumberOrContact(call["number"], call["contact_name"]) or timefilter.inTimeline(seconds):
				continue

			if call["duration"] == "0":
				call.decompose()
				removed = True

		if removed:
			self.updateRemove()

	def updateRemove(self):
		if self.smsXML:
			nodes = self.soup.find("smses").contents
		else:
			nodes = self.soup.find("calls").contents

		i = 0
		nlen = len(nodes)

		while i < nlen:
			node = nodes[i]
			if i < nlen - 1 and isinstance(node, bs4.element.NavigableString) and node == "\n":
				#find extra newlines and delete them
				j = i + 1
				while j < nlen and isinstance(nodes[j], bs4.element.NavigableString) and nodes[j] == "\n":
					#NavigableString has no decompose()
					nodes[j].extract()
					nlen -= 1
			i += 1

		if self.smsXML:
			smses = self.soup.find("smses")
			smses["count"] = len(self.soup.find_all("sms")) + len(self.soup.find_all("mms"))
		else:
			calls = self.soup.find("calls")
			calls["count"] = len(self.soup.find_all("call"))

	def stripAttrs(self, aggressive=False):
		if self.smsXML:
			for node in self.soup.find_all("sms"):
				KEEPATTR = set(["address", "body", "contact_name", "date", "date_sent", "read", "readable_date", "type"])

				attrs = node.attrs.copy()
				for attr in node.attrs:
					if attr not in KEEPATTR:
						del(attrs[attr])
				node.attrs = attrs

			for node in self.soup.find_all("part"):
				KEEPATTR = set(["chset", "cid", "cl", "ct", "data", "name", "seq", "text"])

				attrs = node.attrs.copy()
				for attr in node.attrs:
					if attr not in KEEPATTR:
						del(attrs[attr])
				node.attrs = attrs

				#strip out crlf from mms part formatting
				if "text" in node.attrs and "seq" in node.attrs and node.attrs["seq"] == "-1":
					node.attrs["text"] = node.attrs["text"].replace("&#13;&#10;", "")
		else:
			for node in self.soup.find_all("call"):
				KEEPATTR = set(["contact_name", "date", "duration", "number", "readable_date", "type"])

				attrs = node.attrs.copy()
				for attr in node.attrs:
					if attr not in KEEPATTR:
						del(attrs[attr])
				node.attrs = attrs

	def extractMedia(self, arname, skiptype, clfilter, timefilter):
		if not self.smsXML:
			raise Exception("cannot extract media from call file")

		mimetypes_dict = {
			"audio/mpeg": "mp2",
			"image/bmp": "bmp",
			"image/gif": "gif",
			"image/jpeg": "jpg",
			"image/png": "png",
			"image/svg+xml": "svg",
			"image/tiff": "tiff",
			"text/html": "txt",
			"video/mpeg": "mpg",
			"video/quicktime": "mov",
			"video/webm": "webm",
			"video/x-msvideo": "avi",
			"video/x-sgi-movie": "movie",
		}

		if arname.endswith(".tgz") or arname.endswith(".tar.gz"):
			ar = tarfile.open(arname, "w:gz")
			atype = "tgz"
		else:
			ar = zipfile.ZipFile(arname, "w")
			atype = "zip"
		usednames = set()

		for node in self.soup.find_all("part"):
			mtype = node["ct"]
			if mtype == "application/smil":
				continue

			#node["data"] doesnt exist anymore?
			if "data" not in node.attrs:
				continue

			mmsparent = node.parent.parent
			if clfilter != None and len(clfilter) != 0:
				if not clfilter.hasNumberOrContact(mmsparent["address"], mmsparent["contact_name"]):
					continue

			#time is stored in milliseconds since epoch
			seconds = int(mmsparent["date"]) // 1000
			if timefilter != None and len(timefilter) != 0 and not timefilter.inTimeline(seconds):
				continue

			if mtype in skiptype:
				continue

			if "name" in node:
				name = node["name"]
				spl = name.split(".")
				fname = ".".join(spl[0:-1])
				ext = spl[-1]

				inc = 1
				while name in usednames:
					name = fname + "_" + str(inc) + "." + ext
					inc += 1
			else:
				ext = mimetypes_dict.get(mtype, mimetypes.guess_extension(mtype))
				name = mmsparent["date"] + "-" + mmsparent["contact_name"] + "." + ext

				inc = 1
				while name in usednames:
					name = mmsparent["date"] + "-" + mmsparent["contact_name"] + "_" + str(inc) + "." + ext
					inc += 1

			data = base64.b64decode(node.attrs["data"])
			sio = io.BytesIO(data)

			if atype == "tgz":
				tarinfo = tarfile.TarInfo(name=str(name))
				tarinfo.size = len(data)
				ar.addfile(tarinfo, sio)
			else:
				ar.writestr(name, sio.getvalue())
			usednames.add(name)

		ar.close()

	def optimizeImages(self, clfilter, timefilter, maxWidth, maxHeight, jpgQuality, shrinkOnly):
		if not self.smsXML:
			raise Exception("cannot optimize images from call file")

		mimetypes_dict = {
			"image/bmp": "bmp",
			"image/gif": "gif",
			"image/jpeg": "jpeg",
			"image/png": "png",
			"image/svg+xml": "svg",
			"image/tiff": "tiff"
		}

		for node in self.soup.find_all("part"):
			mtype = node["ct"]
			if mtype == "application/smil":
				continue

			#node["data"] doesnt exist anymore?
			if "data" not in node.attrs:
				continue

			mmsparent = node.parent.parent
			if clfilter != None and len(clfilter) != 0:
				if not clfilter.hasNumberOrContact(mmsparent["address"], mmsparent["contact_name"]):
					continue

			#time is stored in milliseconds since epoch
			seconds = int(mmsparent["date"]) // 1000
			if timefilter != None and len(timefilter) != 0 and not timefilter.inTimeline(seconds):
				continue

			if mtype in mimetypes_dict:
				changed = False

				data = base64.b64decode(node.attrs["data"])
				sio = io.BytesIO(data)
				img = Image.open(sio)

				if maxWidth != -1 or maxHeight != -1:
					if maxWidth == -1:
						maxWidth = img.width
					if maxHeight == -1:
						maxHeight = img.height

					if maxWidth < img.width or maxHeight < img.height:
						img.thumbnail( (maxWidth, maxHeight), Image.ANTIALIAS)
						changed = True

				tmpbuf = io.BytesIO()
				if mtype == "image/jpeg":
					if jpgQuality == -1:
						jpgQuality = "keep"
					else:
						changed = True

					if changed:
						img.save(tmpbuf, format=mimetypes_dict[mtype], optimize=True, quality=jpgQuality)
				else:
					img.save(tmpbuf, format=mimetypes_dict[mtype], optimize=True)
					changed = True

				if changed:
					if not shrinkOnly or sio.getbuffer().nbytes > tmpbuf.getbuffer().nbytes:
						newdata = base64.b64encode(tmpbuf.getvalue()).decode("ascii")
						node.attrs["data"] = newdata
					else:
						mmselement = node.parent.parent
						print("img: " + mmselement.attrs["address"] + ' "' + mmselement.attrs["contact_name"].replace('"', '\\"') + '" ' + mmselement.attrs["readable_date"] + ": image did not shrink!", file=sys.stderr)

	def removeComments(self, root=None):
		if root is None:
			root = self.soup

		for node in root:
			if isinstance(node, bs4.element.Comment):
				#Comment has no decompose()
				node.extract()
			else:
				try:
					if len(list(node.children)) > 0:
						self.removeComments(node)
				except:
					pass

	def hasStylesheet(self):
		for child in self.soup.children:
			if isinstance(child, bs4.element.XMLProcessingInstruction):
				if str(child).startswith("xml-stylesheet"):
					return True
		return False

	def prettify(self, indent=2, tabs=False):
		lines = self.soup.prettify().split("\n")

		if not self.hasStylesheet():
			if self.smsXML:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
			else:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')

		if tabs:
			length = len(lines)
			c = 0

			while c < length:
				line = lines[c]
				linelen = len(line)

				i = 0
				while i < linelen and line[i] == " ":
					i += 1

				if i != 0:
					lines[c] = ("\t" * i) + line[i:]
				c += 1

			output = "\n".join(lines)
		else:
			if indent != 1:
				wspace = re.compile(r'^(\s*)', re.MULTILINE)
				output = wspace.sub("\\1" * indent, "\n".join(lines))
			else:
				output = "\n".join(lines)
		return output

	def __str__(self):
		lines = str(self.soup).split("\n")

		if not self.hasStylesheet():
			if self.smsXML:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
			else:
				lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')
		return "\n".join(lines)

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

def unescapeInvalidXmlCharacters(data):
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
