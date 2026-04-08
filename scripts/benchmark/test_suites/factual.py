"""Quick factual questions test cases - 25 tests."""

FACTUAL_TESTS = [
    # Definitions (7 tests)
    {
        "id": "factual_001",
        "category": "factual",
        "subcategory": "definition",
        "query": "What is a REST API? Provide a concise definition.",
        "expected_elements": ["REST", "API", "definition", "HTTP", "architecture"],
        "complexity": "low"
    },
    {
        "id": "factual_002",
        "category": "factual",
        "subcategory": "definition",
        "query": "Define 'machine learning' in one sentence.",
        "expected_elements": ["machine learning", "AI", "definition", "algorithms", "data"],
        "complexity": "low"
    },
    {
        "id": "factual_003",
        "category": "factual",
        "subcategory": "definition",
        "query": "What is the difference between HTTP and HTTPS?",
        "expected_elements": ["HTTP", "HTTPS", "security", "encryption", "difference"],
        "complexity": "low"
    },
    {
        "id": "factual_004",
        "category": "factual",
        "subcategory": "definition",
        "query": "Define 'containerization' in software context.",
        "expected_elements": ["container", "Docker", "isolation", "deployment", "definition"],
        "complexity": "low"
    },
    {
        "id": "factual_005",
        "category": "factual",
        "subcategory": "definition",
        "query": "What is a SQL JOIN? Explain briefly.",
        "expected_elements": ["SQL", "JOIN", "tables", "combine", "database"],
        "complexity": "low"
    },
    {
        "id": "factual_006",
        "category": "factual",
        "subcategory": "definition",
        "query": "Define 'technical debt' in software development.",
        "expected_elements": ["technical debt", "code quality", "compromise", "refactoring", "definition"],
        "complexity": "low"
    },
    {
        "id": "factual_007",
        "category": "factual",
        "subcategory": "definition",
        "query": "What is a microservices architecture?",
        "expected_elements": ["microservices", "architecture", "services", "distributed", "definition"],
        "complexity": "low"
    },

    # Facts & Knowledge (8 tests)
    {
        "id": "factual_008",
        "category": "factual",
        "subcategory": "fact",
        "query": "What year was Python first released?",
        "expected_elements": ["Python", "year", "1991", "release", "history"],
        "complexity": "low"
    },
    {
        "id": "factual_009",
        "category": "factual",
        "subcategory": "fact",
        "query": "Who created the Linux kernel?",
        "expected_elements": ["Linux", "Linus Torvalds", "creator", "kernel", "1991"],
        "complexity": "low"
    },
    {
        "id": "factual_010",
        "category": "factual",
        "subcategory": "fact",
        "query": "What is the current latest stable version of React (as of 2024)?",
        "expected_elements": ["React", "version", "18", "stable", "JavaScript"],
        "complexity": "low"
    },
    {
        "id": "factual_011",
        "category": "factual",
        "subcategory": "fact",
        "query": "What does ACID stand for in database transactions?",
        "expected_elements": ["ACID", "atomicity", "consistency", "isolation", "durability"],
        "complexity": "low"
    },
    {
        "id": "factual_012",
        "category": "factual",
        "subcategory": "fact",
        "query": "What is the time complexity of binary search?",
        "expected_elements": ["binary search", "O(log n)", "complexity", "algorithm", "performance"],
        "complexity": "low"
    },
    {
        "id": "factual_013",
        "category": "factual",
        "subcategory": "fact",
        "query": "Which company developed the TypeScript language?",
        "expected_elements": ["TypeScript", "Microsoft", "company", "developed", "JavaScript"],
        "complexity": "low"
    },
    {
        "id": "factual_014",
        "category": "factual",
        "subcategory": "fact",
        "query": "What is the default port for HTTPS?",
        "expected_elements": ["HTTPS", "port", "443", "default", "protocol"],
        "complexity": "low"
    },
    {
        "id": "factual_015",
        "category": "factual",
        "subcategory": "fact",
        "query": "When was the first iPhone released?",
        "expected_elements": ["iPhone", "2007", "Apple", "release", "first"],
        "complexity": "low"
    },

    # Comparisons (5 tests)
    {
        "id": "factual_016",
        "category": "factual",
        "subcategory": "comparison",
        "query": "What's the difference between Git and GitHub?",
        "expected_elements": ["Git", "GitHub", "version control", "tool", "service"],
        "complexity": "low"
    },
    {
        "id": "factual_017",
        "category": "factual",
        "subcategory": "comparison",
        "query": "SQL vs NoSQL: when to use which?",
        "expected_elements": ["SQL", "NoSQL", "database", "comparison", "use case"],
        "complexity": "medium"
    },
    {
        "id": "factual_018",
        "category": "factual",
        "subcategory": "comparison",
        "query": "What's the difference between let and const in JavaScript?",
        "expected_elements": ["let", "const", "JavaScript", "variables", "immutability"],
        "complexity": "low"
    },
    {
        "id": "factual_019",
        "category": "factual",
        "subcategory": "comparison",
        "query": "Compare Monolith and Microservices architecture in 3 points.",
        "expected_elements": ["monolith", "microservices", "comparison", "architecture", "trade-offs"],
        "complexity": "medium"
    },
    {
        "id": "factual_020",
        "category": "factual",
        "subcategory": "comparison",
        "query": "What's the difference between TCP and UDP?",
        "expected_elements": ["TCP", "UDP", "protocol", "reliability", "speed"],
        "complexity": "medium"
    },

    # Quick Answers (5 tests)
    {
        "id": "factual_021",
        "category": "factual",
        "subcategory": "answer",
        "query": "How do I check Python version in terminal?",
        "expected_elements": ["python", "version", "command", "terminal", "--version"],
        "complexity": "low"
    },
    {
        "id": "factual_022",
        "category": "factual",
        "subcategory": "answer",
        "query": "What's the shortcut to force refresh a browser?",
        "expected_elements": ["refresh", "shortcut", "Ctrl+F5", "browser", "cache"],
        "complexity": "low"
    },
    {
        "id": "factual_023",
        "category": "factual",
        "subcategory": "answer",
        "query": "How to stop a running process in terminal?",
        "expected_elements": ["stop", "Ctrl+C", "terminal", "process", "signal"],
        "complexity": "low"
    },
    {
        "id": "factual_024",
        "category": "factual",
        "subcategory": "answer",
        "query": "What's the command to list files in Unix/Linux?",
        "expected_elements": ["ls", "list", "files", "command", "Unix"],
        "complexity": "low"
    },
    {
        "id": "factual_025",
        "category": "factual",
        "subcategory": "answer",
        "query": "How do I install npm packages?",
        "expected_elements": ["npm", "install", "package", "command", "JavaScript"],
        "complexity": "low"
    },
]

__all__ = ["FACTUAL_TESTS"]
