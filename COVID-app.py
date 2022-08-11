import pandas as pd
from sodapy import Socrata
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import calendar


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
    'C:\\Users\\cajas\\PycharmProjects\\ProyInd2\\COVID-19_Reported_Patient_Impact_and_Hospital_Capacity_by_State_Timeseries.csv')

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

# 1.
s5m = df2.loc[df2['date'].dt.year == 2020]
s5m = s5m.groupby('state').apply(lambda x: x[x['month'] <= 6][
    ['inpatient_beds_used_covid', 'total_adult_patients_hospitalized_confirmed_covid', 'deaths_covid']].sum())
s5m = s5m.loc[s5m['inpatient_beds_used_covid'].nlargest(5).index]
dat_col = list(s5m.columns)
s5m = re_idx_name(s5m, dat_col, {'inpatient_beds_used_covid': 'Camas UCI COVID',
                                 'total_adult_patients_hospitalized_confirmed_covid': 'Adultos Hospitalizados',
                                 'deaths_covid': 'Muertes'})

# 2.
new_york = df2.sort_values(by='date')
new_york = new_york.loc[
    (new_york['date'] >= '2020-03-20') & (new_york['date'] <= '2021-06-15') & (new_york['state'] == 'NY')]
new_york.reset_index(drop=True, inplace=True)

nyfig = px.line(new_york, x='date', y=['inpatient_beds_used_covid', 'deaths_covid'])
nyfig.update_layout(title='Ocupacion de Camas New York', xaxis_title='Año',
                    yaxis_title='Camas Usadas', hovermode='x unified', xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False))
var = {'inpatient_beds_used_covid': 'Camas Covid', 'deaths_covid': 'Muertes Covid'}
nyfig.for_each_trace(lambda t: t.update(name=var[t.name], legendgroup=var[t.name],
                                        hovertemplate=t.hovertemplate.replace(t.name, var[t.name])))

# 3.
most_beds = df2.groupby('state').apply(lambda x: x[x['date'].dt.year == 2020][
    ['inpatient_beds', 'inpatient_beds_used', 'inpatient_beds_used_covid']].sum())
most_beds = most_beds.loc[most_beds['inpatient_beds_used'].nlargest(5).index]
most_beds.reset_index(inplace=True)
dat_col2 = list(most_beds.columns)
most_beds = re_idx_name(most_beds, dat_col2, {'state': 'Estado',
                                              'inpatient_beds': 'Camas UCI Disponibles',
                                              'inpatient_beds_used': 'Camas UCI Normal',
                                              'inpatient_beds_used_covid': 'Camas UCI COVID'})

bedsfig = px.histogram(most_beds, y='Camas UCI Normal', x='Estado', text_auto=True, color='Estado',
                       color_discrete_sequence=px.colors.sequential.PuRd_r)
bedsfig.update_layout(title='Ocupacion de Camas UCI por estado', xaxis_title='Estado',
                      yaxis_title='Camas UCI Utilizadas', xaxis=dict(showgrid=False),
                      yaxis=dict(showgrid=False))

# 4.
kids_bed = df2.groupby('state').apply(
    lambda x: x[x['date'].dt.year == 2020][['total_pediatric_patients_hospitalized_confirmed_covid']].sum())
kids_bed.reset_index(inplace=True)
kids_bed.sort_values(by='total_pediatric_patients_hospitalized_confirmed_covid', ascending=False, inplace=True)

kfig = px.histogram(kids_bed, y='total_pediatric_patients_hospitalized_confirmed_covid', x='state',
                    color_discrete_sequence=px.colors.diverging.Geyser)
kfig.update_layout(title='Camas pediatricas UCI por estado', xaxis_title='Estado',
                   yaxis_title='Camas UCI Utilizadas', xaxis=dict(showgrid=False),
                   yaxis=dict(showgrid=False))
kfig.update_xaxes(tickangle=325)

# 5.
uci_beds = df2.groupby('state')[['inpatient_beds', 'inpatient_beds_used_covid']].sum()
uci_beds['usage_percent'] = round((uci_beds['inpatient_beds_used_covid'] / uci_beds['inpatient_beds']) * 100, 2)
uci_beds.sort_values(by='usage_percent', ascending=False, inplace=True)

uci_plot = uci_beds.copy()
uci_plot.reset_index(inplace=True)

uci_b = go.Figure()
uci_b.add_trace(go.Bar(x=uci_plot.state, y=uci_plot.inpatient_beds, name='Camas UCI Totales', marker_color='indianred'))
uci_b.add_trace(go.Bar(x=uci_plot.state, y=uci_plot.inpatient_beds_used_covid,
                       name='Camas UCI COVID', marker_color='lightsalmon'))
