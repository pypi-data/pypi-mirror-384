#!/usr/bin/env python3
"""
Get full curriculum hierarchy with platform IDs using getStudentXP query.
"""
import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GraphQL endpoint and auth
GRAPHQL_URL = "https://qlut52i3snagncfndjewqgixgq.appsync-api.us-east-1.amazonaws.com/graphql"
AUTH_TOKEN = "eyJraWQiOiJWalVrVFNXeGtVZnB2YncyNWlhcFgrUjl6bThqallMeTlhQ0lHak5hTzVrPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJjdXN0b206c3R1ZGVudENyZWRzRW5jU2FsdCI6ImQ2NjgxMDMyYWUzN2U0NjNjZjhmZWE1NmU4ZDUzMDYwZTYwMmU4M2M3NWJhOWEzNjNlMDIwOWVhNmM4NzUxNmYwMiIsImNvZ25pdG86Z3JvdXBzIjpbIlN0dWRlbnQiXSwiZW1haWxfdmVyaWZpZWQiOnRydWUsImNvZ25pdG86cHJlZmVycmVkX3JvbGUiOiJhcm46YXdzOmlhbTo6NTE1NDUxNzE1MDg2OnJvbGVcL2FscGhhY29hY2hib3QtcHJvZHVjdGlvbi1hbHBoYWNvYWNoYm90cHJvZHVjdGlvbnMtMURGOUk1SUpKUVVKSiIsImlzcyI6Imh0dHBzOlwvXC9jb2duaXRvLWlkcC51cy1lYXN0LTEuYW1hem9uYXdzLmNvbVwvdXMtZWFzdC0xX2FEUEM2V0hsMSIsImNvZ25pdG86dXNlcm5hbWUiOiI4YzQ1ZjM3Yy1mZTdhLTRhMjMtYTQ0MC1mNTMzZGU0ZDAzZjYiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJwcmF2ZWVuLmtva2FAdHJpbG9neS5jb20iLCJsb2NhbGUiOiJlbi1VUyIsImN1c3RvbTpzdHVkZW50SUQiOiI1YjU1MmJlYy0wNmZhLTRmZjItYmUzNC1mODUxYzE1NzI3ZWYiLCJjdXN0b206dXNlcklEIjoiMzU5Y2NkOWUtMmNiMS00MDFlLTk0NTctMWYxOGM4YjNkNzQwIiwib3JpZ2luX2p0aSI6ImVlY2NhYTQ2LTE4OTktNGNkZC04NzMzLWNjMzNjOGRjNjgzYiIsImNvZ25pdG86cm9sZXMiOlsiYXJuOmF3czppYW06OjUxNTQ1MTcxNTA4Njpyb2xlXC9hbHBoYWNvYWNoYm90LXByb2R1Y3Rpb24tYWxwaGFjb2FjaGJvdHByb2R1Y3Rpb25zLTFERjlJNUlKSlFVSkoiXSwiYXVkIjoiZzk0MWxtMTJsODdvOTA5Ym11ZGRzOXY4MSIsImV2ZW50X2lkIjoiNzY1YzA2ZTItNzYwMi00Nzk4LTk4MGQtODBhOTAwMTY2NDQ0IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NTk3NDE3NDIsImN1c3RvbTpwcmVmZXJyZWROYW1lIjoiUHJhdmVlbiBLb2thIiwiZXhwIjoxNzU5ODI4MTQyLCJjdXN0b206cm9sZSI6IlN0dWRlbnQiLCJpYXQiOjE3NTk3NDE3NDIsImp0aSI6ImFjZmZiODFiLWQ1MTgtNDg0Mi04OWI0LWY1ZjE0NjI3YmU5OCIsImVtYWlsIjoicHJhdmVlbi5rb2thQHRyaWxvZ3kuY29tIn0.AGkKCZUfr6Jxf-4UuacvSfPd_jBy5ejLHqu9eqWM5j4E1Bbp6Tirt2ekTNVoUXCKAZ_C1BMM6mTZOKTe81fSR3TQ78R6GJ3xkdCYNdnMkVt_UVNDEXljh0LVLHwc93kCOML-us_NDtFB83Anaq8t8bLGI_9B9E3MSWS3SB6pvg9KUY4hbojGx1cwLVsVgN6W8JtrRYP5f3V2CNm-1e1bxCc5MOKqPzclIBZnFRa7W0gbEcauAnU-bSXaEeSpryNUHlM0yr20bKaVaVNKDye6O4uFN690-c1RmajS56ujYwYdARgb8s4ABt5AcJjScF-WiJtvzmRD9EnaDOFqXJ2K7Q"
STUDENT_ID = "5b552bec-06fa-4ff2-be34-f851c15727ef"

