import re
import urllib.parse

LATEX_SERVICE = "https://latex.codecogs.com/png.latex?"


def latex_to_url(latex: str, inline: bool = True) -> str:
    """Convert LaTeX formula to codecogs URL for rendering."""
    if inline:
        latex = f"\\colorbox{{white}}{{$ {latex} $}}"
    encoded = urllib.parse.quote(latex)
    return f"{LATEX_SERVICE}{encoded}"


def find_latex_expressions(text: str) -> list[tuple[int, int, str]]:
    """Find all LaTeX expressions in text.

    Returns list of (start, end, formula) tuples.
    Matches both $...$ (inline) and $$...$$ (block).
    """
    results = []

    # Block math $$...$$
    for m in re.finditer(r'\$\$(.+?)\$\$', text, re.DOTALL):
        results.append((m.start(), m.end(), m.group(1)))

    # Inline math $...$  (skip $$)
    for m in re.finditer(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', text):
        # Check it's not inside a $$ block
        is_in_block = any(s <= m.start() <= e for s, e, _ in results)
        if not is_in_block:
            results.append((m.start(), m.end(), m.group(1)))

    return results


def render_latex_in_html(text: str) -> str:
    """Replace LaTeX expressions with rendered images in HTML."""
    expressions = find_latex_expressions(text)
    result = text
    offset = 0

    for start, end, formula in expressions:
        url = latex_to_url(formula)
        img_tag = f'<img src="{url}" alt="{formula}" style="vertical-align: middle;" />'
        result = result[:start + offset] + img_tag + result[end + offset:]
        offset += len(img_tag) - (end - start)

    return result


def validate_latex(latex: str) -> tuple[bool, str]:
    """Basic validation of LaTeX syntax. Returns (is_valid, message)."""
    # Check balanced braces
    depth = 0
    for ch in latex:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        if depth < 0:
            return False, "Unmatched closing brace }"
    if depth != 0:
        return False, f"Unmatched opening brace(s): {depth} unclosed"

    # Check balanced brackets
    depth = 0
    for ch in latex:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if depth < 0:
            return False, "Unmatched closing bracket ]"
    if depth != 0:
        return False, f"Unmatched opening bracket(s): {depth} unclosed"

    return True, "Valid"
