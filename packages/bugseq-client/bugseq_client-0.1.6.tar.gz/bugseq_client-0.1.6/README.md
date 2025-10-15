# BugSeq Python Client Library

Authentication and client code for interacting with the [BugSeq](https://bugseq.com) API.

## Installation

`pip install bugseq-client`

## Example Usage

```python
from pathlib import Path

import requests

from bugseq_client.auth import (
    DEFAULT_OAUTH_CONFIG,
    Session,
    get_default_credential_storage_provider,
)
import bugseq_client.openapi_client


def download_url_to_file(download_url: str, dst: Path):
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(dst, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)


class App:
    def __init__(self):
        storage = get_default_credential_storage_provider()
        self.session = Session(DEFAULT_OAUTH_CONFIG, storage)

    def run(self):
        token = self.session.get_token()

        configuration = bugseq_client.openapi_client.Configuration(
            host="https://api.bugseq.com",
            access_token=token,
        )

        with bugseq_client.openapi_client.ApiClient(configuration) as api_client:
            api = bugseq_client.openapi_client.JobsApi(api_client)

            print("fetching jobs")
            jobs_resp = api.list_analyses_v1_jobs_get()
            for job in jobs_resp.job_runs:
                print(
                    f"id={job.id} name={job.user_provided_name} status={job.job_status}"
                )

            print()

            job_id = jobs_resp.job_runs[0].id
            print(f"fetching outputs for job {job_id}")

            results_dir = Path(f"downloaded-results-{job_id}")

            results_resp = api.get_analysis_results_v1_jobs_job_id_results_get(job_id)
            for output in results_resp.outputs:
                print(f"  output filename={output.filename} size={output.size}")

                download_resp = (
                    api.download_analysis_result_v1_jobs_job_id_results_download_get(
                        job_id, output.filename
                    )
                )

                download_dst = results_dir / output.filename
                download_dst.parent.mkdir(exist_ok=True, parents=True)
                download_url_to_file(download_resp.url, download_dst)
                print(
                    f"  downloaded filename={output.filename} dst={str(download_dst)}"
                )


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
```

## Releasing to PyPI

```shell
docker run -it --rm \
    -v "$(pwd)":/work \
    -w /work \
    python:3.13 \
    bash
```

```shell
rm -rf dist/*
python3 -m pip install --upgrade build twine
python3 -m build
python3 -m twine upload dist/*
```
