import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.elevator_sim import SimParams, run_simulation


st.set_page_config(page_title="Akıllı Asansör Simülasyonu", layout="wide")

st.title("Akıllı Asansör Trafiği Simülasyonu (Vize Sürümü)")
st.caption("Streamlit arayüzü + SimPy ayrık olay simülasyonu. Bugün: temel model + rapor metrikleri. Final: gelişmiş kontrol stratejileri.")


with st.sidebar:
    st.header("Parametreler")

    seed = st.number_input("Seed", min_value=0, max_value=10_000_000, value=42, step=1)
    sim_minutes = st.slider("Simülasyon süresi (dakika)", min_value=5, max_value=240, value=60, step=5)

    floors = st.slider("Kat sayısı", min_value=3, max_value=40, value=10, step=1)
    elevators = st.slider("Asansör sayısı", min_value=1, max_value=4, value=1, step=1)
    capacity = st.slider("Asansör kapasitesi (kişi)", min_value=2, max_value=20, value=8, step=1)

    st.subheader("Trafik")
    mean_interarrival_seconds = st.slider("Ortalama geliş aralığı (sn)", min_value=1.0, max_value=60.0, value=8.0, step=1.0)
    traffic_mode = st.selectbox("Trafik modu", ["mixed", "up_peak", "down_peak"], index=0)

    # Vize sürümünde sabit (UI'dan kaldırıldı). Finalde tekrar açılabilir.
    seconds_per_floor = 3.0
    door_seconds = 6.0
    board_s = 1.0
    alight_s = 1.0
    snapshot_every_seconds = 10

    run = st.button("Simülasyonu çalıştır", type="primary")


def make_heatmap(df_snap: pd.DataFrame, floors_n: int, bin_seconds: int = 60) -> go.Figure:
    if df_snap.empty:
        return go.Figure()

    df = df_snap.copy()
    df["t_bin"] = (df["t"] // bin_seconds).astype(int)

    long_rows = []
    for f in range(floors_n):
        col = f"q_{f}"
        if col in df.columns:
            tmp = df[["t_bin", col]].rename(columns={col: "q"})
            tmp["floor"] = f
            long_rows.append(tmp)
    if not long_rows:
        return go.Figure()

    long_df = pd.concat(long_rows, ignore_index=True)
    agg = long_df.groupby(["floor", "t_bin"], as_index=False)["q"].mean()
    pivot = agg.pivot(index="floor", columns="t_bin", values="q").fillna(0.0)

    fig = px.imshow(
        pivot.values,
        labels={"x": f"Zaman dilimi (x{bin_seconds}sn)", "y": "Kat", "color": "Ortalama kuyruk"},
        x=pivot.columns.astype(int),
        y=pivot.index.astype(int),
        aspect="auto",
        color_continuous_scale="Turbo",
    )
    fig.update_layout(margin=dict(l=30, r=10, t=30, b=30))
    return fig


if run:
    params = SimParams(
        seed=int(seed),
        sim_minutes=int(sim_minutes),
        floors=int(floors),
        elevators=int(elevators),
        elevator_capacity=int(capacity),
        seconds_per_floor=float(seconds_per_floor),
        door_seconds=float(door_seconds),
        board_seconds_per_person=float(board_s),
        alight_seconds_per_person=float(alight_s),
        mean_interarrival_seconds=float(mean_interarrival_seconds),
        traffic_mode=traffic_mode,  # type: ignore[arg-type]
        snapshot_every_seconds=int(snapshot_every_seconds),
    )

    with st.spinner("Simülasyon çalışıyor..."):
        out = run_simulation(params)

    metrics = out["metrics"]
    df_snap: pd.DataFrame = out["snapshots"]
    df_pax: pd.DataFrame = out["passengers"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Üretilen yolcu", f"{int(metrics['generated_passengers'])}")
    c2.metric("Servis edilen yolcu", f"{int(metrics['served_passengers'])}")
    c3.metric("Ortalama bekleme (sn)", f"{metrics.get('wait_mean_s', np.nan):.1f}")
    c4.metric("P90 bekleme (sn)", f"{metrics.get('wait_p90_s', np.nan):.1f}")

    st.divider()

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Toplam kuyruk (zaman serisi)")
        if not df_snap.empty:
            fig = px.line(df_snap, x="t", y="total_queue", labels={"t": "Zaman (sn)", "total_queue": "Toplam kuyruk"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Snapshot verisi yok.")

        st.subheader("Bekleme süresi dağılımı")
        if not df_pax.empty and "wait_s" in df_pax.columns:
            fig2 = px.histogram(df_pax, x="wait_s", nbins=40, labels={"wait_s": "Bekleme (sn)"})
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Henüz servis edilen yolcu yok.")

    with right:
        st.subheader("Kat bazlı yoğunluk ısı haritası")
        if not df_snap.empty:
            st.plotly_chart(make_heatmap(df_snap, floors_n=int(floors), bin_seconds=60), use_container_width=True)
        else:
            st.info("Snapshot verisi yok.")

        st.subheader("Ham çıktılar")
        with st.expander("Metrikler (JSON)"):
            st.json(metrics)
        with st.expander("Yolcular tablosu (ilk 200)"):
            st.dataframe(df_pax.head(200), use_container_width=True)
        with st.expander("Snapshot tablosu (ilk 200)"):
            st.dataframe(df_snap.head(200), use_container_width=True)

else:
    st.info("Parametreleri seçip **Simülasyonu çalıştır** butonuna bas.")

