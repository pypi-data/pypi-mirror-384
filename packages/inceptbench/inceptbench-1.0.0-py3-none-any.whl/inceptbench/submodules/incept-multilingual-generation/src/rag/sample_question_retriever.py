import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import psycopg2
import os

logger = logging.getLogger(__name__)

@dataclass
class SampleQuestion:
    """Represents a sample question retrieved from textbooks/curriculum."""
    question_text: str
    subject: str
    grade: int
    topic: str
    difficulty: str
    language: str
    answer: Optional[str] = None
    explanation: Optional[str] = None
    source: Optional[str] = None
    similarity_score: Optional[float] = None

class SampleQuestionRetriever:
    """
    RAG-based sample question retriever for educational content.
    
    Retrieves 100-200 sample questions per topic from textbooks and curriculum materials
    to serve as foundation for HRM-based question generation.
    
    Key Features:
    - Fast vector-based similarity search
    - Subject-specific vector indexes
    - Grade and difficulty filtering
    - UAE curriculum alignment
    """
    
    def __init__(self, POSTGRES_URI: str = os.getenv('POSTGRES_URI')):
        self.POSTGRES_URI = POSTGRES_URI
        
        # Lazy initialization - only load when needed for similarity search
        self.encoder = None
        
        # Subject-specific indexes for fast retrieval
        self.subject_indexes = {}
        self.subject_questions = {}
        
        # Don't build vector indexes on init - too slow
        # Questions are loaded directly from PostgreSQL as needed
    
    def _load_sample_questions(self):
        """Load sample questions from JSON files."""
        logger.info("Loading sample questions from textbooks...")
        
        # Load from different subject files
        subjects = ["arithmetic", "algebra", "geometry", "calculus", "statistics", "trigonometry", "quadratic equations"]
        
        for subject in subjects:
            subject_file = self.data_dir / f"{subject}_samples.json"
            
            if subject_file.exists():
                with open(subject_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                    self.subject_questions[subject] = [
                        SampleQuestion(**q) for q in questions_data
                    ]
                    logger.info(f"Loaded {len(self.subject_questions[subject])} sample questions for {subject}")
            else:
                # Create sample data for demonstration
                self.subject_questions[subject] = self._create_sample_data(subject)
                self._save_sample_data(subject)
    
    def _create_sample_data(self, subject: str) -> List[SampleQuestion]:
        """Create sample question data for a subject (placeholder implementation)."""
        
        # Add more subject mappings for better coverage
        sample_questions = {
            "arithmetic": [
                SampleQuestion(
                    question_text="احسب: 15 + 23 = ؟",
                    subject="arithmetic",
                    grade=2,
                    topic="addition",
                    difficulty="easy",
                    language="arabic",
                    answer="38",
                    explanation="نجمع الآحاد: 5 + 3 = 8، ثم العشرات: 1 + 2 = 3، فالناتج 38",
                    source="UAE Grade 2 Mathematics Textbook"
                ),
                SampleQuestion(
                    question_text="إذا كان مع أحمد 45 درهماً واشترى لعبة بـ 18 درهماً، كم درهماً تبقى معه؟",
                    subject="arithmetic", 
                    grade=3,
                    topic="subtraction_word_problems",
                    difficulty="medium",
                    language="arabic",
                    answer="27 درهماً",
                    explanation="المبلغ المتبقي = 45 - 18 = 27 درهماً",
                    source="UAE Grade 3 Mathematics Curriculum"
                )
            ],
            "algebra": [
                SampleQuestion(
                    question_text="حل المعادلة: 2x + 5 = 13",
                    subject="algebra",
                    grade=8,
                    topic="linear_equations",
                    difficulty="medium", 
                    language="arabic",
                    answer="x = 4",
                    explanation="2x = 13 - 5 = 8، إذن x = 8 ÷ 2 = 4",
                    source="UAE Grade 8 Algebra Textbook"
                )
            ],
            "geometry": [
                SampleQuestion(
                    question_text="أوجد مساحة المستطيل الذي طوله 8 سم وعرضه 5 سم",
                    subject="geometry",
                    grade=4,
                    topic="area_rectangle", 
                    difficulty="easy",
                    language="arabic",
                    answer="40 سم²",
                    explanation="مساحة المستطيل = الطول × العرض = 8 × 5 = 40 سم²",
                    source="UAE Grade 4 Geometry Unit"
                )
            ],
            "quadratic equations": [
                SampleQuestion(
                    question_text="حل المعادلة التربيعية: x² - 5x + 6 = 0",
                    subject="quadratic equations",
                    grade=10,
                    topic="quadratic_equations",
                    difficulty="medium",
                    language="arabic",
                    answer="x = 2 أو x = 3",
                    explanation="نستخدم التحليل: (x-2)(x-3) = 0، إذن x = 2 أو x = 3",
                    source="UAE Grade 10 Algebra Textbook"
                ),
                SampleQuestion(
                    question_text="أوجد الجذور للمعادلة: 2x² + 7x - 4 = 0",
                    subject="quadratic equations", 
                    grade=11,
                    topic="quadratic_formula",
                    difficulty="hard",
                    language="arabic",
                    answer="x = 0.5 أو x = -4",
                    explanation="نستخدم القانون العام: x = (-b ± √(b²-4ac)) / 2a",
                    source="UAE Grade 11 Advanced Mathematics"
                )
            ]
        }
        
        # Return sample questions for the subject or empty list
        return sample_questions.get(subject, [])
    
    def _save_sample_data(self, subject: str):
        """Save sample questions to JSON file."""
        if subject in self.subject_questions:
            subject_file = self.data_dir / f"{subject}_samples.json"
            questions_data = [
                {
                    "question_text": q.question_text,
                    "subject": q.subject,
                    "grade": q.grade,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "language": q.language,
                    "answer": q.answer,
                    "explanation": q.explanation,
                    "source": q.source
                }
                for q in self.subject_questions[subject]
            ]
            
            with open(subject_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, ensure_ascii=False, indent=2)
    
    def _build_vector_indexes(self):
        """Build FAISS vector indexes for fast similarity search."""
        logger.info("Building vector indexes for sample questions...")
        
        for subject, questions in self.subject_questions.items():
            if not questions:
                continue
            
            # Create embeddings for all questions
            question_texts = [q.question_text for q in questions]
            embeddings = self.encoder.encode(question_texts)
            
            # Build FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            index.add(embeddings.astype(np.float32))
            
            self.subject_indexes[subject] = index
            logger.info(f"Built vector index for {subject} with {len(questions)} questions")
    
    def _ensure_encoder_loaded(self):
        """Lazy load the sentence transformer encoder."""
        if self.encoder is None:
            logger.info("Loading sentence transformer for similarity search...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _ensure_indexes_built(self):
        """Lazy build vector indexes if not already built."""
        if not self.subject_indexes:
            self._ensure_encoder_loaded()
            self._build_vector_indexes()

    def retrieve_similar_questions(
        self,
        query: str,
        subject: str,
        grade: int,
        quantity: int = 5,
        difficulty: Optional[str] = None,
        language: str = "arabic"
    ) -> List[SampleQuestion]:
        """
        Retrieve similar sample questions based on query.
        
        Args:
            query: Search query describing desired question type
            subject: Mathematics subject (arithmetic, algebra, etc.)
            grade: Grade level (1-12)
            quantity: Number of similar questions to retrieve
            difficulty: Optional difficulty filter
            language: Preferred language
            
        Returns:
            List of similar sample questions with similarity scores
        """
        
        # Ensure indexes are built (lazy initialization)
        self._ensure_indexes_built()
        
        if subject not in self.subject_indexes:
            logger.warning(f"No sample questions available for subject: {subject}")
            return []
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search in subject-specific index
        index = self.subject_indexes[subject]
        questions = self.subject_questions[subject]
        
        # Get more candidates than needed for filtering
        k = min(len(questions), quantity * 3)
        similarities, indices = index.search(query_embedding.astype(np.float32), k)
        
        # Filter and rank results
        filtered_results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            question = questions[idx]
            
            # Apply filters
            if abs(question.grade - grade) > 2:  # Allow ±2 grade levels
                continue
            
            if difficulty and question.difficulty != difficulty:
                continue
            
            if language and question.language != language:
                continue
            
            # Add similarity score
            question.similarity_score = float(similarity)
            filtered_results.append(question)
            
            if len(filtered_results) >= quantity:
                break
        
        logger.info(f"Retrieved {len(filtered_results)} similar questions for query: {query[:50]}...")
        return filtered_results
    
    def get_topic_questions(
        self,
        subject: str,
        topic: str,
        grade: int,
        max_questions: int = 200
    ) -> List[SampleQuestion]:
        """
        Get all sample questions for a specific topic.
        
        Retrieves 100-200 questions per topic as mentioned in transcript.
        """
        
        if subject not in self.subject_questions:
            return []
        
        topic_questions = [
            q for q in self.subject_questions[subject]
            if q.topic == topic and abs(q.grade - grade) <= 1
        ]
        
        return topic_questions[:max_questions]
    
    def add_sample_questions(self, questions: List[Dict[str, Any]], subject: str):
        """Add new sample questions to the database."""
        
        if subject not in self.subject_questions:
            self.subject_questions[subject] = []
        
        for q_data in questions:
            question = SampleQuestion(**q_data)
            self.subject_questions[subject].append(question)
        
        # Rebuild index for this subject
        self._build_subject_index(subject)
        self._save_sample_data(subject)
        
        logger.info(f"Added {len(questions)} questions to {subject}")
    
    def _build_subject_index(self, subject: str):
        """Rebuild vector index for a specific subject."""
        questions = self.subject_questions[subject]
        if not questions:
            return
        
        question_texts = [q.question_text for q in questions]
        embeddings = self.encoder.encode(question_texts)
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        index.add(embeddings.astype(np.float32))
        
        self.subject_indexes[subject] = index
    
    def retrieve_sample_questions(
        self,
        grade: int,
        subject: str,
        limit: int = 3
    ) -> List[SampleQuestion]:
        """
        Retrieve sample questions from PostgreSQL database by grade and subject.
        Used by simple_question_generator for fast question generation.
        """
        try:
            conn = psycopg2.connect(self.POSTGRES_URI)
            cur = conn.cursor()
            
            # Query for questions with flexible subject matching and grade range
            query = """
                SELECT question_text, question_text_arabic, subject_area, normalized_grade, 
                       broad_topic, subtopic, difficulty_level, correct_answer, answer_explanation, language
                FROM uae_educational_questions_cleaned 
                WHERE (subject_area ILIKE %s OR broad_topic ILIKE %s OR subtopic ILIKE %s)
                  AND normalized_grade BETWEEN %s AND %s
                  AND question_text IS NOT NULL
                ORDER BY RANDOM()
                LIMIT %s
            """
            
            # Allow ±2 grade levels and flexible subject matching
            grade_min = max(1, grade - 2)
            grade_max = min(12, grade + 2)
            subject_pattern = f"%{subject}%"
            
            cur.execute(query, (subject_pattern, subject_pattern, subject_pattern, grade_min, grade_max, limit))
            rows = cur.fetchall()
            
            questions = []
            for row in rows:
                (question_text, question_text_arabic, subject_area, norm_grade, 
                 broad_topic, subtopic, difficulty_level, correct_answer, answer_explanation, language) = row
                
                # Use Arabic text if available, otherwise English
                text_to_use = question_text_arabic if question_text_arabic else question_text
                
                question = SampleQuestion(
                    question_text=text_to_use,
                    subject=subject_area or subject,
                    grade=norm_grade or grade,
                    topic=subtopic or broad_topic or "general",
                    difficulty=difficulty_level or "medium",
                    language=language or "arabic",
                    answer=correct_answer,
                    explanation=answer_explanation,
                    source="UAE Educational Questions Database"
                )
                questions.append(question)
            
            cur.close()
            conn.close()
            
            logger.info(f"Retrieved {len(questions)} sample questions from database for {subject}, grade {grade}")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to retrieve sample questions from database: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded sample questions."""
        stats = {
            "total_questions": sum(len(questions) for questions in self.subject_questions.values()),
            "subjects": list(self.subject_questions.keys()),
            "questions_per_subject": {
                subject: len(questions) 
                for subject, questions in self.subject_questions.items()
            }
        }
        return stats