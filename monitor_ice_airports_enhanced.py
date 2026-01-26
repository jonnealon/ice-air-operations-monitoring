import requests
from datetime import datetime, timedelta
import json
import os
import math
from collections import defaultdict

# Major ICE Air Operations airports
ICE_AIRPORTS = {
    'AZA': {'name': 'Mesa Gateway (Phoenix)', 'lat': 33.3078, 'lon': -111.6545},
    'AEX': {'name': 'Alexandria International', 'lat': 31.3274, 'lon': -92.5498},
    'SAT': {'name': 'San Antonio International', 'lat': 29.5337, 'lon': -98.4698},
    'BRO': {'name': 'Brownsville South Padre', 'lat': 25.9068, 'lon': -97.4259},
    'ELP': {'name': 'El Paso International', 'lat': 31.8072, 'lon': -106.3778},
    'HRL': {'name': 'Harlingen Valley', 'lat': 26.2285, 'lon': -97.6544},
    'MFE': {'name': 'McAllen Miller', 'lat': 26.1758, 'lon': -98.2386},
    'TUS': {'name': 'Tucson International', 'lat': 32.1161, 'lon': -110.9410}
}

# Known ICE charter operators
CHARTER_OPERATORS = {
    'SWQ': 'Swift Air',
    'WAL': 'World Atlantic',
    'CSQ': 'iAero Airways',
    'SWA': 'iAero Group',
    'N166HQ': 'Known ICE Aircraft',
    'N167HQ': 'Known ICE Aircraft',
    'N168HQ': 'Known ICE Aircraft'
}

# Watch list regions (bearing ranges in degrees)
WATCH_REGIONS = {
    'AFRICA_EAST': {'bearing_range': (60, 120), 'destinations': ['Eritrea', 'Somalia', 'Ethiopia', 'Kenya']},
    'AFRICA_WEST': {'bearing_range': (45, 90), 'destinations': ['Senegal', 'Guinea', 'Sierra Leone', 'Gambia']},
    'EASTERN_EUROPE': {'bearing_range': (30, 60), 'destinations': ['Romania', 'Moldova', 'Ukraine']},
    'MIDDLE_EAST': {'bearing_range': (45, 90), 'destinations': ['Iraq', 'Syria', 'Yemen']},
    'SOUTH_ASIA': {'bearing_range': (15, 45), 'destinations': ['Bangladesh', 'Myanmar', 'Nepal']},
    'MEXICO_CENTRAL_AMERICA': {'bearing_range': (150, 210), 'destinations': ['Mexico', 'Guatemala', 'Honduras', 'El Salvador'], 'normal': True},
    'CARIBBEAN': {'bearing_range': (90, 135), 'destinations': ['Haiti', 'Dominican Republic', 'Jamaica'], 'normal': True}
}

MONITOR_RADIUS_KM = 5  # Expanded from 15km based on TNT findings
ALTITUDE_THRESHOLD_M = 2000  # Monitor below 2000m based on TNT findings

