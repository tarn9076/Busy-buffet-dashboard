"""
================================================================================
streamlit_app.py | Busy Buffet Dashboard - Hotel Amber 85
ATMIND Data Analytics Test 2026
================================================================================
[หมายเหตุถึงตัวเอง - อ่านก่อนแก้ไฟล์นี้]

หน้าเว็บเป็นภาษาอังกฤษ เพราะโจทย์มาเป็นภาษาอังกฤษ
แต่คอมเมนต์ในโค้ดเป็นภาษาไทย เพื่อให้กลับมาอ่านแล้วเข้าใจเองได้

โครงสร้าง 5 แท็บ:
    Tab 0 : Overview + ข้อจำกัดของข้อมูล
    Tab 1 : Task 1 - พิสูจน์คำพูดพนักงาน 3 ข้อ
    Tab 2 : Task 2 - หักล้างมาตรการ 3 ข้อ
    Tab 3 : Task 3 - ข้อเสนอเดียวแบบ conditional priority
    Tab 4 : Assumptions & Data Quality

[กฎเหล็ก - ห้ามลืม]
ห้ามใช้ภาษาไทยเป็นชื่อคอลัมน์หรือ keyword argument ของ Python เด็ดขาด
เพราะ Python จะ normalize สระอำ (ำ) แตกเป็นนิคหิต+สระอา (ํา) อัตโนมัติ
ทำให้ชื่อคอลัมน์ไม่ตรงกับ string ที่พิมพ์ ทั้งที่ตาเห็นเหมือนกัน
เคยพลาดมาแล้วตอนเทส deploy -> px.bar หา column ไม่เจอ
================================================================================
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Busy Buffet - Amber 85", layout="wide")

# --------------------------------------------------------------------------
# BLOCK 1: ค่าคงที่ + โหลดข้อมูล
# --------------------------------------------------------------------------
# เรียงวันตามปฏิทิน ไม่ให้ plotly เรียงตามตัวอักษรเอง
DAY_ORDER = ["Fri 13 Mar", "Sat 14 Mar", "Sun 15 Mar", "Tue 17 Mar", "Wed 18 Mar"]

# แปลงชื่อวันจากไฟล์ (ภาษาไทย) เป็นอังกฤษสำหรับแสดงผล
DAY_MAP = {
    "ศุกร์ 13/3": "Fri 13 Mar", "เสาร์ 14/3": "Sat 14 Mar",
    "อาทิตย์ 15/3": "Sun 15 Mar", "อังคาร 17/3": "Tue 17 Mar",
    "พุธ 18/3": "Wed 18 Mar",
}

# สีประจำ guest type ใช้ให้เหมือนกันทุกกราฟ คนดูจะจำได้เอง
COLOR_GUEST = {"In house": "#2E86AB", "Walk in": "#F18F01"}
RED = "#D64545"


@st.cache_data
def load():
    """โหลดไฟล์ที่ผ่าน cleaning pipeline (clean_data.py) มาแล้ว"""
    g = pd.read_csv("clean_groups.csv")
    u = pd.read_csv("clean_units.csv")
    # แปลงชื่อวันเป็นอังกฤษตั้งแต่ตอนโหลด จะได้ไม่ต้องแปลงซ้ำทุกกราฟ
    g["day"] = g["day_label"].map(DAY_MAP)
    u["day"] = u["day_label"].map(DAY_MAP)
    return g, u


groups, units = load()


# --------------------------------------------------------------------------
# BLOCK 2: ฟังก์ชันคำนวณ occupancy และความยาวคิว รายนาที
# --------------------------------------------------------------------------
# วิธีคิด: สร้างแกนเวลา 1440 ช่อง (1 วัน = 1440 นาที)
# แล้วไล่ทุกกลุ่ม บวก +1 ลงในทุกนาทีที่โต๊ะถูกครอง
# ทำแบบนี้เพราะคำถาม "ตอน 9 โมงมีกี่โต๊ะถูกใช้" ตอบได้ตรงกว่าการเฉลี่ยรายชั่วโมง

@st.cache_data
def occupancy_curve(day, cap_minutes=None):
    """คืน array 1440 ช่อง = จำนวนหน่วยโต๊ะที่ถูกครองในแต่ละนาที
    cap_minutes: ถ้าใส่ จะจำลองว่าบังคับให้ลุกภายในกี่นาที (ใช้ simulate Action 1)
    """
    sub = units[units["day"] == day].dropna(subset=["meal_start_min", "meal_end_min"])
    grid = np.zeros(1440)
    for _, r in sub.iterrows():
        a = int(r["meal_start_min"])
        b = int(r["meal_end_min"])
        if cap_minutes is not None:
            b = int(min(b, a + cap_minutes))
        if b > a:
            grid[a:b] += 1
    return grid


@st.cache_data
def queue_curve(day):
    """คืน array 1440 ช่อง = จำนวนกลุ่มที่ยืนรออยู่ในคิวแต่ละนาที"""
    sub = groups[(groups["day"] == day) & (groups["has_queue"])].dropna(
        subset=["queue_start_min", "queue_end_min"])
    grid = np.zeros(1440)
    for _, r in sub.iterrows():
        a, b = int(r["queue_start_min"]), int(r["queue_end_min"])
        if b > a:
            grid[a:b] += 1
    return grid


def hhmm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


# --------------------------------------------------------------------------
# BLOCK 3: หัวเรื่อง + แท็บ
# --------------------------------------------------------------------------
st.title("Busy Buffet — Hotel Amber 85")
st.caption("ATMIND Data Analytics Test 2026 · Data from 13–18 March 2026 (5 days)")

tab0, tab1, tab2, tab3, tab4 = st.tabs(
    ["Overview", "Task 1 · Staff Comments", "Task 2 · Why Actions Fail",
     "Task 3 · What To Do", "Assumptions & Data Quality"])


# ==========================================================================
# TAB 0 : Overview
# ==========================================================================
with tab0:
    queued_groups = int(groups["has_queue"].sum())
    walkaway_groups = int(groups["is_walkaway"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Groups analysed", f"{len(groups):,}")
    c2.metric("Recorded guests", f"{groups['pax'].sum():,.0f}")
    c3.metric("Median dining time", f"{groups['duration_min_clean'].median():.0f} min")
    c4.metric("Queue outcome", f"{queued_groups} queued · {walkaway_groups} left")

    st.markdown("### Important Notes Before the Charts")
    # เอาข้อจำกัดขึ้นก่อนกราฟ เพราะถ้าคนเห็นกราฟก่อน จะตีความเกินกว่าที่ข้อมูลรองรับ
    st.markdown("""I found four main limitations in the data that affect the analysis below:

