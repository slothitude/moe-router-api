"""Code generation and debugging test cases - 30 tests."""

CODE_TESTS = [
    # Code Generation (12 tests)
    {
        "id": "code_001",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Write a Python function to validate email addresses using regex. Handle: dots, plus signs, multiple @ symbols. Return boolean.",
        "expected_elements": ["function", "regex", "validation", "email", "boolean"],
        "complexity": "medium"
    },
    {
        "id": "code_002",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Create a Python class for a basic binary search tree with methods: insert, search, delete, and inorder traversal.",
        "expected_elements": ["class", "binary search tree", "insert", "search", "traversal"],
        "complexity": "high"
    },
    {
        "id": "code_003",
        "category": "code",
        "subcategory": "generation",
        "language": "javascript",
        "query": "Write a JavaScript function to debounce input events. Delay: 300ms. Should work for search input in a React component.",
        "expected_elements": ["function", "debounce", "delay", "event", "React"],
        "complexity": "medium"
    },
    {
        "id": "code_004",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Create a Python async function to fetch multiple URLs concurrently using aiohttp. Handle errors and timeouts. Return list of responses.",
        "expected_elements": ["async", "aiohttp", "concurrent", "fetch", "error handling"],
        "complexity": "high"
    },
    {
        "id": "code_005",
        "category": "code",
        "subcategory": "generation",
        "language": "sql",
        "query": "Write a SQL query to find the top 10 customers by total order value. Tables: customers (id, name), orders (id, customer_id, amount). Join and group by.",
        "expected_elements": ["SQL", "JOIN", "GROUP BY", "ORDER BY", "aggregate"],
        "complexity": "medium"
    },
    {
        "id": "code_006",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Write a Python decorator that caches function results for 5 minutes. Use functools. Handle function arguments as cache keys.",
        "expected_elements": ["decorator", "cache", "functools", "timing", "wrapper"],
        "complexity": "high"
    },
    {
        "id": "code_007",
        "category": "code",
        "subcategory": "generation",
        "language": "javascript",
        "query": "Implement a JavaScript Promise.race() polyfill from scratch. Should accept array of promises and return first to resolve/reject.",
        "expected_elements": ["Promise", "race", "polyfill", "async", "array"],
        "complexity": "high"
    },
    {
        "id": "code_008",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Create a FastAPI endpoint for file upload. Accept: image files (max 5MB). Save to disk, return file URL. Include validation.",
        "expected_elements": ["FastAPI", "upload", "validation", "file", "endpoint"],
        "complexity": "medium"
    },
    {
        "id": "code_009",
        "category": "code",
        "subcategory": "generation",
        "language": "html/css",
        "query": "Create HTML and CSS for a responsive card grid. Cards have: image, title, description. Grid: 3 columns desktop, 2 tablet, 1 mobile. Use CSS Grid.",
        "expected_elements": ["HTML", "CSS", "Grid", "responsive", "media queries"],
        "complexity": "medium"
    },
    {
        "id": "code_010",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Write a Python context manager for measuring execution time. Should print time elapsed when exiting context. Use time module.",
        "expected_elements": ["context manager", "timing", "with statement", "time", "measurement"],
        "complexity": "medium"
    },
    {
        "id": "code_011",
        "category": "code",
        "subcategory": "generation",
        "language": "bash",
        "query": "Write a bash script to backup a MySQL database. Steps: check if mysqldump exists, create backup filename with date, compress with gzip, keep last 7 days.",
        "expected_elements": ["bash", "mysqldump", "backup", "compression", "cron"],
        "complexity": "medium"
    },
    {
        "id": "code_012",
        "category": "code",
        "subcategory": "generation",
        "language": "python",
        "query": "Implement a Python generator function to read large CSV files line by line without loading entire file into memory. Yield dict per row.",
        "expected_elements": ["generator", "CSV", "memory efficient", "yield", "iteration"],
        "complexity": "medium"
    },

    # Code Debugging (10 tests)
    {
        "id": "code_013",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "Fix this Python code that's causing infinite loop:\nfor i in range(10):\n    if i % 2 == 0:\n        continue\n    i -= 1\n    print(i)",
        "expected_elements": ["debug", "loop", "logic error", "fix", "explanation"],
        "complexity": "low"
    },
    {
        "id": "code_014",
        "category": "code",
        "subcategory": "debugging",
        "language": "javascript",
        "query": "Debug why this React component doesn't update when props change:\nconst MyComponent = (props) => {\n  const data = props.data;\n  return <div>{data}</div>;\n};",
        "expected_elements": ["React", "debug", "props", "update", "explanation"],
        "complexity": "medium"
    },
    {
        "id": "code_015",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "Fix the list comprehension error: result = [x * 2 for x in range(10) if x > 5 else x]. Explain what's wrong and provide correct version.",
        "expected_elements": ["debug", "list comprehension", "syntax error", "fix", "explanation"],
        "complexity": "low"
    },
    {
        "id": "code_016",
        "category": "code",
        "subcategory": "debugging",
        "language": "javascript",
        "query": "Why does this async function always return undefined? Fix it:\nasync function getData() {\n  fetch('/api/data')\n    .then(res => res.json())\n    .then(data => data);\n}",
        "expected_elements": ["async", "Promise", "return", "debug", "fix"],
        "complexity": "medium"
    },
    {
        "id": "code_017",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "This code raises TypeError: can't multiply sequence by non-int. Fix it:\nprice = '100'\ndiscount = 0.1\nfinal_price = price * (1 - discount)",
        "expected_elements": ["debug", "TypeError", "type conversion", "fix", "explanation"],
        "complexity": "low"
    },
    {
        "id": "code_018",
        "category": "code",
        "subcategory": "debugging",
        "language": "sql",
        "query": "This query is slow. Optimize it:\nSELECT * FROM orders o, customers c WHERE o.customer_id = c.id AND c.country = 'USA'. Explain the issue.",
        "expected_elements": ["SQL", "optimization", "JOIN", "performance", "explain"],
        "complexity": "medium"
    },
    {
        "id": "code_019",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "Fix the mutable default argument bug:\ndef append_to_list(item, lst=[]):\n    lst.append(item)\n    return lst\n\nExplain why this is problematic.",
        "expected_elements": ["debug", "default argument", "mutable", "fix", "explanation"],
        "complexity": "medium"
    },
    {
        "id": "code_020",
        "category": "code",
        "subcategory": "debugging",
        "language": "javascript",
        "query": "Why does 'this' lose context in this callback? Fix:\nclass Counter {\n  constructor() { this.count = 0; }\n  increment() { setTimeout(function() { this.count++; }, 100); }\n}",
        "expected_elements": ["this", "context", "callback", "bind", "fix"],
        "complexity": "medium"
    },
    {
        "id": "code_021",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "This code causes MemoryError when processing large files. Fix:\nwith open('large.txt', 'r') as f:\n    content = f.read()\n    lines = content.split('\\n')",
        "expected_elements": ["debug", "memory", "file handling", "efficient", "fix"],
        "complexity": "medium"
    },
    {
        "id": "code_022",
        "category": "code",
        "subcategory": "debugging",
        "language": "python",
        "query": "Fix the race condition in this code:\nif not os.path.exists('file.txt'):\n    write_to_file('file.txt', data)",
        "expected_elements": ["debug", "race condition", "concurrency", "fix", "explanation"],
        "complexity": "high"
    },

    # Code Optimization (8 tests)
    {
        "id": "code_023",
        "category": "code",
        "subcategory": "optimization",
        "language": "python",
        "query": "Optimize this O(n²) code to O(n):\nresult = []\nfor item in items:\n    if item not in result:\n        result.append(item)\nreturn result",
        "expected_elements": ["optimization", "O(n)", "set", "performance", "algorithm"],
        "complexity": "medium"
    },
    {
        "id": "code_024",
        "category": "code",
        "subcategory": "optimization",
        "language": "python",
        "query": "Refactor nested loops using list comprehension:\nresult = []\nfor i in range(10):\n    for j in range(10):\n        if i * j > 50:\n            result.append((i, j))",
        "expected_elements": ["refactor", "list comprehension", "nested loops", "clean code"],
        "complexity": "low"
    },
    {
        "id": "code_025",
        "category": "code",
        "subcategory": "optimization",
        "language": "javascript",
        "query": "Optimize this inefficient array operation:\nlet arr = [1, 2, 3, 4, 5];\nfor (let i = 0; i < arr.length; i++) {\n  arr.splice(i, 1);\n}",
        "expected_elements": ["optimization", "array", "splice", "performance", "fix"],
        "complexity": "medium"
    },
    {
        "id": "code_026",
        "category": "code",
        "subcategory": "optimization",
        "language": "python",
        "query": "Optimize database queries in this loop:\nfor user_id in user_ids:\n    user = db.query('SELECT * FROM users WHERE id = ?', user_id)\n    process(user)",
        "expected_elements": ["optimization", "database", "batch", "IN clause", "performance"],
        "complexity": "high"
    },
    {
        "id": "code_027",
        "category": "code",
        "subcategory": "optimization",
        "language": "python",
        "query": "Replace string concatenation with f-string for better performance:\nname = 'World'\nmessage = 'Hello, ' + name + '! Today is ' + day + '.'",
        "expected_elements": ["f-string", "optimization", "string formatting", "performance"],
        "complexity": "low"
    },
    {
        "id": "code_028",
        "category": "code",
        "subcategory": "optimization",
        "language": "javascript",
        "query": "Optimize this jQuery code to vanilla JS:\n$('.button').on('click', function() {\n  $(this).addClass('active');\n});",
        "expected_elements": ["optimization", "vanilla JS", "jQuery", "performance", "DOM"],
        "complexity": "low"
    },
    {
        "id": "code_029",
        "category": "code",
        "subcategory": "optimization",
        "language": "python",
        "query": "Use caching to optimize this recursive Fibonacci function:\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
        "expected_elements": ["optimization", "caching", "memoization", "recursion", "performance"],
        "complexity": "medium"
    },
    {
        "id": "code_030",
        "category": "code",
        "subcategory": "optimization",
        "language": "sql",
        "query": "Optimize this query that uses subquery:\nSELECT name, (SELECT COUNT(*) FROM orders WHERE customer_id = c.id) as order_count FROM customers c",
        "expected_elements": ["SQL", "optimization", "JOIN", "subquery", "performance"],
        "complexity": "medium"
    },
]

__all__ = ["CODE_TESTS"]
