# Python GitLab Plus
An enhanced Python client for GitLab that extends the functionality of the official `python-gitlab` package, providing better error handling, merge request management, branch operations, and more.

---

## Features
- ✅ Simplified connection to GitLab Cloud and Self-hosted instances
- ✅ Robust error handling with comprehensive logging
- ✅ **Service-based architecture** for organized functionality
- ✅ **Project management** (members, info)
- ✅ **Branch operations** (create, delete, protect, list)
- ✅ **Merge Request management** (create, merge, approve, assign, comment)
- ✅ **Pipeline operations** (trigger, monitor, wait for completion)
- ✅ **Tag management** (create, delete, list)
- ✅ **File operations** (read, create, update, delete)
- ✅ **Advanced MR features** (approval, assignment, state management)

---

## Installation
```bash
pip install python-gitlab-plus
```

---

## Configuration
The package uses environment variables for authentication and configuration:

```bash
# Required environment variables
GITLAB_ACCESS_TOKEN=your_gitlab_access_token
GITLAB_URL=https://gitlab.com  # Your GitLab instance URL (default: gitlab.com)
```

## Examples

### Basic Setup and Connection
```python
from python_gitlab_plus import GitLabClient

# Initialize GitLab client with service-based architecture
gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",  # Note: parameter name changed
    project_id="your-project-id"
)

# Access different services
project_service = gitlab_client.project
branch_service = gitlab_client.branch
mr_service = gitlab_client.merge_request
pipeline_service = gitlab_client.pipeline
tag_service = gitlab_client.tag
file_service = gitlab_client.file
```

### Branch Management
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Create a new branch
branch = gitlab_client.branch.create(
    branch_name="feature/new-feature",
    from_branch="main"
)
print(f"Created branch: {branch.name}")

# List branches
branches = gitlab_client.branch.list()
for branch in branches:
    print(f"Branch: {branch.name}")

# Protect a branch
gitlab_client.branch.protect("main")

# Delete a branch
gitlab_client.branch.delete("feature/old-feature")
```

### Merge Request Management
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Create a merge request
mr = gitlab_client.merge_request.create(
    title="Add new feature",
    from_branch="feature/new-feature",
    target="main"
)
print(f"Created MR: !{mr.iid}")

# Assign MR to a user
gitlab_client.merge_request.assign(mr.iid, "username")

# Add a comment
gitlab_client.merge_request.add_comment(mr.iid, "Great work!")

# Approve the MR
gitlab_client.merge_request.approve(mr.iid)

# Merge the MR
gitlab_client.merge_request.merge(mr.iid)
```

### Pipeline Operations
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Trigger a pipeline
pipeline = gitlab_client.pipeline.trigger(
    branch_name="main",
    variables={"ENVIRONMENT": "production"}
)
print(f"Pipeline triggered: {pipeline.id}")

# Check pipeline status
status = gitlab_client.pipeline.status(pipeline.id)
print(f"Pipeline status: {status}")

# Wait for pipeline completion
final_status = gitlab_client.pipeline.wait_until_finished(
    pipeline.id,
    check_interval=30,
    timeout=3600
)
print(f"Pipeline completed with status: {final_status}")
```

### File Operations
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Read file content
file_content = gitlab_client.file.fetch_content(
    file_path="README.md",
    ref="main"
)
print(f"File content: {file_content[:100]}...")

# Create a new file
gitlab_client.file.create(
    file_path="new-feature.py",
    branch="feature/new-feature",
    content="# New feature implementation\nprint('Hello World')",
    commit_message="Add new feature implementation"
)

# Update an existing file
gitlab_client.file.update(
    file_path="README.md",
    branch="feature/update-readme",
    content="# Updated README\nThis is the new content",
    commit_message="Update README with new information"
)

# Delete a file
gitlab_client.file.delete(
    file_path="old-file.txt",
    branch="feature/cleanup",
    commit_message="Remove old file"
)
```

### Tag Management
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Create a tag
tag = gitlab_client.tag.create(
    tag_name="v1.0.0",
    from_branch="main",
    message="Release version 1.0.0"
)
print(f"Created tag: {tag.name}")

# List tags
tags = gitlab_client.tag.list()
for tag in tags:
    print(f"Tag: {tag.name}")

# Delete a tag
gitlab_client.tag.delete("v0.9.0")
```

### Project Management
```python
from python_gitlab_plus import GitLabClient

gitlab_client = GitLabClient(
    gitlab_url="https://gitlab.com",
    access_token="your_access_token",
    project_id="your-project-id"
)

# Get project information
project_info = gitlab_client.project.get_info()
print(f"Project: {project_info.name}")
print(f"Description: {project_info.description}")

# List project members
members = gitlab_client.project.list_members()
for member in members:
    print(f"Member: {member.username}")

# Add a member
gitlab_client.project.add_member("newuser", 30)  # 30 = Developer access level

# Remove a member
gitlab_client.project.remove_member("olduser")
```

---

## 🤝 Contributing
If you have a helpful tool, pattern, or improvement to suggest:
Fork the repo <br>
Create a new branch <br>
Submit a pull request <br>
I welcome additions that promote clean, productive, and maintainable development. <br>

---

## 🙏 Thanks
Thanks for exploring this repository! <br>
Happy coding! <br>