def distance_km(lat1, lon1, lat2, lon2):
    """Calculate actual distance in km"""
    lat_diff = (lat1 - lat2) * 111
    lon_diff = (lon1 - lon2) * 111 * math.cos(math.radians(lat1))
    return math.sqrt(lat_diff**2 + lon_diff**2)

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing between two points"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    diff_lon = math.radians(lon2 - lon1)
    
    x = math.sin(diff_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(diff_lon)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def check_region(bearing):
    """Determine which region aircraft is heading toward"""
    for region_name, region_info in WATCH_REGIONS.items():
        start, end = region_info['bearing_range']
        if start <= bearing <= end:
            is_unusual = not region_info.get('normal', False)
            return region_name, region_info['destinations'], is_unusual
    return 'UNKNOWN', [], False

def is_charter_operator(callsign, icao24):
    """Check if aircraft matches known ICE charter operators"""
    callsign_upper = callsign.upper()
    
    # Check callsign patterns
    for pattern, operator in CHARTER_OPERATORS.items():
        if callsign_upper.startswith(pattern):
            return True, operator
    
    return False, None

def get_aircraft_near_airports():
    """Query OpenSky for aircraft near all ICE airports"""
    all_detections = []
    
    for code, airport in ICE_AIRPORTS.items():
        lat = airport['lat']
        lon = airport['lon']
        
        # Calculate bounding box
        lat_offset = MONITOR_RADIUS_KM / 111
        lon_offset = MONITOR_RADIUS_KM / (111 * abs(lat / 90))
        
        min_lat = lat - lat_offset
        max_lat = lat + lat_offset
        min_lon = lon - lon_offset
        max_lon = lon + lon_offset
        
        url = f"https://opensky-network.org/api/states/all?lamin={min_lat}&lomin={min_lon}&lamax={max_lat}&lomax={max_lon}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data and 'states' in data and data['states']:
                for state in data['states']:
                    # Skip high-altitude aircraft
                    if state[7] and state[7] > ALTITUDE_THRESHOLD_M:
                        continue
                    
                    aircraft = {
                        'timestamp': datetime.now().isoformat(),
                        'airport_code': code,
                        'airport_name': airport['name'],
                        'icao24': state[0],
                        'callsign': state[1].strip() if state[1] else 'Unknown',
                        'latitude': state[6],
                        'longitude': state[5],
                        'altitude_m': state[7],
                        'velocity_ms': state[9],
                        'heading': state[10],
                        'vertrate': state[11],
                        'on_ground': state[8]
                    }
                    
                    # Calculate distance and bearing
                    if aircraft['latitude'] and aircraft['longitude']:
                        dist = distance_km(airport['lat'], airport['lon'], 
                                         aircraft['latitude'], aircraft['longitude'])
                        aircraft['distance_from_airport_km'] = dist
                        
                        bearing = calculate_bearing(
                            airport['lat'], airport['lon'],
                            aircraft['latitude'], aircraft['longitude']
                        )
                        aircraft['bearing_from_airport'] = bearing
                        
                        # Check region
                        region, destinations, is_unusual = check_region(bearing)
                        aircraft['projected_region'] = region
                        aircraft['potential_destinations'] = destinations
                        aircraft['unusual_destination'] = is_unusual
                        
                        # Check if charter operator
                        is_charter, operator = is_charter_operator(aircraft['callsign'], aircraft['icao24'])
                        aircraft['is_charter_operator'] = is_charter
                        aircraft['operator_name'] = operator
                        
                        # ENHANCED: Flag unknown/missing callsigns (lesson from TNT)
                        is_unknown_callsign = aircraft['callsign'] in ['Unknown', '', 'N/A']
                        aircraft['unknown_callsign'] = is_unknown_callsign
                        
                        # Flag alerts
                        alerts = []
                        
                        if is_charter:
                            alerts.append(f"CHARTER_OPERATOR:{operator}")
                        
                        if is_unknown_callsign:
                            alerts.append("UNKNOWN_CALLSIGN")
                        
                        if is_unusual:
                            alerts.append(f"UNUSUAL_DESTINATION:{region}")
                        
                        # ENHANCED: Flag close proximity (within 2km = high confidence)
                        if dist < 2:
                            alerts.append("VERY_CLOSE_TO_AIRPORT")
                        
                        # ENHANCED: Flag descending aircraft near airport
                        if aircraft['vertrate'] and aircraft['vertrate'] < -2 and dist < 5:
                            alerts.append("DESCENDING_NEAR_AIRPORT")
                        
                        # ENHANCED: Combination alerts (charter + unusual + close)
                        if is_charter and is_unusual and dist < 5:
                            alerts.append("HIGH_PRIORITY:Charter+Unusual_Destination")
                        
                        aircraft['alerts'] = alerts
                        aircraft['is_alert'] = len(alerts) > 0
                        
                        all_detections.append(aircraft)
                        
        except Exception as e:
            print(f"Error querying {code}: {e}")
            continue
    
    return all_detections

def save_detections(detections):
    """Save all detections to monthly log with enhanced metadata"""
    os.makedirs('ice_operations_data', exist_ok=True)
    
    filename = f"ice_operations_data/ice_airports_{datetime.now().strftime('%Y-%m')}.json"
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
    else:
        data = []
    
    data.extend(detections)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(detections)} detections")

