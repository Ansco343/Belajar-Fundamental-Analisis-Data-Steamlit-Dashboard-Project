from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dashboard Bike Sharing", page_icon="🚲", layout="wide")
sns.set_theme(style="whitegrid")

BASE_DIR = Path(__file__).parent

URUTAN_WAKTU = ["Pagi (05-10)", "Siang (11-15)", "Sore (16-19)", "Malam (20-04)"]
URUTAN_SUHU = ["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-30°C)", "Panas (≥30°C)"]
URUTAN_CUACA = ["Cerah", "Berkabut/Mendung", "Hujan/Salju Ringan"]
URUTAN_MUSIM = ["Spring", "Summer", "Fall", "Winter"]
URUTAN_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
LABEL_LEVEL = ["Rendah (<3.000)", "Sedang (3.000-5.999)", "Tinggi (≥6.000)"]
WARNA_HARI = {"Hari Kerja": "#1f77b4", "Akhir Pekan/Libur": "#ff7f0e"}


@st.cache_data
def muat_data():
    hour = pd.read_csv(BASE_DIR / "main_data.csv", parse_dates=["dteday"])
    day = pd.read_csv(BASE_DIR / "main_data_day.csv", parse_dates=["dteday"])
    day["level_permintaan"] = pd.cut(
        day["cnt"], bins=[0, 3000, 6000, np.inf], labels=LABEL_LEVEL, right=False
    ).astype(str)
    return hour, day


def angka(x):
    return f"{x:,.0f}".replace(",", ".")


hour_all, day_all = muat_data()

# ------------------------------------------------------------------ sidebar
st.sidebar.title("🚲 Filter Data")
tgl_min, tgl_max = day_all["dteday"].min().date(), day_all["dteday"].max().date()
rentang = st.sidebar.date_input(
    "Rentang tanggal", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max
)
musim_pilihan = st.sidebar.multiselect("Musim", URUTAN_MUSIM, default=URUTAN_MUSIM)
st.sidebar.caption("Sumber data: Capital Bikeshare, Washington D.C. (2011-2012).")

if not (isinstance(rentang, (list, tuple)) and len(rentang) == 2):
    st.info("Pilih tanggal awal dan tanggal akhir pada filter di sebelah kiri.")
    st.stop()
if not musim_pilihan:
    st.info("Pilih minimal satu musim pada filter di sebelah kiri.")
    st.stop()

awal, akhir = pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1])


def saring(df):
    return df[df["dteday"].between(awal, akhir) & df["musim"].isin(musim_pilihan)]


hour_df, day_df = saring(hour_all), saring(day_all)
if day_df.empty:
    st.warning("Tidak ada data pada filter yang dipilih.")
    st.stop()

# ------------------------------------------------------------------ header
st.title("🚲 Dashboard Analisis Bike Sharing")
st.caption("Capital Bikeshare, Washington D.C. | Pola penyewaan menurut jam, cuaca, dan suhu")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", angka(day_df["cnt"].sum()))
k2.metric("Rata-rata per hari", angka(day_df["cnt"].mean()))
k3.metric("Pengguna registered", f"{day_df['registered'].sum() / day_df['cnt'].sum() * 100:.1f}%")
k4.metric("Jumlah hari", angka(len(day_df)))

tab1, tab2, tab3 = st.tabs(["Pertanyaan 1: Pola Jam", "Pertanyaan 2: Cuaca & Suhu", "Analisis Lanjutan"])

