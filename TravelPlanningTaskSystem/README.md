# TATA - AI Travel Planning Assistant

TATA is an intelligent travel planning assistant that helps users create personalized travel itineraries. The system combines advanced AI agents with comprehensive travel databases to provide detailed travel recommendations including accommodations, attractions, restaurants, and transportation.

## ✨ Key Features

- **Intelligent Travel Planning**: AI-powered itinerary generation based on user preferences
- **Multi-Modal Support**: Integration with various travel services and databases
- **Real-time Data**: Up-to-date information on accommodations, attractions, and restaurants  
- **Interactive Frontend**: Modern React-based user interface
- **Flexible Architecture**: Modular agent system supporting various travel planning scenarios
- **Database Integration**: Comprehensive travel data from multiple sources

## 🛠 Prerequisites

- **Version Control**: Git
- **Development Environment**: Python 3.8+, Node.js 16+, MySQL 8.0+
- **Containerization**: Docker and Docker Compose (for containerized deployment)

---

## 🚀 Manual Installation & Setup

Follow these steps to set up TATA on your local development environment.

### 1. Clone Repository

```bash
git clone <repository-url>
cd TATA
```

### 2. Backend Setup

```bash
# 1. Create and activate Python virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "import fastapi, langchain, sqlalchemy; print('Backend dependencies installed successfully')"
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd tata-frontend

# Install Node.js dependencies
npm install

# Return to root directory
cd ..
```

### 4. Database Configuration

1. **Ensure MySQL 8.0+ is installed and running**
2. **Configure environment variables**:
   - Copy `agent/.env.example` to `.env` and update database configuration (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`) to match your MySQL setup
3. **Initialize database**:
   ```bash
   python setup_database.py
   ```

### 5. Download travelplanner database
Download the database (https://drive.google.com/file/d/1pF1Sw6pBmq2sFkJvm-LzJOqrmfWoQgxE/view?usp=drive_link) and unzip it to the TravelPlanner directory (i.e., your/path/TravelPlanner).

### 6. Start Services

You need to run two terminal windows for the backend and frontend services.

**Terminal 1: Start Backend**
```bash
# (ensure virtual environment is activated)
cd server
python main.py
```
> Backend API will be available at `http://localhost:8000`

**Terminal 2: Start Frontend**
```bash
cd tata-frontend
npm start
```
> Frontend application will be available at `http://localhost:3000`

---

## 🐳 Docker Installation & Setup (Recommended)

Use Docker for a simplified, containerized deployment that includes all services and dependencies.

### 1. Clone Repository

```bash
git clone <repository-url>
cd TATA
```

### 2. Environment Configuration

Configure your API keys and environment variables for the project.

```bash
# Copy environment template
cp agent/.env.example agent/.env

# Edit .env file with your API keys
nano agent/.env
```

### 3. Build and Start Services

```bash
# This command builds and starts all services (database, backend, frontend)
sudo docker-compose up -d --build
```

### 4. Initialize Database

Once the containers are running, initialize the database with the required schema and data.

```bash
# 1. Copy SQL schema to MySQL container
sudo docker cp database/init.sql tata-mysql:/tmp/init.sql

# 2. Execute SQL schema in MySQL container to create database structure
sudo docker-compose exec mysql mysql -u root -p123456 tata -e "source /tmp/init.sql"
```

### 5. Verify Installation

```bash
# 1. Check that all containers are running (status should show 'Up')
sudo docker-compose ps

# 2. Verify database initialization
sudo docker-compose exec mysql mysql -u root -p123456 tata -e "SHOW TABLES; SELECT COUNT(*) FROM users;"
```
> You should see tables created and user count displayed, confirming successful database initialization.

### 6. Access Services

- **Frontend Application**: `http://<your-server-ip>:3001`
- **Backend API**: `http://<your-server-ip>:8000`
- **Metabase Analytics**: `http://<your-server-ip>:3000`

## 📊 Project Structure

```
TATA/
├── agent/                          # Core AI agent system
│   ├── core/                       # Core agent functionality
│   │   ├── agent.py               # Main agent orchestrator
│   │   ├── nodes/                 # Processing nodes
│   │   └── prompts.py             # AI prompts and templates
│   ├── tool/                      # Travel planning tools
│   │   ├── travel_planner.py      # Main travel planning logic
│   │   ├── accommodation_planner.py # Hotel/lodging recommendations
│   │   ├── attraction_planner.py   # Tourist attraction suggestions
│   │   └── restaurant_planner.py   # Restaurant recommendations
│   └── TravelPlanner/             # Enhanced travel planning engine
├── tata-frontend/                 # React frontend application
│   ├── src/
│   │   └── components/
│   │       └── TATAStoryAssistant/ # Main UI components
├── server/                        # Backend API server
├── database/                      # Database schemas and migrations
└── docs/                         # Project documentation
```

