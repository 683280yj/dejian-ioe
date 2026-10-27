from types import SimpleNamespace

from django.test import SimpleTestCase

from ai_assist import assistant


def _sug(pk, name, qty, pos, dhat, lead=12, case=6):
    return SimpleNamespace(
        pk=pk, target_label=name, title=name, quantity=qty,
        values={'库存位置': pos, 'd̂': dhat, 'MA': dhat, '季节指数': 1.0},
        inputs={'交期天': lead, '箱规': case},
        ai_explanation='', ai_anomalies=[
            {'code': 'cover_lt_lead', 'level': 'high', 'text': f'含在途仅够卖 {pos / dhat:.0f} 天，短于交期 {lead} 天，断货风险高'}
        ] if pos / dhat < lead else [],
    )


class AssistantReplyTests(SimpleTestCase):
    def setUp(self):
        self.items = [
            _sug(1, '代理酱香·流通款', 408, 144, 15.3),
            _sug(2, '体验酱香·年份窖藏10', 1002, 424, 35.3, lead=7),
            _sug(3, '代理酱香·窖藏款', 186, 146, 7.6),
        ]

    def test_briefing_mentions_count_and_most_urgent(self):
        text = assistant.briefing(self.items)
        self.assertIn('3 条', text)
        self.assertIn('代理酱香·流通款', text)

    def test_most_urgent_ranked_by_cover_days(self):
        text, _, _a = assistant.reply(self.items, '哪条最急')
        self.assertIn('代理酱香·流通款', text)

    def test_why_returns_explanation(self):
        text, _, _a = assistant.reply(self.items, '为什么第一条补这么多')
        self.assertIn('408', text)

    def test_adopt_requires_confirmation_then_emits_action(self):
        text, state, action = assistant.reply(self.items, '生成草稿')
        self.assertIsNone(action)
        self.assertTrue(state.get('pending_adopt'))
        text, state, action = assistant.reply(self.items, '好', state)
        self.assertFalse(state.get('pending_adopt'))
        self.assertEqual(action, {'adopt_pks': state.get('pending_adopt') or action['adopt_pks']})
        self.assertEqual(len(action['adopt_pks']), 1)

    def test_adopt_cancel_emits_no_action(self):
        _, state, _a = assistant.reply(self.items, '给第二条生成草稿')
        self.assertEqual(state.get('pending_adopt'), [2])
        text, state, action = assistant.reply(self.items, '算了', state)
        self.assertIsNone(action)
        self.assertFalse(state.get('pending_adopt'))

    def test_empty_items(self):
        text, _, _a = assistant.reply([], '哪条最急')
        self.assertIn('没有待处理', text)