1. **Incomplete week:** I only have data for 5 days instead of 7 (Monday, March 16, and Thursday are missing). Therefore, I cannot evaluate a full weekly trend.
2. **Queue interpretation:** Queue fields appear only on Saturday and Sunday. Following the dataset guide, blank queue fields are treated as direct seating; capture consistency remains a data-quality risk.
3. **No satisfaction data:** Waiting and walk-away behaviour are observable, but the dataset cannot prove that guests were unhappy or explain why they left.
4. **Missing financial data:** There are no actual sales, cost, or paid-cover fields, so pricing impact cannot be measured directly.""")

    st.divider()
    st.markdown("### How busy was each day")

    day_sum = (groups.groupby("day")
               .agg(n_groups=("service_no", "size"), n_pax=("pax", "sum"))
               .reindex(DAY_ORDER).reset_index())
    # แบ่งสีตาม weekday / weekend เพราะนี่คือสิ่งที่เราอยากให้คนเห็นความต่าง
    day_sum["type"] = day_sum["day"].map(
        groups.groupby("day")["is_weekend"].first()).map(
        {True: "Weekend", False: "Weekday"})

    # ต้องใส่ category_orders เสมอเมื่อใช้ color แบ่งกลุ่ม
    # เพราะ plotly จะวาดทีละกลุ่มสี ทำให้แกน x เรียงตามสี ไม่ใช่ตามวันที่
    fig = px.bar(day_sum, x="day", y="n_pax", text="n_pax", color="type",
                 category_orders={"day": DAY_ORDER,
                                  "type": ["Weekday", "Weekend"]},
                 color_discrete_map={"Weekday": "#B8D8E8", "Weekend": "#2E86AB"},
                 title="Guests per day",
                 labels={"day": "", "n_pax": "Guests", "type": ""})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    st.markdown("""Weekend demand is 40% higher than weekdays (averaging **160** vs. **114** guests per day). This clear jump means we need different staffing and table preparation for weekends.""")

    st.caption(
        "Queue records appear only on Saturday and Sunday; blank queue fields are treated as direct seating according to the task guide.")


# ==========================================================================
# TAB 1 : Task 1
# ==========================================================================
with tab1:
    st.header("Task 1 — Are the staff comments true?")

    # ---------------- COMMENT 1 ----------------
    st.markdown("## Comment 1")
    st.markdown(
        "> *In-house guests are unhappy that they have to wait for a table. "
        "Walk-in customers also queue for a long time and leave.*")
    st.markdown("### Answer: Partially supported — the operational symptoms are visible, but dissatisfaction is not measured")

    q = groups[groups["has_queue"]]
    t = (q.groupby("guest_type")
         .agg(queued=("service_no", "size"),
              walkaway=("is_walkaway", "sum"),
              med_wait=("wait_min", "median")).reset_index())
    t["walkaway_rate"] = (t["walkaway"] / t["queued"] * 100).round(1)
    t["med_wait"] = t["med_wait"].round(1)
    queue_metrics = t.set_index("guest_type")
    ih = queue_metrics.loc["In house"]
    wi = queue_metrics.loc["Walk in"]

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(t, x="guest_type", y="walkaway_rate", text="walkaway_rate",
                     color="guest_type", color_discrete_map=COLOR_GUEST,
                     title="Walk-away rate (%)",
                     labels={"guest_type": "", "walkaway_rate": "% who left the queue"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
    with c2:
        fig = px.bar(t, x="guest_type", y="med_wait", text="med_wait",
                     color="guest_type", color_discrete_map=COLOR_GUEST,
                     title="Median wait (minutes)",
                     labels={"guest_type": "", "med_wait": "Minutes"})
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')

    st.info(f"""**What the data supports:**

