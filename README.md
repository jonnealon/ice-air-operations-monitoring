# ice-air-operations-monitoringICE Air Operations Monitoring System

Automated surveillance of deportation flight activity at major Immigration and Customs Enforcement (ICE) Air Operations facilities.
Overview

This system continuously monitors aircraft activity at 8 major ICE deportation hubs to detect:

    Flights to unusual destinations (Africa, Eastern Europe, Middle East, Asia)
    Known charter operator movements
    Potential new deportation agreements
    Covert operations (aircraft with no callsign)
    Policy shifts before official announcements

Built using lessons learned from trajectory analysis of Dade-Collier Training Airport (TNT) operations, including Air Force One security perimeter detection.
Monitored Facilities
Code	Airport	Location	Significance
AZA	Mesa Gateway	Phoenix, AZ	Primary ICE Air Operations hub
AEX	Alexandria International	Louisiana	Major deportation hub
SAT	San Antonio International	Texas	Border operations center
BRO	Brownsville South Padre	Texas	Rio Grande border
ELP	El Paso International	Texas	West Texas border
HRL	Harlingen Valley	Texas	Rio Grande Valley
MFE	McAllen Miller	Texas	Border operations
TUS	Tucson International	Arizona	Border operations
Key Capabilities
1. Real-Time Monitoring

    Frequency: Every 30 minutes, 24/7
    Coverage: 5km radius around each airport
    Altitude: Aircraft below 2,000 meters
    Method: OpenSky Network ADS-B data

2. Time Gap Detection

Identifies actual landings/takeoffs by tracking when aircraft:

    Appear near airport → disappear for 60+ minutes = likely landed
    Reappear after extended gap = likely took off
    Does not require continuous tracking (accounts for transponders turning off)

3. Unknown Callsign Tracking

Critical finding from TNT analysis: Many sensitive operations use aircraft with no broadcast identification.

System specifically flags:

    Callsign = "Unknown"
    Missing callsign data
    Anonymous operations

4. Charter Operator Database

Tracks known ICE contractors:

    Swift Air (SWQ callsign)
    iAero Airways (CSQ/SWA callsigns)
    World Atlantic (WAL callsign)
    Known ICE aircraft (N166HQ, N167HQ, N168HQ)

5. Unusual Destination Detection

Monitors flight bearings to identify departures toward non-traditional deportation destinations:

Watch List Regions:

    🌍 East Africa: Eritrea, Somalia, Ethiopia, Kenya
    🌍 West Africa: Senegal, Guinea, Sierra Leone, Gambia
    🇪🇺 Eastern Europe: Romania, Moldova, Ukraine
    🕌 Middle East: Iraq, Syria, Yemen
    🌏 South Asia: Bangladesh, Myanmar, Nepal

Normal Patterns (for comparison):

    🌎 Mexico & Central America (expected deportation routes)
    🏝️ Caribbean destinations

6. Historical Aircraft Database

Builds comprehensive database over time:

    Every unique aircraft detected
    Airports visited
    Frequency of appearances
    Operator identification
    First/last seen timestamps

Alert System
🔴 Critical Priority

Charter operator + unusual destination + close to airport
Unknown callsign + descending near airport + charter operator

🟡 High Priority

Charter operators at any distance
Unusual destination bearings
Very close to airport (<2km)
Descending near airport

🟢 Medium Priority

Aircraft within monitoring radius
Normal destination patterns
General aviation traffic

Data Collection
Files Generated

Every 30 minutes:

    ice_airports_YYYY-MM.json - All aircraft detections with metadata

Real-time:

    ALERTS_YYYY-MM.json - High-priority alerts only

Daily (noon UTC):

    daily_summary_YYYY-MM-DD.json - Gap analysis results, likely landings/takeoffs

Continuously updated:

    aircraft_database.json - Historical tracking of all detected aircraft

Data Structure

Each detection includes:
json

{
  "timestamp": "2026-01-26T14:30:00",
  "airport_code": "AZA",
  "airport_name": "Mesa Gateway (Phoenix)",
  "icao24": "a12345",
  "callsign": "SWQ123",
  "distance_from_airport_km": 3.2,
  "altitude_m": 1200,
  "bearing_from_airport": 95,
  "projected_region": "AFRICA_EAST",
  "is_charter_operator": true,
  "operator_name": "Swift Air",
  "unknown_callsign": false,
  "unusual_destination": true,
  "alerts": ["CHARTER_OPERATOR:Swift Air", "UNUSUAL_DESTINATION:AFRICA_EAST"],
  "is_alert": true
}

Methodology
Enhanced Trajectory Analysis

Based on research at Dade-Collier Training Airport (TNT) where traditional methods failed to detect operations including Air Force One's July 1, 2025 visit.

Key Innovations:

    Wider Detection Radius: Most operations detected 2-5km from airport, not just at runway
    Gap-Based Inference: Aircraft don't need continuous tracking; disappearance patterns indicate landings
    Unknown Callsign Priority: High percentage of sensitive operations use no broadcast identification
    Historical Tracking: Build patterns over time rather than single-snapshot detection

Validation: Successfully detected 75 operations at TNT over 2 months using gap analysis, vs. 0 with traditional altitude-only methods.
Limitations

What this system CAN detect:

    ✅ Aircraft with active ADS-B transponders
    ✅ Departures toward unusual regions
    ✅ Charter operator activity
    ✅ Pattern changes over time
    ✅ Security perimeter operations

What this system CANNOT reliably detect:

    ❌ Aircraft with transponders completely off
    ❌ Exact landing counts (many operations occur "dark")
    ❌ Ground operations after landing
    ❌ Classified/military flights using operational security

