#requires python3-bs4, python3-pil, python3-lxml

import parser
from parser import Parser

import bisect
import re
import sys
import time

def main(argv):
	infname = None
	outfname = None

	filterContacts = set()
	filterNumbers = set()
	filterTimes = []
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
	shrinkOnly = False

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
			elif arg == "-t" or arg == "--filter-time":
				if i == len(argv) - 2:
					printHelp()
					exit(1)

				try:
					startTime = int(argv[i + 1])
				except:
					startTime = int(time.mktime(time.strptime(argv[i + 1], "%Y-%m-%d %H:%M:%S")))
				try:
					endTime = int(argv[i + 2])
				except:
					endTime = int(time.mktime(time.strptime(argv[i + 2], "%Y-%m-%d %H:%M:%S")))

				if startTime > endTime:
					print("Error: filter time " + str(startTime) + " and " + str(endTime) + " is in wrong order", file=sys.stderr)
					exit(1)

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

				insertarr(filterTimes, ( startTime, 0 ), cmpfunc, unique=True)
				insertarr(filterTimes, ( endTime, 1 ), cmpfunc, unique=True)
				i += 2
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
			elif arg == "--shrink-only":
				shrinkOnly = True
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

	if len(filterTimes) != 0:
		condensedtime = []
		length = len(filterTimes)

		i = 0
		while i < length:
			startTime = filterTimes[i][0]
			i += 1

			while True:
				changed = False

				while i < length and filterTimes[i][1] == 0:
					changed = True
					i += 1

				while i < length - 1 and filterTimes[i + 1][1] == 1:
					changed = True
					i += 1

				while i < length - 1 and filterTimes[i][0] == filterTimes[i + 1][0]:
					changed = True
					i += 1

				if not changed or i == length:
					break

			if i == length:
				i -= 1

			endTime = filterTimes[i][0]

			condensedtime.append( (startTime, endTime) )
			i += 1

		filterTimes = condensedtime

	if removeNoDuration:
		parserObj.removeNoDuration(filterContacts, filterNumbers, filterTimes)

	if len(replaceNumbers) != 0:
		for contact in replaceNumbers:
			parserObj.replaceNumber(contact, replaceNumbers[contact], filterTimes)

	if len(filterContacts) != 0 or len(filterNumbers) != 0 or len(filterTimes) != 0:
		if removeFiltered:
			parserObj.removeByFilter(filterContacts, filterNumbers, filterTimes)
		elif keepFiltered:
			cdiff = set()
			ndiff = set()
			invertTime = parserObj.invertTimeFilter(filterTimes)

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
			elif len(filterNumbers) != 0:
				ndiff = numbersSet - filterNumbers

			parserObj.removeByFilter(cdiff, ndiff, invertTime)

	if listStats:
		#refresh list
		contactsList = parserObj.getContacts()

		ctcount, numcount, mmscount = parserObj.countByFilter(filterContacts, filterNumbers, filterTimes)
		totalCount = 0

		for ct in ctcount:
			totalCount += ctcount[ct][0]
			totalCount += ctcount[ct][1]
		for num in numcount:
			if len(num) != 0 and contactsList[num] in ctcount:
				continue

			totalCount += numcount[num][0]
			totalCount += numcount[num][1]

		print(infname + ":")
		print("SMS Total Count: " + str(totalCount))
		print("")

		print("Number, Contact, Sent To, Received From")
		for num in numcount:
			if len(num) == 0:
				continue

			print(num + ', "' + contactsList[num] + '", ' + str(numcount[num][0]) + ', ' + str(numcount[num][1]))

		#check if there are any contacts not in the numbers list for some reason
		hasCts = False
		for ct in ctcount:
			num = None
			for n in contactsList:
				if contactsList[n] == ct:
					num = n
					break
			if num in numcount:
				continue

			hasCts = True
			break

		if hasCts:
			print("")
			print("Number, Contact, Sent To, Received From")
			for ct in ctcount:
				num = None
				for n in contactsList:
					if contactsList[n] == ct:
						num = n
						break
				if num in numcount:
					continue

				print(num + ', "' + ct + '", ' + str(ctcount[ct][0]) + ', ' + str(ctcount[ct][1]))

		totalMmsCount = 0
		for mms in mmscount:
			totalMmsCount += mmscount[mms][0]
			totalMmsCount += mmscount[mms][1]

		if totalMmsCount > 0:
			print("")
			print("MMS Total Count: " + str(totalMmsCount))
			print("")
			#print("Number, Contact, Sent To, Received From")
			print("Number, Contact, Count")

			for mms in mmscount:
				#print(mms + ', "' + contactsList[mms] + '", ' + str(mmscount[mms][0]) + ', ' + str(mmscount[mms][1]))
				print(mms + ', "' + contactsList[mms] + '", ' + str(mmscount[mms][1]))


		print("")
		exit(0)

	if listContacts:
		#refresh list
		contactsList = parserObj.getContacts()

		sys.stdout.buffer.write("\n".join(list(map(lambda x: x + "," + contactsList[x], contactsList))).encode("utf-8"))
		print("")
		exit(0)

	if imageWidth != -1 or imageHeight != -1 or jpgQuality != -1:
		parserObj.optimizeImages(filterContacts, filterNumbers, filterTimes, imageWidth, imageHeight, jpgQuality, shrinkOnly)

	if extractfname is not None:
		parserObj.extractMedia(extractfname, set(), filterContacts, filterNumbers, filterTimes)
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

def insertarr(arr, value, cmpfunc, unique=False):
	length = len(arr)
	low = 0
	high = length

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

def printHelp():
	print(
		"SMSBackupXML to valid XML converter\n"
		"Usage: smstoxml.py [input] [output] options...\n"
		"\n"
		"  -h, --help                          shows this help menu\n"
		"  --statistics                        display statistics of sms/calls\n"
		"  -l, --list                          list the contacts in the file and exit\n"
		"  -f, --filter-contact [name]         use contact as filter for other options\n"
		"  -g, --filter-number [number]        use number as filter for other options\n"
		"  -t, --filter-time [time] [time]     use time range as filter for other options\n"
		"      times can be in seconds since epoch, or YYYY-MM-DD HH:MM:SS\n"
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
		"  --shrink-only                       only change media if the size is smaller\n"
	)

if __name__ == "__main__":
	main(sys.argv)
