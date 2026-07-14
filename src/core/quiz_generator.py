import re
import random
import logging

logger = logging.getLogger("MarkdownToPDF.quiz")


def generate_quiz_from_text(text: str) -> dict:
    """Generate a quiz from Markdown text.

    Extracts headings as topics and bullet points as potential answers.
    Returns dict with questions, each having question, options, answer.
    """
    lines = text.split('\n')
    headings = []
    bullets = {}
    current_heading = None

    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r'^(#{1,4})\s+(.*)', stripped)
        bullet_match = re.match(r'^[-*+]\s+(.*)', stripped)

        if heading_match:
            current_heading = heading_match.group(2).strip()
            headings.append(current_heading)
            bullets[current_heading] = []
        elif bullet_match and current_heading:
            bullets[current_heading].append(bullet_match.group(1).strip())

    questions = []

    # Generate questions from headings + bullets
    for heading in headings:
        items = bullets.get(heading, [])
        if len(items) >= 2:
            # Multiple choice from bullet points
            correct = items[0]
            wrong = [item for item in items[1:]]
            wrong = wrong[:3]  # Max 3 wrong options

            if len(wrong) < 3:
                # Fill with other headings as distractors
                other_headings = [h for h in headings if h != heading and h != correct]
                wrong.extend(other_headings[:3 - len(wrong)])

            options = [correct] + wrong
            random.shuffle(options)

            questions.append({
                "question": f"What is related to: {heading}?",
                "options": options,
                "answer": correct,
                "topic": heading,
            })
        elif items:
            # True/False style
            questions.append({
                "question": f"True or False: {heading} is mentioned in the document.",
                "options": ["True", "False"],
                "answer": "True",
                "topic": heading,
            })

    # Generate fill-in-the-blank from sentences
    all_words = [w for w in re.findall(r'\b\w{4,}\b', text) if w[0].islower()]
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    for sentence in sentences[:5]:
        words = sentence.split()
        if len(words) > 5:
            key_word = random.choice([w for w in words if len(w) > 4] or words[3:6])
            blank = sentence.replace(key_word, "________")
            distractors = [w for w in all_words if w.lower() != key_word.lower()]
            random.shuffle(distractors)
            options = [key_word] + distractors[:3]
            random.shuffle(options)
            questions.append({
                "question": f"Fill in the blank: {blank}",
                "options": options,
                "answer": key_word,
                "topic": "Fill-in-the-blank",
            })

    return {
        "questions": questions,
        "total": len(questions),
        "topics": headings,
    }


def quiz_to_markdown(quiz: dict) -> str:
    """Convert quiz to Markdown format."""
    lines = [f"# Quiz ({quiz['total']} questions)\n"]
    for i, q in enumerate(quiz['questions'], 1):
        lines.append(f"### Question {i}\n")
        lines.append(f"{q['question']}\n")
        for j, opt in enumerate(q['options'], 1):
            lines.append(f"  {chr(96+j)}) {opt}")
        lines.append(f"\n**Answer:** {q['answer']}\n")
    return "\n".join(lines)


def quiz_to_html(quiz: dict) -> str:
    """Convert quiz to interactive HTML."""
    import html
    questions_html = []
    for i, q in enumerate(quiz['questions'], 1):
        options_html = []
        for j, opt in enumerate(q['options']):
            safe_opt = html.escape(opt)
            options_html.append(f"""
            <label class="option">
                <input type="radio" name="q{i}" value="{safe_opt}" />
                <span>{safe_opt}</span>
            </label>""")

        safe_q = html.escape(q['question'])
        safe_a = html.escape(q['answer'])
        questions_html.append(f"""
        <div class="question" id="q{i}">
            <h3>Q{i}: {safe_q}</h3>
            {''.join(options_html)}
            <div class="answer" style="display:none;color:#27ae60;font-weight:bold;">
                Correct: {safe_a}
            </div>
        </div>""")

    return f"""<!DOCTYPE html>
<html><head><style>
body {{ font-family: sans-serif; padding: 20px; max-width: 700px; margin: 0 auto; }}
.question {{ background: white; border-radius: 8px; padding: 16px; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.option {{ display: block; padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 4px; cursor: pointer; }}
.option:hover {{ background: #e9ecef; }}
.option input {{ margin-right: 8px; }}
.show-answers {{ background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }}
</style></head><body>
<h2>📝 Quiz ({quiz['total']} questions)</h2>
<button class="show-answers" onclick="document.querySelectorAll('.answer').forEach(a=>a.style.display='block')">
    Show All Answers
</button>
{''.join(questions_html)}
</body></html>"""
