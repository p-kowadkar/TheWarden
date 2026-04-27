# BP_PlaneManager & BP_SightLens Specification
**Version:** 1.1
**Engine:** Unreal Engine 5.7

## 1. Overview
The `BP_PlaneManager` handles the global transition between the Mundane and Bleed visual states. It works in tandem with `BP_SightLens`, which is the player-facing item that triggers the transition. All visual effects are consolidated into a single post-process material: `M_PostProcess_Sight`.

## 2. BP_PlaneManager
This manager is responsible for interpolating post-process parameters, toggling entity visibility, and managing zone-specific Bleed density.

### 2.1 Transition Specifications
- **Mundane to Bleed Transition:** 1.5-second crossfade.
  - Interpolate `M_PostProcess_Sight` parameters from 0.0 to 1.0.
  - Fade in Bleed entity visibility (e.g., Millicent Grey).
  - Fade in the Bleed ambient audio layer beneath the Mundane audio.
- **Bleed to Mundane Transition:** 1.0-second crossfade (a faster "snap back").
  - Interpolate `M_PostProcess_Sight` parameters from 1.0 to 0.0.
  - Fade out Bleed entity visibility.
  - Fade out the Bleed ambient audio layer.

### 2.2 Zone-Specific Bleed Density
Different locations have different Bleed density levels. This affects entity visibility clarity, ambient sound layer intensity, and the `SightEndurance` drain rate in `BP_PlayerWarden`.

| Zone | Bleed Density |
|------|---------------|
| `Zone_EntryHall` | 0.3f |
| `Zone_Study` | 0.4f |
| `Zone_Kitchen` | 0.1f |
| `Zone_Library_Exterior` | 0.5f |
| `Zone_EastWingCorridor` | 0.8f (Highest in Sprint 1) |
| `Zone_EstateExterior` | 0.2f |

## 3. BP_SightLens
This is the physical item the player uses to activate the Sight.

- **State:** Tracks whether the lens is currently active (`bSightActive` in `BP_PlayerWarden`).
- **Activation:** When the player presses the designated key, `BP_SightLens` calls `BP_PlaneManager` to begin the transition.
- **Endurance Drain:** While active, it continuously drains `SightEndurance` based on the current zone's Bleed density. If endurance reaches 0, it forces deactivation.

## 4. M_PostProcess_Sight Parameters
All Bleed visual effects are consolidated into this single material. The parameters are driven by `BP_PlaneManager` during transitions and by `BP_PlayerWarden` for Sanity effects.

**Core Parameters:**
- `float BleedSaturationMultiplier` (Default: 0.8f, reduces saturation by 20%)
- `float BleedColorTemperatureShift` (Default: -500.0f, shifts Kelvin toward cool)
- `float BleedVignetteIntensity` (Default: 0.3f)
- `float BleedChromaticAberration` (Default: 0.2f)

**Sanity-Driven Parameters:**
- `float SanityAberrationBoost` (Added by the Sanity system in `BP_PlayerWarden` at lower tiers)
- `float SanityDesaturation` (Applied at Sanity tiers 0.6-0.5)
