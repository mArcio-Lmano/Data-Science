from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from datetime import timedelta, datetime, timezone
import json
import pandas as pd

import pytz

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 4, 20),
    "email": ["marcio.mano2322@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def transform_data(**kwargs):
    def convertKelvin(temperature):
        kelvinConstant = -273.15
        return round(temperature + kelvinConstant, 2)

    def convertToMachineUTC(date):
        date = datetime.fromisoformat(date)
        local_tz = pytz.timezone("Europe/Lisbon")
        now_local = pytz.utc.localize(date).astimezone(local_tz)
        return now_local

    task_instance = kwargs["ti"]
    info = task_instance.xcom_pull(task_ids="extract_weather")
    city = info["name"]
    date = convertToMachineUTC(
        datetime.fromtimestamp(info["dt"], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )
    temperature_info = info["main"]
    min_temperature = convertKelvin(temperature_info["temp_min"])
    max_temperature = convertKelvin(temperature_info["temp_max"])
    humidity = temperature_info["humidity"]

    weather_info = info["weather"][0]
    weather = weather_info["main"]
    weather_description = weather_info["description"]

    clouds = info["clouds"]["all"]

    wind_info = info["wind"]
    wind_speed = wind_info["speed"]
    wind_deg = wind_info["deg"]

    sunrise = convertToMachineUTC(
        datetime.fromtimestamp(info["sys"]["sunrise"], timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    sunset = convertToMachineUTC(
        datetime.fromtimestamp(info["sys"]["sunset"], timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    transformed_weather = {
        "city": city,
        "date": date,
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
        "humidity": humidity,
        "weather": weather,
        "weather_description": weather_description,
        "clouds": clouds,
        "wind_speed": wind_speed,
        "wind_deg": wind_deg,
        "sunrise": sunrise,
        "sunset": sunset,
    }

    df = pd.DataFrame([transformed_weather])
    df.to_csv(f"s3://manosweatherbucket/Weather_porto_{date}.csv", index=False)


with DAG(
    "weather_dag",
    default_args=default_args,
    description="Check weather for Porto daily",
    schedule="@daily",
    catchup=False,
) as dag:

    api_key_conn_id = "openweathermap_api"

    city_name = "Porto"
    # with open("api.key", "r") as file:
    #     api_key = file.read()
    api_key = "a3d23475d1415dd9e8b765d7efe21473"

    url = f"/data/2.5/weather?q={city_name}&appid={api_key}"

    weather_api_working = HttpSensor(
        task_id="weather_sensor", http_conn_id=api_key_conn_id, endpoint=url
    )

    extract_weather = SimpleHttpOperator(
        task_id="extract_weather",
        http_conn_id=api_key_conn_id,
        endpoint=url,
        method="GET",
        response_filter=lambda r: json.loads(r.text),
        log_response=True,
    )

    transforme_weather = PythonOperator(
        task_id="transforme_weather",
        python_callable=transform_data,
        provide_context=True,
    )

    weather_api_working >> extract_weather >> transforme_weather
