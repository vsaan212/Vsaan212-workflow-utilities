===Header===
Model Type: Video
Model Name: LTX 2.3 Screenplay
Media Type: Video; Screenplay Beats + Audio
Is Video: true
Has Audio: true
Prompt:
Write a prompt for LTX Video 2.3 in screenplay format. No preamble, no explanation. Begin immediately with the first character.

OUTPUT — write these sections in order, separated by a blank line. Do NOT write any section headers or labels. Do not write "CHARACTERS", "SCENE", "ACTION + DIALOGUE" or any other label. Just the content.

SECTION 1 — one separate paragraph per character, blank line between them.
Invent a name, age, and full physical description for every character the user did not describe. Be specific: first name, age, hair colour and length, eye colour, skin tone, build, notable physical features. One character per paragraph, nothing else on that line.
Example output for two characters:
Becky, 21. Long natural blonde hair, blue eyes, pale skin, slim build, medium full breasts, small waist, soft hands.

John, 34. Short dark hair, brown eyes, light brown skin, medium-athletic build, broad shoulders, defined chest and abs.

SECTION 2 — one paragraph describing the location.
Time of day, light source and colour temperature, surface textures, atmosphere, ambient sound. Specific and grounded.
Example: A softly lit bedroom at night. Warm amber bedside lamp casting long shadows across white cotton sheets. Dark hardwood floor, city noise muffled behind closed curtains, the low hum of traffic outside.

SECTION 3 onwards — one paragraph per action beat, blank line between each.
Each beat: physical action in present tense, dialogue in "quotes" with voice quality noted, camera move and what it finds, dominant sound. 2–4 sentences per beat. Alternate between characters. Keep actions physically simple — hip movement, weight shifts, reaching, turning, leaning. Do not write complex choreography. Do not write a label before each beat. Just write the paragraph and leave a blank line.
Only write as many beats as the duration needs. When done, stop — do not write a trailing label or empty section.

═══ SPARSE INPUT ENRICHMENT (MANDATORY) ═══
The user often writes one short sentence. Your job is to expand it into a rich, production-ready prompt without changing their intent.

LOCKED FACTS — never drop, weaken, or contradict these:
- Keep every person, place, and action the user named.
- Example lock: "The girl walks down a busy street in NY" → subject is a girl/young woman, action is walking, place is a busy New York City street.

INVENT WHEN MISSING (be concrete, not vague):
- Age as a specific adult number (18+) if unspecified — for "girl" with no age, invent a young adult (e.g. 22–28), never a child.
- Hair (colour, length, style), face cues, body type, clothing with fabric/colour, footwear.
- Exact NYC texture: borough/neighborhood vibe, sidewalk material, storefronts, signage blur, taxis, steam, scaffolding, crowd density — pick ONE coherent block (e.g. SoHo cobble + cast-iron facades, OR Midtown glass + yellow cabs, OR rainy Times Square neon). Do not name-drop every landmark.
- Time of day + weather + season that fit "busy street" (rush-hour dusk, bright noon, wet night after rain, etc.).
- Shot scale, camera position, and one clear camera move (or deliberate static).
- Lighting: source + colour temperature + how it hits skin and wet/dry pavement.
- Background motion: pedestrians crossing, traffic flow, flags, steam, reflections — keep the girl as the hero; crowd stays anonymous atmosphere.

STAY FAITHFUL:
- Do not invent a second main character, a plot twist, or a destination the user did not imply.
- Stay SFW unless the user asked for sensual or explicit content.
- Prefer sensory specificity ("wool coat collar turned up", "heel strikes wet asphalt") over empty intensifiers ("beautiful", "amazing", "stunning").


═══ SPARSE / SFW DEFAULTS (this skill) ═══
When the user is vague, invent a full named character with age and physical description — keep descriptions grounded and SFW unless the user asked for sensual/explicit detail.
Do not default to sexualized body focus for everyday scenes (street, cafe, commute).
Example SFW character line:
Maya, 25. Shoulder-length dark brown hair, hazel eyes, light olive skin, slim athletic build, camel wool coat over a black knit sweater, practical hands.

Location paragraph must make "busy NY street" concrete (time, light, pavement, traffic, crowd sound).
Beats: walking progression only — start mid-block, navigate crowd, pass a storefront, reach a corner — scaled to clip duration. Optional short dialogue with voice quality.

---
USER INSTRUCTIONS BLOCK:
Text between the markers below is temporary user instructions for this run.
If the block contains any text, those instructions are mandatory and must be followed.
If the block is empty or missing, ignore this section entirely.

***UserPrompt***

***UserPromptEnd***
