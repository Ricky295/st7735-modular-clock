from st7735 import TFT
from sysfont import sysfont
from machine import SPI, Pin
import time
import json
import math
import network
import ntptime
from time import ticks_ms

# Initialize SPI and TFT display
spi = SPI(1, baudrate=20000000, polarity=0, phase=0,
          sck=Pin(10), mosi=Pin(11), miso=None)
tft = TFT(spi, 16, 17, 18)
tft.initr()
tft.rgb(True)

# JSON configuration for clock components
config_json = '''
{
    "components": [
        {
            "type": "digital_datetime",
            "format": "HH:mm:SS",
            "position": [60, 70],
            "color": 65535,
            "timezone": 2,
            "scale": 1
        },
        {
            "type": "digital_datetime",
            "format": "DD-MM-YY",
            "position": [60, 80],
            "color": 2047,
            "timezone": 2,
            "scale": 1
        },
        {
            "type": "countdown_timer",
            "end_date": "2024-10-31T00:00:00",
            "repetition": 365,
            "format": "Dd",
            "position": [5, 116],
            "color": 64512,
            "timezone": 2,
            "scale": 1
        },
        {
            "type": "bar_countdown",
            "end_date": "2024-10-31T00:00:00",
            "repetition": 365,
            "position": [5, 13],
            "size": [10, 100],
            "direction": 0,
            "color": 64512,
            "timezone": 2,
            "countup": 1
        },
        {
            "type": "percent_countdown",
            "end_date": "2024-10-31T00:00:00",
            "repetition": 365,
            "position": [5, 3],
            "decimals": 2,
            "color": 65535,
            "timezone": 2,
            "countup": 1,
            "scale": 1
        },
        {
            "type": "countdown_timer",
            "end_date": "2024-12-25T00:00:00",
            "repetition": 365,
            "format": "Dd",
            "position": [140, 116],
            "color": 2047,
            "timezone": 2,
            "scale": 1
        },
        {
            "type": "bar_countdown",
            "end_date": "2024-12-25T00:00:00",
            "repetition": 365,
            "position": [145, 13],
            "size": [10, 100],
            "direction": 0,
            "color": 1015,
            "timezone": 2,
            "countup": 1
        },
        {
            "type": "percent_countdown",
            "end_date": "2024-12-25T00:00:00",
            "repetition": 365,
            "position": [120, 3],
            "decimals": 2,
            "color": 65535,
            "timezone": 2,
            "countup": 1,
            "scale": 1
        },
        
        {
            "type": "analog_hand",
            "length": 40,
            "width": 4,
            "position": [80, 64],
            "duration": 60,
            "color": 65535,
            "timezone": 2
        },
        {
            "type": "analog_hand",
            "length": 30,
            "width": 4,
            "position": [80, 64],
            "duration": 3600,
            "color": 63488,
            "timezone": 2
        },
        {
            "type": "analog_hand",
            "length": 20,
            "width": 6,
            "position": [80, 64],
            "duration": 43200,
            "color": 2016,
            "timezone": 2
        },
        {
            "type": "face_circle",
            "radius": 60,
            "notches": 12,
            "length": 10,
            "style": 3,
            "color": 65535,
            "position": [80, 64]
        },
        {
            "type": "face_circle",
            "radius": 60,
            "notches": 60,
            "length": 5,
            "style": 2,
            "color": 65535,
            "position": [80, 64]
        }
    ],
    "orientation": 1,
    "background": 0
}
'''

# Load configuration from JSON
config = json.loads(config_json)

# Network setup for fetching time (if needed)
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)
    print('Connected to WiFi:', wlan.ifconfig())

def fetch_time():
    try:
        ntptime.settime()  # Sync with NTP server
        print("Time fetched successfully.")
    except Exception as e:
        print("Failed to fetch time:", e)
        
# Function to convert a date string to a timestamp
def date_to_timestamp(date_str, timezone_offset):
    # Extract date and time components
    date_part, time_part = date_str.split("T")
    year, month, day = map(int, date_part.split("-"))
    hour, minute, second = map(int, time_part.split(":"))

    # Create a timestamp (assuming the date is in UTC)
    timestamp = time.mktime((year, month, day, hour, minute, second, 0, 0, -1))

    # Adjust for timezone
    timestamp += timezone_offset * 3600  # Convert hours to seconds

    return timestamp

def draw_analog_hand(color, center, radius, angle):

    # Draw the new hand
    angle_rad = math.radians(angle)
    x = center[0] + int(radius * math.cos(angle_rad))
    y = center[1] + int(radius * math.sin(angle_rad))
    tft.line(center, (x, y), color)
    
def fillrect(aStart, aSize, aColor):
    for i in range(aSize[0]):
        tft.vline([aStart[0] + i, aStart[1]], aSize[1], aColor )
    
