import streamlit as st
from groq import Groq
import json
import re
import random
import concurrent.futures
import os
from dotenv import load_dotenv

# ─── Load ENV ─────────────────────────────────────────────────────────────
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found. Please set it in environment variables.")
    st.stop()

# ─── Page Config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCQ Distracter Generator",
    page_icon="🎯",
    layout="wide"
)

# ─── Session State ───────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "saved_questions" not in st.session_state:
    st.session_state.saved_questions = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "num_questions" not in st.session_state:
    st.session_state.num_questions = 1
if "form_reset_key" not in st.session_state:
    st.session_state.form_reset_key = 0

# ─── Generate Distractors ────────────────────────────────────────────────
def generate_distractors(index, question, correct_answer, subject):
    try:
        client = Groq(api_key=api_key)

        prompt = f"""You are an expert MCQ creator for educational assessments.

Subject: {subject}
Question: {question}
Correct Answer: {correct_answer}

Generate exactly 3 DISTRACTORS (wrong answer options).

Rules:
1. Plausible and logical — not obviously wrong
2. Similar length and style to the correct answer
3. Target common misconceptions
4. Must be CLEARLY WRONG
5. Do NOT repeat or paraphrase the correct answer

Return ONLY JSON:
{{
  "distractors": ["A", "B", "C"],
  "explanation": "Why these distractors are effective"
}}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )

        text = response.choices[0].message.content.strip()
        text = re.sub(r'```json|```', '', text).strip()
        data = json.loads(text)

        distractors = data.get("distractors", [])
        options = distractors + [correct_answer]
        random.shuffle(options)

        return {
            "question": question,
            "correct_answer": correct_answer,
            "options": options,
            "labels": ["A", "B", "C", "D"],
            "explanation": data.get("explanation", ""),
            "error": None
        }

    except Exception as e:
        return {
            "question": question,
            "correct_answer": correct_answer,
            "options": [],
            "labels": ["A", "B", "C", "D"],
            "explanation": "",
            "error": str(e)
        }

# ─── Parallel Execution ──────────────────────────────────────────────────
def generate_all_parallel(questions, subject):
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(generate_distractors, i, q, a, subject)
            for i, (q, a) in enumerate(questions)
        ]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

# ─── MAIN APP ────────────────────────────────────────────────────────────
def main():
    st.title("🎯 MCQ Distracter Generator")

    num_q = st.number_input("Number of Questions", 1, 10, 1)
    subject = st.text_input("Subject")

    questions = []
    for i in range(num_q):
        q = st.text_area(f"Question {i+1}")
        a = st.text_input(f"Answer {i+1}")
        questions.append((q, a))

    if st.button("Generate MCQs"):
        valid = all(q.strip() and a.strip() for q, a in questions)

        if not valid:
            st.error("⚠️ Fill all fields")
            return

        with st.spinner("Generating..."):
            results = generate_all_parallel(questions, subject or "General")

        for i, r in enumerate(results):
            if r["error"]:
                st.error(f"❌ Q{i+1} failed: {r['error']}")
                continue

            st.subheader(f"Q{i+1}: {r['question']}")

            for j, opt in enumerate(r["options"]):
                correct = opt.strip().lower() == r["correct_answer"].strip().lower()
                mark = "✅" if correct else ""
                st.write(f"{r['labels'][j]}. {opt} {mark}")

            if r["explanation"]:
                st.info(r["explanation"])

# ─── RUN ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()