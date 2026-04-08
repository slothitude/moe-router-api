"""Agentic assistant test cases - 30 tests.

Multi-step reasoning, planning, tool use simulation.
"""

AGENTIC_TESTS = [
    # Planning Tasks (10 tests)
    {
        "id": "agentic_001",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Plan a 5-day trip to Tokyo with budget constraints. Consider: flights, hotels, food, attractions. Prioritize cultural experiences.",
        "expected_elements": ["itinerary", "budget", "cultural", "transport", "days"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_002",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Create a comprehensive study plan for learning machine learning in 3 months. Include: math prerequisites, programming skills, projects, and resources.",
        "expected_elements": ["math", "programming", "projects", "timeline", "resources"],
        "complexity": "high",
        "estimated_steps": 6
    },
    {
        "id": "agentic_003",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Design a meal prep plan for a family of 4 for one week. Budget: $150. Dietary restrictions: vegetarian, gluten-free. Include shopping list.",
        "expected_elements": ["meals", "budget", "shopping", "vegetarian", "gluten-free"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_004",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Plan a software development project from scratch. Team: 5 developers. Timeline: 6 months. Product: e-commerce platform. Include phases and milestones.",
        "expected_elements": ["phases", "milestones", "team", "timeline", "development"],
        "complexity": "high",
        "estimated_steps": 7
    },
    {
        "id": "agentic_005",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Create a fitness training plan for a beginner preparing for their first 5K run in 8 weeks. Include workout schedule, nutrition, and rest days.",
        "expected_elements": ["training", "schedule", "nutrition", "rest", "weeks"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_006",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Develop a content marketing strategy for a B2B SaaS startup. Include: content types, channels, frequency, and KPIs to track.",
        "expected_elements": ["strategy", "content", "channels", "frequency", "metrics"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_007",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Plan a home renovation project: kitchen remodel. Budget: $25,000. Timeline: 6 weeks. Include contractors, materials, and contingency.",
        "expected_elements": ["budget", "timeline", "contractors", "materials", "contingency"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_008",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Create a disaster preparedness plan for a small business. Include: risk assessment, emergency procedures, communication plan, and recovery steps.",
        "expected_elements": ["risk", "emergency", "communication", "recovery", "procedures"],
        "complexity": "high",
        "estimated_steps": 6
    },
    {
        "id": "agentic_009",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Design an onboarding program for new remote employees. First week focus. Include: orientation, tools setup, training sessions, and team integration.",
        "expected_elements": ["onboarding", "orientation", "tools", "training", "remote"],
        "complexity": "medium",
        "estimated_steps": 5
    },
    {
        "id": "agentic_010",
        "category": "agentic",
        "subcategory": "planning",
        "query": "Plan a fundraising event for a non-profit. Goal: $50,000. Event type: gala. Include: venue, catering, entertainment, and sponsorship tiers.",
        "expected_elements": ["fundraising", "venue", "catering", "entertainment", "sponsorship"],
        "complexity": "high",
        "estimated_steps": 5
    },

    # Multi-step Reasoning (10 tests)
    {
        "id": "agentic_011",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "A company has 100 employees. If 20% work in sales, 30% in engineering, and the rest in operations. If sales team grows by 50% and engineering shrinks by 20%, what's the new distribution?",
        "expected_elements": ["calculation", "sales", "engineering", "operations", "percentage"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_012",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "You're troubleshooting a slow website. Symptoms: pages load in 10s, CPU at 80%, database queries slow. Walk through your diagnostic steps and solutions.",
        "expected_elements": ["troubleshooting", "database", "diagnosis", "solutions", "performance"],
        "complexity": "high",
        "estimated_steps": 6
    },
    {
        "id": "agentic_013",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "Analyze this business decision: Should we switch from annual to monthly pricing? Consider: cash flow, churn, customer acquisition cost, and LTV.",
        "expected_elements": ["pricing", "cash flow", "churn", "CAC", "LTV"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_014",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "A product has three features. Users rate them: A=8/10, B=6/10, C=9/10. But only 20% use C, while 80% use A and B. How do you prioritize development?",
        "expected_elements": ["prioritization", "usage", "ratings", "trade-offs", "development"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_015",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "You notice a 30% drop in organic traffic. Google Analytics shows traffic dropped equally across all pages. What are your hypotheses and how do you test them?",
        "expected_elements": ["analysis", "hypotheses", "testing", "traffic", "investigation"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_016",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "Your team velocity decreased by 40% this sprint. Possible factors: 2 engineers sick, new tools introduced, scope creep. How do you diagnose and address?",
        "expected_elements": ["velocity", "diagnosis", "factors", "solutions", "sprint"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_017",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "A SaaS company has: MRR $100K, churn 5%, ARPU $50, 2000 customers. If they reduce churn to 3% and increase ARPU to $60, what's the new MRR after 6 months assuming no new customers?",
        "expected_elements": ["calculation", "churn", "MRR", "ARPU", "projection"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_018",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "You need to choose between two job offers. Offer A: $120K salary, $20K bonus, fully remote. Offer B: $140K salary, $40K bonus, hybrid 3 days/week. What's your analysis?",
        "expected_elements": ["comparison", "salary", "bonus", "remote", "trade-offs"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_019",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "A database has 1M records. Query takes 10s. You add an index, it takes 2s. But inserts now take 2x longer. Was this the right decision? Explain your reasoning.",
        "expected_elements": ["database", "index", "performance", "trade-offs", "reasoning"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_020",
        "category": "agentic",
        "subcategory": "reasoning",
        "query": "Your app crashes on iOS 17 but works on iOS 16. Crash logs show: 'Thread 0: SIGABRT'. 50% of users are on iOS 17. What's your response plan?",
        "expected_elements": ["troubleshooting", "crash", "iOS", "plan", "priority"],
        "complexity": "high",
        "estimated_steps": 5
    },

    # Tool Use Simulation (10 tests)
    {
        "id": "agentic_021",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "I need to analyze customer reviews. First, search for how to use sentiment analysis APIs. Then, outline a solution using Python and a cloud service.",
        "expected_elements": ["research", "solution", "API", "Python", "sentiment"],
        "complexity": "medium",
        "estimated_steps": 3
    },
    {
        "id": "agentic_022",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "Help me debug this: my Python script works locally but fails in Docker. Error: 'Connection refused'. Walk through checking network, ports, and environment variables.",
        "expected_elements": ["debugging", "Docker", "network", "environment", "troubleshooting"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_023",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "I want to automate daily reports from Google Analytics. Outline the steps: authenticate, fetch data, generate report, email it. Include tools/APIs to use.",
        "expected_elements": ["automation", "API", "authentication", "reports", "email"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_024",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "Create a workflow: monitor a website every hour, alert if down, log results. Specify tools, cron configuration, and alerting mechanism.",
        "expected_elements": ["monitoring", "workflow", "cron", "alerts", "logging"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_025",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "I need to extract data from 1000 PDFs. Plan the solution: choose libraries (Python), handle errors, parallel processing, and output format.",
        "expected_elements": ["PDF", "extraction", "Python", "parallel", "format"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_026",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "Set up CI/CD for a React app. Steps: run tests, build, deploy to Vercel. Include GitHub Actions workflow configuration.",
        "expected_elements": ["CI/CD", "React", "tests", "deployment", "GitHub Actions"],
        "complexity": "high",
        "estimated_steps": 4
    },
    {
        "id": "agentic_027",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "I need to merge two CSV files by email address. Some emails are in different formats. Plan: cleaning, fuzzy matching, merging tools (Python/pandas).",
        "expected_elements": ["CSV", "merging", "cleaning", "fuzzy matching", "pandas"],
        "complexity": "medium",
        "estimated_steps": 4
    },
    {
        "id": "agentic_028",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "Build a chatbot backend: receive webhook from Slack, process with LLM, respond. Include API design, webhook handler, and response format.",
        "expected_elements": ["chatbot", "Slack", "webhook", "LLM", "API"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_029",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "Create a data pipeline: collect tweets with hashtag #AI, clean text, extract sentiment, store in database. Specify tools and architecture.",
        "expected_elements": ["pipeline", "Twitter", "sentiment", "database", "architecture"],
        "complexity": "high",
        "estimated_steps": 5
    },
    {
        "id": "agentic_030",
        "category": "agentic",
        "subcategory": "tool_use",
        "query": "I need to backup MySQL to S3 every night. Plan: mysqldump command, compression, S3 upload, retention policy, and monitoring.",
        "expected_elements": ["backup", "MySQL", "S3", "compression", "retention"],
        "complexity": "medium",
        "estimated_steps": 4
    },
]

__all__ = ["AGENTIC_TESTS"]
