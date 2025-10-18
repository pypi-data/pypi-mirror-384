# GitLab PS Utils

GitLab PS utils is the foundational API and utilities libraries used by GitLab Professional Services. 
To see the source code, project backlog and contributing guide, [check here](https://gitlab.com/gitlab-org/professional-services-automation/gitlab-ps-utils)

## Install

```bash
pip install gitlab-ps-utils
```

## Usage

This library contains various utility modules and classes.
Refer to the repository source code to see available utility functions.

### Importing a utility function

```python
from gitlab_ps_utils.string_utils import strip_numbers

test_var = "abc123"
print(strip_numbers(test_var))
```

### Importing a utility class

```python
from gitlab_ps_utils.api import GitLabApi

gl_api = GitLabApi()

gl_api.generate_get_request("http://gitlab.example.com", "token", "/projects")
```

## Other resources

### Python-GitLab

We include a basic GitLab API wrapper class in this library. We will include specific API wrapper functions in the future.
Our wrapper class and specific wrappers were created when [python-gitlab](https://python-gitlab.readthedocs.io/en/stable/) was in a much earlier state,
so we continued to use our wrapper instead of switching to python-gitlab

For generic requests to the GitLab API, our wrapper is more lightweight than python-gitlab,
but python-gitlab is a great option for more complex API scripts

