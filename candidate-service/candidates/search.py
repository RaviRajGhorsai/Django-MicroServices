from opensearchpy import OpenSearch
from django.conf import settings

client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
    use_ssl=False,
)

CANDIDATES_INDEX = 'candidates'
JOBS_INDEX       = 'jobs'        # written by job-service, read by us


# ══════════════════════════════════════════════════════
# CANDIDATES INDEX — candidate-service owns this
# ══════════════════════════════════════════════════════

def create_index():
    """Called once on startup via create_os_index management command."""
    if not client.indices.exists(CANDIDATES_INDEX):
        client.indices.create(CANDIDATES_INDEX, body={
            'mappings': {
                'properties': {
                    'name':             {'type': 'text'},
                    'email':            {'type': 'keyword'},
                    'skills':           {'type': 'keyword'},
                    'location':         {'type': 'keyword'},
                    'experience_years': {'type': 'integer'},
                    'resume_text':      {'type': 'text'},
                }
            }
        })


def index_candidate(candidate):
    """Write/update a candidate document. Called via Celery task."""
    client.index(
        index=CANDIDATES_INDEX,
        id=str(candidate.id),
        body={
            'name':             candidate.name,
            'email':            candidate.email,
            'skills':           candidate.skills,
            'location':         candidate.location,
            'experience_years': candidate.experience_years,
            'resume_text':      candidate.resume_text,
        }
    )


def delete_candidate(candidate_id):
    """Remove candidate document when profile is deleted."""
    client.delete(index=CANDIDATES_INDEX, id=str(candidate_id), ignore=[404])


# ══════════════════════════════════════════════════════
# JOBS INDEX — job-service owns this, we only READ it
# ══════════════════════════════════════════════════════

def search_jobs_from_opensearch(query=None, location=None,
                                skills=None, salary_min=None):
    """
    Candidate searches active jobs.
    Reads from `jobs` index written by job-service.
    No HTTP call to job-service needed.
    """
    must    = []
    filters = [{'term': {'status': 'active'}}]  # candidates never see draft/closed

    if query:
        must.append({
            'multi_match': {
                'query':     query,
                'fields':    ['title^3', 'description'],  # title boosted
                'fuzziness': 'AUTO',
            }
        })

    if location:
        filters.append({'term': {'location': location}})

    if skills:
        for skill in skills:
            filters.append({'term': {'skills_required': skill}})

    if salary_min:
        filters.append({
            'range': {'salary_max': {'gte': float(salary_min)}}
        })

    body = {
        'query': {
            'bool': {
                'must':   must or [{'match_all': {}}],
                'filter': filters,
            }
        },
        'sort': [{'created_at': 'desc'}],
        'size': 20,
    }

    resp = client.search(index=JOBS_INDEX, body=body)
    return [
        {'id': h['_id'], 'score': h['_score'], **h['_source']}
        for h in resp['hits']['hits']
    ]


def get_job_by_id(job_id):
    """
    Candidate views a single job detail.
    Reads from `jobs` index by document ID.
    Returns None if not found.
    """
    try:
        resp = client.get(index=JOBS_INDEX, id=str(job_id))
        return {'id': resp['_id'], **resp['_source']}
    except Exception:
        return None