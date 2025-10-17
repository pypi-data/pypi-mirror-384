"""
Enhanced Question Retriever with PostgreSQL Integration
Prioritizes UAE educational questions from Supabase database
Falls back to RAG when database doesn't have specific topics
"""

import os
import json
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class UAEQuestion:
    """Represents a question from UAE curriculum database"""
    id: int
    question_text: str
    answer: str
    subject: str
    grade: int
    topic: str
    difficulty: str
    language: str
    explanation: Optional[str] = None
    solution_steps: Optional[List[str]] = None
    uae_context: Optional[str] = None
    curriculum_alignment: Optional[str] = None
    similarity_score: Optional[float] = None

class EnhancedQuestionRetriever:
    """
    Enhanced retriever that prioritizes database questions over RAG
    
    Primary Source: UAE educational questions from PostgreSQL
    Fallback: RAG-based retrieval from sample questions
    """
    
    def __init__(self, POSTGRES_URI: str = None):
        """Initialize with database connection"""
        
        # Use environment variable if not provided
        self.POSTGRES_URI = POSTGRES_URI or os.getenv('POSTGRES_URI')
        if not self.POSTGRES_URI:
            logger.warning("No PostgreSQL URI provided, will use RAG only")
            self.db_available = False
        else:
            self.db_available = self._test_db_connection()
        
        # Initialize sentence transformer for similarity
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Cache for database questions
        self.question_cache = {}
        self.vector_indexes = {}
        
        # Load initial questions from database
        if self.db_available:
            self._load_database_questions()
    
    def _test_db_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = psycopg2.connect(self.POSTGRES_URI)
            conn.close()
            logger.info("✅ Successfully connected to UAE questions database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def _load_database_questions(self):
        """Load all questions from database into cache"""
        try:
            conn = psycopg2.connect(self.POSTGRES_URI)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Query the UAE educational questions table with correct column names
            query = """
            SELECT 
                id,
                question_text,
                correct_answer as answer,
                subject_area as subject,
                normalized_grade as grade,
                subtopic as topic,
                difficulty_level as difficulty,
                language,
                answer_explanation as explanation,
                prerequisite_concepts as solution_steps,
                textbook_name as uae_context,
                broad_topic as curriculum_alignment
            FROM uae_educational_questions_cleaned
            WHERE subject ILIKE '%math%' 
               OR subject_area IN ('Mathematics', 'Algebra', 'Geometry', 
                                  'Calculus', 'Statistics', 'Trigonometry', 
                                  'Arithmetic', 'Number Theory')
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Group questions by grade and topic
            for row in rows:
                grade = row.get('grade', 0)
                topic = row.get('topic', 'general').lower()
                
                if grade not in self.question_cache:
                    self.question_cache[grade] = {}
                
                if topic not in self.question_cache[grade]:
                    self.question_cache[grade][topic] = []
                
                # Parse solution steps if stored as JSON
                solution_steps = row.get('solution_steps', [])
                if isinstance(solution_steps, str):
                    try:
                        solution_steps = json.loads(solution_steps)
                    except:
                        solution_steps = [solution_steps]
                
                question = UAEQuestion(
                    id=row['id'],
                    question_text=row['question_text'],
                    answer=row['answer'],
                    subject=row.get('subject', 'mathematics'),
                    grade=grade,
                    topic=topic,
                    difficulty=row.get('difficulty', 'medium'),
                    language=row.get('language', 'arabic'),
                    explanation=row.get('explanation'),
                    solution_steps=solution_steps,
                    uae_context=row.get('uae_context'),
                    curriculum_alignment=row.get('curriculum_alignment')
                )
                
                self.question_cache[grade][topic].append(question)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Loaded {len(rows)} questions from database")
            
            # Build vector indexes for each grade
            self._build_vector_indexes()
            
        except Exception as e:
            logger.error(f"Error loading database questions: {e}")
            self.db_available = False
    
    def _build_vector_indexes(self):
        """Build FAISS indexes for similarity search"""
        
        for grade, topics in self.question_cache.items():
            all_questions = []
            all_texts = []
            
            for topic, questions in topics.items():
                for q in questions:
                    all_questions.append(q)
                    all_texts.append(q.question_text)
            
            if all_texts:
                # Create embeddings
                embeddings = self.encoder.encode(all_texts)
                
                # Build FAISS index
                dimension = embeddings.shape[1]
                index = faiss.IndexFlatIP(dimension)
                
                # Normalize for cosine similarity
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                index.add(embeddings.astype(np.float32))
                
                self.vector_indexes[grade] = {
                    'index': index,
                    'questions': all_questions
                }
                
                logger.info(f"Built vector index for grade {grade} with {len(all_questions)} questions")
    
    def get_questions_for_topic(
        self,
        grade: int,
        topic: str,
        difficulty: str = None,
        language: str = "arabic",
        limit: int = 10
    ) -> List[UAEQuestion]:
        """
        Get questions for a specific topic from database
        
        Priority:
        1. Exact topic match from database
        2. Similar questions from database using vector search
        3. Fallback to RAG if needed
        """
        
        questions = []
        
        # Try database first
        if self.db_available and grade in self.question_cache:
            # Exact topic match
            if topic.lower() in self.question_cache[grade]:
                topic_questions = self.question_cache[grade][topic.lower()]
                
                # Filter by difficulty and language if specified
                filtered = []
                for q in topic_questions:
                    if difficulty and q.difficulty != difficulty:
                        continue
                    if language and q.language != language:
                        continue
                    filtered.append(q)
                
                questions.extend(filtered[:limit])
            
            # If not enough questions, use vector similarity
            if len(questions) < limit and grade in self.vector_indexes:
                similar = self._find_similar_questions(
                    query=f"Grade {grade} {topic} {difficulty or 'medium'} question",
                    grade=grade,
                    limit=limit - len(questions)
                )
                questions.extend(similar)
        
        return questions[:limit]
    
    def _find_similar_questions(
        self,
        query: str,
        grade: int,
        limit: int = 5
    ) -> List[UAEQuestion]:
        """Find similar questions using vector search"""
        
        if grade not in self.vector_indexes:
            return []
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        
        # Search
        index_data = self.vector_indexes[grade]
        index = index_data['index']
        all_questions = index_data['questions']
        
        k = min(len(all_questions), limit * 2)  # Get more candidates
        similarities, indices = index.search(query_embedding.astype(np.float32), k)
        
        # Return top matches with similarity scores
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx < len(all_questions):
                question = all_questions[idx]
                question.similarity_score = float(sim)
                results.append(question)
        
        return results[:limit]
    
    def get_all_topics_for_grade(self, grade: int) -> List[str]:
        """Get all available topics for a grade"""
        
        topics = set()
        
        if self.db_available and grade in self.question_cache:
            topics.update(self.question_cache[grade].keys())
        
        # Add standard topics from curriculum
        grade_topics = {
            1: ["counting", "addition_subtraction_10", "shapes", "patterns"],
            2: ["addition_subtraction_100", "skip_counting", "time", "money"],
            3: ["multiplication_facts", "division_basics", "fractions_intro"],
            4: ["multi_digit_multiplication", "fractions_basic", "geometry_angles"],
            5: ["decimals_operations", "fractions_advanced", "volume"],
            6: ["ratios_intro", "basic_algebra", "geometry_basics"],
            7: ["integers", "basic_algebra", "probability"],
            8: ["linear_equations", "statistics", "pythagorean_theorem"],
            9: ["quadratic_equations", "trigonometry_basics", "coordinate_geometry"],
            10: ["quadratic_functions", "trigonometry", "probability"],
            11: ["advanced_functions", "sequences_series", "calculus_intro"],
            12: ["calculus", "complex_numbers", "statistics"]
        }
        
        if grade in grade_topics:
            topics.update(grade_topics[grade])
        
        return sorted(list(topics))
    
    def execute_custom_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute custom SQL query on database"""
        
        if not self.db_available:
            return []
        
        try:
            conn = psycopg2.connect(self.POSTGRES_URI)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about available questions"""
        
        stats = {
            "database_available": self.db_available,
            "total_questions": 0,
            "questions_by_grade": {},
            "questions_by_topic": {},
            "coverage_matrix": {}
        }
        
        if self.db_available:
            for grade, topics in self.question_cache.items():
                grade_total = 0
                grade_topics = {}
                
                for topic, questions in topics.items():
                    count = len(questions)
                    grade_total += count
                    grade_topics[topic] = count
                    
                    if topic not in stats["questions_by_topic"]:
                        stats["questions_by_topic"][topic] = 0
                    stats["questions_by_topic"][topic] += count
                
                stats["questions_by_grade"][grade] = grade_total
                stats["coverage_matrix"][grade] = grade_topics
                stats["total_questions"] += grade_total
        
        return stats