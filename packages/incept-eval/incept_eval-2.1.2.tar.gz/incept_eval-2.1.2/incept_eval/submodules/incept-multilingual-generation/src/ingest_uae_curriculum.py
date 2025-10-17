import csv
import os
from typing import Dict, Set, Tuple, Optional
from uuid import UUID
from src.db.supabase_client import supabase
from dotenv import load_dotenv

load_dotenv()

class UAECurriculumIngester:
    def __init__(self):
        self.supabase = supabase
        self.cache = {
            'grades': {},
            'topics': {},
            'chapters': {},
            'subtopics': {}
        }
        
    def setup_base_data(self):
        """Setup initial data for countries, education systems, subjects, etc."""
        
        # Insert UAE country
        uae_country = self.supabase.table('countries').upsert({
            'code': 'UAE',
            'name': 'United Arab Emirates'
        }, on_conflict='code').execute()
        
        # Insert UAE MOE education system
        uae_moe = self.supabase.table('education_systems').upsert({
            'code': 'UAE_MOE',
            'name': 'UAE Ministry of Education',
            'description': 'United Arab Emirates Ministry of Education Curriculum'
        }, on_conflict='code').execute()
        
        # Insert Mathematics subject
        math_subject = self.supabase.table('subjects').upsert({
            'code': 'MATH',
            'name': 'Mathematics',
            'description': 'Mathematics curriculum'
        }, on_conflict='code').execute()
        
        # Insert English language
        english_lang = self.supabase.table('languages').upsert({
            'code': 'EN',
            'name': 'English'
        }, on_conflict='code').execute()
        
        # Insert question type for example questions
        example_qt = self.supabase.table('question_types').upsert({
            'code': 'EXAMPLE',
            'name': 'Example Question',
            'description': 'Example questions from curriculum'
        }, on_conflict='code').execute()
        
        # Link country to education system
        if uae_country.data and uae_moe.data:
            # Check if relationship already exists
            existing_rel = self.supabase.table('country_education_systems').select('id').eq(
                'country_id', uae_country.data[0]['id']
            ).eq('education_system_id', uae_moe.data[0]['id']).execute()
            
            if not existing_rel.data:
                self.supabase.table('country_education_systems').insert({
                    'country_id': uae_country.data[0]['id'],
                    'education_system_id': uae_moe.data[0]['id'],
                    'is_primary': True
                }).execute()
        
        return {
            'country_id': uae_country.data[0]['id'] if uae_country.data else None,
            'education_system_id': uae_moe.data[0]['id'] if uae_moe.data else None,
            'subject_id': math_subject.data[0]['id'] if math_subject.data else None,
            'language_id': english_lang.data[0]['id'] if english_lang.data else None,
            'question_type_id': example_qt.data[0]['id'] if example_qt.data else None
        }
    
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
        existing = self.supabase.table('grades').select('id').eq(
            'education_system_id', education_system_id
        ).eq('grade_number', grade_number).execute()
        
        if existing.data:
            grade_id = existing.data[0]['id']
        else:
            # Create new grade
            result = self.supabase.table('grades').insert({
                'education_system_id': education_system_id,
                'grade_number': grade_number,
                'grade_name': grade_name,
                'age_group': age_group
            }).execute()
            grade_id = result.data[0]['id']
        
        self.cache['grades'][grade_name] = grade_id
        return grade_id
    
    def get_or_create_topic(self, topic_name: str, education_system_id: str, 
                           subject_id: str, grade_id: str) -> str:
        """Get or create a topic and return its ID."""
        cache_key = f"{grade_id}:{topic_name}"
        if cache_key in self.cache['topics']:
            return self.cache['topics'][cache_key]
        
        # Check if topic exists
        existing = self.supabase.table('topics').select('id').eq(
            'education_system_id', education_system_id
        ).eq('subject_id', subject_id).eq('grade_id', grade_id).eq('name', topic_name).execute()
        
        if existing.data:
            topic_id = existing.data[0]['id']
        else:
            # Create new topic
            result = self.supabase.table('topics').insert({
                'education_system_id': education_system_id,
                'subject_id': subject_id,
                'grade_id': grade_id,
                'name': topic_name
            }).execute()
            topic_id = result.data[0]['id']
        
        self.cache['topics'][cache_key] = topic_id
        return topic_id
    
    def get_or_create_chapter(self, chapter_name: str, topic_id: str) -> str:
        """Get or create a chapter and return its ID."""
        cache_key = f"{topic_id}:{chapter_name}"
        if cache_key in self.cache['chapters']:
            return self.cache['chapters'][cache_key]
        
        # Check if chapter exists
        existing = self.supabase.table('chapters').select('id').eq(
            'topic_id', topic_id
        ).eq('name', chapter_name).execute()
        
        if existing.data:
            chapter_id = existing.data[0]['id']
        else:
            # Create new chapter
            result = self.supabase.table('chapters').insert({
                'topic_id': topic_id,
                'name': chapter_name
            }).execute()
            chapter_id = result.data[0]['id']
        
        self.cache['chapters'][cache_key] = chapter_id
        return chapter_id
    
    def get_or_create_subtopic(self, subtopic_name: str, chapter_id: str) -> str:
        """Get or create a subtopic and return its ID."""
        cache_key = f"{chapter_id}:{subtopic_name}"
        if cache_key in self.cache['subtopics']:
            return self.cache['subtopics'][cache_key]
        
        # Check if subtopic exists
        existing = self.supabase.table('sub_topics').select('id').eq(
            'chapter_id', chapter_id
        ).eq('name', subtopic_name).execute()
        
        if existing.data:
            subtopic_id = existing.data[0]['id']
        else:
            # Create new subtopic
            result = self.supabase.table('sub_topics').insert({
                'chapter_id': chapter_id,
                'name': subtopic_name
            }).execute()
            subtopic_id = result.data[0]['id']
        
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
                        existing_q = self.supabase.table('questions').select('id').eq(
                            'sub_topic_id', subtopic_id
                        ).eq('question_text', example_question).execute()
                        
                        if not existing_q.data:
                            self.supabase.table('questions').insert({
                                'sub_topic_id': subtopic_id,
                                'language_id': base_data['language_id'],
                                'question_type_id': base_data['question_type_id'],
                                'question_text': example_question,
                                'difficulty_level': 'medium'
                            }).execute()
                    
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
        ingester = UAECurriculumIngester()
        ingester.ingest_csv(csv_path)