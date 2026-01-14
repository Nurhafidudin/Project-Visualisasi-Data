import streamlit as st
import pandas as pd
import altair as alt


# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Indeks Harga Industri Domestik",
    layout="wide"
)


# Load & praproses data
@st.cache_data
def load_data():
    df = pd.read_csv("domestic_industrial_price_index_clean.csv")
    df["TLIST(M1)"] = df["TLIST(M1)"].astype(str)
    df["Tahun"] = df["TLIST(M1)"].str.slice(0, 4)
    df["Bulan_angka"] = df["TLIST(M1)"].str.slice(4, 6)
    df["Periode"] = df["Tahun"] + "-" + df["Bulan_angka"]

    mapping_sektor_indo = {
        "Food products (10)": "Produk makanan (10)",
        "Textiles (13)": "Tekstil (13)",
        "Wearing apparel (14)": "Pakaian jadi (14)",
        "Wood and wood products, except furniture (16)": "Kayu dan produk kayu, kecuali furnitur (16)",
        "Paper and paper products (17)": "Kertas dan produk kertas (17)",
        "Chemicals and chemical products (20)": "Bahan kimia dan produk kimia (20)",
        "Rubber and plastic products (22)": "Produk karet dan plastik (22)",
        "Other non-metallic mineral products (23)": "Produk mineral bukan logam lainnya (23)",
        "Basic metals (24)": "Logam dasar (24)",
        "Fabricated metal products, except machinery and equipment (25)":
            "Produk logam fabrikasi, kecuali mesin dan peralatannya (25)",
        "Electrical equipment (27)": "Peralatan listrik (27)",
        "Motor vehicles, trailers and semi-trailers (29)":
            "Kendaraan bermotor, trailer dan semi-trailer (29)",
        "Furniture (31)": "Furnitur (31)",
        "Mining and quarrying (05 to 09)": "Pertambangan dan penggalian (05 s.d. 09)",
    }
    df["Sektor_Indo"] = df["Industry Sector NACE Rev 2"].map(mapping_sektor_indo).fillna(
        df["Industry Sector NACE Rev 2"]
    )
    return df

df = load_data()

# Sidebar filter
st.sidebar.header("Pengaturan Filter")

semua_sektor = sorted(df["Sektor_Indo"].unique())
sektor_dipilih = st.sidebar.multiselect(
    "Pilih sektor industri",
    options=semua_sektor,
    default=semua_sektor[:5],
    help="Pilih satu atau lebih sektor untuk dianalisis."
)

st.sidebar.markdown("---")

# rentang tahun (bukan bulan)
tahun_opsi = sorted(df["Tahun"].unique())
awal_tahun, akhir_tahun = st.sidebar.select_slider(
    "Pilih rentang tahun",
    options=tahun_opsi,
    value=(tahun_opsi[0], tahun_opsi[-1])
)
st.sidebar.caption(f"Periode data: {awal_tahun} sampai {akhir_tahun}")

data_terfilter = df[
    (df["Sektor_Indo"].isin(sektor_dipilih)) &
    (df["Tahun"] >= awal_tahun) &
    (df["Tahun"] <= akhir_tahun)
].copy()


# Header & metrik
st.title("Dashboard Indeks Harga Industri Domestik")

st.markdown(
    """
Dashboard ini menampilkan **indeks harga industri domestik** yang sudah diringkas
menjadi rata-rata **tahunan** per sektor (Base 2021=100).
"""
)

if data_terfilter.empty:
    st.warning("Tidak ada data untuk kombinasi filter saat ini. Silakan ubah filter di sidebar.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Jumlah baris data", f"{len(data_terfilter):,}")
with col2:
    st.metric("Jumlah sektor terpilih", data_terfilter["Sektor_Indo"].nunique())
with col3:
    st.metric(
        "Rentang tahun",
        f"{data_terfilter['Tahun'].min()} - {data_terfilter['Tahun'].max()}"
    )


# Agregasi tahunan
# rata-rata tahunan per sektor
data_tahunan = (
    data_terfilter
    .groupby(["Tahun", "Sektor_Indo"], as_index=False)["VALUE"]
    .mean()
    .rename(columns={"VALUE": "Indeks_tahunan"})
)

# rata-rata (lintas tahun) per sektor
rata2_sektor = (
    data_tahunan.groupby("Sektor_Indo", as_index=False)["Indeks_tahunan"]
    .mean()
    .rename(columns={"Indeks_tahunan": "Rata-rata indeks tahunan"})
)


# BARIS 1: Bar sektor & Line tahunan 
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Bar Chart: Rata-rata indeks tahunan per sektor")

    chart_bar = (
        alt.Chart(rata2_sektor)
        .mark_bar()
        .encode(
            x=alt.X(
                "Sektor_Indo:N",
                title="Sektor industri",
                sort="-y",
                axis=alt.Axis(labelLimit=50)
            ),
            y=alt.Y(
                "Rata-rata indeks tahunan:Q",
                title="Rata-rata indeks tahunan"  
            ),
            color=alt.Color(
                "Sektor_Indo:N",
                title="Sektor industri",
                legend=alt.Legend(labelLimit=320)
            ),
            tooltip=[
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Rata-rata indeks tahunan", title="Rata-rata indeks", format=".2f"),
            ],
        )
        .properties(width=450, height=320)
    )
    st.altair_chart(chart_bar, use_container_width=True)

