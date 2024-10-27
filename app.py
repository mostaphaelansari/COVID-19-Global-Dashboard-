import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from datetime import timedelta
import numpy as np

# Set page configuration with custom theme and favicon
st.set_page_config(
    page_title="Enhanced COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Application title and description with enhanced formatting
st.title("🦠 COVID-19 Global Dashboard")
st.markdown("""
    <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 5px; margin-bottom: 1rem;'>
        <h3 style='margin: 0;'>Interactive COVID-19 Analytics Platform</h3>
        <p>Explore comprehensive COVID-19 data through interactive visualizations and real-time analytics.</p>
    </div>
""", unsafe_allow_html=True)

# Enhanced data loading with error handling
@st.cache_data
def load_data():
    try:
        data = pd.read_csv('data/covid_19_clean_complete.csv')
        data['Date'] = pd.to_datetime(data['Date'])
        data.fillna({'Lat': 0, 'Long': 0}, inplace=True)
        return data, None
    except Exception as e:
        return None, f"Error loading data: {str(e)}"

# Load data with progress indication
with st.spinner('Loading COVID-19 data...'):
    covid_data, error = load_data()

if error:
    st.error(error)
    st.stop()

# Enhanced sidebar with more filtering options
st.sidebar.header("📊 Dashboard Controls")

# Date range filter with presets
date_filter_type = st.sidebar.radio(
    "Date Filter Type",
    ["Single Date", "Date Range", "Preset Periods"]
)

if date_filter_type == "Single Date":
    selected_date = st.sidebar.date_input(
        "Select Date",
        covid_data['Date'].max().date(),
        min_value=covid_data['Date'].min().date(),
        max_value=covid_data['Date'].max().date()
    )
    filtered_data = covid_data[covid_data['Date'].dt.date == selected_date]
elif date_filter_type == "Date Range":
    start_date = st.sidebar.date_input(
        "Start Date",
        covid_data['Date'].min().date(),
        min_value=covid_data['Date'].min().date(),
        max_value=covid_data['Date'].max().date()
    )
    end_date = st.sidebar.date_input(
        "End Date",
        covid_data['Date'].max().date(),
        min_value=start_date,
        max_value=covid_data['Date'].max().date()
    )
    filtered_data = covid_data[
        (covid_data['Date'].dt.date >= start_date) &
        (covid_data['Date'].dt.date <= end_date)
    ]
else:
    preset = st.sidebar.selectbox(
        "Select Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"]
    )
    end_date = covid_data['Date'].max().date()
    if preset == "Last 7 Days":
        start_date = end_date - timedelta(days=7)
    elif preset == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
    elif preset == "Last 90 Days":
        start_date = end_date - timedelta(days=90)
    else:
        start_date = covid_data['Date'].min().date()
    filtered_data = covid_data[
        (covid_data['Date'].dt.date >= start_date) &
        (covid_data['Date'].dt.date <= end_date)
    ]

# Region filter
selected_regions = st.sidebar.multiselect(
    "Filter by WHO Region",
    options=covid_data['WHO Region'].unique(),
    default=[]
)
if selected_regions:
    filtered_data = filtered_data[filtered_data['WHO Region'].isin(selected_regions)]

# Enhanced metrics with daily changes
st.markdown("### 📈 Global COVID-19 Metrics")
metrics_cols = st.columns(4)

# Calculate daily changes
latest_date = filtered_data['Date'].max()
previous_date = latest_date - timedelta(days=1)

# Ensure that the filtered data is not empty
if not filtered_data.empty:
    # Only sum numeric columns for the latest and previous dates
    latest_data = filtered_data[filtered_data['Date'] == latest_date].select_dtypes(include=[np.number]).sum()
    previous_data = filtered_data[filtered_data['Date'] == previous_date].select_dtypes(include=[np.number]).sum()
    
    # Now you can proceed to calculate changes
    def calculate_change(current, previous):
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    # Calculate changes
    confirmed_change = calculate_change(latest_data['Confirmed'], previous_data['Confirmed'])
    deaths_change = calculate_change(latest_data['Deaths'], previous_data['Deaths'])
    recovered_change = calculate_change(latest_data['Recovered'], previous_data['Recovered'])
    active_change = calculate_change(latest_data['Active'], previous_data['Active'])

    # Store metric data for display
    metric_data = [
        ("Confirmed Cases", latest_data['Confirmed'], confirmed_change),
        ("Deaths", latest_data['Deaths'], deaths_change),
        ("Recovered", latest_data['Recovered'], recovered_change),
        ("Active Cases", latest_data['Active'], active_change)
    ]

    # Display metrics
    for col, (label, value, change) in zip(metrics_cols, metric_data):
        col.metric(
            label,
            f"{value:,.0f}",
            f"{change:+.1f}%" if change != 0 else "No change"
        )
else:
    st.warning("No data available for the selected filters.")
    st.stop()


def calculate_change(current, previous):
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

# Display enhanced metrics with changes
metric_data = [
    ("Confirmed Cases", latest_data['Confirmed'], calculate_change(latest_data['Confirmed'], previous_data['Confirmed'])),
    ("Deaths", latest_data['Deaths'], calculate_change(latest_data['Deaths'], previous_data['Deaths'])),
    ("Recovered", latest_data['Recovered'], calculate_change(latest_data['Recovered'], previous_data['Recovered'])),
    ("Active Cases", latest_data['Active'], calculate_change(latest_data['Active'], previous_data['Active']))
]

