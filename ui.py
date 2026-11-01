"""Shared look-and-feel (DeepMind-inspired) and small HTML helpers."""
import altair as alt
import streamlit as st

CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');
:root{--ink:#0b0b0f;--muted:#5f6368;--line:#e8eaed;--card:#f4f6f8;}
html{scroll-behavior:smooth}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:#fff!important;color:var(--ink)}
.stApp,.stApp p,.stApp label,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp h4,
[data-testid="stMarkdownContainer"] *{font-family:'Google Sans','DM Sans',Arial,sans-serif}
#MainMenu,header[data-testid="stHeader"],footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
.block-container,[data-testid="stMainBlockContainer"]{max-width:1240px!important;padding:84px 32px 0!important}
[data-testid="stMarkdownContainer"] a{text-decoration:none}
iframe{border-radius:24px;border:1px solid #e8eaed}

.dm-nav{position:fixed;top:0;left:0;right:0;z-index:1000;height:68px;display:flex;align-items:center;justify-content:space-between;
padding:0 clamp(16px,4vw,40px);background:rgba(255,255,255,.86);backdrop-filter:saturate(180%) blur(16px);border-bottom:1px solid var(--line)}
.dm-brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:18px;color:var(--ink)!important}
.dm-dot{width:22px;height:22px;border-radius:50%;background:conic-gradient(from 200deg,#4285f4,#9b72cb,#d96570,#f6b26b,#4285f4)}
.dm-links{display:flex;gap:26px;align-items:center}
.dm-links a.l{color:var(--ink)!important;font-size:15px;font-weight:500;opacity:.75}
.dm-links a.l:hover{opacity:1}
.btn{display:inline-flex;align-items:center;gap:8px;padding:15px 28px;border-radius:999px;font-weight:600;font-size:16px;transition:.2s}
.btn-dark{background:var(--ink);color:#fff!important}.btn-dark:hover{background:#34343c}
.btn-line{border:1.5px solid var(--ink);color:var(--ink)!important;background:transparent}
.btn-line:hover{background:var(--ink);color:#fff!important}
.btn-sm{padding:9px 18px;font-size:14px}
.row{display:flex;gap:12px;flex-wrap:wrap}

.hero{position:relative;padding:64px 0 8px;overflow:hidden}
.orb{position:absolute;right:-140px;top:-80px;width:560px;height:560px;border-radius:50%;filter:blur(72px);opacity:.5;z-index:0;
background:radial-gradient(circle at 30% 30%,#4285f4,transparent 60%),radial-gradient(circle at 72% 38%,#d96570,transparent 55%),radial-gradient(circle at 50% 82%,#9b72cb,transparent 60%)}
.hero>*:not(.orb){position:relative;z-index:1}
.eyebrow{font-size:14px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:18px}
.hero h1{font-size:clamp(44px,8vw,104px);line-height:.98;letter-spacing:-.04em;font-weight:500;margin:0 0 26px;max-width:960px;padding:0}
.grad{background:linear-gradient(90deg,#4285f4,#9b72cb 55%,#d96570);-webkit-background-clip:text;background-clip:text;color:transparent}
.lead{font-size:clamp(18px,2vw,23px);line-height:1.45;color:var(--muted);max-width:700px;margin:0 0 34px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-top:52px}
.stat{background:var(--card);border-radius:28px;padding:28px}
.stat b{display:block;font-size:clamp(30px,4vw,52px);letter-spacing:-.03em;font-weight:500}
.stat span{color:var(--muted);font-size:15px}

.sec{padding-top:104px;scroll-margin-top:72px}
.sec h2{font-size:clamp(32px,5vw,58px);letter-spacing:-.035em;line-height:1.05;font-weight:500;margin:0 0 16px;padding:0}
.sub{color:var(--muted);font-size:clamp(17px,1.8vw,20px);max-width:680px;line-height:1.5;margin:0 0 30px}
.secbar{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:8px}

.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.card{border-radius:28px;padding:30px;min-height:290px;display:flex;flex-direction:column;justify-content:space-between}
.card h3{font-size:26px;letter-spacing:-.02em;font-weight:500;margin:0 0 10px;padding:0}
.card p{margin:0;color:#3c4043;font-size:16px;line-height:1.5}
.tag{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.07em;color:#3c4043;opacity:.7}
.big{font-size:44px;letter-spacing:-.04em;font-weight:500}
.c1{background:#e8f0fe}.c2{background:#f3e8fd}.c3{background:#fce8e6}.c4{background:#e6f4ea}

.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--card);border-radius:28px;padding:32px}
.panel h3{font-size:24px;letter-spacing:-.02em;font-weight:500;margin:0 0 18px;padding:0}
.kv{display:flex;justify-content:space-between;gap:20px;padding:14px 0;border-bottom:1px solid #dadce0;font-size:16px}
.kv:last-child{border-bottom:none}.kv span:first-child{color:var(--muted)}.kv span:last-child{font-weight:500;text-align:right}
.flow{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:22px}
.chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:10px 16px;font-size:15px;font-weight:500}
.chip.hi{background:var(--ink);color:#fff;border-color:var(--ink)}
.arrow{color:var(--muted)}
.legend{display:flex;gap:18px;font-size:14px;color:var(--muted);margin:-6px 0 8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px}
.note{color:var(--muted);font-size:15px;line-height:1.5;margin-top:14px}

.st-key-demo_box,[data-testid="stVerticalBlockBorderWrapper"]{border-radius:32px!important;border:none!important;background:var(--card)!important;padding:20px!important}
[data-testid="stFileUploaderDropzone"]{background:#fff!important;border:1.5px dashed #c4c7c5!important;border-radius:20px!important}
[data-testid="stFileUploaderDropzone"] button{border-radius:999px!important;border:1.5px solid var(--ink)!important;background:#fff!important;color:var(--ink)!important}
[data-baseweb="select"]>div{border-radius:16px!important;background:#fff!important}
[data-testid="stImage"] img{border-radius:20px}
.res{background:#fff;border-radius:24px;padding:30px;min-height:250px}
.pill{display:inline-block;padding:8px 18px;border-radius:999px;font-weight:600;font-size:15px}
.pill.bad{background:#fce8e6;color:#c5221f}.pill.good{background:#e6f4ea;color:#137333}.pill.idle{background:#eef0f2;color:var(--muted)}
.res h3{font-size:clamp(34px,4vw,50px);letter-spacing:-.035em;font-weight:500;margin:18px 0 4px;padding:0}
.bar{height:10px;background:#e8eaed;border-radius:99px;overflow:hidden;margin:18px 0 10px}
.bar i{display:block;height:100%;border-radius:99px}

.vid{border-radius:24px;overflow:hidden}
.soon{background:var(--card);border-radius:28px;padding:48px;text-align:center;color:var(--muted);font-size:18px}

.foot{background:var(--ink);color:#fff;border-radius:36px;margin-top:120px;padding:60px clamp(24px,5vw,64px) 36px}
.foot-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:32px}
.foot h4{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#9aa0a6;margin:0 0 14px;font-weight:600;padding:0}
.foot a{display:block;color:#fff!important;opacity:.88;margin:10px 0;font-size:16px}
.foot a:hover{opacity:1}
.foot .brand{font-size:30px;letter-spacing:-.03em;font-weight:500;line-height:1.1;max-width:340px}
.foot small{display:block;margin-top:44px;color:#9aa0a6;font-size:14px;border-top:1px solid #3c4043;padding-top:22px;line-height:1.6}

@media(max-width:900px){
.cards{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}
.foot-grid{grid-template-columns:1fr 1fr}.dm-links a.l{display:none}.orb{opacity:.35}
}
@media(max-width:560px){.cards{grid-template-columns:1fr}.block-container,[data-testid="stMainBlockContainer"]{padding:84px 16px 0!important}}

.hero{overflow:visible!important}
[data-testid="stMain"]{overflow-x:hidden}
.page.c{text-align:center}.page.c .sub{margin-left:auto;margin-right:auto}
/* ---------- app shell: top bar, forms, metrics, tabs, tables ---------- */
.st-key-topbar{position:fixed;top:14px;right:clamp(12px,3vw,36px);width:470px;z-index:1002}
.st-key-topbar [data-testid="stHorizontalBlock"]{gap:8px;justify-content:flex-end;flex-wrap:nowrap}
.st-key-topbar [data-testid="stColumn"]{flex:0 0 auto!important;width:auto!important;min-width:0!important}
.st-key-topbar [data-testid="stColumn"]:empty,.st-key-topbar [data-testid="stColumn"]:not(:has(button)){display:none}
.st-key-topbar button{border-radius:999px;padding:0 8px;min-height:38px;font-weight:600;font-size:14px;width:auto;padding:0 16px;white-space:nowrap}
.st-key-topbar button p{overflow:visible!important;text-overflow:clip!important;white-space:nowrap}
.st-key-topbar [data-testid="stBaseButton-secondary"]{background:#fff;border:1.5px solid var(--ink);color:var(--ink)}
.st-key-topbar [data-testid="stBaseButton-secondary"]:hover{background:var(--ink);color:#fff}
.st-key-topbar [data-testid="stBaseButton-primary"]{background:var(--ink);border:1.5px solid var(--ink);color:#fff}
.st-key-topbar [data-testid="stBaseButton-primary"]:hover{background:#34343c}
.dm-links{margin-right:480px}
.banner{border-radius:20px;padding:14px 22px;margin:0 0 18px;font-size:16px;font-weight:500}
.banner.info{background:#e8f0fe;color:#174ea6}.banner.warn{background:#fef7e0;color:#8a5a00}.banner.bad{background:#fce8e6;color:#a50e0e}
.page{padding-top:28px}
.page h2{font-size:clamp(30px,4.4vw,48px);letter-spacing:-.035em;line-height:1.05;font-weight:500;margin:0 0 10px;padding:0}
.stButton button,[data-testid="stFormSubmitButton"] button,[data-testid="stDownloadButton"] button{border-radius:999px;font-weight:600;padding:8px 22px}
[data-testid="stFormSubmitButton"] button{width:100%}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primaryFormSubmit"]{background:var(--ink)!important;border-color:var(--ink)!important;color:#fff!important}
[data-testid="stForm"]{background:var(--card);border:none;border-radius:28px;padding:26px}
[data-testid="stTextInputRootElement"],[data-testid="stNumberInputContainer"],[data-baseweb="input"],[data-baseweb="base-input"],[data-baseweb="textarea"]{background:#fff!important;border-radius:14px!important}
[data-testid="stTextInputRootElement"],[data-testid="stNumberInputContainer"],[data-baseweb="textarea"]{border:1px solid #cfd3d8!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input{background:#fff!important;border-radius:14px}
[data-testid="stTextInputRootElement"]:focus-within{border-color:var(--ink)!important}
[data-testid="stMetric"]{background:var(--card);border-radius:22px;padding:18px 22px}
[data-testid="stMetricLabel"] p{color:var(--muted);font-size:14px}
[data-testid="stMetricValue"]{font-size:32px;letter-spacing:-.02em;font-weight:500}
[data-baseweb="tab-list"]{gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line)}
[data-baseweb="tab"]{border-radius:999px 999px 0 0;font-weight:600}
[data-testid="stDataFrame"]{border-radius:18px;overflow:hidden}
[data-testid="stExpander"]{border-radius:20px;border:1px solid var(--line)}
.who{display:inline-flex;gap:10px;align-items:center;background:var(--card);border-radius:999px;padding:8px 16px;font-size:15px;font-weight:500;margin-bottom:14px}
.ok{color:#137333;font-weight:600}.no{color:#c5221f;font-weight:600}
@media(max-width:1180px){.dm-links a.l{display:none}.dm-links{margin-right:0}}
@media(max-width:700px){
.st-key-topbar{top:74px;left:8px;right:8px;width:auto;background:#fff;padding:6px 0}
.block-container,[data-testid="stMainBlockContainer"]{padding-top:132px!important}
}
"""


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def html(s: str) -> str:
    """Markdown ko HTML block todne se bachane ke liye: blank lines aur indentation hata do."""
    return "\n".join(line.strip() for line in s.splitlines() if line.strip())


def render_nav(show_links: bool):
    links = ""
    if show_links:
        links = "".join(f'<a class="l" href="#{a}" target="_self">{t}</a>' for a, t in
                        [("demo", "Demo"), ("project", "Project"), ("results", "Results"),
                         ("slides", "Slides"), ("report", "Report"), ("video", "Video")])
    st.markdown(html(f"""
    <div class="dm-nav">
    <span class="dm-brand"><span class="dm-dot"></span>Malaria Cell Detection</span>
    <div class="dm-links">{links}</div>
    </div>
    """), unsafe_allow_html=True)


def banner(text: str, kind: str = "info"):
    st.markdown(f'<div class="banner {kind}">{text}</div>', unsafe_allow_html=True)


def page_head(eyebrow: str, title: str, sub: str = "", centered: bool = False):
    st.markdown(html(f"""
    <div class="page{' c' if centered else ''}"><div class="eyebrow">{eyebrow}</div><h2>{title}</h2>
    {f'<p class="sub">{sub}</p>' if sub else ''}</div>
    """), unsafe_allow_html=True)


def bar_chart(df, colors, height=260):
    """Bars in the exact row order of df (dates stay chronological, bins stay in order)."""
    d = df.copy()
    d.index = [x.strftime("%d %b") if hasattr(x, "strftime") else str(x) for x in d.index]
    d.index.name = "x"
    long = d.reset_index().melt("x", var_name="series", value_name="count")
    multi = len(d.columns) > 1
    chart = (
        alt.Chart(long)
        .mark_bar(size=18 if len(d) > 8 else 44, cornerRadiusTopLeft=0 if multi else 5, cornerRadiusTopRight=0 if multi else 5)
        .encode(
            x=alt.X("x:N", sort=list(d.index), title=None,
                    axis=alt.Axis(labelAngle=0, labelOverlap=True, ticks=False, domain=False, labelColor="#5f6368")),
            y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1, format="d", ticks=False, domain=False,
                                                       gridColor="#e3e5e8", labelColor="#5f6368")),
            color=alt.Color("series:N", scale=alt.Scale(domain=list(d.columns), range=colors),
                            legend=alt.Legend(orient="bottom", title=None, labelColor="#5f6368") if multi else None),
            tooltip=[alt.Tooltip("x:N", title="Day"), alt.Tooltip("series:N", title="Series"), alt.Tooltip("count:Q", title="Count")],
        )
        .properties(height=height)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart)
