"""Visual bible + voice bible.

FLUX has no memory between pictures, so the ONLY way to keep Rama, Sita, Hanuman ... looking the same in every
scene is to paste the same short description into every prompt that contains them. Gemini only names *who* is
in a scene; this file supplies *what they look like*.
"""

ART_STYLE = ("divine Indian mythological digital painting, ornate details, glowing golden light, rich saturated colors, "
             "cinematic dramatic composition, ultra detailed, subjects centered in the frame, no text, no letters, no watermark")

# attire variants for the three heroes: palace (Ayodhya / Mithila), forest (exile), war (Lanka)
RAMA = {
    "base": "Lord Rama, handsome young man with glowing blue skin, lotus eyes, calm divine face, red tilak, long black hair",
    "palace": "golden crown, gold jewellery, flower garland, saffron silk dhoti",
    "forest": "hair in a matted topknot, simple saffron cloth, long bow in hand, quiver on back",
    "war": "golden crown, golden armor, mighty bow with a glowing arrow",
}
SITA = {
    "base": "Sita, graceful beautiful woman with golden-brown skin, long black braid, gentle kind eyes, small red bindi",
    "palace": "red and gold silk sari, jewellery",
    "forest": "simple yellow cotton sari, very little jewellery",
    "war": "simple yellow cotton sari, very little jewellery",
}
LAKSHMANA = {
    "base": "Lakshmana, strong fair-skinned young warrior, sharp loyal eyes, black hair",
    "palace": "golden crown, red royal clothes",
    "forest": "hair in a matted topknot, brown bark-cloth, bow and quiver",
    "war": "golden armor, bow and quiver",
}

# key: (looks, voice profile)
CHARACTERS = {
    "rama": (RAMA, "hero"),
    "sita": (SITA, "woman"),
    "lakshmana": (LAKSHMANA, "fiery"),
    "bharata": ("Bharata, young prince with fair skin, plain saffron clothes, humble sorrowful face, no crown", "hero"),
    "shatrughna": ("Shatrughna, young prince, fair skin, plain saffron clothes, loyal face", "hero"),
    "hanuman": ("Hanuman, powerful monkey god with golden-orange fur, red face, muscular, golden armlets, big mace, long tail, "
                "devoted glowing eyes", "vanara"),
    "ravana": ("Ravana, mighty demon king with ten heads, dark skin, golden crowns, fierce red eyes, black and gold armor", "villain"),
    "dasharatha": ("King Dasharatha, elderly king with white beard, golden crown, rich red royal robes", "elder"),
    "kaikeyi": ("Queen Kaikeyi, proud queen in green and gold sari, ornate jewellery, crown, sharp stern look", "queen"),
    "kaushalya": ("Queen Kaushalya, gentle mature queen in white and gold sari, kind loving face", "queen"),
    "sumitra": ("Queen Sumitra, calm mature queen in pale blue and gold sari, wise face", "queen"),
    "manthara": ("Manthara, hunchbacked old maidservant with a scheming face, plain brown sari", "queen"),
    "janaka": ("King Janaka, wise king with grey beard, golden crown, white and gold robes", "elder"),
    "vishwamitra": ("Sage Vishwamitra, fierce old sage with long white beard, matted hair, saffron robes, rudraksha beads", "elder"),
    "sage": ("old sage with long white beard, matted hair, saffron robes, rudraksha beads, glowing aura", "elder"),
    "anasuya": ("Sage Anasuya, gentle elderly sage's wife in a white sari, glowing aura", "queen"),
    "guha": ("Guha, tribal boatman king with dark skin, simple forest clothes, feather headband, warm smile", "hero"),
    "sugriva": ("Sugriva, monkey king with brown fur, golden crown, red cloth, worried kind face", "vanara"),
    "vali": ("Vali, huge powerful monkey king with golden-brown fur, golden garland, proud mighty look", "vanara"),
    "tara": ("Tara, wise vanara queen in a blue sari, graceful and calm", "woman"),
    "angad": ("Angad, young strong monkey prince with brown fur, golden armlets, brave face", "vanara"),
    "jambavan": ("Jambavan, old wise bear king with dark shaggy fur, grey muzzle, kind eyes", "elder"),
    "jatayu": ("Jatayu, giant divine vulture with huge golden-brown wings, noble eyes", "elder"),
    "sampati": ("Sampati, giant old wingless vulture with a scorched body, sad wise eyes", "elder"),
    "vibhishana": ("Vibhishana, noble demon prince with one head, blue-grey skin, simple golden crown, white clothes, gentle wise face", "hero"),
    "kumbhakarna": ("Kumbhakarna, gigantic mountain-sized demon with brown skin, golden earrings, sleepy fierce face", "villain"),
    "indrajit": ("Indrajit, young powerful demon prince with dark skin, golden armor and crown, holding a bow", "villain"),
    "mandodari": ("Queen Mandodari, beautiful demon queen in deep purple and gold sari, jeweled crown", "queen"),
    "surpanakha": ("Surpanakha, demoness with a sharp fierce face, long dark hair, red sari, large golden earrings", "queen"),
    "maricha": ("Maricha, a shimmering golden deer with silver spots and gentle glowing eyes", "villain"),
    "shabari": ("Shabari, very old tribal woman with white hair, simple cloth, joyful devoted face, basket of berries", "queen"),
    "trijata": ("Trijata, kind old demoness with grey hair, gentle face, simple sari", "queen"),
    "lankini": ("Lankini, giant fierce guardian demoness of Lanka with dark skin and glowing eyes", "queen"),
    "kabandha": ("Kabandha, giant headless demon with long arms and a mouth on his belly", "villain"),
    "demon": ("fierce demon soldier with dark skin, small tusks, red eyes, holding a spear", "villain"),
    "vanara": ("brave vanara warrior monkey with brown fur, holding a tree branch", "vanara"),
    "citizen": ("simple Ayodhya villagers in colourful traditional Indian clothes", "elder"),
}

