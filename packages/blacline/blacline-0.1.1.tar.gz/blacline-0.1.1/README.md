# Blacline

**Blacline** is a Python package for **bus scheduling, crew scheduling, and timetable generation**.  
It is designed to help transport planners, and developers quickly generate schedules for public transport operations.


## Exising Features
- Schedule buses from multiple terminals while maintaining headway
- Calculate trip departure and arrival times
- Output schedules as Pandas DataFrames for further analysis or export

## Future Features
- Generate crew schedules and duty allocations

## Installation

You can install Blacline directly from PyPI:

```bash
pip install blacline

## Usage
from blacline.scheduling import basic_schedule

schedule = basic_schedule(
    routeNumber='1A',
    numBuses=6,
    serviceStart=300,
    serviceEnd=1300,
    terminal1='T1',
    terminal2='T2',
    depot1='D1',
    depot2='D2',
    routeLength1=10,
    routeLength2=11,
    tripDuration1=35,
    tripDuration2=45,
    pulloutD1T1_length=0.5,
    pulloutD1T1_tt=10,
    pullinT1D1_length=0.5,
    pullinT2D1_length=11,
    pullinT1D1_tt=5,
    pullinT2D1_tt=55,
    pulloutD2T2_length=1,
    pulloutD2T2_tt=5,
    pullinT1D2_length=11,
    pullinT2D2_length=2,
    pullinT1D2_tt=40,
    pullinT2D2_tt=10,
    dutyPeriod=8*60,
    reliefTime=30,
    restPeriod=30,
    layoverT1=5,
    layoverT2=10
)

## Functions
basic_schedule(...) – Generates a bus timetable with start times, terminals, and duty allocations.


## License

Blacline is released under the MIT License. See LICENSE for details.