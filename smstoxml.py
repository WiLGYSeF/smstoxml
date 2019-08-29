#requires python3-bs4, python3-pil, python3-lxml

import parser
from parser import Parser

import re
import sys

def main(argv):
	infname = None
	outfname = None

	filterContacts = set()
	filterNumbers = set()
	replaceNumbers = {}

	listStats = False
	removeFiltered = False
	keepFiltered = False
	removeNoDuration = False
	listContacts = False
	revert = False
	doConvert = True
	stripAttr = False
	extractfname = None

	imageWidth = -1
	imageHeight = -1
	jpgQuality = -1

	removeComments = False
	indentation = 1

	if len(argv) > 1:
		i = 1
		parse = True

		while i < len(argv):
			arg = argv[i]

			if arg == "--":
				parse = False
				i += 1
				continue

			if not parse:
				if infname is None:
					infname = arg
				else:
					outfname = arg

				i += 1
				continue

			if arg == "-h" or arg == "--help":
				printHelp()
				exit(0)
			elif arg == "--statistics":
				listStats = True
			elif arg == "-l" or arg == "--list":
				listContacts = True
			elif arg == "-f" or arg == "--filter-contact":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				filterContacts.add(argv[i + 1])
				i += 1
			elif arg == "-g" or arg == "--filter-number":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				filterNumbers.add(argv[i + 1])
				i += 1
			elif arg == "--replace-number":
				if i == len(argv) - 2:
					printHelp()
					exit(1)

				replaceNumbers[argv[i + 1]] = argv[i + 2]
				i += 2
			elif arg == "--remove-filtered":
				removeFiltered = True
			elif arg == "--remove-no-duration":
				removeNoDuration = True
			elif arg == "--remove-comments":
				removeComments = True
			elif arg == "--keep-filtered":
				keepFiltered = True
			elif arg == "-r" or arg == "--revert":
				revert = True
			elif arg == "--no-convert":
				doConvert = False
			elif arg == "-s" or arg == "--strip":
				stripAttr = True
			elif arg == "--indent":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				if argv[i + 1].lower() == "tab" or argv[i + 1].lower() == "tabs" or argv[i + 1].lower() == "t":
					indentation = "tab"
				else:
					indentation = int(argv[i + 1])
				i += 1
			elif arg == "-e" or arg == "--extract-media":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				extractfname = argv[i + 1]
				i += 1
			elif arg == "--image-width":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				imageWidth = int(argv[i + 1])
				i += 1
			elif arg == "--image-height":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				imageHeight = int(argv[i + 1])
				i += 1
			elif arg == "--jpg-quality":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				jpgQuality = int(argv[i + 1])
				i += 1
			elif arg[0] == "-":
				print("Error: unknown argument " + arg, file=sys.stderr)
				exit(1)
			else:
				if infname is None:
					infname = arg
				else:
					if outfname is None:
						outfname = arg
					else:
						print("Error: too many filenames", file=sys.stderr)
						exit(1)
			i += 1

	if infname is None:
		printHelp()
		exit(1)

	if removeFiltered and keepFiltered:
		print("Error: both --remove-filtered and --keep-filtered specified", file=sys.stderr)
		print("")
		printHelp()
		exit(1)

	parserObj = None

	try:
		infile = open(infname, "r", encoding="utf8")
		data = infile.read()

		parserObj = Parser(data)

		infile.close()
	except Exception as e:
		print("Error: could not read file: " + infname + ". " + str(e), file=sys.stderr)
		exit(1)

	contactsList = parserObj.getContacts()
	numbersSet = set(contactsList)
	contactsSet = set(list(map(lambda x: contactsList[x], contactsList)))

	if len(filterContacts) != 0:
		noexist = filterContacts - contactsSet

		if len(noexist) != 0:
			for v in noexist:
				print(v + ": not found", file=sys.stderr)
			filterContacts = filterContacts - noexist

	if len(filterNumbers) != 0:
		noexist = filterNumbers - set(contactsList)

		if len(noexist) != 0:
			for v in noexist:
				print(v + ": not found", file=sys.stderr)
			filterNumbers = filterNumbers - noexist

	if removeNoDuration:
		parserObj.removeNoDuration(filterContacts, filterNumbers)

	if len(replaceNumbers) != 0:
		for contact in replaceNumbers:
			parserObj.replaceNumber(contact, replaceNumbers[contact])

	if len(filterContacts) != 0 or len(filterNumbers) != 0:
		if removeFiltered:
			parserObj.removeByFilter(filterContacts, filterNumbers)
		elif keepFiltered:
			cdiff = set()
			ndiff = set()

			if len(filterContacts) != 0 and len(filterNumbers) != 0:
				cdiff = contactsSet - filterContacts
				ndiff = numbersSet - filterNumbers

				#make sure the two sets don't contradict

				for c in filterContacts:
					for key, val in contactsList.items():
						if val == c and key in ndiff:
							ndiff.remove(key)

				for n in filterNumbers:
					if contactsList[n] in cdiff:
						cdiff.remove(contactsList[n])

				if "(Unknown)" in cdiff:
					cdiff.remove("(Unknown)")

					for key, val in contactsList.items():
						if val == "(Unknown)" and key not in filterNumbers:
							ndiff.add(key)
			elif len(filterContacts) != 0:
				cdiff = contactsSet - filterContacts
			else:
				ndiff = numbersSet - filterNumbers

			parserObj.removeByFilter(cdiff, ndiff)

	if listStats:
		#refresh list
		contactsList = parserObj.getContacts()

		ctcount, numcount, mmscount = parserObj.countByFilter(filterContacts, filterNumbers)
		totalCount = 0

		for ct in ctcount:
			totalCount += ctcount[ct]
		for num in numcount:
			if contactsList[num] in ctcount:
				continue

			totalCount += numcount[num]

		print(infname + ":")
		print("Total Count: " + str(totalCount))
		print("")

		for num in numcount:
			print(num + "," + contactsList[num] + ": " + str(numcount[num]))

		for ct in ctcount:
			num = None
			for n in contactsList:
				if contactsList[n] == ct:
					num = n
					break
			if num in numcount:
				continue

			print(num + "," + ct + ": " + str(ctcount[ct]))

		totalMmsCount = 0
		for mms in mmscount:
			totalMmsCount += mmscount[mms]

		if totalMmsCount > 0:
			print("")
			print("MMS Total Count: " + str(totalMmsCount))

			for mms in mmscount:
				print(mms + "," + contactsList[mms] + ": " + str(mmscount[mms]))


		print("")
		exit(0)

	if listContacts:
		#refresh list
		contactsList = parserObj.getContacts()

		sys.stdout.buffer.write("\n".join(list(map(lambda x: x + "," + contactsList[x], contactsList))).encode("utf-8"))
		print("")
		exit(0)

	if imageWidth != -1 or imageHeight != -1 or jpgQuality != -1:
		parserObj.optimizeImages(filterContacts, filterNumbers, imageWidth, imageHeight, jpgQuality)

	if extractfname is not None:
		parserObj.extractMedia(extractfname, set(), filterContacts, filterNumbers)
		exit(0)

	if stripAttr:
		parserObj.stripAttrs()

	if removeComments:
		parserObj.removeComments()

	usetabs = indentation == "tab"

	output = parserObj.prettify(indent=indentation, tabs=usetabs)

	if revert or not doConvert:
		output = parser.unescapeInvalidXmlCharacters(output)

	if outfname is not None:
		try:
			outfile = open(outfname, "w", encoding="utf8")
			outfile.write(output)
			outfile.close()
		except Exception as e:
			print("Error: could not write file: " + outfname + ". " + str(e), file=sys.stderr)
			exit(1)
	else:
		sys.stdout.buffer.write(output.encode("utf-8"))
		print("")

