#pragma once
#include "Config.hpp"

namespace hipo {

typedef long long int int64;

int64 HIPO_WIN_API getTickCount(void);
double HIPO_WIN_API getTickFrequency(void);

class HIPO_WIN_API TickMeter
{
public:
    //! the default constructor
    TickMeter()
    {
        reset();
    }

    /**
    starts counting ticks.
    */
    void start()
    {
        startTime = getTickCount();
    }

    /**
    stops counting ticks.
    */
    void stop()
    {
        int64 time = getTickCount();
        if (startTime == 0)
            return;
        ++counter;
        sumTime += (time - startTime);
        startTime = 0;
    }

    /**
    returns counted ticks.
    */
    int64 getTimeTicks() const
    {
        return sumTime;
    }

    /**
    returns passed time in microseconds.
    */
    double getTimeMicro() const
    {
        return getTimeMilli()*1e3;
    }

    /**
    returns passed time in milliseconds.
    */
    double getTimeMilli() const
    {
        return getTimeSec()*1e3;
    }

    /**
    returns passed time in seconds.
    */
    double getTimeSec()   const
    {
        return (double)getTimeTicks() / getTickFrequency();
    }

    /**
    returns internal counter value.
    */
    int64 getCounter() const
    {
        return counter;
    }

    /**
    resets internal values.
    */
    void reset()
    {
        startTime = 0;
        sumTime = 0;
        counter = 0;
    }

private:
    int64 counter;
    int64 sumTime;
    int64 startTime;
};

}


