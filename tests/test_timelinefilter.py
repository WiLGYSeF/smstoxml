import datetime
import unittest

import timelinefilter


INPUT = 'in'
OUTPUT = 'out'
INVERTED = 'inverted'

TIMELINE_CHANGES = [
    {INPUT: (1, 3), OUTPUT: [(1, 0), (3, 1)], INVERTED: [(0, 0), (1, 1), (3, 0), (2 ** 32 - 1, 1)]},
    {
        INPUT: (6, 9),
        OUTPUT: [(1, 0), (3, 1), (6, 0), (9, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (6, 1), (9, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (5, 7),
        OUTPUT: [(1, 0), (3, 1), (5, 0), (9, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (5, 1), (9, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (8, 10),
        OUTPUT: [(1, 0), (3, 1), (5, 0), (10, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (5, 1), (10, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (7, 9),
        OUTPUT: [(1, 0), (3, 1), (5, 0), (10, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (5, 1), (10, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (4, 11),
        OUTPUT: [(1, 0), (3, 1), (4, 0), (11, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (4, 1), (11, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (13, 15),
        OUTPUT: [(1, 0), (3, 1), (4, 0), (11, 1), (13, 0), (15, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (4, 1), (11, 0), (13, 1), (15, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (15, 16),
        OUTPUT: [(1, 0), (3, 1), (4, 0), (11, 1), (13, 0), (16, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (4, 1), (11, 0), (13, 1), (16, 0), (2 ** 32 - 1, 1)],
    },
    {
        INPUT: (11, 13),
        OUTPUT: [(1, 0), (3, 1), (4, 0), (16, 1)],
        INVERTED: [(0, 0), (1, 1), (3, 0), (4, 1), (16, 0), (2 ** 32 - 1, 1)],
    },
]


class TimelineFilterTest(unittest.TestCase):
    def setUp(self):
        self.timeline = timelinefilter.TimelineFilter()

    def test_addTimeRange_success(self):
        for tc in TIMELINE_CHANGES:
            self.timeline.addTimeRange(tc[INPUT][0], tc[INPUT][1])
            self.assertListEqual(self.timeline.timeline, tc[OUTPUT])

    def test_addTimeRange_convert_success(self):
        self.timeline.addTimeRange('3', '12')
        self.assertListEqual(self.timeline.timeline, [(3, 0), (12, 1)])

        def ts(x):
            return (x - datetime.date(1970, 1, 1)).total_seconds()

        self.timeline.addTimeRange(ts(datetime.date(1997, 1, 31)), '1999-12-31 00:00:10')
        self.assertListEqual(self.timeline.timeline, [(3, 0), (12, 1), (854668800, 0), (946616410, 1)])

    def test_addTimeRange_fail(self):
        self.assertRaises(Exception, self.timeline.addTimeRange, 5, 1)

    def test_invert_success(self):
        for i in range(1, len(TIMELINE_CHANGES)):
            timeline = timelinefilter.TimelineFilter()

            for j in range(i):
                tc = TIMELINE_CHANGES[j]
                timeline.addTimeRange(tc[INPUT][0], tc[INPUT][1])

            self.assertListEqual(timeline.invert().timeline, tc[INVERTED])

    def test_inTimeline_success(self):
        for tc in TIMELINE_CHANGES:
            self.timeline.addTimeRange(tc[INPUT][0], tc[INPUT][1])

        self.assertTrue(self.timeline.inTimeline(1))
        self.assertTrue(self.timeline.inTimeline(3))
        self.assertTrue(self.timeline.inTimeline(7))
        self.assertTrue(self.timeline.inTimeline(9.9))

    def test_inTimeline_fail(self):
        for tc in TIMELINE_CHANGES:
            self.timeline.addTimeRange(tc[INPUT][0], tc[INPUT][1])

        self.assertFalse(self.timeline.inTimeline(3.5))
        self.assertFalse(self.timeline.inTimeline(3, inclusive=False))

    def test_isEmpty_success(self):
        self.assertTrue(self.timeline.isEmpty())

        for tc in TIMELINE_CHANGES:
            self.timeline.addTimeRange(tc[INPUT][0], tc[INPUT][1])

        self.assertFalse(self.timeline.isEmpty())
