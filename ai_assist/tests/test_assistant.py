from types import SimpleNamespace
from unittest.mock import patch
import io
import json
import os

from django.test import SimpleTestCase, TestCase, RequestFactory

from ai_assist import assistant, chat_api, tools, views


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

    def test_model_answer_uses_current_suggestions(self):
        class Response:
            def __enter__(self): return io.BytesIO(json.dumps({'choices': [{'message': {'content': '先看流通款，约够卖 9 天。'}}]}).encode())
            def __exit__(self, *args): pass

        with patch.dict(os.environ, {'AI_API_BASE': 'https://example.invalid/v1',
                                     'AI_API_KEY': 'test-key', 'AI_API_MODEL': 'test-model'}), \
             patch('ai_assist.chat_api.urllib.request.urlopen', return_value=Response()) as call:
            text, action = chat_api.answer('tenant', self.items, '哪条最急')
        self.assertIn('9 天', text)
        self.assertIsNone(action)
        payload = json.loads(call.call_args.args[0].data)
        self.assertIn('代理酱香·流通款', payload['messages'][1]['content'])
        self.assertIn('tools', payload)
        self.assertEqual(call.call_args.args[0].full_url, 'https://example.invalid/v1/chat/completions')

    def test_model_tool_call_executes_and_feeds_back(self):
        first = {'choices': [{'message': {'tool_calls': [
            {'id': 'call_1', 'function': {'name': 'query_stock',
                                          'arguments': '{"keyword": "酱香"}'}}]}}]}
        second = {'choices': [{'message': {'content': '酱香款库存 144 箱。'}}]}

        class Response:
            def __init__(self, body): self._b = body
            def __enter__(self): return io.BytesIO(json.dumps(self._b).encode())
            def __exit__(self, *args): pass

        responses = [Response(first), Response(second)]
        with patch.dict(os.environ, {'AI_API_BASE': 'https://example.invalid/v1',
                                     'AI_API_KEY': 'test-key', 'AI_API_MODEL': 'test-model'}), \
             patch('ai_assist.chat_api.urllib.request.urlopen',
                   side_effect=lambda req, *a, **k: responses.pop(0)) as call:
            text, action = chat_api.answer('tenant', self.items, '酱香库存多少')
        self.assertIn('144', text)
        self.assertIsNone(action)
        # 第二次请求应带上一轮的工具结果
        second_payload = json.loads(call.call_args.args[0].data)
        self.assertEqual(second_payload['messages'][-1]['role'], 'tool')

    def test_model_adopt_tool_returns_pending_action(self):
        msg = {'choices': [{'message': {'tool_calls': [
            {'id': 'call_1', 'function': {'name': 'adopt_suggestions',
                                          'arguments': '{"ids": [1]}'}}]}}]}
        after = {'choices': [{'message': {'content': '好，请回「好」确认。'}}]}

        class Response:
            def __init__(self, body): self._b = body
            def __enter__(self): return io.BytesIO(json.dumps(self._b).encode())
            def __exit__(self, *args): pass

        responses = [Response(msg), Response(after)]
        with patch.dict(os.environ, {'AI_API_BASE': 'https://example.invalid/v1',
                                     'AI_API_KEY': 'test-key', 'AI_API_MODEL': 'test-model'}), \
             patch('ai_assist.chat_api.urllib.request.urlopen',
                   side_effect=lambda req, *a, **k: responses.pop(0)), \
             patch.object(tools.Suggestion.objects, 'filter',
                          return_value=SimpleNamespace(values_list=lambda *a, **k: [1])) as _qs:
            text, action = chat_api.answer('tenant', self.items, '给第一条生成草稿')
        self.assertEqual(action, {'adopt_pks': [1]})
        self.assertIn('确认', text)

    def test_toolbox_write_tools_whitelisted(self):
        for name, (_fn, is_write) in tools.TOOLBOX.items():
            if name not in ('adopt_suggestions', 'create_product'):
                self.assertFalse(is_write)


    def test_purchase_confirmation_does_not_call_model(self):
        request = RequestFactory().post('/ai/assistant/chat/', {'message': '生成草稿'})
        request.user = SimpleNamespace(is_authenticated=True)
        request.tenant = object()
        request.session = {}
        with patch('ai_assist.views.restock_suggestions', return_value=(None, self.items)), \
             patch('ai_assist.views.chat_api.answer') as model:
            response = views.assistant_chat(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(json.loads(response.content)['action'])
        self.assertTrue(request.session['assistant_state']['pending_adopt'])
        model.assert_not_called()


class CreateProductToolTests(SimpleTestCase):
    def test_create_product_tool_validates_without_db(self):
        result = tools.execute('create_product', {'name': '', 'price': 1, 'cost': 2}, 'tenant')
        self.assertIn('error', result)
        result = tools.execute('create_product', {'name': 'X', 'price': 'abc', 'cost': 2}, 'tenant')
        self.assertIn('error', result)
        result = tools.execute('create_product', {'name': 'X', 'price': -1, 'cost': 2}, 'tenant')
        self.assertIn('error', result)


class CreateProductConfirmFlowTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from tenancy.models import Membership, Role, Tenant
        self.tenant = Tenant.objects.create(name='测试企业', code='test-ai-prod')
        self.boss = get_user_model().objects.create_user('boss1', password='x')
        Membership.objects.create(user=self.boss, tenant=self.tenant, role=Role.BOSS)
        self.sales = get_user_model().objects.create_user('sales1', password='x')
        Membership.objects.create(user=self.sales, tenant=self.tenant, role=Role.SALES)
        self.spec = {'name': '酱香新品', 'price': '128.00', 'cost': '66.00',
                     'category': '酱香型', 'specification': '53度/500ml'}

    def _request(self, user, state, message):
        from tenancy.models import Membership, Role
        request = RequestFactory().post('/ai/assistant/chat/', {'message': message})
        request.user = user
        request.tenant = self.tenant
        request.membership = Membership.objects.get(user=user, tenant=self.tenant)
        request.session = dict(state) if state else {}
        return request

    def test_confirm_creates_product(self):
        from inventory.models import Product
        request = self._request(self.boss, {'pending_create_product': self.spec}, '好')
        request.session['assistant_state'] = {'pending_create_product': self.spec}
        with patch('ai_assist.views.restock_suggestions', return_value=(None, [])):
            response = views.assistant_chat(request)
        self.assertEqual(response.status_code, 200)
        p = Product.objects.get(tenant=self.tenant, name='酱香新品')
        self.assertEqual(p.category.name, '酱香型')
        self.assertTrue(p.barcode)
        self.assertNotIn('pending_create_product', request.session.get('assistant_state', {}))

    def test_cancel_does_not_create(self):
        from inventory.models import Product
        request = self._request(self.boss, {'pending_create_product': self.spec}, '算了')
        request.session['assistant_state'] = {'pending_create_product': self.spec}
        with patch('ai_assist.views.restock_suggestions', return_value=(None, [])):
            views.assistant_chat(request)
        self.assertFalse(Product.objects.filter(tenant=self.tenant, name='酱香新品').exists())

    def test_non_boss_denied(self):
        from inventory.models import Product
        request = self._request(self.sales, {'pending_create_product': self.spec}, '好')
        request.session['assistant_state'] = {'pending_create_product': self.spec}
        with patch('ai_assist.views.restock_suggestions', return_value=(None, [])):
            response = views.assistant_chat(request)
        self.assertIn('老板', json.loads(response.content)['reply'])
        self.assertFalse(Product.objects.filter(tenant=self.tenant, name='酱香新品').exists())
