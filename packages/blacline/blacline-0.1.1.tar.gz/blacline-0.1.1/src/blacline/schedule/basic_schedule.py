from .allocation import allocate_buses
from .quick_schedule import schedule_bus
import pandas as pd

def basic_schedule(routeNumber,numBuses,serviceStart,serviceEnd,terminal1,terminal2,depot1,depot2,routeLength1,routeLength2,tripDuration1,tripDuration2,pulloutD1T1_length,pulloutD1T1_tt,pullinT1D1_length,pullinT2D1_length,pullinT1D1_tt,pullinT2D1_tt,pulloutD2T2_length,pulloutD2T2_tt,pullinT1D2_length,pullinT2D2_length,pullinT1D2_tt,pullinT2D2_tt,dutyPeriod,reliefTime,restPeriod,layoverT1,layoverT2):
    allocation_df, shift, cycleTime = allocate_buses(routeNumber, numBuses, tripDuration1, tripDuration2, layoverT1, layoverT2, serviceStart, serviceEnd, terminal1, terminal2, dutyPeriod, reliefTime, restPeriod)
    # print('allocation_df\n', allocation_df, '\n')

    #estimating_trips
    busServiceSpan = serviceEnd - max(allocation_df['serviceStart'])
    timeLost = (shift*restPeriod) + (shift-1)*reliefTime
    cycleTrips = (busServiceSpan-timeLost)/cycleTime
    restPeriodNumber = round(busServiceSpan/dutyPeriod)

    if shift == 2:
        directionalTrips = int(round(cycleTrips) * 2)
    else:
        directionalTrips = round(cycleTrips * 2.0)

    df = pd.DataFrame()
    for i,dp in allocation_df.iterrows():
        scheduleNum = dp['schedule_no']
        startTerminal = dp['start_terminal']
        Departure = dp['serviceStart']

        x = schedule_bus(directionalTrips, scheduleNum, startTerminal, Departure, routeNumber, numBuses,
                     serviceStart, serviceEnd, terminal1, terminal2, depot1, depot2,
                     routeLength1, routeLength2, tripDuration1, tripDuration2, pulloutD1T1_length,
                     pulloutD1T1_tt, pullinT1D1_length, pullinT2D1_length, pullinT1D1_tt, pullinT2D1_tt,
                     pulloutD2T2_length, pulloutD2T2_tt, pullinT1D2_length, pullinT2D2_length,
                     pullinT1D2_tt, pullinT2D2_tt, dutyPeriod, reliefTime, restPeriod, layoverT1,
                     layoverT2, shift, restPeriodNumber)

        df = pd.concat([df, x])
    return df

# schedule = basic_schedule(routeNumber='1A',numBuses=6,serviceStart=300,serviceEnd=1300,terminal1='T1',terminal2='T2',depot1='D1',depot2='D2',routeLength1=10,routeLength2=11,tripDuration1=35,tripDuration2=45,pulloutD1T1_length=0.5,pulloutD1T1_tt=10,pullinT1D1_length=0.5,pullinT2D1_length=11,pullinT1D1_tt=5,pullinT2D1_tt=55,pulloutD2T2_length = 1,pulloutD2T2_tt=5,pullinT1D2_length=11,pullinT2D2_length=2,pullinT1D2_tt=40,pullinT2D2_tt=10,dutyPeriod=8*60,reliefTime=30,restPeriod=30,layoverT1=5,layoverT2=10)

# print('schedule\n', schedule, '\n')
