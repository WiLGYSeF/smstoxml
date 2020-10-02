#!/usr/bin/env python3

#requires python3-bs4, python3-pil, python3-lxml, pyyaml

import argparse
import json
import sys

import yaml

from contactlistfilter import ContactListFilter
from timelinefilter import TimelineFilter
import parser


def main(argv):
	aparser = argparse.ArgumentParser(description="")
	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("-l", "--list", action="store_true", help="list the contacts in the file")
	agroup.add_argument("-s", "--stats", action="store_true", help="display statistics of entries")
	aparser.add_argument("-y", "--yaml", action="store_true", help="output statistics as YAML instead of JSON")
	aparser.add_argument("--no-output", action="store_true", help="do not write output when using --list or --stats, use - as the output file")

	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("--sort-contact", action="store_true", help="sort list output by contact")
	agroup.add_argument("--sort-number", action="store_true", help="sort list output by number (default)")

	aparser.add_argument("-d", "--filter-contact-expr", metavar="EXPR", action="append", help="add contact expression to filter")
	aparser.add_argument("-e", "--filter-number-expr", metavar="EXPR", action="append", help="add number expression to filter")
	aparser.add_argument("-f", "--filter-contact", metavar="NAME", action="append", help="add contact to filter")
	aparser.add_argument("-g", "--filter-number", metavar="NUM", action="append", help="add number to filter")
	aparser.add_argument("-t", "--filter-time", metavar=("START", "END"), nargs=2, action="append", help="add time range to filter, START/END can be in seconds since epoch or YYYY-MM-DD HH:MM:SS")

	aparser.add_argument("--replace-num-num", "--rnn", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace number by number")
	aparser.add_argument("--replace-num-contact", "--rnc", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace number by contact")
	aparser.add_argument("--replace-contact-contact", "--rcc", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace contact name by contact")
	aparser.add_argument("--replace-contact-num", "--rcn", metavar=("SEARCH", "REPLACE"), nargs=2, action="append", help="replace contact name by number")

	agroup = aparser.add_mutually_exclusive_group()
	agroup.add_argument("-r", "--remove-filtered", action="store_true", help="remove entries that match the given filters")
	agroup.add_argument("-k", "--keep-filtered", action="store_true", help="keep entries that match the given filters")
	aparser.add_argument("--match-any", action="store_true", help="entries will be filtered if either contact/number or time filter matches instead of needing both to match")
	aparser.add_argument("--partial-match", action="store_true", help="an entry with any numbers/contacts in the filter can match instead of all of them needing to match")

	aparser.add_argument("--remove-no-duration", action="store_true", help="remove call entries with no call duration")
	aparser.add_argument("--remove-comments", action="store_true", help="remove comments from output")

	aparser.add_argument("--revert-escape", action="store_true", help="revert escaped invalid XML")

	aparser.add_argument("--strip", action="store_true", help="strips non-critical attributes from entries, MAY AFFECT RESTORATION")

	aparser.add_argument("-i", "--indent", metavar="VALUE", action="store", help="indent entries by VALUE spaces, or 'tab'")

	aparser.add_argument("-x", "--extract-media", metavar="FILE", action="store", help="extract media files to FILE archive")
	aparser.add_argument("--no-write-optimized-images", action="store_true", help="do not write optimized images into the output file")
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

	if argspace.filter_contact_expr is not None:
		for expr in argspace.filter_contact_expr:
			clFilter.addContactExpr(expr)
	if argspace.filter_number_expr is not None:
		for expr in argspace.filter_number_expr:
			clFilter.addNumberExpr(expr)

	if argspace.filter_time is not None:
		for start, end in argspace.filter_time:
			timeFilter.addTimeRange(start, end)
	timeFilter.condense()

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

	if any(map(lambda x: x is not None, [argspace.filter_number, argspace.filter_contact, argspace.filter_number_expr, argspace.filter_contact_expr, argspace.filter_time])):
		if not argspace.remove_filtered and not argspace.keep_filtered:
			argspace.keep_filtered = True

	if argspace.remove_filtered or argspace.keep_filtered:
		mainParser.removeByFilter(clFilter, timeFilter, removeFiltered=argspace.remove_filtered, matchesAnyFilter=argspace.match_any, fullMatch=not argspace.partial_match)

	#update contacts after replacing, removing
	contactList = mainParser.getFullContacts()

	try:
		if argspace.indent == "tab":
			argspace.indent = "\t"
		else:
			argspace.indent = int(argspace.indent)
	except:
		argspace.indent = 2

	if not argspace.no_write_optimized_images:
		optimizeAndExtractIfEnabled(mainParser, argspace, clFilter, timeFilter)

	if argspace.stats:
		counter = mainParser.count()
		if argspace.yaml:
			unicode_print(yaml.dump(counter))
		else:
			unicode_print(json.dumps(counter, indent=argspace.indent))

	if argspace.list:
		if argspace.sort_contact:
			items = sorted(contactList.items())
		else:
			items = sorted(contactList.items(), key=lambda x: x[1])

		for num, ctname in items:
			if argspace.sort_contact:
				unicode_print("%s: %s" % (ctname, num))
			else:
				unicode_print("%s: %s" % (num, ctname))

	if argspace.remove_comments:
		mainParser.removeComments()

	if argspace.strip:
		mainParser.stripAttrs()

	if not argspace.no_output:
		outputBuf = mainParser.prettify(indent=argspace.indent).encode("ascii", errors="xmlcharrefreplace")
		if argspace.revert_escape:
			outputBuf = parser.unescapeEscapedAmpersands(outputBuf)

		if argspace.output != "-":
			with open(argspace.output, "wb") as f:
				f.write(outputBuf)
		else:
			print(outputBuf.decode("ascii"))

	if argspace.no_write_optimized_images:
		optimizeAndExtractIfEnabled(mainParser, argspace, clFilter, timeFilter)


def optimizeImages(mainParser, argspace, clFilter, timeFilter):
	width = argspace.image_width
	height = argspace.image_height
	quality = argspace.jpg_quality

	if width is not None:
		width = int(width)
	if height is not None:
		height = int(height)
	if quality is not None:
		quality = int(quality)

	mainParser.optimizeImages(clfilter=clFilter, timefilter=timeFilter, maxWidth=width, maxHeight=height, jpgQuality=quality, onlyShrink=argspace.shrink_only)


def optimizeAndExtractIfEnabled(mainParser, argspace, clFilter, timeFilter):
	if any(map(lambda x: x is not None, [argspace.image_width, argspace.image_height, argspace.jpg_quality])):
		optimizeImages(mainParser, argspace, clFilter, timeFilter)
	if argspace.extract_media is not None:
		mainParser.extractMedia(argspace.extract_media, clfilter=clFilter, timefilter=timeFilter)


def unicode_print(s):
	sys.stdout.buffer.write(s.encode("utf-8"))
	print("")

if __name__ == "__main__":
	main(sys.argv)
