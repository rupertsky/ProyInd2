import pandas as pd
from sodapy import Socrata
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def re_idx_name(data, ogcol, rename=None):
    """
    Funcion que re-organiza las columnas en un Dataframe

    Parametros
    ----------
    :param data: Dataframe
    :param ogcol: Orden de las columnas con sus nombres originales
    :param rename: Si se quiere renombrar alguna columna,
    se le pasa un Dict que contenga el nombre de la columna original
    y su nuevo nombre. De la forma {'nombre': 'Nombre'}

    Return
    ----------
    :return: Dataframe reindexado
    """
    try:
        data = data.reindex(ogcol, axis=1)
        if rename:
            data.rename(columns=rename, inplace=True)
            return data
        return data
    except TypeError:
        print('TypeError: Insert a dict in rename place')
    except Exception as e:
        return e


df = pd.read_csv(
    'COVID-19_Reported_Patient_Impact_and_Hospital_Capacity_by_State_Timeseries.csv')

df.drop_duplicates(inplace=True)
df.fillna(0, inplace=True)

df2 = df.drop(df.iloc[:, 98:], axis=1)
df2.drop(columns=['previous_day_admission_adult_covid_confirmed', 'previous_day_admission_pediatric_covid_confirmed'],
         inplace=True)
df2.drop(df2.filter(regex='coverage|numerator|denominator|suspected|reported|utilization|unknown|percent|geo').columns,
         axis=1, inplace=True)

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

df2['date'] = pd.to_datetime(df2['date'])
df2['month'] = df2['date'].dt.month
df2['total_hospitalized'] = df2['total_adult_patients_hospitalized_confirmed_covid'] + df2[
    'total_pediatric_patients_hospitalized_confirmed_covid']
df2['state_name'] = df2['state'].replace(abbrev_to_us_state)
df2 = df2.convert_dtypes()
df2.reset_index(drop=True, inplace=True)

eeuu_map = df2.copy()
eeuu_map['date'] = eeuu_map['date'].dt.strftime('%Y-%m-%d')
eeuu_map.sort_values(by='date', inplace=True)

usa_map2 = px.choropleth_mapbox(eeuu_map,
                                geojson='https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json',
                                locations='state_name', featureidkey='properties.name',
                                color='total_hospitalized', color_continuous_scale='Reds',
                                mapbox_style="carto-positron", zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                                opacity=0.5, labels={'total_hospitalized': 'Total Hospitalizados',
                                                     'state_name': 'Estado',
                                                     'date': 'Fecha'}, animation_frame='date')
usa_map2.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

hospt = df2.groupby('state')[['total_hospitalized']].sum()
hospt.reset_index(inplace=True)
hospt['state_name'] = hospt['state'].replace(abbrev_to_us_state)
hospt.sort_values(by='total_hospitalized', ascending=False, inplace=True)
hospt.drop(columns='state', inplace=True)
dat_col3 = ['total_hospitalized', 'state_name']
hospt = re_idx_name(hospt, dat_col3, {'state_name': 'Estado', 'total_hospitalized': 'Hospitalizados_COVID'})
hospt.reset_index(drop=True, inplace=True)

usa_map = px.choropleth_mapbox(hospt,
                               geojson='https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json',
                               locations='Estado', featureidkey='properties.name',
                               color='Hospitalizados_COVID', color_continuous_scale='Reds',
                               mapbox_style="carto-positron", zoom=3, center={"lat": 37.0902, "lon": -95.7129},
                               opacity=0.5, labels={'Hospitalizados_COVID': 'Total Hospitalizados'})
usa_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

# Interfaz Web #
st.title('Mapa de Hospitalizados en EEUU')
st.plotly_chart(usa_map2)
################
st.subheader('Ranking de Estados con mayor ocupación hospitalaria por **_COVID_**')
st.dataframe(hospt)
st.markdown('Mapa por estado de Hospitalizados por COVID Totales')
st.plotly_chart(usa_map)
