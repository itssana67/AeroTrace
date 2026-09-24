import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(
    page_title="AeroTrace",
    page_icon="🌍",
    layout="wide"
)

# =====================================================
# SNOWFLAKE CONNECTION
# =====================================================
def get_connection():
    s = st.secrets["snowflake"]

    return snowflake.connector.connect(
        account=s["account"],
        user=s["user"],
        password=s["password"],
        warehouse=s["warehouse"],
        database=s["database"],
        schema=s["schema"],
        role=s["role"],
        client_session_keep_alive=True
    )


def run_query(query):
    conn = get_connection()

    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()

# =====================================================
# HEADER
# =====================================================

st.title("🌍 AeroTrace")
st.subheader("Air Pollution Source Detection & Risk Analysis")

st.divider()


# =====================================================
# CITY SELECTION
# =====================================================

st.markdown("## 📍 Select City / Area")

city = st.selectbox(
    "Choose a city",
    ["Lucknow", "Delhi", "Kanpur", "Mumbai"]
)

st.write("Selected Area:", city)


# =====================================================
# INTERACTIVE POLLUTION MAP
# =====================================================

st.markdown("## 🗺️ Interactive Pollution Map")

if city == "Lucknow":

    map_query = """
    SELECT
        hotspot_latitude AS "latitude",
        hotspot_longitude AS "longitude"
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_HOTSPOTS
    """

    map_data = run_query(map_query)

    if not map_data.empty:

        st.map(
            map_data[["latitude", "longitude"]],
            zoom=10
        )

        st.caption(
            "📍 Pollution hotspots detected from AeroTrace air-quality data."
        )

    else:
        st.info("No hotspot locations available.")

else:

    st.info(
        "Pollution map data for this city will be connected next."
    )


st.divider()

# =====================================================
# CORE FEATURE 1
# POLLUTION MONITORING
# =====================================================

st.markdown("## 📊 Pollution Monitoring")

if city == "Lucknow":

    pollution_query = """
    SELECT
        datetime_local,
        pollutant,
        value,
        unit,
        latitude,
        longitude
    FROM AEROTRACE_DB.CLEAN.AIR_QUALITY_CLEAN
    ORDER BY datetime_local DESC
    LIMIT 50
    """

    pollution = run_query(pollution_query)

    if not pollution.empty:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Measurements",
            len(pollution)
        )

        c2.metric(
            "Pollutants",
            pollution["POLLUTANT"].nunique()
        )

        c3.metric(
            "Latest Reading",
            str(pollution["DATETIME_LOCAL"].max())
        )

        st.dataframe(
            pollution,
            use_container_width=True
        )

    else:
        st.info("No pollution data available.")

else:
    st.info("Pollution monitoring will be connected for this city.")


# =====================================================
# CORE FEATURE 2
# HOTSPOT DETECTION
# =====================================================

st.markdown("## 🏭 Hotspot Detection")

if city == "Lucknow":

    hotspot_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        measurements
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_HOTSPOTS
    ORDER BY avg_pollution DESC
    LIMIT 10
    """

    hotspots = run_query(hotspot_query)

    if not hotspots.empty:

        st.markdown("### 🔥 Top Pollution Hotspots")

        st.dataframe(
            hotspots,
            use_container_width=True
        )

    else:
        st.info("No pollution hotspots detected.")

else:
    st.info("Hotspot detection will be connected for this city.")


# =====================================================
# CORE FEATURE 3
# SPIKE DETECTION
# =====================================================

st.markdown("## 📈 Spike Detection")

if city == "Lucknow":

    spike_query = """
    SELECT
        datetime_local,
        pollutant,
        value,
        previous_value,
        increase_percent,
        latitude,
        longitude
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_SPIKES
    ORDER BY increase_percent DESC
    LIMIT 10
    """

    spikes = run_query(spike_query)

    if not spikes.empty:

        st.markdown("### 🚨 Detected Pollution Spikes")

        st.dataframe(
            spikes,
            use_container_width=True
        )

    else:
        st.info("No significant pollution spikes detected.")

else:
    st.info("Spike detection will be connected for this city.")


# =====================================================
# CORE FEATURE 4
# SOURCE ANALYSIS
# =====================================================

st.markdown("## 🔎 Source Analysis")

if city == "Lucknow":

    source_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        feature_type,
        nearby_features
    FROM AEROTRACE_DB.ANALYTICS.HOTSPOT_SOURCE_CONTEXT
    ORDER BY avg_pollution DESC, nearby_features DESC
    LIMIT 15
    """

    sources = run_query(source_query)

    if not sources.empty:

        st.markdown("### 🏭 Nearby Pollution Source Context")

        st.dataframe(
            sources,
            use_container_width=True
        )

        st.caption(
            "Source categories represent nearby mapped features "
            "and should be interpreted as contextual signals, "
            "not proof of causation."
        )

    else:
        st.info("No source context available.")

else:
    st.info("Source analysis will be connected for this city.")


# =====================================================
# CORE FEATURE 5
# WEATHER & WIND
# =====================================================

st.markdown("## 🌬️ Weather & Wind Context")

