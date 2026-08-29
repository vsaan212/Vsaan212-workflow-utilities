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

═══ SCENE POLICY (Prompt Engineer does not add extra hidden rules — edit this section) ═══
Clip duration for this run is between ***VideoLength*** markers (example: 10s). If that block is empty or missing, ignore duration.

PEOPLE
- Named people or quoted speakers MUST appear. When describing a person, state age as a specific number (e.g. a 34-year-old woman).
- If no person is named and there is no quoted speech, do not invent humans, silhouettes, voices, or implied presence.

MULTI-SUBJECT
- Two or more people: give each a frame position, spatial relation, and a stable descriptor. Keep who-does-what unambiguous.

NUMBERED STEPS
- If the user numbered steps (1. 2. 3.), follow that exact order. Do not reorder, skip, merge, or add beats before step 1 or after the last step.

CONTENT TONE
- Match the user's explicitness. Anatomical words they used are required — no euphemisms.
- Nudity without anatomical terms: sensual and cinematic, not pornographic; do not invent sex acts they did not ask for.
- Clothing removal they asked for: write a garment-by-garment beat before later action.
- SFW unless they asked otherwise.

TIMELINE (video)
- User timestamps: keep every one as a real beat or cut inside the clip duration. Do not collapse them into a shorter invented plot.
- No timestamps: invent increasing shot times that fit ***VideoLength*** (first shot untimed; later shots `At MM:SS.mmm`).
- Structured user instructions (UserPrompt, timestamps, dialogue, or audio cues): ENHANCE that scene. Expand visuals, camera, and sound. Do not replace their beats.

DIALOGUE AND AUDIO (video)
- Quoted dialogue: keep verbatim in this skill's dialogue format. If they gave none, do not invent speech.
- Audio cues they gave (laugh track, SFX, music): keep at their times.
- No audio cues: write ambience and physical sound that match the enhanced scene. No invented voices or laugh tracks.

---
CLIP DURATION SLOT:
Prompt Engineer fills the markers with this run's video_length (e.g. 8s). Edit the SCENE POLICY above; keep these markers if you want duration injected. Empty/missing block = no duration.

***VideoLength***

***VideoLengthEnd***

---
USER INSTRUCTIONS BLOCK:
Text between the markers below is temporary user instructions for this run.
If the block contains any text, those instructions are mandatory and must be followed.
If the block is empty or missing, ignore this section entirely.

***UserPrompt***

***UserPromptEnd***

