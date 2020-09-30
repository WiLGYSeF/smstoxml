#!/usr/bin/env python3

import sys

from contactlistfilter import ContactListFilter
from timelinefilter import TimelineFilter
import parser


def main(argv):
	xmlFile = open(argv[1], "rb")

	smsParser = parser.Parser(xmlFile.read())

	xmlFile.close()


if __name__ == "__main__":
	main(sys.argv)
