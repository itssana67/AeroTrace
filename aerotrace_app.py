import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(
    page_title="AeroTrace",
    page_icon="🌍",
    layout="wide"
)

# =====================================================
# SNOWFLAKE CONNECTION & CACHING
# =====================================================
@st.cache_resource(ttl=3600, show_spinner="Connecting to Snowflake...")
def get_connection():
    if "snowflake" not in st.secrets:
        return None

    s = st.secrets["snowflake"]
    return snowflake.connector.connect(
        account=s["account"],
        user=s["user"],
        password=s["password"],
        warehouse=s.get("warehouse", "COMPUTE_WH"),
        database=s.get("database", "AEROTRACE_DB"),
        schema=s.get("schema", "ANALYTICS"),
        role=s.get("role", "ACCOUNTADMIN"),
        client_session_keep_alive=True
    )


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query):
    if "snowflake" not in st.secrets:
        return pd.DataFrame()

    conn = get_connection()
    if conn is None:
        return pd.DataFrame()

    try:
        return pd.read_sql(query, conn)
    except Exception:
        # Re-try with a fresh connection if cached session expired
        s = st.secrets["snowflake"]
        fresh_conn = snowflake.connector.connect(
            account=s["account"],
            user=s["user"],
            password=s["password"],
            warehouse=s.get("warehouse", "COMPUTE_WH"),
            database=s.get("database", "AEROTRACE_DB"),
            schema=s.get("schema", "ANALYTICS"),
            role=s.get("role", "ACCOUNTADMIN"),
            client_session_keep_alive=True
        )
        try:
            return pd.read_sql(query, fresh_conn)
        finally:
            fresh_conn.close()


