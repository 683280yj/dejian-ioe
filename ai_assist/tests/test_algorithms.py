from django.test import SimpleTestCase

from ai_assist import algorithms as A


class StatsTests(SimpleTestCase):
    def test_z_and_safety_stock(self):
        z = A.z_for_service_level(0.95)
        self.assertAlmostEqual(z, 1.645, places=2)
        self.assertGreater(A.safety_stock(z, 2.0, 9), 0)

    def test_seasonal_ratio_shrinks_and_clamps(self):
        monthly = {m: 1.0 for m in range(1, 13)}
        monthly[1] = 10.0
        raw = monthly[1] / monthly[10]
        r = A.seasonal_ratio(monthly, 10, 1)
        self.assertLess(r, raw)
        self.assertLessEqual(r, 2.5)
        self.assertEqual(A.seasonal_ratio({}, 10, 1), 1.0)

    def test_budget_allocate_respects_budget(self):
        items = [A.KnapsackItem(key=str(i), cost=100.0 * (i + 1), value=10.0 * (3 - i), units=10, step=1) for i in range(3)]
        res = A.budget_allocate(items, 250)
        used = sum(q * it.cost / it.units for it in items for k, q in res.items() if k == it.key)
        self.assertLessEqual(used, 250 + 1e-6)
        self.assertEqual(res['0'], 10)  # 性价比最高的整单保留
