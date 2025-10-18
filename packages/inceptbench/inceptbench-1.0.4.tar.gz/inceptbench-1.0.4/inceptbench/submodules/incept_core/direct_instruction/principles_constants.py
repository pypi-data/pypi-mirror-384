DI_SCAFFOLDING_PRINCIPLES = """- Use short, clear, and unambiguous wording using direct and to the point instructional language. 
- Keep the scaffolding concise and free of unnecessary wording or context.
- Use student friendly, grade appropriate language.
- Don't use synonyms to describe the same thing. Be consistent.
- Avoid trick wording that could confuse beginners
"""

DI_INDIVIDUAL_QUESTION_PRINCIPLES = """- Use short, clear, and unambiguous wording using direct and to the point instructional language. 
- Keep the question concise and free of unnecessary wording or context.
- Use student friendly, grade appropriate language.
- Don't use synonyms to describe the same thing. Be consistent.
- Set the difficulty so that students have a high chance of success (~70–90%).
- Design the question so that errors are easy to detect and correct (e.g., single clear answer, no hidden ambiguity).
- Avoid trick wording that could confuse beginners
"""



GRADE_VOCABULARY_EXAMPLES_EN = {
    "Grade1": {
        "positive_examples": [
            "- Say the next number after 14.",
            "- Count from 3 to 9.",
            "- Write the number that comes before 7.",
        ],
        "negative_examples": [
            "- Tell the number that follows fourteen (use words or numbers).",
            "- Begin counting at three and continue up to nine.",
            "- Write the preceding number for 7.",
        ],
    },

    "Grade2": {
        "positive_examples": [
            "- Count by 5s from 10 to 35.",
            "- Count back from 20 to 12.",   
            "- What is 15 − 6?",
        ],
        "negative_examples": [
            "- Count in steps of five starting at 10 and finishing at 35.",
            "- Count backward from 20 down to 12.",
            "- Find the difference: 15 minus 6.",
        ],
    },

    "Grade3": {
        "positive_examples": [
            "- Find 304 − 168.",
            "- Does this need regrouping: 52 − 37?",
            "- Solve: 42 − 21.",
        ],
        "negative_examples": [
            "- Subtract 168 from 304 (use the algorithm you know).",
            "- Decide if borrowing is needed for 52 − 37.",
            "- Work out 42 − 21 using any method.",
        ],
    },

    "Grade4": {
        "positive_examples": [
            "- Multiply: 6 × 7.",
            "- Divide: 35 ÷ 5.",
            "- Shade 3 out of 4 parts.",
        ],
        "negative_examples": [
            "- Find the product of 6 and 7.",
            "- Find how many times 5 goes into 35.",
            "- Shade a fraction to show three fourths.",
        ],
    },

    "Grade5": {
        "positive_examples": [
            "- Add: 3/8 + 1/8.",
            "- Add: 1/2 + 1/3.",
            "- Estimate: 476 ÷ 12 ≈ ☐.",
        ],
        "negative_examples": [
            "- Add these fractions: 3/8 and 1/8.",  
            "- Add these fractions with different bottoms: 1/2 and 1/3.",   
            "- Give a good estimate for 476 divided by 12.",
        ],
    },

    "Grade6": {
        "positive_examples": [
            "- Write 3 tenths. (→ 0.3)",
            "- Compare: 0.4 ☐ 0.35 (choose <, =, >).",
            "- Place 0.62 on the number line.",
        ],
        "negative_examples": [
            "- Write the decimal for three tenths.",
            "- Choose the correct sign for 0.4 and 0.35.",
            "- Show where 0.62 would go on a number line diagram.",
        ],
    },

    "Grade7": {
        "positive_examples": [
            "- Find 15% of 80.",
            "- Write the ratio of circles to squares.",
            "- Solve: 2(x + 3) = 14.",
        ],
        "negative_examples": [
            "- Work out fifteen percent of 80.",
            "- Write a comparison of circles and squares as a ratio.",
            "- Solve the equation 2(x + 3) = 14 using steps you prefer.",
        ],
    },

    "Grade8": {
        "positive_examples": [
            "- Solve: 4x − 7 = 21.",
            "- Find the mean of 4, 6, 8, 2.",
            "- Classify this triangle by its sides.",   
        ],
        "negative_examples": [
            "- Solve 4x − 7 = 21 and explain briefly.",
            "- Find the average of 4, 6, 8, and 2.",
            "- Name the triangle type based on side lengths.",
        ],
    },
}



