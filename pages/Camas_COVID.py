import pandas as pd
from sodapy import Socrata
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

df = pd.read_csv(
    'COVID-19_Reported_Patient_Impact_and_Hospital_Capacity_by_State_Timeseries.csv')

df.drop_duplicates(inplace=True)
df.fillna(0, inplace=True)

df2 = df.drop(df.iloc[:, 98:], axis=1)
df2.drop(columns=['previous_day_admission_adult_covid_confirmed', 'previous_day_admission_pediatric_covid_confirmed'],
         inplace=True)
df2.drop(df2.filter(regex='coverage|numerator|denominator|suspected|reported|utilization|unknown|percent|geo').columns,
         axis=1, inplace=True)

df2['date'] = pd.to_datetime(df2['date'])
df2['month'] = df2['date'].dt.month
df2 = df2.convert_dtypes()
df2.reset_index(drop=True, inplace=True)

us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}

# invert the dictionary
abbrev_to_us_state = dict(map(reversed, us_state_to_abbrev.items()))

df2['total_hospitalized'] = df2['total_adult_patients_hospitalized_confirmed_covid'] + \
                            df2['total_pediatric_patients_hospitalized_confirmed_covid']
df2['date'] = pd.to_datetime(df2['date'])
df2['month'] = df2['date'].dt.month
df2['state_name'] = df2['state'].replace(abbrev_to_us_state)
df2 = df2.convert_dtypes()
df2.reset_index(drop=True, inplace=True)

bed_timeline = df2.copy()
bed_timeline['date'] = bed_timeline['date'].dt.strftime('%Y-%m-%d')
bed_timeline.sort_values(by='date', inplace=True)

timelinefig = px.choropleth_mapbox(bed_timeline,
                                   geojson='https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data'
                                           '/geojson/us-states.json',
                                   locations='state_name', featureidkey='properties.name',
                                   color='inpatient_beds_used_covid', color_continuous_scale='Inferno_r',
                                   mapbox_style="carto-positron", zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                                   opacity=0.5, labels={'inpatient_beds_used_covid': 'Total Camas',
                                                        'state_name': 'Estado',
                                                        'date': 'Fecha'}, animation_frame='date')
timelinefig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# Interfaz Web #
st.title('Uso de Camas UCI en EEUU')
st.plotly_chart(timelinefig)
