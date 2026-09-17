import unittest
from unittest.mock import patch

from backend.app.core.anomalies import BOMAnomalyDetector


class _FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, _query):
        return self

    def fetchall(self):
        return self._rows


class _FakeConnection:
    def __init__(self, rows):
        self._cursor = _FakeCursor(rows)

    def cursor(self):
        return self._cursor

    def close(self):
        pass


class StageViolationTests(unittest.TestCase):
    def _detect(self, parent_stage, child_stage):
        rows = [{
            "HDR_MATERIAL": "PARENT-001",
            "HDR_MATL_GROUP": parent_stage,
            "COMP_MATERIAL": "CHILD-001",
            "COMP_MATL_GROUP": child_stage,
            "PLANT": "PLT01",
        }]
        detector = BOMAnomalyDetector(graph=None)
        with patch(
            "backend.app.core.anomalies.get_connection",
            return_value=_FakeConnection(rows),
        ):
            return detector.detect_stage_violations()

    def test_later_stage_parent_with_earlier_component_is_valid(self):
        self.assertEqual(self._detect("FPN", "PKGD"), [])

    def test_earlier_stage_parent_with_later_component_is_violation(self):
        anomalies = self._detect("PKGD", "FPN")
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["type"], "STAGE_VIOLATION")


if __name__ == "__main__":
    unittest.main()
