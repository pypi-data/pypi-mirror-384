#!/usr/bin/env python3
"""
Extract mathematics questions from Athena API for a specific grade.
"""
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

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
AUTH_TOKEN = "eyJraWQiOiJWalVrVFNXeGtVZnB2YncyNWlhcFgrUjl6bThqallMeTlhQ0lHak5hTzVrPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJjdXN0b206c3R1ZGVudENyZWRzRW5jU2FsdCI6ImQ2NjgxMDMyYWUzN2U0NjNjZjhmZWE1NmU4ZDUzMDYwZTYwMmU4M2M3NWJhOWEzNjNlMDIwOWVhNmM4NzUxNmYwMiIsImNvZ25pdG86Z3JvdXBzIjpbIlN0dWRlbnQiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImNvZ25pdG86cHJlZmVycmVkX3JvbGUiOiJhcm46YXdzOmlhbTo6NTE1NDUxNzE1MDg2OnJvbGVcL2FscGhhY29hY2hib3QtcHJvZHVjdGlvbi1hbHBoYWNvYWNoYm90cHJvZHVjdGlvbnMtMURGOUk1SUpKUVVKSiIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX2FEUEM2V0hsMSIsImNvZ25pdG86dXNlcm5hbWUiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwcmF2ZWVuLmtva2FAdHJpbG9neS5jb20iLCJsb2NhbGUiOiJlbi1VUyIsImN1c3RvbTpzdHVkZW50SUQiOiI1YjU1MmJlYy0wNmZhLTRmZjItYmUzNC1mODUxYzE1NzI3ZWYiLCJjdXN0b206dXNlcklEIjoiMzU5Y2NkOWUtMmNiMS00MDFlLTk0NTctMWYxOGM4YjNkNzQwIiwib3JpZ2luX2p0aSI6ImVlY2NhYTQ2LTE4OTktNGNkZC04NzMzLWNjMzNjOGRjNjgzYiIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjUxNTQ1MTcxNTA4Njpyb2xlXC9hbHBoYWNvYWNoYm90LXByb2R1Y3Rpb24tYWxwaGFjb2FjaGJvdHByb2R1Y3Rpb25zLTFERjlJNUlKSlFVSkoiXSwiYXVkIjoiZzk0MWxtMTJsODdvOTA5Ym11ZGRzOXY4MSIsImV2ZW50X2lkIjoiNzY1YzA2ZTItNzYwMi00Nzk4LTk4MGQtODBhOTAwMTY2NDQ0IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NTk3NDE3NDIsImN1c3RvbTpwcmVmZXJyZWROYW1lIjoiUHJhdmVlbiBLb2thIiwiZXhwIjoxNzU5OTE1NTUwLCJjdXN0b206cm9sZSI6IlN0dWRlbnQiLCJpYXQiOjE3NTk4MjkxNTAsImp0aSI6IjQ2M2E4NmUyLTRlMzQtNDVlNi1iNzk5LTdiMjUxMzg4MTA0NiIsImVtYWlsIjoicHJhdmVlbi5rb2thQHRyaWxvZ3kuY29tIn0.jPwT2ajCo1EjqoiVZU0lIRxU6NdsYAqRIMcSGTaX1-JhBnmFdHX7pbm8q1EZO1O7WNQx3Znb4IAf1P11oqg7kiQuydej_Gpxih7JpFFXXVgzvM3hEsrX_i5JhC4l-HcP154VbdZXcXDNOh_cCGqHgUC6YDRBKNSgvyWy8wiYydrqZGFm1auG-Y7h0MDWhWVts2692rSKJdW9d2uPZnXeK9HuBPnfuOxDCkTfD9GuhNuKr32SJl1DaUjNQGLUccr7RHUWKpDBRWwv4WLgBhIbScm2xZRjBxHpbq_DGZxxSrBOJU_mcb5tdX1cPLrqy0RXCce3m2N-KFaTG1wGexIbtQ"

def get_learning_content_items(course_id: str, unit_id: str, lesson_id: str, level_id: str, batch_size: int = 50, exclude_ids: Optional[List[str]] = None) -> List[Dict]:
    """Get learning content items for a specific level."""
    headers = {
        'content-type': 'application/json',
        'authorization': AUTH_TOKEN
    }

    query = """
    query GetLearningContentItemsQuery($input: GetLearningContentItemsInput!) {
      getLearningContentItems(input: $input) {
        items {
          contentId
          contentTypeId
          contentTypeName
          content
          subjectId
          courseId
          unitId
          lessonId
          levelId
          attributes {
            attributeName
            attributeValue
          }
          extendedAttributes {
            type
            value
          }
        }
      }
    }
    """

    variables = {
        "input": {
            "courseId": course_id,
            "unitId": unit_id,
            "lessonId": lesson_id,
            "levelId": level_id,
            "programType": "FOUNDATIONAL",
            "batchSize": batch_size
        }
    }

    if exclude_ids:
        variables["input"]["excludeContentIds"] = exclude_ids

    payload = {
        'operationName': 'GetLearningContentItemsQuery',
        'variables': variables,
        'query': query
    }

    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return []

        items = data.get('data', {}).get('getLearningContentItems', {}).get('items', [])
        return items
    except Exception as e:
        logger.error(f"Failed to get content: {e}")
        return []

