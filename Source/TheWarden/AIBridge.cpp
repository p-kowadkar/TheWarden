#include "AIBridge.h"

UAIBridge::UAIBridge()
{
    // Constructor
}

void UAIBridge::SendNPCMessage(
    FString NPCId,
    FString PlayerMessage,
    float Sanity,
    float Relationship,
    TArray<FString> Evidence,
    FOnNPCResponseReceived OnResponse)
{
    // STUB - Developer implements this
    // 1. Serialize parameters to JSON
    // 2. Send async request to Python FastAPI backend via UnrealGenAISupport
    // 3. Handle response and trigger OnResponse delegate
    
    // Temporary canned response for Sprint 1 testing
    FString CannedResponse = TEXT("I'm sorry, I don't have much to say about that right now.");
    
    if (NPCId == TEXT("NPC-001"))
    {
        if (PlayerMessage.Contains(TEXT("Eleanor")))
        {
            CannedResponse = TEXT("She left in a hurry. That's all I know.");
        }
        else if (PlayerMessage.Contains(TEXT("lake")))
        {
            CannedResponse = TEXT("I don't go near the water. Neither should you.");
        }
    }
    
    // Simulate network delay
    // In a real implementation, this would be an async callback
    OnResponse.ExecuteIfBound(CannedResponse);
}
