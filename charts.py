"""Chart.js charts (shadcn-style cards) embedded in Streamlit.

Each chart is a small self-contained HTML card rendered in an iframe: title, legend, responsive canvas,
hover tooltips, click-on-legend to hide a series. Chart.js is loaded from the jsDelivr CDN.
"""
import json

import streamlit as st

CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js"

# Chart colours (validated palette). Orange/blue always mean Parasitized/Uninfected.
ORANGE, BLUE, VIOLET, AQUA, NAVY = "#eb6834", "#2a78d6", "#6250d6", "#1baf7a", "#14213d"

_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:transparent;font-family:'DM Sans','Google Sans',system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#0b0b0f}
.card{height:calc(100% - 2px);margin:1px;border:1px solid #e8eaed;border-radius:24px;background:#fff;padding:20px 22px 16px;display:flex;flex-direction:column}
h3{margin:0;font-size:17px;font-weight:600;letter-spacing:-.01em;display:flex;align-items:center;gap:9px}
.dot{width:10px;height:10px;border-radius:50%;flex:none}
.sub{margin:3px 0 0;font-size:13px;color:#6b7280}
.lg{display:flex;flex-wrap:wrap;gap:6px 14px;margin:12px 0 4px;min-height:20px}
.lg button{all:unset;cursor:pointer;display:inline-flex;align-items:center;gap:7px;font-size:13px;color:#3c4043;padding:2px 0}
.lg button.off{opacity:.38;text-decoration:line-through}
.lg i{width:10px;height:10px;border-radius:3px;display:inline-block}
.lg b{font-weight:600;color:#0b0b0f}
.wrap{position:relative;flex:1;min-height:0;margin-top:6px}
.empty{position:absolute;inset:0;display:none;align-items:center;justify-content:center;color:#9aa0a6;font-size:14px;pointer-events:none}
</style></head><body>
<div class="card"><h3 id="t"></h3><p class="sub" id="s"></p><div class="lg" id="lg"></div>
<div class="wrap"><canvas id="c"></canvas><div class="empty" id="e">No data yet</div></div></div>
<script src="__CDN__"></script>
<script>
const S = __SPEC__;
const INK="#0b0b0f", MUTED="#6b7280", GRID="#eceef1";
const hexA = (h,a) => { const n=parseInt(h.slice(1),16); return `rgba(${n>>16},${(n>>8)&255},${n&255},${a})`; };
const accent = S.accent || (S.datasets[0] && (S.datasets[0].color || (S.datasets[0].colors||[])[0])) || "#2a78d6";
document.getElementById("t").innerHTML = '<span class="dot" style="background:'+accent+'"></span><span></span>';
document.getElementById("t").lastChild.textContent = S.title;
document.querySelector(".card").style.background = "linear-gradient(180deg,"+hexA(accent,.10)+" 0%,#fff 120px)";
if (S.subtitle) document.getElementById("s").textContent = S.subtitle; else document.getElementById("s").remove();
const lg = document.getElementById("lg");
function showError(msg){ document.querySelector(".wrap").innerHTML = '<div style="color:#9aa0a6;font-size:14px;padding-top:30px">'+msg+'</div>'; lg.remove(); }
if (!window.Chart) { showError("Chart could not load. Please check your internet connection."); }
else {
Chart.defaults.font.family = "'DM Sans','Google Sans',system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = MUTED;
const isDonut = S.type === "doughnut";
const fmtTick = v => S.fmt==="pct" ? (v*100).toFixed(0)+"%" : S.fmt==="dec" ? (+v).toFixed(2) : String(v);
const fmtTip  = v => S.fmt==="pct" ? (v*100).toFixed(2)+"%" : S.fmt==="dec" ? (+v).toFixed(4) : Number(v).toLocaleString();
const all = S.datasets.flatMap(d => d.data);
if (!all.some(v => v > 0)) document.getElementById("e").style.display = "flex";

const tip = {backgroundColor:"#fff",titleColor:INK,bodyColor:"#3c4043",footerColor:INK,borderColor:"#e3e5e8",borderWidth:1,
  padding:12,cornerRadius:12,boxPadding:5,usePointStyle:true,titleFont:{weight:"600",size:13},bodyFont:{size:13},footerFont:{weight:"600",size:12},
  callbacks:{
    label: c => isDonut
      ? ` ${c.label}: ${fmtTip(c.parsed)} (${(c.parsed/c.dataset.data.reduce((a,b)=>a+b,0)*100||0).toFixed(1)}%)`
      : ` ${c.dataset.label}: ${fmtTip(S.horizontal ? c.parsed.x : c.parsed.y)}`,
    footer: items => (S.stacked && items.length > 1) ? "Total: " + fmtTip(items.reduce((a,c)=>a+c.parsed.y,0)) : ""
  }};

let cfg;
if (isDonut) {
  const d = S.datasets[0], total = d.data.reduce((a,b)=>a+b,0);
  S.labels.forEach((l,i) => {
    const b = document.createElement("button"); b.style.cursor="default";
    b.innerHTML = `<i style="background:${d.colors[i]}"></i>${l} <b>${Number(d.data[i]).toLocaleString()}</b> <span style="color:#9aa0a6">(${total?(d.data[i]/total*100).toFixed(0):0}%)</span>`;
    lg.appendChild(b);
  });
  cfg = {type:"doughnut",
    data:{labels:S.labels,datasets:[{data:d.data,backgroundColor:d.colors,borderColor:"#fff",borderWidth:3,hoverOffset:6}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:"70%",animation:{duration:700},plugins:{legend:{display:false},tooltip:tip}},
    plugins:[{id:"center",afterDraw(ch){
      if(!total) return; const a = ch.chartArea, cx=(a.left+a.right)/2, cy=(a.top+a.bottom)/2, x = ch.ctx;
      x.save(); x.textAlign="center"; x.textBaseline="middle";
      x.fillStyle=INK; x.font="600 28px 'DM Sans',system-ui,sans-serif"; x.fillText(total.toLocaleString(), cx, cy-8);
      x.fillStyle=MUTED; x.font="500 13px 'DM Sans',system-ui,sans-serif"; x.fillText(S.centerLabel||"total", cx, cy+16);
      x.restore(); }}]};
} else {
  const isLine = S.type === "line";
  const datasets = S.datasets.map(d => {
    const base = {label:d.label, data:d.data};
    if (isLine) return {...base, borderColor:d.color, borderWidth:2.5, tension:.35, fill:!!S.area, pointRadius:4, pointHoverRadius:6,
      pointBackgroundColor:d.color, pointBorderColor:"#fff", pointBorderWidth:2,
      backgroundColor: c => { const a=c.chart.chartArea; if(!a) return hexA(d.color,.15);
        const g=c.chart.ctx.createLinearGradient(0,a.top,0,a.bottom); g.addColorStop(0,hexA(d.color,.22)); g.addColorStop(1,hexA(d.color,0)); return g; }};
    return {...base, backgroundColor:d.color, hoverBackgroundColor:d.color, borderRadius:S.stacked?4:8, borderSkipped:false,
      borderColor:"#fff", borderWidth:S.stacked?2:0, maxBarThickness:S.horizontal?22:38};
  });
  if (!lg.children.length) lg.style.display = "none";
  const cat = {stacked:!!S.stacked, grid:{display:false}, border:{display:false}, ticks:{color:MUTED, maxRotation:0, autoSkip:true}};
  const val = {stacked:!!S.stacked, beginAtZero:S.yMin==null, min:S.yMin, max:S.yMax, grid:{color:GRID}, border:{display:false},
    ticks:{color:MUTED, precision:(S.fmt==="int"?0:undefined), maxTicksLimit:7, callback:fmtTick}};
  if (S.datasets.length > 1) {
    S.datasets.forEach((d,i) => {
      const b = document.createElement("button");
      b.innerHTML = `<i style="background:${d.color}"></i>${d.label}`;
      b.onclick = () => { const vis = chart.isDatasetVisible(i); chart.setDatasetVisibility(i, !vis); b.classList.toggle("off", vis); chart.update(); };
      lg.appendChild(b);
    });
  }
  cfg = {type:isLine?"line":"bar", data:{labels:S.labels, datasets},
    options:{responsive:true, maintainAspectRatio:false, indexAxis:S.horizontal?"y":"x", animation:{duration:700},
      interaction:{mode:"index", intersect:false}, plugins:{legend:{display:false}, tooltip:tip},
      scales: S.horizontal ? {x:val, y:cat} : {x:cat, y:val}}};
}
var chart = new Chart(document.getElementById("c"), cfg);
}
</script></body></html>"""


def _embed(html: str, height: int):
    if hasattr(st, "iframe"):
        st.iframe(html, height=height)
    else:  # purane Streamlit versions
        import streamlit.components.v1 as components
        components.html(html, height=height)


def chart(title, labels, datasets, kind="bar", subtitle="", stacked=False, horizontal=False, area=False,
          fmt="int", height=340, y_min=None, y_max=None, center_label="total", accent=None):
    """Draw one chart card.

    kind: "bar" | "line" | "doughnut".
    datasets: [{"label": str, "data": [numbers], "color": "#hex"}]  (doughnut: [{"data": [...], "colors": [...]}])
    fmt: "int" (counts) | "pct" (values are 0..1) | "dec" (decimals, e.g. loss)
    """
    spec = {"title": title, "subtitle": subtitle, "type": kind, "labels": [str(x) for x in labels],
            "datasets": [{**d, "data": [float(v) if v == v else 0.0 for v in d["data"]]} for d in datasets],
            "stacked": stacked, "horizontal": horizontal, "area": area, "fmt": fmt,
            "yMin": y_min, "yMax": y_max, "centerLabel": center_label, "accent": accent}
    payload = json.dumps(spec).replace("</", "<\\/")
    _embed(_TEMPLATE.replace("__CDN__", CHARTJS_CDN).replace("__SPEC__", payload), height)
