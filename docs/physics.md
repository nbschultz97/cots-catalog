# Physics model

Three engineering approximations. **Not a flight simulator.**

## Multirotor hover

Blade-Element / Momentum theory induced power:

$$
P_\text{induced} = (m g) \cdot \sqrt{\frac{m g}{2 \rho A}}
$$

Where:

- $m$ = AUW (kg)
- $g$ = 9.81 m/s²
- $\rho$ = air density (kg/m³)
- $A$ = total disc area = $n_\text{motors} \cdot \pi \cdot r_\text{prop}^2$

Then real electrical power = `P_induced × aero_loss_multiplier ÷ eta_drivetrain`.

`aero_loss_multiplier` is an empirical fudge factor (3-8 depending on
prop diameter) that captures profile drag, tip vortex losses, and
high-disc-loading inefficiencies that pure BEM ignores. Tuned to
published flight times from common FPV builds.

## Multirotor cruise

`endurance_cruise = endurance_hover × cruise_factor`

`cruise_factor` is airframe-class-aware (5-inch ~1.3, 7-inch ~1.75,
flying wing ~2.5).

## Fixed-wing cruise

Simplified Breguet:

$$
P_\text{cruise} = \frac{m g V_\text{cruise}}{(L/D) \cdot \eta_\text{total}}
$$

`(L/D) × eta_total` is treated as a single empirical product per
airframe class (foam FW ~3.5, flying wing ~5, long-endurance ~8) to
match real flight times under low-Reynolds-number conditions.

## Accuracy

- ±25% for multirotor hover
- ±35% for multirotor cruise
- ±40% for fixed-wing cruise

Calibrate against your own build data; defaults are FPV community
rules of thumb.
