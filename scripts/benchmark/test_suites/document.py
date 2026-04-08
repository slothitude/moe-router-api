"""Document writing and editing test cases - 25 tests."""

DOCUMENT_TESTS = [
    # Document Writing (10 tests)
    {
        "id": "document_001",
        "category": "document",
        "subcategory": "writing",
        "query": "Write a professional email to a client about a 2-week project delay. Be apologetic but confident. Include: reason, new timeline, and mitigation steps.",
        "expected_elements": ["apology", "delay", "timeline", "mitigation", "professional"],
        "complexity": "medium"
    },
    {
        "id": "document_002",
        "category": "document",
        "subcategory": "writing",
        "query": "Draft a press release for a startup's Series A funding: $10M raised, led by Sequoia, for AI-powered analytics platform. Include quote from CEO.",
        "expected_elements": ["funding", "Series A", "quote", "analytics", "announcement"],
        "complexity": "medium"
    },
    {
        "id": "document_003",
        "category": "document",
        "subcategory": "writing",
        "query": "Write a product description for an ergonomic office chair. Highlight: lumbar support, adjustable arms, 12-hour comfort, 5-year warranty. Target: remote workers.",
        "expected_elements": ["chair", "ergonomic", "features", "comfort", "warranty"],
        "complexity": "low"
    },
    {
        "id": "document_004",
        "category": "document",
        "subcategory": "writing",
        "query": "Create a job posting for a Senior Python Developer. Requirements: 5+ years exp, Django, AWS, distributed systems. Include responsibilities and benefits.",
        "expected_elements": ["job", "Python", "requirements", "responsibilities", "benefits"],
        "complexity": "medium"
    },
    {
        "id": "document_005",
        "category": "document",
        "subcategory": "writing",
        "query": "Write a privacy policy for a mobile app that collects: email, location, usage analytics. Include: data collection, usage, sharing, user rights.",
        "expected_elements": ["privacy", "data collection", "sharing", "rights", "policy"],
        "complexity": "high"
    },
    {
        "id": "document_006",
        "category": "document",
        "subcategory": "writing",
        "query": "Draft a meeting agenda for a Q1 planning session. Topics: review Q4 results, set Q1 OKRs, discuss roadmap, allocate budget. Duration: 2 hours, 8 attendees.",
        "expected_elements": ["agenda", "Q1", "OKRs", "roadmap", "planning"],
        "complexity": "medium"
    },
    {
        "id": "document_007",
        "category": "document",
        "subcategory": "writing",
        "query": "Write a user guide for a password manager app. Cover: installation, setup master password, add passwords, auto-fill feature. Keep it beginner-friendly.",
        "expected_elements": ["guide", "password manager", "setup", "features", "instructions"],
        "complexity": "medium"
    },
    {
        "id": "document_008",
        "category": "document",
        "subcategory": "writing",
        "query": "Create an API documentation for a POST /users endpoint. Include: description, request body (name, email, password), response format, error codes.",
        "expected_elements": ["API", "endpoint", "request", "response", "errors"],
        "complexity": "medium"
    },
    {
        "id": "document_009",
        "category": "document",
        "subcategory": "writing",
        "query": "Write a resignation letter. Role: Software Engineer. Notice: 2 weeks. Reason: new opportunity. Include: offer to help transition, gratitude.",
        "expected_elements": ["resignation", "notice", "transition", "gratitude", "professional"],
        "complexity": "low"
    },
    {
        "id": "document_010",
        "category": "document",
        "subcategory": "writing",
        "query": "Draft a sales landing page for a B2B CRM tool. Hook: 'Save 10 hours/week on lead management'. Include: benefits, features, social proof, CTA.",
        "expected_elements": ["sales", "CRM", "benefits", "features", "CTA"],
        "complexity": "medium"
    },

    # Document Editing (8 tests)
    {
        "id": "document_011",
        "category": "document",
        "subcategory": "editing",
        "query": "Edit this paragraph for clarity and conciseness: 'In order to be able to effectively and efficiently utilize the software application, it is necessary that users complete the required training program.'",
        "expected_elements": ["concise", "clear", "edit", "simplified"],
        "complexity": "low"
    },
    {
        "id": "document_012",
        "category": "document",
        "subcategory": "editing",
        "query": "Rewrite this email to be more professional: 'Hey, cant make mtg tmrw. sick. reschedule?'",
        "expected_elements": ["professional", "rewrite", "formal", "polite"],
        "complexity": "low"
    },
    {
        "id": "document_013",
        "category": "document",
        "subcategory": "editing",
        "query": "Fix the grammar and improve flow: 'Me and my team has been working on the project since last year. We had did alot of progress but their remains some challenges.'",
        "expected_elements": ["grammar", "flow", "corrected", "improved"],
        "complexity": "low"
    },
    {
        "id": "document_014",
        "category": "document",
        "subcategory": "editing",
        "query": "Convert this passive voice text to active: 'The report was reviewed by the manager. Errors were found. Corrections will be made.'",
        "expected_elements": ["active voice", "rewrite", "direct", "action"],
        "complexity": "low"
    },
    {
        "id": "document_015",
        "category": "document",
        "subcategory": "editing",
        "query": "Simplify this technical explanation for non-technical users: 'The application leverages microservices architecture to achieve horizontal scalability and fault isolation through containerization.'",
        "expected_elements": ["simplified", "non-technical", "accessible", "clear"],
        "complexity": "medium"
    },
    {
        "id": "document_016",
        "category": "document",
        "subcategory": "editing",
        "query": "Expand this brief into a full paragraph: 'Product launch delayed due to bugs.'",
        "expected_elements": ["expanded", "detailed", "elaborated", "context"],
        "complexity": "medium"
    },
    {
        "id": "document_017",
        "category": "document",
        "subcategory": "editing",
        "query": "Make this more persuasive: 'Our product is good. You should buy it. It has features.'",
        "expected_elements": ["persuasive", "compelling", "benefits", "convincing"],
        "complexity": "medium"
    },
    {
        "id": "document_018",
        "category": "document",
        "subcategory": "editing",
        "query": "Adjust the tone from casual to formal: 'What's up? Just checking in on that thing. Hit me back when you can.'",
        "expected_elements": ["formal", "professional", "tone", "adjustment"],
        "complexity": "low"
    },

    # Summarization (7 tests)
    {
        "id": "document_019",
        "category": "document",
        "subcategory": "summarization",
        "query": "Summarize this article in 3 bullets: [Imagine a 500-word article about remote work trends including: 58% of companies offer remote work, productivity increased 22%, challenges include isolation and communication. Focus on key statistics.]",
        "expected_elements": ["summary", "key points", "bullets", "concise"],
        "complexity": "medium"
    },
    {
        "id": "document_020",
        "category": "document",
        "subcategory": "summarization",
        "query": "Create a one-sentence executive summary for a 20-page report about Q3 performance: revenue up 15%, customer acquisition cost down 8%, market share increased to 23%, but churn rose 2%.",
        "expected_elements": ["executive summary", "one-sentence", "key metrics", "overview"],
        "complexity": "medium"
    },
    {
        "id": "document_021",
        "category": "document",
        "subcategory": "summarization",
        "query": "Summarize a 30-minute meeting transcript (hypothetical) into 5 action items. Topics discussed: product roadmap, hiring plan, budget allocation, marketing strategy, and tech debt.",
        "expected_elements": ["action items", "summary", "decisions", "next steps"],
        "complexity": "high"
    },
    {
        "id": "document_022",
        "category": "document",
        "subcategory": "summarization",
        "query": "Extract the key insights from this customer feedback (imagine 10 reviews): 4 praise speed, 3 complain about UI, 2 want more features, 1 mention bugs.",
        "expected_elements": ["insights", "feedback", "patterns", "summary"],
        "complexity": "medium"
    },
    {
        "id": "document_023",
        "category": "document",
        "subcategory": "summarization",
        "query": "Create a tl;dr summary of a blog post about 'The Future of AI in Healthcare'. The post covers: diagnostic AI, drug discovery, personalized medicine, ethical concerns, and regulatory challenges.",
        "expected_elements": ["tl;dr", "summary", "key topics", "brief"],
        "complexity": "medium"
    },
    {
        "id": "document_024",
        "category": "document",
        "subcategory": "summarization",
        "query": "Condense this project update into a status tweet (280 chars): 'Phase 1 complete: API designed and documented. Phase 2 in progress: backend development, 60% done. Phase 3 (frontend) delayed by 2 weeks due to resource constraints. ETD: November 15th.'",
        "expected_elements": ["tweet", "condensed", "status", "brief"],
        "complexity": "low"
    },
    {
        "id": "document_025",
        "category": "document",
        "subcategory": "summarization",
        "query": "Write a 50-word abstract for a paper titled 'Machine Learning for Predictive Maintenance'. The paper discusses: using sensor data, LSTM models, 30% cost reduction, real-time monitoring, case study in manufacturing.",
        "expected_elements": ["abstract", "50 words", "concise", "overview"],
        "complexity": "medium"
    },
]

__all__ = ["DOCUMENT_TESTS"]
