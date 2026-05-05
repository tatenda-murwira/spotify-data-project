"""
Spotify Listening Intelligence Dashboard
Clean, Professional Edition
"""

import glob
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Spotify Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)
import pandas as pd

@st.cache_data
def load_data():
    url = st.secrets["data_url"]  # Google Drive direct download link
    return pd.read_csv(url)

# ── Color Palette ────────────────────────────────────────────────────────────
P = {
    "bg": "#ffffff",
    "surface": "#f8f9fa",
    "border": "#e9ecef",
    "primary": "#8b5cf6",
    "secondary": "#ec4899",
    "text": "#212529",
    "muted": "#6c757d",
    "success": "#10b981",
    "danger": "#ef4444",
}

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color=P["text"]),
    margin=dict(t=40, b=20, l=20, r=20),
)

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,500,1,0&display=swap');

* {{ font-family: 'Inter', sans-serif !important; }}

.ms {{
    font-family: 'Material Symbols Rounded' !important;
    font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
    line-height: 1;
    display: inline-flex;
    vertical-align: -0.15em;
    user-select: none;
}}

.page-title {{
    font-size: 2.1rem;
    font-weight: 800;
    color: {P["text"]};
    letter-spacing: -0.02em;
    margin: 0;
}}

.page-meta {{
    font-size: 0.95rem;
    color: {P["muted"]};
    margin-top: 6px;
}}

.sidebar-brand {{
    text-align: center;
    padding: 18px 0 8px 0;
}}

.sidebar-brand-title {{
    font-size: 1.65rem;
    font-weight: 800;
    color: {P["primary"]};
}}

.sidebar-brand-subtitle {{
    font-size: 0.9rem;
    color: {P["muted"]};
    margin-top: 4px;
}}

.sidebar-section-title {{
    font-size: 0.95rem;
    font-weight: 700;
    color: {P["text"]};
    margin: 8px 0 10px 0;
}}

.stApp {{ background: {P["bg"]}; }}

section[data-testid="stSidebar"] {{
    background: {P["surface"]} !important;
    border-right: 1px solid {P["border"]};
}}

.stTabs [data-baseweb="tab-list"] {{
    background: transparent;
    border-bottom: 2px solid {P["border"]};
    gap: 24px;
}}

.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {P["muted"]} !important;
    font-weight: 600;
    font-size: 0.95rem;
    padding-bottom: 12px;
    border-bottom: 2px solid transparent;
}}

.stTabs [aria-selected="true"] {{
    color: {P["primary"]} !important;
    border-bottom: 2px solid {P["primary"]} !important;
}}

div[data-testid="metric-container"] {{
    background: white;
    border: 1px solid {P["border"]};
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}}

div[data-testid="metric-container"]:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}

.metric-card {{
    background: white;
    border: 1px solid {P["border"]};
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}}

.section-title {{
    font-size: 1.25rem;
    font-weight: 700;
    color: {P["text"]};
    margin-bottom: 20px;
}}

.rank-item {{
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px;
    border-radius: 8px;
    background: white;
    border: 1px solid {P["border"]};
    margin-bottom: 12px;
    transition: all 0.2s;
}}

.rank-item:hover {{
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateX(4px);
}}

.rank-num {{
    font-weight: 700;
    color: {P["muted"]};
    min-width: 30px;
}}

.rank-name {{
    font-weight: 600;
    color: {P["text"]};
    flex: 1;
}}