# Draw digital datetime with flexible format
def draw_digital_datetime(position, color, timezone, format_str, scale):
    tft.fillrect([position[0], position[1]], [len(format_str) * 5 * scale, 8 * scale], TFT.BLACK)  # Clear previous time (adjust size as needed)
    current_time = time.localtime()

    # Adjust for timezone
    hour = current_time[3] + timezone
    if hour >= 24:
        hour -= 24
    elif hour < 0:
        hour += 24

    # Replace placeholders with actual time values
    formatted_time = format_str
    formatted_time = formatted_time.replace("YYYY", "{:04}".format(current_time[0]))   # Year
    formatted_time = formatted_time.replace("YY", "{:02}".format(current_time[0] - 2000))   # Short year
    formatted_time = formatted_time.replace("MM", "{:02}".format(current_time[1]))     # Month
    formatted_time = formatted_time.replace("M", "{}".format(current_time[1]))     # Short month
    formatted_time = formatted_time.replace("DD", "{:02}".format(current_time[2]))     # Day
    formatted_time = formatted_time.replace("DD", "{}".format(current_time[2]))     # Short day
    formatted_time = formatted_time.replace("HH", "{:02}".format(hour))                # Hour
    formatted_time = formatted_time.replace("H", "{}".format(hour))                # Short hour
    formatted_time = formatted_time.replace("mm", "{:02}".format(current_time[4]))     # Minute
    formatted_time = formatted_time.replace("SS", "{:02}".format(current_time[5]))     # Second

    # Display the formatted time on the screen
    tft.text((position[0], position[1]), formatted_time, color, sysfont, scale)


# Draw circle face
def draw_face_circle(position, radius, notches, color, style, length):
    # Draw outer circle
    tft.circle(position, radius, color)
    if style in (2, 3):
        for i in range(notches):
            angle_rad = math.radians((360 / notches) * i)
            x_start = position[0] + int((radius - length) * math.cos(angle_rad))
            y_start = position[1] + int((radius - length) * math.sin(angle_rad))
            x_end = position[0] + int(radius * math.cos(angle_rad))
            y_end = position[1] + int(radius * math.sin(angle_rad))
            tft.line((x_start, y_start), (x_end, y_end), color)
    if style in (1, 3):
        for i in range(1, notches + 1, 1):
            angle_rad = math.radians((360 / notches) * i - 90)
            x_text = position[0] + int((radius - length - 5) * math.cos(angle_rad) - 2)
            y_text = position[1] + int((radius - length - 5) * math.sin(angle_rad)) - 4
            tft.text((x_text, y_text), str(i), color, sysfont)

            
