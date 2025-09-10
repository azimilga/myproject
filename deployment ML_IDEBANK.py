import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from dotenv import load_dotenv
import os
import psycopg2
import joblib, pickle
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# # Load environment variables
dotenv_path = 'C:/Users/azga/env'
load_dotenv(dotenv_path)

# # Load environment variables
server_group_name = os.getenv('SERVER_GROUP_NAME')
server_name = os.getenv('SERVER_NAME')
local_hostname = os.getenv('LOCAL_HOSTNAME')
user_name = os.getenv('USER_NAME')
pass_name = os.getenv('PASS_NAME')
database_name = os.getenv('DATABASE_NAME')
port_no = os.getenv('PORT_NO')
table_name = os.getenv('TABLE_NAME')

# SET COLUMNS' NAMES of the dataframe
number_id    = 'id'
building_col = 'building_id'
room_col     = 'room_id'
time_data    = 'measured_date'
manuf_col    = 'manuf_id'
instr_col    = 'instrument_id'
serial_col   = 'serial_id'
dtype_col    = 'datatype_id'
value_data   = 'data_value'

Laptop_directory = 'G:/My Drive/'       #NILU
# Laptop_directory =  'C:/Users/azimilga/My Drive/'    #NTNU
ML_directory = Laptop_directory + 'Colab Notebooks/Project/data-ready/all years/all schools/export/ML/regression w-o/'
ML_directory_symptom = Laptop_directory + 'Colab Notebooks/Project/data-ready/all years/brannfjell/export/ML/regression/'
with open(ML_directory + "10min_brannfjell_all years_rd_air_model_RFR.pkl","rb") as file1:
    ML_air = pickle.load(file1)
with open(ML_directory + "10min_brannfjell_all years_rd_temp_model_RFR.pkl","rb") as file2:
    ML_temp = pickle.load(file2)
with open(ML_directory_symptom + "10min_brannfjell_all years_health_head_model_RFR.pkl","rb") as file3:
    ML_health_head = pickle.load(file3)
with open(ML_directory_symptom + "10min_brannfjell_all years_health_tired_model_RFR.pkl","rb") as file4:
    ML_health_tired = pickle.load(file4)
# Sample DataFrame (replace this with your actual data)
folder_url  = 'C:/Users/azga/OneDrive - NTNU/Work/MIN SKOLE - 2022/Idebank/'      #NILU
# folder_url  = 'C:/Users/azimilga/OneDrive - NTNU/Work/MIN SKOLE - 2022/Idebank/'    #NTNU
matrix_hot  = pd.read_excel(folder_url + 'idebank_brannfjell.xlsx', sheet_name='too hot' ) #.astype(str)
matrix_cold = pd.read_excel(folder_url + 'idebank_brannfjell.xlsx', sheet_name='too cold' ) #.astype(str)
matrix_vent = pd.read_excel(folder_url + 'idebank_brannfjell.xlsx', sheet_name='ventilation' ) #.astype(str)

# Define basic variables
value_temp_out = 10
value_rh_out = 50
value_sun_out = 100
time_hour_now = pd.Timestamp.now().hour
time_month_now = pd.Timestamp.now().month
datetime_now = pd.Timestamp.now().strftime("%H:%M, %A %d %B %Y")
occupation_time = time_hour_now - 6


# DEFINING IDEBANK LOGIC
def determine_category_hot(t_value_1, t_value_2, t_value_3, rd_temp_11, temp_hot, temp_heater, value_temp_out, value_bright_sun, time_hour_now):
    # Step 1: Check rd_air_11 value
    if rd_temp_11 < 25:
        return 0
    else:
        # Step 2: Check if all three t_values are < 19
        if min(t_value_1 , t_value_2 , t_value_3) > 25:
            return 6
        else:
            if t_value_1 > 24:
                if value_temp_out > 5 :
                    if time_hour_now < 9:
                        return 4
                    else :
                        return 3
                else:
                    return 3
            else:
                if t_value_1 > 23 :
                    if value_temp_out < 5:
                        return 1
                    else:
                        if value_bright_sun > 1 :
                            return 2
                        else:
                            return 3
                else:
                    if t_value_1 >22:
                        if value_temp_out > 12:
                            return 5
                        else:
                            return 4
                    else:
                        if t_value_1 < 22 :
                            if temp_heater > 1:
                                return 8
                            else : 
                                if temp_hot > 1:
                                    return 7
                                else : 
                                    return 0
                        else:
                            return 0

