from typing import Dict, Any

QUESTION_EVAL_RUBRIC: Dict[str, Any] = {
    "rubric_version": "0.1.0",
    "total_points": 100,
    "criteria": [
        {
            "id": "content_quality_relevance",
            "name": "Content Quality & Relevance",
            "weight": 15,
            "scale": {
                0: "Off-skill or unclear; not grade-appropriate.",
                1: "Partially aligned; notable clarity/grade issues.",
                2: "Mostly aligned; minor clarity/grade issues.",
                3: "Clearly aligned; appropriate language; minimal issues.",
                4: "Crystal-clear, tightly aligned; no issues."
            },
            "checks": [
                "targets_intended_skill",
                "grade_appropriate_language_only",
                "concise_no_eduspeak",
                "factual_accuracy"
            ]
        },
        {
            "id": "structure_format",
            "name": "Structure & Format (DI Non-Interactive)",
            "weight": 15,
            "applies_if": "kind == 'article'",
            "scale": {
                0: "Missing DI flow; redundant/confusing sections.",
                1: "DI flow weak; redundancy present.",
                2: "Basic DI flow; some extra sections/ambiguity.",
                3: "Good DI flow: Purpose → HowTo → Examples; minimal redundancy.",
                4: "Exemplary DI flow; no redundant sections; formatting aids cognition."
            },
            "checks": [
                "purpose_concrete_example_before_rules",
                "how_to_solve_steps_grade_appropriate",
                "worked_examples_cover_easy_med_hard",
                "no_hints_misc_sections_no_negative_examples_no_nonworked_examples"
            ]
        },
        {
            "id": "article_length_cognitive_load",
            "name": "Article Length & Cognitive Load",
            "weight": 10,
            "applies_if": "kind == 'article'",
            "scale": {
                0: "Exceeds 2-min ceiling; adds load.",
                1: "Near ceiling with extra load.",
                2: "At/under ceiling with some load issues.",
                3: "Comfortably under ceiling; minimal load.",
                4: "Optimally concise; focused; minimal load."
            },
            "checks": [
                "under_two_min_grade_reader",
                "no_unnecessary_padding",
                "80_20_rule_examples_to_explanation"
            ]
        },
        {
            "id": "worked_examples_quality",
            "name": "Worked Examples Quality",
            "weight": 20,
            "applies_if": "kind == 'article'",
            "scale": {
                0: "Too few/too many; missing coverage; steps unclear.",
                1: "Coverage weak; steps not memory-friendly.",
                2: "Adequate but uneven; some redundancy.",
                3: "Covers needed cases; steps clear and economical.",
                4: "Covers all cases; steps optimized for working memory; no redundancy."
            },
            "checks": [
                "concrete_before_abstract",
                "covers_cases_for_practice",
                "steps_breakdown_memory_limits",
                "no_redundant_examples"
            ]
        },
        {
            "id": "answers_distractors",
            "name": "Answers & Distractors (MCQ)",
            "weight": 15,
            "applies_if": "kind == 'question' && type == 'mcq'",
            "scale": {
                0: "Correct answer unclear; distractors random.",
                1: "Correct answer clear; distractors mostly irrelevant.",
                2: "Half of distractors map to misconceptions.",
                3: "Most distractors plausible & diagnostic.",
                4: "All distractors purposeful, distinct, map to specific misconceptions."
            },
            "checks": [
                "correct_answer_unique",
                "distractors_plausible",
                "distractors_map_common_errors",
                "no_pattern_bias"
            ]
        },
        {
            "id": "explanations_rationales",
            "name": "Explanations & Rationales",
            "weight": 10,
            "applies_if": "kind == 'question'",
            "scale": {
                0: "No explanation or only states answer.",
                1: "Minimal explanation; ignores distractors.",
                2: "Explains correct answer; weak distractor coverage.",
                3: "Explains correct & most distractors clearly.",
                4: "Concise, complete; explains all distractors."
            },
            "checks": [
                "explains_correct_answer",
                "addresses_each_distractor_if_mcq",
                "concise_grade_level_appropriate"
            ]
        },
        {
            "id": "progressive_hints",
            "name": "Step-wise Hints / Progressive Reveal",
            "weight": 10,
            "applies_if": "kind == 'question' && hints_present",
            "scale": {
                0: "Hints absent or reveal answer early.",
                1: "Hints present but too vague/revealing.",
                2: "Progress present; one step too revealing.",
                3: "Clear progression; full solution only at last step.",
                4: "Exemplary scaffolding; minimal-first; increasing specificity; answer last."
            },
            "checks": [
                "increasing_specificity",
                "final_answer_only_in_last_step",
                "hint_titles_as_nudges"
            ]
        },
        {
            "id": "difficulty_calibration",
            "name": "Difficulty Calibration",
            "weight": 10,
            "applies_if": "kind == 'question'",
            "scale": {
                0: "Configured difficulty mismatches time & accuracy.",
                1: "Large mismatch on time or accuracy.",
                2: "Minor mismatch on one dimension.",
                3: "Both within tolerance.",
                4: "Centered within target bands."
            },
            "checks": ["time_within_band", "accuracy_within_band"],
            "bands": {
                "easy":   {"target_avg_time_s": 30,  "time_tolerance_pct": 0.50, "accuracy_target_pct": 85, "accuracy_tolerance_pct": 0.10},
                "medium": {"target_avg_time_s": 60,  "time_tolerance_pct": 0.40, "accuracy_target_pct": 65, "accuracy_tolerance_pct": 0.12},
                "hard":   {"target_avg_time_s": 120, "time_tolerance_pct": 0.35, "accuracy_target_pct": 40, "accuracy_tolerance_pct": 0.15}
            }
        },
        {
            "id": "learning_value_alignment",
            "name": "Learning Value & Alignment",
            "weight": 10,
            "scale": {
                0: "Does not reinforce target concept.",
                1: "Weak alignment; extraneous load.",
                2: "Mostly aligned; some extra load.",
                3: "Well aligned; focused on concept.",
                4: "Tightly aligned; every element serves goal."
            },
            "checks": ["reinforces_target_concept", "avoids_unnecessary_cognitive_load", "consistent_vocab_across_lessons"]
        },
        {
            "id": "coherence_presentation",
            "name": "Coherence & Presentation",
            "weight": 5,
            "scale": {
                0: "Disorganized; contradictions; formatting issues.",
                1: "Some organizational issues.",
                2: "Mostly coherent; minor flaws.",
                3: "Clear flow; no contradictions.",
                4: "Polished; student-friendly."
            },
            "checks": ["no_contradictions", "clear_formatting_language"]
        }
    ]
}