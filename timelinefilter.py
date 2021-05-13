import time


class TimelineFilter:
	RANGE_BEGIN = 0
	RANGE_END = 1


	def __init__(self):
		self.timeline = []


	def addTimeRange(self, start, end, dateformat="%Y-%m-%d %H:%M:%S"):
		def convertToTime(x):
			if isinstance(x, int):
				return x
			else:
				try:
					return int(x)
				except:
					return int(time.mktime(time.strptime(x, dateformat)))

		startTime = convertToTime(start)
		endTime = convertToTime(end)

		if startTime > endTime:
			raise Exception("Start time of range is greater than end time: [%d, %d]" % (start, end))

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

		# 0 for start time, 1 for end time
		insertarr(self.timeline, ( startTime, TimelineFilter.RANGE_BEGIN ), cmpfunc, unique=True)
		insertarr(self.timeline, ( endTime, TimelineFilter.RANGE_END ), cmpfunc, unique=True)
		self.condense()


	def condense(self):
		condensedTimeline = []
		idx = 0

		def traverse(idx):
			while idx < len(self.timeline) and self.timeline[idx][1] == TimelineFilter.RANGE_BEGIN:
				idx += 1

			while idx < len(self.timeline) and self.timeline[idx][1] == TimelineFilter.RANGE_END:
				end = self.timeline[idx][0]
				idx += 1

			last = None
			while idx < len(self.timeline) and self.timeline[idx][0] == end:
				last = self.timeline[idx]
				idx += 1

			if last is not None and last[1] == 0:
				return traverse(idx)
			return idx

		while idx < len(self.timeline):
			start = self.timeline[idx][0]
			end = None

			idx = traverse(idx + 1)
			end = self.timeline[idx - 1][0]

			condensedTimeline.append( ( start, TimelineFilter.RANGE_BEGIN ) )
			condensedTimeline.append( ( end, TimelineFilter.RANGE_END ) )

		self.timeline = condensedTimeline


	def invert(self, minStart=0, maxEnd=2 ** 32 - 1):
		inverted = TimelineFilter()

		endTime = self.timeline[0][0]

		if endTime > minStart:
			inverted.addTimeRange(minStart, endTime)

		idx = 1
		while idx < len(self.timeline) - 1:
			startTime = self.timeline[idx][0]
			endTime = self.timeline[idx + 1][0]

			if startTime < endTime:
				inverted.addTimeRange(startTime, endTime)

			idx += 2

		endTime = self.timeline[-1][0]
		if endTime < maxEnd:
			inverted.addTimeRange(endTime, maxEnd)

		return inverted


	def inTimeline(self, time, inclusive=True):
		idx = 0
		while idx < len(self.timeline) - 1:
			if self.timeline[idx][0] < time and self.timeline[idx + 1][0] > time:
				return True
			if inclusive and (self.timeline[idx][0] == time or self.timeline[idx + 1][0] == time):
				return True
			idx += 2
		return False


	def isEmpty(self):
		return len(self.timeline) == 0


#insert into sorted array
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
