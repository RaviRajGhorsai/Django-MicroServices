from opensearchpy import OpenSearch
from django.conf import settings

client = OpenSearch(
    hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
    use_ssl=False,
)

JOBS_INDEX         = 'jobs'
APPLICATIONS_INDEX = 'applications'


# ── Jobs index ────────────────────────────────────────────

def create_index():
    if not client.indices.exists(JOBS_INDEX):
        client.indices.create(JOBS_INDEX, body={
            'mappings': {'properties': {
                'title':           {'type': 'text'},
                'description':     {'type': 'text'},
                'company':         {'type': 'keyword'},
                'location':        {'type': 'keyword'},
                'skills_required': {'type': 'keyword'},
                'status':          {'type': 'keyword'},
                'salary_min':      {'type': 'float'},
                'salary_max':      {'type': 'float'},
                'created_at':      {'type': 'date'},
            }}
        })
    if not client.indices.exists(APPLICATIONS_INDEX):
        client.indices.create(APPLICATIONS_INDEX, body={
            'mappings': {'properties': {
                'job_id':           {'type': 'integer'},
                'job_title':        {'type': 'text'},
                'candidate_id':     {'type': 'integer'},
                'candidate_name':   {'type': 'text'},
                'candidate_email':  {'type': 'keyword'},
                'skills':           {'type': 'keyword'},
                'location':         {'type': 'keyword'},
                'experience_years': {'type': 'integer'},
                'cover_letter':     {'type': 'text'},
                'status':           {'type': 'keyword'},
                'applied_at':       {'type': 'date'},
            }}
        })

def index_job(job):
    client.index(index=JOBS_INDEX, id=str(job.id), body={
        'title':           job.title,
        'description':     job.description,
        'company':         job.company,
        'location':        job.location,
        'skills_required': job.skills_required,
        'status':          job.status,
        'salary_min':      float(job.salary_min) if job.salary_min else None,
        'salary_max':      float(job.salary_max) if job.salary_max else None,
        'created_at':      job.created_at.isoformat(),
    })

def delete_job(job_id):
    client.delete(index=JOBS_INDEX, id=str(job_id), ignore=[404])

def index_application(application):
    client.index(index=APPLICATIONS_INDEX, id=str(application.id), body={
        'job_id':           application.job.id,
        'job_title':        application.job.title,
        'candidate_id':     application.candidate_id,
        'candidate_name':   application.candidate_name,
        'candidate_email':  application.candidate_email,
        'skills':           application.candidate_skills,
        'location':         application.candidate_location,
        'experience_years': application.experience_years,
        'cover_letter':     application.cover_letter,
        'status':           application.status,
        'applied_at':       application.applied_at.isoformat(),
    })

def update_application_status_in_os(application_id: int, new_status: str):
    client.update(index=APPLICATIONS_INDEX, id=str(application_id), body={
        'doc': {'status': new_status}
    })

def search_applicants(job_id, query=None, skills=None, location=None,
                      min_experience=None, status=None):
    must    = []
    filters = [{'term': {'job_id': job_id}}]   # always scoped to one job

    if query:
        must.append({'multi_match': {
            'query': query,
            'fields': ['candidate_name^2', 'cover_letter'],
            'fuzziness': 'AUTO',
        }})
    if skills:
        for s in skills:
            filters.append({'term': {'skills': s}})
    if location:
        filters.append({'term': {'location': location}})
    if min_experience:
        filters.append({'range': {'experience_years': {'gte': int(min_experience)}}})
    if status:
        filters.append({'term': {'status': status}})

    body = {
        'query': {'bool': {'must': must or [{'match_all': {}}], 'filter': filters}},
        'sort':  [{'applied_at': 'desc'}],
        'size':  50,
    }
    resp = client.search(index=APPLICATIONS_INDEX, body=body)
    return [{'id': h['_id'], 'score': h['_score'], **h['_source']}
            for h in resp['hits']['hits']]