def determine_category_cold(t_value_1, t_value_2, t_value_3, out_temp_now, c_value_1, rd_temp_11, temp_draw, too_cold, temp_heater, time_hour_now):
    if rd_temp_11 < 25:
        return 0
    else:
        if max(t_value_1 , t_value_2 , t_value_3) < 19:
            return 4
        else:
            if t_value_1 < 20 :
                if time_hour_now <= 8:
                    return 1
                else:
                    if out_temp_now <= (-5):
                        return 8
                    else:
                        return 6
            else:
                if t_value_1 <21 :
                    if temp_heater > 1:
                        return 9
                    else:
                        if temp_draw >1:
                            if too_cold > 1:
                                return 2
                            else:
                                return 5
                        return 9
                if t_value_1 <= 22:
                    if too_cold > 1:
                        return 3
                    else:
                        if c_value_1 > 800:
                            return 7
                        else:
                            return 9
                else:
                    return 0
                        
def determine_category_vent ( c_value_1, rd_air_11, air_smell, air_heavy, time_month_now):
    if rd_air_11 <25:
        return 0
    else:
        if air_heavy > 1 :
            if c_value_1 >= 900 :
                return 3
            else:
                return 2
        else:
            if c_value_1 >=900:
                return 1
            else:
                if time_month_now >4 and time_month_now < 10 :
                    return 4
                else:
                    if air_smell > 1 :
                        return 5
                    else:
                        return 1

#Layout of Text Display        
def sub_displaying_result(result_, icon, theme_text ):
    if result_['category']==0:
        st.subheader(icon + "no issue about" + theme_text + 'in this room ' + str(selected_room) )
    else:
        # Display results for Cold Room
        st.subheader(icon + theme_text +"Issue Report, Room: "+ str(selected_room))
        st.markdown(f"**Problem we may have:** {str(result_['problem'])}")
        st.markdown(f"**Suggestion to apply:** {str(result_['suggestion'])}")
        st.markdown(f"**Consequence of this problem:** {str(result_['consequence'])}")
        st.markdown(f"**Benefit of this suggestion:** {str(result_['benefit'])}")
        st.write(" ")

#Layout of Text Display
def displaying_result (result_hot,result_cold, result_vent):
    # Display reports
    sub_displaying_result(result_hot, ' 🔥 ', ' Room Hot ' )
    sub_displaying_result(result_cold, ' ❄️ ', ' Room Cold ' )
    sub_displaying_result(result_vent, ' 𖣘 ', ' Room Ventilation ' )


room_id_ref = {'name': ['142', '141','221', '222', '223','224', '225', '226' , '227','228', '331', '332', '333', '334', '335', '336',np.nan, np.nan, np.nan,  np.nan, np.nan,  ], #sql room.identification, select id
               'room': [11 , 12, 21, 22, 23, 24, 25, 26, 27, 28,31, 32, 33, 34, 35, 36,     37, 38, 39, 20, 29 ],
                'id' : [47, 53,  57, 64, 36, 63, 52, 67, 37, 65, 38, 56, 66, 60, 68, 58,    62, 55, 61,54, 59 ]}

