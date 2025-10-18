"""
Parse #lang directive from PW code
"""

import re
from typing import Tuple


SUPPORTED_LANGUAGES = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "go": "go",
    "golang": "go",
    "rust": "rust",
    "rs": "rust"
}


def parse_language_header(code: str) -> Tuple[str, str]:
    """
    Parse #lang directive from PW code
    
    Examples:
        "#lang python\ncode" → ("python", "code")
        "#lang javascript\ncode" → ("javascript", "code")
        "#lang go\ncode" → ("go", "code")
        "code" → ("python", "code")  # default to python
    
    Returns:
        (target_language, clean_code)
    """
    # Match #lang directive at start of file
    match = re.match(r'^\s*#lang\s+(\w+)\s*\n', code)
    
    if match:
        lang_name = match.group(1).lower()
        
        # Normalize language name
        target_lang = SUPPORTED_LANGUAGES.get(lang_name)
        
        if not target_lang:
            raise ValueError(
                f"Unsupported language: {lang_name}. "
                f"Supported: {', '.join(set(SUPPORTED_LANGUAGES.values()))}"
            )
        
        # Remove header from code
        clean_code = code[match.end():]
        return target_lang, clean_code
    
    # No header found - default to Python
    return "python", code


def add_language_header(code: str, target_lang: str) -> str:
    """Add #lang header to code"""
    return f"#lang {target_lang}\n{code}"


if __name__ == "__main__":
    # Test language header parser
    print("Testing Language Header Parser...")
    print()
    
    test_cases = [
        ("#lang python\nprint('hello')", "python", "print('hello')"),
        ("#lang javascript\nconsole.log('hi')", "javascript", "console.log('hi')"),
        ("#lang go\nfmt.Println('test')", "go", "fmt.Println('test')"),
        ("# No header\ncode", "python", "# No header\ncode"),
        ("#lang py\ncode", "python", "code"),
        ("#lang js\ncode", "javascript", "code"),
    ]
    
    for code, expected_lang, expected_code in test_cases:
        lang, clean = parse_language_header(code)
        status = "✅" if lang == expected_lang and clean == expected_code else "❌"
        print(f"{status} Input: {repr(code[:30])}")
        print(f"   Detected: {lang}, Code: {repr(clean[:30])}")
    
    print()
    print("✅ Language header parser working!")
