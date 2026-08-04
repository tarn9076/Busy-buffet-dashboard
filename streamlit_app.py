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
    day_sum["queue_data"] = day_sum["day"].map(
        groups.groupby("day")["queue_data_available"].first())
    # บอกในกราฟเลยว่าวันไหนมีข้อมูลคิว จะได้ไม่ต้องอธิบายซ้ำ
    day_sum["note"] = np.where(day_sum["queue_data"],
                               "Queue data available", "No queue data")

    fig = px.bar(day_sum, x="day", y="n_pax", text="n_pax", color="note",
                 color_discrete_map={"Queue data available": "#2E9E5B",
                                     "No queue data": "#9AA0A6"},
                 title="Guests per day",
                 labels={"day": "", "n_pax": "Guests", "note": ""})
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, width='stretch')

    st.markdown("""Weekends bring about **160 guests a day**. Weekdays bring about **114**. That is 40% more. The week is not the same every day.""")


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
    st.markdown("### Answer: True — but the reason is not what staff think")

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

    st.error("""**The two charts say opposite things.** In-house guests wait **less** than walk-ins — 28 minutes against 42.5. But they leave the queue **almost twice as often** — 28.0% against 14.6%.

So the wait is not the problem. In-house guests just give up faster. They already paid for a room, so they expect a table. This is about what guests expect, not about how many tables we have.""")

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
    st.markdown("### Answer: False — for the 5 days we can check")

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
        st.markdown("""**Friday and Tuesday never reach 75%. Not for one minute.**

- Friday sits at **26.8%** on average. Half the room is empty for 5.5 hours.
- Tuesday sits at **37.9%**.
- Only Sunday touches 90%, and only for **3 minutes**.

The restaurant does get crowded. But it happens on **Saturday and Sunday, between 09:00 and 10:30**. Not every day.""")
    with c2:
        st.dataframe(
            occ_tbl.rename(columns={"day": "Day", "peak_pct": "Peak %",
                                    "avg_pct": "Avg %", "peak_time": "Peak time",
                                    "min_over75": "Min above 75%"}),
            width='stretch', hide_index=True)

    st.caption("""One limit: we only have 5 of the 7 days. We can say these 5 days are not the same. We cannot say anything about Monday or Thursday.""")

    st.divider()

    # ---------------- COMMENT 3 ----------------
    st.markdown("## Comment 3")
    st.markdown(
        "> *Walk-in customers sit the whole day. It is very difficult to find seats "
        "for in-house customers.*")
    st.markdown("### Answer: False — but staff did notice something real")

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

    st.markdown("""**The restaurant is only open for 7 hours — 06:26 to 13:30.**

- The 5-hour rule covers **71% of the whole opening time**.
- To use all 5 hours, a guest has to arrive before **08:30**. Only 40.5% of guests arrive that early.
- The longest real stay used only **75%** of the 5 hours. Only **8 guests (2.3%)** used more than half.

Sitting *the whole day* is not possible here. Nobody even came close.""")

    st.warning("""**What staff got right:** walk-ins do stay longer. **66 minutes** against **38.5 minutes** for in-house guests. That is 1.7 times longer. They also use **70% of all table time**, but they are only 57% of the groups.

Staff saw the right thing. They just made it much bigger than it is.""")

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
    st.markdown("### It fixes a problem we do not have")

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

    st.markdown("""**Cutting from 5 hours to 4 hours changes nothing.** Nobody stays that long.

The limit has to drop to **90 minutes** before anything happens. And that would push out 59 groups — 17% of all guests.""")

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

    st.markdown("""Even at 90 minutes, **Friday does not move at all**. It stays at 59.4%. Sunday only drops from 90.6% to 87.5%. That is very little, and we would lose one guest in six to get it.""")

    st.divider()

    # ---------------- ACTION 2 ----------------
    st.markdown("## Action 2 — Raise the price to 259 every day")
    st.markdown("### Too risky, and it hits the wrong days")

    st.markdown("""**First, something I cannot do.** The file has no price, sales or cost column. So I cannot measure how guests react to a price change. Instead I asked an easier question: *how many guests can we lose before we make less money?*""")

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

    st.markdown("""**Problem 1 — there is not much room for error.** On weekdays the price would jump **63%**, from 159 to 259. If more than **38.6%** of guests stop coming, we make less money. On weekends we can only lose **23.2%**.

**Problem 2 — it hits the wrong days.** The biggest jump lands on weekdays. Those are the days when only **26.8% to 40.7%** of tables are used. We would charge more when half the room is empty. And Saturday and Sunday would still be crowded.""")

    st.caption("""A note on method: weekend prices are 25% higher, and weekends are busier. This does not prove that guests ignore price. In this data, price and day of week always change together. So we cannot tell which one brought the guests in.""")

    st.divider()

    # ---------------- ACTION 3 ----------------
    st.markdown("## Action 3 — Let in-house guests skip the queue")
    st.markdown("### The idea is fine, but it cannot be used every day")

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

    st.markdown("""**Reason 1 — on 3 of the 5 days there is no queue to skip.** Friday, Tuesday and Wednesday only reach 59–78% table usage. The rule would do nothing on those days.

**Reason 2 — it moves the problem, it does not fix it.** On Sunday, 19 in-house groups waited and 35 walk-in groups waited. If all the in-house groups jump ahead, walk-ins wait about 54% longer. We still have the same number of tables.

**Reason 3 — staff cannot tell who is a hotel guest.** Someone who booked a room without breakfast, then buys the buffet at the door, is written down as *Walk in*. Staff at the door cannot see the difference.""")

    st.warning("""**Here is the evidence.** Between 06:00 and 06:59, people from outside the hotel have not arrived yet. But the data shows **21 Walk in groups and only 2 In house** — walk-ins are 91% of that hour.

So in this data, *Walk in* probably means **how the guest paid**. It does not mean **the guest is not staying at the hotel**.""")