for col, (label, value, change) in zip(metrics_cols, metric_data):
    col.metric(
        label,
        f"{value:,.0f}",
        f"{change:+.1f}%" if change != 0 else "No change"
    )

# Enhanced trend analysis with rolling averages
st.markdown("### 📊 COVID-19 Trends Analysis")

# Add rolling average toggle
show_rolling_average = st.checkbox("Show 7-day Rolling Average", value=True)

trend_data = filtered_data.groupby('Date')[['Confirmed', 'Deaths', 'Recovered', 'Active']].sum().reset_index()
if show_rolling_average:
    for col in ['Confirmed', 'Deaths', 'Recovered', 'Active']:
        trend_data[f'{col}_Rolling'] = trend_data[col].rolling(window=7).mean()

fig_trend = go.Figure()
metrics = ['Confirmed', 'Deaths', 'Recovered', 'Active']
colors = ['#FF9999', '#FF0000', '#00FF00', '#FFFF00']

for metric, color in zip(metrics, colors):
    fig_trend.add_trace(go.Scatter(
        x=trend_data['Date'],
        y=trend_data[metric],
        name=metric,
        line=dict(color=color, width=1),
        mode='lines'
    ))
    if show_rolling_average:
        fig_trend.add_trace(go.Scatter(
            x=trend_data['Date'],
            y=trend_data[f'{metric}_Rolling'],
            name=f'{metric} (7-day avg)',
            line=dict(color=color, width=2, dash='dash'),
            mode='lines'
        ))

fig_trend.update_layout(
    title="Global COVID-19 Trends Over Time",
    xaxis_title="Date",
    yaxis_title="Cases",
    hovermode='x unified',
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01
    )
)

st.plotly_chart(fig_trend, use_container_width=True)

# Enhanced regional and country analysis
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🌍 Regional Analysis")
    region_data = filtered_data.groupby('WHO Region').agg({
        'Confirmed': 'sum',
        'Deaths': 'sum',
        'Recovered': 'sum',
        'Active': 'sum'
    }).reset_index()
    
    fig_region = px.bar(
        region_data,
        x="WHO Region",
        y="Confirmed",
        color="WHO Region",
        title="Confirmed Cases by WHO Region",
        labels={'Confirmed': 'Confirmed Cases'},
        template="plotly_white"
    )
    fig_region.update_layout(showlegend=False)
    st.plotly_chart(fig_region, use_container_width=True)

with col2:
    st.markdown("### 🔝 Top Affected Countries")
    metric_choice = st.selectbox(
        "Select Metric",
        ["Confirmed", "Deaths", "Recovered", "Active"]
    )
    top_n = st.slider("Number of Countries", 5, 20, 10)
    
    top_countries = filtered_data.groupby('Country/Region')[metric_choice].sum()\
        .nlargest(top_n).reset_index()
    
    fig_countries = px.bar(
        top_countries,
        x="Country/Region",
        y=metric_choice,
        color="Country/Region",
        title=f"Top {top_n} Countries by {metric_choice} Cases",
        template="plotly_white"
    )
    st.plotly_chart(fig_countries, use_container_width=True)

# Enhanced map visualization with clustering
st.markdown("### 🗺️ Global COVID-19 Map")
map_metric = st.selectbox("Select Map Metric", ["Confirmed", "Deaths", "Recovered", "Active"])

m = folium.Map(location=[20, 0], zoom_start=2, tiles='CartoDB positron')

# Add clustered markers
marker_cluster = folium.plugins.MarkerCluster().add_to(m)

for idx, row in filtered_data.iterrows():
    if row[map_metric] > 0:
        folium.CircleMarker(
            location=[row['Lat'], row['Long']],
            radius=np.log(row[map_metric] + 1) * 2,  # Logarithmic scaling for better visualization
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.7,
            popup=folium.Popup(
                f"""
                <div style='width: 200px'>
                    <h4>{row['Country/Region']}</h4>
                    <b>Confirmed:</b> {row['Confirmed']:,.0f}<br>
                    <b>Deaths:</b> {row['Deaths']:,.0f}<br>
                    <b>Recovered:</b> {row['Recovered']:,.0f}<br>
                    <b>Active:</b> {row['Active']:,.0f}
                </div>
                """,
                max_width=300
            )
        ).add_to(marker_cluster)

st_folium(m, width=1000, height=600)

# Enhanced insights section
st.sidebar.markdown("### 📊 Key Insights")

# Calculate and display key statistics
latest_data = filtered_data[filtered_data['Date'] == filtered_data['Date'].max()]
mortality_rate = (latest_data['Deaths'].sum() / latest_data['Confirmed'].sum() * 100)
recovery_rate = (latest_data['Recovered'].sum() / latest_data['Confirmed'].sum() * 100)

st.sidebar.markdown(f"""
    #### Current Statistics:
    - Mortality Rate: {mortality_rate:.2f}%
    - Recovery Rate: {recovery_rate:.2f}%
    - Most Affected Region: {region_data.iloc[region_data['Confirmed'].argmax()]['WHO Region']}
    - Most Affected Country: {top_countries.iloc[0]['Country/Region']}
""")

# Add data download option
st.sidebar.markdown("### 💾 Download Data")
if st.sidebar.button("Download Filtered Data"):
    csv = filtered_data.to_csv(index=False)
    st.sidebar.download_button(
        label="Click to Download",
        data=csv,
        file_name="covid_data.csv",
        mime="text/csv"
    )