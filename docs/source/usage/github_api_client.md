# GitHub API Client

The `GitHubAPIClient` provides a typed, feature-rich wrapper around the GitHub REST and GraphQL APIs with built-in rate limit handling, pagination support, and GitHub Enterprise Server (GHES) compatibility.

## Features

- **Typed API access**: Full type hints for better IDE support and type safety
- **Automatic rate limit handling**: Detects rate limits and waits automatically (configurable)
- **Exponential backoff**: Retries failed requests with configurable backoff
- **Conditional requests**: ETag support for efficient caching
- **GHES support**: Custom base URL for GitHub Enterprise Server
- **Pagination helpers**: Simplified iteration over paginated results
- **GraphQL support**: Execute GraphQL queries with typed responses

## Basic Usage

### Initialize the Client

```python
from github_action_toolkit import GitHubAPIClient

# Using environment variable (GITHUB_TOKEN)
client = GitHubAPIClient()

# Or with explicit token
client = GitHubAPIClient(token="ghp_your_token_here")

# For GitHub Enterprise Server
client = GitHubAPIClient(
    token="ghp_your_token",
    base_url="https://github.mycompany.com/api/v3"
)
```

### Get Repository Information

```python
# Get a repository
repo = client.get_repo("owner/repo")
print(f"Repository: {repo.full_name}")
print(f"Stars: {repo.stargazers_count}")
print(f"Language: {repo.language}")
```

### Get User Information

```python
# Get authenticated user
user = client.get_user()
print(f"Logged in as: {user.login}")

# Get specific user
user = client.get_user("octocat")
print(f"User: {user.name}")
```

### Get Organization Information

```python
org = client.get_organization("github")
print(f"Organization: {org.name}")
print(f"Members: {org.public_members_count}")
```

## Pagination

The client provides a convenient method to iterate through paginated results:

```python
# Paginate through issues
repo = client.get_repo("owner/repo")
for issue in client.paginate(repo.get_issues):
    print(f"Issue #{issue.number}: {issue.title}")

# Paginate with parameters
for issue in client.paginate(repo.get_issues, state="closed", labels=["bug"]):
    print(f"Closed bug #{issue.number}: {issue.title}")

# Paginate through pull requests
for pr in client.paginate(repo.get_pulls, state="open"):
    print(f"PR #{pr.number}: {pr.title}")
```

## Rate Limit Handling

The client automatically handles rate limits:

```python
# Automatic waiting (default behavior)
client = GitHubAPIClient(token="ghp_token", rate_limit_wait=True)

# Without automatic waiting (raises RateLimitError)
client = GitHubAPIClient(token="ghp_token", rate_limit_wait=False)

# Check current rate limit status
rate_limit = client.get_rate_limit()
print(f"Core API: {rate_limit['core']['remaining']}/{rate_limit['core']['limit']}")
print(f"Search API: {rate_limit['search']['remaining']}/{rate_limit['search']['limit']}")
print(f"GraphQL API: {rate_limit['graphql']['remaining']}/{rate_limit['graphql']['limit']}")
```

## Raw HTTP Requests

For advanced use cases, you can make raw HTTP requests:

```python
# Simple GET request
response = client.request("GET", "/user/repos")
repos = response.json()

# POST request with data
response = client.request(
    "POST",
    "/repos/owner/repo/issues",
    json={
        "title": "Issue title",
        "body": "Issue description",
        "labels": ["bug"]
    }
)
issue = response.json()
```

## Conditional Requests with ETags

Use ETags to reduce bandwidth and API calls:

```python
# First request - gets data and caches ETag
response1 = client.request("GET", "/repos/owner/repo", use_etag=True)
data1 = response1.json()

# Second request - uses cached data if not modified (304)
response2 = client.request("GET", "/repos/owner/repo", use_etag=True)
data2 = response2.json()  # Returns cached data if unchanged
```

## GraphQL Queries

Execute GraphQL queries for more efficient data fetching:

