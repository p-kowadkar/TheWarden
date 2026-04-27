#include "WorldState.h"

UWorldState::UWorldState()
{
    TimeScale = 3.0f; // 3 real-world minutes = 1 in-game hour
    CurrentTimeOfDay = 8.0f; // Start at 8:00 AM
    CurrentDay = 1;
    WeatherState = 0; // Start overcast
}

void UWorldState::TickSimulation(float DeltaTime)
{
    // STUB - Developer implements full tick logic
    // Advance time based on TimeScale
    float InGameHoursPassed = DeltaTime / (TimeScale * 60.0f);
    CurrentTimeOfDay += InGameHoursPassed;

    if (CurrentTimeOfDay >= 24.0f)
    {
        CurrentTimeOfDay -= 24.0f;
        CurrentDay++;
    }

    // Weather state machine logic goes here
    // e.g., trigger rain after 30 real-world minutes
}

bool UWorldState::IsNight() const
{
    return (CurrentTimeOfDay >= 22.0f || CurrentTimeOfDay < 5.0f);
}
