"""Building a Benchmarking Dashboard for SNN Methods — pure-Python
front end.

    streamlit run streamlit_app.py

or press Run on run_streamlit.py, which does the same without needing a
terminal command typed.

No hand-written JavaScript anywhere. Layout is Streamlit, charts are Plotly,
and every number comes from dashboard_data.py — the same module app.py reads,
so the Flask page and this page cannot report different figures for the same
condition.

The primary control is the SIMULATOR selector: a reader picks simulators, not
backends, because the simulator is the unit the research question is asked
about. Selecting one filters every chart, every table and every headline
figure. Backend detail is available behind a disclosure rather than occupying
the page.

Single hardware platform. This is a controlled comparison: the machine is
held fixed so that a difference in runtime can be attributed to a difference
in the simulator rather than to the hardware it happened to run on. That is
why there is no hardware selector — every row was measured under identical
conditions, which is the property that makes the comparison valid. Extending
the same harness to GPU hardware is set out as future work in the thesis.
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

try:
    import pandas as pd
    import plotly.graph_objects as go
    import streamlit as st
except ImportError:
    sys.exit(
        "\n  This dashboard needs streamlit, plotly and pandas.\n"
        "  Install them, then run this file again:\n\n"
        f"      {sys.executable} -m pip install -r requirements-streamlit.txt\n\n"
        "  (Prefer the Flask version instead? Run app.py — it needs only "
        "Flask.)\n")

import dashboard_config as config
import dashboard_data as data
import dashboard_theme as theme
import optimization
import robustness

st.set_page_config(page_title=config.TITLE, page_icon="⚡", layout="wide")


# --------------------------------------------------------------------- style
# Streamlit's default is a low-contrast light grey on white. These rules put
# the page on the tinted ground the palette was validated against, raise the
# body ink to near-black, and give every panel a coloured rail — the same
# three changes that stop the Flask page reading as washed out.
st.markdown(f"""
<style>
  .stApp {{ background: {theme.SURFACE}; color-scheme: dark; }}
  div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
      background: {theme.CARD}; border-radius: 10px;
  }}
  div[data-testid="stExpander"] details {{
      background: {theme.CARD}; border: 1px solid {theme.BORDER};
      border-radius: 10px;
  }}
  section[data-testid="stSidebar"] {{
      background: {theme.CARD}; border-right: 1px solid {theme.BORDER};
  }}
  h1, h2, h3, h4 {{ color: {theme.INK} !important; letter-spacing: -.015em; }}
  .stApp, .stMarkdown, p, li, label {{ color: {theme.INK_SOFT}; }}
  div[data-testid="stMetric"] {{
      background: {theme.CARD}; border: 1px solid {theme.BORDER};
      border-radius: 12px; padding: 15px 18px; position: relative;
      box-shadow: 0 1px 3px rgba(16,23,37,.07), 0 6px 18px rgba(16,23,37,.05);
      overflow: hidden;
  }}
  div[data-testid="stMetricValue"] {{
      color: {theme.INK} !important; font-size: 27px; font-weight: 750;
  }}
  div[data-testid="stMetricLabel"] {{
      color: {theme.INK_MUTED} !important; font-size: 10.5px !important;
      font-weight: 750; letter-spacing: .07em; text-transform: uppercase;
  }}
  .panel {{
      background: {theme.CARD}; border: 1px solid {theme.BORDER};
      border-radius: 12px; padding: 16px 19px; margin-bottom: 8px;
      box-shadow: 0 1px 3px rgba(16,23,37,.07);
  }}
  .panel h4 {{ margin: 0 0 4px 0; font-size: 14.5px; font-weight: 700; }}
  .panel .sub {{ color: {theme.INK_MUTED}; font-size: 12.5px; line-height: 1.58; }}
  .caveat {{
      border-left: 3px solid {theme.WARN}; background: #2a2214;
      padding: 12px 16px; border-radius: 0 9px 9px 0;
      font-size: 12.5px; color: {theme.INK_SOFT}; line-height: 1.62;
  }}
  .tau {{
      background: {theme.CARD}; border: 1px solid {theme.BORDER};
      border-top: 3px solid var(--tc); border-radius: 10px; padding: 13px 15px;
  }}
  .tau .k {{ font-size: 10.5px; font-weight: 750; letter-spacing: .06em;
             text-transform: uppercase; color: {theme.INK_MUTED}; }}
  .tau .v {{ font-size: 25px; font-weight: 750; margin-top: 5px; }}
  .tau .r {{ font-size: 11.5px; color: {theme.INK_MUTED}; margin-top: 5px; line-height: 1.45; }}
  .explain {{
      background: {theme.CARD}; border: 1px solid {theme.BORDER};
      border-top: 3px solid var(--c); border-radius: 10px; padding: 15px 17px;
      height: 100%;
  }}
  .explain h4 {{ font-size: 14.5px; font-weight: 700; color: var(--c); margin: 0 0 2px; }}
  .explain .kind {{ font-size: 10px; font-weight: 750; letter-spacing: .07em;
                    text-transform: uppercase; color: {theme.INK_MUTED}; margin-bottom: 8px; }}
  .explain .one {{ font-size: 12.5px; color: {theme.INK}; font-weight: 600; margin-bottom: 7px; }}
  .explain .detail {{ font-size: 12.5px; color: {theme.INK_MUTED}; line-height: 1.58; }}
  .explain .best {{ margin-top: 9px; padding-top: 8px; border-top: 1px solid {theme.GRID};
                    font-size: 12px; color: {theme.INK_SOFT}; }}
  .explain .src {{ margin-top: 7px; font-size: 11.5px; color: {theme.INK_MUTED};
                   font-style: italic; line-height: 1.5; }}
  /* Simulator buttons: Streamlit renders these as real buttons, so the
     selected state is carried by button type rather than a CSS class. */
  div[data-testid="stButton"] button {{ width: 100%; border-radius: 9px; font-weight: 650; }}
  hr {{ border-color: {theme.BORDER}; }}