Among {len(q)} queued groups, in-house guests had a median wait of **{ih['med_wait']:.0f} minutes** and a **{ih['walkaway_rate']:.1f}% group walk-away rate**. Walk-in guests waited longer at **{wi['med_wait']:.1f} minutes**, with a lower **{wi['walkaway_rate']:.1f}% group walk-away rate**.

**What the data cannot prove:** The file contains no satisfaction score, complaint reason, or reason for leaving. Therefore, it supports the waiting and walk-away concern, but it cannot prove that guests were unhappy or identify expectation as the root cause.""")

    st.dataframe(
        t.rename(columns={"guest_type": "Guest type", "queued": "Groups queued",
                          "walkaway": "Left the queue", "med_wait": "Median wait (min)",
                          "walkaway_rate": "Walk-away rate (%)"}),
        width='stretch', hide_index=True)

    st.divider()

    # ---------------- COMMENT 2 ----------------
    st.markdown("## Comment 2")
    st.markdown(
        "> *We are very busy every day of the week. This buffet business is not "
        "possible for this hotel.*")
    st.markdown("### Answer: Not supported by the five observed days")

    rows = []
    for d in DAY_ORDER:
        curve = occupancy_curve(d)
        window = curve[390:750]        # ช่วงข้อมูลที่สังเกตอย่างสม่ำเสมอ 06:30-12:30
        day_groups = groups[groups["day"] == d]
        rows.append({"day": d,
                     "peak_units": int(curve.max()),
                     "avg_units": round(window.mean(), 1),
                     "peak_time": hhmm(curve.argmax()),
                     "queued_groups": int(day_groups["has_queue"].sum()),
                     "walkaways": int(day_groups["is_walkaway"].sum())})
    occ_tbl = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_bar(x=occ_tbl["day"], y=occ_tbl["peak_units"], name="Peak occupied units",
                marker_color="#B8D8E8", text=occ_tbl["peak_units"], textposition="outside")
    fig.add_bar(x=occ_tbl["day"], y=occ_tbl["avg_units"], name="Average occupied units",
                marker_color="#2E86AB", text=occ_tbl["avg_units"], textposition="outside")
    fig.update_layout(barmode="group", title="Estimated occupied table units by day",
                      yaxis_title="Occupied table units", xaxis_title="")
    st.plotly_chart(fig, width='stretch')

    # ดึงตัวเลขจาก occ_tbl โดยตรง ไม่พิมพ์มือ
    # เพราะข้อความกับตารางวางอยู่ข้างกันบนหน้าจอเดียวกัน ถ้าไม่ตรงกันจะเห็นทันที
    _o = occ_tbl.set_index("day")

    def _pk(day_name):
        return int(_o.loc[day_name, "peak_units"])

    def _av(day_name):
        return _o.loc[day_name, "avg_units"]

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"""**Primary evidence — occupied table units:**

Estimated occupied units were lower on Friday (**peak {_pk('Fri 13 Mar')}; average {_av('Fri 13 Mar')}**) and Tuesday (**{_pk('Tue 17 Mar')}; {_av('Tue 17 Mar')}**) than Saturday (**{_pk('Sat 14 Mar')}; {_av('Sat 14 Mar')}**) and Sunday (**{_pk('Sun 15 Mar')}; {_av('Sun 15 Mar')}**). Wednesday was closer to weekend conditions (**peak {_pk('Wed 18 Mar')}; average {_av('Wed 18 Mar')}**), so the pattern is not simply weekday versus weekend.

