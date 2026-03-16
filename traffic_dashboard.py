import streamlit as st
import pandas as pd
import plotly.express as px

#   Title & basic layout
st.set_page_config(page_title="Simple Traffic Dashboard", layout="wide")
st.title(" Basic Traffic Analytics Dashboard")
st.markdown("Upload your traffic CSV or use the sample format below.")

uploaded_file = st.file_uploader("Upload your traffic CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    try:
        df = pd.read_csv("traffic.csv")   
        st.info("Using sample file 'traffic.csv' (change path if needed)")
    except FileNotFoundError:
        st.error("No file uploaded and 'traffic.csv' not found in folder.")
        st.stop()

# Quick data cleaning / preparation
# onvert Date & Time → real datetime
date_col = None
time_col = None

possible_date_cols = ['Date', 'date', 'DateTime']
possible_time_cols = ['Time', 'time']

for col in possible_date_cols:
    if col in df.columns:
        date_col = col
        break

for col in possible_time_cols:
    if col in df.columns:
        time_col = col
        break

if date_col and time_col:
    df['Datetime'] = pd.to_datetime(df[date_col] + ' ' + df[time_col], errors='coerce')
elif date_col:
    df['Datetime'] = pd.to_datetime(df[date_col], errors='coerce')
else:
    # fallback
    datetime_candidates = ['Datetime', 'timestamp', 'DateTime']
    for c in datetime_candidates:
        if c in df.columns:
            df['Datetime'] = pd.to_datetime(df[c], errors='coerce')
            break

#columns
if 'Datetime' in df.columns and df['Datetime'].notna().any():
    df['Hour'] = df['Datetime'].dt.hour
    df['Day_of_week'] = df['Datetime'].dt.day_name()
    df['Date_only'] = df['Datetime'].dt.date

# Common columns we might have
vehicle_col = next((c for c in ['Vehicles', 'Total', 'CarCount', 'vehicles'] if c in df.columns), None)
location_col = next((c for c in ['Junction', 'Location', 'junction'] if c in df.columns), None)

#   Sidebar filters
st.sidebar.header("Filters")

if location_col and df[location_col].nunique() > 1:
    locations = ['All'] + sorted(df[location_col].dropna().unique().tolist())
    selected_location = st.sidebar.selectbox("Select Location/Junction", locations)
    if selected_location != 'All':
        df = df[df[location_col] == selected_location]

if 'Hour' in df.columns:
    hour_range = st.sidebar.slider("Hour of Day", 0, 23, (0, 23))
    df = df[df['Hour'].between(hour_range[0], hour_range[1])]

#   Key Metrics
st.subheader("Key Numbers")

col1, col2, col3 = st.columns(3)

if vehicle_col:
    total_vehicles = df[vehicle_col].sum()
    avg_vehicles = df[vehicle_col].mean()
    max_vehicles = df[vehicle_col].max()

    col1.metric("Total Vehicles", f"{total_vehicles:,.0f}")
    col2.metric("Average per Reading", f"{avg_vehicles:.1f}")
    col3.metric("Peak Vehicles", f"{max_vehicles:,}")

if 'Datetime' in df.columns:
    busiest_hour = df.groupby('Hour')[vehicle_col].mean().idxmax() if vehicle_col else "—"
    col1.metric("Busiest Hour (avg)", f"{busiest_hour:02d}:00")

#   Visualizations
st.subheader("Traffic Patterns")

if vehicle_col and 'Datetime' in df.columns:
    # Time series line chart
    fig_line = px.line(
        df.sort_values('Datetime'),
        x='Datetime',
        y=vehicle_col,
        color=location_col if location_col else None,
        title="Traffic Volume Over Time"
    )
    st.plotly_chart(fig_line, use_container_width=True)

if vehicle_col and 'Hour' in df.columns:
    # Hourly average bar chart
    hourly = df.groupby('Hour')[vehicle_col].mean().reset_index()
    fig_bar = px.bar(
        hourly,
        x='Hour',
        y=vehicle_col,
        title="Average Traffic by Hour of Day",
        labels={vehicle_col: "Avg Vehicles"}
    )
    fig_bar.update_xaxes(type='category')
    st.plotly_chart(fig_bar, use_container_width=True)

if vehicle_col and location_col and df[location_col].nunique() <= 12:
    # Heatmap style – average by hour & location
    pivot = df.pivot_table(
        values=vehicle_col,
        index='Hour',
        columns=location_col,
        aggfunc='mean'
    )
    fig_heat = px.imshow(
        pivot,
        title="Average Traffic Heatmap (Hour vs Location)",
        color_continuous_scale="YlOrRd",
        labels=dict(color="Avg Vehicles")
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# Raw data preview
with st.expander("See raw data (first 100 rows)"):
    st.dataframe(df.head(100))

st.markdown("---")
st.caption("Traffic dashboard – extend it with predictions!")