import csv
import os
from typing import Dict, Set, Tuple, Optional
from uuid import UUID
from src.db.postgres_client import postgres_client
from dotenv import load_dotenv

load_dotenv()

class UAECurriculumIngesterPSQL:
    def __init__(self):
        self.postgres = postgres_client
        self.cache = {
            'grades': {},
            'topics': {},
            'chapters': {},
            'subtopics': {}
        }
        
    def setup_base_data(self):
        """Setup initial data for countries, education systems, subjects, etc."""
        
        # Insert UAE country
        uae_country_query = """
            INSERT INTO countries (code, name)
            VALUES ('UAE', 'United Arab Emirates')
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id, code, name
        """
        uae_country = self.postgres.execute_query(uae_country_query)
        
        # Insert UAE MOE education system
        uae_moe_query = """
            INSERT INTO education_systems (code, name, description)
            VALUES ('UAE_MOE', 'UAE Ministry of Education', 'United Arab Emirates Ministry of Education Curriculum')
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
            RETURNING id, code, name
        """
        uae_moe = self.postgres.execute_query(uae_moe_query)
        
        # Insert Mathematics subject
        math_subject_query = """
            INSERT INTO subjects (code, name, description)
            VALUES ('MATH', 'Mathematics', 'Mathematics curriculum')
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
            RETURNING id, code, name
        """
        math_subject = self.postgres.execute_query(math_subject_query)
        
        # Insert English language
        english_lang_query = """
            INSERT INTO languages (code, name)
            VALUES ('EN', 'English')
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
            RETURNING id, code, name
        """
        english_lang = self.postgres.execute_query(english_lang_query)
        
        # Insert question type for example questions
        example_qt_query = """
            INSERT INTO question_types (code, name, description)
            VALUES ('EXAMPLE', 'Example Question', 'Example questions from curriculum')
            ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
            RETURNING id, code, name
        """
        example_qt = self.postgres.execute_query(example_qt_query)
        
        # Debug logging
        print(f"UAE Country result: {uae_country}")
        print(f"UAE MOE result: {uae_moe}")
        
        # Link country to education system
        if uae_country['success'] and uae_moe['success']:
            # Check if we have data in the response
            if 'data' in uae_country and uae_country['data']:
                country_id = uae_country['data'][0]['id']
            else:
                # Try alternative: run a SELECT query to get the ID
                country_result = self.postgres.execute_query("SELECT id FROM countries WHERE code = 'UAE'")
                if country_result['success'] and country_result['data']:
                    country_id = country_result['data'][0]['id']
                else:
                    print("Error: Could not get country ID")
                    return {}
            
            if 'data' in uae_moe and uae_moe['data']:
                education_system_id = uae_moe['data'][0]['id']
            else:
                # Try alternative: run a SELECT query to get the ID
                moe_result = self.postgres.execute_query("SELECT id FROM education_systems WHERE code = 'UAE_MOE'")
                if moe_result['success'] and moe_result['data']:
                    education_system_id = moe_result['data'][0]['id']
                else:
                    print("Error: Could not get education system ID")
                    return {}
            
            # Check if relationship already exists
            existing_rel = self.postgres.execute_query(f"""
                SELECT id FROM country_education_systems 
                WHERE country_id = '{country_id}' AND education_system_id = '{education_system_id}'
            """)
            
            if existing_rel['success'] and not existing_rel['data']:
                self.postgres.execute_query(f"""
                    INSERT INTO country_education_systems (country_id, education_system_id, is_primary)
                    VALUES ('{country_id}', '{education_system_id}', true)
                """)
        
        # Get IDs using fallback SELECT queries if needed
        result_data = {}
        
        # Get country ID
        if uae_country['success'] and 'data' in uae_country and uae_country['data']:
            result_data['country_id'] = uae_country['data'][0]['id']
        else:
            country_result = self.postgres.execute_query("SELECT id FROM countries WHERE code = 'UAE'")
            result_data['country_id'] = country_result['data'][0]['id'] if country_result['success'] and country_result['data'] else None
        
        # Get education system ID
        if uae_moe['success'] and 'data' in uae_moe and uae_moe['data']:
            result_data['education_system_id'] = uae_moe['data'][0]['id']
        else:
            moe_result = self.postgres.execute_query("SELECT id FROM education_systems WHERE code = 'UAE_MOE'")
            result_data['education_system_id'] = moe_result['data'][0]['id'] if moe_result['success'] and moe_result['data'] else None
        
        # Get subject ID
        if math_subject['success'] and 'data' in math_subject and math_subject['data']:
            result_data['subject_id'] = math_subject['data'][0]['id']
        else:
            subject_result = self.postgres.execute_query("SELECT id FROM subjects WHERE code = 'MATH'")
            result_data['subject_id'] = subject_result['data'][0]['id'] if subject_result['success'] and subject_result['data'] else None
        
        # Get language ID
        if english_lang['success'] and 'data' in english_lang and english_lang['data']:
            result_data['language_id'] = english_lang['data'][0]['id']
        else:
            lang_result = self.postgres.execute_query("SELECT id FROM languages WHERE code = 'EN'")
            result_data['language_id'] = lang_result['data'][0]['id'] if lang_result['success'] and lang_result['data'] else None
        
        # Get question type ID
        if example_qt['success'] and 'data' in example_qt and example_qt['data']:
            result_data['question_type_id'] = example_qt['data'][0]['id']
        else:
            qt_result = self.postgres.execute_query("SELECT id FROM question_types WHERE code = 'EXAMPLE'")
            result_data['question_type_id'] = qt_result['data'][0]['id'] if qt_result['success'] and qt_result['data'] else None
        
        return result_data
    
    def get_or_create_grade(self, grade_name: str, age_group: str, education_system_id: str) -> str:
        """Get or create a grade and return its ID."""
        if grade_name in self.cache['grades']:
            return self.cache['grades'][grade_name]
        
        # Extract grade number from grade name (e.g., "Grade 1" -> 1, "Grade 10 (General)" -> 10)
        import re
        match = re.search(r'Grade (\d+)', grade_name)
        if match:
            grade_number = int(match.group(1))
        else:
            raise ValueError(f"Could not extract grade number from: {grade_name}")
        
        # Check if grade exists
        existing = self.postgres.execute_query(f"""
            SELECT id FROM grades 
            WHERE education_system_id = '{education_system_id}' AND grade_number = {grade_number}
        """)
        
        if existing['success'] and existing['data']:
            grade_id = existing['data'][0]['id']
        else:
            # Create new grade
            result = self.postgres.execute_query(f"""
                INSERT INTO grades (education_system_id, grade_number, grade_name, age_group)
                VALUES ('{education_system_id}', {grade_number}, '{grade_name}', '{age_group}')
                RETURNING id
            """)
            if result['success'] and 'data' in result and result['data']:
                grade_id = result['data'][0]['id']
            else:
                # Fallback to SELECT
                grade_result = self.postgres.execute_query(f"""
                    SELECT id FROM grades 
                    WHERE education_system_id = '{education_system_id}' AND grade_number = {grade_number}
                """)
                if grade_result['success'] and grade_result['data']:
                    grade_id = grade_result['data'][0]['id']
                else:
                    raise Exception(f"Failed to create grade: {grade_name}")
        
        self.cache['grades'][grade_name] = grade_id
        return grade_id
    
    def get_or_create_topic(self, topic_name: str, education_system_id: str, 
                           subject_id: str, grade_id: str) -> str:
        """Get or create a topic and return its ID."""
        cache_key = f"{grade_id}:{topic_name}"
        if cache_key in self.cache['topics']:
            return self.cache['topics'][cache_key]
        
        # Escape single quotes in topic name
        topic_name_escaped = topic_name.replace("'", "''")
        
        # Check if topic exists
        existing = self.postgres.execute_query(f"""
            SELECT id FROM topics 
            WHERE education_system_id = '{education_system_id}' 
                AND subject_id = '{subject_id}' 
                AND grade_id = '{grade_id}' 
                AND name = '{topic_name_escaped}'
        """)
        
        if existing['success'] and existing['data']:
            topic_id = existing['data'][0]['id']
        else:
            # Create new topic
            result = self.postgres.execute_query(f"""
                INSERT INTO topics (education_system_id, subject_id, grade_id, name)
                VALUES ('{education_system_id}', '{subject_id}', '{grade_id}', '{topic_name_escaped}')
                RETURNING id
            """)
            if result['success'] and 'data' in result and result['data']:
                topic_id = result['data'][0]['id']
            else:
                # Fallback to SELECT
                topic_result = self.postgres.execute_query(f"""
                    SELECT id FROM topics 
                    WHERE education_system_id = '{education_system_id}' 
                        AND subject_id = '{subject_id}' 
                        AND grade_id = '{grade_id}' 
                        AND name = '{topic_name_escaped}'
                """)
                if topic_result['success'] and topic_result['data']:
                    topic_id = topic_result['data'][0]['id']
                else:
                    raise Exception(f"Failed to create topic: {topic_name}")
        
        self.cache['topics'][cache_key] = topic_id
        return topic_id
    
    def get_or_create_chapter(self, chapter_name: str, topic_id: str) -> str:
        """Get or create a chapter and return its ID."""
        cache_key = f"{topic_id}:{chapter_name}"
        if cache_key in self.cache['chapters']:
            return self.cache['chapters'][cache_key]
        
        # Escape single quotes in chapter name
        chapter_name_escaped = chapter_name.replace("'", "''")
        
        # Check if chapter exists
        existing = self.postgres.execute_query(f"""
            SELECT id FROM chapters 
            WHERE topic_id = '{topic_id}' AND name = '{chapter_name_escaped}'
        """)
        
        if existing['success'] and existing['data']:
            chapter_id = existing['data'][0]['id']
        else:
            # Create new chapter
            result = self.postgres.execute_query(f"""
                INSERT INTO chapters (topic_id, name)
                VALUES ('{topic_id}', '{chapter_name_escaped}')
                RETURNING id
            """)
            if result['success'] and 'data' in result and result['data']:
                chapter_id = result['data'][0]['id']
            else:
                # Fallback to SELECT
                chapter_result = self.postgres.execute_query(f"""
                    SELECT id FROM chapters 
                    WHERE topic_id = '{topic_id}' AND name = '{chapter_name_escaped}'
                """)
                if chapter_result['success'] and chapter_result['data']:
                    chapter_id = chapter_result['data'][0]['id']
                else:
                    raise Exception(f"Failed to create chapter: {chapter_name}")
        
        self.cache['chapters'][cache_key] = chapter_id
        return chapter_id
    
    def get_or_create_subtopic(self, subtopic_name: str, chapter_id: str) -> str:
        """Get or create a subtopic and return its ID."""
        cache_key = f"{chapter_id}:{subtopic_name}"
        if cache_key in self.cache['subtopics']:
            return self.cache['subtopics'][cache_key]
        
        # Escape single quotes in subtopic name
        subtopic_name_escaped = subtopic_name.replace("'", "''")
        
        # Check if subtopic exists
        existing = self.postgres.execute_query(f"""
            SELECT id FROM sub_topics 
            WHERE chapter_id = '{chapter_id}' AND name = '{subtopic_name_escaped}'
        """)
        
        if existing['success'] and existing['data']:
            subtopic_id = existing['data'][0]['id']
        else:
            # Create new subtopic
            result = self.postgres.execute_query(f"""
                INSERT INTO sub_topics (chapter_id, name)
                VALUES ('{chapter_id}', '{subtopic_name_escaped}')
                RETURNING id
            """)
            if result['success'] and 'data' in result and result['data']:
                subtopic_id = result['data'][0]['id']
            else:
                # Fallback to SELECT
                subtopic_result = self.postgres.execute_query(f"""
                    SELECT id FROM sub_topics 
                    WHERE chapter_id = '{chapter_id}' AND name = '{subtopic_name_escaped}'
                """)
                if subtopic_result['success'] and subtopic_result['data']:
                    subtopic_id = subtopic_result['data'][0]['id']
                else:
                    raise Exception(f"Failed to create subtopic: {subtopic_name}")
        
        self.cache['subtopics'][cache_key] = subtopic_id
        return subtopic_id
    
    def ingest_csv(self, csv_path: str):
        """Ingest the UAE MOE Math curriculum CSV file."""
        # Setup base data
        base_data = self.setup_base_data()
        
        if not all(base_data.values()):
            print("Error: Failed to setup base data")
            return
        
        # Read and process CSV
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Extract data from row
                    grade_name = row['Year / Grade'].strip()
                    age_group = row['Age'].strip()
                    topic_name = row['Broad Topic'].strip()
                    subtopic_name = row['Subtopic'].strip()
                    chapter_name = row['Chapter'].strip()
                    example_question = row['Example question'].strip()
                    
                    # Get or create grade
                    grade_id = self.get_or_create_grade(
                        grade_name, age_group, base_data['education_system_id']
                    )
                    
                    # Get or create topic
                    topic_id = self.get_or_create_topic(
                        topic_name, base_data['education_system_id'], 
                        base_data['subject_id'], grade_id
                    )
                    
                    # Get or create chapter
                    chapter_id = self.get_or_create_chapter(chapter_name, topic_id)
                    
                    # Get or create subtopic
                    subtopic_id = self.get_or_create_subtopic(subtopic_name, chapter_id)
                    
                    # Create example question if provided
                    if example_question and example_question.lower() != 'n/a':
                        # Escape single quotes in question text
                        example_question_escaped = example_question.replace("'", "''")
                        
                        existing_q = self.postgres.execute_query(f"""
                            SELECT id FROM questions 
                            WHERE sub_topic_id = '{subtopic_id}' 
                                AND question_text = '{example_question_escaped}'
                        """)
                        
                        if existing_q['success'] and not existing_q['data']:
                            self.postgres.execute_query(f"""
                                INSERT INTO questions (sub_topic_id, language_id, question_type_id, question_text, difficulty_level)
                                VALUES ('{subtopic_id}', '{base_data['language_id']}', '{base_data['question_type_id']}', 
                                        '{example_question_escaped}', 'medium')
                            """)
                    
                    print(f"Processed: {grade_name} - {topic_name} - {subtopic_name}")
                    
                except Exception as e:
                    print(f"Error processing row: {row}")
                    print(f"Error: {str(e)}")
                    continue
        
        print("Ingestion complete!")

if __name__ == "__main__":
    csv_path = "data/uae_moe_math.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
    else:
        ingester = UAECurriculumIngesterPSQL()
        ingester.ingest_csv(csv_path)