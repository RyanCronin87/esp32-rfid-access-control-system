from flask import Flask, jsonify, request
import sqlite3
import time
import secrets

current_token = None
token_expiry = 0

app = Flask(__name__)

@app.route("/")
def dashboard():

    token = request.args.get("token")

    if token != current_token or time.time() > token_expiry:
        return '<a href="/login">Access Denied - Click here to login</a>'


    return """
    <html>
    <head>
        <title>Sensor Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>

        <h1>Sensor Dashboard</h1>

        <h2>Current Values</h2>
        <p id="temp"></p>
        <p id="humidity"></p>
        <p id="pressure"></p>

        <h2>Temperature</h2>
        <canvas id="tempChart"></canvas>

        <h2>Humidity</h2>
        <canvas id="humidityChart"></canvas>

        <h2>Pressure</h2>
        <canvas id="pressureChart"></canvas>

        <script>
        let tempChart, humidityChart, pressureChart;

        async function loadData() {
            const scrollPos = window.scrollY;

            const token = new URLSearchParams(window.location.search).get("token");
            const response = await fetch('/readings?token=' + token);

            if (!response.ok) {
                alert("Session expired - please log in again");
                window.location.href = "/login";
                return;
            }

            const data = await response.json();


            if (!data || data.length === 0) return;

            const labels = data.map(d => d.timestamp).reverse();
            const temps = data.map(d => d.temperature).reverse();
            const humidity = data.map(d => d.humidity).reverse();
            const pressure = data.map(d => d.pressure).reverse();

            // Update current values
            const latest = data[0];
            document.getElementById("temp").innerText = "Temperature: " + latest.temperature.toFixed(1) + "°C";
            document.getElementById("humidity").innerText = "Humidity: " + Math.round(latest.humidity) + "%";
            document.getElementById("pressure").innerText = "Pressure: " + Math.round(latest.pressure) + " hPa";

            // Destroy old charts if they exist
            if (tempChart) tempChart.destroy();
            if (humidityChart) humidityChart.destroy();
            if (pressureChart) pressureChart.destroy();

            // Temperature chart
            tempChart = new Chart(document.getElementById("tempChart"), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Temperature',
                        data: temps
                    }]
                }
            });

            // Humidity chart
            humidityChart = new Chart(document.getElementById("humidityChart"), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Humidity',
                        data: humidity
                    }]
                }
            });

            // Pressure chart
            pressureChart = new Chart(document.getElementById("pressureChart"), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Pressure',
                        data: pressure
                    }]
                }
            });

            window.scrollTo(0, scrollPos);
        }

        loadData();
        setInterval(loadData, 5000); // refresh every 5 seconds
        </script>

    </body>
    </html>
    """
    #conn = sqlite3.connect("sensehat.db")
    #cursor = conn.cursor()

    #cursor.execute("""
    #SELECT temperature, humidity, pressure, timestamp
    #FROM sensor_data
    #ORDER BY id DESC
    #LIMIT 10
    #""")

    #rows = cursor.fetchall()
    #conn.close()

    #html = "<h1>Sense HAT Dashboard</h1>"
    #html += "<table border='1'>"
    #html += "<tr><th>Temperature</th><th>Humidity</th><th>Pressure</th><th>Time</th></tr>"

    #for r in rows:
        #html += f"<tr><td>{r[0]:.2f}</td><td>{r[1]:.2f}</td><td>{r[2]:.2f}</td><td>{r[3]}</td></tr>"

    #html += "</table>"

    #return html


@app.route("/readings")
def readings():

    token = request.args.get("token")

    if token != current_token or time.time() > token_expiry:
        return jsonify({"error": "unauthorized"}), 403
    conn = sqlite3.connect("sensehat.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT temperature, humidity, pressure, timestamp
    FROM sensor_data
    ORDER BY id DESC
    LIMIT 500
    """)

    rows = cursor.fetchall()
    conn.close()

    data = []

    for r in rows:
        data.append({
            "temperature": r[0],
            "humidity": r[1],
            "pressure": r[2],
            "timestamp": r[3]
        })

    return jsonify(data)

@app.route("/test")
def test():
    return jsonify({"message": "Pi is working"})

@app.route("/grant", methods=["POST"])
def grant():
    global current_token, token_expiry

    current_token = secrets.token_hex(2)
    token_expiry = time.time() + 120  # 2 mins

    return jsonify({"token": current_token})

@app.route("/login")
def login():
    return """
    <h2>Enter Access Token</h2>
    <input id="token" placeholder="Enter token">
    <button onclick="go()">Access Dashboard</button>

    <script>
    function go() {
        const token = document.getElementById("token").value;
        window.location.href = "/?token=" + token;
    }
    </script>
    """

if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5000)
