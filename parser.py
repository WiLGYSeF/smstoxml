from collections import deque
import base64
import re
import sys
import traceback

import bs4

import archiver
import media
import mimetype


class Parser:
    SMS_RECEIVED = 1
    SMS_SENT = 2
    SMS_DRAFT = 3

    def __init__(self, data):
        self.smsXML = bool(re.search(b'<smses(?: [^>]*)?>', data))

        if self.smsXML:
            data = escapeInvalidXmlCharacters(data)

        self.soup = bs4.BeautifulSoup(data.decode('utf-8'), 'xml')

    def getFullContacts(self):
        contactList = self.getContacts()
        self.convertMmsContacts(contactList)
        self.renameUnknownContacts(contactList)

        return contactList

    def getContacts(self):
        contactList = {}

        if self.smsXML:
            for node in self.soup.find_all(['sms', 'mms']):
                number = node['address']
                ctname = node['contact_name']

                # will override to latest contact name
                contactList[number] = ctname
        else:
            for call in self.soup.find_all('call'):
                number = call['number']

                # will override to latest contact name
                contactList[number] = call['contact_name']
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
                    'sent': 0,
                    'received': 0,
                }

            obj[k]['sent' if sent else 'received'] += 1

        if self.smsXML:
            sSent = 0
            sRecv = 0
            mSent = 0
            mRecv = 0

            for node in self.soup.find_all(['sms', 'mms']):
                sent = int(node['msg_box' if node.name == 'mms' else 'type']) == Parser.SMS_SENT
                numbers, contacts = self.splitMmsContacts(node['address'], node['contact_name'])

                if node.name == 'sms':
                    if sent:
                        sSent += 1
                    else:
                        sRecv += 1
                else:
                    if sent:
                        mSent += 1
                    else:
                        mRecv += 1

                for i in range(len(numbers)):
                    incr([node.name, 'numbers'], numbers[i], sent)
                    incr([node.name, 'contacts'], contacts[i], sent)

            if 'sms' in counter:
                counter['sms']['total'] = {'sent': sSent, 'received': sRecv}
            if 'mms' in counter:
                counter['mms']['total'] = {'sent': mSent, 'received': mRecv}
        else:
            cSent = 0
            cRecv = 0

            for call in self.soup.find_all('call'):
                sent = int(call['type']) == Parser.SMS_SENT

                if sent:
                    cSent += 1
                else:
                    cRecv += 1

                incr(['call', 'numbers'], call['number'], sent)
                incr(['call', 'contacts'], call['contact_name'], sent)

            if 'call' in counter:
                counter['call']['total'] = {'sent': cSent, 'received': cRecv}

        return counter

    def convertMmsContacts(self, contactList):
        for num, ctname in list(contactList.items()):
            numbers, contacts = self.splitMmsContacts(num, ctname)
            if len(numbers) > 1:
                for i in range(len(numbers)):
                    contactList[numbers[i]] = contacts[i]
                del contactList[num]

    def splitMmsContacts(self, numbers, contacts):
        if '~' in numbers:
            numberlist = numbers.split('~')
            contactlist = contacts.split(', ')

            while len(numberlist) > len(contactlist):
                contactlist.append('(Unknown)')
        else:
            numberlist = [numbers]
            contactlist = [contacts]

        return numberlist, contactlist

    def joinMmsContacts(self, numbers, contacts):
        return '~'.join(numbers), ', '.join(contacts)

    def renameUnknownContacts(self, contactList):
        unknownCount = 1

        for num, ctname in list(contactList.items()):
            if ctname == '(Unknown)':
                contactList[num] = '(Unknown %d)' % unknownCount
                unknownCount += 1

    def removeByFilter(self, clfilter, timefilter, removeFiltered=True, matchesAnyFilter=False, fullMatch=True):
        removed = False

        if self.smsXML:
            for node in self.soup.find_all(['sms', 'mms']):
                # time is stored in milliseconds since epoch
                seconds = int(node['date']) // 1000

                numbers, contacts = self.splitMmsContacts(node['address'], node['contact_name'])
                bMapped = list(
                    map(
                        lambda num, ctname: self.inFilters(
                            clfilter,
                            timefilter,
                            num,
                            ctname,
                            seconds,
                            removeFiltered=removeFiltered,
                            matchesAnyFilter=matchesAnyFilter,
                        ),
                        numbers,
                        contacts,
                    )
                )

                if (fullMatch and all(bMapped)) or (not fullMatch and any(bMapped)):
                    node.decompose()
                    removed = True
        else:
            for call in self.soup.find_all('call'):
                num = call['number']
                ctname = call['contact_name']
                # time is stored in milliseconds since epoch
                seconds = int(call['date']) // 1000

                if self.inFilters(
                    clfilter,
                    timefilter,
                    num,
                    ctname,
                    seconds,
                    removeFiltered=removeFiltered,
                    matchesAnyFilter=matchesAnyFilter,
                ):
                    call.decompose()
                    removed = True

        if removed:
            self.updateCount()

    def replace(self, search, replace, searchType, replaceType, timefilter=None):
        hasTimeFilter = timefilter is not None and not timefilter.isEmpty()

        def modifyContactInfo(num, ctname):
            numbers, contacts = self.splitMmsContacts(num, ctname)
            for i in range(len(numbers)):
                if (searchType == 'number' and numbers[i] == search) or (
                    searchType == 'contact' and contacts[i] == search
                ):
                    if replaceType == 'number':
                        numbers[i] = replace
                    elif replaceType == 'contact':
                        contacts[i] = replace
            return self.joinMmsContacts(numbers, contacts)

        if self.smsXML:
            for node in self.soup.find_all(['sms', 'mms']):
                if hasTimeFilter:
                    # time is stored in milliseconds since epoch
                    seconds = int(node['date']) // 1000
                    if not timefilter.inTimeline(seconds):
                        continue

                numstr, ctstr = modifyContactInfo(node['address'], node['contact_name'])
                node['address'] = numstr
                node['contact_name'] = ctstr
        else:
            for call in self.soup.find_all('call'):
                if hasTimeFilter:
                    # time is stored in milliseconds since epoch
                    seconds = int(node['date']) // 1000
                    if not timefilter.inTimeline(seconds):
                        continue

                numstr, ctstr = modifyContactInfo(call['number'], call['contact_name'])
                call['number'] = numstr
                call['contact_name'] = ctstr

    def replaceNumberByNumber(self, searchNum, replaceNum, timefilter=None):
        self.replace(searchNum, replaceNum, 'number', 'number', timefilter)

    def replaceNumberByContact(self, searchContact, replaceNum, timefilter=None):
        self.replace(searchContact, replaceNum, 'contact', 'number', timefilter)

    def replaceContactByContact(self, searchContact, replaceContact, timefilter=None):
        self.replace(searchContact, replaceContact, 'contact', 'contact', timefilter)

    def replaceContactByNumber(self, searchNum, replaceContact, timefilter=None):
        self.replace(searchNum, replaceContact, 'number', 'contact', timefilter)

    def removeNoDuration(self, clfilter, timefilter, removeFiltered=True, matchesAnyFilter=False):
        if self.smsXML:
            raise Exception('cannot remove no-duration calls from sms file')

        removed = False

        for call in self.soup.find_all('call'):
            # time is stored in milliseconds since epoch
            seconds = int(call['date']) // 1000

            if self.inFilters(
                clfilter,
                timefilter,
                call['number'],
                call['contact_name'],
                seconds,
                removeFiltered=removeFiltered,
                matchesAnyFilter=matchesAnyFilter,
            ):
                continue

            if call['duration'] == '0':
                call.decompose()
                removed = True

        if removed:
            self.updateCount()

    def updateCount(self):
        if self.smsXML:
            nodes = self.soup.find('smses').contents
        else:
            nodes = self.soup.find('calls').contents

        nlen = len(nodes)
        idx = 0

        while idx < nlen:
            node = nodes[idx]
            if idx < nlen - 1 and isinstance(node, bs4.element.NavigableString) and node == '\n':
                # find extra newlines and delete them
                nlx = idx + 1
                while nlx < nlen and isinstance(nodes[nlx], bs4.element.NavigableString) and nodes[nlx] == '\n':
                    # NavigableString has no decompose()
                    nodes[nlx].extract()
                    nlen -= 1
            idx += 1

        if self.smsXML:
            smses = self.soup.find('smses')
            smses['count'] = len(self.soup.find_all('sms')) + len(self.soup.find_all('mms'))
        else:
            calls = self.soup.find('calls')
            calls['count'] = len(self.soup.find_all('call'))

    def stripAttrs(self):
        def delattrib(obj, keep):
            attrs = list(filter(lambda x: x not in keep, obj.attrs))
            for a in attrs:
                del obj.attrs[a]

        if self.smsXML:
            KEEPATTR = set(['address', 'body', 'contact_name', 'date', 'date_sent', 'read', 'readable_date', 'type'])
            for node in self.soup.find_all('sms'):
                delattrib(node, KEEPATTR)

            KEEPATTR = set(['chset', 'cid', 'cl', 'ct', 'data', 'name', 'seq', 'text'])
            for node in self.soup.find_all('part'):
                delattrib(node, KEEPATTR)

                # strip out crlf from mms part formatting
                if 'text' in node.attrs and 'seq' in node.attrs and node.attrs['seq'] == '-1':
                    node.attrs['text'] = node.attrs['text'].replace('&#13;&#10;', '')
        else:
            KEEPATTR = set(['contact_name', 'date', 'duration', 'number', 'readable_date', 'type'])
            for node in self.soup.find_all('call'):
                delattrib(node, KEEPATTR)

    def removeComments(self, root=None):
        if root is None:
            root = self.soup

        nodeque = deque([root])
        while len(nodeque) > 0:
            node = nodeque.popleft()
            if isinstance(node, bs4.element.Comment):
                # Comment has no decompose()
                node.extract()
            else:
                try:
                    for c in node.children:
                        nodeque.append(c)
                except:
                    pass

    def inFilters(self, clFilter, timeFilter, num, ctname, seconds, removeFiltered=True, matchesAnyFilter=False):
        hasClFilter = clFilter is not None and not clFilter.isEmpty()
        hasTimeFilter = timeFilter is not None and not timeFilter.isEmpty()
        b = False

        if matchesAnyFilter:
            b = (hasClFilter and clFilter.hasNumberOrContact(num, ctname)) or (
                hasTimeFilter and timeFilter.inTimeline(seconds)
            )
        else:
            b = False
            if hasClFilter:
                b = clFilter.hasNumberOrContact(num, ctname)
            if hasTimeFilter:
                if not hasClFilter:
                    b = True
                b = b and timeFilter.inTimeline(seconds)

        return b if removeFiltered else not b

    def extractMedia(self, arname, artype=None, excludeMimetypes=None, clfilter=None, timefilter=None):
        if not self.smsXML:
            raise Exception('cannot extract media from call file')

        archive = archiver.Archiver(arname, type_=artype)
        usedNames = set()

        for node in self.genMmsMedia(excludeMimetypes, clFilter=clfilter, timeFilter=timefilter):
            if 'name' in node:
                name = node['name']
                if '.' in name:
                    spl = name.split('.')
                    fname = '.'.join(spl[1:])
                    ext = '.' + spl[0]
                else:
                    fname = ''
                    ext = ''

                incr = 1
                while name in usedNames:
                    name = '%s_%d%s' % (fname, incr, ext)
                    incr += 1
            else:
                mmsparent = node.parent.parent
                ext = mimetype.guessExtension(node['ct'])

                if ext is not None and len(ext) != 0:
                    ext = '.' + ext
                name = '%s-%s%s' % (mmsparent['date'], mmsparent['contact_name'], ext)

                incr = 1
                while name in usedNames:
                    name = '%s-%s_%d%s' % (mmsparent['date'], mmsparent['contact_name'], incr, ext)
                    incr += 1

            data = base64.b64decode(node.attrs['data'])
            try:
                archive.addFile(name, data)
                usedNames.add(name)
            except:
                traceback.print_exc()

        archive.close()

    def optimizeImages(
        self, clfilter=None, timefilter=None, maxWidth=None, maxHeight=None, jpgQuality=None, onlyShrink=False
    ):
        if not self.smsXML:
            raise Exception('cannot optimize images from call file')

        for node in self.genMmsMedia(None, clFilter=clfilter, timeFilter=timefilter):
            if node['ct'] not in media.imageMimetypes:
                continue

            try:
                optimized = media.optimizeImage(
                    base64.b64decode(node.attrs['data']),
                    media.imageMimetypes[node['ct']],
                    maxWidth=maxWidth,
                    maxHeight=maxHeight,
                    jpgQuality=jpgQuality,
                    onlyShrink=onlyShrink,
                )

                if optimized:
                    node.attrs['data'] = base64.b64encode(optimized).decode('ascii')
                if optimized is None:
                    mmse = node.parent.parent
                    print(
                        'img: %s "%s" %s: image did not shrink'
                        % (
                            mmse.attrs['address'],
                            mmse.attrs['contact_name'].replace('"', r'\"'),
                            mmse.attrs['readable_date'],
                        ),
                        file=sys.stderr,
                    )
            except:
                pass

    def genMmsMedia(self, excludeMimetypes=None, clFilter=None, timeFilter=None):
        hasClFilter = clFilter is not None and not clFilter.isEmpty()
        hasTimeFilter = timeFilter is not None and not timeFilter.isEmpty()

        for node in self.soup.find_all('part'):
            mtype = node['ct']
            if mtype == 'application/smil':
                continue
            if 'data' not in node.attrs:
                continue

            mmsparent = node.parent.parent
            numbers, contacts = self.splitMmsContacts(mmsparent['address'], mmsparent['contact_name'])
            if hasClFilter and not any(
                map(lambda num, ctname: clFilter.hasNumberOrContact(num, ctname), numbers, contacts)
            ):
                continue
            # time is stored in milliseconds since epoch
            seconds = int(mmsparent['date']) // 1000
            if hasTimeFilter and not timeFilter.inTimeline(seconds):
                continue

            if excludeMimetypes is not None and mtype in excludeMimetypes:
                continue

            yield node

    def prettify(self, indent=2):
        lines = self.soup.prettify().split('\n')

        if not self.hasStylesheet():
            if self.smsXML:
                lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
            else:
                lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')

        if indent != 1:
            for i in range(len(lines)):
                line = lines[i]
                c = 0

                while c < len(line):
                    if line[c] != ' ':
                        break
                    c += 1
                lines[i] = ('\t' * c if indent == '\t' else ' ' * indent * c) + line[c:]

        return '\n'.join(lines)

    def hasStylesheet(self):
        for child in self.soup.children:
            if isinstance(child, bs4.element.XMLProcessingInstruction):
                if str(child).startswith('xml-stylesheet'):
                    return True
        return False

    def __str__(self):
        lines = str(self.soup).split('\n')

        if not self.hasStylesheet():
            if self.smsXML:
                lines.insert(1, '<?xml-stylesheet type="text/xsl" href="sms.xsl"?>')
            else:
                lines.insert(1, '<?xml-stylesheet type="text/xsl" href="calls.xsl"?>')
        return '\n'.join(lines)


