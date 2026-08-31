import unittest

from app.models.report import DailyReport
from app.services import report_service


class RecordingQuery:
    def __init__(self):
        self.filters = []
        self.calls = []

    def filter(self, *criteria):
        self.calls.append("filter")
        self.filters.extend(criteria)
        return self

    def count(self):
        self.calls.append("count")
        return 3

    def order_by(self, *_args):
        self.calls.append("order_by")
        return self

    def offset(self, _value):
        self.calls.append("offset")
        return self

    def limit(self, _value):
        self.calls.append("limit")
        return self

    def all(self):
        self.calls.append("all")
        return ["report"]


class RecordingSession:
    def __init__(self):
        self.query_object = RecordingQuery()

    def query(self, model):
        self.model = model
        return self.query_object


class ReportFilterTest(unittest.TestCase):
    def test_filters_are_applied_before_count_and_pagination(self):
        db = RecordingSession()

        items, total = report_service.get_reports(
            db, user_id=7, page=2, page_size=10, status="completed", days="7"
        )

        self.assertIs(db.model, DailyReport)
        self.assertEqual(items, ["report"])
        self.assertEqual(total, 3)
        self.assertEqual(len(db.query_object.filters), 3)
        self.assertLess(db.query_object.calls.index("count"), db.query_object.calls.index("offset"))
        self.assertEqual(db.query_object.calls[-3:], ["offset", "limit", "all"])

    def test_rejects_unknown_filter_values(self):
        db = RecordingSession()

        with self.assertRaises(ValueError):
            report_service.get_reports(db, user_id=7, status="unknown")
        with self.assertRaises(ValueError):
            report_service.get_reports(db, user_id=7, days="365")
