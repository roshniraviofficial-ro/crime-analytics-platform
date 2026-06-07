import folium 
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import plotly.express as px
from pyvis.network import Network
import networkx as nx
import streamlit.components.v1 as components

# Page Settings
st.set_page_config(page_title="CrimeSageAI",layout="wide")

# Title
st.title("CrimeSage AI")
st.subheader("Conversational Crime Intelligence & Analytics Platform")

# Search Box
search_query = st.text_input("Search Crime Records")

# Load dataset
df = pd.read_csv("data/fir_records.csv")
offender_counts = df["accused_name"].value_counts()
df["repeat_count"] = df["accused_name"].map(offender_counts)

df["risk_score"] = df["severity_score"] + df["repeat_count"]

def risk_level(score):
    if score >= 7:
        return "High Risk"
    elif score >= 5:
        return "Medium Risk"
    else:
        return "Low Risk"

df["risk_level"] = df["risk_score"].apply(risk_level)
# Sidebar filters
st.sidebar.title("Filters")

selected_location = st.sidebar.selectbox("Select Location", df["location"].unique())
filtered_df = df[df["location"] == selected_location]

# Search functionality
if search_query:
    filtered_df = filtered_df[
        filtered_df.apply(
            lambda row: search_query.lower() in row.to_string().lower(),
            axis=1
        )
    ]
    st.write("## AI Crime Intelligence Summary")

if search_query:
    total_results = len(filtered_df)

    st.info(f"Query understood: '{search_query}'")

    if total_results > 0:
        st.success(f"Found {total_results} matching crime record(s).")

        crime_types = filtered_df["crime_type"].unique()
        locations = filtered_df["location"].unique()

        st.write("### Summary")
        st.write(f"This query is related to {', '.join(crime_types)} case(s) in {', '.join(locations)}.")

        st.write("### Evidence FIR IDs")
        st.write(", ".join(filtered_df["fir_id"].astype(str).tolist()))
    else:
        st.warning("No matching crime records found.")
else:
    st.write("Ask a crime-related question or search keyword to generate intelligence summary.")
st.write("## FIR Records")
st.dataframe(filtered_df)

# Crime Count Chart
st.write("## Crime Type Distribution")
crime_count = filtered_df["crime_type"].value_counts().reset_index()
crime_count.columns = ["crime_type", "count"]

fig = px.bar(
    crime_count,
    x="crime_type",
    y="count",
    title="Crime Type Analysis"
)
st.plotly_chart(fig, use_container_width=True)

# Location Wise Crime
st.write("## Location Wise Crimes")
location_count = filtered_df["location"].value_counts().reset_index()
location_count.columns = ["location", "count"]
fig2 = px.pie(
    location_count,
    names="location",
    values="count",
    title="Crime Distribution by Location"
)
st.plotly_chart(fig2, use_container_width=True)

st.write("## Criminal Network Analysis")

# Create graph
G = nx.Graph()

# Add connections
for index, row in filtered_df.iterrows():
    accused = row["accused_name"]
    fir = row["fir_id"]
    location = row["location"]

    G.add_node(accused, color="red")
    G.add_node(fir, color="blue")
    G.add_node(location, color="green")

    G.add_edge(accused, fir)
    G.add_edge(fir, location)

# Create PyVis network
net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")

net.from_nx(G)

# Save graph
net.save_graph("crime_network.html")

# Display graph
HtmlFile = open("crime_network.html", "r", encoding="utf-8")
source_code = HtmlFile.read()

components.html(source_code, height=550)
st.write("## Offender Risk Scoring")

risk_table = df[["accused_name", "repeat_count", "severity_score", "risk_score", "risk_level"]]

st.dataframe(risk_table.drop_duplicates())
st.write("## Crime Hotspot Map")

# Create map
crime_map = folium.Map(location=[13.0, 77.0], zoom_start=5)

# Add markers
for index, row in filtered_df.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
        popup=f"{row['crime_type']} - {row['location']}",
        tooltip=row["accused_name"]
    ).add_to(crime_map)

# Show map
st_folium(crime_map, width=700, height=500)