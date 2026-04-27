#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "AIBridge.generated.h"

DECLARE_DYNAMIC_DELEGATE_OneParam(FOnNPCResponseReceived, const FString&, ResponseText);

/**
 * UAIBridge
 * Developer-implemented stub for connecting Unreal Engine to the Python FastAPI backend.
 * Handles async communication with the Claude API via UnrealGenAISupport.
 */
UCLASS(Blueprintable, BlueprintType)
class THEWARDEN_API UAIBridge : public UObject
{
    GENERATED_BODY()

public:
    UAIBridge();

    /**
     * Sends a message to the AI backend and triggers the delegate when a response is received.
     * 
     * @param NPCId The unique identifier for the NPC (e.g., "NPC-001" for Oswald).
     * @param PlayerMessage The text input from the player.
     * @param Sanity The player's current sanity level (0.0 to 1.0).
     * @param Relationship The current relationship level with the NPC (0 to 4).
     * @param Evidence Array of collected evidence IDs to inject into the prompt context.
     * @param OnResponse Delegate called when the async response is ready.
     */
    UFUNCTION(BlueprintCallable, Category = "AI")
    void SendNPCMessage(
        FString NPCId,
        FString PlayerMessage,
        float Sanity,
        float Relationship,
        TArray<FString> Evidence,
        FOnNPCResponseReceived OnResponse
    );
};