def escapeInvalidXmlCharacters(data):
    regex = re.compile(rb'&#(\d+|x[\dA-Fa-f]+);')
    newdata = bytearray()
    offset = 0

    for match in re.finditer(regex, data):
        if match.group(1)[0] == 'x':
            num = int(match.group(1)[1:], 16)
        else:
            num = int(match.group(1))

        if isValidXML(num):
            newdata += data[offset : match.end()]
        else:
            newdata += data[offset : match.start()] + '&amp;#' + match.group(1) + ';'
        offset = match.end()
    newdata += data[offset:]

    return newdata


def unescapeEscapedAmpersands(data):
    regex = re.compile(b"body=(\"[^\"]*(?:&amp;#)[^\"]*\"|'[^']*(?:&amp;#)[^']*')")
    newdata = bytes()
    offset = 0

    for match in re.finditer(regex, data):
        newdata += data[offset : match.start()] + data[match.start() : match.end()].replace('&amp;#', '&#')
        offset = match.end()
    newdata += data[offset:]

    return newdata


def escapeBodyNewlines(data):
    regex = re.compile("body=(\"[^\"]*\n[^\"]*\"|'[^']*\n[^']*')")
    newdata = ""
    offset = 0

    for match in re.finditer(regex, data):
        newdata += data[offset : match.start()] + data[match.start() : match.end()].replace('\n', '&#10;')
        offset = match.end()
    newdata += data[offset:]

    return newdata


def isValidXML(c):
    return (
        c == 0x09
        or c == 0x0A
        or c == 0x0D
        or (c >= 0x20 and c <= 0xD7FF)
        or (c >= 0xE000 and c <= 0xFFFD)
        or (c >= 0x10000 and c <= 0x10FFFF)
    )