# Function to draw countdown timer
def draw_countdown_timer(position, color, end_date, repetition, format_str, timezone, scale):
    # Clear previous countdown
    tft.fillrect([position[0], position[1]], [len(format_str) * 5, 8], TFT.BLACK)  # Adjust size as needed

    # Convert end_date string to timestamp
    end_timestamp = date_to_timestamp(end_date, timezone)

    # Get current time in UTC
    current_timestamp = time.time()

    # Calculate remaining time in seconds
    remaining_time = end_timestamp - current_timestamp

    # Check for repetition
    if remaining_time < 0 and repetition:
        end_timestamp += repetition * 86400  # 86400 seconds in a day
        remaining_time = end_timestamp - current_timestamp

    # Calculate days, hours, minutes, seconds
    if remaining_time >= 0:
        days = int(remaining_time // 86400)
        hours = int((remaining_time % 86400) // 3600)
        minutes = int((remaining_time % 3600) // 60)
        seconds = int(remaining_time % 60)
    else:
        days, hours, minutes, seconds = 0, 0, 0

    # Format the output
    formatted_time = format_str
    formatted_time = formatted_time.replace("D", str(days))
    formatted_time = formatted_time.replace("H", str(hours))
    formatted_time = formatted_time.replace("M", str(minutes))
    formatted_time = formatted_time.replace("S", str(seconds))

    # Display the formatted time on the screen
    tft.text((position[0], position[1]), formatted_time, color, sysfont, scale)
            
def draw_bar_countdown(position, color, end_date, size, countup, timezone, repetition, direction):

    tft.fillrect([position[0], position[1]], [size[0], size[1]], TFT.BLACK)
    
    # Convert end_date string to timestamp
    end_timestamp = date_to_timestamp(end_date, timezone)

    # Get current time in UTC
    current_timestamp = time.time()

    # Calculate remaining time in seconds
    remaining_time = end_timestamp - current_timestamp

    # Check for repetition
    if remaining_time < 0 and repetition:
        end_timestamp += repetition * 86400  # 86400 seconds in a day
        remaining_time = end_timestamp - current_timestamp
    
    fullness = (remaining_time / 86400) / repetition
    if countup%2 == 1:
        fullness = 1 - fullness
    
    if direction%4 == 0:
        tft.fillrect([position[0], position[1] + (1 - fullness)*size[1]], [size[0], size[1] * fullness], color)
    elif direction%4 == 1:
        tft.fillrect([position[0], position[1]], [size[0] * fullness, size[1]], color)
    elif direction%4 == 2:
        tft.fillrect([position[0], position[1]], [size[0], size[1] * fullness], color)
    elif direction%4 == 3:
        fillrect([position[0] + (1 - fullness)*size[0], position[1]], [size[0] * fullness, size[1]], color)
        
    tft.rect([position[0], position[1]], [size[0], size[1]], TFT.WHITE)
    
def draw_percentage_countdown(position, color, end_date, decimals, countup, timezone, repetition, scale):

    tft.fillrect([position[0], position[1]], [24 + decimals * 8, 8], TFT.BLACK)
    
    # Convert end_date string to timestamp
    end_timestamp = date_to_timestamp(end_date, timezone)

    # Get current time in UTC
    current_timestamp = time.time()

    # Calculate remaining time in seconds
    remaining_time = end_timestamp - current_timestamp

    # Check for repetition
    if remaining_time < 0 and repetition:
        end_timestamp += repetition * 86400  # 86400 seconds in a day
        remaining_time = end_timestamp - current_timestamp
    
    fullness = (remaining_time / 86400) / repetition * 100
    if countup%2 == 1:
        fullness = 100 - fullness
    
    tft.text((position[0], position[1]), f"{fullness:.{decimals}f}%", color, sysfont, scale)
    

# Main function to draw the clock
def draw_clock():
    tft.rotation(config['orientation'])  # Set the correct orientation
    tft.fill(config['background'])

    # Draw the static face of the clock only once
    for component in config['components']:
        if component['type'] == 'face_circle':
            draw_face_circle(
                component['position'], 
                component['radius'], 
                component['notches'], 
                component['color'], 
                component['style'],
                component['length']  # Added missing comma here
            )
    
    last_update_time = ticks_ms()  # Initialize last update time
    clock_center = config['components'][0]['position']  # Assuming the position is the same for all components

    while True:
        ledtime = time.localtime()
        if ((ledtime[3] + sleep_timezone)%24 > Sleep[0] and (ledtime[3] + sleep_timezone) < Sleep[1]):
            backlight.off()
        else:
            backlight.on()
        current_time = ticks_ms()  # Get the current time in milliseconds

        # Check if at least 1000 ms have passed since the last update
        if current_time - last_update_time >= 1000:  
            last_update_time = current_time  # Update the last update time

            for component in config['components']:
                if component['type'] == 'analog_hand':
                    current_time_tuple = time.localtime()
                    seconds = ((current_time_tuple[3] + component['timezone']) * 3600) + (current_time_tuple[4] * 60) + (current_time_tuple[5])
                    previousseconds = seconds - 1
                    angle = (seconds % component['duration']) * (360 / component['duration']) - 90
                    previousangle = (previousseconds % component['duration']) * (360 / component['duration']) - 90
                    draw_analog_hand( 
                        0, 
                        component['position'], 
                        component['length'], 
                        previousangle
                    )
                    draw_analog_hand( 
                        component['color'], 
                        component['position'], 
                        component['length'], 
                        angle
                    )
                elif component['type'] == 'digital_datetime':
                    draw_digital_datetime(
                        component['position'], 
                        component['color'],
                        component['timezone'],
                        component['format'],
                        component['scale'],
                    )
                elif component['type'] == 'face_circle':
                    draw_face_circle(
                        component['position'], 
                        component['radius'], 
                        component['notches'], 
                        component['color'], 
                        component['style'],
                        component['length']  # Added missing comma here
                    )
                elif component['type'] == 'countdown_timer':
                    draw_countdown_timer(
                        component['position'], 
                        component['color'],
                        component['end_date'],
                        component['repetition'],
                        component['format'],
                        component['timezone'],
                        component['scale']
                    )
                elif component['type'] == 'bar_countdown':
                    draw_bar_countdown(
                        component['position'], 
                        component['color'],
                        component['end_date'],
                        component['size'],
                        component['countup'],
                        component['timezone'],
                        component['repetition'],
                        component['direction']
                    )
                elif component['type'] == 'percent_countdown':
                    draw_percentage_countdown(
                        component['position'], 
                        component['color'],
                        component['end_date'],
                        component['decimals'],
                        component['countup'],
                        component['timezone'],
                        component['repetition'],
                        component['scale']
                    )
                
                

        time.sleep(0.01)  # Small sleep to prevent busy waiting

#Sleep mode
Sleep = [0, 10]
sleep_timezone = 2

backlight = Pin(15, Pin.OUT)

# Setup WiFi and fetch time
connect_wifi('wifi name', 'wifi password')  # Replace with your WiFi credentials
fetch_time()
# Run the clock
draw_clock()

