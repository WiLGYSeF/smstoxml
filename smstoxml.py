#!/usr/bin/env python3

#requires python3-bs4, python3-pil, python3-lxml

import argparse
import json
import sys

from contactlistfilter import ContactListFilter
from timelinefilter import TimelineFilter
import parser


def main(argv):
	aparser = argparse.ArgumentParser(description="")
	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("-l", "--list", action="store_true", help="list the contacts in the file and exit")
	agroup.add_argument("--statistics", action="store_true", help="display statistics of entries and exit")

	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("--sort-contact", action="store_true", help="sort list output by contact")
	agroup.add_argument("--sort-number", action="store_true", help="sort list output by number (default)")

	aparser.add_argument("-f", "--filter-contact", metavar="NAME", action="append", help="add contact to filter")
	aparser.add_argument("-g", "--filter-number", metavar="NUM", action="append", help="add number to filter")
	aparser.add_argument("-t", "--filter-time", metavar=("START", "END"), nargs=2, action="append", help="add time range to filter, START/END can be in seconds since epoch or YYYY-MM-DD HH:MM:SS")

	aparser.add_argument("--replace-num-num", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace number by number")
	aparser.add_argument("--replace-num-contact", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace number by contact")
	aparser.add_argument("--replace-contact-contact", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace contact name by contact")
	aparser.add_argument("--replace-contact-num", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace contact name by number")

	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("--remove-filtered", action="store_true", help="remove entries that match the given filters")
	agroup.add_argument("--keep-filtered", action="store_true", help="keep entries that match the given filters (default)")

	aparser.add_argument("--remove-no-duration", action="store_true", help="remove call entries with no call duration")
	aparser.add_argument("--remove-comments", action="store_true", help="remove comments from output")

	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("--revert-escape", action="store_true", help="revert escaping invalid XML")
	agroup.add_argument("--no-escape", action="store_true", help="do not escape invalid XML") #?

	aparser.add_argument("--strip", action="store_true", help="strips non-critical attributes from entries, MAY AFFECT RESTORATION")

	aparser.add_argument("--indent", metavar="VALUE", action="store", help="indent entries by VALUE spaces, or 'tab'")

	aparser.add_argument("--extract-media", metavar="FILE", action="store", help="extract media files to FILE archive")
	aparser.add_argument("--image-width", metavar="VALUE", action="store", help="set maximum image width")
	aparser.add_argument("--image-height", metavar="VALUE", action="store", help="set maximum image height")
	aparser.add_argument("--jpg-quality", metavar="VALUE", action="store", help="set jpg image quality")
	aparser.add_argument("--shrink-only", action="store_true", help="only change media if the newer data is smaller")

	aparser.add_argument("output", metavar="OUTPUT", action="store")
	aparser.add_argument("inputs", metavar="INPUT", action="store", nargs="+")

	argspace = aparser.parse_args()

	with open(argspace.inputs[0], "rb") as f:
		mainParser = parser.Parser(f.read())
		if mainParser.smsXML:
			collection = mainParser.soup.find("smses")
		else:
			collection = mainParser.soup.find("calls")

	if len(argspace.inputs) > 1:
		for i in range(1, len(argspace.inputs)):
			with open(argspace.inputs[i], "rb") as f:
				mergeParser = parser.Parser(f.read())
				if mergeParser.smsXML != mainParser.smsXML:
					raise Exception("cannot merge mixed file types")

				if mainParser.smsXML:
					nodes = mergeParser.soup.find_all(["sms", "mms"])
				else:
					nodes = mergeParser.soup.find_all("call")

				for n in nodes:
					collection.append(n.extract())


	contactList = mainParser.getFullContacts()
	clFilter = ContactListFilter(contactList)
	timeFilter = TimelineFilter()

	if argspace.filter_contact is not None:
		for ct in argspace.filter_contact:
			clFilter.addContact(ct)
	if argspace.filter_number is not None:
		for num in argspace.filter_number:
			clFilter.addNumber(num)

	if argspace.filter_time is not None:
		for start, end in argspace.filter_time:
			timeFilter.addTimeRange(start, end)

	if argspace.remove_no_duration and not mainParser.smsXML:
		mainParser.removeNoDuration(clFilter, timeFilter)

	if argspace.replace_num_num is not None:
		for n1, n2 in argspace.replace_num_num:
			mainParser.replaceNumberByNumber(n1, n2)
	if argspace.replace_num_contact is not None:
		for ct, num in argspace.replace_num_contact:
			mainParser.replaceNumberByContact(ct, num)
	if argspace.replace_contact_contact is not None:
		for ct1, ct2 in argspace.replace_contact_contact:
			mainParser.replaceContactByContact(ct1, ct2)
	if argspace.replace_contact_num is not None:
		for num, ct in argspace.replace_contact_num:
			mainParser.replaceContactByNumber(num, ct)

	contactList = mainParser.getFullContacts()

	if argspace.statistics:
		counter = mainParser.count()
		print(json.dumps(counter, indent=2))
		exit(0)


if __name__ == "__main__":
	main(sys.argv)
