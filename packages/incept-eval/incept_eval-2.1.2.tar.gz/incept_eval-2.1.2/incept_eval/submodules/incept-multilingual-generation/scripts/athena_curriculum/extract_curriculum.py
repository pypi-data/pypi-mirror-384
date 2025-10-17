#!/usr/bin/env python3
"""
Extract curriculum data from Athena GraphQL API.
"""
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GraphQL endpoint and auth
GRAPHQL_URL = "https://qlut52i3snagncfndjewqgixgq.appsync-api.us-east-1.amazonaws.com/graphql"
AUTH_TOKEN = "eyJraWQiOiJWalVrVFNXeGtVZnB2YncyNWlhcFgrUjl6bThqallMeTlhQ0lHak5hTzVrPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJjdXN0b206c3R1ZGVudENyZWRzRW5jU2FsdCI6ImQ2NjgxMDMyYWUzN2U0NjNjZjhmZWE1NmU4ZDUzMDYwZTYwMmU4M2M3NWJhOWEzNjNlMDIwOWVhNmM4NzUxNmYwMiIsImNvZ25pdG86Z3JvdXBzIjpbIlN0dWRlbnQiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImNvZ25pdG86cHJlZmVycmVkX3JvbGUiOiJhcm46YXdzOmlhbTo6NTE1NDUxNzE1MDg2OnJvbGVcL2FscGhhY29hY2hib3QtcHJvZHVjdGlvbi1hbHBoYWNvYWNoYm90cHJvZHVjdGlvbnMtMURGOUk1SUpKUVVKSiIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX2FEUEM2V0hsMSIsImNvZ25pdG86dXNlcm5hbWUiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwcmF2ZWVuLmtva2FAdHJpbG9neS5jb20iLCJsb2NhbGUiOiJlbi1VUyIsImN1c3RvbTpzdHVkZW50SUQiOiI1YjU1MmJlYy0wNmZhLTRmZjItYmUzNC1mODUxYzE1NzI3ZWYiLCJjdXN0b206dXNlcklEIjoiMzU5Y2NkOWUtMmNiMS00MDFlLTk0NTctMWYxOGM4YjNkNzQwIiwib3JpZ2luX2p0aSI6ImVlY2NhYTQ2LTE4OTktNGNkZC04NzMzLWNjMzNjOGRjNjgzYiIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjUxNTQ1MTcxNTA4Njpyb2xlXC9hbHBoYWNvYWNoYm90LXByb2R1Y3Rpb24tYWxwaGFjb2FjaGJvdHByb2R1Y3Rpb25zLTFERjlJNUlKSlFVSkoiXSwiYXVkIjoiZzk0MWxtMTJsODdvOTA5Ym11ZGRzOXY4MSIsImV2ZW50X2lkIjoiNzY1YzA2ZTItNzYwMi00Nzk4LTk4MGQtODBhOTAwMTY2NDQ0IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NTk3NDE3NDIsImN1c3RvbTpwcmVmZXJyZWROYW1lIjoiUHJhdmVlbiBLb2thIiwiZXhwIjoxNzU5ODI4MTQyLCJjdXN0b206cm9sZSI6IlN0dWRlbnQiLCJpYXQiOjE3NTk3NDE3NDIsImp0aSI6ImFjZmZiODFiLWQ1MTgtNDg0Mi04OWI0LWY1ZjE0NjI3YmU5OCIsImVtYWlsIjoicHJhdmVlbi5rb2thQHRyaWxvZ3kuY29tIn0.AGkKCZUfr6Jxf-4UuacvSfPd_jBy5ejLHqu9eqWM5j4E1Bbp6Tirt2ekTNVoUXCKAZ_C1BMM6mTZOKTe81fSR3TQ78R6GJ3xkdCYNdnMkVt_UVNDEXljh0LVLHwc93kCOML-us_NDtFB83Anaq8t8bLGI_9B9E3MSWS3SB6pvg9KUY4hbojGx1cwLVsVgN6W8JtrRYP5f3V2CNm-1e1bxCc5MOKqPzclIBZnFRa7W0gbEcauAnU-bSXaEeSpryNUHlM0yr20bKaVaVNKDye6O4uFN690-c1RmajS56ujYwYdARgb8s4ABt5AcJjScF-WiJtvzmRD9EnaDOFqXJ2K7Q"

