"""Environment presets for LazyPrompt (location, lighting, sound). Ported from Gemma4Prompt."""

ENVIRONMENT_PRESETS = {
    "None — LLM decides": None,
    "🎲 Random — seed picks": "RANDOM",

    # ── NATURAL ──────────────────────────────────────────────────────────
    "🏖 Beach — golden hour": (
        "wide open beach at golden hour, warm amber light raking low across wet sand, "
        "shallow surf foaming in irregular sheets over the flat shore, "
        "distant horizon blurred with sea haze, seaweed and shell fragments at the tide line, "
        "salt crust on every exposed surface, damp sand firm underfoot then soft further up the beach",
        "warm directional sidelight from the low sun, long soft shadows stretching inland, "
        "orange-gold palette with deep blue shadows pooling in the wet sand troughs",
        "rolling waves building and collapsing, wind-carried spray hissing across the sand, "
        "distant gulls, the hollow clap of a wave folding on itself"),

    "🏔 Mountain peak — dawn": (
        "exposed mountain summit at first light, vast sky opening below in every direction, "
        "cold thin air, bare grey-brown rock underfoot fractured into angular plates, "
        "pale blue and rose light spreading from the east across cloud layers far below, "
        "distant ranges stretching to a gently curved horizon, breath visible in the cold",
        "cold directional dawn light from the east, high contrast, no fill light, "
        "long purple shadows from every ridge and rock formation, rose-to-blue sky gradient",
        "wind building and fading in slow gusts, deep silence between them, "
        "the creak of cold rock contracting, faint echo from the valley below"),

    "🌲 Dense forest — diffused green": (
        "deep forest interior, canopy dense and fully closed 20 metres overhead, "
        "light filtering down in soft broken columns through layered leaves, "
        "moss-covered ground, ferns at knee height filling every gap between roots, "
        "standing water in root depressions reflecting green light back upward, "
        "bark textured with lichen and fungal rings, the space between trunks creating receding depth",
        "diffused green-filtered light with no hard shadows, uniform soft fill from the canopy above, "
        "every surface tinted with reflected chlorophyll green",
        "birdsong in overlapping species layers, wind audible in the canopy but absent at ground level, "
        "a dry leaf shifting somewhere unseen, distant running water"),

    "🌊 Underwater — shallow reef": (
        "shallow tropical reef underwater, clear turquoise water with 20-metre visibility, "
        "shafts of broken sunlight refracting through the rippling surface in caustic patterns, "
        "staghorn and brain coral formations in soft focus below, "
        "small fish holding station in the gentle current, everything moving in slow surge rhythm",
        "caustic light patterns dancing across every surface from above, "
        "high-key teal-blue overall, darker blue fading into depth below",
        "muffled pressure, the steady rise of bubbles, distant boat hull drone, "
        "the creak of coral in the current"),

    "🌧 Rain-soaked city street — night": (
        "rain-soaked urban street at night, wet asphalt reflecting neon signs "
        "in elongated distorted colour streaks, steam rising from iron grates in the road, "
        "pools of amber streetlight surrounded by dark, blurred traffic in background, "
        "awnings dripping, gutters running",
        "neon colour reflections in puddles — red, blue, white, amber — "
        "cool blue ambient fill, warm sodium overhead streetlamps",
        "rain on pavement in constant hiss, distant traffic, "
        "wet tyre sound on asphalt, footsteps echoing under an awning"),

    "🏜 Desert — midday heat": (
        "open desert at midday, bleached pale sand extending to a dead-flat horizon, "
        "air rippling with heat shimmer low above the ground, "
        "sky a brilliant white-blue with no cloud, no shade, no landmarks, "
        "surface cracked into geometric plates closer to the foreground",
        "brutal overhead sun, harsh vertical top-light with zero shadow relief, "
        "bleached palette — near-white sand, white-blue sky, black under anything that casts shade",
        "silence — then wind — then silence again, fine sand skittering across the crust"),

    "🌌 Night sky — open field": (
        "open field under a fully clear night sky, grass running to a dark horizon, "
        "the Milky Way arcing overhead in a dense band of blue-white stars, "
        "no artificial light source, ground-level detail barely visible in deep blue-black ambient",
        "starlight only, near-black ambient, faint blue-grey top-light from the sky itself, "
        "the Milky Way core casting a measurable soft gradient",
        "crickets in continuous layers, light wind through the grass, "
        "a frog somewhere, the profound silence beneath everything"),

    "🌁 Rooftop — city at night": (
        "high rooftop at night, city skyline spreading in every direction below, "
        "warm glow rising from the streets like a second horizon, "
        "wind at this height, ventilation stacks and water tanks breaking the flat roof surface, "
        "a parapet at the edge with the drop visible beyond it",
        "city glow from below as warm amber fill, cool blue sky above, "
        "backlit silhouette potential against the lit skyline",
        "distant city hum rising and falling, wind, "
        "an occasional siren rising from far below and fading"),

    "✈ Plane cockpit — cruising altitude": (
        "aircraft cockpit at cruising altitude, instrument panel spread in amber and green glow, "
        "black sky through the windshield, stars visible above the cloud layer, "
        "the vibration and low hum of engines constant beneath everything, "
        "oxygen mask clips and circuit breakers detailed on the overhead panel",
        "instrument panel glow from below — warm amber dials, green digital readouts — "
        "cool black from the windshield, no natural light",
        "engine hum constant and enveloping, radio static between calls, "
        "pressurised air hiss from the vents, the occasional click of switches"),

    # ── INTERIOR ─────────────────────────────────────────────────────────
    "🏠 Bedroom — warm evening": (
        "warm bedroom interior in the evening, a single bedside lamp casting a pool of amber light, "
        "soft shadow in the far corners, bed linen slightly rumpled with the weight of use, "
        "curtains drawn against the dark outside, a glass of water on the nightstand",
        "warm tungsten point source from the bedside lamp, soft falloff, "
        "intimate amber glow, deep shadow beyond its reach",
        "rain against the window glass if it's raining, or the distant low hum of the city through double glazing, "
        "the bed shifting under weight, fabric sliding on fabric, "
        "a phone on the nightstand screen briefly lighting then going dark, "
        "breathing — the rhythm and depth of it — the only sound that belongs to the room itself"),

    "🛁 Bathroom — steam and tile": (
        "steam-filled bathroom, a hot shower running behind frosted glass, "
        "white tile walls beaded with condensation, mirror completely fogged over, "
        "damp warm air thick enough to see, a folded towel on the rail, "
        "soap residue on the tile floor",
        "diffused warm light through frosted glass — soft, hazy, no hard edges, "
        "the steam itself lit from within",
        "shower hiss steady behind glass, water hitting tile, "
        "a slow drip from the tap, muffled echo in the tiled space"),

    "🪟 Penthouse — floor-to-ceiling glass": (
        "high-floor penthouse interior with floor-to-ceiling glass on two walls, "
        "city spread far below, clean minimal interior — low furniture in dark leather and pale stone, "
        "daylight flooding in from the glass wall, the room reflected in the glass at certain angles",
        "natural daylight through glass — even, cool, diffused by height and haze — "
        "city providing a continuous ambient glow from below at night",
        "near-silence — the city thirty floors below reduced to a formless low frequency hum, "
        "the building's HVAC cycling barely audible, glass creaking faintly in wind at this height, "
        "ice settling in a glass, the sound of someone's breathing amplified by the quiet, "
        "and the occasional deep resonant vibration of the building itself moving"),

    "🎹 Jazz club — late night": (
        "intimate jazz club late at night, low ceiling with exposed brickwork, "
        "small stage lit warm at the far end, tables pressed close together, "
        "a candle stub on each table burning low, smoke visible in the stage light, "
        "a bar along one wall with backlit bottles",
        "warm tungsten stage wash, candle fill table by table, "
        "deep shadow in the corners and upper walls",
        "a jazz trio — upright bass, brushed snare, and a tenor saxophone — playing a slow blues "
        "at the far end of the room, the saxophone filling the space and bending at the end of each phrase, "
        "the bassist walking the changes in a low steady pulse, brushes on the snare barely louder than breathing, "
        "a glass set down on the bar between phrases, low conversation that stops "
        "when the sax player leans into a long held note, "
        "the specific intimate acoustic of a low ceiling that puts the music right inside the chest"),

    "🚂 Train — moving through night": (
        "train carriage moving at night, window showing dark landscape "
        "with scattered lights passing in rhythm, warm interior against the cold black outside, "
        "moving reflections of the carriage interior in the glass, "
        "seats in worn fabric, the rhythmic sway of the carriage",
        "warm interior tungsten against total black window exterior, "
        "moving reflections layered over the dark passing world",
        "rhythmic track click accelerating and decelerating on curves, "
        "engine vibration through the floor, the world passing outside muffled by glass"),

    "💊 Underground club — strobes and bass": (
        "underground club at full capacity, strobes cutting the dark in sharp white intervals, "
        "bass pressure felt in the chest before it is heard, crowd pressed together in the dark, "
        "a DJ booth visible through smoke at the far end, coloured wash lights sweeping low",
        "stroboscopic white cuts, colour wash through smoke — purple, red, blue — "
        "near-black between flashes, faces caught in freeze-frame light",
        "bass at physical volume, the crowd as a breathing mass of sound, "
        "the specific compression of a room built for this volume"),

    "🏢 Office — after hours": (
        "corporate office after hours, desks empty and personal items abandoned mid-day, "
        "flat cold overhead fluorescent across an open-plan floor, "
        "city visible through floor-to-ceiling glass on one wall, "
        "the quality of silence that fills a building after everyone has left",
        "flat cold fluorescent overhead, warm city glow through the glass, "
        "clinical blue-white palette, long shadows from desk furniture",
        "air conditioning hum at low frequency, a distant elevator, "
        "the silence of an empty building with one person in it"),

    "🚗 Car — moving at night": (
        "car interior at night, moving through a lit city, streetlights sweeping "
        "through the windows in rhythmic pulses of amber and shadow, "
        "dashboard instruments glowing warm from below, city blurred and wet outside, "
        "the close interior smell of upholstery and warm electronics",
        "rhythmic streetlight sweeps through the windows, "
        "warm dashboard glow from below, moving pattern of light and shadow across interior surfaces",
        "engine, tyres on wet road, city muffled by glass, "
        "faint radio under everything"),

    # ── ICONIC LOCATIONS ─────────────────────────────────────────────────
    "🏰 Big Ben — Westminster at night": (
        "standing directly beneath the Elizabeth Tower on the Westminster Bridge approach, "
        "the illuminated clock face filling the upper frame, warm floodlit limestone glowing gold "
        "against a deep navy sky, the Thames visible beyond the stone parapet, "
        "black iron lampposts lining the bridge behind, black cabs and buses passing in soft blur",
        "warm sodium floodlighting on the tower face, cold blue ambient sky, "
        "wet stone reflecting gold below, the clock face its own light source",
        "distant Big Ben chime on the quarter, Thames wind across the bridge, "
        "traffic crossing behind, footsteps on stone"),

    "🗽 Times Square — peak night": (
        "standing at the centre of Times Square at 2am, surrounded by skyscrapers "
        "sheathed in animated LED billboards — saturated reds, whites, yellows cascading down the canyon walls, "
        "NASDAQ ticker scrolling, yellow cabs streaming through the intersection, "
        "tourists in every direction, steam rising from road grates",
        "total ambient saturation — no single source, light arriving simultaneously from every direction, "
        "colour-shifting as the billboards cycle",
        "traffic, crowd hum, distant busker, NYPD siren one block over, "
        "the specific sound of a city that never quietens"),

    "🗼 Eiffel Tower — sparkling midnight": (
        "standing on the Champ de Mars facing the Eiffel Tower at midnight, "
        "the hourly light show in full effect — 20,000 gold bulbs sparkling in random sequence "
        "across the iron lattice, the Seine to the left catching the glow, "
        "Parisian apartment blocks framing both sides, a few couples on the lawn nearby",
        "gold sparkle wash from the tower varying every second, "
        "deep blue ambient sky, distant street lamp orange at the park edges",
        "city ambience, wind across the park, the faint metallic creak of the iron structure, "
        "distant traffic on the quai"),

    "🌉 Golden Gate Bridge — fog morning": (
        "standing mid-span on the Golden Gate Bridge walkway, "
        "thick morning fog rolling in from the Pacific and swallowing the south tower completely, "
        "only the top third of the north tower visible above the fog line, "
        "the bridge roadway disappearing into white in both directions, "
        "the bay invisible below, cold salt air, the bridge's suspension cables vanishing into cloud",
        "flat diffuse fog light — directionless, grey-white, no shadows, "
        "every surface equally softened, the towers fading to silhouette then to nothing",
        "wind through the cables producing a low resonant hum that changes pitch with gusts, "
        "foghorn in the bay, distant muffled traffic"),

    "🏯 Japanese shrine — early morning": (
        "ancient Shinto shrine at first light, stone torii gate at the entrance "
        "casting a long shadow down the gravel path, stone lanterns lining both sides, "
        "cedar trees so tall the canopy closes overhead, "
        "moss on every stone surface, a single paper lantern still lit from overnight at the main hall",
        "cool blue pre-dawn light filtering through cedar, "
        "warm paper lantern glow at the gate, raking first light beginning on the gravel",
        "wind through cedar boughs, gravel shifting underfoot, "
        "distant temple bell, water dripping from a stone basin"),

    "🌆 Tokyo Shibuya crossing — night": (
        "the Shibuya scramble crossing at night between signal changes, "
        "hundreds of people streaming in every direction simultaneously, "
        "Shibuya 109 building and its neon crown directly ahead, "
        "rain-slicked asphalt reflecting every sign and screen in doubled colour, "
        "7-Eleven and Starbucks glowing warm through steam",
        "neon and LED saturation from every angle — amber, white, red, blue — no hard shadows, "
        "everything doubled in the wet ground",
        "crossing signal tone, crowd footsteps, idling cars, "
        "distant J-pop from a store entrance, the specific density of Shibuya at night"),

    "🌊 Amalfi Coast — cliff road": (
        "narrow coastal road cut directly into the Amalfi cliff face, "
        "turquoise Mediterranean far below catching direct sun and breaking white on the rocks, "
        "no barrier on the seaward side of the road, "
        "lemon groves terraced into the hillside above, "
        "a white-painted village visible across the bay in the afternoon haze",
        "Mediterranean full sun — hard, directional, high contrast, "
        "deep shadows in the cliff cuts, warm gold on the road surface",
        "sea wind, waves far below, a distant scooter engine, "
        "cicadas in the lemon trees above"),

    "🏖 Maldives — overwater bungalow at dusk": (
        "wooden deck extending directly over the lagoon from an overwater bungalow, "
        "water below so clear the sand and coral are visible in turquoise and white, "
        "dusk turning the horizon to a band of orange fading through pink to violet, "
        "the Indian Ocean completely flat, other bungalows in a line behind, "
        "a rope ladder descending from the deck edge into the glowing water",
        "last light warm orange from the horizon, cool violet sky above, "
        "water reflecting both colours simultaneously",
        "water lapping at the stilts below the deck in slow irregular rhythm, "
        "a wind chime on the bungalow moving in the sea breeze, "
        "a distant boat engine somewhere out on the lagoon, "
        "the reef making its evening clicks and pops beneath the surface, "
        "a fruit bat passing overhead, and underneath all of it the oceanic silence of open water at dusk"),

    "🎪 Coachella — main stage sunset": (
        "main Coachella stage at golden hour, the Indio desert stretching to the horizon behind the crowd, "
        "mountains blue and distant in the haze, the stage framed by its giant LED screen "
        "showing warm amber graphics matching the sunset, "
        "tens of thousands on the flat desert floor, dust haze in the air, flags and totems swaying",
        "golden hour desert sun from the west, warm amber fill from the stage screens, "
        "everything amber-soaked and backlit",
        "festival crowd roar, bass from the PA crossing the desert, "
        "the dry desert wind, helicopter overhead"),

    "🌃 Seoul Han River bridge — night": (
        "walking the pedestrian lane of the Banpo Bridge at night, "
        "Seoul's skyline reflected in the Han River below in a long shimmering stripe, "
        "the Moonlight Rainbow Fountain arcing jets of lit water from the bridge rail, "
        "apartment towers in every direction, Namsan Tower with its crown visible on the hill",
        "bridge lighting warm white, fountain colour wash cycling, "
        "Seoul skyline ambient glow on the water surface",
        "water jets from the fountain, Han River wind, "
        "distant city, a passing tour boat"),

    "🏔 High-altitude snowfield": (
        "open snowfield at high altitude, no trees, no shelter, "
        "snow surface wind-sculpted into slow sastrugi waves, "
        "a single ridge of darker rock breaking the white in the far distance, "
        "sky a deep near-violet blue at this altitude, "
        "breath visible in long plumes, footstep tracks the only mark on the surface",
        "flat overcast bounce off the snow — sourceless, directionless white light, "
        "everything equally lit, no shadows, the snow itself the only light source",
        "wind — and nothing else — occasionally a snow grain skittering across the surface crust"),

    "🚇 NYC subway platform — 3am": (
        "empty New York City subway platform at 3am, "
        "tiled walls in grimy institutional cream and brown, "
        "fluorescent tubes overhead with one flickering on a slow cycle, "
        "gum-stained concrete, yellow warning stripe at the platform edge, "
        "a distant rumble building to a full roar as a train approaches and passes without stopping",
        "flat fluorescent overhead, one tube flickering, "
        "the train's headlight briefly sweeping the tunnel end",
        "train rumble building and fading, platform PA echo, "
        "a distant busker's note floating from the next platform"),

    "🌅 Santorini caldera — dawn": (
        "whitewashed terrace on the caldera rim in Santorini at first light, "
        "the volcanic caldera dropping sheer below, the Aegean spread to the horizon in deep blue, "
        "blue-domed churches clustered on the clifftop in the middle distance, "
        "bougainvillea cascading over the terrace wall in magenta",
        "first light pale gold on the white walls, deep blue sea and sky, "
        "magenta flower accent, the white walls almost glowing",
        "Aegean wind, a distant church bell, a boat engine somewhere far below"),

    "🏟 Empty stadium — floodlit night": (
        "standing alone on the pitch of a major football stadium at night, no crowd, "
        "the four giant floodlight rigs pouring hard white light down onto the turf, "
        "stands empty in darkness beyond the light line, "
        "the pitch surface wet from sprinklers, scoreboard dark",
        "four-point overhead flood — hard white industrial light, "
        "deep shadow in the empty stands beyond the light boundary",
        "floodlight hum at low constant frequency, wind across the open bowl, "
        "a single flag snapping on the roof"),

    "🎻 Vienna opera house — empty stage": (
        "standing alone on the stage of the Vienna State Opera between performances, "
        "grand proscenium arch overhead, six tiers of red velvet boxes receding into darkness, "
        "a single work light — a bare bulb on a stand — the only source on stage, "
        "the ghost light casting long shadows across the boards",
        "single bare bulb ghost light — hard, warm, tungsten — "
        "everything else in dense theatrical dark, the boxes invisible",
        "the ghost light's single bulb humming faintly at low frequency, "
        "the vast room holding its breath — the acoustic of 2000 empty velvet seats absorbing all reflection, "
        "a board creaking once under shifting weight, "
        "the heating system deep in the walls ticking, "
        "and the profound specific silence of a concert hall built for music "
        "when the music has stopped — a silence with shape and texture"),

    "🌿 Amazon jungle interior": (
        "deep Amazon rainforest interior with no sky visible, "
        "canopy 40 metres overhead and fully closed, "
        "light arriving only as occasional single shafts breaking through the layers, "
        "forest floor a tangle of buttress roots and fern, "
        "something moving in the mid-canopy unseen and continuous",
        "green-filtered indirect light, permanent green shade, "
        "occasional single shaft of direct sun breaking through, "
        "everything in the same flat green ambient",
        "constant insect layer at full volume — the Amazon roar — "
        "bird calls cutting through, distant water, drip from leaves"),

    "🧊 Ice hotel — Lapland": (
        "interior of an ice hotel room in Lapland in deep winter, "
        "walls, ceiling and furniture carved entirely from glacier ice, "
        "sleeping reindeer skins draped over ice bed frames, "
        "the walls faintly glowing blue-white from ice thickness, "
        "breath visible in every shot, everything translucent",
        "ambient blue-white glow through the ice walls — sourceless, cold, crystalline — "
        "no artificial light, the ice itself luminous",
        "near-total silence — only the creak of settling ice and breath, "
        "occasionally the distant howl of wind outside"),

    "🏬 Tokyo convenience store — 3am": (
        "Lawson or 7-Eleven interior in Tokyo at 3am, completely deserted, "
        "fluorescent lights at full brightness, every shelf perfectly faced and stocked, "
        "hot foods rotating in their case by the register, "
        "rain audible on the pavement outside, "
        "the automatic door briefly opening to let in cold air and admit no one",
        "flat harsh fluorescent overhead — clinical white, no shadows, "
        "everything overlit in that specific convenience store way",
        "refrigerator hum, hot case motor, rain outside, "
        "the door's pneumatic hiss and seal"),

    "🛕 Angkor Wat — golden hour": (
        "standing at the western causeway of Angkor Wat at sunrise, "
        "the five towers reflected in the rectangular moat below, "
        "warm orange light catching every carved sandstone spire, "
        "jungle visible above the outer walls in every direction, "
        "lotus blossoms floating on the moat surface, a monk crossing in the distance",
        "direct low sunrise orange from the east, long shadows down the causeway, "
        "warm pink sky reflected in still water",
        "jungle birds, water lapping the moat edge, distant chanting, "
        "the complete stillness of early morning before tourists arrive"),

    # ── HORROR ───────────────────────────────────────────────────────────
    "🏚 Abandoned building — dark interior": (
        "derelict interior — a former house or institution stripped back to bare structure, "
        "plaster fallen from walls exposing dark brick, floorboards rotted through in patches, "
        "a single doorway open to a deeper corridor beyond, debris underfoot, "
        "curtains torn and hanging at a broken window, rust stains tracking down every wall",
        "single motivated light source only — a torch beam, a crack of moonlight through a board, "
        "a bare bulb on a frayed wire just barely working — everything beyond its reach is near-black",
        "structural settling sounds — a distant creak, something dripping, wind through a gap, "
        "the specific silence of a space that hasn't had a person in it for years — then it does"),

    "🏥 Hospital corridor — fluorescent night": (
        "long hospital corridor at night, linoleum floor with a worn central track, "
        "institutional cream walls with a dado rail at waist height, "
        "a row of numbered doors receding in both directions, one door ajar at the far end, "
        "an overturned wheelchair near the nurse's station, a clipboard on the floor",
        "overhead fluorescent strip lights — two out, one flickering at irregular intervals, "
        "the working ones casting cold blue-white, long green-tinged shadows on the floor",
        "the flicker hum of the failing fluorescent, distant HVAC, a door somewhere closing softly, "
        "the squeak of something on the linoleum floor at the far end of the corridor"),

    "🌲 Haunted woods — dead of night": (
        "dense forest at night, canopy completely blocking the sky, "
        "bare or near-bare trees with high branches interlocked overhead, "
        "root-broken ground underfoot, a faint path barely distinguishable from the surrounding forest floor, "
        "mist at knee height in a clearing visible through the trees ahead, "
        "a structure — the suggestion of one — barely visible in the dark beyond the clearing",
        "no ambient light — torch beam only, or moonlight arriving at odd angles through gaps in the canopy, "
        "blue-black shadow everywhere the light doesn't reach, mist catching and holding any beam",
        "wind in the upper canopy — audible but not felt at ground level — "
        "an owl somewhere, a branch snapping under weight in a direction the camera hasn't looked yet"),

    # ── SPAGHETTI WESTERN ────────────────────────────────────────────────
    "🏜 Ghost town — high noon standoff": (
        "abandoned western town, main street wide enough for a wagon, "
        "false-front wooden buildings on both sides — general store, saloon, sheriff's office — "
        "all long-abandoned, paint peeling, a tumbleweed lodged against a hitching post, "
        "dust rising from the street in a slow gust, shutters banging on a broken hinge, "
        "a single figure at each end of the street, heat shimmer between them",
        "brutal noon sun directly overhead — no shadow, no relief, every surface bleached near-white, "
        "sky a deep saturated blue with no cloud, the sun itself the only light source",
        "wind — nothing else — then the wind stops — then silence so deep the heartbeat is audible — "
        "a shutter bangs once — and then nothing again"),

    "🌵 Open desert — late afternoon heat": (
        "flat desert extending to a dead horizon in every direction, "
        "cracked salt flats closer, red dust further out, a distant mesa barely distinguishable from sky, "
        "a single dead tree on the left edge of frame, a buzzard circling high, "
        "heat shimmer turning the horizon liquid, no road, no structure, no shade anywhere",
        "late afternoon sun at 20° — long amber shadows stretching hard to the left, "
        "warm orange-red on every surface, deep purple shadow in any depression, "
        "sky transitioning from pale blue at zenith to deep amber at the horizon",
        "wind carrying fine dust, a distant hawk, the creak of the dead tree, "
        "and total silence underneath everything — the silence of a landscape indifferent to people"),

    "🍺 Frontier saloon — dusk interior": (
        "interior of a frontier-era saloon, long bar of bare wood on the left, "
        "a mirror behind it age-spotted and dark, bottles in uneven rows, "
        "six or seven tables with mismatched chairs, sawdust on the floor, "
        "a piano in the far corner, a staircase to rooms above, "
        "wanted posters on the wall beside the door, dust motes in the late light",
        "late sun through two windows — long amber shafts cutting through dust, "
        "oil lamp practicals on the bar already lit against the coming dark, "
        "deep shadow in the corners and beneath the staircase",
        "an upright piano in the corner playing a ragtime waltz — slightly out of tune on the high strings, "
        "the pianist visible only as a silhouette — someone drinking alone at the bar, "
        "a chair scraping on floorboards, spurs on the wooden floor as someone stands, "
        "a glass set down hard on the bar top, the staircase creaking under descending weight, "
        "and underneath it all the wind outside finding every gap in the timber walls"),

    # ── DREAMCORE / LIMINAL ──────────────────────────────────────────────
    "🛒 Empty shopping mall — fluorescent liminal": (
        "large shopping mall completely empty of people, long corridors of shuttered storefronts "
        "stretching in both directions, the shutters all down and locked, "
        "a few abandoned planters with dead or fake plants, "
        "a central atrium with a dry fountain, escalators running with no one on them, "
        "the carpet slightly different patterns at each junction suggesting years of piecemeal replacement",
        "overhead fluorescent grid — full brightness, slightly blue-white, no shadows anywhere, "
        "the specific flat even light of a space designed for commerce that no longer happens",
        "the escalators' constant mechanical hum, the HVAC cycling, "
        "a distant jingle from a speaker playing to no one, "
        "footsteps that shouldn't be there echoing from somewhere further in"),

    "🏫 School corridor — after hours": (
        "secondary school corridor at night, lockers running the full length of both walls, "
        "some hanging open, one with a torn photo still attached to the inside door, "
        "classroom doors with small rectangular windows, the rooms dark beyond them, "
        "emergency exit sign at the far end the only non-fluorescent light source, "
        "a forgotten backpack on the floor, a classroom door ajar showing empty desks",
        "overhead fluorescent at half — the end nearest the exit sign off, "
        "creating a gradient from lit to near-dark toward the emergency exit's green cast",
        "the fluorescent buzz, a locker door swinging slightly in a draught, "
        "the distant sound of something institutional — a boiler, a clock — "
        "and the specific silence of a building built for noise now completely empty"),

    "🟨 Backrooms — endless yellow corridors": (
        "an infinite office-like corridor of consistent beige-yellow walls and carpet, "
        "no windows, no doors visible, the corridor turning at irregular intervals, "
        "the same carpet pattern repeating indefinitely, "
        "fluorescent panels in the dropped ceiling, some working some not, "
        "a faint wet-carpet smell implied by the visual texture of the aging floor covering, "
        "the horizon of each corridor always the same distance away regardless of movement",
        "flat fluorescent from the ceiling panels — no shadows, no depth cues, "
        "the light slightly yellow-green from the aging panels, uniformly too bright",
        "a low persistent hum from the lighting and from something deeper in the structure, "
        "no echo — the space absorbs sound — "
        "and the sound of footsteps that are yours and also slightly delayed"),

    # ── ACTION / BLOCKBUSTER ─────────────────────────────────────────────
    "🏙 Rooftop chase — night city": (
        "rooftop of a city building at night, air conditioning units and water tanks "
        "creating obstacles across the flat roof, gravel underfoot, "
        "the edge with its low parapet visible ahead, the city sprawling below and beyond, "
        "the roof of the next building slightly lower and a gap between them, "
        "wet from recent rain, puddles on the flat membrane roof catching city glow",
        "city ambient glow from every direction as orange fill, "
        "cool blue from the night sky above, practical rooftop lights on the equipment, "
        "the edge of the roof backlit by the city below it",
        "city noise rising from below, wind at height, footsteps on gravel carrying clearly, "
        "a helicopter somewhere — its searchlight sweeping — "
        "and the impact sounds of bodies on metal and concrete"),

    "🏭 Industrial warehouse — emergency lighting": (
        "large industrial warehouse interior, steel-frame structure with a high corrugated ceiling, "
        "abandoned equipment and crated goods on wooden pallets creating a maze of cover, "
        "concrete floor with oil stains and painted navigation lines, "
        "a mezzanine level accessible by metal stairs on the far side, "
        "tall narrow windows at ceiling height letting in fractured moonlight",
        "standard lighting failed — emergency strips only at floor level in red, "
        "moonlight through the ceiling windows in diagonal shafts through dust, "
        "torchlight as a moving motivated source, deep shadow between every structure",
        "the metal structure ticking as it cools, "
        "every footstep echoing in the high ceiling space, "
        "something mechanical still running somewhere — a pump, a conveyor — and then stopping"),

    "🛣 Rain-soaked highway — car chase": (
        "a six-lane highway at night, rain heavy enough to reduce visibility to 50 metres, "
        "headlights of other vehicles forming blurred streaks in the wet, "
        "the road surface a sheet of reflected white and amber, "
        "crash barriers on both sides, an overpass ahead, "
        "the subject vehicle threading between slower traffic at high speed",
        "headlight white from every direction reflected in the wet asphalt, "
        "amber sodium from the highway gantries above, "
        "police or pursuit lighting in blue-red in the rear-view mirror",
        "tyre roar on wet tarmac at speed, rain on the roof and windscreen, "
        "the engine at high revs, the blast of air as a vehicle is overtaken, "
        "a distant siren growing closer"),

    # ── COOKING SHOW ─────────────────────────────────────────────────────
    "👨‍🍳 Professional kitchen — service": (
        "commercial kitchen at full service, stainless steel surfaces everywhere, "
        "six burner ranges with active flames, a pass at the far end where plates are assembled, "
        "the section system visible — hot section, cold section, pastry at the back, "
        "multiple cooks in whites moving with practised urgency, "
        "steam rising from multiple pans, heat visible as shimmer above the ranges, "
        "orders called from the pass, the specific controlled chaos of a kitchen at capacity",
        "overhead fluorescent on stainless — hard, bright, clinical, no shadows — "
        "the flames from the burners providing warm orange counter-light from below, "
        "the pass lit separately in clean white for plating",
        "the roar of extractor fans overhead, burner flames under pans, "
        "the call-and-response of the pass, metal on metal, the hiss of liquid hitting a hot pan"),

    "🍳 Home kitchen — morning light": (
        "domestic kitchen in morning light, an island counter in the centre, "
        "a window above the sink showing a garden or street outside, "
        "used chopping board, a few ingredients out on the counter, "
        "a pan on the hob with a tea towel draped nearby, "
        "the specific lived-in quality of a kitchen used every day",
        "natural morning light through the window — soft, directional, warm white — "
        "the window as the key source, shadows soft to the left of everything, "
        "under-cabinet lighting on if it's still early, adding warm fill to the counter",
        "the hob ticking as it heats, the extractor fan at low, "
        "a radio somewhere in the house, the knife on the board, "
        "water coming to the boil"),

    # ── WES ANDERSON ─────────────────────────────────────────────────────
    "🏨 Grand hotel lobby — Wes Anderson": (
        "a grand hotel lobby of the early-to-mid 20th century, perfectly symmetrical from the camera's position, "
        "a long reception desk centred at the far end, two matching staircases curving up on either side, "
        "a chandelier centred in the ceiling, patterned carpet in a geometric repeat, "
        "a bellboy standing perfectly still at the left, an identical one at the right, "
        "framed portraits evenly spaced on the walls, a revolving door centred in the entrance behind camera",
        "warm amber from the chandelier and wall sconces — even, sourceless-feeling, "
        "the light itself part of the symmetry — no shadow falls asymmetrically",
        "a grandfather clock ticking in precise four-four time, the revolving door cycling at the entrance "
        "with its exact pneumatic sweep and click, a telephone on the front desk ringing twice and stopping, "
        "a bellboy's trolley wheels on marble in perfect straight lines, "
        "someone at the piano in the adjacent salon playing something from 1932 in a major key, "
        "the specific hush of a lobby where every sound is permitted but nothing is loud"),

    "🏘 Pastel townhouse street — afternoon": (
        "a street of terraced townhouses each a different pastel colour — "
        "pale yellow, dusty rose, sage green, powder blue — in a repeating sequence, "
        "perfectly maintained window boxes with matching flowers, "
        "a pavement of identical grey cobbles, "
        "a bicycle of a matching pastel colour leaning against a door on the left, "
        "a letter box, a brass knocker, and a doormat all perfectly centred on each door",
        "flat overcast afternoon — no directional shadow, the pastels fully saturated and even, "
        "the colour of each house reading cleanly against the white of the sky",
        "a bicycle bell ringing once at exactly the right moment, a distant tram on its fixed route, "
        "a window opening on the second floor of the sage-green house — precisely — and closing again, "
        "someone practising scales on a woodwind instrument somewhere behind a wall, "
        "the sound of a letterbox closing, footsteps on cobble in a specific rhythm, "
        "and then complete symmetric silence"),

    # ── K-DRAMA ───────────────────────────────────────────────────────────
    "🌆 Seoul rooftop — dusk golden hour": (
        "rooftop of a Seoul apartment building at dusk, "
        "laundry lines with clothes barely visible in the fading light, "
        "water tanks and ventilation boxes, a small garden of potted plants in one corner, "
        "the city below spreading to every horizon, apartment towers lit in warm evening windows, "
        "the Han River a faint dark band in the mid-distance, "
        "two folding chairs and a small table — recently used",
        "dusk: the last directional light gone, sky a gradient of deep rose to cool indigo at the zenith, "
        "the city's warm amber rising from below like a second horizon, "
        "a street lamp on the access staircase providing the only warm key light",
        "city hum from below, wind at rooftop height carrying K-indie or lo-fi from an open window several floors down, "
        "a distant siren absorbed into traffic, the creak of a laundry line wire, "
        "the specific rooftop silence that sits just above the city's noise floor — "
        "present enough to feel alone, close enough to feel held"),

    "🌸 Cherry blossom park — midday": (
        "a park with cherry blossom trees in full bloom, "
        "petals continuously falling in the light wind, "
        "a stone path through the trees, wooden benches at intervals, "
        "other people visible in soft focus at the edges — couples, families — "
        "the blossom so dense it forms a soft ceiling overhead, "
        "petals accumulating in drifts against the kerb of the path",
        "filtered overhead light through the blossom canopy — soft pink-white, directionless, "
        "everything in the scene faintly lit from above through the petals, "
        "no hard shadows, skin luminous in the diffused light",
        "wind through the blossom — a collective soft rustle — "
        "petals landing on surfaces with barely any sound, "
        "distant park sounds softened by the canopy, someone laughing"),

    "🛋 Modern Seoul apartment — evening": (
        "interior of a modern Seoul apartment, open-plan living and kitchen area, "
        "floor-to-ceiling glass on one wall showing the Seoul skyline at evening, "
        "minimal furniture — a sofa, a low table, a kitchen island in white and grey — "
        "everything clean and considered, a single personal object on the table "
        "suggesting the room is lived in, a glass of water recently placed",
        "evening: the skyline outside providing ambient warm orange glow through the glass, "
        "interior lighting warm and low — a single floor lamp, no overhead lights, "
        "the glass wall doubling every interior light source in its reflection",
        "the city muffled by the glass — a distant siren, traffic below — "
        "the HVAC at low, the specific silence of a well-insulated modern apartment, "
        "and whatever the scene between the people in it generates"),

    # ── NIGHTLIFE / ADULT VENUES ─────────────────────────────────────────
    "💃 Strip club — main floor": (
        "strip club interior at full operation, a raised centre stage with a brass pole "
        "catching coloured light, mirrored wall behind the stage doubling everything, "
        "leather booths arranged in a horseshoe around the stage, VIP rope section off to one side, "
        "a long bar with backlit shelves of bottles along the far wall, "
        "scattered tables between stage and bar, each with a small candle flickering in red glass, "
        "smoke machine haze hanging at waist height, a DJ booth tucked in the corner",
        "stage wash cycling slow between magenta, violet, and warm amber — hard spots on the pole, "
        "UV strips along the stage edge making white fabric glow, "
        "deep shadow in the booths beyond the stage light spill, "
        "the mirrored wall creating infinite depth behind the performer",
        "bass-heavy RnB or trap at medium volume, ice in glasses, "
        "low conversation from the booths, heels on the stage surface, "
        "the specific sound of a room designed to keep you looking at the centre"),

    "🔒 Private booth — POV": (
        "POV from a man seated in a strip club private booth, "
        "camera locked at seated eye height looking slightly upward, "
        "black leather seat visible at the lower edge of frame, "
        "a curtain of dark velvet or beaded strands half-drawn behind the performer, "
        "the booth is small — the performer fills the frame at arm's length, "
        "a low table to one side with a drink, the main club visible only as blurred colour and movement "
        "through the curtain gap, a small wall-mounted speaker, dim recessed light overhead",
        "single overhead recessed downlight — warm amber, tight pool, directly above the performance space, "
        "everything outside the light pool near-black, "
        "the performer lit from above with strong shadow below the chin and cheekbones, "
        "occasional colour bleed — magenta, blue — leaking through the curtain from the main floor",
        "bass from the main floor muffled through the curtain, "
        "the booth speaker playing its own quieter track, breathing audible at this proximity, "
        "fabric shifting, the creak of leather seating, ice settling in the glass"),

    # ── BEACHES / OUTDOOR SOCIAL ─────────────────────────────────────────
    "🌴 LA beach — Venice / Santa Monica": (
        "Venice Beach boardwalk spilling onto wide flat sand in late afternoon golden hour, "
        "the Pacific glinting hard silver-gold to the horizon, palm trees in a line along the boardwalk, "
        "skaters and cyclists in soft-focus background on the bike path, "
        "muscle beach gym frames visible further down, graffiti walls and vendor stalls along the walk, "
        "lifeguard tower in classic white and red, crowds scattered across the sand — towels, coolers, "
        "someone playing volleyball, the Santa Monica pier and its ferris wheel visible in the distant haze",
        "golden hour California sun — warm, low, directional from the west over the ocean, "
        "long shadows stretching inland, everything backlit and rim-lit, "
        "skin glowing warm, sunglasses catching flare, the specific amber-pink LA light",
        "waves on the shore in steady rhythm, crowd noise from the boardwalk, "
        "a boombox somewhere playing hip-hop, skate wheels on concrete, "
        "seagulls, distant laughter, the Venice Beach energy that never fully quiets down"),

    "🍹 Ibiza pool party — golden hour": (
        "infinity pool at a cliff-edge villa in Ibiza at golden hour, "
        "the Mediterranean spread below in deep blue, white-washed walls and terracotta tiles, "
        "the pool overflowing its edge into the view, DJ setup under a white canopy, "
        "people in the water and on daybeds around the pool, champagne in ice buckets, "
        "string lights not yet lit waiting for dusk, smoke from a grill drifting across",
        "direct golden hour sun from the west — hard, warm, every water droplet catching it, "
        "skin glistening, pool surface a sheet of shifting gold, "
        "white surfaces bouncing light everywhere as natural fill",
        "deep house from the DJ at medium volume, water splashing, laughter, "
        "glasses clinking, the wind off the Mediterranean, "
        "the specific sound of an afternoon that knows it's about to become a night"),

    "🏄 Bondi Beach — bright midday": (
        "Bondi Beach at midday from the promenade level looking down the crescent of sand, "
        "the ocean a vivid turquoise with white breakers rolling in regular sets, "
        "hundreds of people on the sand, surfers in the water, the iconic red and yellow lifeguard flags, "
        "the sandstone headland at each end of the crescent, Norfolk pines along the promenade, "
        "the Icebergs pool visible cut into the rocks at the south end",
        "harsh Australian midday sun — overhead, no shadow relief, high UV, "
        "bleached sand near-white, ocean almost too bright to look at, "
        "everything saturated and high-contrast, sunscreen-sheen on skin",
        "surf crash in steady sets, crowd buzz, lifeguard whistle, "
        "someone's portable speaker, seagulls fighting over chips, "
        "the specific roar of a packed beach at the height of summer"),

    # ── MOODY / CINEMATIC INTERIORS ──────────────────────────────────────
    "🕯 Candlelit loft — exposed brick": (
        "open loft apartment with exposed brick walls and timber ceiling beams, "
        "the only light from clusters of pillar candles — on the floor, on shelves, on a low table, "
        "thirty or forty flames creating overlapping pools of warm amber, "
        "a large bed with dark linen visible in the back half of the space, "
        "a freestanding cast-iron bathtub near the windows, "
        "tall industrial windows showing the city at night but curtained with sheer fabric",
        "candlelight only — warm amber from multiple low sources, "
        "flames creating soft moving shadows on the brick, "
        "the candles reflected in the dark window glass, deep shadow above the beam line",
        "candle flames guttering in a draught, distant city through the glass, "
        "the creak of old timber, fabric shifting, "
        "the specific intimate quiet of a room lit only by fire"),

    "🚿 Rain shower — glass-walled bathroom": (
        "large walk-in rain shower with floor-to-ceiling glass walls on two sides, "
        "a single oversized showerhead directly overhead raining straight down, "
        "steam filling the upper half of the glass enclosure, "
        "water streaming in sheets down the glass, "
        "dark slate tile floor and walls, recessed warm LED strip at floor level, "
        "a bench built into the back wall, the bathroom beyond the glass visible but soft through steam",
        "recessed warm LED strip at floor level casting upward through the steam and water, "
        "overhead downlight diffused through the rain and mist, "
        "everything soft-edged and glowing, skin wet and catching every light source",
        "rain shower hiss from directly overhead — enveloping, constant, "
        "water hitting slate, steam, breathing amplified by the glass enclosure, "
        "the specific acoustics of a tiled glass box"),

    "🪩 Hotel rooftop bar — city night": (
        "rooftop bar on a high-end hotel, the city skyline as the backdrop on three sides, "
        "the bar itself a long backlit slab of marble or onyx, cocktails in progress, "
        "low seating clusters — velvet and brass — arranged around fire pit tables, "
        "a small pool or water feature reflecting the city lights, "
        "well-dressed people at the edges, a DJ playing from a minimal booth, "
        "string lights and pendant fixtures overhead creating warm islands of light",
        "warm practical lighting from the bar, fire pits, and string lights, "
        "city skyline ambient glow as backdrop, "
        "the sky a deep dark blue with the city preventing true black",
        "cocktail bar sounds — shaker, ice, glass on marble, low conversation, "
        "deep house at low volume from the DJ, wind at height, "
        "the city far below as a continuous ambient hum"),

    # ── TRANSPORT / MOTION ───────────────────────────────────────────────
    "🛥 Yacht deck — open ocean sunset": (
        "aft deck of a motor yacht at sunset, teak deck underfoot, "
        "the wake stretching back white and straight to the horizon, "
        "open ocean in every direction — deep blue turning to copper near the sun, "
        "the stern rail and a pair of chaise lounges, champagne in a bucket lashed to the rail, "
        "the upper flybridge visible above casting a shadow across the back half of the deck, "
        "sea spray occasionally reaching the lower deck",
        "direct sunset from the stern — warm copper-gold, hard rim light on everything facing aft, "
        "deep blue shadow on the forward side, the wake itself catching the light, "
        "skin lit warm from behind, face in soft reflected ocean fill",
        "engine vibration through the deck, wind, the hull cutting water, "
        "wake turbulence behind, a halyard clinking somewhere, "
        "the deep isolation of being the only thing on the ocean"),

    "🏎 Supercar interior — night drive": (
        "interior of a low-slung supercar at night — Lamborghini, McLaren, or similar — "
        "the cockpit tight and low, carbon fibre dash and centre console, "
        "the instrument cluster glowing warm amber behind the flat-bottom steering wheel, "
        "city lights streaking past through the low windshield, "
        "LED ambient strips along the door sills in cool blue, the seats deep bucket-shaped, "
        "the road surface visible through the windshield blurred with speed",
        "instrument cluster glow from below — warm amber, "
        "LED ambient strips in cool blue along the sills, "
        "city light streaking through the glass in rhythmic pulses, "
        "the driver's face lit from below and from the passing city",
        "engine note — a specific high-RPM mechanical scream behind and below the seats, "
        "tyres on asphalt, wind noise at speed, "
        "the turbo spool between shifts, city sound entering and leaving in doppler pulses"),

    # ── RAW / GRITTY ─────────────────────────────────────────────────────
    "🏨 Cheap motel room — neon through blinds": (
        "single-room motel interior at night, a queen bed with a thin patterned bedspread, "
        "wood-veneer furniture, a CRT TV on the dresser, venetian blinds at the window "
        "casting horizontal neon stripes — red and blue — across the bed and opposite wall, "
        "the bathroom door ajar showing harsh fluorescent inside, "
        "a bag on the floor, car headlights occasionally sweeping across the ceiling",
        "neon from outside through the blinds — alternating red and blue in horizontal bands, "
        "harsh bathroom fluorescent spilling through the cracked door as a single cold stripe, "
        "headlight sweeps across the ceiling at irregular intervals, "
        "the room itself has no light on — everything lit from outside or the bathroom",
        "the neon sign buzzing outside the window, ice machine humming through the wall, "
        "distant traffic on the highway, a door slamming somewhere in the building, "
        "the specific acoustic of thin walls and a parking lot outside"),

    "🏗 Industrial warehouse — night": (
        "cavernous warehouse interior at night, concrete floor cracked and oil-stained, "
        "steel columns running in a grid to the far wall, high corrugated roof lost in shadow, "
        "a few industrial pendant lights still working casting hard pools on the floor, "
        "loading dock doors along one wall — one rolled halfway up showing the dark yard outside, "
        "a car parked inside with its headlights on cutting two beams through the dust",
        "hard pools of light from the industrial pendants — warm sodium orange, "
        "car headlights cutting white beams through floating dust, "
        "deep black shadow between the light pools, the roof invisible",
        "echo — everything echoes in here, footsteps, voices, the drip from a pipe, "
        "a distant generator running, wind through the half-open loading dock, "
        "the specific reverb of a concrete box fifty metres long"),

    # ── RURAL / EQUESTRIAN ───────────────────────────────────────────────
    "🐴 Horse stable — warm afternoon": (
        "centre aisle of a large horse stable, stalls lining both sides with wooden half-doors, "
        "horses visible in several stalls — heads over the doors, ears forward, watching, "
        "the aisle floor compacted earth and straw, hay bales stacked against the far wall, "
        "tack and bridles hanging from iron hooks between stalls, "
        "afternoon light streaming through the open barn doors at the far end "
        "in long golden shafts full of floating dust and hay particles, "
        "the timber roof beams high overhead with swallows nesting in the crossbeams",
        "warm directional afternoon sun from the open barn doors — long golden shafts cutting the aisle, "
        "the stalls in warm shadow, straw on the floor catching the light, "
        "dust motes and hay particles suspended in every beam of light, "
        "deep amber warmth throughout, cool shadow in the stalls themselves",
        "horses shifting weight in their stalls — hooves on straw, a snort, "
        "a tail swishing against wood, the creak of a stall door, "
        "swallows above, distant meadow sounds from outside the barn, "
        "the deep quiet underneath everything that says countryside"),

    "🐴 Horse stable — night lantern": (
        "horse stable at night, the aisle lit by a single hanging lantern "
        "swaying gently from a roof beam, casting moving amber light and shadow, "
        "stalls on both sides — horses dozing, one head visible over a door, "
        "straw deep on the aisle floor, a saddle resting on a stand by the far wall, "
        "the barn doors closed against the dark, a gap at the top showing stars, "
        "a wool blanket folded on a hay bale, the smell of horse and leather implied by every surface",
        "single hanging lantern — warm amber, swaying, casting moving shadows "
        "that shift across the stall doors and the roof beams, "
        "everything beyond the lantern's reach in deep warm darkness, "
        "the horses' eyes catching the light from inside their stalls",
        "a horse breathing slow and heavy in the nearest stall, straw rustling, "
        "the lantern chain creaking with its sway, a horse stamping once, "
        "wind outside the closed doors, an owl somewhere beyond the barn, "
        "the complete rural silence that makes every small sound distinct"),

    "🌾 Barn interior — hay loft": (
        "upper hay loft of a large timber barn, the floor thick with loose hay and straw, "
        "a loft door open to the countryside showing fields stretching to the horizon, "
        "the roof beams close overhead — rough-hewn timber, iron bolts, cobwebs, "
        "bales stacked against the back wall, a pitchfork leaning in the corner, "
        "the loft edge with a wooden rail looking down to the barn floor below, "
        "golden late-afternoon light flooding through the open loft door",
        "golden hour sun pouring through the open loft door — directional, warm, "
        "every piece of hay in the air backlit and glowing, "
        "the light hitting the loose straw on the floor and turning it to gold, "
        "deep shadow against the back wall behind the bales",
        "wind through the open loft door, hay shifting, "
        "birds in the rafters, distant farm sounds — a tractor, a dog, "
        "the creak of the old timber structure, the countryside beyond the door"),

    "🏡 Farmhouse kitchen — early morning": (
        "large farmhouse kitchen at dawn, an Aga or wood-burning range against one wall "
        "radiating warmth, a scrubbed pine table in the centre with mismatched chairs, "
        "a window over the sink showing fields in early mist, "
        "copper pans hanging from a ceiling rack, a stone floor with a woven rug, "
        "a collie asleep in a basket by the range, a mug of tea steaming on the table",
        "cold blue dawn light through the window mixing with warm orange from the range, "
        "the two colour temperatures meeting in the middle of the kitchen, "
        "her face lit warm from one side and cool from the other",
        "the range ticking as it heats, a clock on the wall, "
        "birdsong building outside, the dog breathing in its basket, "
        "a kettle not yet boiling, the specific deep quiet of a farmhouse before the day starts"),
}
