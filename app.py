import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import boto3
from geopy.geocoders import Nominatim
import requests
import branca.colormap as cm

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace 'your-region' with your AWS region
table = dynamodb.Table('CityTemperatures')

# Function to get recent temperature data from DynamoDB
def get_recent_temperature_data():
    response = table.scan()
    items = response.get('Items', [])
    return pd.DataFrame(items)

# Function to get user location based on IP address
def get_user_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        return data['loc'].split(','), data['city']
    except Exception as e:
        st.error("Could not get user location.")
        return None, None

# Function to get weather data for a given latitude and longitude
def get_weather_data(lat, lon, api_key):
    weather_url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}"
    response = requests.get(weather_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Could not fetch weather data.")
        return None

# Title of the Streamlit app
st.title('Real-time Weather Visualization')

# Get user location
user_location, user_city = get_user_location()

if user_location:
    user_lat, user_lon = float(user_location[0]), float(user_location[1])

    # Display the weather conditions for the user's location
    weather_api_key = '766cd03fff0a4e5781192438243105'  # Replace with your actual WeatherAPI key
    weather_data = get_weather_data(user_lat, user_lon, weather_api_key)
    
    if weather_data:
        weather_details = {
            "Temperature": f"{weather_data['current']['temp_c']}°C",
            "Humidity": f"{weather_data['current']['humidity']}%",
            "Wind Speed": f"{weather_data['current']['wind_kph']} kph",
            "Precipitation": f"{weather_data['current']['precip_mm']} mm",
            "Condition": weather_data['current']['condition']['text'],
            "Observation Time": weather_data['current']['last_updated']
        }
        st.markdown(f"""
        <div style="padding: 10px; border-radius: 5px; background-color: #f0f0f0;">
            <h3 style="color: #333;">Your Location</h3>
            <p><strong>Latitude:</strong> {user_lat}, <strong>Longitude:</strong> {user_lon}</p>
            <p><strong>City:</strong> {user_city}</p>
            <h3 style="color: #333;">Current Weather Conditions</h3>
            <p><strong>Temperature:</strong> {weather_details['Temperature']}</p>
            <p><strong>Humidity:</strong> {weather_details['Humidity']}</p>
            <p><strong>Wind Speed:</strong> {weather_details['Wind Speed']}</p>
            <p><strong>Precipitation:</strong> {weather_details['Precipitation']}</p>
            <p><strong>Condition:</strong> {weather_details['Condition']}</p>
            <p><strong>Observation Time:</strong> {weather_details['Observation Time']}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.error("Unable to determine your location.")

# Get the latest temperature data from DynamoDB
temperature_data = get_recent_temperature_data()

temperature_data['Temperature'] = temperature_data['Temperature'].astype(float)
temperature_data['WindSpeed'] = temperature_data['WindSpeed'].astype(float)
temperature_data['Rain'] = temperature_data['Rain'].astype(float)
temperature_data['Humidity'] = temperature_data['Humidity'].astype(float)

# Temperature filter slider
min_temp = float(temperature_data['Temperature'].min())
max_temp = float(temperature_data['Temperature'].max())
selected_temp_range = st.slider('Select temperature range:', min_temp, max_temp, (min_temp, max_temp))

# Filter the temperature data based on the selected range
filtered_temperature_data = temperature_data[
    (temperature_data['Temperature'] >= selected_temp_range[0]) &
    (temperature_data['Temperature'] <= selected_temp_range[1])
]

# Create a map centered on Europe
m = folium.Map(location=[54.5260, 15.2551], zoom_start=4)

# Add user location marker to the map
if user_location:
    folium.Marker(
        location=[user_lat, user_lon],
        popup='Your Location',
        icon=folium.Icon(color='red')
    ).add_to(m)

# Create a list of heatmap data
heat_data = [[row['Latitude'], row['Longitude'], row['Temperature']] for index, row in filtered_temperature_data.iterrows()]

# Create a colormap
colormap = cm.LinearColormap(
    colors=['blue', 'cyan', 'lime', 'yellow', 'orange', 'red'],
    vmin=min_temp,
    vmax=max_temp
)
colormap = colormap.to_step(index=[min_temp, -10, 0, 10, 20, 30, max_temp])
colormap.caption = 'Temperature (°C)'

# Add the heatmap to the map
HeatMap(
    heat_data,
    min_opacity=0.2,
    max_zoom=18,
    max_intensity=max_temp,
    gradient={0.0: 'blue', 0.2: 'cyan', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
).add_to(m)

# Add the colormap to the map
colormap.add_to(m)

# Display the map in Streamlit
folium_static(m)


# City selection for recent temperature check
selected_city = st.selectbox('Select a city to see recent temperature:', temperature_data['City'])

if selected_city:
    recent_temp = temperature_data[temperature_data['City'] == selected_city]['Temperature'].values[0]
    st.write(f'The recent temperature in {selected_city} is {recent_temp}°C.')



#Add Rain Data

# Rain filter slider
min_rain = float(temperature_data['Rain'].min())
max_rain = float(temperature_data['Rain'].max())
selected_rain_range = st.slider('Select rain range:', min_rain, max_rain, (min_rain, max_rain))

# Filter the temperature data based on the selected range
filtered_rain_data = temperature_data[
    (temperature_data['Rain'] >= selected_rain_range[0]) &
    (temperature_data['Rain'] <= selected_rain_range[1])
]

# Create a map centered on Europe
m = folium.Map(location=[54.5260, 15.2551], zoom_start=4)

# Add user location marker to the map
if user_location:
    folium.Marker(
        location=[user_lat, user_lon],
        popup='Your Location',
        icon=folium.Icon(color='red')
    ).add_to(m)

# Create a list of heatmap data
rain_data = [[row['Latitude'], row['Longitude'], row['Rain']] for index, row in filtered_rain_data.iterrows()]


# create a colormap for the rain intensity
rain_colormap = cm.LinearColormap(
    colors=['lightblue', 'blue', 'darkblue'],
    vmin=min_rain,
    vmax=max_rain
)

#be careful for float division zero
if max_rain == 0:
    max_rain = 1

rain_colormap = rain_colormap.to_step(index=[min_rain, max_rain/2, max_rain])


rain_colormap.caption = 'Rain (mm)'
# Add the heatmap to the map
HeatMap(
    rain_data,
    min_opacity=0.2,
    max_zoom=18,
    max_intensity=max_rain,
    gradient={0.0: 'lightblue', 0.5: 'blue', 1.0: 'darkblue'}
).add_to(m)


# Add the colormap to the map
rain_colormap.add_to(m)

# Display the map in Streamlit
folium_static(m)


# City selection for recent rain check
selected_city = st.selectbox('Select a city to see recent rain:', temperature_data['City'])

if selected_city:
    recent_rain = temperature_data[temperature_data['City'] == selected_city]['Rain'].values[0]
    st.write(f'The recent rain in {selected_city} is {recent_rain} mm.')