Recorded queues and walk-aways are supporting evidence only because queue-capture consistency remains uncertain. Occupied units are shown as counts rather than utilization percentages because the appendix does not confirm total physical capacity.

**Conclusion:** The claim that the buffet is “very busy every day” is not supported by this five-day sample. However, staffing, cost, and profit data are missing, so whether the business is financially sustainable cannot be tested.""")
    with c2:
        st.dataframe(
            occ_tbl.rename(columns={"day": "Day", "peak_units": "Peak units",
                                    "avg_units": "Avg units", "peak_time": "Peak time",
                                    "queued_groups": "Queued", "walkaways": "Walk-away"}),
            width='stretch', hide_index=True)

    st.caption("""**Data Limitation Note:** I only have data for 5 out of 7 days. While I can clearly see that daily demand varies significantly, I cannot draw conclusions about Monday or Thursday.""")

    st.divider()

    # ---------------- COMMENT 3 ----------------
    st.markdown("## Comment 3")
    st.markdown(
        "> *Walk-in customers sit the whole day. It is very difficult to find seats "
        "for in-house customers.*")
    st.markdown("### Answer: False — but staff correctly noticed a difference in dining behavior")

    dur = groups.dropna(subset=["duration_min_clean"])

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.box(dur, x="guest_type", y="duration_min_clean", color="guest_type",
                     color_discrete_map=COLOR_GUEST, points="outliers",
                     title="How long guests actually stay (minutes)",
                     labels={"guest_type": "", "duration_min_clean": "Minutes"})
        # เส้นอ้างอิง = สิทธิ์ที่โปรโมชั่นให้ 5 ชั่วโมง = 300 นาที
        fig.add_hline(y=300, line_dash="dash", line_color=RED,
                      annotation_text="What the promotion allows: 5 hours")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.metric("Groups over 5 hours", "0", delta=f"out of {len(dur)} valid records",
                  delta_color="off")
        st.metric("Longest stay in the whole file", "225 min",
                  delta="3 hours 45 minutes", delta_color="off")
        st.metric("Median stay", "52 min", delta="17% of the 5 hours allowed",
                  delta_color="off")

    long_groups = int((dur["duration_min_clean"] > 150).sum())
    st.markdown(f"""**The Reality of Dining Duration:**

Observed meal activity runs from 06:26 to 13:30. This is the observed data window, not a confirmed operating-hours schedule.

**Nobody used the full 5-hour allowance:** The longest valid group stay was 225 minutes (3 hours 45 minutes). Only **{long_groups} groups ({long_groups / len(dur) * 100:.1f}%)** stayed longer than 2.5 hours.""")

    st.success("""**What Staff Correctly Observed:**

Walk-in guests do stay 1.7 times longer than in-house guests (median 66 minutes vs. 38.5 minutes).

While walk-in groups make up 57% of valid dining records, they account for about 69% of observed dining minutes.

**Conclusion:** Staff accurately sensed that walk-ins have longer dining durations, which can reduce turnover during a peak. However, the perception that they "sit the whole day" is an exaggeration.""")

    share = (groups.dropna(subset=["duration_min_clean"])
             .groupby("guest_type")["duration_min_clean"].sum().reset_index())
    fig = px.pie(share, names="guest_type", values="duration_min_clean", hole=0.45,
                 color="guest_type", color_discrete_map=COLOR_GUEST,
                 title="Share of observed dining minutes")
    st.plotly_chart(fig, width='stretch')


# ==========================================================================
# TAB 2 : Task 2
# ==========================================================================
with tab2:
    st.header("Task 2 — Why the three actions should not be blanket daily policies")
    st.error("**Decision:** Do not implement any of the three proposed actions as an all-day, every-day policy based on the available evidence.")

    # ---------------- ACTION 1 ----------------
    st.markdown("## Action 1 — Cut the seating time from 5 hours")
    st.markdown("### Decision: Reject as proposed — the 5-hour allowance is not the binding constraint")

    d = groups["duration_min_clean"].dropna()
    caps = [300, 240, 180, 120, 90, 60]
    impact = pd.DataFrame({
        "cap_label": [f"{c} min ({c/60:.1f} h)" for c in caps],
        "n_affected": [int((d > c).sum()) for c in caps]})
    impact["pct_affected"] = (impact["n_affected"] / len(d) * 100).round(1)

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(impact, x="cap_label", y="n_affected", text="n_affected",
                     title="How many groups a time limit would really affect (out of 347)",
                     labels={"cap_label": "Time limit", "n_affected": "Groups affected"})
        fig.update_traces(textposition="outside", marker_color="#2E86AB")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            impact.rename(columns={"cap_label": "Time limit",
                                   "n_affected": "Groups affected",
                                   "pct_affected": "%"}),
            width='stretch', hide_index=True)

    st.markdown("""**Why this fails (Operational View):**