</style>
""", unsafe_allow_html=True)


def plot_layout(fig, *, xtitle="", ytitle="", height=340, logx=False, logy=False):
    """House style for every chart. Applied through one function so a change
    lands everywhere at once."""
    fig.update_layout(
        height=height, paper_bgcolor=theme.CARD, plot_bgcolor=theme.CARD,
        font=dict(color=theme.INK_SOFT, size=12),
        margin=dict(l=8, r=8, t=8, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="left", x=0, font=dict(size=11)),
        hoverlabel=dict(bgcolor=theme.CARD, bordercolor=theme.BORDER,
                        font=dict(color=theme.INK, size=12)),
    )
    axis = dict(gridcolor=theme.GRID, zerolinecolor=theme.GRID,
                linecolor=theme.BORDER, tickfont=dict(size=11),
                title_font=dict(size=12))
    # An axis type is set only when a log scale is wanted. Forcing "linear"
    # otherwise breaks the categorical axis the horizontal bar charts need:
    # the axis renders with numeric ticks and no bars at all.
    fig.update_xaxes(title_text=xtitle, **({"type": "log"} if logx else {}), **axis)
    fig.update_yaxes(title_text=ytitle, **({"type": "log"} if logy else {}), **axis)
    return fig


def panel(title, sub=""):
    st.markdown(f'<div class="panel"><h4>{title}</h4>'
                f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def caveat(text):
    st.markdown(f'<div class="caveat">{text}</div>', unsafe_allow_html=True)


def csv_button(df, filename, key, label="Export CSV"):
    st.download_button(label, df.to_csv(index=False).encode("utf-8"),
                        file_name=filename, mime="text/csv", key=key)


def bar(rows, *, x, y, hover=None, xtitle="", height=340, logx=False):
    """Horizontal bars, one per backend, coloured by simulator."""
    fig = go.Figure()
    for r in rows:
        fig.add_trace(go.Bar(
            y=[r[y]], x=[r[x]], orientation="h", name=r[y],
            marker=dict(color=theme.color_for(r["framework"]), line=dict(width=0)),
            width=0.62, showlegend=False,
            hovertemplate=(hover(r) if hover else f"{r[y]}: {r[x]}") + "<extra></extra>",
        ))
    plot_layout(fig, xtitle=xtitle, height=height, logx=logx)
    fig.update_layout(bargap=0.34)
    fig.update_yaxes(autorange="reversed")
    return fig


def tau_tile(label, shown, reading, color):
    return (f'<div class="tau" style="--tc:{color}">'
            f'<div class="k">{label}</div>'
            f'<div class="v" style="color:{color}">{shown}</div>'
            f'<div class="r">{reading}</div></div>')


def tau_color(v):
    if v is None:
        return theme.INK_MUTED
    if v >= 0.8:
        return theme.GOOD
    if v >= 0.5:
        return theme.WARN
    return theme.BAD


# ------------------------------------------------------------------ load data
meta = data.get_meta()
if not meta.get("ok"):
    st.title(config.TITLE)
    st.error(meta.get("error", "No data."))
    st.stop()

FRAMEWORKS = [f for f in data.get_frameworks() if not f["is_control"]]
ALL_FW = [f["id"] for f in FRAMEWORKS]

if "active" not in st.session_state:
    st.session_state.active = set(ALL_FW)


# ------------------------------------------------------------------- header
head_l, head_r = st.columns([3, 1])
with head_l:
    st.markdown(
        f"<h2 style='margin-bottom:2px'>⚡ {config.TITLE}</h2>"
        f"<div style='color:{theme.INK_MUTED};font-size:12.5px'>"
        f"{getattr(config, 'AUTHOR', '')} · {getattr(config, 'INSTITUTION', '')}</div>"
        f"<div style='color:{theme.INK_MUTED};font-size:13px;margin-top:5px'>"
        f"{config.SUBTITLE}</div>", unsafe_allow_html=True)
with head_r:
    st.markdown(
        f"<div style='text-align:right;margin-top:6px'>"
        f"<span style='background:#16233a;border:1px solid #2c4a75;color:#8fbcf5;"
        f"border-radius:999px;padding:4px 12px;font-size:11.5px;font-weight:650'>"
        f"Single hardware platform</span> "
        f"<span style='background:{theme.CARD_ALT};border:1px solid {theme.BORDER};"
        f"border-radius:999px;padding:4px 12px;font-size:11.5px;font-weight:650'>"
        f"{meta['counts']['runs']} measured runs</span></div>",
        unsafe_allow_html=True)

    # Export everything, and start the harness — the two actions the Flask
    # page carries top-right.
    all_rows = []
    for kind in ("inference", "scalability", "memory", "training", "validation"):
        try:
            for r in data.export_rows(kind):
                all_rows.append(dict(dataset=kind, **r))
        except ValueError:
            pass
    if all_rows:
        st.download_button(
            "⬇  Export all results (CSV)",
            pd.DataFrame(all_rows).to_csv(index=False).encode("utf-8"),
            file_name="benchmark-all.csv", mime="text/csv", key="csv_all")

    if st.button("▶  Run benchmark (quick sweep)", key="runbench"):
        root = Path(__file__).resolve().parent.parent
        try:
            subprocess.Popen([sys.executable, "run.py", "bench", "--quick"],
                              cwd=str(root))
            st.success(
                "Benchmark started in a separate process. It appends to the "
                "results database — nothing existing is cleared. Reload this "
                "page when it finishes to read the new rows.")
        except FileNotFoundError:
            st.error(f"Could not find run.py in {root}. The dashboard folder "
                      f"must sit inside the benchmark project for this to work.")

st.divider()


active = st.session_state.active


def keep(r):
    return r["framework"] in active


def eligible(rows):
    """Controls and compile-dominated backends stay visible everywhere but
    never win a headline figure — the same rule the Flask page applies."""
    return [r for r in rows
            if keep(r) and r["framework"] not in theme.CONTROL_FRAMEWORKS
            and not r.get("compile_dominated")]



# ─────────────────────────────────────────────────────────────── KPIs
inf_all = data.get_inference()
mem_all = data.get_memory()
scale_all = data.get_scalability_series()
train_all = data.get_training()

k1, k2, k3, k4 = st.columns(4)
inf_e, mem_e = eligible(inf_all), eligible(mem_all)
scale_e = [s for s in eligible(scale_all) if s["fit"] and s["fit"]["r2"] >= 0.25]
train_e = [r for r in train_all
           if keep(r) and r["framework"] not in theme.CONTROL_FRAMEWORKS
           and r["accuracy_pct"] is not None]

with k1:
    if inf_e:
        b = min(inf_e, key=lambda r: r["runtime_median_s"])
        st.metric("Fastest inference", f"{b['runtime_median_s'] * 1000:.2f} ms",
                   f"{theme.label_for(b['framework'])} / {b['backend']}")
    else:
        st.metric("Fastest inference", "—", "no eligible simulator selected")
with k2:
    if mem_e:
        b = min(mem_e, key=lambda r: r["peak_mb"])
        st.metric("Lowest peak memory", f"{b['peak_mb']:.0f} MB",
                   f"{theme.label_for(b['framework'])} / {b['backend']}")
    else:
        st.metric("Lowest peak memory", "—", "no eligible simulator selected")
with k3:
    if scale_e:
        b = min(scale_e, key=lambda s: s["fit"]["k"])
        st.metric("Flattest scaling", f"k = {b['fit']['k']:.3f}",
                   f"{theme.label_for(b['framework'])} / {b['backend']}")
    else:
        st.metric("Flattest scaling", "—", "no eligible simulator selected")
with k4:
    if train_e:
        b = max(train_e, key=lambda r: r["accuracy_pct"])
        st.metric("Best MNIST accuracy", f"{b['accuracy_pct']:.2f}%",
                   f"{theme.label_for(b['framework'])} / {b['backend']}")
    else:
        st.metric("Best MNIST accuracy", "—", "no training rows for this selection")

shown = [theme.label_for(f) for f in ALL_FW if f in active]
hidden = [theme.label_for(f) for f in ALL_FW if f not in active]
st.caption(
    (f"**Showing:** {', '.join(shown)}" if shown else "**Nothing selected.**")
    + (f" · **hidden:** {', '.join(hidden)}" if hidden else "")
    + ". Headline figures exclude the two NumPy validation controls and any compile-dominated "
      "backend — both stay visible in the charts and tables below, but neither "
      "is comparable on these axes.")

# ────────────────────────────────────────────────── simulator selector
st.markdown(
    f"<div style='font-size:11px;font-weight:750;letter-spacing:.07em;"
    f"text-transform:uppercase;color:{theme.INK_MUTED};margin-bottom:6px'>"
    f"Simulators &nbsp;<span style='text-transform:none;letter-spacing:0;"
    f"font-weight:400;font-size:12px'>— click to select or de-select. Every "
    f"chart, table and headline figure responds immediately.</span></div>",
    unsafe_allow_html=True)

cols = st.columns(len(FRAMEWORKS) + 3)
for col, fw in zip(cols, FRAMEWORKS):
    with col:
        on = fw["id"] in st.session_state.active
        tag = "control · " if fw["is_control"] else ""
        if st.button(
                f"{'●' if on else '○'}  {fw['label']}",
                key=f"fw_{fw['id']}",
                type="primary" if on else "secondary",
                help=f"{tag}{fw['n_backends']} backend"
                      f"{'' if fw['n_backends'] == 1 else 's'} — {fw['one_line']}",
                use_container_width=True):
            if on:
                st.session_state.active.discard(fw["id"])
            else:
                st.session_state.active.add(fw["id"])
            st.rerun()
with cols[-3]:
    if st.button("Select all", key="all", use_container_width=True):
        st.session_state.active = set(ALL_FW)
        st.rerun()
with cols[-2]:
    if st.button("Clear", key="none", use_container_width=True):
        st.session_state.active = set()
        st.rerun()

with cols[-1]:
    st.caption("All Simulators and Optimisation are the first two tabs below.")

# Backend detail, hidden until asked for.
with st.expander("Show backend detail"):
    st.caption(
        "A **backend** is one execution path within a simulator — a "
        "code-generation target, a thread count, or an implementation "
        "variant. Backends are filtered by their simulator above; this panel "
        "explains what each one is. Every backend listed produced measured "
        "rows.")
    bcols = st.columns(2)
    for i, b in enumerate(b for b in data.get_backends() if b["framework"] != "reference"):
        with bcols[i % 2]:
            c = theme.color_for(b["framework"])
            st.markdown(
                f"<div style='border-left:3px solid {c};background:{theme.CARD};"
                f"border:1px solid {theme.BORDER};border-left:3px solid {c};"
                f"border-radius:8px;padding:9px 12px;margin-bottom:8px'>"
                f"<div style='font-size:12.5px;font-weight:650;color:{theme.INK}'>"
                f"{theme.label_for(b['framework'])} / {b['backend']}</div>"
                f"<div style='font-size:11.5px;color:{theme.INK_MUTED};"
                f"line-height:1.5'>{b['note']}</div></div>",
                unsafe_allow_html=True)



# ────────────────────────────────────────────────────────── overview charts
# A line chart and a bar chart directly beneath the selector, so the shape of
# the result is visible before the reader opens a tab. Both respond to the
# simulator selection above.
ov1, ov2 = st.columns(2)
with ov1:
    panel("How runtime grows with network size",
          "Every selected simulator across the full sweep, both axes "
          "logarithmic. A straight line is power-law scaling; a flat line "
          "means a fixed cost is dominating rather than the network.")
    ov_series = [x for x in scale_all if keep(x)]
    if ov_series:
        fig = go.Figure()
        for x in ov_series:
            fig.add_trace(go.Scatter(
                x=[q["n"] for q in x["points"]], y=[q["t"] for q in x["points"]],
                mode="lines+markers", name=x["id"],
                line=dict(color=theme.color_for(x["framework"]), width=2.2,
                          dash=theme.dash_for(x["framework"], x["backend"])),
                marker=dict(size=7, line=dict(width=1.5, color=theme.CARD)),
                hovertemplate=(f"<b>{x['id']}</b><br>N=%{{x:,}}<br>"
                               "%{y:.4f} s median<extra></extra>"),
            ))
        plot_layout(fig, xtitle="neurons (N)", ytitle="seconds",
                    logx=True, logy=True, height=330)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("No simulators selected.")
with ov2:
    panel("Inference cost at the reference size",
          "Median wall-clock time for one run, warmup excluded. Log scale — "
          "the spread across these backends is four orders of magnitude.")
    ov_inf = [x for x in inf_all if keep(x)]
    if ov_inf:
        st.plotly_chart(bar(
            ov_inf, x="runtime_median_s", y="id",
            hover=lambda r: (f"<b>{r['id']}</b><br>"
                             f"{r['runtime_median_s'] * 1000:.3f} ms median<br>"
                             f"CV {r['cv_pct']:.1f}% over {r['n_runs']} runs"),
            xtitle="seconds per run (log)", logx=True, height=330),
            width="stretch")
    else:
        st.info("No simulators selected.")


with st.expander("Start here: a four-step reading path", expanded=False):
    for _num, _verb, _q, _href, _label, _text in robustness.READING_PATH:
        st.markdown(f"**{_num}. {_verb}: {_q}** - open the *{_label}* tab. {_text}")
    st.markdown("**Three things to take away**")
    for _t in robustness.takeaways():
        st.markdown(f"- **{_t['title']}.** {_t['text']}")
    st.caption("Recomputed from the stored measurements on every load; they describe one machine and one workload.")

tabs = st.tabs(["All Simulators", "Optimisation", "Inference",
                "Scalability", "Memory", "Training", "Sensitivity",
                "Equivalence & provenance", "What the baselines are",
                "Robustness"])


# ══════════════════════════════════════════════════════ 1 — INFERENCE
with tabs[2]:
    inf = [r for r in inf_all if keep(r)]
    if not inf:
        st.info("No simulators selected.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            panel(f"Inference runtime — {inf[0]['network_size']}-neuron network",
                  "Median wall-clock seconds over the measured runs, warmup "
                  "excluded. Log scale — the spread is four orders of magnitude.")
            st.plotly_chart(bar(
                inf, x="runtime_median_s", y="id",
                hover=lambda r: (f"<b>{r['id']}</b><br>"
                                 f"{r['runtime_median_s'] * 1000:.3f} ms median<br>"
                                 f"CV {r['cv_pct']:.1f}% over {r['n_runs']} runs"),
                xtitle="seconds (log)", logx=True, height=330), width="stretch")
        with c2:
            panel("Peak memory",
                  "Peak resident set size of the whole Python process — "
                  "interpreter and imports included, which at this network "
                  "size is most of it.")
            st.plotly_chart(bar(
                inf, x="peak_rss_mb", y="id",
                hover=lambda r: f"<b>{r['id']}</b><br>{r['peak_rss_mb']:.0f} MB peak RSS",
                xtitle="MB", height=330), width="stretch")

        c3, c4 = st.columns(2)
        with c3:
            panel("Energy proxy index",
                  "runtime × CPU utilisation × configured TDP, rescaled so the "
                  "costliest reads 100.")
            st.plotly_chart(bar(
                [r for r in inf if r["energy_index"] is not None],
                x="energy_index", y="id",
                hover=lambda r: (f"<b>{r['id']}</b><br>index {r['energy_index']:.1f}"
                                 f"<br>{r['energy_median_j']:.3f} J estimated"),
                xtitle="index (worst = 100)", height=300), width="stretch")
        with c4:
            panel("Processor utilisation",
                  "Mean process CPU% during the measured window. Above 100% "
                  "means more than one core was busy.")
            st.plotly_chart(bar(
                inf, x="cpu_pct", y="id",
                hover=lambda r: f"<b>{r['id']}</b><br>{r['cpu_pct']:.0f}% mean CPU",
                xtitle="% of one core", height=300), width="stretch")

        st.markdown("#### Detailed results")
        st.dataframe(pd.DataFrame([{
            "Backend": r["id"],
            "Runtime (s)": round(r["runtime_median_s"], 6),
            "CV %": round(r["cv_pct"] or 0, 2),
            "Setup (s)": round(r["setup_s"], 4) if r["setup_s"] else None,
            "Peak MB": round(r["peak_rss_mb"], 1),
            "CPU %": round(r["cpu_pct"] or 0, 1),
            "Spikes": r["spikes"],
            "Energy (J)": round(r["energy_median_j"] or 0, 4),
            "Runs": r["n_runs"],
            "Note": ("compile-dominated" if r["compile_dominated"]
                     else ("baseline" if r["framework"] in theme.CONTROL_FRAMEWORKS else "")),
        } for r in inf]), width="stretch", hide_index=True)
        csv_button(pd.DataFrame(data.export_rows("inference")),
                    "inference.csv", "csv_inf")
        caveat(
            "<b>Setup and simulation are timed separately</b> so a backend "
            "that is slow to build is distinguishable from one that is slow "
            "to run. Brian2's <code>cpp_standalone</code> target reports a "
            "runtime dominated by C++ compilation rather than by simulation; "
            "it is marked and excluded from the headline figures, but not "
            "hidden, because that behaviour is a finding a simulator chooser "
            "needs.")


# ═══════════════════════════════════════════════════ 2 — SCALABILITY
with tabs[3]:
    series = [s for s in scale_all if keep(s)]
    if not series:
        st.info("No simulators selected.")
    else:
        c1, c2 = st.columns([1.15, 1])
        with c1:
            panel("Runtime against network size",
                  "Both axes logarithmic, so a straight line is power-law "
                  "scaling and its slope is the exponent k.")
            fig = go.Figure()
            for s in series:
                fig.add_trace(go.Scatter(
                    x=[p["n"] for p in s["points"]], y=[p["t"] for p in s["points"]],
                    mode="lines+markers", name=s["id"],
                    line=dict(color=theme.color_for(s["framework"]), width=2.2,
                              dash=theme.dash_for(s["framework"], s["backend"])),
                    marker=dict(size=8, line=dict(width=1.6, color=theme.CARD)),
                    customdata=[[p["cv"], p["spikes"], p["runs"]] for p in s["points"]],
                    hovertemplate=(f"<b>{s['id']}</b><br>N=%{{x:,}}<br>"
                                   "%{y:.4f} s median<br>"
                                   "CV %{customdata[0]:.1f}% over %{customdata[2]} runs<br>"
                                   "%{customdata[1]:,} spikes<extra></extra>"),
                ))
            plot_layout(fig, xtitle="neurons (N)", ytitle="seconds",
                        logx=True, logy=True, height=400)
            st.plotly_chart(fig, width="stretch")
        with c2:
            panel("Throughput at the largest size",
                  "Neurons simulated per second of wall clock at the top of "
                  "the sweep. Higher is better.")
            thr = sorted([s for s in series if s["throughput"]],
                          key=lambda s: -s["throughput"])
            st.plotly_chart(bar(
                thr, x="throughput", y="id",
                hover=lambda s: (f"<b>{s['id']}</b><br>{s['throughput']:,.0f} neurons/s"
                                 f"<br>at N={s['largest_n']:,}"),
                xtitle="neurons per second (log)", logx=True, height=400),
                width="stretch")

        st.markdown("#### Fitted scaling exponent")
        st.caption(
            "Least-squares fit of log(runtime) on log(N). r² says whether the "
            "straight line describes the data at all — where it is low the "
            "exponent is not worth quoting, and the interpretation column says "
            "so instead.")
        st.dataframe(pd.DataFrame([{
            "Backend": s["id"],
            "k": round(s["fit"]["k"], 3) if s["fit"] else None,
            "95% CI": (f"{s['fit']['ci'][0]:+.3f} … {s['fit']['ci'][1]:+.3f}"
                        if s["fit"] else "—"),
            "r²": round(s["fit"]["r2"], 3) if s["fit"] else None,
            "Sizes": len(s["points"]),
            "Runtime at largest N": (f"{s['largest_t']:.4f} s"
                                      if s["largest_t"] else "—"),
            "Interpretation": s["interpretation"],
        } for s in series]), width="stretch", hide_index=True)
        csv_button(pd.DataFrame(data.export_rows("scalability")),
                    "scalability.csv", "csv_scale")
        caveat(
            "<b>A near-zero exponent is not a fast simulator.</b> Brian2's "
            "backends post k close to zero because a fixed per-run cost "
            "dominates the integration at every size measured here. Read k "
            "together with the absolute runtime column beside it.")


# ═══════════════════════════════════════════════════════ 3 — MEMORY
with tabs[4]:
    mem = [s for s in mem_all if keep(s)]
    if not mem:
        st.info("No simulators selected.")
    else:
        c1, c2 = st.columns([1.15, 1])
        with c1:
            panel("Peak memory against network size",
                  "Where a line is flat, the footprint is interpreter and "
                  "imports rather than the network. Where it climbs, the "
                  "simulator is genuinely allocating per neuron.")
            fig = go.Figure()
            for s in mem:
                fig.add_trace(go.Scatter(
                    x=[p["n"] for p in s["points"]], y=[p["mem"] for p in s["points"]],
                    mode="lines+markers", name=s["id"],
                    line=dict(color=theme.color_for(s["framework"]), width=2.2,
                              dash=theme.dash_for(s["framework"], s["backend"])),
                    marker=dict(size=8, line=dict(width=1.6, color=theme.CARD)),
                    hovertemplate=(f"<b>{s['id']}</b><br>N=%{{x:,}}<br>"
                                   "%{y:.0f} MB peak RSS<extra></extra>"),
                ))
            plot_layout(fig, xtitle="neurons (N)", ytitle="peak RSS (MB)",
                        logx=True, height=380)
            st.plotly_chart(fig, width="stretch")
        with c2:
            panel("Memory attributable to the network",
                  "Growth from the smallest to the largest size divided by "
                  "neuron count — computed from the growth rather than the "
                  "peak, because the fixed interpreter cost is not a "
                  "per-neuron cost.")
            kb = sorted([s for s in mem if s["kb_per_neuron"] is not None],
                         key=lambda s: -s["kb_per_neuron"])
            st.plotly_chart(bar(
                kb, x="kb_per_neuron", y="id",
                hover=lambda s: (f"<b>{s['id']}</b><br>{s['kb_per_neuron']:.2f} KB/neuron"
                                 f"<br>{s['growth_mb']:+.1f} MB growth to N={s['largest_n']:,}"),
                xtitle="KB per neuron", height=380), width="stretch")

        st.dataframe(pd.DataFrame([{
            "Backend": s["id"],
            "Smallest N (MB)": round(s["baseline_mb"], 1),
            "Largest N (MB)": round(s["peak_mb"], 1),
            "Growth (MB)": round(s["growth_mb"], 1),
            "KB / neuron": (round(s["kb_per_neuron"], 3)
                            if s["kb_per_neuron"] is not None else None),
        } for s in mem]), width="stretch", hide_index=True)
        csv_button(pd.DataFrame(data.export_rows("memory")), "memory.csv", "csv_mem")

        st.markdown("#### Repeatability of the quoted medians")
        st.caption(
            "Every individual measured run behind the inference figure. A "
            "median with five tight runs behind it and one with five scattered "
            "runs are not the same claim.")
        spread = [s for s in data.get_run_spread("inference") if keep(s)]
        if spread:
            fig = go.Figure()
            for s in spread:
                fig.add_trace(go.Box(
                    x=s["values"], name=s["id"], orientation="h",
                    marker=dict(color=theme.color_for(s["framework"])),
                    line=dict(width=1.5), boxpoints="all", jitter=0.4,
                    pointpos=0, showlegend=False,
                    hovertemplate=f"<b>{s['id']}</b><br>%{{x:.5f}} s<extra></extra>",
                ))
            plot_layout(fig, xtitle="seconds per run (log)", logx=True, height=340)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, width="stretch")


# ═════════════════════════════════════════════════════ 4 — TRAINING
with tabs[5]:
    train = [r for r in train_all if keep(r)]
    if not train:
        st.info("No training rows for the selected simulators.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            panel("Test accuracy — MNIST classification",
                  "Held-out accuracy after training with each simulator's own "
                  "native learning rule. The dashed line is chance on ten classes.")
            fig = go.Figure()
            for r in train:
                fig.add_trace(go.Bar(
                    y=[r["id"]], x=[r["accuracy_pct"]], orientation="h",
                    marker=dict(color=theme.color_for(r["framework"])),
                    width=0.62, showlegend=False,
                    hovertemplate=(f"<b>{r['id']}</b><br>%{{x:.2f}}% test accuracy"
                                   "<extra></extra>"),
                ))
            fig.add_vline(x=10, line=dict(color=theme.BAD, width=1.5, dash="dash"))
            fig.add_annotation(x=10, y=1.06, yref="paper", text="chance (10%)",
                                showarrow=False, font=dict(size=11, color=theme.BAD))
            plot_layout(fig, xtitle="test accuracy (%)", height=330)
            fig.update_layout(bargap=0.34)
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, width="stretch")
        with c2:
            panel("Cost per epoch",
                  "Seconds per training epoch — or, for Nengo, the cost of the "
                  "single closed-form decoder solve, which has no epoch to "
                  "divide by.")
            st.plotly_chart(bar(
                sorted(train, key=lambda r: r["seconds_per_epoch"]),
                x="seconds_per_epoch", y="id",
                hover=lambda r: (f"<b>{r['id']}</b><br>{r['seconds_per_epoch']:,.1f} s/epoch"
                                 f"<br>{r['runtime_median_s']:,.0f} s total"),
                xtitle="seconds per epoch (log)", logx=True, height=330),
                width="stretch")

        st.markdown("#### What each simulator actually did")
        st.caption(
            "These rows are deliberately not running the same algorithm. Each "
            "uses the learning mechanism it was built for, which is the fair "
            "comparison; forcing one shared algorithm onto all of them would "
            "measure how well each imitates the others.")
        st.dataframe(pd.DataFrame([{
            "Backend": r["id"],
            "Accuracy %": round(r["accuracy_pct"], 2) if r["accuracy_pct"] is not None else None,
            "Did it learn?": ("no — no better than guessing"
                              if r["at_chance"] else "yes"),
            "Hidden": r["hidden"], "Train": r["train_n"], "Test": r["test_n"],
            "Epochs": r["epochs"],
            "s / epoch": round(r["seconds_per_epoch"], 2),
            "Mechanism": r["mechanism"],
        } for r in train]), width="stretch", hide_index=True)
        csv_button(pd.DataFrame(data.export_rows("training")), "training.csv", "csv_train")
        st.caption(
            "**How to read \"no — no better than guessing\".** MNIST has ten "
            "digit classes, so a model that has learned nothing and answers at "
            "random is right about 10% of the time. Any row sitting at roughly "
            "10% has not separated the classes at all — its accuracy is what "
            "guessing would have produced, so the number is reported as a "
            "failure to learn rather than as a low score. Rows marked *yes* "
            "are far enough above 10% that the learning rule demonstrably "
            "worked.")

        chance = [r for r in train if r["at_chance"]]
        if chance:
            names = ", ".join(dict.fromkeys(r["id"] for r in chance))
            plural = len(chance) > 1
            caveat(
                f"<b>{names} {'score' if plural else 'scores'} no better "
                f"than guessing, and the "
                f"{'rows say' if plural else 'row says'} so rather than burying "
                "it.</b> These use unsupervised spike-timing-dependent "
                "plasticity with a neuron-labelling readout. Without lateral "
                "inhibition and an adaptive threshold, every hidden neuron "
                "converges on the same filter, the labelling pass assigns most "
                "of them to one class, and that class then wins every test "
                "image — and the full budget, with ten times the images and "
                "more than three times the epochs, still leaves every such row "
                "at or below chance. What is "
                "measured is that limitation, not a property of the simulator.")
        caveat(
            "<b>Accuracy is not comparable across learning rules; cost per "
            "epoch is.</b> A surrogate-gradient result at three epochs and a "
            "plasticity result at three epochs are snapshots of two different "
            "convergence curves.")


# ══════════════════════════════════════ 5 — SENSITIVITY (Experiment 4)
with tabs[6]:
    s = data.get_sensitivity()
    panel("Experiment 4 — how much does the answer depend on how we asked?",
          "The other three experiments ask how fast, how large and how "
          "accurate each simulator is. This one asks whether those answers "
          "survive a change in the question. A benchmark whose ranking flips "
          "when the network size or the metric changes has not produced a "
          "recommendation — it has produced an artefact of its own "
          "configuration.")
    st.caption(
        "The statistic is **Kendall's τ**, the rank correlation between two "
        "orderings of the same backends. τ = 1 means they agree exactly, 0 "
        "means unrelated, −1 means reversed. Rank correlation is used rather "
        "than a comparison of the values because the claim under test is about "
        "the *order a reader would act on*, not the magnitudes.")

    if not s.get("ok"):
        st.warning(s.get("error", "No sensitivity data."))
    else:
        st.markdown("#### Does the ordering depend on the network size measured?")
        st.caption("Each tile compares the runtime ordering at that size "
                    "against the ordering at the largest size measured.")
        scols = st.columns(len(s["size_stability"]) or 1)
        for col, r in zip(scols, s["size_stability"]):
            with col:
                st.markdown(tau_tile(
                    f"N = {r['n']:,}", f"τ = {r['tau']:.3f}",
                    "reference ordering" if r["is_reference"]
                    else r["reading"].split(": ")[-1],
                    tau_color(r["tau"])), unsafe_allow_html=True)
        worst = min((r for r in s["size_stability"] if not r["is_reference"]),
                     key=lambda r: r["tau"], default=None)
        if worst:
            caveat(
                "<b>The ordering measured at one size does not carry to "
                f"another.</b> The weakest agreement is at N = {worst['n']:,}, "
                f"where τ = {worst['tau']:.3f} "
                f"({worst['reading'].split(': ')[-1]}). A benchmark reporting a single small network would "
                "recommend a different simulator from one reporting a large "
                "network, using the same measurements. This is the strongest "
                "argument in this study against single-point benchmarking.")

        st.markdown("#### Does the ordering depend on the metric chosen?")
        st.caption("Each tile compares the ordering under that metric against "
                    "the ordering by runtime, both at the largest size.")
        mcols = st.columns(len(s["metric_stability"]) or 1)
        for col, r in zip(mcols, s["metric_stability"]):
            with col:
                st.markdown(tau_tile(
                    r["metric"], f"τ = {r['tau']:.3f}",
                    "reference ordering" if r["is_reference"]
                    else r["reading"].split(": ")[-1],
                    tau_color(r["tau"])), unsafe_allow_html=True)
        memr = next((r for r in s["metric_stability"] if "memory" in r["metric"].lower()), None)
        scalr = next((r for r in s["metric_stability"] if "scaling" in r["metric"].lower()), None)
        caveat(
            "<b>Which metric you choose changes which simulator wins.</b>"
            + (f" Ranking by peak memory gives τ = {memr['tau']:.3f} against "
               f"ranking by runtime ({memr['reading'].split(': ')[-1]}): the "
               "fastest simulator here is not necessarily the most "
               "memory-efficient one."
               if memr else "")
            + (f" Ranking by scaling exponent gives τ = {scalr['tau']:.3f}, so "
               "how fast a simulator is at one size tells a reader almost "
               "nothing about how its cost grows." if scalr else "")
            + " A single-metric recommendation is therefore not a "
              "recommendation about the simulator; it is a recommendation "
              "about the metric.")

        st.markdown("#### Objective O2 — the energy proxy against the EFLOP metric")
        ev = s.get("energy_validation")
        if ev:
            o1, o2 = st.columns(2)
            with o1:
                st.markdown(tau_tile(
                    "Spearman rank correlation", f"ρ = {ev['rho']:.3f}",
                    f"energy proxy against EFLOP, {ev['n_pairs']} paired "
                    f"observations across network sizes",
                    tau_color(ev["rho"])), unsafe_allow_html=True)
            with o2:
                st.markdown(tau_tile(
                    "Distinct EFLOP values at the largest N",
                    f"{ev['eflop_distinct_at_ref']}",
                    "EFLOP separates the simulators" if ev["discriminates"]
                    else "one identical value for every simulator — EFLOP "
                          "cannot rank them against each other",
                    tau_color(1.0 if ev["discriminates"] else 0.0)),
                    unsafe_allow_html=True)
            caveat(ev["reading"])
        else:
            st.info("Not enough paired energy and EFLOP observations to "
                     "compute the correlation.")


# ═══════════════════════════════════ 6 — EQUIVALENCE & PROVENANCE
with tabs[7]:
    v = data.get_validation()
    panel("Do the simulators agree on the answer?",
          "Before any timing comparison means anything, the implementations "
          "have to be simulating the same network. Each backend's output "
          "firing rate is compared against the plain-NumPy validation control "
          "implementation of the identical model.")
    if not v.get("ok"):
        st.warning(v.get("error"))
    else:
        rows = [r for r in v["rows"] if str(r["id"]).split("/")[0] in active]
        vdf = pd.DataFrame([{
            "Backend": r["id"], "Status": r["status"],
            "Rate (Hz)": r["rate_hz"], "Reference (Hz)": r["ref_hz"],
            "Relative deviation": r["rel"], "Note": r["message"] or "",
        } for r in rows])
        st.dataframe(vdf, width="stretch", hide_index=True)
        csv_button(vdf, "equivalence.csv", "csv_valid")

    st.markdown("#### Provenance")
    st.caption("Recorded programmatically at run time, not transcribed.")
    p1, p2 = st.columns(2)
    with p1:
        mdf = pd.DataFrame(list(meta["machine"].items()), columns=["Property", "Value"])
        # Arrow needs one dtype per column, and this one holds both numbers
        # and strings.
        mdf["Value"] = mdf["Value"].astype(str)
        st.dataframe(mdf, width="stretch", hide_index=True)
    with p2:
        pdf = pd.DataFrame(list(meta["packages"].items()), columns=["Package", "Version"])
        pdf["Version"] = pdf["Version"].astype(str)
        st.dataframe(pdf, width="stretch", hide_index=True)
    cdf = pd.DataFrame(list(meta["config"].items()), columns=["Parameter", "Value"])
    cdf["Value"] = cdf["Value"].astype(str)   # same mixed column as above
    st.dataframe(cdf, width="stretch", hide_index=True)
    st.caption(f"Database: `{meta['db']}`")
    if meta.get("excluded"):
        others = ", ".join(f"`{m}`" for m in meta.get("other_machines", []))
        parts = [
            f"<b>{meta['excluded']} condition record"
            f"{'' if meta['excluded'] == 1 else 's'} in this database are "
            "excluded from every figure on this page.</b>"
        ]
        if meta.get("excluded_other_machine"):
            parts.append(
                f" {meta['excluded_other_machine']} were measured on a "
                f"different machine ({others}) — the whole comparison rests "
                "on the machine being held fixed, so a row measured "
                "elsewhere cannot be pooled with the campaign even when it "
                "covers the same condition."
            )
        if meta.get("excluded_same_machine"):
            parts.append(
                f" {meta['excluded_same_machine']} more were measured on "
                "this same machine but during an earlier, superseded attempt "
                "at this campaign — left behind while a bug was being fixed, "
                "and excluded on the same principle even though the hardware "
                "matches, since they are not part of the single verified run "
                "this page reports on."
            )
        parts.append(
            " The rows are kept rather than deleted, so every exclusion "
            "above can be checked against the database directly."
        )
        caveat("".join(parts))


# ═══════════════════════════════════ 7 — WHAT THE BASELINES ARE
with tabs[8]:
    panel("SNN methods and the measurement control",
          "The five SNN simulators are the methods studied. A separate internal "
          "reference is an internal benchmark control, not a sixth simulator "
          "or a candidate for recommendation.")
    ordered = FRAMEWORKS
    for start in range(0, len(ordered), 3):
        for fw, col in zip(ordered[start:start + 3], st.columns(3)):
            with col:
                st.markdown(
                    f'<div class="explain" style="--c:{fw["color"]}">'
                    f'<h4>{fw["label"]}</h4>'
                    f'<div class="kind">'
                    f'{"experimental control" if fw["is_control"] else fw["kind"]}'
                    f' · {fw["n_backends"]} backend'
                    f'{"" if fw["n_backends"] == 1 else "s"}</div>'
                    f'<div class="one">{fw["one_line"]}</div>'
                    f'<div class="detail">{fw["detail"]}</div>'
                    f'<div class="best"><b>Best for:</b> {fw["best_for"]}'
                    f'</div></div>',
                    unsafe_allow_html=True)

    st.caption("The benchmark dataset also contains separate internal validation records; "
               "Brian2/NumPy is a real Brian2 execution backend and remains compared.")
    st.markdown("#### Research gaps this benchmark addresses")
    gaps = data.get_gaps()
    # One column per gap: zipping against a fixed column count would
    # silently drop a gap the moment a fourth was added, which is
    # exactly what happened when RQ4 was introduced.
    for g, col in zip(gaps, st.columns(len(gaps) or 1)):
        with col:
            st.markdown(
                f'<div class="panel"><div style="font-size:10px;font-weight:750;'
                f'letter-spacing:.07em;text-transform:uppercase;color:#4f93ea">'
                f'{g["rq"]}</div><h4>{g["title"]}</h4>'
                f'<div class="sub">{g["desc"]}</div></div>',
                unsafe_allow_html=True)

    st.markdown("#### What this dashboard does not claim")
    caveat(
        "<b>The energy figure is a proxy, not a measurement.</b> It is "
        "runtime × CPU utilisation × a configured TDP value, comparable only "
        "within this machine and this session. It is not joules at the wall "
        "socket.<br><br>"
        "<b>The simulators are not solving identical problems.</b> The "
        "tensor-based libraries run a discrete recurrence; the simulators "
        "integrate an ODE. The equivalence view bounds how far apart that lets "
        "the answers drift.<br><br>"
        "<b>One hardware platform, by design.</b> Holding the machine fixed "
        "is what allows a difference in runtime to be read as a difference "
        "between simulators rather than between machines. The consequence is "
        "that the absolute timings belong to this platform: the rankings and "
        "the scaling behaviour are the transferable results, not the "
        "millisecond values. Running the same harness on GPU hardware is set "
        "out as future work in the thesis.")



# ─────────────────────────────────────────── SUPERVISOR-REQUESTED PEER TABS
with tabs[0]:
    panel("All Simulators — side-by-side measured methods",
          "A peer-level tab rather than a hidden link. These are the five "
          "SNN simulators, with internal validation records excluded from rankings.")
    rows = [r for r in data.get_inference()
            if r["framework"] not in theme.CONTROL_FRAMEWORKS
            and not r.get("compile_dominated")]
    by_fw = {}
    for r in rows:
        prev = by_fw.get(r["framework"])
        if prev is None or r["runtime_median_s"] < prev["runtime_median_s"]:
            by_fw[r["framework"]] = r
    if by_fw:
        summary = []
        for fw in ALL_FW:
            r = by_fw.get(fw)
            if r:
                summary.append(dict(Simulator=theme.label_for(fw),
                                    **{"Measured backend": r["backend"],
                                       "Inference runtime (s)": round(r["runtime_median_s"],6),
                                       "Peak RSS (MB)": round(r["peak_rss_mb"],1)}))
        st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
        st.caption("Each row names that simulator's lowest measured inference-runtime "
                   "backend at the 100-neuron reference condition. These are "
                   "observations, not hardware-independent winners. Use the "
                   "Optimisation tab for scenario-specific joint selection.")
    else:
        st.info("No comparable measurements available.")

with tabs[1]:
    panel("Optimisation — four-criterion method selection",
          "Network size is a measured inference-workload setting, not an optimisation "
          "weight. Adjust inference, memory, scalability and optionally accuracy "
          "importance; Streamlit recalculates immediately when a slider moves.")
    sizes = optimization.available_sizes()
    if sizes:
        sc1, sc2 = st.columns(2)
        with sc1:
            chosen_n = st.selectbox("Measured inference network size (neurons)", sizes, key="opt_n")
        with sc2:
            mem_cap = st.number_input("Maximum peak RSS (MB; 0 = no cap)", min_value=0,
                                      value=0, step=100, key="opt_cap")
        norm_label = st.radio("Normalisation of the measured criteria",
                              ["Min–max (0 = best, 1 = worst)", "Share of total (value ÷ sum)"],
                              horizontal=True, key="opt_norm")
        norm = "share" if norm_label.startswith("Share") else "minmax"
        def _apply_preset(w):
            st.session_state["opt_inf"], st.session_state["opt_mem"] = w["inference"], w["memory"]
            st.session_state["opt_scale"], st.session_state["opt_acc"] = w["scalability"], w["accuracy"]
        _presets = robustness.presets()
        st.caption("Quick choices (each is an existing reader profile) - or set the sliders yourself:")
        for _col, _pr in zip(st.columns(len(_presets)), _presets):
            _col.button(_pr["label"], key=f"opt_preset_{_pr['key']}", on_click=_apply_preset, args=(_pr["weights"],),
                        help=f"Reader profile: {_pr['profile']}", use_container_width=True)
        wc1, wc2, wc3, wc4 = st.columns(4)
        with wc1:
            wi = st.slider("Inference speed importance", 0, 100, 50, 5, key="opt_inf")
        with wc2:
            wm = st.slider("Memory importance (less extra memory as the network grows)", 0, 100, 50, 5, key="opt_mem")
        with wc3:
            ws = st.slider("Scalability importance (runtime grows more slowly)", 0, 100, 50, 5, key="opt_scale")
        with wc4:
            wa = st.slider("Accuracy importance (exploratory)", 0, 100, 0, 5, key="opt_acc")
        weights = dict(inference=wi, memory=wm, scalability=ws, accuracy=wa)
        if sum(weights.values()) == 0:
            st.warning("At least one priority must be greater than zero.")
        else:
            result = optimization.evaluate_four(chosen_n, weights,
                         None if mem_cap == 0 else mem_cap, normalisation=norm)
            st.caption("Effective priorities: " + " · ".join(
                f"{name}: {pct*100:.1f}%" for name, pct in result['weights'].items()))
            if result['exploratory']:
                st.warning("EXPLORATORY: MNIST accuracy comes from a different task, "
                           "with native learning rules that optimise different objectives. "
                           "The four-criterion score is a preference illustration, NOT "
                           "a controlled comparison of equivalent learning methods.")
            else:
                st.info("Accuracy is visible for context but carries no scoring weight. "
                        "This is a three-criterion inference-cost selection analysis.")
            if result['ok']:
                robustness.decorate(result, chosen_n, weights, None if mem_cap == 0 else mem_cap, norm)
                _ans = robustness.answer(result)
                st.markdown(f"**{_ans['badge']}**")
                st.markdown(f"### {_ans['lead']}")
                for _note in _ans['notes']:
                    st.markdown(f"- {_note}")
                st.caption("How to read this page: " + robustness.HOW_TO_READ)
                leader = result['winner']
                st.success(f"Conditional recommendation: {leader['id']} · "
                           f"inference {leader['runtime_s']:.5f} s · "
                           f"peak memory {leader['memory_mb']:.1f} MB "
                           f"(growth {leader['memory_growth_mb']:.1f} MB) · "
                           f"scaling k = {leader['scaling_k']:.3f}. "
                           "No software is accelerated by this calculation.")
                ordered = result['rows']
                tie = result['tie']
                if tie['is_tie']:
                    st.warning(robustness.tie_sentence(tie))
                stab = result['stability']
                if stab:
                    st.markdown("#### Stability of this recommendation")
                    marks = {'same': '✓', 'changes': '✗', 'becomes_tie': '≈', 'resolves': '≈', 'n/a': '–'}
                    lines = [f"- {marks[c['status']]} {c['text']}" for c in stab['checks']]
                    if stab['margin']:
                        lines.append(f"- Δ Margin to runner-up ({stab['margin']['runner_up']}): "
                                     f"**{stab['margin']['value']:.4f}** ({stab['margin']['note']})")
                    st.markdown("\n".join(lines))
                    st.caption(stab['note'])
                st.markdown("#### Weighted-cost contributions (shorter is better)")
                chart = go.Figure()
                for key, label, color in [
                   ('inference', 'Inference', '#3273b8'),
                   ('memory', 'Memory', '#21a39a'),
                   ('scalability', 'Scalability', '#d79b2d'),
                   ('accuracy', 'Accuracy*', '#9a6acc')]:
                    chart.add_trace(go.Bar(name=label,
                              y=[r['id'] for r in ordered],
                              x=[r['contributions'][key] for r in ordered],
                              marker_color=color, orientation='h'))
                chart.update_layout(barmode='stack', height=420,
                                    yaxis=dict(autorange='reversed'),
                                    xaxis_title='Normalised weighted cost (lower is better)',
                                    margin=dict(l=20,r=15,t=35,b=35))
                st.plotly_chart(chart, use_container_width=True)
                st.markdown("#### Inference runtime versus memory")
                scatter = go.Figure()
                for ix, r in enumerate(ordered):
                    scatter.add_trace(go.Scatter(
                        x=[r['runtime_s']],y=[r['memory_mb']], mode='markers+text',
                        text=[r['id']],textposition='top center',showlegend=False,
                        marker=dict(size=16 if ix==0 else (12 if r['pareto'] else 9),
                                    color=theme.color_for(r['framework']),
                                    symbol='star' if ix == 0 else ('diamond' if r['pareto'] else 'circle'))))
                scatter.update_xaxes(type='log', title='Measured inference runtime (s)')
                scatter.update_yaxes(type='log', title='Peak process RSS (MB)')
                scatter.update_layout(height=410, margin=dict(l=20,r=15,t=25,b=35))
                st.plotly_chart(scatter, use_container_width=True)
                display = [dict(Rank=i, Backend=r['id'],
                          Inference_seconds=round(r['runtime_s'],6),
                          Peak_RSS_MB=round(r['memory_mb'],1),
                          Memory_growth_MB=round(r['memory_growth_mb'],1),
                          Scaling_exponent=round(r['scaling_k'],3),
                          Scaling_R_squared=round(r['scaling_r2'],3) if r['scaling_r2'] is not None else None,
                          Native_MNIST_accuracy_pct=round(r['accuracy_pct'],2) if r['accuracy_pct'] is not None else None,
                          Weighted_cost=round(r['score'],4), Rank_sum=r['rank_sum'], Pareto=r['pareto'],
                          Wins_on_priority_grid=f"{r['scenario_wins']}/{result['n_grid_points']}")
                          for i,r in enumerate(ordered,1)]
                prof = robustness.attach_profile_ties(optimization.evaluate_profiles(
                    chosen_n, None if mem_cap == 0 else mem_cap, normalisation=norm, extra=weights))
                st.markdown("#### Reader profiles (output layer of the selection network)")
                st.caption("Each profile is a weighted sum y = Wx of the normalised criteria. "
                           "Lower score is better; * = uses exploratory accuracy. Profiles are "
                           "illustrative readers, not elicited preferences.")
                ptab = [dict(Profile=pf['label'],
                             Recommended=prof['labels'][pf['key']],
                             Weights=", ".join(f"{k} {v*100:.0f}%" for k, v in pf['weights'].items() if v > 0))
                        for pf in prof['profiles']]
                st.dataframe(pd.DataFrame(ptab), use_container_width=True, hide_index=True)
                sm = optimization.softmax_priorities(prof)
                st.markdown("#### Activation function")
                st.caption("Each simulator is represented by its best eligible backend for the "
                           "profile; its priority is exp(-y/τ) divided by the sum over the "
                           f"simulators, with τ = {sm['tau']:g}. Priorities add up to 100% per "
                           "profile. Softmax is monotone, so the simulator with the highest "
                           "priority is always the one whose backend is recommended; the "
                           "priorities show how clear that choice is. They are not probabilities "
                           "that a simulator is truly best.")
                stab = [dict({'Profile': pf['label']},
                             **{theme.FRAMEWORK_LABELS.get(s_, s_): (f"{100*pf['priority'][s_]:.1f}%"
                                                               if s_ in pf['priority'] else '—')
                                for s_ in sm['simulators']},
                             **{'Highest priority': ('no difference (all tied)' if pf['tied'] else
                                                     f"{theme.FRAMEWORK_LABELS.get(pf['rows'][0]['simulator'], pf['rows'][0]['simulator'])} via {pf['rows'][0]['backend']}")})
                        for pf in sm['profiles']]
                st.dataframe(pd.DataFrame(stab), use_container_width=True, hide_index=True)
                sm_labels = {pf['label']: pf for pf in sm['profiles']}
                sm_pick = st.selectbox("Activation curve for profile", list(sm_labels),
                                       index=next((i for i, pf in enumerate(sm['profiles'])
                                                   if pf['key'] == 'balanced'), 0),
                                       key="softmax_curve_profile")
                cur = optimization.softmax_curve(sm_labels[sm_pick], sm['tau'])
                pmax = max(p_['priority'] for p_ in cur['points'])
                ymax = min(1.0, max(0.5, math.ceil(pmax * 10 + 0.5) / 10))
                cfig = go.Figure()
                cx, cy = zip(*[(x_, y_) for x_, y_ in cur['curve'] if y_ <= ymax * 1.02])
                cfig.add_trace(go.Scatter(x=cx, y=cy, mode="lines", line=dict(color="#334155", width=2),
                                          name="softmax output", hoverinfo="skip"))
                for p_ in cur['points']:
                    lab = theme.FRAMEWORK_LABELS.get(p_['simulator'], p_['simulator'])
                    cfig.add_shape(type="line", x0=p_['score'], x1=p_['score'], y0=0, y1=p_['priority'],
                                   line=dict(color="#2a6db0", dash="dash", width=1))
                    cfig.add_shape(type="line", x0=1, x1=p_['score'], y0=p_['priority'], y1=p_['priority'],
                                   line=dict(color="#2a6db0", dash="dot", width=1))
                    cfig.add_trace(go.Scatter(
                        x=[p_['score']], y=[p_['priority']], mode="markers+text",
                        marker=dict(color="#2a6db0", size=9), text=[f"{lab} {100*p_['priority']:.1f}%"],
                        textposition="top left", showlegend=False,
                        hovertemplate=f"{lab} via {p_['backend']}<br>y = %{{x:.3f}}<br>π = %{{y:.3f}}<extra></extra>"))
                cfig.update_layout(height=380, margin=dict(l=60, r=20, t=20, b=50), showlegend=False,
                                   xaxis=dict(title="Simulator score y (best eligible backend; lower is better →)",
                                              range=[1, 0]),
                                   yaxis=dict(title="Softmax priority π", range=[0, ymax]))
                st.plotly_chart(cfig, width="stretch")
                st.markdown("#### Measured inputs and derived ranking")
                st.dataframe(pd.DataFrame(display), use_container_width=True, hide_index=True)
                st.download_button("Export all four-criterion evidence (CSV)",
                        pd.DataFrame(display).to_csv(index=False).encode('utf-8'),
                        f"optimization-four-criteria-N{chosen_n}.csv", mime='text/csv',
                        key='opt_download')
                st.caption("Memory is scored as growth in peak process memory above "
                           "the same backend's footprint at the smallest measured size, "
                           "because the absolute footprint mostly reflects which process "
                           "was measured. Scaling k is fitted across five measured network sizes; "
                           "a small k is not proof of universally better scaling when "
                           "fixed overhead dominates or fit R² is low. Accuracy is "
                           "native MNIST accuracy at 60,000 training images, 10 epochs, "
                           "hidden 256—not accuracy for the selected inference network size. "
                           "Priority-grid wins describe deterministic sensitivity, not probability.")
            else:
                st.warning(result['notice'])
        with st.expander("Terms used on this page"):
            for _term, _text in robustness.GLOSSARY:
                st.markdown(f"**{_term}.** {_text}")
            st.caption("Backend names: " + "; ".join(f"{i} = {n}" for i, n in robustness.names()))
    else:
        st.info("No measured scalability data available.")

# ══════════════════════════════════════════════════════ ROBUSTNESS
with tabs[9]:
    rb = robustness.load_robustness()
    st.markdown(f"**{robustness.robustness_lead(rb)}**")
    st.subheader(f"{rb['headline']['stable']} of {rb['headline']['total']} recommendations unchanged under all checks")
    st.caption("Nine profiles × five measured sizes (session A, min–max). Tags: N = normalisation, "
               "S = session B, R = scalability removed, T = exact tie. " + rb['caption'])
    sizes = list(rb['sizes'])
    glyph = {'stable': '✓', 'changes': '✗', 'tie': '≈'}
    gtab = [dict(Profile=p, **{f"N = {n:,}": f"{glyph[rb['grid'][p][n]['status']]} {rb['grid'][p][n]['pick']}"
                                 + (f" [{''.join(rb['grid'][p][n]['tags'])}]" if rb['grid'][p][n]['tags'] else '')
                                 for n in sizes}) for p in rb['profiles']]
    st.dataframe(pd.DataFrame(gtab), use_container_width=True, hide_index=True)
    st.markdown("#### What changes a recommendation")
    for c in rb['causes']:
        st.markdown(f"**{c['tag']} · {c['name']}: {c['count']}**  \n{c['text']}")
    st.markdown("#### What a wrong-size choice costs (Fast SNN, runtime only)")
    W = rb['wrong_size']
    fig = go.Figure()
    for key, rows, name, color in (('fwd', W['forward'], f"{W['forward_backend']} (best at N = 100) reused", '#3273b8'),
                                    ('rev', W['reverse'], f"{W['reverse_backend']} (best at N = 10,000) reused", '#d79b2d')):
        fig.add_trace(go.Bar(name=name, x=[f"N = {int(r['N']):,}" for r in rows],
                             y=[float(r['ratio_reused_over_best']) for r in rows],
                             text=[f"{float(r['ratio_reused_over_best']):.3g}×" for r in rows],
                             textposition='outside', marker_color=color))
    fig.update_yaxes(type='log', title='Runtime ÷ best runtime (log; 1× = the best)')
    fig.update_layout(barmode='group', height=380, margin=dict(l=20, r=15, t=25, b=35))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Session transfer: cells whose choice differs between sessions"):
        st.dataframe(pd.DataFrame(rb['session']), use_container_width=True, hide_index=True)
    st.download_button("Export robustness data (CSV)",
                       pd.DataFrame(robustness.export_rows()).to_csv(index=False).encode('utf-8'),
                       "robustness.csv", mime='text/csv', key='rb_csv')
    st.download_button("Export robustness data (JSON)", robustness.export_json().encode('utf-8'),
                       "robustness.json", mime='application/json', key='rb_json')


st.divider()
st.caption(
    f"{config.TITLE} · {getattr(config, 'AUTHOR', '')} · "
    f"{getattr(config, 'INSTITUTION', '')} · "
    f"{meta['counts']['runs']} measured runs across "
    f"{meta['counts']['conditions']} conditions, one hardware platform")
