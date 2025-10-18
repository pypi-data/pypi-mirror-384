import pandas as pd
from .allocation import change_terminal

# Set options to display all rows and columns
pd.set_option('display.max_rows', None)
pd.set_option("display.max_columns", None)   # show all columns
pd.set_option("display.width", None)         # don't wrap to console width

# routeNumber,numBuses,serviceStart,serviceEnd,terminal1,terminal2,depot1,depot2,routeLength1,routeLength2,tripDuration1,tripDuration2,pulloutD1terminal1_length,pulloutD1terminal2_length,pulloutD1terminal1_tt,pulloutD1terminal2_tt,pullinterminal1D1_length,pullinterminal2D1_length,pullinterminal1D1_tt,pullinterminal2D1_tt,pulloutD2terminal1_length,pulloutD2terminal2_length,pulloutD2terminal1_tt,pulloutD2terminal2_tt,pullinterminal1D2_length,pullinterminal2D2_length,pullinterminal1D2_tt,pullinterminal2D2_tt,dutyPeriod,reliefTime,restPeriod,layoverT1,layoverT2

def schedule_bus(directionalTrips, scheduleNum, startTerminal, Departure, routeNumber, numBuses,
                     serviceStart, serviceEnd, terminal1, terminal2, depot1, depot2,
                     routeLength1, routeLength2, tripDuration1, tripDuration2, pulloutD1T1_length,
                     pulloutD1T1_tt, pullinT1D1_length, pullinT2D1_length, pullinT1D1_tt, pullinT2D1_tt,
                     pulloutD2T2_length, pulloutD2T2_tt, pullinT1D2_length, pullinT2D2_length,
                     pullinT1D2_tt, pullinT2D2_tt, dutyPeriod, reliefTime, restPeriod, layoverT1,
                     layoverT2, shift, restPeriodNumber):
    df = pd.DataFrame(columns=['schedule_no', 'trip_no', 'event_type', 'origin', 'dest', 'start_time', 'end_time', 'distance', 'duration', 'crew_no'])

    # start shuttle
    trip_count = 1
    if startTerminal == terminal1:
        start_time = Departure - pulloutD1T1_tt
        orig = depot1
        shuttle_distance = pulloutD1T1_length
        dest = terminal1
        shuttle_duration = pulloutD1T1_tt
    else:
        start_time = Departure - pulloutD2T2_tt
        orig = depot2
        shuttle_distance = pulloutD2T2_length
        dest = terminal2
        shuttle_duration = pulloutD2T2_tt
    end_time = Departure
    df.loc[len(df)] = [scheduleNum, trip_count, 'shuttle', orig, dest, start_time, Departure, shuttle_distance, shuttle_duration, 1]

    trips_per_shift = round(directionalTrips/2)
    trips_in_first_block = int(trips_per_shift/2)
    trips_in_second_block = int(round(trips_per_shift/2))

    # first half - crew 1
    for i in range(trips_in_first_block):
        trip_count += 1
        orig = dest
        dest = change_terminal(orig, terminal1, terminal2)
        start_time = end_time
        if orig == terminal1:
            end_time = start_time + tripDuration1
            trip_distance = routeLength1
            trip_duration = tripDuration1
        else:
            end_time = start_time + tripDuration2
            trip_distance = routeLength2
            trip_duration = tripDuration2

        df.loc[len(df)] = [scheduleNum, trip_count, 'trip', orig, dest, start_time, end_time, trip_distance, trip_duration, 1]

        trip_count += 1
        orig = dest
        start_time = end_time
        if  i+1 < trips_in_first_block:
            if orig == terminal1:
                end_time = start_time + layoverT1
                trip_distance = 0
                trip_duration = layoverT1
            else:
                end_time = start_time + layoverT2
                trip_distance = 0
                trip_duration = layoverT2
            df.loc[len(df)] = [scheduleNum, trip_count, 'layover', orig, dest, start_time, end_time, trip_distance, trip_duration, 1]

    # crew 1 break
    trip_count += 1
    start_time = end_time
    end_time = start_time + restPeriod
    orig = dest
    df.loc[len(df)] = [scheduleNum, trip_count, 'crew break', orig, dest, start_time, end_time, 0, restPeriod, 1]

    # second half - crew 1
    for i in range(trips_in_second_block):
        trip_count += 1
        orig = dest
        dest = change_terminal(orig, terminal1, terminal2)
        start_time = end_time
        if orig == terminal1:
            end_time = start_time + tripDuration1
            trip_distance = routeLength1
            trip_duration = tripDuration1
        else:
            end_time = start_time + tripDuration2
            trip_distance = routeLength2
            trip_duration = tripDuration2

        df.loc[len(df)] = [scheduleNum, trip_count, 'trip', orig, dest, start_time, end_time, trip_distance, trip_duration, 1]

        trip_count += 1
        orig = dest
        start_time = end_time
        if  i+1 < trips_in_second_block:
            if orig == terminal1:
                end_time = start_time + layoverT1
                trip_distance = 0
                trip_duration = layoverT1
            else:
                end_time = start_time + layoverT2
                trip_distance = 0
                trip_duration = layoverT2
            df.loc[len(df)] = [scheduleNum, trip_count, 'layover', orig, dest, start_time, end_time, trip_distance, trip_duration, 1]

    # crew change
    trip_count += 1
    start_time = end_time
    end_time = start_time + reliefTime
    orig = dest
    df.loc[len(df)] = [scheduleNum, trip_count, 'crew change', orig, dest, start_time, end_time, 0, reliefTime, -1]

    # first half - crew 2
    for i in range(trips_in_first_block):
        trip_count += 1
        orig = dest
        dest = change_terminal(orig, terminal1, terminal2)
        start_time = end_time
        if orig == terminal1:
            end_time = start_time + tripDuration1
            trip_distance = routeLength1
            trip_duration = tripDuration1
        else:
            end_time = start_time + tripDuration2
            trip_distance = routeLength2
            trip_duration = tripDuration2

        df.loc[len(df)] = [scheduleNum, trip_count, 'trip', orig, dest, start_time, end_time, trip_distance, trip_duration, 2]

        trip_count += 1
        orig = dest
        start_time = end_time
        if i + 1 < trips_in_first_block:
            if orig == terminal1:
                end_time = start_time + layoverT1
                trip_distance = 0
                trip_duration = layoverT1
            else:
                end_time = start_time + layoverT2
                trip_distance = 0
                trip_duration = layoverT2
            df.loc[len(df)] = [scheduleNum, trip_count, 'layover', orig, dest, start_time, end_time, trip_distance, trip_duration, 2]

    # crew 2 break
    trip_count += 1
    start_time = end_time
    end_time = start_time + restPeriod
    orig = dest
    df.loc[len(df)] = [scheduleNum, trip_count, 'crew break', orig, dest, start_time, end_time, 0, restPeriod, 2]

    # second half - crew 2
    for i in range(trips_in_second_block):
        trip_count += 1
        orig = dest
        dest = change_terminal(orig, terminal1, terminal2)
        start_time = end_time
        if orig == terminal1:
            end_time = start_time + tripDuration1
            trip_distance = routeLength1
            trip_duration = tripDuration1
        else:
            end_time = start_time + tripDuration2
            trip_distance = routeLength2
            trip_duration = tripDuration2

        df.loc[len(df)] = [scheduleNum, trip_count, 'trip', orig, dest, start_time, end_time, trip_distance, trip_duration, 2]

        trip_count += 1
        orig = dest
        start_time = end_time
        if  i+1 < trips_in_second_block:
            if orig == terminal1:
                end_time = start_time + layoverT1
                trip_distance = 0
                trip_duration = layoverT1
            else:
                end_time = start_time + layoverT2
                trip_distance = 0
                trip_duration = layoverT2
            df.loc[len(df)] = [scheduleNum, trip_count, 'layover', orig, dest, start_time, end_time, trip_distance, trip_duration, 2]

    trip_count += 1
    orig = dest
    start_time = end_time
    if startTerminal == terminal1:
        dest = depot1
        if orig == terminal1:
            shuttle_distance = pullinT1D1_length
            shuttle_duration = pullinT1D1_tt
            end_time = start_time + pullinT1D1_tt
        else:
            shuttle_distance = pullinT2D1_length
            shuttle_duration = pullinT2D1_tt
            end_time = start_time+pullinT2D1_tt
    else:
        dest = depot2
        if orig == terminal1:
            shuttle_distance = pullinT1D2_length
            shuttle_duration = pullinT1D2_tt
            end_time = start_time + pullinT1D2_tt
        else:
            shuttle_distance = pullinT2D2_length
            shuttle_duration = pullinT2D2_tt
            end_time = start_time + pullinT2D2_tt

    # print(scheduleNum, orig, dest)
    start_time = end_time
    end_time = start_time + shuttle_duration
    df.loc[len(df)] = [scheduleNum, trip_count, 'shuttle', orig, dest, start_time, end_time, shuttle_distance, shuttle_duration, 2]
    return df
