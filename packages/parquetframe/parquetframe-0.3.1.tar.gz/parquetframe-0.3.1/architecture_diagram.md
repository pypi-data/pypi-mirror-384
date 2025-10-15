# ParquetFrame Architecture Diagram

```mermaid
graph TB
    %% User Interface Layer
    CLI[CLI Interface<br/>cli.py] --> Interactive[Interactive Mode<br/>interactive.py]
    CLI --> BatchOps[Batch Operations<br/>run, info, benchmark]

    %% Core Library Layer
    Core[ParquetFrame Core<br/>core.py] --> BackendSwitch{Backend Selection}
    BackendSwitch --> Pandas[Pandas Backend]
    BackendSwitch --> Dask[Dask Backend]

    %% Feature Modules
    Core --> SQL[SQL Module<br/>sql.py]
    Core --> Bio[BioFrame Integration<br/>bio.py]
    Core --> Workflows[YAML Workflows<br/>workflows.py]

    %% AI & Data Context
    AI[LLM Agent<br/>ai/agent.py] --> Ollama[Ollama LLM]
    AI --> Prompts[Prompt Engineering<br/>ai/prompts.py]
    DataContext[DataContext<br/>datacontext/] --> ParquetContext[Parquet Context]
    DataContext --> DatabaseContext[Database Context]
    Interactive --> AI
    Interactive --> DataContext

    %% Performance & Benchmarking
    Benchmark[Performance Benchmarking<br/>benchmark.py] --> SystemMetrics[System Memory<br/>psutil]
    Core --> Benchmark

    %% Supporting Modules
    History[Session History<br/>history.py] --> Interactive
    Exceptions[Error Handling<br/>exceptions.py] --> Core
    WorkflowHistory[Workflow History<br/>workflow_history.py] --> Workflows
    WorkflowViz[Workflow Visualization<br/>workflow_visualization.py] --> Workflows

    %% External Dependencies
    SQL --> DuckDB[(DuckDB)]
    Bio --> BioFrame[(BioFrame)]
    Pandas --> PyArrow[(PyArrow)]
    Dask --> PyArrow
    DataContext --> SQLAlchemy[(SQLAlchemy)]

    %% Data Storage
    ParquetFiles[(Parquet Files)] --> Core
    Databases[(SQL Databases)] --> DatabaseContext

    style Core fill:#e1f5fe
    style CLI fill:#f3e5f5
    style AI fill:#fff3e0
    style DataContext fill:#e8f5e8
    style Benchmark fill:#fce4ec
```

## Architecture Summary

### Core Components

1. **ParquetFrame Core** (`core.py`)
   - Central DataFrame wrapper with intelligent backend switching
   - Automatic pandas/Dask selection based on file size and system memory
   - Property-based backend control with `islazy` flag

2. **CLI Interface** (`cli.py`)
   - Rich command-line interface with multiple commands
   - Batch processing (`run`), interactive mode, file info, benchmarking
   - Integration with all core features

3. **Interactive Mode** (`interactive.py`)
   - REPL-style interface for data exploration
   - AI-powered natural language queries
   - Session persistence and history tracking

4. **AI Integration** (`ai/`)
   - LLM agent for natural language to SQL conversion
   - Sophisticated prompt engineering with self-correction
   - Local inference via Ollama

5. **DataContext System** (`datacontext/`)
   - Unified abstraction for different data sources
   - Parquet data lakes and SQL database integration
   - Schema discovery and query execution

### Feature Modules

- **SQL Support** (`sql.py`) - DuckDB-based SQL queries on DataFrames
- **BioFrame Integration** (`bio.py`) - Genomic interval operations with parallel processing
- **YAML Workflows** (`workflows.py`) - Declarative data processing pipelines
- **Performance Benchmarking** (`benchmark.py`) - Comprehensive performance testing suite

### Supporting Infrastructure

- **Error Handling** (`exceptions.py`) - Comprehensive exception hierarchy
- **Session History** (`history.py`) - Command tracking and reproducibility
- **Workflow Management** (`workflow_history.py`, `workflow_visualization.py`)
