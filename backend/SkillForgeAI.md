# SkillForgeAI

SkillForgeAI is an AI-powered backend system designed to facilitate personalized learning, skill assessment, and adaptive roadmaps for users. The project is structured as a modular Python application, leveraging FastAPI and modern best practices for maintainability and scalability.

## Project Structure

- **app/**: Main application package
  - **ai/**: AI adapters, clients, and prompt templates
  - **api/**: FastAPI route handlers for authentication, diagnosis, learning state, roadmaps, tasks, and users
  - **core/**: Core configuration, constants, logging, and exception handling
  - **db/**: Database models and repository classes for data access
  - **domain/**: Domain logic for roadmap transitions, validation, and business entities
  - **schemas/**: Pydantic models for request/response validation and serialization
  - **services/**: Business logic and service layer for AI, authentication, diagnosis, evaluation, learning state, mentoring, roadmaps, skills, tasks, and users
  - **tests/**: Unit and integration tests for core modules and APIs
  - **utils/**: Utility functions for security and time management
- **pyproject.toml**: Project metadata and dependencies
- **requirements.txt**: List of Python dependencies
- **README.md**: Project overview and setup instructions


## API Endpoints

### Authentication (`/auth`)

The authentication module handles user registration, login, logout, and token management using JWTs stored in HTTP-only cookies.

- **POST /auth/register**
  - **Description**: Registers a new user with email, password, and name.
  - **Request Body**: `RegisterRequest` (email, password, name).
  - **Response**: Sets `access_token` and `refresh_token` cookies. Returns success message.
  - **Errors**: 400 (Registration failed), 500 (Internal server error).

- **POST /auth/login**
  - **Description**: Authenticates a user and issues tokens.
  - **Request Body**: `LoginRequest` (email, password).
  - **Response**: Sets `access_token` and `refresh_token` cookies. Returns user setup status.
  - **Errors**: 401 (Invalid credentials).

- **POST /auth/logout**
  - **Description**: Logs out the user by clearing authentication cookies.
  - **Response**: Clears `access_token` and `refresh_token` cookies.

- **POST /auth/refresh**
  - **Description**: Refreshes the access token using a valid refresh token.
  - **Request**: Requires `refresh_token` cookie.
  - **Response**: Sets a new `access_token` cookie.
  - **Errors**: 401 (Missing or invalid refresh token).

### User Management (`/users`)

Manages user profiles and initial setup.

- **GET /users/current_user**
  - **Description**: Retrieves basic information about the currently authenticated user.
  - **Response**: User ID, email, and setup completion status.

- **POST /users/setup_user**
  - **Description**: Completes the initial user setup, including skill assessment.
  - **Request Body**: `UserSetupRequest` (skills, goals, etc.).
  - **Response**: Updated user profile data.

- **GET /users/general_profile**
  - **Description**: Retrieves the full profile of the authenticated user.
  - **Response**: ID, email, name, setup status, and creation timestamp.

### Diagnosis (`/diagnose`)

Provides AI-driven skill diagnosis.

- **POST /diagnose/**
  - **Description**: Analyzes a provided set of skills to identify weaknesses.
  - **Request Body**: Dictionary of skills and their levels.
  - **Response**: List of identified weak skills.

### Learning State (`/learning_state`)

Manages the user's evolving learning state, including skill vectors and history.

- **POST /learning_state/init**
  - **Description**: Initializes a new learning state for the user, optionally linking to a roadmap.
  - **Query Params**: `roadmap_id` (optional).
  - **Response**: The created learning state object.

- **GET /learning_state/**
  - **Description**: Retrieves the current user's learning state.
  - **Response**: `UserLearningState` object containing skill vectors and history.

- **PATCH /learning_state/**
  - **Description**: Updates specific fields in the user's learning state.
  - **Request Body**: Dictionary of fields to update.
  - **Response**: The updated learning state.

### Roadmap (`/roadmap`)

Handles the creation and retrieval of personalized learning roadmaps.

- **GET /roadmap** (also **/roadmap/current**)
  - **Description**: Retrieves the currently active roadmap for the user.
  - **Response**: `RoadmapState` object.
  - **Errors**: 404 (Active roadmap not found), 500 (Roadmap corrupted).

- **POST /roadmap/init**
  - **Description**: Generates and initializes a new roadmap based on the user's goal.
  - **Response**: The newly created `RoadmapState`.
  - **Errors**: 400 (Roadmap already exists).

- **GET /roadmap/latest**
  - **Description**: Retrieves the most recent roadmap, whether active or completed.
  - **Response**: `RoadmapState` object.
  - **Errors**: 404 (No roadmap exists).

### Roadmap Slot (`/roadmap/slot`)

Manages individual learning slots within a roadmap.

- **POST /roadmap/slot/start**
  - **Description**: Starts a specific slot in the roadmap, changing its status to `in_progress`.
  - **Query Params**: `slot_id`.
  - **Response**: Returns the started task instance and an AI-generated hint.
  - **Errors**: 404 (Slot not found), 409 (Another slot in progress), 500 (Configuration error).

### Submissions (`/submissions`)

Handles the submission and evaluation of tasks.

- **POST /submissions**
  - **Description**: Submits a solution for an active task instance. Triggers AI evaluation and roadmap updates.
  - **Request Body**: `TaskSubmissionCreate` (slot_id, task_instance_id, payload).
  - **Response**: `TaskSubmission` object including evaluation results.
  - **Errors**: 400 (Slot not in progress), 409 (Duplicate submission or mismatch), 423 (Roadmap locked).

### Tasks (`/tasks`)

- **GET /tasks/**
  - **Description**: A protected endpoint for retrieving task-related information (currently a placeholder).
  - **Response**: User ID and message.



---

## Key Features

- **User Authentication**: Secure registration, login, logout, and token refresh endpoints
- **Skill Diagnosis**: AI-driven diagnosis of user skills and learning needs
- **Personalized Roadmaps**: Dynamic generation and management of learning roadmaps
- **Task Management**: Creation, submission, and evaluation of learning tasks
- **Skill Tracking**: Evidence and history tracking for user skill progression
- **Mentor Integration**: AI mentor services for guidance and feedback

## Technologies Used

- Python 3.x
- FastAPI
- Pydantic
- SQLAlchemy (assumed for DB layer)
- JWT for authentication
- Pytest for testing

## Getting Started

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables** as needed (see `app/core/config.py`)
4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```
5. **Run tests**
   ```bash
   pytest app/tests
   ```

## Folder Overview

| Folder/File         | Purpose                                              |
|--------------------|------------------------------------------------------|
| app/ai/            | AI adapters, clients, and prompt templates           |
| app/api/           | API endpoints for all major features                 |
| app/core/          | Core configuration, constants, and logging           |
| app/db/            | Database models and repositories                     |
| app/domain/        | Domain logic and business entities                   |
| app/schemas/       | Pydantic models for data validation                  |
| app/services/      | Service layer for business logic                     |
| app/tests/         | Unit and integration tests                           |
| app/utils/         | Utility functions                                    |
| pyproject.toml     | Project metadata and dependencies                    |
| requirements.txt   | Python dependencies                                  |
| README.md          | Project overview and setup instructions              |

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.