```python
# Simple query
query = """
query {
  viewer {
    login
    name
    email
  }
}
"""
result = client.graphql(query)
print(f"User: {result['viewer']['login']}")

# Query with variables
query = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    name
    description
    stargazerCount
    issues(first: 5, states: OPEN) {
      nodes {
        title
        number
      }
    }
  }
}
"""
variables = {"owner": "github", "name": "hub"}
result = client.graphql(query, variables=variables)
repo_data = result["repository"]
print(f"Stars: {repo_data['stargazerCount']}")
for issue in repo_data["issues"]["nodes"]:
    print(f"Issue #{issue['number']}: {issue['title']}")
```

## Configuration Options

### Retry Strategy

```python
# Configure retry behavior
client = GitHubAPIClient(
    token="ghp_token",
    max_retries=5,           # Maximum retry attempts
    backoff_factor=2.0       # Exponential backoff multiplier
)
```

### Error Handling

```python
from github_action_toolkit import GitHubAPIClient, RateLimitError, APIError

client = GitHubAPIClient(token="ghp_token", rate_limit_wait=False)

try:
    repo = client.get_repo("owner/repo")
except RateLimitError as e:
    print(f"Rate limit exceeded. Reset at: {e.reset_time}")
except APIError as e:
    print(f"API error ({e.status_code}): {e}")
```

## Advanced Usage

### Access Underlying PyGithub Instance

For features not directly exposed, you can access the underlying PyGithub client:

```python
# Access PyGithub directly
pygithub_client = client.github

# Use any PyGithub method
gists = pygithub_client.get_gists()
for gist in gists:
    print(gist.description)
```

### Custom Headers

```python
# Add custom headers to requests
response = client.request(
    "GET",
    "/repos/owner/repo/contents/file.txt",
    headers={
        "Accept": "application/vnd.github.v3.raw"
    }
)
content = response.text
```

## Best Practices

1. **Reuse client instances**: Create one client and reuse it across your application
2. **Use pagination**: Don't fetch all results at once for large datasets
3. **Enable rate limit waiting**: Set `rate_limit_wait=True` for long-running scripts
4. **Use GraphQL for complex queries**: Fetch multiple related resources in one request
5. **Use conditional requests**: Enable ETags for frequently accessed, rarely changing data
6. **Handle errors gracefully**: Catch `RateLimitError` and `APIError` appropriately

## Examples

### Check if Repository Exists

```python
from github_action_toolkit import GitHubAPIClient, APIError

client = GitHubAPIClient()

try:
    repo = client.get_repo("owner/repo")
    print(f"Repository exists: {repo.full_name}")
except APIError as e:
    if e.status_code == 404:
        print("Repository not found")
    else:
        raise
```

### Create an Issue

```python
client = GitHubAPIClient()
repo = client.get_repo("owner/repo")

issue = repo.create_issue(
    title="Bug report",
    body="Description of the bug",
    labels=["bug", "high-priority"]
)
print(f"Created issue #{issue.number}: {issue.html_url}")
```

### List Open Pull Requests

```python
client = GitHubAPIClient()
repo = client.get_repo("owner/repo")

print("Open Pull Requests:")
for pr in client.paginate(repo.get_pulls, state="open"):
    print(f"  PR #{pr.number}: {pr.title}")
    print(f"    Author: {pr.user.login}")
    print(f"    Branch: {pr.head.ref} → {pr.base.ref}")
    print()
```

### Monitor Repository Activity

```python
import time
from github_action_toolkit import GitHubAPIClient

client = GitHubAPIClient(rate_limit_wait=True)

# Monitor new issues every 5 minutes
last_check = time.time()

while True:
    repo = client.get_repo("owner/repo")
    
    for issue in client.paginate(repo.get_issues, since=last_check):
        print(f"New issue: #{issue.number} - {issue.title}")
    
    last_check = time.time()
    time.sleep(300)  # 5 minutes
```

## API Reference

See the module docstrings for complete API documentation:

```python
from github_action_toolkit import GitHubAPIClient

help(GitHubAPIClient)
```
