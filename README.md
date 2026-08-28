# Job Board Microservices Platform

A robust, event-driven microservices architecture for a job board platform, consisting of a Job Service and a Candidate Service.

## How to Run This Project Locally

### Prerequisites
- [Docker](https://www.docker.com/get-started) and Docker Compose installed on your system.

### Setup Instructions

1. **Environment Variables Configuration**
   You need to set up the environment variables for the root and the microservices.
   Copy the sample environment files and configure them (you can leave the default values for local development):

   ```bash
   # Root environment variables
   cp .env.sample .env

   # Job Service environment variables
   cp job-service/.env.sample job-service/.env

   # Candidate Service environment variables
   cp candidate-service/.env.sample candidate-service/.env
   ```

2. **Build and Run the Containers**
   Use Docker Compose to build the images and start all services (databases, message brokers, caching, backend APIs, background workers, and consumers).

   ```bash
   docker-compose up --build
   ```
   *(Add `-d` to run in detached mode).*

3. **Accessing the Services**
   Once the containers are up and running and health checks pass, the services will be available at:
   - **Job Service API**: `http://localhost:8000`
   - **Candidate Service API**: `http://localhost:8777`

### Stopping the Project
To stop the containers and free up resources:
```bash
docker-compose down
```

---

## About the Project Architecture

This project adopts a modern microservices architecture designed for scalability, loose coupling, and high performance. The system is split into two primary backend services:

1. **Job Service**: Responsible for managing HR profiles, creating and managing job postings, and reviewing candidate applications.
2. **Candidate Service**: Responsible for managing candidate profiles, handling the job application process from the candidate's perspective, and providing powerful job search capabilities.

### Independent Data Storage
Each microservice maintains its own distinct PostgreSQL database (`job-db` and `candidate-db`). This adheres to the microservices database-per-service pattern, preventing tight coupling at the data layer and allowing each service to evolve its schema independently.

### How Kafka is Used (Event-Driven Architecture)
To keep the services decoupled while maintaining data consistency across boundaries, the platform uses **Apache Kafka** (running in KRaft mode) for asynchronous, event-driven communication.

- **Publishing Events**: When a state-changing action occurs (e.g., an HR user creates a new job in the Job Service, or a candidate submits an application in the Candidate Service), the originating service publishes an event to a Kafka topic.
- **Consuming Events**: Independent Kafka consumers (`job-consumer` and `candidate-consumer`) run alongside the web APIs. They listen to these topics and react accordingly. For example, if a job is updated in the Job Service, the Candidate Service consumer can update its own read-models or search indexes without requiring synchronous HTTP calls between the services.

### How OpenSearch is Used
**OpenSearch** is integrated to provide lightning-fast, highly relevant full-text search capabilities, significantly outperforming standard relational database queries for complex text analysis.

- **Indexing**: When data (like a Job Posting or a Candidate Profile) is created or modified, it needs to be indexed in OpenSearch. To prevent this from slowing down the HTTP API responses, the heavy lifting of indexing is offloaded to background tasks.
- **Background Workers**: **Celery** (backed by **Redis** as a message broker) manages these background tasks (`job-worker` and `candidate-worker`). The API immediately returns a success response to the user, while Celery asynchronously pushes the data to OpenSearch.
- **Searching**: When a user performs a search (e.g., a candidate searching for jobs by specific skills or keywords), the Candidate Service queries the OpenSearch cluster directly to retrieve highly accurate results instantly.