QUERY = """
query GetCurriculumQuery {
  getCurriculum {
    curriculum {
      subjects {
        id
        image
        name
        learningOrder
        courses {
          id
          learningOrder
          programType
          mainImageUrl
          name
          thumbnailUrl
          isDisabled
          grade {
            grade
            name
            __typename
          }
          units {
            id
            learningOrder
            name
            category
            mainImageUrl
            thumbnailUrl
            lessons {
              id
              learningOrder
              name
              mainImageUrl
              thumbnailUrl
              levels {
                id
                learningOrder
                name
                mainImageUrl
                thumbnailUrl
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

def fetch_curriculum():
    """Fetch curriculum data from GraphQL API."""
    logger.info("Fetching curriculum data from Athena API...")

    headers = {
        'content-type': 'application/json',
        'authorization': AUTH_TOKEN
    }

    payload = {
        'operationName': 'GetCurriculumQuery',
        'variables': {},
        'query': QUERY
    }

    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return None

        return data
    except Exception as e:
        logger.error(f"Failed to fetch curriculum: {e}")
        return None

def extract_lessons(curriculum_data, output_file, subject_filter='Math'):
    """Extract lessons from curriculum data and write to JSONL."""

    if not curriculum_data:
        logger.error("No curriculum data to process")
        return

    curriculum = curriculum_data.get('data', {}).get('getCurriculum', {}).get('curriculum', {})
    subjects = curriculum.get('subjects', [])

    total_lessons = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for subject in subjects:
            subject_name = subject.get('name')
            subject_id = subject.get('id')

            # Filter for Math only
            if subject_name != subject_filter:
                logger.info(f"Skipping subject: {subject_name}")
                continue

            logger.info(f"Processing subject: {subject_name}")

            for course in subject.get('courses', []):
                course_name = course.get('name')
                course_id = course.get('id')
                grade_info = course.get('grade', {})
                grade = grade_info.get('grade')
                grade_name = grade_info.get('name')

                if course.get('isDisabled'):
                    logger.info(f"  Skipping disabled course: {course_name} (Grade {grade})")
                    continue

                logger.info(f"  Course: {course_name} (Grade {grade})")

                for unit in course.get('units', []):
                    unit_name = unit.get('name')
                    unit_id = unit.get('id')

                    for lesson in unit.get('lessons', []):
                        lesson_name = lesson.get('name')
                        lesson_id = lesson.get('id')

                        for level in lesson.get('levels', []):
                            record = {
                                'subject_id': subject_id,
                                'subject_name': subject_name,
                                'course_id': course_id,
                                'course_name': course_name,
                                'grade': grade,
                                'grade_name': grade_name,
                                'unit_id': unit_id,
                                'unit_name': unit_name,
                                'lesson_id': lesson_id,
                                'lesson_name': lesson_name,
                                'level_id': level.get('id'),
                                'level_name': level.get('name'),
                                'level_order': level.get('learningOrder'),
                                'level_image': level.get('mainImageUrl'),
                                'level_thumbnail': level.get('thumbnailUrl'),
                                'extracted_at': datetime.now().isoformat()
                            }

                            f.write(json.dumps(record, ensure_ascii=False) + '\n')
                            total_lessons += 1

    logger.info(f"\n✅ Extraction complete!")
    logger.info(f"   Total lessons extracted: {total_lessons}")
    logger.info(f"   Output file: {output_file}")

def main():
    output_dir = Path(__file__).parent.parent.parent / "data" / "athena_extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "math_curriculum.jsonl"

    logger.info(f"🚀 Starting Athena curriculum extraction")
    logger.info(f"   Output: {output_file}\n")

    # Fetch curriculum
    curriculum_data = fetch_curriculum()

    if not curriculum_data:
        logger.error("Failed to fetch curriculum data")
        sys.exit(1)

    # Extract and write lessons
    extract_lessons(curriculum_data, output_file)

if __name__ == "__main__":
    main()
