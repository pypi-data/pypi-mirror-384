# FastAPI Launch

A FastAPI starter project with async MySQL database connection, migrations, and authentication.

## Features

- Async MySQL database connection
- Database migrations with Alembic
- Authentication system
- API documentation with Swagger/OpenAPI

## Setup Instructions

### 1. Install uv

```bash
pip install uv
```

### 2. Install Dependencies (from pyproject.toml)

- App deps only:

```bash
uv sync
```

- Include dev tools (ruff, basedpyright):

```bash
uv sync --all-groups
```

### 3. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_NAME=your_db_name
JWT_SECRET_KEY=your_jwt_secret
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### 4. Database Setup

Create your MySQL database and ensure it's accessible with the credentials in your `.env` file.

### 5. Database Migrations

Generate initial migrations (if needed):

```bash
alembic revision --autogenerate -m "Initial migration"
```

Run migrations:

```bash
alembic upgrade head
```

Generate new migrations when you modify models:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### 6. Start the Server

```bash
python run.py
```

The server will start on `http://localhost:8000` by default.

## Linting & Type Checking

### VS Code Extensions Required

For proper linting and type checking to work, install these VS Code extensions:

- `charliermarsh.ruff` - Ruff linter and formatter
- `anysphere.cursorpyright` - Type checking with Pyright

### VS Code Settings

Add the following to your VS Code `settings.json`:

```json
{
  "cursorpyright.analysis.autoImportCompletions": true,
  "cursorpyright.analysis.typeCheckingMode": "recommended",
  "python.languageServer": "None",
  "ruff.configurationPreference": "filesystemFirst",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.insertSpaces": true,
    "editor.tabSize": 4,
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    },
    "editor.inlayHints.enabled": "offUnlessPressed"
  }
}
```

### Command Line Tools

- Ruff (lint):

```bash
ruff check
```

- Ruff (auto-fix + format):

```bash
ruff check --fix
ruff format
```

- Pyright (basedpyright):

```bash
uv run basedpyright
```

## Development

- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