Estimated coverage: 20-40% of actual operations at facilities with security protocols
Use Cases
1. Policy Investigation

Detect new deportation agreements before official announcement:

    Swift Air departure toward Eritrea = investigate pending agreement
    Unusual spike in Eastern Europe flights = research policy changes

2. Accountability Journalism

Document patterns over time:

    Which facilities most active?
    Which operators winning contracts?
    Cost-benefit analysis of charter operations

3. Litigation Support

Build evidentiary database:

    Operation frequency
    Contractor identification
    Pattern documentation
    Timeline correlation with known events

4. Comparative Analysis

    TNT vs. Mesa Gateway activity levels
    Border facilities vs. interior hubs
    Pre/post policy change patterns

Installation & Deployment
Prerequisites

    GitHub account (free)
    OpenSky Network account (free for research)

Setup

    Create Repository

bash

   # On GitHub: New repository → "ice-air-operations-monitoring"
   # Make it Public for free Actions

    Add Files
        monitor_ice_airports_enhanced.py
        analyze_gaps_daily.py
        .github/workflows/monitor-ice-enhanced.yml
    Enable Permissions
        Settings → Actions → General
        Workflow permissions: "Read and write"
        Save
    Manual Test

bash

   python3 monitor_ice_airports_enhanced.py

    Deploy
        Commit files to repository
        GitHub Actions will run automatically every 30 minutes
        Daily analysis runs at noon UTC

Analysis Examples
Finding Unusual Destinations
python

import json

with open('ice_operations_data/ice_airports_2026-01.json') as f:
    data = json.load(f)

unusual = [d for d in data if d['unusual_destination']]
print(f"Unusual destination flights: {len(unusual)}")

for flight in unusual[:10]:
    print(f"{flight['timestamp']}: {flight['callsign']} at {flight['airport_code']}")
    print(f"  → Heading toward {flight['projected_region']}")

Tracking Specific Charter Operators
python

swift_air = [d for d in data if 'Swift Air' in str(d.get('operator_name'))]
print(f"Swift Air operations: {len(swift_air)}")

by_airport = {}
for op in swift_air:
    airport = op['airport_code']
    by_airport[airport] = by_airport.get(airport, 0) + 1

for airport, count in sorted(by_airport.items(), key=lambda x: x[1], reverse=True):
    print(f"{airport}: {count} detections")

Reviewing Daily Summaries
python

import glob

summaries = glob.glob('ice_operations_data/daily_summary_*.json')
total_landings = 0
total_takeoffs = 0

for summary_file in summaries:
    with open(summary_file) as f:
        summary = json.load(f)
        total_landings += len(summary['possible_landings'])
        total_takeoffs += len(summary['possible_takeoffs'])

print(f"Total operations detected: {total_landings + total_takeoffs}")
```

---

## Research Applications

### Academic
- **Geospatial Journalism:** Methodology development for accountability investigations
- **Migration Studies:** Documentation of state-sponsored transportation patterns
- **Human Rights:** Evidence collection for advocacy and litigation

### Journalistic
- **Breaking News:** First detection of policy changes via flight patterns
- **Investigative Series:** Long-term pattern documentation
- **Data Journalism:** Visualization of deportation infrastructure

### Legal
- **Litigation Support:** Evidentiary database for cases against contractors
- **FOIA Corroboration:** Validate official records against observed activity
- **Pattern Evidence:** Demonstrate systematic practices

---

## Theoretical Framework

This monitoring system operationalizes the concept of **"migrant body commodification"** - analyzing how state transportation operations convert human beings into logistical units within aviation infrastructure.

**Research Questions:**
- How do deportation flight patterns reveal diplomatic negotiations?
- What role do private contractors play in state migration enforcement?
- Can open-source geospatial methods provide accountability when official transparency fails?

---

## Credits & Citation

**Methodology developed by:** Jon Nealon (MS Geographic Information Science, University at Albany SUNY)

**Based on:** Trajectory analysis research at Dade-Collier Training Airport, including detection of Air Force One security perimeter operations via proxy indicators (sheriff helicopter patterns), July-August 2025.

**Data Source:** OpenSky Network (https://opensky-network.org)

**If using this system or methodology, please cite:**
```
Nealon, J. (2026). Automated Surveillance of ICE Air Operations: 
Gap-Based Trajectory Analysis for Accountability Journalism. 
GitHub: github.com/[username]/ice-air-operations-monitoring

Contact & Collaboration

This is open-source accountability infrastructure. Contributions welcome.

For:

    Investigative collaborations
    Methodology questions
    Data sharing
    Legal/advocacy partnerships

Related Projects:

    Dade-Collier Flight Monitoring (alligator-alcatraz-monitoring)
    Geospatial Journalism Curriculum Development
    Migrant Body Commodification Research

License

Data and code released for research, journalism, and accountability purposes.

Permitted uses:

    Academic research
    Investigative journalism
    Advocacy and litigation support
    Public interest reporting

Restrictions:

    No commercial deportation facilitation
    No surveillance of individuals
    Must credit methodology and data sources

updaated 2/9/26

Changelog

v2.0 (Enhanced) - January 2026

    Added time gap detection based on TNT findings
    Implemented unknown callsign tracking
    Expanded detection radius to 5km
    Added daily gap analysis automation
    Built historical aircraft database
    Increased altitude threshold to 2000m

v1.0 (Initial) - January 2026

    Basic real-time monitoring
    Charter operator detection
    Unusual destination alerts
    8 facility coverage

Last Updated: January 26, 2026