.rank-value {{
    font-weight: 600;
    color: {P["primary"]};
}}
</style>
""", unsafe_allow_html=True)


def ms_icon(name: str, *, size_px: int = 20, color: str | None = None) -> str:
    color = color or P["muted"]
    return f"<span class='ms' style='font-size:{size_px}px;color:{color};'>{name}</span>"


def section_title(title: str, icon_name: str | None = None) -> None:
    icon = f"{ms_icon(icon_name, size_px=20, color=P['primary'])} " if icon_name else ""
    st.markdown(f"<div class='section-title'>{icon}{title}</div>", unsafe_allow_html=True)


# ── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    root = Path(__file__).parent
    csv_path = root / "clean_spotify_history.csv"
    
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df["played_at"] = pd.to_datetime(df["played_at"], errors="coerce", utc=True).dt.tz_convert("Africa/Harare")
    else:
        files = glob.glob(str(root / "Streaming_History_*.json"))
        if not files:
            raise FileNotFoundError("No Spotify history files found.")
        
        raw = pd.concat([pd.read_json(f) for f in files], ignore_index=True)
        raw["played_at"] = pd.to_datetime(raw["ts"], errors="coerce", utc=True).dt.tz_convert("Africa/Harare")
        raw["minutes_played"] = raw["ms_played"] / 60000
        raw = raw.rename(columns={
            "master_metadata_album_artist_name": "artist_name",
            "master_metadata_track_name": "track_name"
        })
        df = raw[["played_at", "artist_name", "track_name", "minutes_played", "ms_played"]].copy()

    df = df.dropna(subset=["played_at", "artist_name", "track_name"]).copy()
    df["minutes_played"] = pd.to_numeric(df["minutes_played"], errors="coerce")
    df["ms_played"] = pd.to_numeric(df["ms_played"], errors="coerce")
    df = df.dropna(subset=["minutes_played", "ms_played"]).sort_values("played_at")
    
    df["year"] = df["played_at"].dt.year
    df["month_num"] = df["played_at"].dt.month
    df["month"] = df["played_at"].dt.strftime("%Y-%m")
    df["date"] = df["played_at"].dt.date
    df["hour"] = df["played_at"].dt.hour
    df["day_of_week"] = df["played_at"].dt.day_name()
    df["is_skip"] = df["ms_played"] < 30000
    df["play"] = 1
    
    return df


# ── Load Data ────────────────────────────────────────────────────────────────
with st.spinner("Loading data..."):
    df = load_data()

min_date = df["played_at"].min().date()
max_date = df["played_at"].max().date()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"""
        <div class='sidebar-brand'>
            <div class='sidebar-brand-title'>{ms_icon('headphones', size_px=26, color=P['primary'])} Spotify</div>
            <div class='sidebar-brand-subtitle'>Listening Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("---")
    
    st.markdown(
        f"<div class='sidebar-section-title'>{ms_icon('tune', size_px=18, color=P['text'])} Filters</div>",
        unsafe_allow_html=True,
    )
    
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    year_options = sorted(df["year"].unique().tolist(), reverse=True)
    selected_years = st.multiselect(
        "Select Years",
        options=year_options,
        default=year_options
    )


# ── Filter Data ──────────────────────────────────────────────────────────────
s_date, e_date = date_range if len(date_range) == 2 else (min_date, max_date)
filt = df[
    (df["date"] >= s_date) & 
    (df["date"] <= e_date) & 
    (df["year"].isin(selected_years))
].copy()

if filt.empty:
    st.warning("No data found for the selected filters. Please adjust your selection.")
    st.stop()


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class='page-title'>{ms_icon('headphones', size_px=32, color=P['primary'])} Your Listening Universe</div>
    <div class='page-meta'><b>{s_date.strftime('%b %d, %Y')} - {e_date.strftime('%b %d, %Y')}</b> | {len(filt):,} plays</div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")


# ── Key Metrics ──────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_hours = filt["minutes_played"].sum() / 60
total_plays = filt["play"].sum()
unique_artists = filt["artist_name"].nunique()
unique_tracks = filt["track_name"].nunique()
skip_rate = filt["is_skip"].mean() * 100

