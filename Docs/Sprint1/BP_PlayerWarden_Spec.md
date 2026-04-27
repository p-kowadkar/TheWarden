# BP_PlayerWarden Specification
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
`BP_PlayerWarden` is the default pawn for the player character. It handles movement, interaction, the Sanity and Sight systems, and inventory tracking. The character operates primarily in third-person, switching to first-person for close object examination.

## 2. Exposed Variables
The following variables must be exposed and accessible to other systems (e.g., UI, Plane Manager, AI Bridge):

- `float SanityLevel` (Default: 1.0, Range: 0.0 to 1.0)
- `float SightEndurance` (Default: 1.0, Range: 0.0 to 1.0)
- `bool bSightActive` (Default: false)
- `int32 RelationshipDay` (Default: 1)
- `TArray<FString> CollectedEvidence` (Empty array)
- `TArray<FString> ActiveSpells` (Empty array)
- `FString CurrentZone` (Default: "Zone_EstateExterior")
- `float TensionLevel` (Default: 0.0, Range: 0.0 to 1.0)

## 3. Movement System
- **Default State:** Third-person perspective.
- **Speed:** Walking pace only indoors. Running is disabled inside the estate to emphasize deliberate, careful movement.
- **Camera Switch:** Auto-switch to first-person perspective when interacting with specific objects (e.g., reading the journal, examining evidence closely).

## 4. Interaction System
- **Prompt:** A single small dot appears centered on the screen when near an interactable object or NPC.
- **Input:** Press 'E' to interact. The dot disappears during the interaction.
- **Logic:** Raycast from the camera center to detect objects implementing the `BPI_Interactable` interface.

## 5. Sanity Tier System
The `SanityLevel` variable drives specific visual and auditory effects. These effects must be implemented exactly as defined below, updating dynamically as Sanity changes.

| Sanity Range | Effect Description | Implementation Notes |
|--------------|--------------------|----------------------|
| **1.0 - 0.8** | No effect. | Base state. |
| **0.7 - 0.6** | Slight chromatic aberration at screen edges only. | Update `M_PostProcess_Sight` parameters. |
| **0.6 - 0.5** | Screen edges desaturated, occasional ambient sound. | Trigger random low-frequency audio cues. |
| **0.5 - 0.4** | Moderate aberration, peripheral Bleed flickers without Sight active. | Briefly flash Bleed post-process at low opacity. |
| **0.4 - 0.3** | Significant distortion, NPC Bleed shadows visible during conversation. | Enable secondary shadow casting on NPCs. |
| **0.3 - 0.2** | Lamp flicker pattern changes (was 3-1-3, now wrong). | Override the East Wing lamp logic to a corrupted pattern. |
| **0.2 - 0.1** | Grief echoes visible without Sight. | Force visibility of Tier 1 echoes (e.g., Millicent Grey) in Mundane state. |
| **0.1 - 0.0** | Placeholder logging only in Sprint 1. | Print string to log: "Sanity Critical". |

## 6. Sight System Integration
- **Input:** Press 'F' (or designated key) to toggle `bSightActive`.
- **Logic:** 
  - When activated, call `BP_PlaneManager` to initiate the Mundane-to-Bleed transition.
  - Begin draining `SightEndurance` based on the `CurrentZone`'s Bleed density.
  - If `SightEndurance` reaches 0.0, force toggle off and apply a Sanity penalty.
  - When deactivated, call `BP_PlaneManager` to initiate the Bleed-to-Mundane transition and begin regenerating `SightEndurance`.
