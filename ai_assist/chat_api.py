"""Server-side model access for the replenishment assistant.

Function calling: read-only tools execute server-side and feed results back;
the write tool (adopt) only returns a pending-confirm action. Purchase actions
remain in the rule engine / existing adopt entry.
"""
import json
import logging
import os
import urllib.request

from . import tools as _tools

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3

SYSTEM_PROMPT = (
    '你是筹策进销存里的补货与运营决策助手。必须用提供的工具查询实时数据后再回答，'
    '不要编造商品、销量、库存、交期、价格或单据状态。用专业、简洁自然的中文回答；数字和单位必须与数据严格一致。\n'
    '企业核心基线：19个季度累计销售16,189箱(890.78万元)，采购79笔(81.18吨)，期末库存约4,200箱(4.9季度均销)，毛利率28.6%，滞留分63，年周转3.1次。\n'
    '优化后目标测算：毛利率31.8%(+3.2pct)，滞留分38(-25分)，周转4.2次(+35%)，市场份额14.1%(+1.7pct)，平均库存压降26%。\n'
    '采销策略：采购端MA28×季节系数结合95%服务水平(z=1.645)与60天覆盖上限；销售端低中高三档价格带(常规55/78/205元)分市场精准投放与增量毛利止损。\n'
    '工具使用规则：\n'
    '1. 涉及库存、销量、建议、草稿等实时数据的问题，先调用对应查询工具，基于返回数据作答。\n'
    '2. 用户明确要为补货建议生成采购草稿时，调用 adopt_suggestions 并传入建议编号；'
    '系统会让用户确认后才执行，你不要声称已完成下单或改库存。\n'
    '3. 一次回答最多连续调用 3 轮工具。'
)


def configured():
    return all(os.environ.get(name) for name in ('AI_API_BASE', 'AI_API_KEY', 'AI_API_MODEL'))


def _suggestion_facts(items):
    facts = []
    for suggestion in items[:10]:
        facts.append({
            '商品': suggestion.target_label or suggestion.title,
            '建议补货量': str(suggestion.quantity),
            '单位': getattr(suggestion, 'unit', ''),
            '测算依据': getattr(suggestion, 'rationale', ''),
            '计算结果': suggestion.values or {},
            '异常提示': suggestion.ai_anomalies or [],
        })
    return facts


def _post(body):
    base = os.environ['AI_API_BASE'].rstrip('/')
    req = urllib.request.Request(
        base + '/chat/completions', data=body, method='POST',
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + os.environ['AI_API_KEY']})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def answer(tenant, items, message, history=()):
    """模型 + 工具循环。返回 (文本, 动作)；失败返回 (None, None) 让规则层接管。

    动作形状与规则层一致：{'adopt_pks': [...]}，由前端走既有采纳入口执行。
    """
    if not configured():
        return None, None
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'system', 'content': '当前企业的待确认补货建议：'
         + json.dumps(_suggestion_facts(items), ensure_ascii=False, default=str)[:12000]},
    ]
    for turn in list(history)[-6:]:
        if isinstance(turn, dict) and turn.get('role') in ('user', 'assistant'):
            content = turn.get('content')
            if isinstance(content, str):
                messages.append({'role': turn['role'], 'content': content[:1000]})
    messages.append({'role': 'user', 'content': message[:1000]})

    action = None
    try:
        for _round in range(MAX_TOOL_ROUNDS):
            data = _post(json.dumps({
                'model': os.environ['AI_API_MODEL'], 'messages': messages,
                'tools': _tools.TOOL_SPECS, 'tool_choice': 'auto',
                'temperature': 0.2, 'max_tokens': 450}).encode())
            choice = data['choices'][0]['message']
            tool_calls = choice.get('tool_calls')
            if not tool_calls:
                text = choice.get('content')
                return (text.strip()[:1200] if isinstance(text, str) and text.strip() else None), action
            messages.append({'role': 'assistant', 'content': choice.get('content') or '',
                             'tool_calls': tool_calls})
            for call in tool_calls:
                name = call['function']['name']
                try:
                    args = json.loads(call['function'].get('arguments') or '{}')
                except ValueError:
                    args = {}
                result = _tools.execute(name, args, tenant)
                if '__action__' in result:
                    action = result.pop('__action__') or action
                    result['说明'] = '已收到生成草稿请求，等用户在对话里确认后执行。请告诉用户回「好」确认。'
                messages.append({'role': 'tool', 'tool_call_id': call.get('id'),
                                 'content': _tools.tool_result_text(result)})
        return '这个问题我查了几轮数据还没理顺，稍后再试试，或换个问法。', action
    except Exception as exc:
        logger.warning('筹策助手模型请求失败，已回退规则回复: %s', type(exc).__name__)
        return None, None