Reducing the limit from 5 to 4 hours has zero impact. My analysis shows that no one stays that long anyway.

To materially change dining behaviour, the limit would need to fall to 90 minutes. That would affect 59 groups, or 17% of the 347 valid dining records—not 17% of individual guests.""")

    # จำลองว่าถ้าบังคับ 90 นาที peak จะลดแค่ไหน
    sim = []
    for dd in DAY_ORDER:
        base = occupancy_curve(dd).max()
        capped = occupancy_curve(dd, cap_minutes=90).max()
        sim.append({"day": dd, "before": int(base), "after": int(capped)})
    sim_df = pd.DataFrame(sim)
    sim_long = sim_df.melt(id_vars="day", var_name="scenario", value_name="units")
    sim_long["scenario"] = sim_long["scenario"].map(
        {"before": "Today", "after": "With a 90-minute limit"})

    fig = px.bar(sim_long, x="day", y="units", color="scenario", barmode="group", text="units",
                 title="Estimated effect of a 90-minute limit on the daily peak",
                 labels={"day": "", "units": "Peak occupied table units", "scenario": ""},
                 color_discrete_map={"Today": "#B8D8E8",
                                     "With a 90-minute limit": "#2E86AB"})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    sun_before = int(sim_df.loc[sim_df["day"] == "Sun 15 Mar", "before"].iloc[0])
    sun_after = int(sim_df.loc[sim_df["day"] == "Sun 15 Mar", "after"].iloc[0])
    st.markdown(f"""**Why the proposed action should be rejected:** The Sunday peak falls from an estimated **{sun_before} to {sun_after} occupied table units**, while 59 groups would be affected by a 90-minute rule. The simulation only truncates recorded meal duration; it does not model cleaning time, guest reaction, or party-to-table matching. The size of those effects requires a pilot, but this limitation does not change the decision that a blanket time limit is not supported as a stand-alone solution.""")

    st.divider()

    # ---------------- ACTION 2 ----------------
    st.markdown("## Action 2 — Raise the price to 259 every day")
    st.markdown("### Decision: Reject a daily 259 THB price — it targets lower-intensity days most heavily")

    st.markdown("""**Note:** Since I do not have historical price elasticity or sales data, I calculated a break-even threshold instead: How many guests can we afford to lose before total revenue drops?""")

    be = []
    for dd in DAY_ORDER:
        price = int(groups[groups["day"] == dd]["menu_price"].iloc[0])
        be.append({"day": dd, "price": price,
                   "increase_pct": round((259 / price - 1) * 100, 1),
                   "breakeven_pct": round((1 - price / 259) * 100, 1)})
    be = pd.DataFrame(be)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(be, x="day", y="breakeven_pct", text="breakeven_pct",
                     color="price", color_continuous_scale=[RED, "#2E86AB"],
                     title="Maximum promotion-volume loss before simplified revenue declines",
                     labels={"day": "", "breakeven_pct": "Break-even volume loss (%)",
                             "price": "Current price"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            be.rename(columns={"day": "Day", "price": "Price now",
                               "increase_pct": "Increase (%)",
                               "breakeven_pct": "Can lose (%)"}),
            width='stretch', hide_index=True)

    st.markdown("""**Why the proposed action should be rejected (Commercial View):**

**Problem 1: Unknown demand response.** Under a simplified promotion-revenue calculation, raising weekday prices from 159 to 259 THB (+63%) can tolerate a maximum 38.6% volume loss before revenue declines. On weekends, the break-even loss is only 23.2%. The dataset contains no elasticity evidence to show which outcome is likely.

**Problem 2: The largest price increase is imposed on lower-intensity days.** Friday and Tuesday have lower peak and average occupied units than Saturday and Sunday. A daily increase may therefore reduce demand where operational pressure is already lower, without guaranteeing that weekend waiting will fall enough.