room_protokoll = {'room': [11 , 12, 21, 22, 23, 24, 25, 26, 27, 28,31, 32, 33, 34, 35, 36,     37, 38, 39, 20, 29 ],
                  'floor_first' : [1, 1,  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,    0, 0, 0,0, 0 ],
                 'west_window' : [0, 0,  0, 0, 0, 0, 0, 0, 0.24, 0.24, 0, 0, 0, 0.24, 0.24, 0.24,    0, 0, 0,0, 0 ],
                 'east_window' : [0.22, 0.22,  0.22, 0.22, 0.22, 0.22, 0.22, 0.22, 0, 0, 0.22, 0.22, 0.22, 0, 0, 0,    0, 0, 0,0, 0],
                 }

room_mapping = {
    room_protokoll['room'][i]: {
        'floor_first': room_protokoll['floor_first'][i],
        'west_window': room_protokoll['west_window'][i],
        'east_window': room_protokoll['east_window'][i],
    }
    for i in range(len(room_protokoll['room']))
}

room_id_ref = pd.DataFrame(room_id_ref).dropna()
room_to_id_map = dict(zip(room_id_ref['id'], room_id_ref['room']))  #translating from id number in SQL : become Room Number
selected_classroom = [11, 23, 26, 27, 34]

# Load SQL data
try:
    conn = psycopg2.connect(
        user=user_name,
        password=pass_name,
        host=local_hostname,
        port=port_no,
        database=database_name,
        connect_timeout=10
    )
    cursor = conn.cursor()
    print('database connected')
    query = f"""
        SELECT measured_date, room_id, datatype_id, data_value FROM {table_name}
        WHERE measured_date BETWEEN (CURRENT_DATE - INTERVAL '1 day') AND (CURRENT_DATE + INTERVAL '1 day' - INTERVAL '1 second');
    """
    df_sql = pd.read_sql(query, conn)

except Exception as e:
    # st.error(f"Error fetching data from PostgreSQL: {e}")
    print('error')
    df_sql = pd.DataFrame()  # Return an empty dataframe if there's an error
finally:
    # Ensure the connection is closed after the query is executed
    if 'conn' in locals() and conn is not None:
        cursor.close()
        conn.close()
        # st.info("Database connection closed.")
        print('database closed')

# Transform data into a structured format
# df_sql.to_csv(Laptop_directory+'sql file.csv')
# df_sql = pd.read_csv(Laptop_directory+'sql file.csv')

df_sql[time_data] = pd.to_datetime(df_sql[time_data])
df_sql[room_col] = df_sql[room_col].map(room_to_id_map)
df_sql = df_sql [df_sql[room_col].isin(selected_classroom)] 

df_sql_co2 = df_sql[df_sql['datatype_id'] == 4].pivot_table(index='measured_date', columns='room_id', values='data_value', aggfunc='mean')
df_sql_temp = df_sql[df_sql['datatype_id'] == 1].pivot_table(index='measured_date', columns='room_id', values='data_value', aggfunc='mean')

# Plotting functions
def plot_co2_data(df):
    fig = px.line(df, labels={'value': 'indoor CO₂ (ppm)', time_data: 'Time'})
    fig.update_layout(yaxis_range=[350, 1250], yaxis_dtick=100)
    st.plotly_chart(fig)
def plot_temp_data(df):
    fig = px.line(df, labels={'value': 'indoor Temperature (°C)', time_data: 'Time'})
    fig.update_layout(yaxis_range=[16, 30], yaxis_dtick=1)
    st.plotly_chart(fig)

# Streamlit dashboard
title_test = "Bruker-orientert Forvaltningssystem"

st.title(title_test)
st.subheader("(Internally for testing only)")
st.header("Brannfjell Skole, Oslo")
st.write( str(datetime_now))

# Plot CO2 and Temperature
st.subheader("CO₂ Levels in All Classrooms")
plot_co2_data(df_sql_co2)

st.subheader("Temperature in All Classrooms")
plot_temp_data(df_sql_temp)

# Select room for prediction
selected_room = st.selectbox("Select a Room Number", options=selected_classroom)
temp_value = df_sql_temp[selected_room].iloc[-1]
co2_value = df_sql_co2[selected_room].iloc[-1]
unselected_room = [room for room in selected_classroom if room != selected_room]