ALIASES = {
    "ram": "rama", "shriram": "rama", "laxman": "lakshmana", "lakshman": "lakshmana", "laxmana": "lakshmana",
    "maruti": "hanuman", "hanumanji": "hanuman", "dashrath": "dasharatha", "dashratha": "dasharatha",
    "bharat": "bharata", "shatrughn": "shatrughna", "vishwamitra": "vishwamitra", "vishvamitra": "vishwamitra",
    "sugreev": "sugriva", "baali": "vali", "kumbhkarna": "kumbhakarna", "meghnad": "indrajit", "meghnada": "indrajit",
    "vibhishan": "vibhishana", "jatayuraj": "jatayu", "surpanakha": "surpanakha", "shurpanakha": "surpanakha",
    "vasishtha": "sage", "vashishtha": "sage", "agastya": "sage", "atri": "sage", "valmiki": "sage", "sutikshna": "sage",
    "sharabhanga": "sage", "bharadvaja": "sage", "rishi": "sage", "kaikai": "kaikeyi", "kausalya": "kaushalya",
    "narrator": "narrator",
}

# voice profile -> (edge-tts voice, rate, edge pitch, caption colour, semitone shift applied afterwards in FFmpeg)
# Marathi has only TWO neural voices (Manohar = man, Aarohi = woman), and the service's own pitch setting is weak,
# so every character is pushed to a clearly different pitch/size by shifting the recorded audio ourselves.
VOICES = {
    "narrator": ("mr-IN-ManoharNeural", "+3%", "+0Hz", "FFFFFF",  0.0),   # reference storyteller
    "hero":     ("mr-IN-ManoharNeural", "+0%", "+0Hz", "FFD54F", +2.0),   # Rama, Bharata, Guha: younger, brighter
    "fiery":    ("mr-IN-ManoharNeural", "+8%", "+0Hz", "FFB300", +3.5),   # Lakshmana: quick, sharp
    "vanara":   ("mr-IN-ManoharNeural", "+8%", "+0Hz", "FF9F43", +4.5),   # Hanuman, Sugriva, Angad: lively
    "elder":    ("mr-IN-ManoharNeural", "-4%", "+0Hz", "A5D6A7", -3.5),   # kings, sages, Jatayu: old and deep
    "villain":  ("mr-IN-ManoharNeural", "-4%", "+0Hz", "FF6B6B", -5.5),   # Ravana, demons: huge and growling
    "woman":    ("mr-IN-AarohiNeural",  "-2%", "+0Hz", "FF9DBD", +1.0),   # Sita, Tara: soft, young
    "queen":    ("mr-IN-AarohiNeural",  "+0%", "+0Hz", "F8A5FF", -2.5),   # Kaikeyi, Kaushalya: mature, firm
}

CAST_KEYS = sorted(CHARACTERS)


def normalize(name):
    """Map whatever Gemini wrote to a known key (or 'narrator' / '' if unknown)."""
    key = "".join(ch for ch in str(name or "").lower() if ch.isalpha())
    key = ALIASES.get(key, key)
    if key == "narrator":
        return "narrator"
    return key if key in CHARACTERS else ""


def voice_profile(speaker):
    key = normalize(speaker)
    profile = CHARACTERS[key][1] if key in CHARACTERS else "narrator"
    return profile, VOICES[profile]


AGE_LOOKS = {
    "infant": {
        "rama": "newborn baby Rama, an adorable glowing blue-skinned baby with big lotus eyes, wrapped in golden cloth, tiny gold ornaments",
        "lakshmana": "newborn baby Lakshmana, an adorable fair-skinned baby wrapped in white and gold cloth, tiny gold ornaments",
        "bharata": "newborn baby Bharata, an adorable fair-skinned baby wrapped in saffron and gold cloth, tiny gold ornaments",
        "shatrughna": "newborn baby Shatrughna, an adorable fair-skinned baby wrapped in white and gold cloth, tiny gold ornaments",
    },
    "teen": {
        "rama": "teenage Rama about sixteen years old, handsome slim youth with glowing blue skin, lotus eyes, calm face, hair in a topknot, saffron cloth, holding a bow",
        "lakshmana": "teenage Lakshmana about fifteen years old, fair-skinned energetic youth with sharp eyes, hair in a topknot, saffron cloth, holding a bow",
        "bharata": "teenage Bharata, fair-skinned youth, saffron cloth, gentle face",
        "shatrughna": "teenage Shatrughna, fair-skinned youth, saffron cloth, loyal face",
    },
}


def describe(key, attire, age="adult"):
    if age in AGE_LOOKS and key in AGE_LOOKS[age]:
        return AGE_LOOKS[age][key]
    looks = CHARACTERS[key][0]
    if isinstance(looks, dict):
        return f"{looks['base']}, wearing {looks.get(attire, looks['palace'])}"
    return looks
