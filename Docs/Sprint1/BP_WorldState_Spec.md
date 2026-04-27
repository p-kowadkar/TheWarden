# BP_WorldState & DT_Evidence Specification
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
`BP_WorldState` manages the global simulation tick, tracking time, weather, and global variables. It also manages the evidence system, tracking the 7 Sprint 1 evidence items via the `DT_Evidence` data table.

## 2. BP_WorldState Variables
- `float TimeScale` (Default: 3.0f, 3 real-world minutes = 1 in-game hour)
- `float CurrentTimeOfDay` (Default: 8.0f, 8:00 AM)
- `int32 CurrentDay` (Default: 1)
- `int32 WeatherState` (0: Overcast, 1: Rain, 2: Clearing, 3: Clear)

## 3. Evidence System
The evidence system tracks discoveries and automatically populates the Journal.

- **Collection:** When the player interacts with an evidence item in the world, its ID is added to `CollectedEvidence` in `BP_PlayerWarden`.
- **Notification:** A brief text overlay appears on the HUD (e.g., "Evidence Collected: Eleanor's Sight Lens Case").
- **Journal Update:** The corresponding entry from `DT_Evidence` is unlocked in the `WBP_Journal` Evidence Board.

## 4. DT_Evidence Data Table
The `DT_Evidence` data table contains the 7 Sprint 1 evidence items. The IDs must match exactly.

| Evidence ID | Name | Description | Location |
|-------------|------|-------------|----------|
| `EV_001` | Eleanor's Sight Lens Case | Empty case found on the desk. She had it with her. | The Study |
| `EV_002` | Unfinished Meal | Half-eaten meal from March 14. She left in a hurry. | The Kitchen |
| `EV_003` | Eleanor's Journal (Partial) | Three pages torn out. | The Study |
| `EV_004` | Correspondence on Entry Table | Opened letter, handwriting visible but illegible from a distance. | Entry Hall |
| `EV_005` | Compact Supply Tin | Contains binding components and a note from C.A. | The Kitchen (Pantry) |
| `EV_006` | Corridor Lamp Pattern (East Wing) | Consistent 3-1-3 flicker pattern. Not an electrical fault. | East Wing Corridor |
| `EV_007` | Millicent Grey (Observed) | Semi-animate echo looping near the non-existent door. | East Wing Corridor (Bleed) |
