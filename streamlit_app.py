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
    Tab 3 : Task 3 - ข้อเสนอ (Plan A / Plan B)
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
    inv = pd.read_csv("table_inventory.csv")
    # แปลงชื่อวันเป็นอังกฤษตั้งแต่ตอนโหลด จะได้ไม่ต้องแปลงซ้ำทุกกราฟ
    g["day"] = g["day_label"].map(DAY_MAP)
    u["day"] = u["day_label"].map(DAY_MAP)
    return g, u, inv


groups, units, inventory = load()
TOTAL_UNITS = len(inventory)          # 32 หน่วยโต๊ะ = ตัวหารของ occupancy
TOTAL_SEATS = int(inventory["seats"].sum())


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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Groups served", f"{len(groups):,}")
    c2.metric("Total guests", f"{groups['pax'].sum():,.0f}")
    c3.metric("Median dining time", f"{groups['duration_min_clean'].median():.0f} min")
    c4.metric("Seating capacity", f"{TOTAL_UNITS} tables · {TOTAL_SEATS} seats")

    st.markdown("### Important Notes Before the Charts")
    # เอาข้อจำกัดขึ้นก่อนกราฟ เพราะถ้าคนเห็นกราฟก่อน จะตีความเกินกว่าที่ข้อมูลรองรับ
    st.markdown("""I found three main limitations in the data that affect the analysis below:

1. **Incomplete week:** I only have data for 5 days instead of 7 (Monday, March 16, and Thursday are missing). Therefore, I cannot evaluate a full weekly trend.
2. **Limited queue data:** Queue data is only available for 2 days (Saturday 14 and Sunday 15). All waiting-time insights are based solely on these two days.
3. **Missing financial data:** There are no price or sales columns, so I cannot measure how guests react to pricing.""")

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
        "Note: queue data was only recorded on Saturday 14 and Sunday 15.")


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
    st.markdown("### Answer: True — but the root cause is guest expectation, not just wait time")

    q = groups[(groups["queue_data_available"]) & (groups["has_queue"])]
    t = (q.groupby("guest_type")
         .agg(queued=("service_no", "size"),
              walkaway=("is_walkaway", "sum"),
              med_wait=("wait_min", "median")).reset_index())
    t["walkaway_rate"] = (t["walkaway"] / t["queued"] * 100).round(1)

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

    st.error("""**My Analysis & Key Takeaway:**

The data reveals an interesting contrast: In-house guests wait much less than walk-ins (28 mins vs. 42.5 mins median), yet they abandon the queue almost twice as often (28.0% walk-away rate vs. 14.6%).

**Why this happens (Operational & Commercial view):** Wait time itself is not the main problem. In-house guests have already paid for their rooms, so they expect immediate seating for breakfast. They simply have a much lower wait tolerance than walk-in visitors.

**Conclusion:** This is an expectation management issue, not a table capacity issue.""")

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
    st.markdown("### Answer: False — based on the 5 days of available data")

    rows = []
    for d in DAY_ORDER:
        curve = occupancy_curve(d)
        window = curve[390:750]        # 06:30-12:30 ช่วงที่ให้บริการจริง
        rows.append({"day": d,
                     "peak_pct": round(curve.max() / TOTAL_UNITS * 100, 1),
                     "avg_pct": round(window.mean() / TOTAL_UNITS * 100, 1),
                     "peak_time": hhmm(curve.argmax()),
                     "min_over75": int((curve >= 0.75 * TOTAL_UNITS).sum())})
    occ_tbl = pd.DataFrame(rows)

    fig = go.Figure()
    fig.add_bar(x=occ_tbl["day"], y=occ_tbl["peak_pct"], name="Peak of the day",
                marker_color="#B8D8E8", text=occ_tbl["peak_pct"], textposition="outside")
    fig.add_bar(x=occ_tbl["day"], y=occ_tbl["avg_pct"], name="Average while open",
                marker_color="#2E86AB", text=occ_tbl["avg_pct"], textposition="outside")
    # เส้น 75% = ระดับที่ร้านอาหารทั่วไปถือว่าเริ่มแน่น
    fig.add_hline(y=75, line_dash="dash", line_color=RED,
                  annotation_text="75% — a restaurant starts to feel full here")
    fig.update_layout(barmode="group", title="Table usage by day (%)",
                      yaxis_title="% of 32 tables", xaxis_title="")
    st.plotly_chart(fig, width='stretch')

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""**My Findings on Table Utilization:**

