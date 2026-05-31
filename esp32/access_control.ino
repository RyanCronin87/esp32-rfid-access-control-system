// ESP32 RFID Access Control System
// Features:
// - RFID authentication
// - OLED display feedback
// - WiFi HTTP requests
// - Raspberry Pi integration
// - Access control token generation


#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>

// ---------------- WIFI ----------------
const char* ssid = "WIFI_SSID";
const char* password = "WIFI_PASSWORD";

// ---------------- RFID ----------------
#define SS_PIN 5
#define RST_PIN 27
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ---------------- OLED ----------------
#define OLED_SDA 21
#define OLED_SCL 22
#define i2c_Address 0x3C
Adafruit_SH1106G display(128, 64, &Wire, -1);

// ---------------- AUTHORISED CARDS ----------------
struct Card {
  String uid;
  String name;
};

Card authorisedCards[] = {
  {"22c6f939", "Ryan"},
  {"66752d43", "Cormac"}
};

const int NUM_CARDS = sizeof(authorisedCards) / sizeof(authorisedCards[0]);
// ---------------- SETUP ----------------
void setup() {
  Serial.begin(115200);

  // WiFi connect
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // OLED setup
  Wire.begin(OLED_SDA, OLED_SCL);
  display.begin(i2c_Address, true);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);

  // RFID setup
  SPI.begin();
  mfrc522.PCD_Init();

  displayMessage("Scan Card...");
}

// ---------------- MAIN LOOP ----------------
void loop() {

  // Wait for card
  if (!mfrc522.PICC_IsNewCardPresent()) return;
  if (!mfrc522.PICC_ReadCardSerial()) return;

  // Read UID
  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) uid += "0";
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }

  Serial.print("UID: ");
  Serial.println(uid);
  delay(1000);

  String name;

  // ---------------- ACCESS CONTROL ----------------
  if (isAuthorised(uid, name)) {

    Serial.println("Access granted to: " + name);

    displayMessage("Welcome " + name);
    delay(1000);

    // ---------------- HTTP REQUEST ----------------
    HTTPClient http;
    http.begin("http://raspberrypi.local:5000/grant");
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST("");

    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("TOKEN:");
      Serial.println(response);

      // Extract token from JSON
      String token = response.substring(response.indexOf(":\"") + 2);
      token.remove(token.length() - 2);

      displayMessage("Token:\n" + token);

    } else {
      Serial.println("HTTP Error");
      displayMessage("Error");
    }

    http.end();

    delay(10000);  // wait 10 seconds so user can read token

    displayMessage("Scan Card...");

// reset RFID so it can scan again
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();

    delay(1000); 
  }

  else {
    displayMessage("Access Denied");
    delay(2000);
    displayMessage("Scan Card...");
  }
}

// ---------------- AUTHORISATION FUNCTION ----------------
bool isAuthorised(String uid, String &name) {
  for (int i = 0; i < NUM_CARDS; i++) {
    if (uid == authorisedCards[i].uid) {
      name = authorisedCards[i].name;
      return true;
    }
  }
  return false;
}

// ---------------- OLED FUNCTION ----------------
void displayMessage(String message) {
  display.clearDisplay();
  display.setCursor(0, 20);
  display.println(message);
  display.display();
}
