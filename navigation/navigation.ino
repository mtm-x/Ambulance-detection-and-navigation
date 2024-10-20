#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <ESP8266WiFi.h>

TinyGPSPlus gps;  // The TinyGPS++ object
SoftwareSerial ss(4, 5); // The serial connection to the GPS device

const char* ssid = "Redmi Note 11 Pro+ 5G";
const char* password = "asdfghjkl";

float latitude, longitude;
int year, month, date, hour, minute, second;
String date_str, time_str, lat_str, lng_str;
int pm;

WiFiServer server(80);

void setup() {
  Serial.begin(115200);
  ss.begin(9600);

  // Connecting to WiFi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  server.begin();
  Serial.println("Server started");
  Serial.println(WiFi.localIP());
}

void loop() {
  while (ss.available() > 0) {
    if (gps.encode(ss.read())) {
      if (gps.location.isValid()) {
        latitude = gps.location.lat();
        lat_str = String(latitude, 6);  // Converting float to string
        longitude = gps.location.lng();
        lng_str = String(longitude, 6); // Converting float to string
      }

      if (gps.date.isValid()) {
        date_str = "";
        date = gps.date.day();
        month = gps.date.month();
        year = gps.date.year();

        if (date < 10)
          date_str = '0';
        date_str += String(date) + " / ";

        if (month < 10)
          date_str += '0';
        date_str += String(month) + " / ";

        date_str += String(year);
      }

      if (gps.time.isValid()) {
        time_str = "";
        hour = gps.time.hour();
        minute = gps.time.minute();
        second = gps.time.second();

        minute = (minute + 30);
        if (minute > 59) {
          minute -= 60;
          hour += 1;
        }
        hour = (hour + 5);
        if (hour > 23)
          hour -= 24;

        pm = (hour >= 12) ? 1 : 0;
        hour %= 12;

        if (hour < 10)
          time_str = '0';
        time_str += String(hour) + " : ";

        if (minute < 10)
          time_str += '0';
        time_str += String(minute) + " : ";

        if (second < 10)
          time_str += '0';
        time_str += String(second);

        time_str += (pm == 1) ? " PM " : " AM ";
      }
    }
  }

  WiFiClient client = server.available();
  if (!client) {
    return;
  }

  // HTML content with blue theme and equal-sized buttons
  String s = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n";
  s += "<!DOCTYPE html> <html> <head> <title>Ambulance Navigation</title>";
  s += "<style>";
  s += "@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;700&display=swap');";  // Importing Poppins Font
  s += "body { font-family: 'Poppins', sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: linear-gradient(135deg, #5b86e5, #36d1dc); color: #fff; }";  // Updated blue gradient background
  
  // Title with blue text
  s += "h1.title { font-size: 48px; font-weight: 900; text-transform: uppercase; letter-spacing: 5px; margin-bottom: 20px; font-family: 'Poppins', sans-serif; color: #fff; background: rgba(0,123,255,0.9); padding: 10px 20px; border-radius: 5px; }";
  
  s += "h2 { font-size: 36px; margin-bottom: 20px; font-weight: 700; color: #fff; }";
  
  // Table styling with blue accents
  s += "table { border-collapse: collapse; width: 60%; background: rgba(255, 255, 255, 0.9); border-radius: 10px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); margin-bottom: 20px; }";
  s += "th, td { padding: 20px; text-align: center; border: 1px solid #ddd; font-size: 18px; color: #333; }";
  s += "th { background-color: #007BFF; color: white; font-size: 20px; font-weight: 500; }";
  s += "td { background-color: #f8f9fa; }";
  
  // Buttons equal size and blue styling
  s += ".button-container { display: flex; flex-direction: column; align-items: center; }";
  s += "a { display: inline-block; width: 250px; text-align: center; background-color: #007BFF; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 10px; transition: background-color 0.3s, transform 0.3s; font-size: 18px; font-weight: 500; }";
  s += "a:hover { background-color: #0056b3; transform: scale(1.05); }";  // Hover effect
  
  // Style for About Us section with blue accents
  s += ".about-us { margin-top: 30px; padding: 20px; background-color: rgba(0,123,255,0.9); border-radius: 10px; text-align: center; font-size: 18px; color: #fff; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2); }";
  s += "</style> </head> <body>";

  // Adding the "Techy Freakz" title above the Ambulance Location Tracker
  s += "<h1 class=\"title\">TECHY FREAKZ</h1>";
  s += "<h2>Ambulance Location Tracker</h2>";  // Moved this below the Techy Freakz title

  s += "<p style=\"font-size: 24px; margin-bottom: 30px;\"><b>Location Details</b></p>";
  s += "<table>";
  s += "<tr><th>Latitude</th><td>" + lat_str + "</td></tr>";
  s += "<tr><th>Longitude</th><td>" + lng_str + "</td></tr>";
  s += "<tr><th>Date</th><td>" + date_str + "</td></tr>";
  s += "<tr><th>Time</th><td>" + time_str + "</td></tr>";
  s += "</table>";

  // Buttons to navigate to Google Maps and nearby hospitals
  s += "<div class=\"button-container\">";
  
  // Correctly passing the live latitude and longitude for Google Maps search
  s += "<a href=\"http://maps.google.com/maps?&z=15&mrt=yp&t=k&q=" + lat_str + "+" + lng_str + "\" target=\"_top\">Check Location in Google Maps</a>";
  
  // Fixing the nearby hospitals search link to use live GPS coordinates with a specific search for hospitals
  s += "<a href=\"https://www.google.com/maps/search/ nearest hospital/@"+ lat_str +","+ lng_str +",14z/\" target=\"_blank\">Find Nearest Hospital</a>";
  
  s += "<a href=\"/\" style=\"background-color: #0056b3;\">Refresh Location</a>";  // Refresh button
  
  // "About Us" section with blue background
  s += "<div class=\"about-us\">";
  s += "<h3>BUILD BY</h3>";
  s += "<p>Jayapranav.R, Balaji.R.G, Thamaraimanalan.M, Mohammed Yassir.I, U.Yeshwanth</p>";
  s += "</div>";
  
  s += "</div>";

  s += "</body> </html>";

  client.print(s);
  delay(100);
}