room_attributes = room_mapping[selected_room]
   

# Predict using ML models
rd_air = ML_air.predict([[temp_value, co2_value, value_temp_out, value_rh_out, value_sun_out, occupation_time]]).round(3) * 100
rd_temp = ML_temp.predict([[temp_value, co2_value, value_temp_out, value_rh_out, value_sun_out]]).round(3) * 100

# Get user input for complaints
too_hot_value = 1 if st.radio("Is the room too hot?", ['Yes', 'No']) == 'Yes' else 0
too_cold_value = 1 if st.radio("Is the room too cold?", ['Yes', 'No']) == 'Yes' else 0
temp_draw_value = 1 if st.radio("Is there a draft?", ['Yes', 'No']) == 'Yes' else 0
air_dry_value = 1 if st.radio("Is the air so dry?", ['Yes', 'No']) == 'Yes' else 0
air_dust_value = 1 if st.radio("Is the air dusty?", ['Yes', 'No']) == 'Yes' else 0
air_heavy_value = 1 if st.radio("Is the air heavy?", ['Yes', 'No']) == 'Yes' else 0
air_smell_value = 1 if st.radio("Is there an odor?", ['Yes', 'No']) == 'Yes' else 0
cold_floor_value = 1 if st.radio("is floor so cold?", ['Yes', 'No']) == 'Yes' else 0
temp_heater_value = 1 if st.radio("is radiator / heater too much?", ['Yes', 'No']) == 'Yes' else 0
value_bright_sun = 1 if st.radio("Too much light from Sun?", ['Yes', 'No']) == 'Yes' else 0
value_bright_lamp = 1 if st.radio("Too much light from Lamp?", ['Yes', 'No']) == 'Yes' else 0
west_window_value = room_attributes['west_window']
east_window_value = room_attributes['east_window']
floor_value = room_attributes['floor_first']

# Predict using ML models
health_head = ML_health_head.predict([[temp_value, co2_value, air_dust_value, air_heavy_value, air_dry_value, air_smell_value, value_bright_lamp, cold_floor_value, temp_draw_value, temp_heater_value, west_window_value, east_window_value, floor_value, too_cold_value, too_hot_value ]]).round(0)
health_tired = ML_health_tired.predict([[temp_value, co2_value, air_dust_value, air_heavy_value, air_dry_value, air_smell_value, value_bright_lamp, cold_floor_value, temp_draw_value, temp_heater_value, west_window_value, east_window_value, floor_value, too_cold_value, too_hot_value]]).round(0)

st.write("Probability of Satisfaction (%)")
st.success("Thermal Comfort : {}".format(  (100 - rd_temp)  ))
st.success("IAQ             : {}".format(  (100 - rd_air)  ))

st.write("Prevalence Symptoms Probability (%) ")
st.success("Headache        : {}".format( health_head ))
st.success("Tiredness       : {}".format(  health_tired ))


# Determine categories based on logic
category_hot    = determine_category_hot(temp_value,df_sql_temp[unselected_room[0]].iloc[-1],df_sql_temp[unselected_room[1]].iloc[-1], rd_temp,
                                         too_hot_value, temp_heater_value, value_temp_out, value_bright_sun, time_hour_now )
category_cold   = determine_category_cold(temp_value,df_sql_temp[unselected_room[0]].iloc[-1],df_sql_temp[unselected_room[1]].iloc[-1], value_temp_out,
                                          co2_value,rd_temp,temp_draw_value, too_cold_value, temp_heater_value , time_hour_now)
category_vent   = determine_category_vent( co2_value, rd_air, air_smell_value, air_heavy_value, time_month_now)

result_hot = matrix_hot[matrix_hot['category'] == category_hot].iloc[0]
result_cold = matrix_cold[matrix_cold['category'] == category_cold].iloc[0]
result_vent = matrix_vent[matrix_vent['category'] == category_vent].iloc[0]

displaying_result (result_hot,result_cold, result_vent)

#"💧🔥❄️𖣘"