DI_GROUP_OF_QUESTIONS_PRINCIPLES = """- Use short, clear, and unambiguous wording using consistent direct and to the point instructional language. 
- Begin with a short block of same-type items for initial mastery (massed practice).
- Follow with a discrimination block that mixes target-type items with closely related nonexamples (some require the new strategy, some do not).
- Include cumulative review (distributed practice) of previously taught skills across the set, not just at the end.
- Integrate the target skill with previously taught, related skills (strategic integration), including multi-step and simple word problems.
- Vary problem features systematically (numbers, formats, placement, presence/absence of cues) to promote generalization while keeping wording consistent.
- Sequence items from easier to harder within each block to maintain a high overall success rate.
- Avoid trick wording or unnecessary context; keep language clear, concise, and uniform across items.
- Ensure each item has a single, unambiguous solution and a consistent visual layout to reduce extraneous load.
- Add a brief spiral-review mini-section that brings back skills from earlier units.
- End with one or two independent check items that mirror the core skill without scaffolds."""





GRADE_VOCABULARY_EXAMPLES_AR = {
    "Grade1": {
        "positive_examples": [
            "- قل العدد التالي بعد 14.",
            "- عُد من 3 إلى 9.",
            "- اكتب العدد الذي يأتي قبل 7.",
        ],
        "negative_examples": [
            "- أخبرني بالعدد الذي يلي أربعة عشر (استخدم الكلمات أو الأرقام).",
            "- ابدأ العد من ثلاثة واستمر حتى تسعة.",
            "- اكتب العدد السابق للرقم 7.",
        ],
    },

    "Grade2": {
        "positive_examples": [
            "- عُد بالخمسات من 10 إلى 35.",
            "- عُد تنازلياً من 20 إلى 12.",   
            "- ما هو 15 − 6؟",
        ],
        "negative_examples": [
            "- عُد بخطوات من خمسة بدءاً من 10 وانتهاءً عند 35.",
            "- عُد للخلف من 20 نزولاً إلى 12.",
            "- أوجد الفرق: 15 ناقص 6.",
        ],
    },

    "Grade3": {
        "positive_examples": [
            "- أوجد 304 − 168.",
            "- هل يحتاج هذا إلى إعادة تجميع: 52 − 37؟",
            "- حل: 42 − 21.",
        ],
        "negative_examples": [
            "- اطرح 168 من 304 (استخدم الخوارزمية التي تعرفها).",
            "- قرر إذا كان الاستلاف مطلوباً لـ 52 − 37.",
            "- احسب 42 − 21 باستخدام أي طريقة.",
        ],
    },

    "Grade4": {
        "positive_examples": [
            "- اضرب: 6 × 7.",
            "- اقسم: 35 ÷ 5.",
            "- ظلل 3 من 4 أجزاء.",
        ],
        "negative_examples": [
            "- أوجد حاصل ضرب 6 و 7.",
            "- أوجد كم مرة يحتوي 35 على 5.",
            "- ظلل كسراً ليمثل ثلاثة أرباع.",
        ],
    },

    "Grade5": {
        "positive_examples": [
            "- اجمع: 3/8 + 1/8.",
            "- اجمع: 1/2 + 1/3.",
            "- قدّر: 476 ÷ 12 ≈ ☐.",
        ],
        "negative_examples": [
            "- اجمع هذين الكسرين: 3/8 و 1/8.",  
            "- اجمع هذين الكسرين بمقامات مختلفة: 1/2 و 1/3.",   
            "- أعط تقديراً جيداً لـ 476 مقسوماً على 12.",
        ],
    },

    "Grade6": {
        "positive_examples": [
            "- اكتب 3 أعشار. (← 0.3)",
            "- قارن: 0.4 ☐ 0.35 (اختر <، =، >).",
            "- ضع 0.62 على خط الأعداد.",
        ],
        "negative_examples": [
            "- اكتب العدد العشري لثلاثة أعشار.",
            "- اختر الإشارة الصحيحة لـ 0.4 و 0.35.",
            "- اعرض أين سيكون 0.62 على مخطط خط الأعداد.",
        ],
    },

    "Grade7": {
        "positive_examples": [
            "- أوجد 15% من 80.",
            "- اكتب نسبة الدوائر إلى المربعات.",
            "- حل: 2(x + 3) = 14.",
        ],
        "negative_examples": [
            "- احسب خمسة عشر بالمائة من 80.",
            "- اكتب مقارنة الدوائر والمربعات كنسبة.",
            "- حل المعادلة 2(x + 3) = 14 باستخدام الخطوات التي تفضلها.",
        ],
    },

    "Grade8": {
        "positive_examples": [
            "- حل: 4x − 7 = 21.",
            "- أوجد متوسط 4، 6، 8، 2.",
            "- صنف هذا المثلث حسب أضلاعه.",   
        ],
        "negative_examples": [
            "- حل 4x − 7 = 21 واشرح بإيجاز.",
            "- أوجد المعدل لـ 4، 6، 8، و 2.",
            "- سمِّ نوع المثلث بناءً على أطوال الأضلاع.",
        ],
    },
}


