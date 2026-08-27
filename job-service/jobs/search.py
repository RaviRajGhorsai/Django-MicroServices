from opensearchpy import OpenSearch
from django.conf import settings


client = OpenSearch(
    hosts=[
        {
            "host": settings.OPENSEARCH_HOST,
            "port": settings.OPENSEARCH_PORT,
        }
    ],
    use_ssl=False,
)


JOBS_INDEX = "jobs"
APPLICATIONS_INDEX = "applications"


# ─────────────────────────────────────────────────────────
# Create indexes
# ─────────────────────────────────────────────────────────


def create_index():

    # Jobs index
    if not client.indices.exists(JOBS_INDEX):
        client.indices.create(
            JOBS_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "description": {"type": "text"},
                        "company": {"type": "keyword"},
                        "location": {"type": "keyword"},
                        "skills_required": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "salary_min": {"type": "float"},
                        "salary_max": {"type": "float"},
                        "created_at": {"type": "date"},
                    }
                }
            },
        )

    # Applications index
    if not client.indices.exists(APPLICATIONS_INDEX):
        client.indices.create(
            APPLICATIONS_INDEX,
            body={
                "mappings": {
                    "properties": {
                        "posted_by": {"type": "integer"},
                        "job_id": {"type": "integer"},
                        "job_title": {"type": "text"},
                        "candidate_id": {"type": "integer"},
                        "candidate_data": {
                            "properties": {
                                "name": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                                "email": {"type": "keyword"},
                                "phone": {"type": "keyword"},
                                "skills": {"type": "keyword"},
                                "location": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                                "experience_years": {"type": "integer"},
                                "resume_text": {"type": "text"},
                            }
                        },
                        "cover_letter": {"type": "text"},
                        "status": {"type": "keyword"},
                        "applied_at": {"type": "date"},
                    }
                }
            },
        )


# ─────────────────────────────────────────────────────────
# Jobs
# ─────────────────────────────────────────────────────────


def index_job(job):

    client.index(
        index=JOBS_INDEX,
        id=str(job.id),
        body={
            "title": job.title,
            "description": job.description,
            "company": job.company,
            "location": job.location,
            "skills_required": job.skills_required,
            "status": job.status,
            "salary_min": (
                float(job.salary_min) if job.salary_min is not None else None
            ),
            "salary_max": (
                float(job.salary_max) if job.salary_max is not None else None
            ),
            "created_at": job.created_at.isoformat(),
        },
    )


def delete_job(job_id):

    client.delete(
        index=JOBS_INDEX,
        id=str(job_id),
        ignore=[404],
    )


# ─────────────────────────────────────────────────────────
# Applications
# ─────────────────────────────────────────────────────────


def index_application(application):

    client.index(
        index=APPLICATIONS_INDEX,
        id=str(application.id),
        body={
            "job_id": application.job.id,
            "job_title": application.job.title,
            "candidate_id": application.candidate_id,
            "posted_by": application.job.posted_by.id,
            # Keep candidate data as one JSON object
            "candidate_data": application.candidate_data,
            "cover_letter": application.cover_letter,
            "status": application.status,
            "applied_at": application.applied_at.isoformat(),
        },
    )


def update_application_status_in_os(
    application_id: int,
    new_status: str,
):

    client.update(
        index=APPLICATIONS_INDEX,
        id=str(application_id),
        body={"doc": {"status": new_status}},
    )


# ─────────────────────────────────────────────────────────
# Search applicants
# ─────────────────────────────────────────────────────────


def search_applicants(
    job_id,
    query=None,
    skills=None,
    location=None,
    min_experience=None,
    status=None,
):

    must = []

    filters = [{"term": {"job_id": job_id}}]

    # General candidate search
    if query:
        must.append(
            {
                "multi_match": {
                    "query": query,
                    "fields": [
                        "candidate_data.name^2",
                        "candidate_data.email",
                        "candidate_data.resume_text",
                        "cover_letter",
                    ],
                    "fuzziness": "AUTO",
                }
            }
        )

    # Skills
    if skills:
        for skill in skills:
            filters.append({"term": {"candidate_data.skills": skill}})

    # Location
    if location:
        filters.append({"term": {"candidate_data.location.keyword": location}})

    # Minimum experience
    if min_experience is not None:
        filters.append(
            {"range": {"candidate_data.experience_years": {"gte": int(min_experience)}}}
        )

    # Application status
    if status:
        filters.append({"term": {"status": status}})

    body = {
        "query": {
            "bool": {
                "must": must or [{"match_all": {}}],
                "filter": filters,
            }
        },
        "sort": [{"applied_at": "desc"}],
        "size": 50,
    }

    response = client.search(
        index=APPLICATIONS_INDEX,
        body=body,
    )

    results = []

    for hit in response["hits"]["hits"]:
        source = hit["_source"]

        results.append(
            {
                "candidate_id": source["candidate_id"],
                **source.get("candidate_data", {}),
            }
        )

    return results

def list_applications(
    posted_by=None,
    job_id=None,
    status=None,
    page=1,
    page_size=20,
):
    """
    List applications for a given HR user (posted_by), optionally scoped
    to a single job, with pagination.
    """

    filters = []

    if posted_by is not None:
        filters.append({"term": {"posted_by": posted_by}})

    if job_id is not None:
        filters.append({"term": {"job_id": job_id}})

    if status:
        filters.append({"term": {"status": status}})

    body = {
        "query": {
            "bool": {
                "filter": filters or [{"match_all": {}}],
            }
        },
        "sort": [{"applied_at": {"order": "desc"}}],
        "from": (page - 1) * page_size,
        "size": page_size,
    }

    response = client.search(
        index=APPLICATIONS_INDEX,
        body=body,
    )

    hits = response["hits"]["hits"]
    total = response["hits"]["total"]["value"]

    results = []
    for hit in hits:
        source = hit["_source"]
        results.append({
            "application_id": hit["_id"],
            "job_id": source.get("job_id"),
            "job_title": source.get("job_title"),
            "candidate_id": source.get("candidate_id"),
            "status": source.get("status"),
            "applied_at": source.get("applied_at"),
            "cover_letter": source.get("cover_letter"),
            **source.get("candidate_data", {}),
        })

    return {
        "results": results,
        "total": total,
        "page": page,
        "page_size": page_size,
    }