# ==========================================================================
# TAB 3 : Task 3
# ==========================================================================
with tab3:
    st.header("Task 3 — What I would do instead")

    st.markdown("""### Keep Action 3, but only turn it on when it is needed

Of the three actions, this is the only one that matches a real problem in the data. In-house guests leave the queue 28% of the time, even though they wait less than walk-ins. The other two actions try to fix problems the data does not find.""")

    st.markdown("### First, the idea I dropped")

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

    st.error("""**My first idea was to turn the rule on at 80% table usage. The data proved me wrong.**

At 09:00 on Sunday, 15 groups are waiting. But table usage shows 71.9%, so the rule stays **off**. At 11:30 usage shows 81.2% and the rule turns **on**, but only 1 group is still waiting.

The reason is simple. A table that looks empty is not ready yet. Someone still has to clear it, wipe it and set it again.""")

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

    st.markdown("""**Why 5 and not another number.** I did not use the walk-away rate to pick it. Only 25 in-house groups ever waited, and 7 of them left. That is too small to trust. So I used the waiting time instead. It is steadier and it goes up smoothly. When the queue reaches 5 groups, the wait doubles from 11.5 to 22 minutes.

**Why this works for the staff**
- They can count queue cards by eye. No system and no maths.
- It would turn on for 33 minutes on Saturday and 173 minutes on Sunday. The other three days need nothing.
- It matches what guests see. Nobody can see a table usage percentage.""")

    st.divider()
    st.markdown("## Plan B — keep 6 tables free for hotel guests during the rush")

    c1, c2, c3 = st.columns(3)
    c1.metric("Tables to keep free", "6 tables", delta="18.8% of 32", delta_color="off")
    c2.metric("What hotel guests really used", "6 tables",
              delta="same on Sat and Sun", delta_color="off")
    c3.metric("Still free for walk-ins", "26 tables", delta="they never used more than 23",
              delta_color="off")

    st.markdown("""**When to use Plan B instead.** If room-only guests really are written down as *Walk in*, then Plan A cannot work. Staff would have no way to know who is a hotel guest. Those guests would go to the back of the queue, and then complain at the front desk.

Plan B avoids this. Nobody has to decide who is who at the door.

**Why 6 tables.** That is the most tables in-house guests actually used between 08:30 and 11:00. It was 6 on Saturday and 6 on Sunday. That still leaves 26 tables for walk-ins, and they never used more than 23.""")

    st.divider()
    st.markdown("""### One warning before this starts

Every number here comes from **2 days of queue data and 73 groups**. It is the best starting point this data can give. It is not a final answer.

**What I would do:** try it for two weeks. Record queue data every day this time. Then set the number again properly. To check if it worked, compare against what we have now — 28% of in-house guests leaving the queue.""")


# ==========================================================================
# TAB 4 : Assumptions & Data Quality
# ==========================================================================
with tab4:
    st.header("Assumptions & Data Quality")

    st.markdown("""I sent four questions about this data on 28 July 2026. I did not get an answer before I had to finish. So I made the assumptions below instead of waiting. They are all listed here, with the evidence for each one.""")

    st.markdown("### Assumptions")
    assumptions = pd.DataFrame([
        ["A-01", "Sheet names are day + month, so the data is 13–18 March 2026",
         "The 2026 calendar matches the Sat–Sun peak, and the last digit of each sheet name is the month"],
        ["A-02", "Short table numbers follow a rule based on party size: 3 or more guests means the whole table",
         "I tested three readings. This one produced fewer impossible overlaps than 'always whole table' (26 vs 37 pairs)"],
        ["A-03", "Table 16 is a real table missing from the floor plan",
         "It appears 24 times, 4–5 times every single day. A typo would not repeat that evenly"],
        ["A-04", "Tables 15A and 15B are accepted as 2 seats each",
         "Only 5 rows (1.4%). I chose the reading that does not inflate total capacity"],
        ["A-05", "Total capacity is 32 tables and 74 seats",
         "Floor plan from the appendix, plus table 16 and 15A/15B from A-03 and A-04"],
        ["A-06", "The 3 days without queue data were not recorded, rather than having no queue",
         "Those days peaked at 59–78% table usage. Nobody waiting at all is not believable"],
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

    st.markdown("""**How I handled them.** I deleted only one row — the one with no usable data. Everything else stayed in and got a code. That way any analysis can keep it or drop it on purpose, and anyone can check what I did.""")

    st.markdown("""### What this data still cannot answer

1. Why Monday 16 March is missing, and why there is no Thursday.
2. Why nobody recorded queue data on Friday, Tuesday and Wednesday.
3. Whether in-house guests pay for breakfast separately or as part of the room rate, and how room-only guests are written down.
4. There is no price or sales data, so any money number here is only an estimate.""")

    with st.expander("View the cleaned dataset"):
        st.dataframe(groups, width='stretch')
