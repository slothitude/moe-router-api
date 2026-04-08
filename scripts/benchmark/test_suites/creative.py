"""Creative writing test cases - 20 tests."""

CREATIVE_TESTS = [
    # Story Writing (8 tests)
    {
        "id": "creative_001",
        "category": "creative",
        "subcategory": "story",
        "query": "Write a short story (200 words) about a robot who discovers emotions. Set in a factory. Include: awakening moment, confusion, first feeling.",
        "expected_elements": ["robot", "emotions", "story", "feelings", "awakening"],
        "complexity": "high"
    },
    {
        "id": "creative_002",
        "category": "creative",
        "subcategory": "story",
        "query": "Create a flash fiction story (100 words) about a time traveler who accidentally changes history. Theme: unintended consequences.",
        "expected_elements": ["time travel", "consequences", "story", "accident", "history"],
        "complexity": "medium"
    },
    {
        "id": "creative_003",
        "category": "creative",
        "subcategory": "story",
        "query": "Write a story opening that hooks the reader. Genre: mystery. First line must be: 'The letter arrived three years late.' Continue for 150 words.",
        "expected_elements": ["mystery", "hook", "opening", "story", "suspense"],
        "complexity": "medium"
    },
    {
        "id": "creative_004",
        "category": "creative",
        "subcategory": "story",
        "query": "Write a sci-fi scene (200 words) about first contact with aliens. Setting: remote research station in Antarctica. Focus on tension and wonder.",
        "expected_elements": ["sci-fi", "aliens", "first contact", "scene", "tension"],
        "complexity": "high"
    },
    {
        "id": "creative_005",
        "category": "creative",
        "subcategory": "story",
        "query": "Create a fable with a moral lesson. Characters: a wise owl and impatient hare. Length: 150 words. Include dialogue.",
        "expected_elements": ["fable", "moral", "animals", "dialogue", "lesson"],
        "complexity": "medium"
    },
    {
        "id": "creative_006",
        "category": "creative",
        "subcategory": "story",
        "query": "Write a romance scene (200 words). Setting: coffee shop on rainy day. Two strangers reach for same book. Include sensory details.",
        "expected_elements": ["romance", "meeting", "sensory", "dialogue", "chemistry"],
        "complexity": "medium"
    },
    {
        "id": "creative_007",
        "category": "creative",
        "subcategory": "story",
        "query": "Create a horror story opening (150 words). Setting: abandoned hospital. Focus on atmosphere and dread. Avoid gore, use psychological horror.",
        "expected_elements": ["horror", "atmosphere", "dread", "abandoned", "psychological"],
        "complexity": "medium"
    },
    {
        "id": "creative_008",
        "category": "creative",
        "subcategory": "story",
        "query": "Write a fantasy scene (200 words). A young wizard casts first spell. It goes wrong hilariously. Include: incantation, unexpected result, lesson learned.",
        "expected_elements": ["fantasy", "wizard", "magic", "humor", "lesson"],
        "complexity": "medium"
    },

    # Poetry (5 tests)
    {
        "id": "creative_009",
        "category": "creative",
        "subcategory": "poetry",
        "query": "Write a haiku about autumn. Traditional 5-7-5 syllable structure. Theme: change and letting go.",
        "expected_elements": ["haiku", "autumn", "nature", "5-7-5", "imagery"],
        "complexity": "low"
    },
    {
        "id": "creative_010",
        "category": "creative",
        "subcategory": "poetry",
        "query": "Create a sonnet about the ocean. Shakespearean style: ABABCDCDEFEFGG. Focus on power and mystery.",
        "expected_elements": ["sonnet", "ocean", "14 lines", "rhyme", "imagery"],
        "complexity": "high"
    },
    {
        "id": "creative_011",
        "category": "creative",
        "subcategory": "poetry",
        "query": "Write free verse poem about city life at night. Length: 20 lines. Include: neon lights, traffic, loneliness, connection.",
        "expected_elements": ["free verse", "city", "night", "imagery", "emotion"],
        "complexity": "medium"
    },
    {
        "id": "creative_012",
        "category": "creative",
        "subcategory": "poetry",
        "query": "Create a limerick about a programmer. AABBA rhyme scheme. Make it humorous but good-natured.",
        "expected_elements": ["limerick", "humor", "programmer", "AABBA", "witty"],
        "complexity": "low"
    },
    {
        "id": "creative_013",
        "category": "creative",
        "subcategory": "poetry",
        "query": "Write an acrostic poem for DREAMS. Each letter starts a line about aspirations and hope.",
        "expected_elements": ["acrostic", "DREAMS", "hope", "line-by-line", "thematic"],
        "complexity": "low"
    },

    # Dialogue (4 tests)
    {
        "id": "creative_014",
        "category": "creative",
        "subcategory": "dialogue",
        "query": "Write a dialogue between two friends debating whether to quit stable jobs to start a business. 200 words. Show distinct voices and conflict.",
        "expected_elements": ["dialogue", "debate", "conflict", "voices", "business"],
        "complexity": "medium"
    },
    {
        "id": "creative_015",
        "category": "creative",
        "subcategory": "dialogue",
        "query": "Create a breakup conversation (150 words). Make it mature and respectful. Both characters communicate honestly. Show subtext.",
        "expected_elements": ["dialogue", "breakup", "honest", "emotional", "subtext"],
        "complexity": "medium"
    },
    {
        "id": "creative_016",
        "category": "creative",
        "subcategory": "dialogue",
        "query": "Write a job interview dialogue (200 words). Interviewer asks unexpected question. Candidate responds creatively. Tension then relief.",
        "expected_elements": ["dialogue", "interview", "tension", "creativity", "resolution"],
        "complexity": "medium"
    },
    {
        "id": "creative_017",
        "category": "creative",
        "subcategory": "dialogue",
        "query": "Create a scene where a parent explains death to a child (150 words). Use gentle metaphors. Child asks questions. Honest but age-appropriate.",
        "expected_elements": ["dialogue", "parent-child", "difficult topic", "gentle", "metaphor"],
        "complexity": "high"
    },

    # Creative Content (3 tests)
    {
        "id": "creative_018",
        "category": "creative",
        "subcategory": "content",
        "query": "Write a movie trailer voiceover script for an original action film. Title: 'ECHO'. Plot: former assassin hunted by shadow agency. Tone: intense, mysterious.",
        "expected_elements": ["trailer", "script", "action", "hook", "voiceover"],
        "complexity": "medium"
    },
    {
        "id": "creative_019",
        "category": "creative",
        "subcategory": "content",
        "query": "Create a menu description for a fictional farm-to-table restaurant. 5 dishes. Make descriptions mouth-watering and evoke local ingredients.",
        "expected_elements": ["menu", "descriptions", "food", "appetizing", "creative"],
        "complexity": "medium"
    },
    {
        "id": "creative_020",
        "category": "creative",
        "subcategory": "content",
        "query": "Write a podcast episode intro for true crime show. Episode: 'The Vanishing'. Format: hook, teaser, intro music cue. Create intrigue.",
        "expected_elements": ["podcast", "intro", "true crime", "hook", "intrigue"],
        "complexity": "medium"
    },
]

__all__ = ["CREATIVE_TESTS"]
