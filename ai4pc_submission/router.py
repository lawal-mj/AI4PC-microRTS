"""
Builds the strategy-selection prompt sent to the LLM.

Java sends a state block (key=value pairs). We wrap it with an instruction
header that asks the model to pick exactly one rush strategy.
"""

INSTRUCTION = """\
You are choosing a combat doctrine for a MicroRTS bot on an 8x8 map.

Pick exactly ONE label and reply with that label only. No explanation.

Decision procedure (apply in order, take the FIRST that matches):

1. If enemy_heavy >= 1: pick RANGED_RUSH. Heavy units are slow; ranged kites
   them.

2. If enemy_light >= 2: pick HEAVY_RUSH. Heavy outranges and out-tanks Light.

3. If enemy_ranged >= 1: pick LIGHT_RUSH. Light is fast enough to close on
   ranged units before they kite.

4. If tick < 200 AND enemy has NO military units (enemy_light, enemy_heavy,
   enemy_ranged are all 0): pick WORKER_RUSH.
   Reason: on 8x8, the enemy's workers reach our base before any tech is
   ready. Mirroring with workers is the only safe opening.

5. Otherwise (mid-game, enemy still has only workers): pick LIGHT_RUSH.

STICKINESS RULE (apply AFTER the above):
After computing your answer, compare it to `previous_strategy` from the
state. If they match, output that. If they differ, ONLY switch if the
enemy has a unit type now that they didn't before — otherwise output
`previous_strategy`. Switching mid-game without a real reason throws away
units we've already built.

Labels:
  WORKER_RUSH, LIGHT_RUSH, HEAVY_RUSH, RANGED_RUSH

Output exactly one label.

STATE
"""


def build_prompt(state_block: str) -> str:
    return INSTRUCTION + state_block.strip() + "\n"
