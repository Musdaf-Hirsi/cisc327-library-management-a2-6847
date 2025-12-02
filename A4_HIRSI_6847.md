# Assignment 4 – End-to-End Testing and Application Containerization
**Course:** CISC/CMPE 327 – Software Quality Assurance  
**Student:** Musdaf Hirsi  
**Student ID:** 20376847  
**Date:** 01 December 2025  

---

## 1. Introduction
This assignment extends the Library Management System by adding browser-based E2E testing with Playwright and containerizing the Flask app with Docker. The goal is to cover realistic user flows, ensure reproducible builds, and demonstrate push–pull–run from Docker Hub.

---

## 2. E2E Testing Approach
**Tool:** Playwright (Python, Chromium, headless).  
**Server setup:** Tests start `python app.py`, wait for `http://127.0.0.1:5000/catalog`, and reset `library.db` at session start.

**User flows tested:**
1. Add a new book via `/add_book`, verify it appears in the catalog, borrow it, confirm success flash, and see availability become unavailable.  
2. Add a book, search for it via `/search`, borrow from the results table, and verify availability updates in the catalog.

**Assertions:** redirections, presence of titles, flash messages, availability text, and table rows for the target books.

**Example command:**
```bash
python -m pytest tests/test_e2e.py
```

---

## 3. Execution Instructions
### Run E2E tests
```bash
python -m venv .a4env
source .a4env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
python -m pytest tests/test_e2e.py -q
```

### Run full suite
```bash
python -m pytest -q
```

### Build Docker image
```bash
docker build -t library-app .
```

### Run the container
```bash
docker run -p 5000:5000 library-app
```

### Run the pulled Docker Hub image (example)
```bash
docker run -p 5000:5000 musdaf/library-app:v1
```

---

## 4. Test Case Summary
| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Add book via `/add_book` (title, author, ISBN, copies=1) | Book appears in catalog with `1/1 Available`. |
| 2 | Borrow the added book with patron ID | Flash shows “Successfully borrowed”; row shows “Not Available”. |
| 3 | Search for the added book on `/search` | The added title appears in results. |
| 4 | Borrow from search results | Flash includes book title; catalog availability decreases (e.g., `1/2 Available`). |

---

## 5. Dockerization Process
Image is based on `python:3.11-slim`, installs `requirements.txt`, copies the app, initializes SQLite on start, and runs Flask on port 5000.

**Commands:**
```bash
docker build -t library-app .
docker run -p 5000:5000 library-app
```

Screenshots: `screenshots/Docker Build Success.png`, `screenshots/Running the container.png`.

---

## 6. Docker Hub Deployment
Demonstrated push, delete, pull, and run.

**Commands:**
```bash
# Tag and push
docker tag library-app musdaf/library-app:v1
docker push musdaf/library-app:v1

# Remove local image
docker rmi musdaf/library-app:v1

# Pull and run
docker pull musdaf/library-app:v1
docker run -p 5000:5000 musdaf/library-app:v1
```

Screenshots: `screenshots/push to docker.png`, `screenshots/remove local image.png`, `screenshots/pulling from the docker.png`.

---

## 7. Challenges and Reflections
- Needed to wait for Flask readiness in Playwright to avoid flaky starts; solved with HTTP retries.  
- Ensured fresh SQLite state by deleting `library.db` per test session.  
- Container entrypoint auto-inits DB and sample data, so runs are reproducible without manual seeding.

---

## 8. Conclusion
Implemented automated browser E2E tests, containerized the Flask app, and completed Docker Hub push–pull–run. The application runs correctly both locally and from the Docker Hub image, meeting assignment requirements.
