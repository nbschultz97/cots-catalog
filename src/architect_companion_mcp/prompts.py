"""MCP Prompts — templated workflows the user invokes by slash command.

Each function returns a complete prompt that instructs the LLM how to
use the MCP server's tools to accomplish a common task. These show up
in Claude Desktop / Claude Code as named slash-commands (e.g.,
``/architect_design_build``) once the server is wired in.
"""

from __future__ import annotations

from typing import Optional


def design_build(
    mission: str = "freestyle",
    budget_usd: Optional[float] = None,
    compute_tier: str = "pi5",
    skill: str = "intermediate",
) -> str:
    return f"""Design an FPV / sUAS build using the Architect Companion MCP server.

**Mission:** {mission}
**Budget:** {f"${budget_usd}" if budget_usd else "no fixed budget"}
**Compute tier:** {compute_tier}
**Pilot skill:** {skill}

Use the MCP tools in this order:

1. Call `recommend_configuration(compute_tier="{compute_tier}", mission_type="{mission}", budget_usd={budget_usd or "null"})` to get a starting kit.
2. Inspect the `validation` block on the response. If it reports any
   issues, swap parts via `list_components` with relevant filters and
   re-run `check_compatibility`.
3. For each part in the recommended kit, summarize the tradeoff (cost,
   weight, mission fit) for the user.
4. Compute total cost + AUW + thrust-to-weight via `estimate_thrust`.
5. Estimate endurance via `estimate_flight_time` for both hover and
   cruise modes. Report both.
6. Surface 1-2 swap ideas the user could consider (e.g., a cheaper
   battery, a higher-thrust motor, a lighter VTX) with their tradeoffs.

Keep the final summary concise. Use a markdown table for the build
manifest. Adapt explanations to a {skill} pilot."""


def compare_builds(build_a_ids: str, build_b_ids: str) -> str:
    return f"""Compare two FPV / sUAS builds using the Architect Companion MCP server.

**Build A part IDs:** {build_a_ids}
**Build B part IDs:** {build_b_ids}

For each build:

1. Resolve each part via `get_part`.
2. Run `check_compatibility` over the manifest.
3. Compute estimated thrust + AUW + T/W via `estimate_thrust` on the
   primary motor + airframe + battery triplet.
4. Estimate endurance via `estimate_flight_time` for both hover and
   cruise.

Then produce a side-by-side comparison table with:

- Total cost
- AUW
- T/W ratio
- Hover and cruise endurance
- Compatibility issues (if any)
- Distinguishing strengths and weaknesses

End with a clear recommendation, including the use case where each
build wins."""


def troubleshoot_build(part_ids: str, symptom: str) -> str:
    return f"""Diagnose an FPV / sUAS build issue using the Architect Companion MCP server.

**Build part IDs:** {part_ids}
**Symptom:** {symptom}

1. Resolve every part via `get_part` and confirm the build manifest.
2. Run `check_compatibility` on the build. Surface every issue.
3. Run `estimate_thrust`. If T/W < 2.5, flag underpowered.
4. Run `estimate_flight_time`. Compare to user's expected endurance.

Then map the symptom to likely root causes from the compatibility /
physics output, ranked by probability. For each cause, propose the
specific test the user can run to confirm (e.g., "swap battery to a
higher-C-rating pack and re-test sag under throttle"). End with a
prioritized action list."""


def endurance_what_if(
    airframe_id: str,
    battery_id: str,
    payload_weight_g: float = 0,
) -> str:
    return f"""Run an endurance trade analysis using the Architect Companion MCP server.

**Airframe:** {airframe_id}
**Battery:** {battery_id}
**Payload:** {payload_weight_g}g

1. Baseline: call `estimate_flight_time(airframe_id="{airframe_id}", battery_id="{battery_id}", payload_weight_g={payload_weight_g}, flight_mode="auto")`.
2. Vary payload over [0, 50, 100, 200, 400] g and call again. Tabulate
   AUW vs endurance.
3. Find the heaviest battery in the catalog compatible with the
   airframe (use `list_components` and check voltage compatibility).
   Re-run baseline endurance with it.
4. Compute range via `estimate_range_km` for the best-endurance config.

Produce a markdown table of payload-vs-endurance and a one-paragraph
narrative on the steepest tradeoff. Be honest about the model's
±25-35% accuracy."""


def upgrade_path(current_build_ids: str, goal: str) -> str:
    return f"""Suggest an upgrade path for an existing FPV / sUAS build using the Architect Companion MCP server.

**Current build:** {current_build_ids}
**Goal:** {goal}

1. Resolve the current build via `get_part`. Run `check_compatibility`
   and `estimate_thrust` / `estimate_flight_time` to baseline.
2. Identify the single weakest link relative to the goal (e.g., for
   "more endurance" → battery / motor efficiency; for "smoother
   cinematic" → camera / VTX; for "longer range" → control radio +
   antennas + VTX power).
3. Propose 3 candidate swaps (one cheap, one balanced, one premium)
   using `list_components` filtered by the relevant axis.
4. For each candidate, re-run `check_compatibility` and re-estimate
   thrust / endurance. Surface the delta.

Return a 3-row comparison table (cost delta, weight delta, endurance
delta, T/W delta) and a clear "if budget is X, swap Y" recommendation."""