with col_b:
    st.subheader("Line Chart: Tren indeks tahunan per sektor")

    chart_line_year = (
        alt.Chart(data_tahunan)
        .mark_line(point=True)
        .encode(
            x=alt.X("Tahun:O", title="Tahun"),
            y=alt.Y(
                "Indeks_tahunan:Q",
                title="Indeks harga rata-rata tahunan (Base 2021=100)"
                
            ),
            color=alt.Color(
                "Sektor_Indo:N",
                title="Sektor industri",
                legend=alt.Legend(labelLimit=320),
            ),
            tooltip=[
                alt.Tooltip("Tahun", title="Tahun"),
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Indeks_tahunan", title="Indeks tahunan", format=".2f"),
            ],
        )
        .properties(width=450, height=320)
        .interactive()
    )
    st.altair_chart(chart_line_year, use_container_width=True)

# ====== SPASI ANTAR BARIS CHART ======
st.markdown("")
st.markdown("")
st.markdown("---")
st.markdown("")


# BARIS 2: Pie sektor & Scatter tahunan
col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Pie Chart: Proporsi rata-rata indeks tahunan per sektor")

    pie_data = rata2_sektor.copy()
    pie_data["Persentase"] = (
        pie_data["Rata-rata indeks tahunan"] / pie_data["Rata-rata indeks tahunan"].sum() * 100
    )

    pie_chart = (
        alt.Chart(pie_data)
        .mark_arc(outerRadius=150)
        .encode(
            theta=alt.Theta("Rata-rata indeks tahunan:Q", stack=True),
            color=alt.Color(
                "Sektor_Indo:N",
                title="Sektor industri",
                legend=alt.Legend(labelLimit=320)
            ),
            tooltip=[
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Rata-rata indeks tahunan", title="Rata-rata indeks", format=".2f"),
                alt.Tooltip("Persentase", title="Persentase (%)", format=".1f"),
            ],
        )
        .properties(width=1000, height=480)
    )
    st.altair_chart(pie_chart, use_container_width=True)

with col_d:
    st.subheader("Scatter Plot: Sebaran indeks tahunan per sektor")

    chart_scatter = (
        alt.Chart(data_tahunan)
        .mark_circle(size=70, opacity=0.7)
        .encode(
            x=alt.X("Tahun:O", title="Tahun"),
            y=alt.Y(
                "Indeks_tahunan:Q",
                title="Indeks harga rata-rata tahunan"
                # default zero=True, start di 0
            ),
            color=alt.Color(
                "Sektor_Indo:N",
                title="Sektor industri",
                legend=alt.Legend(labelLimit=320),
            ),
            tooltip=[
                alt.Tooltip("Tahun", title="Tahun"),
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Indeks_tahunan", title="Indeks tahunan", format=".2f"),
            ],
        )
        .properties(width=450, height=320)
        .interactive()
    )
    st.altair_chart(chart_scatter, use_container_width=True)

# ====== SPASI ANTAR BARIS CHART ======
st.markdown("")
st.markdown("")
st.markdown("---")
st.markdown("")


# BARIS 3: Stacked Bar Vertikal & Horizontal
st.subheader("Komposisi indeks tahunan per sektor dan tahun")

col_e, col_f = st.columns(2)

with col_e:
    st.markdown("**Stacked Vertical Bar Chart: per tahun dan sektor**")

    chart_stacked_vertical = (
        alt.Chart(data_tahunan)
        .mark_bar()
        .encode(
            x=alt.X("Tahun:N", title="Tahun"),
            y=alt.Y(
                "Indeks_tahunan:Q",
                title="Rata-rata indeks",
                stack="zero"     # baseline nol untuk stacked bar [web:52]
            ),
            color=alt.Color(
                "Sektor_Indo:N",
                title="Sektor industri",
                legend=alt.Legend(labelLimit=320),
            ),
            tooltip=[
                alt.Tooltip("Tahun", title="Tahun"),
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Indeks_tahunan", title="Rata-rata indeks", format=".2f"),
            ],
        )
        .properties(width=450, height=320)
    )
    st.altair_chart(chart_stacked_vertical, use_container_width=True)

with col_f:
    st.markdown("**Stacked Horizontal Bar Chart: per sektor dan tahun**")

    chart_stacked_horizontal = (
        alt.Chart(data_tahunan)
        .mark_bar()
        .encode(
            y=alt.Y(
                "Sektor_Indo:N",
                title="Sektor industri",
                axis=alt.Axis(labelLimit=200),
            ),
            x=alt.X(
                "Indeks_tahunan:Q",
                title="Rata-rata indeks",
                stack="zero"
            ),
            color=alt.Color(
                "Tahun:N",
                title="Tahun",
                legend=alt.Legend(labelLimit=120),
            ),
            tooltip=[
                alt.Tooltip("Sektor_Indo", title="Sektor industri"),
                alt.Tooltip("Tahun", title="Tahun"),
                alt.Tooltip("Indeks_tahunan", title="Rata-rata indeks", format=".2f"),
            ],
        )
        .properties(width=450, height=320)
    )
    st.altair_chart(chart_stacked_horizontal, use_container_width=True)

# Tabel data tahunan detail
st.subheader("Tabel data tahunan per sektor")

st.dataframe(
    data_tahunan.sort_values(["Tahun", "Sektor_Indo"]),
    use_container_width=True,
)
