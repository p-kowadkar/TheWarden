# L_HarrowEstate Level Specification
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
The `L_HarrowEstate` level encompasses the exterior grounds and five specific interior rooms of the Harrow Estate. The environment is designed to convey a sense of maintained but unloved history, set in 1903 Edwardian England.

## 2. World Partition Configuration
The level utilizes UE 5.7's World Partition system to manage streaming. There are no loading screens between the exterior and interior rooms, ensuring a seamless experience.

## 3. The Estate Exterior
The player begins at the estate gate, with the camera opening here.

- **Layout:** A gravel path leads 80 meters from the gate to the main house. The formal garden (Thomas's domain) is to the left; the stable (Oswald's domain) is to the right.
- **Architecture:** The main house is a three-story stone structure with a slate roof, styled in Edwardian architecture.
- **Weather:** The game starts overcast. A dynamic weather system triggers rain approximately 30 minutes after arrival.

## 4. Interior Rooms (Sprint 1 Scope)
The interior consists of five specific rooms, each with distinct narrative and atmospheric requirements.

### 4.1 Entry Hall
- **Description:** Double-height ceiling with a staircase to the right.
- **Features:** Portraits of previous owners on the walls. A side table holds a candlestick, opened correspondence (Evidence `EV_004`), and the Warden's satchel.

### 4.2 The Study
- **Description:** Eleanor's workspace, located on the ground floor, west wing. Organized chaos.
- **Features:** The Sight Lens case (Evidence `EV_001`) is open and empty on the desk. Eleanor's Journal (Partial) (Evidence `EV_003`) is present. A false panel exists behind the bookshelf (inaccessible in Sprint 1). Features a real-time working fireplace.

### 4.3 The Kitchen
- **Description:** The only warm room in the house.
- **Features:** Contains a half-eaten meal from March 14 (Evidence `EV_002`). A locked pantry door (key accessible) hides a Compact supply delivery tin (Evidence `EV_005`).

### 4.4 Library (Exterior)
- **Description:** Located on the ground floor, east wing. The door is locked with a heavy, period-accurate lock.
- **Features:** The interior is visible through the gap but inaccessible. In the Bleed layer, the room has elevated density.

### 4.5 East Wing Corridor
- **Description:** Located on the first floor. The central challenge of Sprint 1.
- **Features:** Dark green, peeling botanical wallpaper. One gas lamp flickers in a consistent 3-1-3 pattern (Evidence `EV_006`). In the Bleed layer, the grief echo of Millicent Grey (Evidence `EV_007`) loops endlessly, reaching for a door that does not exist in the Mundane layer.
