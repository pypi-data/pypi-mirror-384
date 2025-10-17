CODE_EXTENSIONS = {
    '.py', '.dart', '.js', '.ts', '.java', '.kt', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.php', '.swift', '.html', '.css', '.scss', '.json',
    '.yml', '.yaml', '.xml', '.sh', '.rb', '.jsx', '.tsx', '.vue', '.sql',
    '.md', '.txt', '.ini', '.cfg', '.conf', '.toml', '.r', '.scala', '.clj',
    '.hs', '.elm', '.lua', '.pl', '.pm', '.bat', '.ps1', '.vbs', '.asm'
}

IGNORE_PATTERNS = {
    '.git', 'node_modules', '.vscode', '.idea', '__pycache__', '.DS_Store',
    'Thumbs.db', '.env', 'venv', 'env', 'dist', 'build', '.next', '.nuxt',
    'coverage', '.nyc_output', 'logs', 'target', 'bin', 'obj', '.gradle',
    'gradle', 'cmake-build-debug', 'cmake-build-release', '.pytest_cache',
    '.mypy_cache', '.tox', 'htmlcov', '.coverage', 'vendor', 'composer.phar'
}

# AI Analysis Configuration
AI_ANALYSIS_PROMPT = """
Analyze the following codebase and provide detailed suggestions in the EXACT JSON format below.
Do NOT add any extra text, explanations, or markdown. ONLY return valid JSON.

Codebase Structure:
{structure}

Code Files Content:
{content}

Return ONLY this JSON structure with your analysis:
{{
    "solid_principles": [
        {{
            "principle": "Single Responsibility Principle",
            "violation": "Description of violation",
            "file": "path/to/file.ext",
            "class_or_function": "ClassName or function_name",
            "suggestion": "Brief suggestion"
        }}
    ],
    "design_patterns": [
        {{
            "pattern": "Pattern Name",
            "suggestion": "Where and why to apply",
            "file": "path/to/file.ext",
            "location": "Class or module name"
        }}
    ],
    "security_issues": [
        {{
            "issue": "Issue type",
            "severity": "high/medium/low",
            "description": "What's the problem",
            "file": "path/to/file.ext",
            "line": "Line number if known",
            "recommendation": "How to fix"
        }}
    ],
    "naming_conventions": [
        {{
            "issue": "Description",
            "file": "path/to/file.ext",
            "current_name": "currentName",
            "suggested_name": "suggested_name",
            "reason": "Why this is better"
        }}
    ],
    "architecture_recommendations": [
        {{
            "category": "Structure/Organization/etc",
            "current_state": "What exists now",
            "recommendation": "What should be done",
            "benefit": "Why this helps"
        }}
    ],
    "general_recommendations": [
        {{
            "title": "Recommendation title",
            "description": "Detailed description",
            "priority": "high/medium/low"
        }}
    ]
}}

CRITICAL: Return ONLY valid JSON. No markdown, no code blocks, no extra text.
"""

# PDF Configuration
PDF_TITLE = "CodePeek Analysis Report"
PDF_SECTIONS = {
    "solid_principles": "SOLID Principles Analysis",
    "design_patterns": "Design Patterns Suggestions",
    "security_issues": "Security Issues",
    "naming_conventions": "Naming Conventions",
    "architecture_recommendations": "Architecture Recommendations",
    "general_recommendations": "General Recommendations"
}

SEVERITY_COLORS = {
    "high": (220, 53, 69),     
    "medium": (255, 193, 7),   
    "low": (40, 167, 69)        
}

PRIORITY_COLORS = {
    "high": (220, 53, 69),
    "medium": (255, 193, 7),
    "low": (40, 167, 69)
}