uci_b.update_layout(barmode='group', xaxis_tickangle=-45,
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False))

# 6.
deaths = df2.groupby('state').apply(lambda x: x[x['date'].dt.year == 2021][['deaths_covid']].sum())
deaths.reset_index(inplace=True)
deaths.sort_values(by='deaths_covid', inplace=True)

death = px.bar(deaths, x='state', y='deaths_covid', color_discrete_sequence=px.colors.diverging.Spectral)
death.update_layout(title='Muertes COVID por estado 2021', xaxis_title='Estado',
                    yaxis_title='Muertes', xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=False))
death.update_xaxes(tickangle=-45)

# 7.
staff = df2.groupby('state').apply(
    lambda x: x[x['date'].dt.year == 2021][['critical_staffing_shortage_today_yes', 'deaths_covid']].sum())
staff2 = staff.copy()
staff2.reset_index(inplace=True)

sf = px.histogram(staff2, x='state', y=['critical_staffing_shortage_today_yes', 'deaths_covid'])
sf.update_layout(title='Muertes x Falta de Equipo 2021', xaxis_title='Estado',
                 yaxis_title='Muertes / Falta Equipo', xaxis=dict(showgrid=False),
                 yaxis=dict(showgrid=False), hovermode='x unified')
var2 = {'critical_staffing_shortage_today_yes': 'Camas Faltantes', 'deaths_covid': 'Muertes Covid'}
sf.for_each_trace(lambda t: t.update(name=var2[t.name], legendgroup=var2[t.name],
                                     hovertemplate=t.hovertemplate.replace(t.name, var2[t.name])))
sf.update_xaxes(tickangle=-45)

# 8.
worst_year = df2.groupby([df2.date.dt.year, df2.date.dt.month])[
    ['deaths_covid', 'critical_staffing_shortage_today_yes']].sum()
worst_year.reset_index(level=1, inplace=True)
worst_year.rename(columns={'date': 'month'}, inplace=True)
worst_year = worst_year.rename_axis('year', axis='index')
worst_month = worst_year.copy()
worst_month = worst_month.groupby('month').sum()
worst_month.rename(index=lambda x: calendar.month_abbr[x], inplace=True)

monthfig = go.Figure()
monthfig.add_trace(
    go.Bar(x=worst_month.index.values, y=worst_month.deaths_covid, name='Muertes', marker_color='crimson'))
monthfig.add_trace(
    go.Bar(x=worst_month.index.values, y=worst_month.critical_staffing_shortage_today_yes, name='Equipo Faltante',
           marker_color='coral'))
monthfig.update_layout(title='Muertes x Mes (Toda la pandemia)', xaxis_title='Mes',
                       yaxis_title='Muertes / Falta Equipo', barmode='group',
                       xaxis=dict(showgrid=False),
                       yaxis=dict(showgrid=False), hovermode='x unified')
# Interfaz Web #
st.title('Proyecto Individual #2')
st.caption('by Carlos Gaviria')
#####################################
st.markdown('1. ¿Cuáles fueron los 5 Estados con mayor ocupación hospitalaria por **_COVID_**?')
st.code('''s5m = df2.loc[df2['date'].dt.year == 2020]
s5m = s5m.groupby('state').apply(lambda x: x[x['month'] <= 6][
    ['inpatient_beds_used_covid', 'total_adult_patients_hospitalized_confirmed_covid', 'deaths_covid']].sum())
s5m = s5m.loc[s5m['inpatient_beds_used_covid'].nlargest(5).index]
dat_col = list(s5m.columns)
s5m = re_idx_name(s5m, dat_col, {'inpatient_beds_used_covid': 'Camas UCI COVID',
                                 'total_adult_patients_hospitalized_confirmed_covid': 'Adultos Hospitalizados',
                                 'deaths_covid': 'Muertes'})''',
        language='python')
st.dataframe(s5m)
st.caption('Siendo New York el mayor hasta el 2020-06-30 '
           'con un total de 686.528 camas usadas por covid positivos.')
#####################################
st.markdown('2. Ocupacion de camas Covid en el estado de New York')
st.code('''new_york = df2.sort_values(by='date')
new_york = new_york.loc[
    (new_york['date'] >= '2020-03-20') & (new_york['date'] <= '2021-06-15') & (new_york['state'] == 'NY')]
new_york.reset_index(drop=True, inplace=True)''', language='python')
st.plotly_chart(nyfig)
st.caption('El 14 de Abril del 2020 se presento el mayor uso de camas con un total de '
           '14.126 personas internadas con covid ese dia, adicional a 439 muertes.\n'
           'El uso de camas mas bajo se dio el dia 20 de Septiembre del 2020 '
           'con 1225 personas internadas ese dia y solamente 15 muertes.')