The exact demand loss cannot be quantified without elasticity data, but that uncertainty is a reason to pilot and measure—not a reason to adopt the blanket price.""")

    st.caption("""**Analytical Note:** Weekends are currently priced 25% higher and bring in more guests. However, because price and day-of-week always move together in this dataset, I cannot separate whether guests care more about the price or simply prefer weekend dining.""")

    st.divider()

    # ---------------- ACTION 3 ----------------
    st.markdown("## Action 3 — Let in-house guests skip the queue")
    st.markdown("### Decision: Reject permanent daily priority — it shifts access without adding capacity")

    qdays = []
    for dd in DAY_ORDER:
        has_data = bool(groups[groups["day"] == dd]["has_queue"].any())
        qc = queue_curve(dd)
        qdays.append({"day": dd,
                      "max_queue": int(qc.max()) if has_data else None,
                      "status": "Queue recorded" if has_data else "Direct seating under guide"})
    qdays = pd.DataFrame(qdays)

    c1, c2, c3 = st.columns(3)
    c1.metric("Days with queue data", "2 of 5")
    c2.metric("In-house groups that queued", "25")
    c3.metric("Walk-in groups that queued", "48")

    st.dataframe(
        qdays.rename(columns={"day": "Day", "max_queue": "Longest queue (groups)",
                              "status": "Queue data"}),
        width='stretch', hide_index=True)

    st.markdown("""**Why the proposed action should be rejected as a blanket daily rule:**

**Reason 1: It is inactive on days without a recorded queue.** Under the dataset guide, Friday, Tuesday, and Wednesday are treated as direct seating, so a daily priority rule adds no value on those observed days.

**Reason 2: It redistributes access rather than adding capacity.** On Sunday, 19 in-house and 35 walk-in groups queued. Moving in-house groups forward would likely transfer some delay to walk-ins. The exact size of the impact requires a priority-queue simulation or pilot, but the action still does not create additional capacity.

**Reason 3: It needs guardrails.** Unlimited queue-skipping could damage walk-in experience and increase their walk-away rate. The action is more defensible as a conditional, monitored rule than as permanent priority all day.""")

    st.info("""**Conclusion:** The data does not support permanent queue-skipping every day. It does support testing a limited priority rule during an active queue, while tracking outcomes for both guest types.""")


# ==========================================================================
# TAB 3 : Task 3
# ==========================================================================
with tab3:
    st.header("Task 3 — Recommended action")

    st.markdown("""### Test conditional in-house priority when the active queue reaches 5 groups

This is a modified version of Action 3—not permanent queue-skipping. It activates only during a visible queue and is designed as a monitored pilot. The goal is to protect the hotel-guest experience without applying a price increase or time restriction to every customer.""")

    st.markdown("### When would the rule activate?")

    day_pick = st.selectbox("Pick a queue day", ["Sun 15 Mar", "Sat 14 Mar"], index=0)
    qc = queue_curve(day_pick)
    x = list(range(6 * 60, 14 * 60))
    active_minutes = int((qc >= 5).sum())
    max_queue = int(qc.max())

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[hhmm(m) for m in x], y=[qc[m] for m in x],
                             name="Groups waiting",
                             line=dict(color="#F18F01", width=3), fill="tozeroy"))
    fig.add_hline(y=5, line_dash="dash", line_color=RED,
                  annotation_text="Pilot trigger: 5 groups")
    fig.update_layout(
        title=f"{day_pick} — active queue by minute",
        xaxis_title="Time", yaxis_title="Groups waiting",
        yaxis_range=[0, max(10, max_queue + 2)], height=430,
        showlegend=False)
    fig.update_xaxes(tickmode="array",
                     tickvals=[hhmm(m) for m in range(6 * 60, 14 * 60, 60)])
    st.plotly_chart(fig, width='stretch')

    c1, c2, c3 = st.columns(3)
    c1.metric("Pilot trigger", "5 groups")
    c2.metric("Maximum recorded queue", f"{max_queue} groups")
    c3.metric("Rule active on selected day", f"{active_minutes} minutes")

    st.caption("Queue length is used as the trigger because it is directly observable. Total physical table capacity and cleaning/reset time are not confirmed in the dataset.")

    st.divider()
    st.markdown("## Evidence for the 5-group working threshold")

    q2 = groups[groups["has_queue"]].dropna(
        subset=["queue_start_min", "queue_end_min", "wait_min"]).copy()

    # นับเฉพาะกลุ่มที่เริ่มรอก่อนกลุ่มปัจจุบันและยังไม่ออกจากคิว ไม่รวมตัวเอง
    def qlen_at_arrival(row):
        same_day = q2[q2["day"] == row["day"]]
        t = row["queue_start_min"]
        return int(((same_day["queue_start_min"] < t) &
                    (same_day["queue_end_min"] > t)).sum())

    q2["qlen"] = q2.apply(qlen_at_arrival, axis=1)
    q2["bucket"] = pd.cut(q2["qlen"], [-1, 2, 4, 6, 9, 99],
                          labels=["0-2", "3-4", "5-6", "7-9", "10+"])
    bk = (q2.groupby("bucket", observed=False)
          .agg(n=("service_no", "size"), med_wait=("wait_min", "median")).reset_index())
    bk["med_wait"] = bk["med_wait"].round(1)

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(bk, x="bucket", y="med_wait", text="med_wait",
                     title="Observed wait by groups already in the queue at arrival",
                     labels={"bucket": "Groups already waiting", "med_wait": "Median wait (minutes)"})
        fig.update_traces(textposition="outside", marker_color="#2E86AB")
        fig.add_vrect(x0=1.5, x1=2.5, fillcolor="#E8A33D", opacity=0.18, line_width=0,
                      annotation_text="working trigger")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            bk.rename(columns={"bucket": "Groups ahead", "n": "Queued groups",
                               "med_wait": "Median wait (min)"}),
            width='stretch', hide_index=True)
        trigger_row = bk[bk["bucket"].astype(str) == "5-6"].iloc[0]
        st.metric("Observed at 5–6 ahead", f"{trigger_row['med_wait']:.0f} min median",
                  delta=f"n = {int(trigger_row['n'])} queued groups", delta_color="off")

    st.info("""**Why this is a pilot threshold—not a proven tipping point:** Median wait rises as the queue becomes longer, and a five-group trigger is simple for a hostess to observe using queue cards. However, the 5–6 group bucket is small and all queue evidence comes from only two days. The threshold must be validated and adjusted during the pilot.""")

    st.markdown("""### Operating rule