# =====================================================
# SIDEBAR: LIVE CONNECTIVITY STATUS
# =====================================================
with st.sidebar:
    st.markdown("## ❄️ Snowflake Live Status")

    if "snowflake" not in st.secrets:
        st.error("🔴 **Not Configured**")
        st.caption("Missing `[snowflake]` in Streamlit Secrets.")
        st.info("💡 Add your credentials in **Streamlit Cloud → App Settings → Secrets**.")
    else:
        try:
            ping_df = run_query("SELECT CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_ROLE()")
            if not ping_df.empty:
                st.success("🟢 **Live Connected**")
                st.caption(f"**Database:** `{ping_df.iloc[0, 2]}`")
                st.caption(f"**Warehouse:** `{ping_df.iloc[0, 1]}`")
                st.caption(f"**Role:** `{ping_df.iloc[0, 3]}`")
                st.caption(f"**Engine:** Snowflake `v{ping_df.iloc[0, 0]}`")
            else:
                st.warning("🟡 Connected (Empty Ping)")
        except Exception as e:
            st.error("🔴 **Connection Error**")
            st.caption(f"Error: `{e}`")

    if st.button("🔄 Refresh Data Cache"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("AeroTrace v2.0 • Real-time Snowflake Telemetry")


# =====================================================
# HEADER
# =====================================================

st.title(" AeroTrace")
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

        st.markdown("### Top Pollution Hotspots")

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

        st.markdown("### Detected Pollution Spikes")

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

        st.markdown("###  Nearby Pollution Source Context")

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
# WEATHER FORECAST & PREDICTION (SNOWFLAKE ML)
# =====================================================

st.markdown("## 🔮 Weather Prediction & Forecasting (Snowflake ML)")

if city == "Lucknow":

    forecast_query = """
    SELECT
        forecast_time,
        predicted_temperature,
        lower_bound,
        upper_bound
    FROM AEROTRACE_DB.ANALYTICS.WEATHER_FORECAST_PREDICTIONS
    ORDER BY forecast_time ASC
    LIMIT 24
    """

    try:
        forecast_data = run_query(forecast_query)
    except Exception:
        forecast_data = pd.DataFrame()

    if not forecast_data.empty:
        forecast_data.columns = [c.upper() for c in forecast_data.columns]

        # Forecast KPI summary
        f1, f2, f3 = st.columns(3)
        avg_future_temp = forecast_data["PREDICTED_TEMPERATURE"].mean()
        max_future_temp = forecast_data["PREDICTED_TEMPERATURE"].max()
        min_future_temp = forecast_data["PREDICTED_TEMPERATURE"].min()

        f1.metric("🌡️ Projected Avg Temp", f"{avg_future_temp:.1f} °C")
        f2.metric("🔥 Expected High", f"{max_future_temp:.1f} °C")
        f3.metric("❄️ Expected Low", f"{min_future_temp:.1f} °C")

        # Interactive Forecast Line Chart
        st.markdown("### 📈 24-Hour Projected Temperature Trend")
        chart_df = forecast_data.set_index("FORECAST_TIME")[["PREDICTED_TEMPERATURE", "LOWER_BOUND", "UPPER_BOUND"]]
        st.line_chart(chart_df, use_container_width=True)

        with st.expander("📋 View ML Forecast Data Table"):
            st.dataframe(forecast_data, use_container_width=True)

        st.caption(
            "Powered by Snowflake ML (SNOWFLAKE.ML.FORECAST). "
            "Predicts future meteorological trends with 95% confidence intervals."
        )

    else:
        st.info("Snowflake ML weather forecast model has not been generated yet or table is empty.")

else:
    st.info("Weather forecast will be connected for this city.")


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

        st.markdown("### Highest Pollution Event Signatures")

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
    WHERE LOWER(pollutant) != 'wind_direction'
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
        # Standardize column headers to uppercase for consistency
        risks.columns = [c.upper() for c in risks.columns]

        # -------------------------------------------------
        # KPI Risk Summary
        # -------------------------------------------------
        k1, k2, k3, k4 = st.columns(4)
        total_signals = len(risks)
        high_count = int((risks["RISK_LEVEL"] == "HIGH").sum())
        med_count = int((risks["RISK_LEVEL"] == "MEDIUM").sum())
        low_count = int((risks["RISK_LEVEL"] == "LOW").sum())

        k1.metric("🚨 Total Signals", total_signals)
        k2.metric("🔴 High Risk", high_count)
        k3.metric("🟡 Medium Risk", med_count)
        k4.metric("🟢 Low Risk", low_count)

        # -------------------------------------------------
        # Interactive Visual Charts
        # -------------------------------------------------
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("### 📊 Risk Level Breakdown")
            risk_dist = (
                risks["RISK_LEVEL"]
                .value_counts()
                .reindex(["HIGH", "MEDIUM", "LOW"])
                .fillna(0)
                .reset_index()
            )
            risk_dist.columns = ["Risk Level", "Alert Count"]
            st.bar_chart(
                risk_dist,
                x="Risk Level",
                y="Alert Count",
                use_container_width=True
            )

        with c_right:
            st.markdown("### ⚡ Pollution Severity by Pollutant")
            # Exclude non-pollutant sensor artifacts (e.g. wind_direction) from pollutant chart
            chart_df = risks[~risks["POLLUTANT"].astype(str).str.lower().isin(["wind_direction"])].copy()
            chart_df["POLLUTANT"] = chart_df["POLLUTANT"].astype(str).str.upper()

            if not chart_df.empty:
                chart_summary = (
                    chart_df.groupby(["POLLUTANT", "RISK_LEVEL"], as_index=False)["AVG_POLLUTION"]
                    .mean()
                )
                st.bar_chart(
                    chart_summary,
                    x="POLLUTANT",
                    y="AVG_POLLUTION",
                    color="RISK_LEVEL",
                    use_container_width=True
                )
            else:
                st.info("No pollutant measurement available for chart.")

        with st.expander("📋 View Underlying Signals Data"):
            st.dataframe(risks, use_container_width=True)

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
        AI_INSIGHT,
        DATETIME_LOCAL
    FROM AEROTRACE_DB.ANALYTICS.AEROTRACE_AI_LAB
    ORDER BY DATETIME_LOCAL DESC
    LIMIT 1
    """

    ai_data = run_query(ai_query)

    if not ai_data.empty:

        st.markdown("###  AI-Generated Pollution Analysis")

        ai_text = str(ai_data.iloc[0]["AI_INSIGHT"])

        # Convert escaped newlines