if city == "Lucknow":

    weather_query = """
    SELECT
        datetime_local,
        temperature,
        relative_humidity,
        precipitation,
        wind_speed,
        wind_direction,
        surface_pressure
    FROM AEROTRACE_DB.RAW.AEROTRACE_WEATHER_HISTORICAL
    ORDER BY datetime_local DESC
    LIMIT 10
    """

    weather = run_query(weather_query)

    if not weather.empty:

        latest = weather.iloc[0]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "🌡️ Temperature",
            f"{latest['TEMPERATURE']} °C"
        )

        c2.metric(
            "💧 Humidity",
            f"{latest['RELATIVE_HUMIDITY']} %"
        )

        c3.metric(
            "💨 Wind Speed",
            f"{latest['WIND_SPEED']}"
        )

        c4.metric(
            "🧭 Wind Direction",
            f"{latest['WIND_DIRECTION']}°"
        )

        st.dataframe(
            weather,
            use_container_width=True
        )

    else:
        st.info("Weather data unavailable.")

else:
    st.info("Weather data will be connected for this city.")


# =====================================================
# USP 1
# POPULATION EXPOSURE
# =====================================================

st.markdown("## 👥 Population Exposure")

if city == "Lucknow":

    population_query = """
    SELECT
        area_name,
        ward_id,
        population,
        exposure_population_level
    FROM AEROTRACE_DB.ANALYTICS.POPULATION_EXPOSURE
    ORDER BY population DESC
    LIMIT 15
    """

    population = run_query(population_query)

    if not population.empty:

        st.dataframe(
            population,
            use_container_width=True
        )

        st.caption(
            "Population level indicates population size by urban ward; "
            "it is not a direct estimate of pollution exposure."
        )

    else:
        st.info("Population data unavailable.")

else:
    st.info("Population exposure will be connected for this city.")


# =====================================================
# USP 2
# SIMILAR EVENT DETECTION
# =====================================================

st.markdown("## 🔍 Similar Event Detection")

if city == "Lucknow":

    event_query = """
    SELECT
        datetime_local,
        latitude,
        longitude,
        avg_pollution,
        avg_temperature,
        avg_humidity,
        avg_wind_speed,
        avg_wind_direction
    FROM AEROTRACE_DB.ANALYTICS.POLLUTION_EVENT_SIGNATURE
    ORDER BY avg_pollution DESC
    LIMIT 10
    """

    events = run_query(event_query)

    if not events.empty:

        st.markdown("### 🔍 Highest Pollution Event Signatures")

        st.dataframe(
            events,
            use_container_width=True
        )

        st.caption(
            "These signatures can be used as a basis for comparing "
            "future pollution events with historical patterns."
        )

    else:
        st.info("No event signatures available.")

else:
    st.info("Similar event detection will be connected for this city.")


# =====================================================
# USP 3
# SMART ALERTS + RISK
# =====================================================

st.markdown("## 🚨 Smart Alerts + Risk Analysis")

if city == "Lucknow":

    risk_query = """
    SELECT
        hotspot_latitude,
        hotspot_longitude,
        pollutant,
        avg_pollution,
        increase_percent,
        temperature,
        relative_humidity,
        wind_speed,
        wind_direction,
        risk_level
    FROM AEROTRACE_DB.ANALYTICS.SMART_RISK_SIGNALS
    ORDER BY
        CASE risk_level
            WHEN 'HIGH' THEN 1
            WHEN 'MEDIUM' THEN 2
            WHEN 'LOW' THEN 3
            ELSE 4
        END,
        avg_pollution DESC
    LIMIT 15
    """

    risks = run_query(risk_query)

    if not risks.empty:

        st.markdown("### 🚨 Active Risk Signals")

        st.dataframe(
            risks,
            use_container_width=True
        )

        st.caption(
            "Risk level is a data-driven signal based on pollution "
            "increase and wind conditions; it is not a medical or "
            "public-health risk assessment."
        )

    else:
        st.info("No active risk signals.")

else:
    st.info("Smart alerts will be connected for this city.")

# =====================================================
# ASK AEROTRACE
# =====================================================

st.markdown("## 🤖 AeroTrace AI Analyst")

if city == "Lucknow":

    ai_query = """
    SELECT
        AI_INSIGHT
    FROM AEROTRACE_DB.ANALYTICS.AEROTRACE_AI_LAB
    ORDER BY DATETIME_LOCAL DESC
    LIMIT 1
    """

    ai_data = run_query(ai_query)

    if not ai_data.empty:

        st.markdown(
            """
            <div style="
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #ddd;
                background-color: #f8f9fa;
            ">
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 🧠 AI-Generated Pollution Analysis")

       ai_text = str(ai_data.iloc[0]["AI_INSIGHT"])

# Convert escaped newlines into real formatting
ai_text = ai_text.replace("\\n", "\n")

# Remove unwanted outer quotes if present
ai_text = ai_text.strip().strip('"')

st.markdown(ai_text)
        st.markdown("</div>", unsafe_allow_html=True)

        st.caption(
            "AI analysis is generated from AeroTrace pollution, "
            "weather and spatial-source context. It provides "
            "source clues and monitoring insights, not proof of causation."
        )

    else:
        st.info("No AI insight available.")

else:
    st.info("AI analysis is currently connected to the Lucknow dataset.")# =====================================================
# FOOTER
# =====================================================

st.divider()

st.markdown(
    "🌍 **AeroTrace** — Monitor → Locate Hotspot → "
    "Detect Spike → Investigate Source → Assess Exposure → Respond"
)