1. Keep normal first-come-first-served seating while fewer than 5 groups are waiting.
2. At 5 or more groups, verify in-house status using the hotel's normal room/name check.
3. Seat one compatible in-house group at the next suitable table, then seat the next compatible walk-in group before using priority again.
4. Turn the rule off once the active queue falls below 5 groups.

The alternating guardrail prevents unlimited queue-skipping and makes the impact on walk-in guests measurable.""")

    st.markdown("""### Two-weekend pilot and success measures

Track the following before and during the pilot:

- In-house median and P90 wait time
- In-house group walk-away rate
- Walk-in median/P90 wait and group walk-away rate
- Seated guests per hour
- Complaints or satisfaction feedback by guest type

**Decision rule:** Continue only if in-house waiting or walk-away improves without a material deterioration in walk-in outcomes. The current 28% in-house walk-away rate is based on only 25 queued groups, so it is a working baseline—not a stable target.""")


# ==========================================================================
# TAB 4 : Assumptions & Data Quality
# ==========================================================================
with tab4:
    st.header("Assumptions & Data Quality Methodology")

    st.markdown("""Source definitions are followed first. Where the file is ambiguous, assumptions are documented separately and are not presented as confirmed physical facts.""")

    st.markdown("### Assumptions")
    assumptions = pd.DataFrame([
        ["A-01", "Sheet names are day + month, so the data is 13–18 March 2026",
         "The 2026 calendar matches the Sat–Sun peak, and the last digit of each sheet name is the month"],
        ["A-02", "Bare table numbers are mapped only to estimate occupied table units",
         "The mapping is an analytical convenience for time-of-day comparison; it is not used to claim total physical capacity."],
        ["A-03", "Table 16 is retained as an undocumented observed table identifier",
         "It appears 24 times across all five days, but its physical size and capacity require hotel confirmation."],
        ["A-04", "Table 15 and 15A/15B are treated as alternative recorded setups",
         "The full and split labels are not added together to estimate total restaurant capacity."],
        ["A-05", "Blank queue fields are treated as direct seating",
         "This follows the dataset guide. Because three entire days are blank, capture consistency remains a limitation."],
        ["A-06", "06:26 to 13:30 is the observed activity window",
         "It is derived from the earliest and latest valid meal records, not assumed to be official operating hours."],
        ["A-07", "Guest_type follows the appendix definition",
         "In house means a hotel guest; Walk in means a visitor who came for breakfast."],
    ], columns=["Code", "Assumption", "Evidence"])
    st.dataframe(assumptions, width='stretch', hide_index=True)

    st.markdown("### Data quality issues found")

    flag_rows = []
    for f in groups["dq_flags"].fillna(""):
        for x in f.split("|"):
            if x:
                flag_rows.append(x)
    flag_count = pd.Series(flag_rows).value_counts().reset_index()
    flag_count.columns = ["flag", "n_rows"]

    FLAG_EN = {
        "DQ01_NO_QUEUE_DATA_THIS_DAY": "No queue recorded; treated as direct seating under the guide",
        "DQ04_BARE_TABLE_NO": "Table number written short, no A/B side given",
        "DQ03_TABLE16_NOT_IN_APPENDIX": "Table 16 is not in the floor plan",
        "DQ16_PAX_OVER_CAPACITY": "More guests than the table can seat",
        "DQ06_SEPARATOR": "Combined tables use the wrong separator",
        "DQ05_TABLE15_SPLIT": "Table 15 was split, but the plan says it cannot be",
        "DQ14_PAX_ZERO_WALKAWAY": "No guest count because they left before sitting",
        "DQ13_PAX_ZERO_BUT_SEATED": "No guest count even though they were seated",
        "DQ11_DURATION_CENSORED": "Left exactly at closing time",
        "DQ_QUEUE_AREA": "Ate in the queueing area (table 99)",
        "DQ07_CROSS_ZONE_COMBINE": "Indoor and outdoor tables combined",
        "DQ10_MEALSTART_OUT_OF_HOURS": "Start time falls outside service hours",
        "DQ09_MEALEND_BEFORE_START": "End time is before start time",
        "DQ17_QUEUE_MEAL_TIME_CONFLICT": "Queue times conflict with recorded meal start",
    }
    flag_count["Issue"] = flag_count["flag"].map(FLAG_EN)
    st.dataframe(
        flag_count[["Issue", "n_rows", "flag"]].rename(
            columns={"n_rows": "Rows", "flag": "Code"}),
        width='stretch', hide_index=True)

    st.markdown("""**How I Handled Data Anomalies:**