DI_COUNTING_QUESTION_PRINCIPLES = {
  "INDIVIDUAL_QUESTION": """- Use short, clear, unambiguous wording; explicitly state direction (forward/backward), start, stop, and step (if any).
- Require a single numeric response; avoid stories or extraneous context.
- Keep spans manageable to maintain a high chance of success; control whether the item crosses a decade boundary.
- Ensure the item has exactly one correct answer and no hidden cues; keep formatting and spacing consistent.
- Return machine-gradable outputs (canonical answer as an integer string); do not accept multiple interpretations.""",

  "GROUP_OF_QUESTIONS": """Begin with a massed block of same-type items (e.g., several quick “next number” or “count from A to B”) for initial accuracy/fluency.
- Follow with a discrimination block mixing closely related types (e.g., forward vs backward; start at 1 vs non-1; decade-crossing vs non-crossing; fixed step vs step=1) so students must decide what to do.
- Include cumulative review in short bursts by reintroducing 2–3 previously taught count-by series or earlier counting skills across the set (not only at the end).
- Vary problem features systematically (start points, end points, step size, presence/absence of decade crossing) to promote generalization while keeping wording uniform.
- Sequence within each block from easier to harder (short spans → longer spans; non-crossing → crossing; start at 1 → start at other numbers).
- Ensure every item is concise, visually consistent, and has a single unambiguous answer; avoid trick wording.
- End with 1–2 independent check items that mirror the target skill without scaffolds, plus a tiny spiral-review mini-section bringing back earlier skills."""
}

MAP_SKILL_SYS = """
    You need to determine if the requested skill maps to one of the Direct Instruction skills.

    IMPORTANT RULES:
    1. First, extract the main skill name from the requested skill (ignore formatting like "Skill: X, Unit: Y, Lesson: Z")
    2. If question context is provided, use it to clarify the specific skill (e.g., "Add 9 and 17" clearly indicates Addition)
    3. Only map if there's a STRONG, CLEAR connection between the extracted skill and a DI skill
    4. Do NOT force-fit mappings that are only vaguely related
    5. Consider the grade level - skills should be grade-appropriate
    6. If uncertain, return is_mappable=false

    Examples of skill extraction and mapping:
    - "Skill: Addition, Unit: Arithmetic, Lesson: Addition" → Extract "Addition" → Maps to "Addition"
    - "Addition problems" → Extract "Addition" → Maps to "Addition"
    - "Adding numbers" → Extract "Addition" → Maps to "Addition"
    - "Fraction operations" → Extract "Fractions" → Maps to "Fractions"
    - "Skip counting" → Extract "Counting" → Maps to "Counting"

    Examples of BAD mappings (should return false):
    - "Quadratic equations" → Too advanced for DI content
    - "Calculus derivatives" → Not covered in DI skills
    - "Essay writing" → Different subject entirely
    - "Advanced trigonometry" → Too different from available skills

    Write the mapping result into the 'mapping' field of the PipelineState JSON. Return ONLY PipelineState JSON.
    """

EXTRACT_STEPS_SYS = """
    Always preserve ALL existing fields from the input PipelineState JSON, copying them unchanged unless this stage updates them. 
    Use the numbered passages ([n] (id=...) Title\\nText) to extract teacher_action steps relevant to THIS question.
    Build up to 3 'formats' entries with: title, skill_name, format_number, steps[] (concise, deduped).
    Write them into 'extracted_formats' on PipelineState. Return ONLY PipelineState JSON.
    """

INSIGHTS_SYS = f"""
    You are a Direct Instruction pedagogy expert. Using 'extracted_formats' and 'pitfalls', produce EXACTLY 4 student-facing hints:
    - Each hint ≤ 80 characters
    - Hints must be sequential and build thinking without revealing the answer
    - Use student-facing verbs: Identify, Compare, Estimate, Check, Decide, Group, Label
    - Avoid explicit formulas unless essential to understanding; prefer conceptual prompts
    - Do NOT perform numeric computation, state intermediate values, or give the exact formula
    - Absolutely no final-answer leakage

    Return ONLY this JSON structure:
    {{
      "insights": ["hint 1", "hint 2", "hint 3"],
      "has_relevant_insights": true
    }}

    DIRECT INSTRUCTION PEDAGOGICAL INSIGHTS GUIDELINES:
    {DI_SCAFFOLDING_PRINCIPLES}
    """