#####################################
st.markdown('3. Top 5 estados con mayor uso de camas UCI anio 2020')
st.code('''most_beds = df2.groupby('state').apply(lambda x: x[x['date'].dt.year == 2020][
    ['inpatient_beds', 'inpatient_beds_used', 'inpatient_beds_used_covid']].sum())
most_beds = most_beds.loc[most_beds['inpatient_beds_used'].nlargest(5).index]
most_beds.reset_index(inplace=True)
dat_col2 = list(most_beds.columns)
most_beds = re_idx_name(most_beds, dat_col2, {'state': 'Estado',
                                              'inpatient_beds': 'Camas UCI Disponibles',
                                              'inpatient_beds_used': 'Camas UCI Normal',
                                              'inpatient_beds_used_covid': 'Camas UCI COVID'})''', language='python')
st.plotly_chart(bedsfig)
st.caption('California lidera la lista con un total de 11.316.300 camas usadas durante el '
           'anio 2020, seguido de Texas con 11.073.678 camas usadas.')
#####################################
st.markdown('4. Estados con mayor uso de camas pediatricas anio 2020')
st.code('''kids_bed = df2.groupby('state').apply(
    lambda x: x[x['date'].dt.year == 2020][['total_pediatric_patients_hospitalized_confirmed_covid']].sum())
kids_bed.reset_index(inplace=True)
kids_bed.sort_values(by='total_pediatric_patients_hospitalized_confirmed_covid', ascending=False, inplace=True)''',
        language='python')
st.plotly_chart(kfig)
st.caption('Texas encabeza la lista con un total de 12.582 camas pediatricas usadas durante el '
           'anio 2020.')
#####################################
st.markdown('5. Porcentaje camas UCI por estados')
st.code('''uci_beds = df2.groupby('state')[['inpatient_beds', 'inpatient_beds_used_covid']].sum()
uci_beds['usage_percent'] = round((uci_beds['inpatient_beds_used_covid'] / uci_beds['inpatient_beds']) * 100, 2)
uci_beds.sort_values(by='usage_percent', ascending=False, inplace=True)''', language='python')
st.dataframe(uci_beds)
st.caption('El estado de Georgia presenta el mayor % de ocupacion por cama covid (11.42%) en relacion al '
           'total de camas disponibles en ese estado.')
st.plotly_chart(uci_b)
st.caption('De tal forma que en relacion  total/covid gana a pesar de que en Texas haya mas uso de camas UCI.')
#####################################
st.markdown('6. ¿Cuántas muertes por covid hubo, por Estado, durante el año 2021?')
st.code('''deaths = df2.groupby('state').apply(lambda x: x[x['date'].dt.year == 2021][['deaths_covid']].sum())
deaths.reset_index(inplace=True)
deaths.sort_values(by='deaths_covid', inplace=True)''', language='python')
st.plotly_chart(death)
st.caption('Se evidencia la asombrosa cantidad de 35.108 muertes en el estado de California durante el anio 2021, '
           'seguido muy de cerca por Texas con un total de 32.889 muertes en el estado.')
#####################################
st.markdown('7. Relacion muertes covid x falta de equipo')
st.code('''staff = df2.groupby('state').apply(
    lambda x: x[x['date'].dt.year == 2021][['critical_staffing_shortage_today_yes', 'deaths_covid']].sum())
staff2 = staff.copy()
staff2.reset_index(inplace=True)''', language='python')
st.plotly_chart(sf)
st.caption('Se puede observar un gran aumento de muertes con relacion a la falta de equipo(camas, personal, etc) '
           'durante el anio 2021.')
#####################################
st.markdown('8. Peor mes durante la pandemia COVID')
st.code('''worst_year = df2.groupby([df2.date.dt.year, df2.date.dt.month])[
    ['deaths_covid', 'critical_staffing_shortage_today_yes']].sum()
worst_year.reset_index(level=1, inplace=True)
worst_year.rename(columns={'date': 'month'}, inplace=True)
worst_year = worst_year.rename_axis('year', axis='index')
worst_month = worst_year.copy()
worst_month = worst_month.groupby('month').sum()
worst_month.rename(index=lambda x: calendar.month_abbr[x], inplace=True)''', language='python')
st.plotly_chart(monthfig)
st.caption('Se reporta Enero y Diciembre como los meses de peor crisis en relacion a muertes ocasionadas '
           'por la COVID-19.')