**Weekdays are under-utilized:** Friday and Tuesday never reach our 75% busy threshold. On average, Friday sits at only 26.8% occupancy, meaning half the restaurant remains empty for 5.5 hours.

**Peak crowding is temporary:** Sunday touches 90% occupancy, but only for 3 minutes.

**When we are actually busy:** The restaurant only experiences true crowding on Saturday and Sunday between 09:00 and 10:30, not every day.""")
    with c2:
        st.dataframe(
            occ_tbl.rename(columns={"day": "Day", "peak_pct": "Peak %",
                                    "avg_pct": "Avg %", "peak_time": "Peak time",
                                    "min_over75": "Min above 75%"}),
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
        st.metric("Guests who stayed over 5 hours", "0", delta="out of 347",
                  delta_color="off")
        st.metric("Longest stay in the whole file", "225 min",
                  delta="3 hours 45 minutes", delta_color="off")
        st.metric("Median stay", "52 min", delta="17% of the 5 hours allowed",
                  delta_color="off")

    st.markdown("""**The Reality of Dining Duration:**

The restaurant is open for 7 hours (06:26 to 13:30), meaning a 5-hour dining limit covers 71% of our total opening time.

To even attempt a 5-hour stay, a guest must arrive before 08:30 (only 40.5% of guests arrive that early).

**Nobody stayed the whole day:** The longest individual stay in the entire dataset was 225 minutes (3 hours 45 minutes). Only 8 guests (2.3%) stayed longer than 2.5 hours.""")

    st.success("""**What Staff Correctly Observed:**

Walk-in guests do stay 1.7 times longer than in-house guests (median 66 minutes vs. 38.5 minutes).

While walk-in groups make up only 57% of total groups, they consume 70% of total table-minutes.

