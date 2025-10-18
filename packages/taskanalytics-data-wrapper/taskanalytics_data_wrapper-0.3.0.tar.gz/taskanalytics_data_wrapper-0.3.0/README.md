# Task Analytics Data Wrapper

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This is a wrapper for Task Analytics APIs. You can use it to download survey responses and metadata for each survey.

Install with

```bash
pip install taskanalytics-data-wrapper
```

or 

```bash
uv add taskanalytics-data-wrapper
```

## Supported APIs

- [Task Analytics Data Wrapper](#task-analytics-data-wrapper)
  - [Supported APIs](#supported-apis)
    - [Log in to Task Analytics](#log-in-to-task-analytics)
    - [Download Survey responses](#download-survey-responses)
    - [Download Survey metadata](#download-survey-metadata)
    - [Download Discovery survey responses](#download-discovery-survey-responses)
    - [Download organization metadata](#download-organization-metadata)

### Log in to Task Analytics

```python
import taskanalytics_data_wrapper.taskanalytics_api as task
```

You can log in with email and password

```python
status = log_in_taskanalytics(username=email, password=password)  
status.status_code
```

### Download Survey responses

You can download survey responses for a Top Task survey using the survey ID, email, password and setting a path for where to store the file.

```python
import taskanalytics_data_wrapper.taskanalytics_api as task

get_survey = task.download_survey(
    username=email, password=password, survey_id="03324", filename="data/survey.csv"
)
get_survey.status_code
```

### Download Survey metadata

You can download the survey metadata which includes the questions and response options for each survey using the survey ID, email and password.

```python
survey_metadata = task.get_survey_metadata(
    username=email,
    password=password,
    survey_id="03419",
    filename_path="data/metadata_survey.json",
)
survey_metadata.status_code
```

The object can be easily inspected transformed into a dictionary for analysis

```python
survey_metadata.text # survey metadata
our_dict = survey_metadata.json() # convert string to dict and store as a variable
```

### Download Discovery survey responses

You can download responses from open ended task discovery surveys as well

```python
get_openended_survey = task.download_discovery_survey(
    username=email,
    password=password,
    organization_id=organization,
    survey_id="03230",
    filename_path="data/open_ended_survey.json",
)
```
See how to turn this into csv in the code example below by expanding

<details>
<summary>Expandable example</summary>

```python
data = get_openended_survey.json()

#create a new dict from our subset of data
def flatten_openended_dict(data):
    """ """
    respondent = []
    completion = []
    category = []
    discovery = []
    comment = []
    for i in data:
        respondent.append(i["id"])
        completion.append(i["completion"])
        category.append(i["category"])
        discovery.append(i["answers"]["discovery"])
        try:
            comment.append(i["answers"]["comment"])
        except:
            comment.append("")
    newlist = [
        {
            "id": respondent,
            "completion": completion,
            "category": category,
            "discovery": discovery,
            "comment": comment,
        }
        for respondent, completion, category, discovery, comment in zip(
            respondent, completion, category, discovery, comment
        )
    ]
    return newlist


newlist = flatten_openended_dict(data["responses"])

# write open ended survey to csv with your preferred encoding and delimiter
keys = newlist[0].keys()

with open("data/open_survey.csv", "w", encoding="utf-8-sig", newline="") as output_file:
    writer = csv.DictWriter(output_file, fieldnames=keys, delimiter=";")
    writer.writeheader()
    writer.writerows(newlist)
```
</details>

### Download organization metadata

Get all the organization account metadata including the list of all survey IDs

```python
# Get all organization settings including surveys from task analytics
get_organization = task.get_organization_metadata(
    username=email,
    password=password,
    organization_id=organization,
    filename_path="data/organization.json",
)
get_organization.status_code 

# %%
get_organization.json()  # read response as json
```