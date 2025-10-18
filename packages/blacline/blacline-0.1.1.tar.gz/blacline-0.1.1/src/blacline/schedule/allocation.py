import math
import sys
import pandas as pd

# Set options to display all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option("display.max_columns", None)   # show all columns
pd.set_option("display.width", None)         # don't wrap to console width

def change_terminal(terminal, terminal1, terminal2):
    return terminal2 if terminal == terminal1 else terminal1
# routeNumber,numBuses,serviceStart,serviceEnd,terminal1,terminal2,depot1,depot2,routeLength1,routeLength2,tripDuration1,tripDuration2,pulloutD1terminal1_length,pulloutD1terminal2_length,pulloutD1terminal1_tt,pulloutD1terminal2_tt,pullinterminal1D1_length,pullinterminal2D1_length,pullinterminal1D1_tt,pullinterminal2D1_tt,pulloutD2terminal1_length,pulloutD2terminal2_length,pulloutD2terminal1_tt,pulloutD2terminal2_tt,pullinterminal1D2_length,pullinterminal2D2_length,pullinterminal1D2_tt,pullinterminal2D2_tt,dutyPeriod,reliefTime,restPeriod,layoverT1,layoverT2


def allocate_buses(routeNumber, numBuses, tripDuration1, tripDuration2, layoverT1, layoverT2, serviceStart, serviceEnd, terminal1, terminal2, dutyPeriod, reliefTime, restPeriod):
    schedules = [f"{routeNumber}_{1 + i}" for i in range(numBuses)]
    terminal1_trips = math.ceil(numBuses / 2)
    terminal2_trips = int(numBuses / 2)
    cycleTime = tripDuration1 + tripDuration2 + layoverT1 + layoverT2
    headway = cycleTime/numBuses
    # print(f"headway: {headway}")

    df = pd.DataFrame()
    df['schedule_no'] = schedules
    df['start_terminal'] = [terminal1 for i in range(terminal1_trips)] + [terminal2 for i in range(terminal2_trips)]

    # start time
    df['serviceStart'] = [serviceStart + (headway * i) for i in range(terminal1_trips)] + [serviceStart + (tripDuration1+layoverT1)%headway + (headway * i) for i in range(terminal2_trips)]
    # print(df)

    service_span = serviceEnd - serviceStart
    if service_span > dutyPeriod:
        shift = 2
    else:
        shift = 1
    offset = max(restPeriod, reliefTime, (service_span - dutyPeriod*shift))
    # print('Shift', shift)
    # print('Offset', offset)

    for i,dp in df.iterrows():
        if i%2 == 1:
            serviceStart_target = dp['serviceStart'] + offset
            while (serviceStart_target > df.at[i, 'serviceStart']):
                if df.at[i, 'start_terminal'] == terminal1:
                    df.at[i, 'start_terminal'] = terminal2
                    df.at[i, 'serviceStart'] = df.at[i, 'serviceStart']+tripDuration1+layoverT1
                else:
                    df.at[i, 'start_terminal'] = terminal1
                    df.at[i, 'serviceStart'] = df.at[i, 'serviceStart']+tripDuration2+layoverT2
    # print(df)
    return df, shift, cycleTime

allocate_buses(routeNumber='1A', numBuses = 6, tripDuration1 = 60, tripDuration2= 65, layoverT1 = 5, layoverT2 = 5, serviceStart = 600, serviceEnd = 1000, terminal1 = 'terminal1', terminal2 = 'terminal2', dutyPeriod = 8*60, reliefTime = 20, restPeriod = 30)
