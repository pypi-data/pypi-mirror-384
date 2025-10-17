# ZvolvClient SDK

<div>
📚 <a href="#documentation">Documentation</a> - 🚀 <a href="#getting-started">Getting started</a> - 💻 <a href="#api-reference">API reference</a> - 💬 <a href="#feedback">Feedback</a>
</div>


Learn how to automate with Zvolv using Python.
## Documentation
- [Docs site](https://python-zvolv-sdk.readthedocs.io/) - explore our docs site and learn more about Zvolv.
- [Examples](https://github.com/zvolvapi/python-zvolv-sdk/blob/main/EXAMPLES.md) - explore our examples docs and learn more about using sdk.

## Getting started
### Installation
You can install the Zvolv Python SDK using the following command.
```
pip install zvolv-sdk
```

> Requires Python 3.0 or higher.

# Usage
## Initialize ZvolvClient

Once the package is installed, you can import the library using import or require approach.

Initializes the ZvolvClient with the base url of the Zvolv server:

```python
from zvolv_sdk import ZvolvClient

client = ZvolvClient(BASE_URL)

```
> BASE_URL is the host address on which your Zvolv workspace is deployed, unless you have isolated custom deployment use 'https://app.zvolv.com'.

## Initialize Workspace

Before performing any operation, SDK needs your workspace context. Use below method to initialize your workspace

```python

try:
    workspace = client.workspace.init(DOMAIN)
except Error:
    print(Error)

```
> DOMAIN is your unique workspace identifier

## Perform Authentication

Zvolv modules are access contolled, you need valid user crendentials to invoke any module methods. Use below method for authentication.

```python
try:
    login = client.auth.login(EMAIL, PASSWORD)
except Error:
    print(Error)
```
> You can use any valid zvolv user's EMAIL & PASSWORD from your workspace

## API references
Zvolv comprises various modules to achieve respective business operations. Use below modules & methods to interact with Zvolv APIs.

### Forms
#### Create a Form
```python
from zvolv_sdk.models.form import Form

form = Form(...)
response = client.forms.post(form)
```
> Use Form model with required attributes

#### Update a Form
```python
from zvolv_sdk.models.form import Form

form = Form(...)
response = client.forms.put(form)
```
> Use Form model with id or uuid & other required attributes

#### Get a Form
```python
from zvolv_sdk.models.form import Form

response: Form = client.forms.get(ID)
```
> ID is unique form identifier


### Submissions
#### Create a Submission
```python
from zvolv_sdk.models.submission import Submission

submission = Submission(...)
response = client.submissions.post(submission)
```
> Use Submission model with elements to be created

#### Update a Submission
```python
from zvolv_sdk.models.submission import Submission

submission = Submission(...)
response = client.submissions.put(submission)
```
> Use Submission model with id & elements to be updated

#### Get a Submission
```python
from zvolv_sdk.models.submission import Submission

response: Submission = client.submissions.get(ID)
```
> ID is unique submission identifier

#### Search Submissions
```python
from elasticsearch_dsl import Q, Search

search_obj = Search()
bool_query = Q('bool', must=[Q(...)])
search_obj = search_obj.query(bool_query)

response = client.submissions.search(FORM_ID, search_obj)
```
> search method support elastic queries. Generate your query with help of elasticsearch_dsl


### Tasks
#### Create a Task
```python
from zvolv_sdk.models.task import Task

task = Task(...)
response = client.tasks.post(task)
```
> Use Task model with required attributes

#### Update a Task
```python
from zvolv_sdk.models.task import Task

task = Task(...)
response = client.tasks.put(task)
```
> Use Task model with id & required attributes to be updated

#### Get a Task
```python
from zvolv_sdk.models.task import Task

response: Task = client.tasks.get(ID)
```
> ID is unique task identifier

#### Search Tasks
```python
from elasticsearch_dsl import Q, Search

search_obj = Search()
bool_query = Q('bool', must=[Q(...)])
search_obj = search_obj.query(bool_query)

response = client.tasks.search(search_obj)
```
> search method support elastic queries. Generate your query with help of elasticsearch_dsl


### Feedback

---

If you get stuck, we’re here to help. The following are the best ways to get assistance working through your issue:

Use our [GitHub Issue Tracker][gh-issues] for reporting bugs or requesting features.
Visit the [Zvolv Community][zvolv-community] for getting help using Zvolv Developer Kit for Python or just generally bond with your fellow Zvolv developers.

<!-- Markdown links -->


[pypi-url]: https://pypi.org/project/slack-sdk/
[python-version]: https://img.shields.io/pypi/pyversions/slack-sdk.svg
[build-image]: https://github.com/slackapi/python-slack-sdk/workflows/CI%20Build/badge.svg
[build-url]: https://github.com/slackapi/python-slack-sdk/actions?query=workflow%3A%22CI+Build%22
[codecov-image]: https://codecov.io/gh/slackapi/python-slack-sdk/branch/main/graph/badge.svg
[codecov-url]: https://codecov.io/gh/slackapi/python-slack-sdk
[contact-image]: https://img.shields.io/badge/contact-support-green.svg
[contact-url]: https://slack.com/support
[slackclientv1]: https://github.com/slackapi/python-slackclient/tree/v1
[api-methods]: https://api.slack.com/methods
[rtm-docs]: https://api.slack.com/rtm
[events-docs]: https://api.slack.com/events-api
[bolt-python]: https://github.com/slackapi/bolt-python
[pypi]: https://pypi.org/
[gh-issues]: https://github.com/zvolvapi/python-zvolv-sdk/issues
[zvolv-community]: https://zvolv.com/
[urllib]: https://docs.python.org/3/library/urllib.request.html
