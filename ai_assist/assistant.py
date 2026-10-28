"""筹策助手：客服式对话层（仿 JadeAI 的 AI Chat Assistant 形态）。

结合当前租户的补货建议回答问题、先讲情况再给建议；
生成采购草稿必须由用户在对话里明确确认后，才调用既有 adopt 服务——AI 不自作主张。
采购动作由规则层处理；问答可通过 AI_API_* 接入模型，失败时回退规则回复。
"""
from . import explain as _explain
from . import business_answers as _biz

_CN_NUM = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
_CONFIRM = {'好', '好的', '可以', '确认', '行', '嗯', '要', '生成', '就这样', 'ok', 'OK', 'Ok'}
_CANCEL = ('不', '别', '取消', '算了', '不要', '不用', '等等', '先不')


def _name(s):
    return getattr(s, 'target_label', '') or getattr(s, 'title', '') or '该商品'


def _cover_days(s):
    v = getattr(s, 'values', None) or {}
    pos = _explain._f(v, '库存位置')
    d = _explain._f(v, 'd̂') or _explain._f(v, 'MA')
    if pos is None or not d:
        return None
    return pos / d


def _rank(items):
    return sorted(items, key=lambda s: (_cover_days(s) is None, _cover_days(s) or 0))


def _pick(items, message):
    """按「第N条」或产品名定位一条；定位不到返回 None。"""
    import re
    m = re.search(r'第\s*([一二三四五六七八九\d])\s*条', message or '')
    if m:
        n = _CN_NUM.get(m.group(1)) or (int(m.group(1)) if m.group(1).isdigit() else None)
        if n and 1 <= n <= len(items):
            return items[n - 1]
    for s in items:
        name = _name(s)
        if name and name in message:
            return s
    for s in items:
        for part in _name(s).replace('·', ' ').split():
            if len(part) >= 2 and part in message:
                return s
    return None


def briefing(items):
    if not items:
        return '你好，我是筹策助手。目前没有待处理的补货建议，库存这边暂时不用操心。有需要随时喊我。'
    top = _rank(items)[0]
    lines = [f'你好，我是筹策助手。今天有 {len(items)} 条补货建议等你确认，最急的是 {_name(top)}：{_explain.short_line(top)}']
    lines.append('你可以直接问我「为什么补这么多」「哪条最急」，或者说「生成草稿」，我确认后帮你办。')
    return '\n'.join(lines)


def _explain_text(s):
    parts = [_explain.short_line(s)]
    full = getattr(s, 'ai_explanation', '') or _explain.rule_explain(s)
    if full:
        parts.append(full)
    anomalies = getattr(s, 'ai_anomalies', None) or _explain.detect_anomalies(s)
    for a in anomalies[1:]:
        parts.append('另外提醒：' + a['text'] + '。')
    return '\n'.join(parts)


def _ask_adopt(items, message, state):
    if any(k in message for k in ('全部', '都', '所有')):
        targets = list(items)
        state['pending_adopt'] = [s.pk for s in targets]
        return (f'好的，{len(targets)} 条建议我都给你生成采购草稿。确认一下：回「好」我就办，想取消说「算了」。', state)
    s = _pick(items, message) or _rank(items)[0]
    state['pending_adopt'] = [s.pk]
    return (f'我先按这条来：{_name(s)}，{_explain.short_line(s)}\n'
            '回「好」我就生成采购草稿；想换一条，直接说产品名或「第几条」。', state)


def _confirm_adopt(items, state):
    """用户确认后不直接写库：返回要执行的 adopt 动作，由前端走既有采纳入口（带 CSRF）完成。"""
    pks = state.pop('pending_adopt', [])
    targets = [s for s in items if s.pk in pks]
    if not targets:
        return '那几条建议已经不在待处理列表里了，可能刚被处理过。', state, None
    names = '、'.join(_name(s) for s in targets)
    return f'好，我这就给 {names} 生成采购草稿。', state, {'adopt_pks': pks}


