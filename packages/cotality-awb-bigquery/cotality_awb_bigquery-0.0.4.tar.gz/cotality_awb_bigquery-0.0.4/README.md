# Python Client for Cotality BigQuery SDK
This package provides a Python client for the Cotality BigQuery SDK, allowing users to interact with BigQuery services in a streamlined manner.

## Prerequisites
Python >= 3.11

## Installation
```zsh
pip install cotality-sdk-bigquery
```

## Example usage Jupiter notebook

Install package:
```
!pip install cotality-sdk-bigquery >/dev/null
```

Setup Clip Application
```
from cotality.platform.bigquery.clip import ClipApp
app = ClipApp()
```
Display Clip application UI
```
app.display()
```
Run backgroun Clip job
```
app.run_job()
```