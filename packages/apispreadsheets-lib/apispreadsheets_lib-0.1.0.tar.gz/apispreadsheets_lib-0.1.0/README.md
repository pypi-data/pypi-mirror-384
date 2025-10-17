# apispreadsheets-test

Python client for API Spreadsheets.

```python
from apispreadsheets_test import Client

c = Client(access_key="...", secret_key="...")
print(c.list_files(accessKey="...", secretKey="..."))