# BP_NPC_Oswald Specification
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
`BP_NPC_Oswald` is the only fully implemented NPC in Sprint 1. He uses a MetaHuman character model and operates on a strict daily schedule. He interacts with the player via the `BP_AIBridge` stub.

## 2. Exposed Variables
- `FString NPCId` (Default: "NPC-001")
- `int32 RelationshipLevel` (Default: 0, Range: 0 to 4)
- `bool bIsTalking` (Default: false)
- `FVector CurrentDestination` (Driven by schedule)

## 3. Schedule System
Oswald's location and behavior are driven by the `CurrentTimeOfDay` variable in `BP_WorldState`.

| Time | Activity | Location |
|------|----------|----------|
| **5:30 AM** | Lights boilers | Estate exterior, near main house |
| **6:00 AM** | Stable check | Stable |
| **7:00 AM - 12:00 PM** | Grounds maintenance | Formal garden / grounds |
| **12:00 PM - 1:00 PM** | Lunch | Groundskeeper cottage |
| **1:00 PM - 4:00 PM** | Town errands | Off-map (or pathing toward gate) |
| **4:00 PM - 6:00 PM** | Evening stable check | Stable |
| **6:00 PM onward** | In cottage | Groundskeeper cottage (Does not answer door after 9:00 PM) |

## 4. Interaction & AI Bridge Integration
- **Interaction:** When the player interacts with Oswald, the `WBP_DialoguePanel` opens.
- **Dialogue Flow:**
  1. Player inputs text.
  2. `BP_NPC_Oswald` calls `SendNPCMessage` on the `BP_AIBridge` component.
  3. Passes `NPCId`, player text, current `SanityLevel`, `RelationshipLevel`, and `CollectedEvidence`.
  4. While waiting for the async response, Oswald plays a "thinking" or "listening" idle animation.
  5. When the delegate fires, the response is displayed in the `WBP_DialoguePanel`.

## 5. Relationship Progression (Sprint 1)
In Sprint 1, relationship progression is simplified. `RelationshipLevel` increments by 1 for each unique in-game day the player speaks to him, up to a maximum of 2. (Levels 3 and 4 require specific narrative triggers not present in Sprint 1).