# ------------------------------------------------------------------ tab 1
with tab1:
    st.subheader("Jam puncak dan selisih penyewaan: hari kerja vs akhir pekan/libur")
    pola_jam = hour_df.groupby(["hr", "jenis_hari"])["cnt"].mean().reset_index()
    pola_waktu = hour_df.groupby(["kelompok_waktu", "jenis_hari"])["cnt"].mean().reset_index()

    kolom_a, kolom_b = st.columns([1.35, 1])
    with kolom_a:
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=pola_jam, x="hr", y="cnt", hue="jenis_hari", palette=WARNA_HARI,
                     marker="o", linewidth=2.2, ax=ax)
        ax.set_title("Rata-rata penyewaan per jam menurut jenis hari", fontweight="bold")
        ax.set_xlabel("Jam dalam sehari")
        ax.set_ylabel("Rata-rata penyewaan per jam")
        ax.set_xticks(range(0, 24, 2))
        ax.set_ylim(0, None)
        ax.legend(title="Jenis hari", loc="upper left")
        sns.despine()
        st.pyplot(fig)
        plt.close(fig)
    with kolom_b:
        fig, ax = plt.subplots(figsize=(7, 5))
        sns.barplot(data=pola_waktu, x="kelompok_waktu", y="cnt", hue="jenis_hari",
                    order=URUTAN_WAKTU, palette=WARNA_HARI, ax=ax)
        for wadah in ax.containers:
            ax.bar_label(wadah, fmt="%.0f", padding=2, fontsize=9)
        ax.set_title("Rata-rata penyewaan per jam menurut kelompok waktu", fontweight="bold", fontsize=11)
        ax.set_xlabel("Kelompok waktu")
        ax.set_ylabel("Rata-rata penyewaan per jam")
        ax.set_ylim(0, pola_waktu["cnt"].max() * 1.4)
        ax.legend(title="Jenis hari", loc="upper right")
        ax.tick_params(axis="x", labelsize=8)
        sns.despine()
        st.pyplot(fig)
        plt.close(fig)

    # ringkasan dinamis
    puncak = pola_jam.loc[pola_jam.groupby("jenis_hari")["cnt"].idxmax()].set_index("jenis_hari")
    teks = [f"- Puncak **{j}**: pukul **{int(r['hr']):02d}.00** (rata-rata {r['cnt']:.0f} sewa/jam)"
            for j, r in puncak.iterrows()]
    st.markdown("\n".join(teks))

    tabel = pola_waktu.pivot(index="kelompok_waktu", columns="jenis_hari", values="cnt").reindex(URUTAN_WAKTU)
    if {"Hari Kerja", "Akhir Pekan/Libur"} <= set(tabel.columns):
        tabel["Selisih (Hari Kerja - Akhir Pekan/Libur)"] = tabel["Hari Kerja"] - tabel["Akhir Pekan/Libur"]
    st.markdown("**Rata-rata penyewaan per jam dan selisihnya per kelompok waktu**")
    st.dataframe(tabel.round(1))

# ------------------------------------------------------------------ tab 2
with tab2:
    st.subheader("Dampak cuaca buruk dan kategori suhu terhadap penyewaan harian")
    kolom_c, kolom_d = st.columns(2)

    cuaca = day_df.groupby("cuaca")["cnt"].agg(["mean", "count"]).reindex(URUTAN_CUACA).dropna()
    suhu = day_df.groupby("kategori_suhu")["cnt"].agg(["mean", "count"]).reindex(URUTAN_SUHU).dropna()

    with kolom_c:
        fig, ax = plt.subplots(figsize=(7.5, 5))
        warna = {"Cerah": "#4c78a8", "Berkabut/Mendung": "#a0a7b0", "Hujan/Salju Ringan": "#e45756"}
        batang = ax.bar([f"{c}\n(n = {int(n)} hari)" for c, n in zip(cuaca.index, cuaca["count"])],
                        cuaca["mean"], color=[warna[c] for c in cuaca.index])
        ax.bar_label(batang, fmt="%.0f", padding=3)
        ax.set_title("Rata-rata penyewaan harian menurut cuaca", fontweight="bold")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.set_xlabel("Kondisi cuaca")
        ax.set_ylim(0, cuaca["mean"].max() * 1.15)
        ax.grid(axis="x", visible=False)
        sns.despine()
        st.pyplot(fig)
        plt.close(fig)
    with kolom_d:
        fig, ax = plt.subplots(figsize=(7.5, 5))
        warna_suhu = ["#2ca02c" if v == suhu["mean"].max() else "#a0a7b0" for v in suhu["mean"]]
        batang = ax.bar([f"{s}\n(n = {int(n)} hari)" for s, n in zip(suhu.index, suhu["count"])],
                        suhu["mean"], color=warna_suhu)
        ax.bar_label(batang, fmt="%.0f", padding=3)
        ax.set_title("Rata-rata penyewaan harian menurut kategori suhu", fontweight="bold")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.set_xlabel("Kategori suhu (hijau = tertinggi)")
        ax.set_ylim(0, suhu["mean"].max() * 1.15)
        ax.grid(axis="x", visible=False)
        sns.despine()
        st.pyplot(fig)
        plt.close(fig)

    if {"Cerah", "Hujan/Salju Ringan"} <= set(cuaca.index):
        turun = (1 - cuaca.loc["Hujan/Salju Ringan", "mean"] / cuaca.loc["Cerah", "mean"]) * 100
        st.markdown(f"- Rata-rata penyewaan saat **Hujan/Salju Ringan** turun **{turun:.1f}%** dibanding cuaca **Cerah**.")
    if "Berkabut/Mendung" in cuaca.index and "Cerah" in cuaca.index:
        turun2 = (1 - cuaca.loc["Berkabut/Mendung", "mean"] / cuaca.loc["Cerah", "mean"]) * 100
        st.markdown(f"- Saat **Berkabut/Mendung**, penurunan dibanding cuaca Cerah sebesar **{turun2:.1f}%**.")
    if not suhu.empty:
        st.markdown(f"- Penyewaan harian tertinggi ada pada kategori suhu **{suhu['mean'].idxmax()}** "
                    f"(rata-rata {suhu['mean'].max():.0f} per hari).")
    st.caption("Catatan: jumlah hari pada tiap kategori ditampilkan di label sumbu. Kategori dengan sedikit hari "
               "(misalnya hujan/salju ringan) perlu ditafsirkan hati-hati.")

