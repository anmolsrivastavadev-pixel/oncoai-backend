"""Curated educational skin-health content.

Written to be accurate, general and non-diagnostic, summarising guidance published by
the NHS, the American Academy of Dermatology (AAD), the Skin Cancer Foundation, Cancer
Research UK and the World Health Organization. Articles deliberately avoid naming
specific diseases or recommending treatments.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    title: str
    url: str


@dataclass(frozen=True)
class Article:
    id: str
    title: str
    summary: str
    body: list[str]
    keywords: list[str]
    sources: list[Source]
    questions: list[str] = field(default_factory=list)  # suggested follow-ups
    listed: bool = True  # shown in GET /assistant/topics


NHS_MOLES = Source("NHS: Moles", "https://www.nhs.uk/conditions/moles/")
NHS_SUN = Source(
    "NHS: Sunscreen and sun safety",
    "https://www.nhs.uk/live-well/seasonal-health/sunscreen-and-sun-safety/",
)
NHS_SUNBURN = Source("NHS: Sunburn", "https://www.nhs.uk/conditions/sunburn/")
NHS_111 = Source("NHS 111 online", "https://111.nhs.uk/")
AAD_ABCDE = Source(
    "American Academy of Dermatology: What to look for (ABCDEs)",
    "https://www.aad.org/public/diseases/skin-cancer/find/at-risk/abcdes",
)
AAD_SELF_EXAM = Source(
    "American Academy of Dermatology: How to check your skin",
    "https://www.aad.org/public/diseases/skin-cancer/find/check-skin",
)
AAD_SUNSCREEN = Source(
    "American Academy of Dermatology: How to select a sunscreen",
    "https://www.aad.org/public/everyday-care/sun-protection/shade-clothing-sunscreen/how-to-select-sunscreen",
)
SCF_SELF_EXAM = Source(
    "Skin Cancer Foundation: Self-exams",
    "https://www.skincancer.org/early-detection/self-exams/",
)
SCF_ANNUAL = Source(
    "Skin Cancer Foundation: Annual skin exams",
    "https://www.skincancer.org/early-detection/annual-exams/",
)
CRUK_UV = Source(
    "Cancer Research UK: The UV index and sunburn risk",
    "https://www.cancerresearchuk.org/about-cancer/causes-of-cancer/sun-uv-and-cancer/the-uv-index-and-sunburn-risk",
)
WHO_UV = Source(
    "World Health Organization: The ultraviolet (UV) index",
    "https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-(uv)-index",
)

ARTICLES: list[Article] = [
    Article(
        id="abcde-rule",
        title="The ABCDE rule for checking moles",
        summary="Five visual features dermatologists suggest watching for in moles and spots.",
        body=[
            "The ABCDE rule is a simple checklist that helps you notice moles or spots that may "
            "be worth showing to a doctor:",
            "A - Asymmetry: one half of the spot does not match the other half.\n"
            "B - Border: the edges are ragged, notched, blurred or irregular.\n"
            "C - Colour: the colour is uneven, with several shades such as brown, black, tan, "
            "red, white or blue.\n"
            "D - Diameter: the spot is larger than about 6 mm (roughly the size of a pencil "
            "eraser), although some concerning spots are smaller.\n"
            "E - Evolving: the spot is changing in size, shape, colour or height, or new "
            "symptoms such as itching, crusting or bleeding appear.",
            "Change over time (the 'E') is often the most important sign. Having one of these "
            "features does not mean something is wrong, but if you notice any of them, or "
            "anything else that worries you, it is a good idea to have the spot checked by a "
            "GP or dermatologist.",
        ],
        keywords=["abcde", "asymmetry", "border", "colour", "color", "diameter", "evolving",
                  "mole", "moles", "warning", "signs", "check", "rule", "change", "changing"],
        sources=[AAD_ABCDE, NHS_MOLES],
        questions=["What is the ugly duckling sign?", "How do I do a monthly skin self-exam?"],
    ),
    Article(
        id="ugly-duckling",
        title="The 'ugly duckling' sign",
        summary="Why a mole that looks different from your other moles deserves attention.",
        body=[
            "Most of a person's moles tend to look similar to each other. The 'ugly duckling' "
            "sign refers to a mole or spot that stands out because it looks different from the "
            "rest: for example darker, lighter, larger, a different shape, or one that is "
            "changing while the others stay the same.",
            "When you do a self-check, compare your spots with each other rather than looking "
            "at each one in isolation. A spot that is the odd one out is worth showing to a "
            "GP or dermatologist, even if it doesn't match any of the ABCDE features.",
        ],
        keywords=["ugly", "duckling", "different", "odd", "stands", "out", "compare", "other",
                  "moles", "unusual"],
        sources=[SCF_SELF_EXAM, AAD_SELF_EXAM],
        questions=["What is the ABCDE rule?", "How often should I check my skin?"],
    ),
    Article(
        id="uv-protection",
        title="UV index and sunscreen basics",
        summary="How to read the UV index and use sunscreen, shade and clothing effectively.",
        body=[
            "The UV index (published with most weather forecasts) measures the strength of the "
            "sun's ultraviolet radiation: 0-2 is low, 3-5 moderate, 6-7 high, 8-10 very high "
            "and 11+ extreme. Sun protection is recommended whenever the UV index is 3 or above, "
            "even on cloudy or cool days.",
            "Sunscreen: choose a broad-spectrum sunscreen (protecting against UVA and UVB) with "
            "SPF 30 or higher; in the UK also look for a UVA rating of at least 4 stars. Most "
            "people apply too little: an adult needs roughly 6-8 teaspoons (about a shot "
            "glass) to cover the whole body. Apply it 15-30 minutes before going out, and "
            "reapply at least every 2 hours and straight after swimming, sweating or towel "
            "drying.",
            "Sunscreen works best alongside other protection: spend time in the shade when the "
            "sun is strongest (around 11am-3pm in the UK, 10am-4pm in many other places), cover "
            "up with clothing, a wide-brimmed hat and UV-protective sunglasses, and never use "
            "sunscreen as a reason to stay in the sun longer. Avoid sunbeds and take extra care "
            "to protect children.",
        ],
        keywords=["uv", "index", "sun", "sunscreen", "spf", "sunblock", "suncream", "cream",
                  "protection", "uva", "uvb", "shade", "hat", "sunbed", "tanning", "burn",
                  "sunburn", "reapply", "summer", "beach"],
        sources=[NHS_SUN, AAD_SUNSCREEN, CRUK_UV, WHO_UV],
        questions=["Which skin type am I?", "How much sunscreen should I use?"],
    ),
    Article(
        id="self-exam",
        title="How to do a monthly skin self-exam",
        summary="A step-by-step routine for checking your whole body once a month.",
        body=[
            "Checking your skin about once a month helps you learn what is normal for you, so "
            "you notice changes early. You'll need good light, a full-length mirror, a hand "
            "mirror, and ideally a partner or friend to check places you can't see.",
            "1. Face, ears, lips and neck - including behind the ears.\n"
            "2. Scalp - part your hair section by section (a comb or hairdryer helps).\n"
            "3. Hands - palms, backs, between the fingers and under the fingernails.\n"
            "4. Arms - elbows, forearms, upper arms and underarms.\n"
            "5. Chest and torso - including under the breasts.\n"
            "6. Back, shoulders and buttocks - use the hand mirror with the full-length mirror.\n"
            "7. Legs - fronts, backs and sides.\n"
            "8. Feet - soles, heels, between the toes and under the toenails.\n"
            "9. Genital area.",
            "Look for new spots, spots that are changing, sores that don't heal, and any spot "
            "that looks different from the others. Taking photos (for example with OncoAI) "
            "under similar lighting each month makes changes easier to see. If anything is new, "
            "changing or worrying you, book a check with a GP or dermatologist.",
        ],
        keywords=["self", "exam", "examination", "check", "monthly", "routine", "mirror",
                  "body", "how", "often", "step", "scalp", "feet", "nails", "photo"],
        sources=[AAD_SELF_EXAM, SCF_SELF_EXAM, NHS_MOLES],
        questions=["What should I look for during a self-check?", "What happens at a dermatologist appointment?"],
    ),
    Article(
        id="dermatologist-visit",
        title="What to expect at a dermatologist appointment",
        summary="How a skin check works and how to prepare for it.",
        body=[
            "A dermatologist is a doctor who specialises in skin, hair and nails. In the UK you "
            "are usually referred by your GP; in many other countries you can book directly.",
            "At a skin check the dermatologist will usually ask about your history (sun "
            "exposure, sunburns, family history, and any changes you've noticed) and then "
            "examine your skin, often from head to toe. They may look closely at spots using a "
            "dermatoscope, a handheld magnifier with a special light, and may take photos to "
            "compare at future visits. If they want more information about a spot they may "
            "suggest further tests, and they will explain any next steps with you.",
            "To prepare: write down the spots you're concerned about and when you noticed them "
            "changing, bring any photos (such as your OncoAI scan history), remove nail polish "
            "and make-up, and note any questions you'd like to ask.",
        ],
        keywords=["dermatologist", "appointment", "visit", "doctor", "gp", "expect", "prepare",
                  "skin", "check", "dermatoscope", "referral", "clinic", "exam"],
        sources=[SCF_ANNUAL, NHS_MOLES],
        questions=["How do I prepare for a skin check?", "How do I do a monthly skin self-exam?"],
    ),
    Article(
        id="understanding-results",
        title="Understanding your OncoAI scan result",
        summary="What the low / moderate / higher concern levels mean - and what they don't.",
        body=[
            "OncoAI looks at visual patterns in your photo - such as how symmetrical a spot is, "
            "how even its border looks, how many colour tones it has, and its relative size - "
            "and combines them into an educational concern level: low, moderate or higher.",
            "Low means no prominent irregular visual patterns were detected in that photo. "
            "Moderate means some irregular visual patterns were detected. Higher means "
            "irregular visual patterns were detected and professional dermatologist evaluation "
            "is suggested.",
            "Important limits: OncoAI is not a diagnosis and cannot tell you what a spot is. "
            "Results depend heavily on lighting, focus, camera and angle; the image model was "
            "developed mostly on close-up clinical (dermoscopy) images rather than phone "
            "photos; and performance may differ across skin tones. A low result does not rule "
            "anything out. If a spot is new, changing, bleeding, itchy or worrying you, see a "
            "GP or dermatologist whatever the scan says.",
        ],
        keywords=["oncoai", "scan", "result", "score", "concern", "level", "low", "moderate",
                  "higher", "meaning", "mean", "accurate", "accuracy", "reliable", "ai", "app",
                  "photo", "retake"],
        sources=[NHS_MOLES, AAD_ABCDE],
        questions=["How can I take a better scan photo?", "What is the ABCDE rule?"],
    ),
    Article(
        id="skin-types",
        title="Fitzpatrick skin types",
        summary="The six skin types and how they relate to sunburn risk.",
        body=[
            "The Fitzpatrick scale groups skin by how it reacts to sun exposure:",
            "Type I - very fair; always burns, never tans.\n"
            "Type II - fair; usually burns, tans with difficulty.\n"
            "Type III - medium; sometimes burns, gradually tans.\n"
            "Type IV - olive or light brown; rarely burns, tans easily.\n"
            "Type V - brown; very rarely burns, tans very easily.\n"
            "Type VI - dark brown or black; almost never burns.",
            "Lighter skin types burn more easily and have a higher risk of sun damage, but "
            "people of every skin type can be affected. In darker skin, concerning spots can "
            "appear in places that get little sun, such as the palms, soles of the feet and "
            "under the nails, so include these in self-checks. You can record your skin type "
            "in your OncoAI profile.",
        ],
        keywords=["fitzpatrick", "skin", "type", "types", "tone", "fair", "dark", "pale",
                  "burn", "tan", "complexion", "melanin"],
        sources=[NHS_SUN, CRUK_UV],
        questions=["How do I read the UV index?", "How do I do a monthly skin self-exam?"],
    ),
    Article(
        id="urgent-care",
        title="When to seek medical help promptly",
        summary="Skin changes that should be checked by a healthcare professional soon.",
        body=[
            "Contact a GP, doctor or dermatologist soon if you notice: a new spot or a mole "
            "that is changing in size, shape or colour; a spot that bleeds, crusts or itches "
            "without an obvious reason; or a sore that hasn't healed within about 4 weeks.",
            "Get urgent help (for example NHS 111 in the UK, an urgent care clinic, or your "
            "local emergency number) for bleeding that won't stop with firm pressure, a spot "
            "that is rapidly swelling, hot, very painful or spreading redness with fever, or "
            "severe sunburn with blistering over a large area, fever, chills, dizziness or "
            "confusion.",
            "If you are ever unsure, it is always reasonable to ask a healthcare professional.",
        ],
        keywords=["urgent", "emergency", "bleeding", "bleed", "bleeds", "sore", "heal",
                  "healing", "fever", "pain", "painful", "swelling", "help", "doctor", "soon",
                  "worried", "spreading", "blister"],
        sources=[NHS_MOLES, NHS_SUNBURN, NHS_111],
        questions=["What happens at a dermatologist appointment?", "What is the ABCDE rule?"],
    ),
    Article(
        id="photo-tips",
        title="Taking a good scan photo",
        summary="Tips for clear, consistent photos that make tracking changes easier.",
        body=[
            "Use bright, even, natural light and avoid harsh flash glare or strong shadows. "
            "Hold the phone steady about 10-15 cm from the skin, parallel to the surface, and "
            "tap the spot to focus. Centre the spot so it fills roughly a third of the frame.",
            "For tracking over time, photograph the same spot from the same distance and in "
            "similar light each time. Placing a ruler or coin next to the spot helps you "
            "compare size between photos.",
        ],
        keywords=["photo", "picture", "camera", "blurry", "blur", "light", "lighting", "dark",
                  "retake", "focus", "quality", "better", "take", "tips"],
        sources=[AAD_SELF_EXAM],
        questions=["What does my scan result mean?", "How do I do a monthly skin self-exam?"],
        listed=False,
    ),
]

ARTICLES_BY_ID = {article.id: article for article in ARTICLES}
