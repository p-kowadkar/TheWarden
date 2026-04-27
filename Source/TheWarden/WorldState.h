#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "WorldState.generated.h"

/**
 * UWorldState
 * Developer-implemented stub for managing the global simulation tick.
 * Tracks time, weather, and global variables.
 */
UCLASS(Blueprintable, BlueprintType)
class THEWARDEN_API UWorldState : public UObject
{
    GENERATED_BODY()

public:
    UWorldState();

    // Real-world minutes per in-game hour (Sprint 1: 3.0f)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Time")
    float TimeScale;

    // Current in-game time (0.0 to 24.0)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Time")
    float CurrentTimeOfDay;

    // Current in-game day
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Time")
    int32 CurrentDay;

    // Weather state machine (0: Overcast, 1: Rain, 2: Clearing, 3: Clear)
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weather")
    int32 WeatherState;

    /**
     * Advances the world simulation by DeltaTime.
     * Called from the GameMode or a global manager tick.
     */
    UFUNCTION(BlueprintCallable, Category = "Simulation")
    void TickSimulation(float DeltaTime);

    /**
     * Checks if it is currently night (10:00 PM to 5:00 AM).
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "Time")
    bool IsNight() const;
};