# ------------------------------------------------------------------ tab 3
with tab3:
    st.subheader("Analisis lanjutan: binning dan manual grouping")

    st.markdown("**1. Proporsi level permintaan harian per musim** (binning jumlah sewa harian)")
    proporsi = (pd.crosstab(day_df["musim"], day_df["level_permintaan"], normalize="index") * 100)
    proporsi = proporsi.reindex(index=[m for m in URUTAN_MUSIM if m in proporsi.index],
                                columns=[l for l in LABEL_LEVEL if l in proporsi.columns])
    fig, ax = plt.subplots(figsize=(8, 3.8))
    sns.heatmap(proporsi, annot=True, fmt=".1f", cmap="Blues", cbar_kws={"label": "% hari dalam musim"}, ax=ax)
    ax.set_xlabel("Level permintaan")
    ax.set_ylabel("Musim")
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("**2. Rata-rata penyewaan per jam menurut hari dalam seminggu**")
    heat = hour_df.pivot_table(index="hari", columns="hr", values="cnt", aggfunc="mean")
    heat = heat.reindex([h for h in URUTAN_HARI if h in heat.index])
    fig, ax = plt.subplots(figsize=(13, 4))
    sns.heatmap(heat, cmap="YlOrRd", cbar_kws={"label": "Rata-rata penyewaan per jam"}, ax=ax)
    ax.set_xlabel("Jam dalam sehari")
    ax.set_ylabel("Hari")
    ax.tick_params(axis="y", rotation=0)
    st.pyplot(fig)
    plt.close(fig)

    st.markdown("**3. Proporsi pengguna casual per kelompok waktu dan jenis hari**")
    komposisi = hour_df.groupby(["jenis_hari", "kelompok_waktu"])[["casual", "registered"]].sum()
    komposisi["persen_casual"] = komposisi["casual"] / (komposisi["casual"] + komposisi["registered"]) * 100
    komposisi = komposisi.reset_index()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.barplot(data=komposisi, x="kelompok_waktu", y="persen_casual", hue="jenis_hari",
                order=URUTAN_WAKTU, palette=WARNA_HARI, ax=ax)
    for wadah in ax.containers:
        ax.bar_label(wadah, fmt="%.1f%%", padding=2, fontsize=9)
    ax.set_xlabel("Kelompok waktu")
    ax.set_ylabel("Persentase pengguna casual")
    ax.set_ylim(0, max(45, komposisi["persen_casual"].max() * 1.2))
    ax.legend(title="Jenis hari")
    sns.despine()
    st.pyplot(fig)
    plt.close(fig)

st.divider()
st.caption("Proyek Analisis Data - Bike Sharing Dataset (Fanaee-T & Gama, 2013).")
