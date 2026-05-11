
# QuickNotes ⚡
### A Serverless Note Management Platform on AWS

> Cloud Computing Course Project — Rayaan Hassan (2023598) & Murtaza Ali Khan (2023472)

---

## What is QuickNotes?

QuickNotes is a fully serverless REST API and web application that allows users to create, manage, and store personal notes with file attachments — all hosted on AWS. There is no traditional server. Every component is a managed AWS service that scales automatically and requires zero infrastructure maintenance.

---

## Live Demo

| Resource | Link |
|---|---|
| **Web Application** | [QuickNotes App](http://quicknotes-files-rayaanhassan.s3-website.eu-north-1.amazonaws.com) |
| **API Base URL** | `https://u02mglup0j.execute-api.eu-north-1.amazonaws.com/prod` |

> All API requests require the `x-api-key` header.

---

## AWS Architecture

```
CLIENT (Browser / Postman)
        │
        │  HTTPS + API Key
        ▼
┌─────────────────┐
│   API Gateway   │  ── validates key, routes request
└────────┬────────┘
         │  Lambda Proxy Event
         ▼
┌─────────────────┐        ┌──────────────┐
│   AWS Lambda    │───────▶│   DynamoDB   │  note records
│   (8 functions) │        └──────────────┘
└────────┬────────┘
         │                 ┌──────────────┐
         ├────────────────▶│  Amazon S3   │  file attachments
         │  pre-signed URL └──────────────┘
         │
         ├────────────────▶  Amazon SNS   ──▶  Email notification
         │
         └────────────────▶  CloudWatch   ──▶  Logs + Alarms
```

---

## AWS Services Used

| Service | Role |
|---|---|
| **API Gateway** | Exposes all 9 REST endpoints with API key authentication and CORS |
| **AWS Lambda** | 8 independent Python 3.12 functions — one per operation |
| **Amazon DynamoDB** | Serverless NoSQL database storing all note records |
| **Amazon S3** | Private file attachment storage via pre-signed URLs |
| **Amazon SNS** | Pub/sub email notifications on note creation |
| **CloudWatch** | Lambda monitoring, log groups, and error-rate alarms |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/notes` | Create a note — triggers SNS email |
| `GET` | `/notes` | List all notes sorted newest first |
| `GET` | `/notes/{id}` | Get a single note by ID |
| `PUT` | `/notes/{id}` | Update title and/or content |
| `DELETE` | `/notes/{id}` | Delete a note permanently |
| `GET` | `/notes/search?search=keyword` | Case-insensitive keyword search |
| `GET` | `/notes/{id}/upload-url` | Get pre-signed S3 URL for file upload |
| `PUT` | S3 pre-signed URL | Upload file directly to S3 |
| `GET` | `/notes/{id}/download-url` | Get pre-signed S3 URL for file download |

---

## Project Structure

```
quicknotes/
├── lambda/
│   ├── createNote.py        # Create note + SNS notification
│   ├── getNote.py           # Get single note by ID
│   ├── listNotes.py         # List all notes
│   ├── updateNote.py        # Update note title/content
│   ├── deleteNote.py        # Delete a note
│   ├── searchNotes.py       # Case-insensitive keyword search
│   ├── getUploadUrl.py      # Generate S3 pre-signed PUT URL
│   └── getDownloadUrl.py    # Generate S3 pre-signed GET URL
└── frontend/
    ├── index.html           # Main application UI
    └── about.html           # Architecture & KPI dashboard
```

---

## How to Deploy

### Prerequisites
- AWS account
- AWS CLI configured
- Postman for testing

### Step 1 — DynamoDB
1. Create table named `Notes`
2. Partition key: `noteId` (String)

### Step 2 — S3
1. Create bucket: `quicknotes-files-<yourname>`
2. Block all public access: ON
3. Add CORS policy:
```json
[{
  "AllowedHeaders": ["*"],
  "AllowedMethods": ["PUT", "GET"],
  "AllowedOrigins": ["*"],
  "ExposeHeaders": []
}]
```

### Step 3 — IAM Role
Create role `LambdaNotesRole` with these policies:
- `AmazonDynamoDBFullAccess`
- `AmazonS3FullAccess`
- `AmazonSNSFullAccess`
- `CloudWatchLogsFullAccess`

### Step 4 — Lambda Functions
For each `.py` file in `/lambda`:
1. Create Lambda function — Python 3.12, LambdaNotesRole
2. Paste the code and click Deploy
3. Add environment variables:
   - `createNote` → `SNS_TOPIC_ARN`
   - `getUploadUrl` and `getDownloadUrl` → `BUCKET_NAME`

### Step 5 — SNS
1. Create Standard topic: `QuickNotesNotifications`
2. Create email subscription and confirm via email
3. Copy Topic ARN and add to `createNote` environment variables

### Step 6 — API Gateway
1. Create REST API: `QuickNotesAPI`
2. Create resources and methods with Lambda proxy integration:
   - `POST /notes` → createNote
   - `GET /notes` → listNotes
   - `GET /notes/{id}` → getNote
   - `PUT /notes/{id}` → updateNote
   - `DELETE /notes/{id}` → deleteNote
   - `GET /notes/search` → searchNotes
   - `GET /notes/{id}/upload-url` → getUploadUrl
   - `GET /notes/{id}/download-url` → getDownloadUrl
3. Enable CORS on all resources
4. Create API key and usage plan
5. Set API Key Required to `true` on all methods
6. Deploy to stage: `prod`

### Step 7 — Frontend
1. Open `frontend/index.html`
2. Replace `YOUR_API_KEY_HERE` with your actual API key
3. Upload both HTML files to S3
4. Enable static website hosting on the bucket

### Step 8 — CloudWatch Alarm
1. CloudWatch → Create Alarm
2. Metric: Lambda → createNote → Errors
3. Threshold: greater than 5 in 1 minute
4. Action: notify `QuickNotesNotifications` SNS topic

---

## Testing with Postman

Set these collection variables:

| Variable | Value |
|---|---|
| `baseUrl` | `https://u02mglup0j.execute-api.eu-north-1.amazonaws.com/prod` |
| `apiKey` | your API key |

Run requests in this order:
1. `POST /notes` — create a note, copy the `noteId`
2. `GET /notes` — confirm note appears in list
3. `GET /notes/{id}` — retrieve by ID
4. `PUT /notes/{id}` — update title or content
5. `GET /notes/search?search=keyword` — search by keyword
6. `GET /notes/{id}/upload-url?filename=test.pdf` — get upload URL
7. `PUT` to S3 URL — upload a file using Body → Binary
8. `GET /notes/{id}/download-url` — get download URL, open in browser
9. `DELETE /notes/{id}` — delete the note

---

## Key Design Decisions

**Pre-signed URLs for file handling**
Lambda never handles file bytes. It generates a short-lived authenticated URL and the client uploads or downloads directly to S3. This eliminates Lambda memory limits on file size, reduces execution time, and is the production pattern used by Dropbox and Google Drive.

**Decoupled SNS notifications**
Lambda publishes one event to an SNS topic rather than calling an email API directly. Additional notification channels such as SMS or mobile push can be added as subscribers without modifying any application code.

**API key authentication**
Requests without a valid `x-api-key` header are rejected at the API Gateway layer before any Lambda function is invoked, keeping costs low and protecting backend resources.

---

## Team

| Name | ID | Role |
|---|---|---|
| Rayaan Hassan | 2023598 | Backend · Lambda · DynamoDB · S3 · SNS |
| Murtaza Ali Khan | 2023472 | API Gateway · Testing · CloudWatch · Hosting |

---

*Cloud Computing Course · 2026*
