"""补货建议的「人话解释层」（2026-10-28 试点）。

设计口径（对齐 JadeAI 的 AI 功能模式）：
- 配置走环境变量：AI_EXPLAIN_ENABLED=1 开启；AI_API_BASE / AI_API_KEY / AI_API_MODEL
  配齐时用 LLM 生成解释（OpenAI 兼容 chat/completions，强约束 JSON 输出）；
- 任一环节失败（未配 key、超时、返回不合规）自动回退到规则解释——由结构化
  inputs/values 确定性生成，永远可用、数字永远与测算一致；
- 异常标记全部由规则从 values/inputs 检出（不依赖 LLM），LLM 只负责把话说顺；
- 解释只做展示，不参与任何写操作；采纳/忽略仍走原有流程。
"""
from __future__ import annotations

import json
import logging
import os
import urllib.request

from django.utils import timezone

logger = logging.getLogger(__name__)


def enabled() -> bool:
    return os.environ.get('AI_EXPLAIN_ENABLED', '0') == '1'


def _llm_config():
    base = os.environ.get('AI_API_BASE', '').rstrip('/')
    key = os.environ.get('AI_API_KEY', '')
    model = os.environ.get('AI_API_MODEL', '')
    if base and key and model:
        return base, key, model
    return None


def _f(d, key, default=None):
    try:
        v = d.get(key, default)
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def detect_anomalies(s) -> list:
    """从结构化取值检出值得采购注意的异常，返回 [{level, text}]。"""
    v, i = s.values or {}, s.inputs or {}
    out = []
    dhat = _f(v, 'd̂') or 0
    pos = _f(v, '库存位置') or 0
    lead = _f(i, '交期天') or 0
    qty_calc = _f(v, '测算量') or 0
    qty_ok = _f(v, '批准量')
    if qty_ok is None:
        qty_ok = float(s.quantity or 0)
    cover = (pos / dhat) if dhat > 0 else None
    if cover is not None and lead and cover < lead:
        out.append({'level': 'high', 'text': f'含在途仅够卖 {cover:.0f} 天，短于交期 {lead:.0f} 天，断货风险高'})
    if qty_ok == 0 and qty_calc > 0:
        out.append({'level': 'high', 'text': f'应补 {qty_calc:.0f} 瓶但预算/库容不足，本次未获批准'})
    elif 0 < qty_ok < qty_calc:
        out.append({'level': 'warn', 'text': f'建议量被预算/库容裁剪：测算 {qty_calc:.0f} 瓶 → 实际 {qty_ok:.0f} 瓶'})
    si = _f(v, '季节指数')
    if si is not None and si >= 1.15:
        out.append({'level': 'info', 'text': f'旺季系数 ×{si:.2f}，需求已按旺季放大'})
    elif si is not None and 0 < si <= 0.85:
        out.append({'level': 'info', 'text': f'淡季系数 ×{si:.2f}，需求已按淡季收缩'})
    ma = _f(v, 'MA') or 0
    sigma = _f(v, 'σ_d') or 0
    if ma > 0 and sigma / ma > 0.6:
        out.append({'level': 'warn', 'text': '近期销量波动大，预测不确定性高，建议小步补货'})
    eoq = _f(v, 'EOQ') or 0
    need = _f(v, 'S', 0) - pos if _f(v, 'S') is not None else 0
    if eoq > 0 and need > 0 and eoq > need:
        out.append({'level': 'info', 'text': '缺口不大，补货量主要由经济批量（EOQ）决定'})
    on_hand = _f(i, '在库') or 0
    transit = _f(i, '在途') or 0
    if transit > on_hand and transit > 0:
        out.append({'level': 'info', 'text': '在途多于在库，注意到货节奏与验收入库'})
    return out


