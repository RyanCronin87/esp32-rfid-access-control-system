from sense_hat import SenseHat
import sqlite3
import time

sense = SenseHat()

while True:

    temp = sense.get_temperature()
    humidity = sense.get_humidity()
    pressure = sense.get_pressure()

    conn = sqlite3.connect("sensehat.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sensor_data (temperature, humidity, pressure)
    VALUES (?, ?, ?)
    """, (temp, humidity, pressure))

    conn.commit()
    conn.close()

    print("Stored:", temp, humidity, pressure)

    time.sleep(10)
