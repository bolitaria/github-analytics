# GitHub Analytics Dashboard

A real-time analytics system for GitHub repository activity using ClickHouse, Python, and Grafana.

## 🚀 Features

- **Real-time Data Processing**: ETL pipeline for GitHub events
- **Columnar Database**: ClickHouse for high-performance analytics
- **Interactive Dashboards**: Grafana for data visualization
- **Demo Mode**: Works without GitHub API token
- **Dockerized**: Complete containerized setup
- **Scalable Architecture**: Partitioned tables and materialized views

## 🛠️ Tech Stack

- **Backend**: Python 3.12, ClickHouse Driver, Requests
- **Database**: ClickHouse (columnar OLAP database)
- **Visualization**: Grafana
- **Containerization**: Docker, Docker Compose
- **Data Processing**: Custom ETL pipeline

## 📦 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd github-analytics
   bash

2. **Set up environment**
    make setup

3. **Run the demo**
    make demo

**Manual Setup**
    **Create virtual environment**
        python3 -m venv venv
        source venv/bin/activate
    **Install dependencies**
        pip install -r requirements.txt
    **Start services**
        make up
    **Initialize database**
        make init
    **Generate sample data**    
        make generate-sample-data
    **Run ETL process**
        make run-etl