**Conclusion:** Staff accurately sensed that walk-ins occupy tables longer and slow down table turnover, but the perception that they "sit the whole day" is an exaggeration.""")

    share = (units.dropna(subset=["duration_min_clean"])
             .groupby("guest_type")["duration_min_clean"].sum().reset_index())
    fig = px.pie(share, names="guest_type", values="duration_min_clean", hole=0.45,
                 color="guest_type", color_discrete_map=COLOR_GUEST,
                 title="Share of total table-minutes")
    st.plotly_chart(fig, width='stretch')


# ==========================================================================
# TAB 2 : Task 2
# ==========================================================================
with tab2:
    st.header("Task 2 — Why each proposed action will not work")

    # ---------------- ACTION 1 ----------------
    st.markdown("## Action 1 — Cut the seating time from 5 hours")
    st.markdown("### It tries to solve a problem that does not exist")

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

To actually free up tables, I would have to drop the time limit drastically to 90 minutes, which would negatively affect 59 groups (17% of all guests).""")

    # จำลองว่าถ้าบังคับ 90 นาที peak จะลดแค่ไหน
    sim = []
    for dd in DAY_ORDER:
        base = occupancy_curve(dd).max()
        capped = occupancy_curve(dd, cap_minutes=90).max()
        sim.append({"day": dd, "before": round(base / TOTAL_UNITS * 100, 1),
                    "after": round(capped / TOTAL_UNITS * 100, 1)})
    sim_long = pd.DataFrame(sim).melt(id_vars="day", var_name="scenario", value_name="pct")
    sim_long["scenario"] = sim_long["scenario"].map(
        {"before": "Today", "after": "With a 90-minute limit"})

    fig = px.bar(sim_long, x="day", y="pct", color="scenario", barmode="group", text="pct",
                 title="What a strict 90-minute limit would do to the busiest moment",
                 labels={"day": "", "pct": "Peak table usage (%)", "scenario": ""},
                 color_discrete_map={"Today": "#B8D8E8",
                                     "With a 90-minute limit": "#2E86AB"})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    st.markdown("""**Minimal results during peak hours:** Even with a strict 90-minute limit, Friday occupancy stays unchanged at 59.4%, and Sunday peak usage only drops slightly from 90.6% to 87.5%. Disrupting 1 in 6 guests for such a tiny gain is not worth the operational friction.""")

    st.divider()

    # ---------------- ACTION 2 ----------------
    st.markdown("## Action 2 — Raise the price to 259 every day")
    st.markdown("### Too risky for revenue, and it penalizes the wrong days")

    st.markdown("""**Note:** Since I do not have historical price elasticity or sales data, I calculated a break-even threshold instead: How many guests can we afford to lose before total revenue drops?""")

    walkin = groups[groups["guest_type"] == "Walk in"]
    be = []
    for dd in DAY_ORDER:
        sub = walkin[walkin["day"] == dd]
        price = int(groups[groups["day"] == dd]["menu_price"].iloc[0])
        pax = sub["pax"].sum()
        be.append({"day": dd, "price": price,
                   "increase_pct": round((259 / price - 1) * 100, 1),
                   "breakeven_pct": round((1 - price / 259) * 100, 1),
                   "revenue": int(pax * price)})
    be = pd.DataFrame(be)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(be, x="day", y="breakeven_pct", text="breakeven_pct",
                     color="price", color_continuous_scale=[RED, "#2E86AB"],
                     title="How many guests we can lose before we make less money",
                     labels={"day": "", "breakeven_pct": "% we can afford to lose",
                             "price": "Current price"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            be.rename(columns={"day": "Day", "price": "Price now",
                               "increase_pct": "Increase (%)",
                               "breakeven_pct": "Can lose (%)",
                               "revenue": "Revenue now (THB)"}),
            width='stretch', hide_index=True)

    st.markdown("""**Why this fails (Commercial View):**

**Problem 1: High financial risk.** Raising weekday prices from 159 to 259 THB (+63%) means if we lose more than 38.6% of weekday volume, we will actively lose money. On weekends, our margin for error is even tighter (23.2% max volume loss).

**Problem 2: It targets the wrong days.** This price hike lands heaviest on weekdays when tables are already 59% to 73% empty. We would be charging more during our slowest periods, while failing to solve the overcrowding problem on weekends.""")

    st.caption("""**Analytical Note:** Weekends are currently priced 25% higher and bring in more guests. However, because price and day-of-week always move together in this dataset, I cannot separate whether guests care more about the price or simply prefer weekend dining.""")

    st.divider()

    # ---------------- ACTION 3 ----------------
    st.markdown("## Action 3 — Let in-house guests skip the queue")
    st.markdown("### Good in theory, but impractical for daily operations")

    qdays = []
    for dd in DAY_ORDER:
        has_data = bool(groups[groups["day"] == dd]["queue_data_available"].iloc[0])
        qc = queue_curve(dd)
        qdays.append({"day": dd,
                      "max_queue": int(qc.max()) if has_data else None,
                      "status": "Recorded" if has_data else "Not recorded"})
    qdays = pd.DataFrame(qdays)

    c1, c2, c3 = st.columns(3)
    c1.metric("Days with queue data", "2 of 5")
    c2.metric("In-house groups that queued", "25")
    c3.metric("Walk-in groups that queued", "48")

    st.dataframe(
        qdays.rename(columns={"day": "Day", "max_queue": "Longest queue (groups)",
                              "status": "Queue data"}),
        width='stretch', hide_index=True)

    st.markdown("""**Why this fails (Operational View):**

**Reason 1: It is useless on weekdays.** On 3 out of 5 recorded days, there is no queue to skip. Table utilization only reaches 59–78%, so priority seating adds no value.

**Reason 2: It just shifts the bottleneck.** On Sunday, 19 in-house groups and 35 walk-in groups waited in line. If in-house guests skip ahead, walk-in wait times will jump by ~54%. Since our total table capacity remains the same, we do not solve the wait time — we only make it worse for walk-in visitors.

**Reason 3: Operations cannot easily identify guest types at the door.** A guest who booked a room without breakfast and pays at the door is recorded as a "Walk-in." Front-of-house staff cannot visually tell the difference during a busy rush.""")

    st.success("""**My Evidence from the Data:**

Between 06:00 and 06:59 AM, outside visitors rarely arrive. Yet, the data shows 21 Walk-in groups and only 2 In-house groups during this early hour (Walk-ins = 91% of early arrivals).

**Conclusion:** In this dataset, "Walk-in" likely indicates how the guest paid (e.g., paying at the door rather than pre-booking breakfast with the room), rather than whether they are actually staying at the hotel.""")


# ==========================================================================
# TAB 3 : Task 3
# ==========================================================================
with tab3:
    st.header("Task 3 — What I would do instead")

    st.markdown("""### Keep Action 3, but only turn it on when it is needed

**Why I focused on Action 3:** Of the three proposed actions, this is the only one that addresses a real operational issue in the data. In-house guests abandon the queue 28% of the time, even though their median wait is shorter than walk-ins. The other two actions try to solve problems that the data does not support.""")

    st.markdown("### Choosing the right trigger")

    day_pick = st.selectbox("Pick a day", ["Sun 15 Mar", "Sat 14 Mar"], index=0)
    occ = occupancy_curve(day_pick)
    qc = queue_curve(day_pick)
    x = list(range(6 * 60, 14 * 60))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[hhmm(m) for m in x],
                             y=[occ[m] / TOTAL_UNITS * 100 for m in x],
                             name="Table usage (%)",
                             line=dict(color="#2E86AB", width=2)))
    fig.add_trace(go.Scatter(x=[hhmm(m) for m in x], y=[qc[m] for m in x],
                             name="Groups waiting", yaxis="y2",
                             line=dict(color="#F18F01", width=2)))
    fig.add_hline(y=80, line_dash="dot", line_color="#999",
                  annotation_text="The idea I dropped: 80% table usage")
    fig.update_layout(
        title=f"{day_pick} — table usage against queue length",
        xaxis_title="Time",
        yaxis=dict(title="Table usage (%)", range=[0, 100]),
        yaxis2=dict(title="Groups waiting", overlaying="y", side="right",
                    range=[0, 25], showgrid=False),
        legend=dict(orientation="h", y=1.12), height=430)
    fig.update_xaxes(tickmode="array",
                     tickvals=[hhmm(m) for m in range(6 * 60, 14 * 60, 60)])
    st.plotly_chart(fig, width='stretch')

    st.error("""**Why I dropped the 80% Table Usage trigger:**

**My initial assumption:** I considered activating priority seating whenever table occupancy hit 80%. However, the data disproved this approach.

**The data mismatch:** At 09:00 on Sunday, 15 groups were waiting, but table usage showed only 71.9% (so the rule would stay OFF). At 11:30, usage showed 81.2% (rule turns ON), but only 1 group was waiting.

**The operational reality:** A table that appears "empty" in the system is often not ready for seating. Staff still need time to clear, clean, and reset the table (turnover lag). Therefore, table occupancy percentage is a poor trigger for queue management.""")

    st.divider()
    st.markdown("## Plan A — turn it on when 5 or more groups are waiting")

    q2 = groups[(groups["queue_data_available"]) & (groups["has_queue"])].dropna(
        subset=["queue_start_min"]).copy()

    # หา "ตอนกลุ่มนี้มาถึง มีคนรออยู่ในคิวกี่กลุ่ม"
    def qlen_at_arrival(row):
        same_day = q2[q2["day"] == row["day"]]
        t = row["queue_start_min"]
        return int(((same_day["queue_start_min"] <= t) &
                    (same_day["queue_end_min"] > t)).sum())

    q2["qlen"] = q2.apply(qlen_at_arrival, axis=1)
    q2["bucket"] = pd.cut(q2["qlen"], [-1, 2, 4, 6, 9, 99],
                          labels=["0-2", "3-4", "5-6", "7-9", "10+"])
    bk = (q2.groupby("bucket", observed=True)
          .agg(n=("service_no", "size"), med_wait=("wait_min", "median")).reset_index())

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(bk, x="bucket", y="med_wait", text="med_wait",
                     title="How long guests waited, based on the queue size when they arrived",
                     labels={"bucket": "Groups already in the queue", "med_wait": "Minutes waited"})
        fig.update_traces(textposition="outside", marker_color="#2E86AB")
        fig.add_vrect(x0=1.5, x1=2.5, fillcolor="#E8A33D", opacity=0.18, line_width=0,
                      annotation_text="wait doubles here")
        st.plotly_chart(fig, width='stretch')
    with c2:
        st.dataframe(
            bk.rename(columns={"bucket": "Queue length", "n": "Sample size",
                               "med_wait": "Median wait (min)"}),
            width='stretch', hide_index=True)
        st.metric("First jump", "5 groups", delta="wait doubles: 11.5 to 22 min",
                  delta_color="off")
        st.metric("Second jump", "10 groups", delta="wait goes 4x: up to 45 min",
                  delta_color="off")

    st.markdown("""**Why I selected a 5-group threshold:**

**Why not use walk-away rates?** Only 25 in-house groups ever queued in the dataset, and 7 left. A sample size of 7 is too small for statistical confidence.

**Using median wait time instead:** Wait time provides a much steadier trend. When the line reaches 5 groups, the median wait doubles from 11.5 to 22 minutes. When it hits 10 groups, the wait jumps 4x to 45 minutes. Therefore, 5 groups is the critical tipping point where intervention is needed.

**Why Plan A works for Operations:**

**Zero system reliance:** Hostesses can trigger this rule visually by counting physical queue cards — no math or software required.

**Targeted activation:** Based on weekend data, this rule would only activate for 33 minutes on Saturday and 173 minutes on Sunday. On weekdays, it remains inactive.

**Guest-facing clarity:** It reacts to what guests actually experience (length of the line), rather than an invisible table percentage.""")

    st.divider()
    st.markdown("## Plan B — keep 6 tables free for hotel guests during the rush")

    c1, c2, c3 = st.columns(3)
    c1.metric("Tables to keep free", "6 tables", delta="18.8% of 32", delta_color="off")
    c2.metric("What hotel guests really used", "6 tables",
              delta="same on Sat and Sun", delta_color="off")
    c3.metric("Still free for walk-ins", "26 tables", delta="they never used more than 23",
              delta_color="off")

    st.markdown("""**When to deploy Plan B instead:**

**The identification barrier:** If front-of-house staff cannot easily distinguish room-only guests from external visitors at the door, Plan A will fail. Misidentified hotel guests would be sent to the back of the line, leading to front-desk complaints.

**The operational solution:** Plan B bypasses door identification entirely by reserving a dedicated buffer of 6 tables for in-house breakfast guests during peak rush hours (08:30 – 11:00).

**Why 6 tables?** My analysis shows that 6 tables (18.8% of capacity) is the maximum concurrent demand from in-house guests between 08:30 and 11:00 on both Saturday and Sunday. This still leaves 26 tables for walk-ins, who never exceeded 23 concurrent tables in the dataset.""")

    st.divider()
    st.markdown("""### Data Limitation Note

All queue thresholds are derived from just 2 days of weekend queue data (73 groups total). While this provides the best analytical starting point available, it should be treated as a working baseline rather than a permanent rule.

**My Recommended Action Plan:**

**Test & Iterate:** Implement Plan A (or Plan B) as a two-week operational pilot.

**Data Collection:** Consistently record daily queue lengths and wait times during the trial.

**Success Metric:** Evaluate success by comparing the new walk-away rate against our current 28% baseline for in-house guests, and refine the threshold accordingly.""")


