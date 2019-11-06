#requires python3-bs4, python3-pil, python3-lxml

import filters
import parser
from parser import Parser

import re
import sys
import time

def main(argv):
	infname = None
	outfname = None

	#filters
	contactFilterList = set()
	numberFilterList = set()

	timeFilter = filters.TimelineFilter()

	replaceNumbers = {}

	#options
	listContacts = False
	listStats = False
	sortContacts = False
	sortNumbers = False
	normalize = False
	removeFiltered = False
	keepFiltered = False
	removeNoDuration = False
	revert = False
	doConvert = True
	stripAttr = False
	extractfname = None
	removeComments = False
	indentation = 1

	#image optimization options
	optimizeImages = False
	imageWidth = -1
	imageHeight = -1
	jpgQuality = -1
	shrinkOnly = False

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
			elif arg == "--sort-contacts":
				sortContacts = True
			elif arg == "--sort-numbers":
				sortNumbers = True
			elif arg == "-f" or arg == "--filter-contact":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				contactFilterList.add(argv[i + 1])
				i += 1
			elif arg == "-g" or arg == "--filter-number":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				numberFilterList.add(argv[i + 1])
				i += 1
			elif arg == "-t" or arg == "--filter-time":
				if i == len(argv) - 2:
					printHelp()
					exit(1)

				try:
					timeFilter.addTimeRange(argv[i + 1], argv[i + 2])
				except Exception as e:
					print("Error: " + str(e), file=sys.stderr)
					exit(1)

				i += 2
			elif arg == "--replace-number":
				if i == len(argv) - 2:
					printHelp()
					exit(1)

				replaceNumbers[argv[i + 1]] = argv[i + 2]
				i += 2
			elif arg == "--normalize":
				normalize = True
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
					try:
						indentation = int(argv[i + 1])
					except:
						print("Error: invalid indentation", file=sys.stderr)
						exit(1)
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

				try:
					imageWidth = int(argv[i + 1])
				except:
					print("Error: invalid image width", file=sys.stderr)
					exit(1)

				optimizeImages = True
				i += 1
			elif arg == "--image-height":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				try:
					imageHeight = int(argv[i + 1])
				except:
					print("Error: invalid image height", file=sys.stderr)
					exit(1)

				optimizeImages = True
				i += 1
			elif arg == "--jpg-quality":
				if i == len(argv) - 1:
					printHelp()
					exit(1)

				try:
					jpgQuality = int(argv[i + 1])
				except:
					print("Error: invalid jpg quality")
					exit(1)

				optimizeImages = True
				i += 1
			elif arg == "--shrink-only":
				shrinkOnly = True
			elif arg[0] == "-":
				if infname is None:
					infname = "-"
				else:
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

	if removeFiltered and keepFiltered:
		print("Error: both --remove-filtered and --keep-filtered specified", file=sys.stderr)
		print("")
		printHelp()
		exit(1)

	if sortContacts and sortNumbers:
		print("Error: both --sort-contacts and --sort-numbers specified", file=sys.stderr)
		print("")
		printHelp()
		exit(1)

	parserObj = None

	try:
		if infname is None or infname == "-":
			infile = sys.stdin
		else:
			infile = open(infname, "r", encoding="utf8")

		data = infile.read()
		parserObj = Parser(data)

		if infile != sys.stdin:
			infile.close()
	except Exception as e:
		print("Error: could not read file: " + infname + ". " + str(e), file=sys.stderr)
		exit(1)

	contactList = parserObj.getContacts()

	clFilter = filters.ContactListFilter(contactList)

	for num in numberFilterList:
		try:
			clFilter.addNumber(num)
		except Exception as e:
			print(e, file=sys.stderr)

	for ct in contactFilterList:
		try:
			clFilter.addContact(ct)
		except Exception as e:
			print(e, file=sys.stderr)

	timeFilter.condense()

	filterActions = 0

	if len(clFilter) != 0 or len(timeFilter) != 0:
		for b in [normalize, removeNoDuration, len(replaceNumbers) != 0, removeFiltered, keepFiltered, listStats, listContacts, optimizeImages, extractfname is not None]:
			if b:
				filterActions += 1

		if filterActions == 0:
			print("Warn: filters were defined, but not used", file=sys.stderr)

	if normalize:
		parserObj.normalizeNumbers(clFilter, timeFilter)

		#update contact list
		contactList = parserObj.getContacts()

	if removeNoDuration:
		try:
			parserObj.removeNoDuration(clFilter, timeFilter)
		except Exception as e:
			print("Error: " + str(e), file=sys.stderr)

	if len(replaceNumbers) != 0:
		parserObj.replaceNumbers(replaceNumbers, timeFilter)

		#update contact list
		contactList = parserObj.getContacts()

	if (listStats or listContacts) and filterActions == 1 and not removeFiltered and not keepFiltered:
		keepFiltered = True

	if len(clFilter) != 0 or len(timeFilter) != 0:
		if removeFiltered:
			parserObj.removeByFilter(clFilter, timeFilter)
		elif keepFiltered:
			#get the inverse of the filters set
			invertedClFilter = clFilter.invert()
			invertedTimeFilter = timeFilter.invert()

			parserObj.removeByFilter(invertedClFilter, invertedTimeFilter)

		#update contact list
		contactList = parserObj.getContacts()

	if listStats:
		numcount, mmscount = parserObj.count()
		totalCount = 0

		for num in numcount:
			totalCount += numcount[num][0]
			totalCount += numcount[num][1]

		print(
			"%s:\n"
			"Total Count: %d\n"
			"" % (infname, totalCount)
		)

		if parserObj.smsXML:
			print("Number, Contact, Sent, Received")
		else:
			print("Number, Contact, Outgoing, Incoming")

		if sortNumbers:
			numbers = list(numcount.keys())
			numbers.sort()

			for num in numbers:
				print('%s, "%s", %d, %d' % (num, contactList[num], numcount[num][0], numcount[num][1]))
		elif sortContacts:
			sortedContact = sorted(contactList.items(), key=lambda x: x[1])
			for item in sortedContact:
				if item[0] not in numcount:
					continue
				print('%s, "%s", %d, %d' % (item[0], item[1], numcount[item[0]][0], numcount[item[0]][1]))
		else:
			for num in numcount:
				print('%s, "%s", %d, %d' % (num, contactList[num], numcount[num][0], numcount[num][1]))

		totalMmsCount = 0
		for mms in mmscount:
			totalMmsCount += mmscount[mms][0]
			totalMmsCount += mmscount[mms][1]

		if totalMmsCount > 0:
			print(
				"\n"
				"MMS Total Count: %d\n"
				"\n"
				"Number, Contact, Sent, Received" % (totalMmsCount)
			)

			if sortNumbers:
				numbers = list(mmscount.keys())
				numbers.sort()

				for mms in numbers:
					print('%s, "%s", %d' % (mms, contactList[mms], mmscount[mms][1]))
			elif sortContacts:
				sortedContact = sorted(contactList.items(), key=lambda x: x[1])
				for item in sortedContact:
					if item[0] not in mmscount:
						continue
					print('%s, "%s", %d, %d' % (item[0], item[1], mmscount[item[0]][0], mmscount[item[0]][1]))
			else:
				for mms in mmscount:
					print('%s, "%s", %d, %d' % (mms, contactList[mms], mmscount[mms][0], mmscount[mms][1]))

		print("")
		exit(0)

	if listContacts:
		contacts = []

		if sortNumbers:
			numbers = list(contactList.keys())
			numbers.sort()

			for num in numbers:
				contacts.append('%s, "%s"' % (num, contactList[num]))
		elif sortContacts:
			sortedContact = sorted(contactList.items(), key=lambda x: x[1])
			for item in sortedContact:
				contacts.append('%s, "%s"' % (item[0], item[1]))
		else:
			for num in contactList:
				contacts.append('%s, "%s"' % (num, contactList[num]))

		if len(contacts) != 0:
			sys.stdout.buffer.write("\n".join(contacts).encode("utf-8"))
			print("")

		exit(0)

	if optimizeImages:
		try:
			parserObj.optimizeImages(clFilter, timeFilter, imageWidth, imageHeight, jpgQuality, shrinkOnly)
		except Exception as e:
			print("Error: " + str(e), file=sys.stderr)
	else:
		if shrinkOnly:
			if parserObj.smsXML:
				print("Warn: --shrink-only was used, but no optimization options were set", file=sys.stderr)
			else:
				print("Warn: --shrink-only was used, but file is a call file", file=sys.stderr)

	if extractfname is not None:
		try:
			parserObj.extractMedia(extractfname, set(), clFilter, timeFilter)
		except Exception as e:
			print("Error: " + str(e), file=sys.stderr)
		exit(0)

	if stripAttr:
		parserObj.stripAttrs()

	if removeComments:
		parserObj.removeComments()

	usetabs = indentation == "tab"

	output = parserObj.prettify(indent=indentation, tabs=usetabs)

	if revert or not doConvert:
		if parserObj.smsXML:
			output = parser.unescapeInvalidXmlCharacters(output)
		else:
			if revert:
				print("Warn: --revert was used, but file is a call file", file=sys.stderr)
			if not doConvert:
				print("Warn: --no-convert was used, but file is a call file", file=sys.stderr)

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
		"  --statistics                        display statistics of sms/calls and exit\n"
		"  -l, --list                          list the contacts in the file and exit\n"
		"  --sort-contacts                     sort list output by contact\n"
		"  --sort-numbers                      sort list output by number (default)\n"
		"\n"
		"  -f, --filter-contact [name]         use contact as filter for other options\n"
		"  -g, --filter-number [number]        use number as filter for other options\n"
		"  -t, --filter-time [time] [time]     use time range as filter for other options\n"
		"                                        - times can be in seconds since epoch,\n"
		"                                          or YYYY-MM-DD HH:MM:SS\n"
		"\n"
		"  --replace-number [contact] [num]    replace contact with new number\n"
		"                                        - will only change time filtered\n"
		"                                          numbers\n"
		"  --normalize                         attempt to normalize numbers to the\n"
		"                                        longest version, only changes filtered\n"
		"                                        numbers\n"
		"\n"
		"  --remove-filtered                   remove sms/calls in the filter\n"
		"  --keep-filtered                     keep only sms/calls in the filter\n"
		"  --remove-no-duration                remove zero duration calls for call.xml\n"
		"                                        - filtered numbers will not be removed\n"
		"  --remove-comments                   remove comments from the output xml file\n"
		"\n"
		"  -r, --revert                        convert valid XML back to SMSBackupXML\n"
		"  --no-convert                        do not convert XML, default is convert\n"
		"\n"
		"  -s, --strip                         strip unnecessary attributes from nodes\n"
		"                                        MAY MAKE FILE UNRESTORABLE!\n"
		"  --indent [value]                    number of spaces for indentation, or 'tab'\n"
		"\n"
		"  -e, --extract-media [file]          extract media to zip file and exit\n"
		"  --image-width [value]               set maximum image width\n"
		"  --image-height [value]              set maximum image height\n"
		"  --jpg-quality [value]               set jpg image quality\n"
		"  --shrink-only                       only change media if the size is smaller\n"
	)

if __name__ == "__main__":
	main(sys.argv)
