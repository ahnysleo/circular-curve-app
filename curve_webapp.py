import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Circular Curve Calculator", layout="wide")

st.title("🛣 Circular Curve Calculator")

# ===== 1. 사용자 입력 =====
col1, col2, col3 = st.columns(3)
with col1:
    I_deg = st.number_input("Intersection Angle I (degrees)", 0.0, 180.0, 40.0, step=0.5)
with col2:
    Da_deg = st.number_input("Degree of Curve Dₐ (degrees)", 0.0, 100.0, 8.0, step=0.1)
with col3:
    PI_station_str = st.text_input("PI Station (e.g., 10+00.00)", "10+00.00")

stake_step = st.slider("Stake Interval (ft)", 25, 100, 50, step=25)

# ===== 유틸 함수 =====
def station_to_ft(sta: str) -> float:
    s = sta.replace('+', '')
    return float(s)

def ft_to_station(x: float) -> str:
    i = int(x // 100)
    r = x - i*100
    return f"{i}+{r:05.2f}"

def deg_to_dms_nearest_sec(deg: float) -> str:
    tot = int(round(deg * 3600))
    d, rem = divmod(tot, 3600)
    m, s = divmod(rem, 60)
    if s == 60:
        s = 0; m += 1
    if m >= 60:
        m -= 60; d += 1
    return f"{d:02d}°{m:02d}′{s:02d}″"

# ===== 2. 기본 요소 계산 =====
if Da_deg > 0 and I_deg > 0:
    PI_ft = station_to_ft(PI_station_str)
    R = 18000.0 / (math.pi * Da_deg)
    T = R * math.tan(math.radians(I_deg/2))
    L = 100.0 * I_deg / Da_deg
    PC_station = PI_ft - T
    PT_station = PC_station + L

    # ===== 3. Stake stations =====
    stations = [PC_station]
    first_full_50 = math.ceil((PC_station + stake_step) / stake_step) * stake_step
    s = first_full_50
    while s < PT_station - 1e-6:
        stations.append(s)
        s += stake_step
    stations.append(PT_station)

    # ===== 4. Deflection & Chord Table =====
    deflection_deg = []
    for stn in stations:
        arc_from_PC = stn - PC_station
        delta = Da_deg * arc_from_PC / 200.0
        deflection_deg.append(delta)

    tape_ct = [0.00]
    edm_ct  = [0.00]
    for i in range(1, len(stations)):
        d_inc = deflection_deg[i] - deflection_deg[i-1]
        chord_inc = 2*R*math.sin(math.radians(d_inc))
        chord_cum = 2*R*math.sin(math.radians(deflection_deg[i]))
        tape_ct.append(round(chord_inc, 2))
        edm_ct.append(round(chord_cum,  2))

    points = (["P.C."] + [str(i) for i in range(1, len(stations)-1)] + ["P.T."])
    df = pd.DataFrame({
        "Point": points,
        "Station": [ft_to_station(x) for x in stations],
        "Defl. Angle": [deg_to_dms_nearest_sec(d) for d in deflection_deg],
        "Tape Ct (ft)": tape_ct,
        "EDM Ct (ft)": edm_ct
    })

    # ===== 5. 좌표 계산 (Curve to RIGHT) =====
    x_points = []
    y_points = []
    for d in deflection_deg:
        angle_rad = math.radians(2*d)
        x = R * math.sin(angle_rad)
        y = -R * (1 - math.cos(angle_rad))   # curve to right
        x_points.append(x)
        y_points.append(y)

    # ===== 6. PI 좌표 계산 =====
    PT_x = x_points[-1]
    PT_y = y_points[-1]
    theta_PT_tan = math.radians(180 - I_deg)
    m2 = math.tan(theta_PT_tan)
    x_PI = PT_x - PT_y/m2
    y_PI = 0

    # ===== 7. 출력 =====
    st.subheader("📐 Curve Elements")
    colA, colB = st.columns(2)
    with colA:
        st.write(f"- **R** = {R:.3f} ft")
        st.write(f"- **T** = {T:.3f} ft")
        st.write(f"- **L** = {L:.3f} ft")
    with colB:
        st.write(f"- Sta. **P.C.** = {ft_to_station(PC_station)}")
        st.write(f"- Sta. **P.T.** = {ft_to_station(PT_station)}")
        st.write(f"- Sta. **P.I.** = {PI_station_str}")

    st.subheader("📋 Deflection & Chord Table")
    st.dataframe(df, use_container_width=True)

    # ===== 8. 그래프 =====
    st.subheader("📈 Curve Layout")
    fig, ax = plt.subplots(figsize=(8,6))
    ax.plot(x_points, y_points, 'o-', label='Curve')
    ax.scatter(x_points[0], y_points[0], color='red', label='P.C.')
    ax.scatter(x_points[-1], y_points[-1], color='green', label='P.T.')

    # Tangents
    ax.plot([x_points[0], x_PI], [y_points[0], y_PI], 'k--', label='Back Tangent')
    ax.plot([PT_x, x_PI], [PT_y, y_PI], 'k--', label='Forward Tangent')

    # PI 표시
    ax.scatter([x_PI], [y_PI], color='blue', label='P.I.')
    ax.text(x_PI+5, y_PI+5, "P.I.", fontsize=9, color='blue')

    # 포인트 라벨
    for i, txt in enumerate(points):
        ax.annotate(txt, (x_points[i], y_points[i]), textcoords="offset points", xytext=(5,5), fontsize=8)

    ax.set_aspect('equal')
    ax.set_title('Simple Circular Curve Layout (Right Curve with P.I.)')
    ax.set_xlabel('X (ft)')
    ax.set_ylabel('Y (ft)')
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

else:
    st.warning("Input I and Dₐ.")