def load_processed_clusters(output_file: Path) -> set:
    """Load set of cluster IDs that have already been processed."""
    if not output_file.exists():
        return set()

    processed = set()
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    cluster_id = record.get('cluster_id')
                    if cluster_id:
                        processed.add(cluster_id)
    except Exception as e:
        logger.warning(f"Could not load processed clusters: {e}")

    return processed

def extract_questions_for_grade(grade: str, output_file: Path):
    """Extract all questions for a specific grade."""

    # Load curriculum data to get all levels for this grade
    curriculum_file = Path(__file__).parent.parent.parent / "data" / "athena_extracted" / "math_curriculum.jsonl"

    if not curriculum_file.exists():
        logger.error(f"Curriculum file not found: {curriculum_file}")
        logger.error("Run extract_curriculum.py first")
        sys.exit(1)

    # Load all levels for this grade
    levels = []
    with open(curriculum_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                if str(record.get('grade')) == str(grade):
                    levels.append(record)

    if not levels:
        logger.error(f"No curriculum levels found for grade {grade}")
        sys.exit(1)

    logger.info(f"Found {len(levels)} levels for grade {grade}")
    logger.info(f"Course: {levels[0].get('course_name')}")

    # Track processed content IDs to avoid duplicates
    processed_content_ids = set()
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    content_id = record.get('content_id')
                    if content_id:
                        processed_content_ids.add(content_id)
        logger.info(f"Loaded {len(processed_content_ids)} previously extracted questions")

    total_questions = 0
    total_levels_processed = 0

    # Process each level
    for i, level_info in enumerate(levels, 1):
        unit_name = level_info.get('unit_name')
        lesson_name = level_info.get('lesson_name')
        level_name = level_info.get('level_name')

        logger.info(f"\n[{i}/{len(levels)}] {unit_name} > {lesson_name} > {level_name}")

        # Get content for this level (batch_size=1 required by adaptive strategy)
        # We'll call multiple times to get more content
        content_items = []
        exclude_ids = list(processed_content_ids)
        max_items_per_level = 10  # Try to get up to 10 items per level

        for attempt in range(max_items_per_level):
            items = get_learning_content_items(
                course_id=level_info.get('course_id'),
                unit_id=level_info.get('unit_id'),
                lesson_id=level_info.get('lesson_id'),
                level_id=level_info.get('level_id'),
                batch_size=1,
                exclude_ids=exclude_ids if exclude_ids else None
            )

            if not items:
                break  # No more content available

            content_items.extend(items)
            # Add to exclude list for next iteration
            for item in items:
                exclude_ids.append(item.get('contentId'))

        if not content_items:
            logger.info(f"  No content found")
            continue

        # Filter out already processed items
        new_items = [item for item in content_items if item.get('contentId') not in processed_content_ids]

        if not new_items:
            logger.info(f"  Retrieved {len(content_items)} items (all already processed)")
            continue

        logger.info(f"  Retrieved {len(new_items)} new items (skipped {len(content_items) - len(new_items)} duplicates)")

        # Write each content item to JSONL
        with open(output_file, 'a', encoding='utf-8') as f:
            for item in new_items:
                # Extract answer from attributes if available
                answer = None
                for attr in item.get('attributes', []):
                    if attr.get('attributeName') in ['answer', 'correctAnswer', 'solution']:
                        answer = attr.get('attributeValue')
                        break

                record = {
                    'grade': grade,
                    'subject': 'Math',
                    'course_name': level_info.get('course_name'),
                    'course_id': level_info.get('course_id'),
                    'unit_id': level_info.get('unit_id'),
                    'unit_name': unit_name,
                    'lesson_id': level_info.get('lesson_id'),
                    'lesson_name': lesson_name,
                    'level_id': level_info.get('level_id'),
                    'level_name': level_name,
                    'content_id': item.get('contentId'),
                    'content_type_id': item.get('contentTypeId'),
                    'content_type_name': item.get('contentTypeName'),
                    'question': item.get('content'),
                    'answer': answer,
                    'attributes': item.get('attributes', []),
                    'extended_attributes': item.get('extendedAttributes', []),
                    'extracted_at': datetime.now().isoformat()
                }

                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                f.flush()
                total_questions += 1
                processed_content_ids.add(item.get('contentId'))

        total_levels_processed += 1

    logger.info(f"\n{'='*80}")
    logger.info(f"✅ Extraction complete for grade {grade}!")
    logger.info(f"   Levels processed: {total_levels_processed}/{len(levels)}")
    logger.info(f"   Total questions extracted: {total_questions}")
    logger.info(f"   Output file: {output_file}")
    logger.info(f"{'='*80}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_questions.py <grade>")
        print("\nExamples:")
        print("  python extract_questions.py 3")
        print("  python extract_questions.py 6")
        sys.exit(1)

    grade = sys.argv[1]

    output_dir = Path(__file__).parent.parent.parent / "data" / "athena_extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"math_questions_grade_{grade}.jsonl"

    logger.info(f"🚀 Starting question extraction for Grade {grade}")
    logger.info(f"   Output: {output_file}\n")

    extract_questions_for_grade(grade, output_file)

if __name__ == "__main__":
    main()
