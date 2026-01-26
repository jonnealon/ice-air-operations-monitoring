import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

print("="*80)
print("DAILY GAP ANALYSIS - ICE AIR OPERATIONS")
print("="*80)

# Load last 48 hours of data
data_dir = 'ice_operations_data'
current_month_file = f"{data_dir}/ice_airports_{datetime.now().strftime('%Y-%m')}.json"

if not os.path.exists(current_month_file):
    print("No data file found")
    exit()

with open(current_month_file, 'r') as f:
    all_data = json.load(f)

# Filter to last 48 hours
cutoff = (datetime.now() - timedelta(hours=48)).isoformat()
recent_data = [d for d in all_data if d['timestamp'] > cutoff]

print(f"\nAnalyzing {len(recent_data)} detections from last 48 hours")

# Group by aircraft
by_aircraft = defaultdict(list)
for d in recent_data:
    by_aircraft[d['icao24']].append(d)

# Look for suspicious gaps
possible_landings = []
possible_takeoffs = []

for icao, detections in by_aircraft.items():
    detections.sort(key=lambda x: x['timestamp'])
    
    for i, det in enumerate(detections):
        if i == 0:
            continue
        
        prev_det = detections[i-1]
        
        # Calculate time gap
        curr_time = datetime.fromisoformat(det['timestamp'])
        prev_time = datetime.fromisoformat(prev_det['timestamp'])
        gap_minutes = (curr_time - prev_time).total_seconds() / 60
        
        # Look for gaps > 60 minutes near airports
        if gap_minutes > 60:
            # Check if appeared near airport (takeoff)
            if det['distance_from_airport_km'] < 5 and det['altitude_m'] < 2000:
                possible_takeoffs.append({
                    'icao': icao,
                    'callsign': det['callsign'],
                    'airport': det['airport_code'],
                    'timestamp': det['timestamp'],
                    'gap_hours': gap_minutes / 60,
                    'distance_km': det['distance_from_airport_km'],
                    'altitude_m': det['altitude_m']
                })
            
            # Check if disappeared near airport (landing)
            if prev_det['distance_from_airport_km'] < 5 and prev_det['altitude_m'] < 2000:
                possible_landings.append({
                    'icao': icao,
                    'callsign': prev_det['callsign'],
                    'airport': prev_det['airport_code'],
                    'timestamp': prev_det['timestamp'],
                    'gap_hours': gap_minutes / 60,
                    'distance_km': prev_det['distance_from_airport_km'],
                    'altitude_m': prev_det['altitude_m']
                })

print(f"\n🛬 POSSIBLE LANDINGS (last 48h): {len(possible_landings)}")
for landing in possible_landings:
    print(f"\n{landing['timestamp'][:19]}")
    print(f"  {landing['callsign']} ({landing['icao']}) at {landing['airport']}")
    print(f"  {landing['distance_km']:.1f}km from airport, {landing['altitude_m']:.0f}m")
    print(f"  Then {landing['gap_hours']:.1f} hour gap")

print(f"\n🛫 POSSIBLE TAKEOFFS (last 48h): {len(possible_takeoffs)}")
for takeoff in possible_takeoffs:
    print(f"\n{takeoff['timestamp'][:19]}")
    print(f"  {takeoff['callsign']} ({takeoff['icao']}) at {takeoff['airport']}")
    print(f"  {takeoff['distance_km']:.1f}km from airport, {takeoff['altitude_m']:.0f}m")
    print(f"  After {takeoff['gap_hours']:.1f} hour gap")

# Save to daily summary
summary_file = f"{data_dir}/daily_summary_{datetime.now().strftime('%Y-%m-%d')}.json"
with open(summary_file, 'w') as f:
    json.dump({
        'date': datetime.now().isoformat(),
        'possible_landings': possible_landings,
        'possible_takeoffs': possible_takeoffs
    }, f, indent=2)

print(f"\nSummary saved to {summary_file}")