def printHelp():
	print(
		"SMSBackupXML to valid XML converter\n"
		"Usage: smstoxml.py [input] [output] options...\n"
		"\n"
		"  -h, --help                          shows this help menu\n"
		"  --statistics                        display statistics of sms/calls\n"
		"  -l, --list                          list the contacts in the file and exit\n"
		"  -f, --filter-contact [name]         use this contact filter for other options\n"
		"  -g, --filter-number [number]        use this number filter for other options\n"
		"  --replace-number [contact] [num]    replace the number for all contact\n"
		"                                        references for grouping purposes\n"
		"  --remove-filtered                   remove the contacts/numbers in the filter\n"
		"  --remove-no-duration                remove zero duration calls for call.xml\n"
		"                                        files, treats filter as keep\n"
		"  --remove-comments                   remove comments from the output xml file\n"
		"  --keep-filtered                     remove contacts/numbers not in the filter\n"
		"\n"
		"  -r, --revert                        convert valid XML back to SMSBackupXML\n"
		"  --no-convert                        do not convert XML, converts by default\n"
		"\n"
		"  -s, --strip                         strip unnecessary attributes from nodes,\n"
		"                                        may make file unrestorable (unlikely)\n"
		"  --indent [value]                    number of spaces for indentation,\n"
		"                                        or 'tab'\n"
		"\n"
		"  -e, --extract-media [file]          extract media to zip file and exit\n"
		"  --image-width [value]               set maximum image width\n"
		"  --image-height [value]              set maximum image height\n"
		"  --jpg-quality [value]               set jpg image quality\n"
	)

if __name__ == "__main__":
	main(sys.argv)
