import unittest
from datetime import date, datetime, timezone
from app.daily_plan import DHAKA, plan_day, current_plan, should_generate, should_publish

class DailyPlanTests(unittest.TestCase):
    def test_local_calendar_date(self):
        p = current_plan(datetime(2026, 11, 15, 19, 30, tzinfo=timezone.utc), owner_id="owner")
        self.assertEqual(p.local_date, date(2026, 11, 16))
    def test_same_day_same_key(self):
        self.assertEqual(plan_day(date(2026, 11, 16), owner_id="owner").key,
                         plan_day(date(2026, 11, 16), owner_id="owner").key)
    def test_one_per_day(self):
        p = plan_day(date(2026, 11, 16), owner_id="owner")
        now = datetime(2026, 11, 16, 10, tzinfo=DHAKA)
        self.assertTrue(should_generate(p, now, existing_keys=set()))
        self.assertFalse(should_generate(p, now, existing_keys={p.key}))
    def test_not_before_discovery(self):
        p = plan_day(date(2026, 11, 16), owner_id="owner")
        self.assertFalse(should_generate(p, datetime(2026, 11, 16, 6, tzinfo=DHAKA), existing_keys=set()))
    def test_publish_requires_approval_and_time(self):
        p = plan_day(date(2026, 11, 16), owner_id="owner")
        self.assertFalse(should_publish(p, datetime(2026, 11, 16, 20, tzinfo=DHAKA), approved=False))
        self.assertFalse(should_publish(p, datetime(2026, 11, 16, 18, tzinfo=DHAKA), approved=True))
        self.assertTrue(should_publish(p, datetime(2026, 11, 16, 19, tzinfo=DHAKA), approved=True))
    def test_naive_time_rejected(self):
        p = plan_day(date(2026, 11, 16), owner_id="owner")
        with self.assertRaises(ValueError):
            should_generate(p, datetime(2026, 11, 16, 12), existing_keys=set())

if __name__ == "__main__":
    unittest.main()
