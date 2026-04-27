# Audio & Time Specifications
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
Audio and time are critical gameplay systems in THE WARDEN. The audio design relies on layered ambient sounds to convey the Mundane and Bleed states, while the day/night cycle drives environmental changes and NPC behavior.

## 2. Audio Design
The audio system is designed to be informative, not just atmospheric.

### 2.1 Mundane Layer
- **Ambient Sounds:** Period-accurate sounds such as distant birdsong, wind, and the estate's structural settling (e.g., pipes, creaking wood).
- **Dynamic Weather:** Rain audio changes based on the surface it hits (e.g., slate roof vs. gravel path). Occasional distant thunder.
- **Footsteps:** Material-specific footstep audio for both the player and NPCs (e.g., stone, wood, gravel).

### 2.2 Bleed Layer
The Bleed audio layer is added beneath the Mundane layer when the Sight is active.
- **Ambient Resonance:** A very faint, low-frequency structural resonance.
- **Non-existent Sources:** Occasional sounds from sources that aren't there in the Mundane layer (e.g., a voice just below audibility, a door closing).
- **East Wing Corridor:** The silence in this specific corridor absorbs sound slightly, making the player's footsteps quieter than elsewhere.

### 2.3 Entity Audio
- **Grief Echoes:** Produce sound on a loop synchronized with their visual loop. This sound is audible through `Sonus Profundi` without the Sight active.
- **East Wing Lamp:** The lamp flickers with a distinct 3-1-3 audio pattern. This pattern is the clearest sound in the corridor.

## 3. Day/Night Cycle
Time passes in real-time during Sprint 1, affecting lighting, weather, and NPC schedules.

- **Time Scale:** 1 in-game hour = 3 real-world minutes. 1 in-game day = 72 real-world minutes.
- **Nighttime:** From 10:00 PM to 5:00 AM. The exterior becomes navigable only by the light of a lantern carried by the player. Oswald is in his cottage and does not answer the door after 9:00 PM.

### 3.1 East Wing Lamp Time-of-Day Variant
The 3-1-3 flicker pattern of the East Wing lamp is time-of-day driven.
- **Midnight Change:** At exactly midnight, the pattern changes to a different sequence.
- **Journal Logging:** This changed pattern is not decodable in Sprint 1. However, on the player's first midnight visit to the corridor, the journal automatically logs the change.
- **Distinction:** This is a world-state change, separate from the Sanity-driven pattern corruption that occurs at Sanity tier 0.3-0.2.