def reply(items, message, state=None):
    """返回 (回复文本, 新状态, 动作)。动作 None 或 {'adopt_pks': [...]}，由前端走既有采纳入口执行。"""
    state = dict(state or {})
    msg = (message or '').strip()

    # 业务战略、数据分析与解决方案全局问答（无需依赖当前是否有未处理补货项）
    if any(k in msg for k in ('原始数据', '数据来源', '数据清单', '数据完备', '清洗', '对齐', '脱敏', '数据分析')):
        return _biz.answer_data_analysis(), state, None
    if any(k in msg for k in ('痛点', '基线', '优化目标', '约束', '边界', '规则', '预算上限', '发现的问题')):
        return _biz.answer_problem_and_constraints(), state, None
    if any(k in msg for k in ('采购方案', '销售方案', '模型', '定价', '促销', '滞留分', '算法', '如何辅助', '怎么介入', '解决方案')):
        return _biz.answer_solutions(), state, None
    if any(k in msg for k in ('优化前后', '成果', '对比', '敏感性', '波动', '预测', '份额', '周转', '我的成果')):
        return _biz.answer_outcomes_and_sensitivity(), state, None
    if any(k in msg for k in ('创新点', '总结', '效益', '可行性', '发展前景', '总结创新')):
        return _biz.answer_summary(), state, None

    if not items:
        return '目前没有待处理的补货建议。你先去点一次「重新测算」，有建议了我再帮你看。', state, None

    if state.get('pending_adopt'):
        if msg in _CONFIRM or msg.startswith(('好', '可以', '确认')):
            return _confirm_adopt(items, state)
        if any(k in msg for k in _CANCEL) and not any(k in msg for k in ('为什么', '最急', '解释')):
            state.pop('pending_adopt', None)
            return '好，那先不生成。需要的时候再喊我。', state, None
        if any(k in msg for k in ('为什么', '原因', '解释', '最急', '优先', '汇总', '哪些')):
            text, state, _a = _route(items, msg, state)
            return text + '\n（刚才问你的草稿还没定：回「好」生成，说「算了」取消。）', state, None
        text, state = _ask_adopt(items, msg, state)
        return text, state, None

    return _route(items, msg, state)


def _route(items, msg, state):
    # 业务战略与数据方案深度问答
    if any(k in msg for k in ('原始数据', '数据来源', '数据清单', '数据完备', '清洗', '对齐', '脱敏', '数据分析')):
        return _biz.answer_data_analysis(), state, None
    if any(k in msg for k in ('痛点', '基线', '优化目标', '约束', '边界', '规则', '预算上限', '发现的问题')):
        return _biz.answer_problem_and_constraints(), state, None
    if any(k in msg for k in ('采购方案', '销售方案', '模型', '定价', '促销', '滞留分', '算法', '如何辅助', '怎么介入', '解决方案')):
        return _biz.answer_solutions(), state, None
    if any(k in msg for k in ('优化前后', '成果', '对比', '敏感性', '波动', '预测', '份额', '周转', '我的成果')):
        return _biz.answer_outcomes_and_sensitivity(), state, None
    if any(k in msg for k in ('创新点', '总结', '效益', '可行性', '发展前景', '总结创新')):
        return _biz.answer_summary(), state, None

    if any(k in msg for k in ('草稿', '下单', '采购单')) or msg in ('生成', '订货'):
        text, state = _ask_adopt(items, msg, state)
        return text, state, None
    if any(k in msg for k in ('为什么', '原因', '解释', '咋', '怎么算')):
        s = _pick(items, msg) or _rank(items)[0]
        return _explain_text(s), state, None
    if any(k in msg for k in ('最急', '优先', '断货', '先补', '紧急')):
        ranked = _rank(items)
        top = ranked[0]
        d = _cover_days(top)
        head = f'最急的是 {_name(top)}' + (f'，只够卖约 {d:.0f} 天' if d is not None else '') + '。'
        rest = '；'.join(f'{_name(s)}（约 {_cover_days(s):.0f} 天）' for s in ranked[1:3] if _cover_days(s) is not None)
        return head + _explain.short_line(top) + (f'\n其次是：{rest}。' if rest else ''), state, None
    if any(k in msg for k in ('汇总', '今天', '情况', '有哪些', '建议', '你好', '您好', 'hi', '在吗')) or not msg:
        lines = [f'一共 {len(items)} 条补货建议，从最急的排起：']
        for i, s in enumerate(_rank(items), 1):
            lines.append(f'{i}. {_name(s)}：{_explain.short_line(s)}')
        lines.append('想给哪条生成草稿，说产品名或「第几条」就行，我会先跟你确认。')
        return '\n'.join(lines), state, None
    return ('我主要帮你看补货建议：可以问「哪条最急」「为什么补这么多」，'
            '或者说「生成草稿」让我帮你办（办之前会先跟你确认）。\n最急的一条是：'
            + _explain.short_line(_rank(items)[0])), state, None