def save_alerts(detections):
    """Save high-priority alerts"""
    alerts = [d for d in detections if d['is_alert']]
    
    if not alerts:
        return
    
    os.makedirs('ice_operations_data', exist_ok=True)
    alert_filename = f"ice_operations_data/ALERTS_{datetime.now().strftime('%Y-%m')}.json"
    
    if os.path.exists(alert_filename):
        with open(alert_filename, 'r') as f:
            alert_data = json.load(f)
    else:
        alert_data = []
    
    alert_data.extend(alerts)
    
    with open(alert_filename, 'w') as f:
        json.dump(alert_data, f, indent=2)
    
    print(f"\n🚨 {len(alerts)} ALERTS:")
    for alert in alerts[:10]:  # Show first 10
        print(f"  {alert['callsign']} at {alert['airport_name']}")
        print(f"    Distance: {alert['distance_from_airport_km']:.1f}km, Alt: {alert['altitude_m']:.0f}m")
        print(f"    Region: {alert['projected_region']}")
        print(f"    Alerts: {', '.join(alert['alerts'])}")

def update_aircraft_database(detections):
    """ENHANCED: Track aircraft over time to build known-visitor database"""
    os.makedirs('ice_operations_data', exist_ok=True)
    db_file = 'ice_operations_data/aircraft_database.json'
    
    # Load existing database
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            database = json.load(f)
    else:
        database = {}
    
    # Update with new detections
    for d in detections:
        icao = d['icao24']
        if icao not in database:
            database[icao] = {
                'icao24': icao,
                'callsigns_seen': set(),
                'airports_visited': set(),
                'first_seen': d['timestamp'],
                'last_seen': d['timestamp'],
                'total_detections': 0,
                'is_charter': d['is_charter_operator'],
                'operator': d.get('operator_name')
            }
        
        # Update
        db_entry = database[icao]
        if isinstance(db_entry['callsigns_seen'], list):
            db_entry['callsigns_seen'] = set(db_entry['callsigns_seen'])
        if isinstance(db_entry['airports_visited'], list):
            db_entry['airports_visited'] = set(db_entry['airports_visited'])
            
        db_entry['callsigns_seen'].add(d['callsign'])
        db_entry['airports_visited'].add(d['airport_code'])
        db_entry['last_seen'] = d['timestamp']
        db_entry['total_detections'] += 1
        
        # Convert sets to lists for JSON serialization
        database[icao]['callsigns_seen'] = list(db_entry['callsigns_seen'])
        database[icao]['airports_visited'] = list(db_entry['airports_visited'])
    
    # Save updated database
    with open(db_file, 'w') as f:
        json.dump(database, f, indent=2)

if __name__ == "__main__":
    print(f"ICE Air Operations Monitor (Enhanced) - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    detections = get_aircraft_near_airports()
    
    if detections:
        save_detections(detections)
        save_alerts(detections)
        update_aircraft_database(detections)
        
        charter_count = sum(1 for d in detections if d['is_charter_operator'])
        unusual_count = sum(1 for d in detections if d['unusual_destination'])
        unknown_count = sum(1 for d in detections if d['unknown_callsign'])
        
        print(f"\nTotal aircraft detected: {len(detections)}")
        print(f"Charter operators: {charter_count}")
        print(f"Unknown callsigns: {unknown_count}")
        print(f"Unusual destinations: {unusual_count}")
    else:
        print("No aircraft detected")
