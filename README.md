# UniFind — Campus Lost & Found Intelligence System

A full-stack web application built with **Python 3**, **Flask**, **PyMongo**, and **MongoDB**. Designed specifically as a class assessment project demonstrating core database principles: **collection-level schema validation (`$jsonSchema`)**, **CRUD operations**, **multi-stage aggregation pipelines**, and **real-time visual analytics**.

---

## 🌟 Key Highlights & Assessment Requirements Checklist

| Requirement | Implementation in UniFind | File Reference |
| :--- | :--- | :--- |
| **MongoDB as Database** | MongoDB Atlas or Local MongoDB 8.x | [`config.py`](file:///g:/Sem7/MongoDB%20Project/config.py) |
| **PyMongo Integration** | Native PyMongo `MongoClient`, BSON ObjectId, cursor queries | [`app.py`](file:///g:/Sem7/MongoDB%20Project/app.py) |
| **Database Validation** | MongoDB `$jsonSchema` collection validator (enums, min/max bounds, email regex, required fields) | [`db_validator.py`](file:///g:/Sem7/MongoDB%20Project/db_validator.py) |
| **CRUD Operations** | Complete Create, Read (filter/search/sort), Update, Claim verification, Delete | [`app.py`](file:///g:/Sem7/MongoDB%20Project/app.py) |
| **Aggregation Pipelines** | 4 pipelines: Campus Hotspots (`$group`), Resolution Rate (`$cond`, `$project`), Multi-facet KPIs (`$facet`), Turnaround Time (`$subtract`, `$avg`) | [`analytics.py`](file:///g:/Sem7/MongoDB%20Project/analytics.py) |
| **Interactive UI** | Modern responsive glassmorphic dashboard with Chart.js charts & live schema test | [`templates/index.html`](file:///g:/Sem7/MongoDB%20Project/templates/index.html) |
| **Render Ready** | `requirements.txt`, `Procfile`, and `render.yaml` configured for zero-friction deployment | [`render.yaml`](file:///g:/Sem7/MongoDB%20Project/render.yaml) |

---

## 🏗️ Architecture & Project Structure

```
MongoDB Project/
├── app.py                 # Flask server & PyMongo controller (with teacher query modifier)
├── config.py              # MongoDB client factory & Atlas TLS configuration
├── db_validator.py        # MongoDB $jsonSchema definition & index creation
├── analytics.py           # 4 Advanced MongoDB Aggregation pipelines
├── seed_data.py           # Sample campus items generator for live demos
├── requirements.txt       # Dependencies (Flask, PyMongo, dnspython, etc.)
├── Procfile               # Render web process command
├── render.yaml            # Render infrastructure specification
├── .env.example           # Template for environment variables
├── .gitignore             # Standard gitignore
├── README.md              # Documentation & presentation guide
├── templates/
│   └── index.html         # Single-page UI with CRUD modals & Chart.js analytics
└── static/
    ├── css/
    │   └── style.css      # Glassmorphism, animations, responsive design
    └── js/
        └── app.js         # Frontend controller, REST client, and chart renderer
```

---

## 🛡️ 1. MongoDB Schema Validation (`$jsonSchema`)

Unlike application-only validation, UniFind registers an explicit `$jsonSchema` inside MongoDB via `create_collection` / `collMod`:
- **Required Fields**: `title`, `description`, `type`, `category`, `campus_location`, `reporter`, `status`, `date_reported`, `created_at`, `updated_at`.
- **Enum Constraints**:
  - `type`: `["Lost", "Found"]`
  - `category`: `["Electronics", "Student ID / Cards", "Keys & Badges", "Books & Stationery", "Bags & Wallets", "Personal Accessories", "Clothing & Gear", "Others"]`
  - `campus_location`: `["Central Library", "Main Cafeteria", "Science & Engineering Block", "Auditorium Complex", "Student Center & Gym", "North Quad Lawn", "Parking Lot A", "Administrative Building"]`
  - `status`: `["Open", "Under Review", "Claimed", "Archived"]`
- **String Length Limits**: `title` (3-100 chars), `description` (5-600 chars).
- **Nested Object Validation**: `reporter.email` validated with standard RFC email regex.

> **Live Demo Feature**: In the UI's **"Schema & Validation Inspector"** tab, click **"Trigger Invalid Document Insert Test"**. The backend attempts to insert an intentionally non-compliant document, and MongoDB's database engine rejects it with a `WriteError`, proving live database-level validation to the evaluator!

---

## 🔄 2. CRUD Operations API

| Method | Endpoint | Description | MongoDB Operation |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/items` | Report a new Lost or Found item | `db.items.insert_one(doc)` |
| **GET** | `/api/items` | Query items with search, filters, and sort | `db.items.find(query).sort(...)` |
| **GET** | `/api/items/<id>` | Retrieve item details by ObjectId | `db.items.find_one({"_id": ObjectId(...)})` |
| **PUT** | `/api/items/<id>` | Update title, location, description, status | `db.items.update_one({"_id": ...}, {"$set": ...})` |
| **PATCH** | `/api/items/<id>/claim` | Record owner claim verification & notes | `db.items.update_one({"_id": ...}, {"$set": {"status": "Claimed", ...}})` |
| **DELETE** | `/api/items/<id>` | Permanently remove item from database | `db.items.delete_one({"_id": ObjectId(...)})` |

---

## 📊 3. MongoDB Aggregation Pipelines

UniFind features 4 distinct aggregation pipelines in [`analytics.py`](file:///g:/Sem7/MongoDB%20Project/analytics.py):

### Pipeline 1: Campus Activity Hotspots
- **Purpose**: Identifies which campus zones have the highest volume of lost & found incidents.
- **Stages**:
  - `$group`: Groups by `$campus_location`, uses `$cond` accumulators to count Lost vs. Found vs. Claimed.
  - `$project`: Calculates recovery percentage using `$multiply`, `$divide`, and `$round`.
  - `$sort`: Sorts locations descending by `total_items`.

### Pipeline 2: Category Recovery Resolution Rate
- **Purpose**: Analyzes which categories of items have the highest success rates for being returned to their owners.
- **Stages**:
  - `$group`: Groups by `$category` with conditional counts.
  - `$project`: Computes `(claimed / total) * 100`.
  - `$sort`: Orders categories by total volume.

### Pipeline 3: Multi-Faceted Executive KPI Overview (`$facet`)
- **Purpose**: Runs multi-dimensional analytical queries in a single database round-trip.
- **Sub-pipelines**:
  - `summary`: Overall totals (Lost, Found, Claimed, Open).
  - `by_status`: Document counts by current status.
  - `by_reporter_role`: Document counts by reporter role (Student, Faculty, Staff, Visitor).

### Pipeline 4: Recovery Turnaround Analysis
- **Purpose**: Measures the average time (in days) between an item being reported and successfully claimed.
- **Stages**:
  - `$match`: Filters for `status: "Claimed"` with valid `claim_details.claimed_date`.
  - `$project`: Uses `$subtract` to calculate millisecond difference divided by `1000 * 60 * 60 * 24`.
  - `$group`: Computes `$avg` turnaround days per category.

---

## 🚀 Quickstart: Running Locally

### Prerequisites
- Python 3.10+ installed
- MongoDB installed locally **OR** a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster URI

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Create a `.env` file (or copy `.env.example`):
```env
MONGO_URI=mongodb://localhost:27017/
DB_NAME=campus_lost_and_found
PORT=5000
SECRET_KEY=unifind-campus-secure-key-2026
```

### 3. Initialize Schema & Seed Sample Data
```bash
python seed_data.py
```

### 4. Start the Application
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🌐 Deploying on Render (Step-by-Step)

### Step 1: Set Up Free MongoDB Atlas Database
1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and sign in.
2. Create a free **M0 Shared Cluster**.
3. Under **Security > Database Access**, create a user (e.g., `unifind_user`) with password.
4. Under **Security > Network Access**, click **Add IP Address** > select **Allow Access from Anywhere (`0.0.0.0/0`)** (required for cloud hosting like Render).
5. Click **Connect** > **Drivers** > copy your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 2: Push Project to GitHub
```bash
git init
git add .
git commit -m "Initial commit of UniFind campus lost and found system"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 3: Deploy on Render
1. Log in to [render.com](https://render.com).
2. Click **New +** > **Web Service**.
3. Connect your GitHub repository.
4. Render will automatically detect Python. Fill in:
   - **Name**: `unifind-campus`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Under **Environment Variables**, add:
   - `MONGO_URI`: *Your MongoDB Atlas connection string from Step 1*
   - `DB_NAME`: `campus_lost_and_found`
   - `SECRET_KEY`: *Any random secret string*
6. Click **Create Web Service**.
7. Once deployed, open your Render URL, click **"Seed Demo Data"** at the top right, and the entire app will be live and populated!

---

## 🎤 Class Presentation Talking Points (Script)

1. **Introduction (30s)**:
   > *"Good morning professor and classmates. For my MongoDB project, I built UniFind—an intelligent Campus Lost & Found tracking system. It solves a real daily university problem while demonstrating collection-level validation, complete CRUD, and advanced aggregation pipelines using PyMongo."*

2. **Database Schema & Validation (60s)**:
   > *"Switch to the **Schema Inspector** tab. Here, we implemented native MongoDB `$jsonSchema` validation directly on the database engine. It enforces required fields, campus location and category enums, and email regex patterns. Watch what happens when I click 'Trigger Invalid Document Insert Test'—the MongoDB engine throws a WriteError and rejects the invalid record."*

3. **CRUD Workflow (60s)**:
   > *"Switch to the **Items Directory** tab. We can filter in real time by category, campus zone, or status, and use text index searching. To show Create, click 'Report Item'. To show Update, we can click on any item, edit details, or use the quick 'Mark as Claimed' action to record claimant verification. To show Delete, click 'Delete from MongoDB'."*

4. **Aggregation Pipelines (60s)**:
   > *"Switch to the **Aggregation Pipelines** tab. All visualizations are powered by multi-stage pipelines in `analytics.py`.
   > - Hotspots uses `$group` and `$sort` to reveal where items are lost most frequently (e.g. Library and Cafeteria).
   > - Category resolution rate uses `$cond` and `$project` to calculate return percentages.
   > - Turnaround time uses `$subtract` on dates to compute days to recovery.
   > - And our top KPI ribbon runs a single `$facet` pipeline that aggregates overall metrics in one trip."*

5. **Live Query Modification in Code (60s)**:
   > *"If asked to modify a query or filter by something specific, open `app.py` lines 50–60 in VS Code. Change `TEACHER_ITEMS_FILTER` (e.g. to `{"campus_location": "Central Library"}`), press Ctrl+S, and refresh the browser—the data updates instantly to demonstrate live PyMongo querying!"*