I removed only one unrecoverable row that lacked usable data. For all other anomalies, I retained the records and assigned specific Data Quality (DQ) codes. This transparent approach preserves data integrity, allows future analysts to filter records intentionally, and ensures full auditability of my work.""")

    # นับกลุ่มที่เริ่มมื้อช่วง 06:00-06:59 เพื่อชี้ความผิดปกติของ label guest_type
    #
    # ทำไมต้องเขียนแบบเช็คคอลัมน์ก่อน:
    # meal_start_min เป็นคอลัมน์ที่ทั้งไฟล์นี้ใช้กับ units เท่านั้น ไม่เคยใช้กับ groups
    # ถ้า clean_groups.csv ไม่มีคอลัมน์นี้ แท็บทั้งแท็บจะพังด้วย KeyError
    # จึงเช็คก่อนว่ามีที่ไหน แล้วค่อยเลือกใช้ ถ้าไม่มีทั้งคู่ก็ข้ามหัวข้อนี้ไปเงียบ ๆ
    # ไม่ให้หน้าจอแดงตอนนำเสนอ
    if "meal_start_min" in groups.columns:
        early_groups = groups[
            (groups["meal_start_min"] >= 6 * 60) &
            (groups["meal_start_min"] < 7 * 60)
        ]
    elif "meal_start_min" in units.columns:
        # units เก็บรายหน่วยโต๊ะ กลุ่มที่ใช้ 2 โต๊ะจะมี 2 แถว
        # ต้อง dedupe ด้วย service_no ไม่งั้นจะนับกลุ่มซ้ำ
        early_groups = units[
            (units["meal_start_min"] >= 6 * 60) &
            (units["meal_start_min"] < 7 * 60)
        ]
        if "service_no" in early_groups.columns:
            early_groups = early_groups.drop_duplicates(subset=["service_no"])
    else:
        early_groups = groups.iloc[0:0]

    n_early = len(early_groups)
    if n_early > 0 and "guest_type" in early_groups.columns:
        early_walkins = int((early_groups["guest_type"] == "Walk in").sum())
        early_note = (
            f"\n5. **Guest-type label consistency:** Of the **{n_early} groups** whose meal "
            f"started between 06:00 and 06:59, **{early_walkins} "
            f"({early_walkins / n_early * 100:.0f}%)** are labelled Walk in. The count is "
            "valid, but the reason behind this pattern cannot be observed in the dataset. "
            "Front-of-house should confirm that the labels follow the appendix definition "
            "before guest type is used for operational targeting."
        )
        n_questions = "five"
    else:
        early_note = ""
        n_questions = "four"

    st.markdown(f"""### Remaining Data Blind Spots & Business Limitations

Despite cleaning the dataset, {n_questions} key questions require additional evidence:

1. **Missing days:** Why are Monday and Thursday absent, and are these five days representative of normal demand?
2. **Physical capacity:** What are the confirmed table configurations, seat counts, and the status of table 16 and 15A/15B?
3. **Guest experience:** Why did each group leave, and what satisfaction or complaint outcome followed the wait?
4. **Commercial sustainability:** Which guests actually paid the buffet price, and what were revenue, food cost, labour cost, and contribution margin?{early_note}""")

    with st.expander("View the cleaned dataset"):
        st.dataframe(groups, width='stretch')