col1.metric("Total Hours", f"{total_hours:,.0f}")
col2.metric("Total Plays", f"{total_plays:,}")
col3.metric("Unique Artists", f"{unique_artists:,}")
col4.metric("Unique Tracks", f"{unique_tracks:,}")
col5.metric("Skip Rate", f"{skip_rate:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)


# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Trends", "Top Artists & Tracks", "Search", "2026 Wrapped"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        section_title("Listening by Day of Week", "calendar_today")
        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_data = filt.groupby("day_of_week")["minutes_played"].sum().reindex(days_order).reset_index()
        
        fig_days = px.bar(
            day_data,
            x="day_of_week",
            y="minutes_played",
            color_discrete_sequence=[P["primary"]]
        )
        fig_days.update_layout(**CHART_LAYOUT, xaxis_title=None, yaxis_title="Minutes", height=350)
        st.plotly_chart(fig_days, use_container_width=True)
    
    with col2:
        section_title("Listening by Hour", "schedule")
        hour_data = filt.groupby("hour")["minutes_played"].sum().reset_index()
        
        fig_hours = px.line(
            hour_data,
            x="hour",
            y="minutes_played",
            markers=True,
            color_discrete_sequence=[P["secondary"]]
        )
        fig_hours.update_layout(**CHART_LAYOUT, xaxis_title="Hour of Day", yaxis_title="Minutes", height=350)
        st.plotly_chart(fig_hours, use_container_width=True)
    
    section_title("Listening Heatmap", "grid_view")
    heat_data = filt.groupby(["day_of_week", "hour"])["minutes_played"].sum().reset_index()
    heat_data["day_of_week"] = pd.Categorical(heat_data["day_of_week"], categories=days_order, ordered=True)
    heat_pivot = heat_data.pivot(index="day_of_week", columns="hour", values="minutes_played").fillna(0)
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns,
        y=heat_pivot.index,
        colorscale=[[0, "#f8f9fa"], [0.5, P["primary"]], [1.0, P["secondary"]]]
    ))
    fig_heat.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig_heat, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: TRENDS
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    section_title("Monthly Listening Trend", "show_chart")
    monthly = filt.groupby("month")["minutes_played"].sum().reset_index()
    
    fig_monthly = px.area(
        monthly,
        x="month",
        y="minutes_played",
        markers=True,
        color_discrete_sequence=[P["primary"]]
    )
    fig_monthly.update_traces(fillcolor=f"rgba(139, 92, 246, 0.2)", line=dict(width=3))
    fig_monthly.update_layout(**CHART_LAYOUT, xaxis_title=None, yaxis_title="Minutes", height=400)
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        section_title("Yearly Comparison", "bar_chart")
        yearly = filt.groupby("year")["minutes_played"].sum().reset_index()
        
        fig_yearly = px.bar(
            yearly,
            x="year",
            y="minutes_played",
            color_discrete_sequence=[P["secondary"]]
        )
        fig_yearly.update_layout(**CHART_LAYOUT, xaxis_title=None, yaxis_title="Minutes", height=350)
        st.plotly_chart(fig_yearly, use_container_width=True)
    
    with col2:
        section_title("Skip Rate Over Time", "skip_next")
        skip_yearly = df.groupby("year")["is_skip"].mean().mul(100).reset_index()
        
        fig_skip = px.line(
            skip_yearly,
            x="year",
            y="is_skip",
            markers=True,
            color_discrete_sequence=[P["danger"]]
        )
        fig_skip.update_layout(**CHART_LAYOUT, xaxis_title=None, yaxis_title="Skip Rate (%)", height=350)
        st.plotly_chart(fig_skip, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: TOP ARTISTS & TRACKS
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        section_title("Top 10 Artists", "mic")
        top_artists = (
            filt.groupby("artist_name")["minutes_played"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        
        for idx, row in top_artists.iterrows():
            st.markdown(f"""
            <div class='rank-item'>
                <div class='rank-num'>{idx + 1:02d}</div>
                <div class='rank-name'>{row['artist_name']}</div>
                <div class='rank-value'>{row['minutes_played'] / 60:.1f} hrs</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        section_title("Top 10 Tracks", "music_note")
        top_tracks = (
            filt.groupby("track_name")["minutes_played"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        
        for idx, row in top_tracks.iterrows():
            st.markdown(f"""
            <div class='rank-item'>
                <div class='rank-num'>{idx + 1:02d}</div>
                <div class='rank-name'>{row['track_name']}</div>
                <div class='rank-value'>{row['minutes_played'] / 60:.1f} hrs</div>
            </div>
            """, unsafe_allow_html=True)
    
    section_title("Top Artists Chart", "bar_chart")
    fig_top_artists = px.bar(
        top_artists,
        x="minutes_played",
        y="artist_name",
        orientation="h",
        color_discrete_sequence=[P["primary"]]
    )
    fig_top_artists.update_layout(
        **CHART_LAYOUT,
        xaxis_title="Minutes Played",
        yaxis_title=None,
        height=500,
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_top_artists, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: SEARCH
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        section_title("Search Artists", "person_search")
        artist_query = st.text_input("Search artist (supports regex)", placeholder="e.g. Drake|Kanye")
        
        if artist_query:
            try:
                mask = filt["artist_name"].str.contains(artist_query, case=False, regex=True, na=False)
                results = filt[mask]
                
                if results.empty:
                    st.warning("No artists found matching your search.")
                else:
                    summary = (
                        results.groupby("artist_name")
                        .agg(
                            mins=("minutes_played", "sum"),
                            plays=("play", "sum"),
                            skips=("is_skip", "sum")
                        )
                        .sort_values("mins", ascending=False)
                        .reset_index()
                    )
                    summary["skip_rate"] = (summary["skips"] / summary["plays"] * 100).round(1)
                    
                    for idx, row in summary.iterrows():
                        st.markdown(f"""
                        <div class='rank-item'>
                            <div class='rank-num'>{idx + 1:02d}</div>
                            <div class='rank-name'>{row['artist_name']}</div>
                            <div class='rank-value'>{row['mins'] / 60:.1f} hrs · {row['plays']} plays</div>
                        </div>
                        """, unsafe_allow_html=True)
            except re.error as e:
                st.error(f"Invalid regex pattern: {e}")
    
    with col2:
        section_title("Search Tracks", "manage_search")
        track_query = st.text_input("Search track (supports regex)", placeholder="e.g. love|night")
        
        if track_query:
            try:
                mask = filt["track_name"].str.contains(track_query, case=False, regex=True, na=False)
                results = filt[mask]
                
                if results.empty:
                    st.warning("No tracks found matching your search.")
                else:
                    summary = (
                        results.groupby(["track_name", "artist_name"])
                        .agg(
                            mins=("minutes_played", "sum"),
                            plays=("play", "sum")
                        )
                        .sort_values("mins", ascending=False)
                        .head(20)
                        .reset_index()
                    )
                    
                    for idx, row in summary.iterrows():
                        st.markdown(f"""
                        <div class='rank-item'>
                            <div class='rank-num'>{idx + 1:02d}</div>
                            <div style='flex: 1;'>
                                <div class='rank-name'>{row['track_name']}</div>
                                <div style='font-size: 0.85rem; color: {P["muted"]};'>{row['artist_name']}</div>
                            </div>
                            <div class='rank-value'>{row['mins'] / 60:.1f} hrs</div>
                        </div>
                        """, unsafe_allow_html=True)
            except re.error as e:
                st.error(f"Invalid regex pattern: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5: 2026 WRAPPED (Jan - Apr)
# ═══════════════════════════════════════════════════════════════════════════
with tab5:
    # Filter for Jan-Apr 2026
    wrapped_2026 = df[(df["year"] == 2026) & (df["month_num"] <= 4)].copy()
    wrapped_2025 = df[(df["year"] == 2025) & (df["month_num"] <= 4)].copy()
    
    if wrapped_2026.empty:
        st.warning("No data available for January - April 2026")
    else:
        # Hero Section
        st.markdown(f"""
        <div style='text-align: center; padding: 40px 20px; background: linear-gradient(135deg, {P["primary"]}, {P["secondary"]}); border-radius: 16px; margin-bottom: 30px;'>
            <div style='margin-bottom: 10px;'>{ms_icon('redeem', size_px=56, color='white')}</div>
            <div style='font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 8px;'>Your 2026 Wrapped</div>
            <div style='font-size: 1.2rem; color: rgba(255,255,255,0.9);'>January - April | Your First Quarter in Music</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Stats Comparison
        w26_hours = wrapped_2026["minutes_played"].sum() / 60
        w26_plays = wrapped_2026["play"].sum()
        w26_artists = wrapped_2026["artist_name"].nunique()
        w26_tracks = wrapped_2026["track_name"].nunique()
        w26_skip = wrapped_2026["is_skip"].mean() * 100
        
        w25_hours = wrapped_2025["minutes_played"].sum() / 60 if not wrapped_2025.empty else 0
        w25_plays = wrapped_2025["play"].sum() if not wrapped_2025.empty else 0
        w25_artists = wrapped_2025["artist_name"].nunique() if not wrapped_2025.empty else 0
        
        def calc_change(current, previous):
            if previous == 0:
                return "", ""
            pct = ((current - previous) / previous) * 100
            if pct > 0:
                return "▲", f"+{pct:.0f}%"
            elif pct < 0:
                return "▼", f"{pct:.0f}%"
            return "", "0%"
        
        # Stats Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        icon_h, change_h = calc_change(w26_hours, w25_hours)
        col1.metric(
            "Total Hours",
            f"{w26_hours:,.0f}",
            f"{icon_h} {change_h} vs 2025" if change_h else None
        )
        
        icon_p, change_p = calc_change(w26_plays, w25_plays)
        col2.metric(
            "Total Plays",
            f"{w26_plays:,}",
            f"{icon_p} {change_p} vs 2025" if change_p else None
        )
        
        icon_a, change_a = calc_change(w26_artists, w25_artists)
        col3.metric(
            "Artists",
            f"{w26_artists:,}",
            f"{icon_a} {change_a} vs 2025" if change_a else None
        )
        
        col4.metric(
            "Tracks",
            f"{w26_tracks:,}"
        )
        
        col5.metric(
            "Skip Rate",
            f"{w26_skip:.1f}%"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Top Artist Spotlight
        top_artist_data = wrapped_2026.groupby("artist_name")["minutes_played"].sum().sort_values(ascending=False)
        if not top_artist_data.empty:
            top_artist = top_artist_data.index[0]
            top_artist_mins = top_artist_data.iloc[0]
            top_artist_plays = wrapped_2026[wrapped_2026["artist_name"] == top_artist]["play"].sum()
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1)); border: 2px solid {P["primary"]}; border-radius: 16px; padding: 30px; margin-bottom: 30px;'>
                <div style='text-align: center;'>
                    <div style='font-size: 1rem; color: {P["muted"]}; font-weight: 600; margin-bottom: 8px;'>{ms_icon('emoji_events', size_px=18, color=P['primary'])} YOUR TOP ARTIST</div>
                    <div style='font-size: 2.5rem; font-weight: 800; color: {P["text"]}; margin-bottom: 12px;'>{top_artist}</div>
                    <div style='font-size: 1.1rem; color: {P["muted"]};'>
                        {top_artist_mins/60:.0f} hours · {top_artist_plays:,} plays
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Top 5 Artists & Tracks
        col1, col2 = st.columns(2)
        
        with col1:
            section_title("Your Top 5 Artists", "mic")
            top5_artists = wrapped_2026.groupby("artist_name")["minutes_played"].sum().sort_values(ascending=False).head(5).reset_index()
            
            for idx, row in top5_artists.iterrows():
                hours = row["minutes_played"] / 60
                plays = wrapped_2026[wrapped_2026["artist_name"] == row["artist_name"]]["play"].sum()
                
                st.markdown(f"""
                <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 20px; margin-bottom: 12px;'>
                    <div style='display: flex; align-items: center; gap: 16px;'>
                        <div style='font-size: 2rem; font-weight: 800; color: {P["primary"]}; min-width: 40px;'>{idx + 1}</div>
                        <div style='flex: 1;'>
                            <div style='font-size: 1.1rem; font-weight: 700; color: {P["text"]}; margin-bottom: 4px;'>{row['artist_name']}</div>
                            <div style='font-size: 0.9rem; color: {P["muted"]};'>{hours:.1f} hours · {plays:,} plays</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            section_title("Your Top 5 Tracks", "music_note")
            top5_tracks = wrapped_2026.groupby(["track_name", "artist_name"])["minutes_played"].sum().sort_values(ascending=False).head(5).reset_index()
            
            for idx, row in top5_tracks.iterrows():
                hours = row["minutes_played"] / 60
                plays = wrapped_2026[(wrapped_2026["track_name"] == row["track_name"]) & (wrapped_2026["artist_name"] == row["artist_name"])]["play"].sum()
                
                st.markdown(f"""
                <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 20px; margin-bottom: 12px;'>
                    <div style='display: flex; align-items: center; gap: 16px;'>
                        <div style='font-size: 2rem; font-weight: 800; color: {P["secondary"]}; min-width: 40px;'>{idx + 1}</div>
                        <div style='flex: 1;'>
                            <div style='font-size: 1.1rem; font-weight: 700; color: {P["text"]}; margin-bottom: 4px;'>{row['track_name']}</div>
                            <div style='font-size: 0.85rem; color: {P["muted"]}; margin-bottom: 4px;'>{row['artist_name']}</div>
                            <div style='font-size: 0.9rem; color: {P["muted"]};'>{hours:.1f} hours · {plays:,} plays</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Listening Patterns
        section_title("Your Listening Patterns", "insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most active day
            day_stats = wrapped_2026.groupby("day_of_week")["minutes_played"].sum().sort_values(ascending=False)
            most_active_day = day_stats.index[0]
            most_active_mins = day_stats.iloc[0]
            
            st.markdown(f"""
            <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 24px; text-align: center;'>
                <div style='margin-bottom: 12px;'>{ms_icon('calendar_today', size_px=44, color=P['primary'])}</div>
                <div style='font-size: 1rem; color: {P["muted"]}; margin-bottom: 8px;'>Most Active Day</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {P["text"]}; margin-bottom: 4px;'>{most_active_day}</div>
                <div style='font-size: 0.9rem; color: {P["muted"]};'>{most_active_mins/60:.0f} hours total</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Peak listening hour
            hour_stats = wrapped_2026.groupby("hour")["minutes_played"].sum().sort_values(ascending=False)
            peak_hour = hour_stats.index[0]
            peak_mins = hour_stats.iloc[0]
            
            st.markdown(f"""
            <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 24px; text-align: center;'>
                <div style='margin-bottom: 12px;'>{ms_icon('schedule', size_px=44, color=P['secondary'])}</div>
                <div style='font-size: 1rem; color: {P["muted"]}; margin-bottom: 8px;'>Peak Listening Hour</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: {P["text"]}; margin-bottom: 4px;'>{peak_hour}:00</div>
                <div style='font-size: 0.9rem; color: {P["muted"]};'>{peak_mins/60:.0f} hours at this time</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Monthly breakdown chart
        section_title("Monthly Breakdown", "bar_chart")
        monthly_wrapped = wrapped_2026.groupby("month")["minutes_played"].sum().reset_index()
        
        fig_wrapped = px.bar(
            monthly_wrapped,
            x="month",
            y="minutes_played",
            color_discrete_sequence=[P["primary"]]
        )
        fig_wrapped.update_layout(
            **CHART_LAYOUT,
            xaxis_title=None,
            yaxis_title="Minutes Played",
            height=350
        )
        st.plotly_chart(fig_wrapped, use_container_width=True)
        
        # Fun Facts
        section_title("Fun Facts", "celebration")
        
        total_days = (wrapped_2026["date"].max() - wrapped_2026["date"].min()).days + 1
        avg_daily_mins = wrapped_2026.groupby("date")["minutes_played"].sum().mean()
        most_played_month = wrapped_2026.groupby("month")["minutes_played"].sum().idxmax()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 20px; text-align: center;'>
                <div style='margin-bottom: 8px;'>{ms_icon('timer', size_px=32, color=P['primary'])}</div>
                <div style='font-size: 1.5rem; font-weight: 700; color: {P["text"]};'>{avg_daily_mins:.0f} min</div>
                <div style='font-size: 0.85rem; color: {P["muted"]}; margin-top: 4px;'>Average per day</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 20px; text-align: center;'>
                <div style='margin-bottom: 8px;'>{ms_icon('calendar_today', size_px=32, color=P['primary'])}</div>
                <div style='font-size: 1.5rem; font-weight: 700; color: {P["text"]};'>{total_days}</div>
                <div style='font-size: 0.85rem; color: {P["muted"]}; margin-top: 4px;'>Days of listening</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: white; border: 1px solid {P["border"]}; border-radius: 12px; padding: 20px; text-align: center;'>
                <div style='margin-bottom: 8px;'>{ms_icon('local_fire_department', size_px=32, color=P['secondary'])}</div>
                <div style='font-size: 1.5rem; font-weight: 700; color: {P["text"]};'>{most_played_month}</div>
                <div style='font-size: 0.85rem; color: {P["muted"]}; margin-top: 4px;'>Your peak month</div>
            </div>
            """, unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: {P["muted"]}; font-size: 0.85rem; padding: 20px 0;'>
    {ms_icon('headphones', size_px=18, color=P['muted'])} Spotify Listening Intelligence | {total_plays:,} plays analyzed
</div>
""", unsafe_allow_html=True)