def rule_explain(s) -> str:
    """规则版一句话解释：只用 values/inputs 里的数字拼装，缺字段自动降级。"""
    v, i = s.values or {}, s.inputs or {}
    name = (s.product.name if getattr(s, 'product_id', None) and getattr(s, 'product', None) else s.target_label) or s.title
    ma = _f(v, 'MA')
    dhat = _f(v, 'd̂')
    pos = _f(v, '库存位置')
    lead = _f(i, '交期天')
    qty = float(s.quantity or 0)
    case = _f(i, '箱规') or 0
    parts = []
    if ma is not None:
        seg = f'近段时间日均卖 {ma:.1f} 瓶'
        si = _f(v, '季节指数')
        if si is not None and abs(si - 1) >= 0.05 and dhat is not None:
            seg += f'，按季节修正后预测日需求 {dhat:.1f} 瓶'
        parts.append(seg)
    if pos is not None and (dhat or ma):
        d = pos / (dhat or ma)
        parts.append(f'现有库存加在途共 {pos:.0f} 瓶，约够卖 {d:.0f} 天')
    if qty > 0:
        seg = f'这次建议补 {qty:.0f} 瓶'
        if case:
            seg += f'（约 {qty / case:.0f} 箱）'
        if lead:
            seg += f'，覆盖交期 {lead:.0f} 天和安全库存'
        parts.append(seg)
    elif qty == 0:
        parts.append('这次不建议补货')
    return f'{name}：' + '；'.join(parts) + '。' if parts else ''


_LLM_SYSTEM = (
    '你是仓库采购助理。把给定的补货测算依据改写成一段口语化中文解释，让采购一眼看懂为什么补、补多少、'
    '有什么风险。只许使用给定数字，禁止编造任何新数字或新事实。不超过 120 字。'
    '必须只返回一个 JSON 对象：{"explanation": "解释文本"}。不要输出 JSON 以外的任何文字。'
    '（异常提醒由系统规则另行生成，你不用管。）'
)


def llm_explain(s, anomalies) -> str | None:
    cfg = _llm_config()
    if not cfg:
        return None
    base, key, model = cfg
    facts = {
        '商品': s.target_label or s.title,
        '建议补货量': f'{s.quantity} {s.unit}' if s.quantity is not None else None,
        '依据原文': s.rationale,
        '计算取值': s.values,
        '输入数据': {k: val for k, val in (s.inputs or {}).items() if k != '近期日销量(末14天)'},
        '规则检出的异常': [a['text'] for a in anomalies],
    }
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': _LLM_SYSTEM},
            {'role': 'user', 'content': json.dumps(facts, ensure_ascii=False)},
        ],
        'temperature': 0.3,
        'response_format': {'type': 'json_object'},
    }).encode('utf-8')
    req = urllib.request.Request(
        f'{base}/chat/completions', data=body, method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        content = data['choices'][0]['message']['content']
        parsed = json.loads(content)
        text = parsed.get('explanation')
        if not isinstance(text, str) or not text.strip() or len(text) > 300:
            return None
        return text.strip()
    except Exception:
        logger.warning('LLM 解释生成失败，回退规则解释', exc_info=True)
        return None


def ensure_explanation(s, allow_llm=True) -> bool:
    """为一条建议生成并落库解释；已有则跳过。返回是否新生成。"""
    if s.ai_explanation or not enabled():
        return False
    anomalies = detect_anomalies(s)
    text = llm_explain(s, anomalies) if allow_llm else None
    source = 'llm'
    if not text:
        text = rule_explain(s)
        source = 'rule'
    if not text:
        return False
    s.ai_explanation = text
    s.ai_anomalies = anomalies
    s.ai_source = source
    s.ai_generated_at = timezone.now()
    s.save(update_fields=['ai_explanation', 'ai_anomalies', 'ai_source', 'ai_generated_at'])
    return True


def fill_run_explanations(objs, cap=20):
    """测算完成后批量生成（LLM 慢，最多先生成前 cap 条，其余在页面侧用规则补齐）。"""
    if not enabled():
        return
    for s in objs[:cap]:
        try:
            ensure_explanation(s, allow_llm=True)
        except Exception:
            logger.warning('解释生成异常（suggestion=%s）', getattr(s, 'pk', None), exc_info=True)
            continue