# ==========================================================================
# TAB 4 : Assumptions & Data Quality
# ==========================================================================
with tab4:
    st.header("Assumptions & Data Quality Methodology")

    st.markdown("""To deliver timely insights without delaying the project, I established clear, logical assumptions to address data anomalies and missing records. Every assumption listed below is backed by evidence found directly within the dataset.""")

    st.markdown("### Assumptions")
    assumptions = pd.DataFrame([
        ["A-01", "Sheet names are day + month, so the data is 13–18 March 2026",
         "The 2026 calendar matches the Sat–Sun peak, and the last digit of each sheet name is the month"],
        ["A-02", "Short table numbers follow a rule based on party size: 3 or more guests means the whole table",
         "I tested three interpretations of the floor plan. This approach resulted in the fewest seating conflicts (26 vs. 37 overlapping pairs)."],
        ["A-03", "Table 16 is a real table missing from the floor plan",
         "It appears 24 times, 4–5 times every single day. A typo would not repeat that evenly"],
        ["A-04", "Tables 15A and 15B are accepted as 2 seats each",
         "Applies to only 5 rows (1.4%). I chose the interpretation that maintains realistic total seating capacity."],
        ["A-05", "Total capacity is 32 tables and 74 seats",
         "Floor plan from the appendix, plus table 16 and 15A/15B from A-03 and A-04"],
        ["A-06", "The 3 days without queue data were not recorded, rather than having no queue",
         "These days reached 59–78% table occupancy. It is operationally unrealistic that zero guests waited; the queue was simply unrecorded."],
        ["A-07", "Service runs 06:26 to 13:30, about 7 hours",
         "Taken from the earliest and latest times in the data, not from an industry standard"],
        ["A-08", "'Walk in' may describe how the guest paid, not whether they stay at the hotel",
         "Between 06:00 and 06:59 there are 21 Walk in groups against 2 In house (91%)"],
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
        "DQ01_NO_QUEUE_DATA_THIS_DAY": "Day has no queue data recorded at all",
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
    }
    flag_count["Issue"] = flag_count["flag"].map(FLAG_EN)
    st.dataframe(
        flag_count[["Issue", "n_rows", "flag"]].rename(
            columns={"n_rows": "Rows", "flag": "Code"}),
        width='stretch', hide_index=True)

    st.markdown("""**How I Handled Data Anomalies:**

I removed only one unrecoverable row that lacked usable data. For all other anomalies, I retained the records and assigned specific Data Quality (DQ) codes. This transparent approach preserves data integrity, allows future analysts to filter records intentionally, and ensures full auditability of my work.""")

    st.markdown("""### Remaining Data Blind Spots & Business Limitations

Despite cleaning the dataset, I identified four key questions that require operational clarification:

1. **Missing Operating Days:** Why are Monday (March 16) and Thursday completely missing from the schedule?
2. **Inconsistent Data Capture:** Why was queue data omitted by floor staff on Friday, Tuesday, and Wednesday?
3. **Revenue Categorization:** Do "in-house" guests pay for breakfast separately or is it included in their room rate? Additionally, how are room-only guests classified at the entrance?
4. **Financial Accuracy:** Due to the absence of actual sales, cost, and pricing columns, all revenue numbers presented in this analysis are estimates.""")

    with st.expander("View the cleaned dataset"):
        st.dataframe(groups, width='stretch')
