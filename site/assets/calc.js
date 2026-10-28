/* 筹策 · 补货测算（单品）
 * 公式与 dejian-ioe main@1ec2c9a 的 ai_assist/workflows/replenish.py、ai_assist/algorithms.py 一致：
 *   d̂ = MA(28) × 季节系数；σ_LT = √(L·σ² + d̂²·σ_L²)；SS = z·σ_LT
 *   ROP = d̂·L + SS；S = d̂·(L+R) + SS；库存位置 = 在库 + 在途
 *   pos < S 时：Q = min(max(S − pos, EOQ), 60·d̂ − pos)，再向上取到箱规、不低于起订量
 *   EOQ = √(2·D·K / (进价·h))
 * 单品页面不含多品之间的预算 / 库容分配（系统里在全部商品之间统一分配）。
 * 用法：<div id="chouce-calc"></div><script src="assets/calc.js" defer></script>
 */
(function () {
  var Z = [[0.50,0],[0.80,0.8416],[0.85,1.0364],[0.90,1.2816],[0.95,1.6449],[0.97,1.8808],[0.98,2.0537],[0.99,2.3263],[0.995,2.5758],[0.999,3.0902]];
  function zFor(p){p=Math.min(Math.max(p,0.5),0.999);for(var i=0;i<Z.length-1;i++){var a=Z[i],b=Z[i+1];if(p>=a[0]&&p<=b[0])return a[1]+(b[1]-a[1])*(p-a[0])/(b[0]-a[0]);}return Z[Z.length-1][1];}
  function mean(a){return a.length?a.reduce(function(s,v){return s+v;},0)/a.length:0;}
  function pstdev(a){if(a.length<2)return 0;var m=mean(a);return Math.sqrt(a.reduce(function(s,v){return s+(v-m)*(v-m);},0)/a.length);}
  function roundUpTo(q,mult,min){if(q<=0)return 0;mult=Math.max(Math.floor(mult||1),1);var r=Math.ceil(q/mult)*mult;if(min&&r<min)r=Math.ceil(min/mult)*mult;return r;}
  function eoq(D,K,c,h){var H=c*h;if(D<=0||H<=0||K<=0)return 0;return Math.sqrt(2*D*K/H);}

  function compute(x){
    var R=7, cover=60, K=300, h=0.12;
    var z=zFor(x.service);
    var ma=mean(x.sales.slice(-28));
    var sigma=pstdev(x.sales.slice(-56));
    var dhat=ma*x.season;
    var sigmaLT=Math.sqrt(x.L*sigma*sigma+dhat*dhat*x.sL*x.sL);
    var ss=z*sigmaLT, rop=dhat*x.L+ss, S=dhat*(x.L+R)+ss;
    var pos=x.onHand+x.transit;
    var cap=Math.max(0,cover*dhat-pos);
    var e=eoq(ma*365,K,x.cost,h);
    var need=Math.max(0,S-pos), raw=0;
    if(pos<S) raw=Math.min(Math.max(need,e),cap);
    var qty=roundUpTo(raw,x.caseSize,x.moq);
    var days=dhat>0?pos/dhat:Infinity;
    var sev=days<x.L?'高':(pos<rop?'中':'低');
    return {z:z,ma:ma,sigma:sigma,dhat:dhat,ss:ss,rop:rop,S:S,pos:pos,cap:cap,eoq:e,need:need,raw:raw,qty:qty,cases:qty/(x.caseSize||1),days:days,sev:sev,R:R,cover:cover};
  }

  var css='.cc{font:inherit;color:inherit;display:grid;gap:20px;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr)}'
   +'@media(max-width:760px){.cc{grid-template-columns:1fr}}'
   +'.cc fieldset{border:1px solid currentColor;border-color:rgba(127,127,127,.35);border-radius:12px;padding:16px;margin:0;display:grid;gap:10px}'
   +'.cc legend{padding:0 6px;font-weight:700}'
   +'.cc label{display:grid;gap:4px;font-size:14px}'
   +'.cc input,.cc textarea{font:inherit;font-size:15px;padding:8px 10px;border-radius:8px;border:1px solid rgba(127,127,127,.45);background:transparent;color:inherit;width:100%;box-sizing:border-box}'
   +'.cc textarea{min-height:72px;font-family:"Geist Mono",ui-monospace,monospace;font-size:13px}'
   +'.cc .row{display:grid;grid-template-columns:1fr 1fr;gap:10px}'
   +'.cc .out{border-radius:12px;padding:18px;background:rgba(135,53,59,.08);display:grid;gap:10px}'
   +'.cc .big{font-size:40px;font-weight:800;line-height:1.1}'
   +'.cc ol{margin:0;padding-left:20px;display:grid;gap:6px;font-size:14px}'
   +'.cc .mono{font-family:"Geist Mono",ui-monospace,monospace}'
   +'.cc .tag{display:inline-block;padding:2px 10px;border-radius:99px;background:#87353b;color:#fff;font-size:13px}'
   +'.cc summary{cursor:pointer;font-size:14px;opacity:.8;min-height:44px;display:flex;align-items:center}'
   +'.cc .note{font-size:12px;opacity:.7}';

  function f(n,d){if(!isFinite(n))return '—';return (Math.round(n*Math.pow(10,d||0))/Math.pow(10,d||0)).toLocaleString('zh-CN');}

  function mount(el){
    var st=document.createElement('style');st.textContent=css;document.head.appendChild(st);
    el.innerHTML='<form class="cc" onsubmit="return false">'
     +'<fieldset><legend>填入一款酒的数据</legend>'
     +'<label>近 28 天每天卖出的瓶数（用逗号或空格分开）<textarea name="sales">6 4 8 5 7 3 9 6 5 7 4 8 6 5 7 6 4 9 5 6 8 7 5 6 4 7 6 8</textarea></label>'
     +'<div class="row"><label>现有库存（瓶）<input name="onHand" type="number" min="0" value="60"></label><label>在途（瓶）<input name="transit" type="number" min="0" value="0"></label></div>'
     +'<label>供应商交期（天）<input name="L" type="number" min="0" value="10"></label>'
     +'<div class="row"><label>箱规（瓶/箱）<input name="caseSize" type="number" min="1" value="6"></label><label>起订量（瓶）<input name="moq" type="number" min="0" value="12"></label></div>'
     +'<details class="more"><summary>更多参数</summary><div style="display:grid;gap:10px;margin-top:10px">'
     +'<div class="row"><label>交期波动（± 天）<input name="sL" type="number" min="0" value="2"></label><label>进价（元/瓶）<input name="cost" type="number" min="0" value="300"></label></div>'
     +'<label>季节系数<input name="season" type="number" step="0.05" min="0.5" max="2.5" value="1"><span class="note">系统里按历史销量自动算出，这里可以手动调</span></label>'
     +'<label>服务水平（不缺货概率）<input name="service" type="number" step="0.01" min="0.5" max="0.999" value="0.95"></label>'
     +'</div></details>'
     +'</fieldset><div class="out" aria-live="polite"></div></form>';
    var form=el.querySelector('form'), out=el.querySelector('.out');
    function num(n){var v=parseFloat(form.elements[n].value);return isFinite(v)?v:0;}
    function run(){
      var sales=(form.elements.sales.value.match(/[\d.]+/g)||[]).map(Number).filter(isFinite);
      if(!sales.length){out.innerHTML='<p>请填入每天的销量。</p>';return;}
      var x={sales:sales,onHand:num('onHand'),transit:num('transit'),L:num('L'),sL:num('sL'),caseSize:Math.max(1,num('caseSize')),moq:num('moq'),cost:num('cost'),season:Math.min(Math.max(num('season')||1,0.5),2.5),service:num('service')||0.95};
      var r=compute(x);
      var head=r.qty>0
        ?'<div>建议补货</div><div class="big">'+f(r.cases)+' 箱 <span style="font-size:18px;font-weight:400">（'+f(r.qty)+' 瓶）</span></div>'
        :'<div>暂不需要补货</div><div class="big">0 箱</div>';
      out.innerHTML=head
       +'<div>紧急程度 <span class="tag">'+r.sev+'</span>　现有加在途约可卖 '+f(r.days,0)+' 天</div>'
       +'<ol>'
       +'<li>近 28 天日均 <b>'+f(r.ma,2)+'</b> 瓶，乘季节系数 '+f(x.season,2)+'，预测日需求 <b>'+f(r.dhat,2)+'</b> 瓶</li>'
       +'<li>服务水平 '+f(x.service*100,1)+'%，安全库存 <b>'+f(r.ss,0)+'</b> 瓶</li>'
       +'<li>再订货点 = 日需求 × 交期 + 安全库存 = <b>'+f(r.rop,0)+'</b> 瓶</li>'
       +'<li>目标库存 = 日需求 × (交期 + '+r.R+' 天) + 安全库存 = <b>'+f(r.S,0)+'</b> 瓶</li>'
       +'<li>现有 '+f(x.onHand)+' + 在途 '+f(x.transit)+' = <b>'+f(r.pos)+'</b> 瓶'+(r.pos<r.S?'，低于目标库存，需要补货':'，不低于目标库存，不用补')+'</li>'
       +(r.pos<r.S?'<li>缺口 '+f(r.need,0)+' 瓶，经济批量 '+f(r.eoq,0)+' 瓶，取较大值；补货后不超过 '+r.cover+' 天需求，上限 '+f(r.cap,0)+' 瓶</li>'
       +'<li>按箱规 '+f(x.caseSize)+' 瓶/箱、起订量 '+f(x.moq)+' 瓶向上取整，得 <b>'+f(r.qty)+'</b> 瓶</li>':'')
       +'</ol>'
       +'<div class="note">算法与筹策系统一致。系统里还会在全部商品之间按采购预算和仓库容量排序分配，确认后生成采购单草稿，再提交审核。</div>';
    }
    form.addEventListener('input',run);run();
  }
  function init(){var el=document.getElementById('chouce-calc');if(el)mount(el);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
