#!/usr/bin/env python3
"""
Subject Manager: Subject-agnostic curriculum management for UAE educational system.
Supports all subjects: Mathematics, Science, English, Arabic, Social Studies, Islamic Studies, etc.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class UAESubject(str, Enum):
    """UAE Curriculum Subjects"""
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    ARABIC = "arabic"
    SOCIAL_STUDIES = "social_studies"
    ISLAMIC_STUDIES = "islamic_studies"
    PHYSICAL_EDUCATION = "physical_education"
    ART = "art"
    MUSIC = "music"
    COMPUTER_SCIENCE = "computer_science"
    
@dataclass
class SubjectCurriculum:
    """Subject-specific curriculum configuration"""
    subject: str
    grade_range: Tuple[int, int]  # (min_grade, max_grade)
    key_concepts: List[str]
    assessment_types: List[str]
    question_formats: List[str]
    difficulty_levels: List[str]
    
@dataclass
class GradeLevel:
    """Grade-level requirements across all subjects"""
    grade: int
    cognitive_level: str  # concrete, formal_concrete, formal_abstract, formal_expert
    reasoning_complexity: float
    attention_span_minutes: int
    vocabulary_level: str

class SubjectManager:
    """
    Manages curriculum requirements across all UAE subjects and grade levels.
    Provides subject-agnostic interface for question generation.
    """
    
    # UAE Grade Level Cognitive Development
    GRADE_COGNITIVE_LEVELS = {
        1: GradeLevel(1, "concrete", 1.0, 15, "basic"),
        2: GradeLevel(2, "concrete", 1.1, 20, "basic"),
        3: GradeLevel(3, "concrete", 1.2, 25, "elementary"),
        4: GradeLevel(4, "concrete", 1.3, 30, "elementary"),
        5: GradeLevel(5, "formal_concrete", 1.5, 35, "elementary"),
        6: GradeLevel(6, "formal_concrete", 1.7, 40, "intermediate"),
        7: GradeLevel(7, "formal_concrete", 2.0, 45, "intermediate"),
        8: GradeLevel(8, "formal_abstract", 2.3, 45, "intermediate"),
        9: GradeLevel(9, "formal_abstract", 2.6, 50, "advanced"),
        10: GradeLevel(10, "formal_abstract", 2.9, 50, "advanced"),
        11: GradeLevel(11, "formal_expert", 3.2, 55, "advanced"),
        12: GradeLevel(12, "formal_expert", 3.5, 60, "expert")
    }
    
    # Subject-Specific Curriculum Definitions
    SUBJECT_CURRICULA = {
        UAESubject.MATHEMATICS: SubjectCurriculum(
            subject="mathematics",
            grade_range=(1, 12),
            key_concepts=["number_sense", "algebra", "geometry", "statistics", "probability", "calculus"],
            assessment_types=["problem_solving", "calculation", "proof", "application"],
            question_formats=["multiple_choice", "short_answer", "worked_solution", "explanation"],
            difficulty_levels=["basic", "intermediate", "advanced", "expert"]
        ),
        
        UAESubject.SCIENCE: SubjectCurriculum(
            subject="science",
            grade_range=(1, 12),
            key_concepts=["physics", "chemistry", "biology", "earth_science", "scientific_method"],
            assessment_types=["experiment_design", "data_analysis", "concept_explanation", "application"],
            question_formats=["multiple_choice", "diagram_analysis", "experiment_description", "hypothesis"],
            difficulty_levels=["observation", "analysis", "synthesis", "evaluation"]
        ),
        
        UAESubject.ENGLISH: SubjectCurriculum(
            subject="english",
            grade_range=(1, 12),
            key_concepts=["reading_comprehension", "writing", "speaking", "listening", "grammar", "vocabulary"],
            assessment_types=["comprehension", "composition", "grammar_usage", "vocabulary"],
            question_formats=["multiple_choice", "essay", "short_response", "analysis"],
            difficulty_levels=["literal", "inferential", "critical", "creative"]
        ),
        
        UAESubject.ARABIC: SubjectCurriculum(
            subject="arabic",
            grade_range=(1, 12),
            key_concepts=["reading", "writing", "grammar", "literature", "poetry", "rhetoric"],
            assessment_types=["comprehension", "composition", "grammar", "literary_analysis"],
            question_formats=["multiple_choice", "essay", "translation", "analysis"],
            difficulty_levels=["basic", "intermediate", "advanced", "mastery"]
        ),
        
        UAESubject.SOCIAL_STUDIES: SubjectCurriculum(
            subject="social_studies",
            grade_range=(1, 12),
            key_concepts=["history", "geography", "civics", "economics", "culture", "uae_heritage"],
            assessment_types=["factual_recall", "analysis", "comparison", "evaluation"],
            question_formats=["multiple_choice", "essay", "map_analysis", "timeline"],
            difficulty_levels=["knowledge", "comprehension", "application", "analysis"]
        ),
        
        UAESubject.ISLAMIC_STUDIES: SubjectCurriculum(
            subject="islamic_studies",
            grade_range=(1, 12),
            key_concepts=["quran", "hadith", "fiqh", "aqeedah", "seerah", "islamic_values"],
            assessment_types=["recitation", "interpretation", "application", "reflection"],
            question_formats=["multiple_choice", "short_answer", "reflection", "application"],
            difficulty_levels=["memorization", "understanding", "application", "reflection"]
        )
    }
    
    def __init__(self):
        logger.info("SubjectManager initialized for UAE curriculum subjects")
    
    def get_subject_curriculum(self, subject: str) -> SubjectCurriculum:
        """Get curriculum configuration for a subject"""
        subject_enum = UAESubject(subject.lower())
        return self.SUBJECT_CURRICULA.get(subject_enum)
    
    def get_grade_level(self, grade: int) -> GradeLevel:
        """Get cognitive and developmental requirements for a grade level"""
        return self.GRADE_COGNITIVE_LEVELS.get(grade, self.GRADE_COGNITIVE_LEVELS[12])
    
    def is_subject_grade_valid(self, subject: str, grade: int) -> bool:
        """Check if a subject is taught at a specific grade level"""
        curriculum = self.get_subject_curriculum(subject)
        if not curriculum:
            return False
        min_grade, max_grade = curriculum.grade_range
        return min_grade <= grade <= max_grade
    
    def get_appropriate_difficulty(self, subject: str, grade: int) -> str:
        """Get appropriate difficulty level for subject and grade"""
        curriculum = self.get_subject_curriculum(subject)
        grade_level = self.get_grade_level(grade)
        
        if not curriculum:
            return "intermediate"
        
        # Map cognitive level to subject difficulty
        if grade <= 4:
            return curriculum.difficulty_levels[0]  # Basic level
        elif grade <= 8:
            return curriculum.difficulty_levels[1]  # Intermediate level
        elif grade <= 10:
            return curriculum.difficulty_levels[2]  # Advanced level
        else:
            return curriculum.difficulty_levels[3]  # Expert level
    
    def get_mathematics_domains_for_grade(self, grade: int) -> List[str]:
        """Get grade-appropriate mathematics domains to prevent complexity mismatch"""
        # UAE Mathematics Curriculum - Grade-specific domains
        grade_domains = {
            1: ["counting", "basic_addition", "basic_subtraction", "shapes"],
            2: ["addition", "subtraction", "basic_multiplication", "place_value", "simple_geometry"],
            3: ["multiplication", "division", "fractions_basic", "measurement", "geometry_2d"],
            4: ["multiplication_tables", "long_division", "fractions", "decimals_basic", "area_perimeter"],
            5: ["decimals", "fractions_advanced", "percentages_basic", "geometry_3d", "data_handling"],
            6: ["ratios", "proportions", "percentages", "integers", "coordinate_geometry"],
            7: ["algebra_basic", "linear_equations_simple", "geometry_angles", "statistics_basic"],
            8: ["algebra_intermediate", "linear_equations", "geometry_advanced", "statistics"],
            9: ["algebra_advanced", "quadratic_equations", "trigonometry_basic", "probability"],
            10: ["trigonometry", "coordinate_geometry_advanced", "sequences_series", "statistics_advanced"],
            11: ["pre_calculus", "functions", "logarithms", "trigonometry_advanced"],
            12: ["calculus", "derivatives", "integrals", "advanced_functions"]
        }
        
        return grade_domains.get(grade, ["arithmetic"])  # Default to basic arithmetic
    
    def is_domain_appropriate_for_grade(self, domain: str, grade: int) -> bool:
        """Check if a mathematical domain is appropriate for a grade level"""
        appropriate_domains = self.get_mathematics_domains_for_grade(grade)
        return domain.lower() in [d.lower() for d in appropriate_domains]
    
    def get_question_formats(self, subject: str) -> List[str]:
        """Get appropriate question formats for a subject"""
        curriculum = self.get_subject_curriculum(subject)
        return curriculum.question_formats if curriculum else ["multiple_choice", "short_answer"]
    
    def get_assessment_types(self, subject: str) -> List[str]:
        """Get appropriate assessment types for a subject"""
        curriculum = self.get_subject_curriculum(subject)
        return curriculum.assessment_types if curriculum else ["knowledge", "application"]
    
    def detect_subject_from_text(self, text: str, instructions: str = "") -> str:
        """Detect subject from question text and instructions using keywords"""
        text_combined = f"{text} {instructions}".lower()
        
        # Subject detection keywords
        subject_keywords = {
            "mathematics": ["math", "calculate", "equation", "solve", "number", "algebra", "geometry", 
                          "trigonometry", "calculus", "statistics", "probability", "derivative", "integral"],
            "science": ["experiment", "hypothesis", "theory", "physics", "chemistry", "biology", 
                       "molecule", "atom", "cell", "ecosystem", "force", "energy", "reaction"],
            "english": ["reading", "writing", "grammar", "vocabulary", "literature", "essay", 
                       "comprehension", "sentence", "paragraph", "author"],
            "arabic": ["arabic", "عربي", "قراءة", "كتابة", "نحو", "أدب", "شعر"],
            "social_studies": ["history", "geography", "civics", "culture", "society", "government", 
                             "economy", "uae", "heritage", "tradition"],
            "islamic_studies": ["islam", "quran", "hadith", "prophet", "islamic", "muslim", 
                              "prayer", "fasting", "pilgrimage"]
        }
        
        # Count keyword matches for each subject
        subject_scores = {}
        for subject, keywords in subject_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_combined)
            if score > 0:
                subject_scores[subject] = score
        
        # Return subject with highest score
        if subject_scores:
            return max(subject_scores, key=subject_scores.get)
        
        # Default fallback
        return "mathematics"
    
    def get_supported_subjects(self) -> List[str]:
        """Get list of all supported subjects"""
        return [subject.value for subject in UAESubject]
    
    def validate_skill_context(self, subject: str, skill_title: str, unit_name: str) -> Dict[str, Any]:
        """Validate and enrich skill context for subject appropriateness"""
        curriculum = self.get_subject_curriculum(subject)
        
        validation_result = {
            "valid": curriculum is not None,
            "subject": subject,
            "skill_title": skill_title,
            "unit_name": unit_name,
            "enriched_context": {},
            "warnings": []
        }
        
        if curriculum:
            validation_result["enriched_context"] = {
                "key_concepts": curriculum.key_concepts,
                "assessment_types": curriculum.assessment_types,
                "question_formats": curriculum.question_formats,
                "difficulty_levels": curriculum.difficulty_levels
            }
        else:
            validation_result["warnings"].append(f"Subject '{subject}' not in UAE curriculum database")
        
        return validation_result