QUERY = """
query GetCurriculum {
    getCurriculum {
        curriculum {
            subjects {
                name
                platformId
                courses {
                    name
                    platformId
                    externalId
                    grade {
                        grade
                        name
                    }
                    domains {
                        name
                        platformId
                        externalId
                        clusters {
                            name
                            externalId
                            platformId
                            standards {
                                platformId
                                description
                                externalId
                            }
                        }
                    }
                }
            }
        }
    }
}
"""

def get_curriculum_hierarchy():
    """Get full curriculum hierarchy with platform IDs."""
    headers = {
        'content-type': 'application/json',
        'authorization': AUTH_TOKEN
    }

    payload = {
        'operationName': 'GetCurriculum',
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

def extract_hierarchy(data, output_file):
    """Extract hierarchy and save to JSONL."""
    curriculum = data.get('data', {}).get('getCurriculum', {}).get('curriculum', {})
    subjects = curriculum.get('subjects', [])

    total_standards = 0

    with open(output_file, 'w', encoding='utf-8') as f:
        for subject in subjects:
            subject_name = subject.get('name')
            subject_platform_id = subject.get('platformId')

            # Filter for Math only
            if subject_name != 'Math':
                continue

            for course in subject.get('courses', []):
                course_name = course.get('name')
                course_platform_id = course.get('platformId')
                course_external_id = course.get('externalId')
                grade_info = course.get('grade', {})
                grade = grade_info.get('grade')
                grade_name = grade_info.get('name')

                for domain in course.get('domains', []):
                    domain_name = domain.get('name')
                    domain_platform_id = domain.get('platformId')
                    domain_external_id = domain.get('externalId')

                    for cluster in domain.get('clusters', []):
                        cluster_name = cluster.get('name')
                        cluster_external_id = cluster.get('externalId')
                        cluster_platform_id = cluster.get('platformId')

                        for standard in cluster.get('standards', []):
                            record = {
                                'subject': subject_name,
                                'subject_platform_id': subject_platform_id,
                                'grade': grade,
                                'grade_name': grade_name,
                                'course_name': course_name,
                                'course_platform_id': course_platform_id,
                                'course_external_id': course_external_id,
                                'domain_name': domain_name,
                                'domain_platform_id': domain_platform_id,
                                'domain_external_id': domain_external_id,
                                'cluster_name': cluster_name,
                                'cluster_external_id': cluster_external_id,
                                'cluster_platform_id': cluster_platform_id,
                                'standard_external_id': standard.get('externalId'),
                                'standard_platform_id': standard.get('platformId'),
                                'standard_description': standard.get('description'),
                                'extracted_at': datetime.now().isoformat()
                            }

                            f.write(json.dumps(record, ensure_ascii=False) + '\n')
                            total_standards += 1

    logger.info(f"✅ Extracted {total_standards} Math standards across all grades")

def main():
    output_dir = Path(__file__).parent.parent.parent / "data" / "athena_extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "math_hierarchy.jsonl"

    logger.info(f"🚀 Fetching curriculum hierarchy from Athena API")
    logger.info(f"   Output: {output_file}\n")

    data = get_curriculum_hierarchy()

    if not data:
        logger.error("Failed to fetch curriculum hierarchy")
        sys.exit(1)

    extract_hierarchy(data, output_file)
    logger.info(f"   Output file: {output_file}")

if __name__ == "__main__":
    main()
