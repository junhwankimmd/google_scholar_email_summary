# Google Scholar Mailing Literature Summary

Your alert emails from Google Scholar are summarized into a markdown file that has information of study titles, lists of authors, links, PMIDs, and abstracts.

## Prerequisites

Before you can use this script, ensure that the following are set up on your system:

1. **Python 3.7+**: This script requires Python version 3.7 or later. You can download Python from the official [Python website](https://www.python.org/downloads/).

2. **Gmail API Credentials**:
    - You need to enable the Gmail API and download the credentials file (`client_secret.json`).
    - Follow the [Google Gmail API Python Quickstart Guide](https://developers.google.com/gmail/api/quickstart/python) to set up the Gmail API.
    - **Ensure that the `client_secret.json` file is saved in the project directory or specify its correct path in the script.**
    - If the file is not in the project root, update the `CREDENTIALS_FILE` variable in the script to reflect the correct path:

    ```python
    CREDENTIALS_FILE = 'path/to/your/client_secret.json'
    ```

3. **Required Python Libraries**:
    - Install the necessary Python libraries using `pip`. Run the following commands in your terminal:

    ```bash
    pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client beautifulsoup4 requests
    ```

    The required libraries include:
    - `google-auth`
    - `google-auth-oauthlib`
    - `google-auth-httplib2`
    - `google-api-python-client`
    - `beautifulsoup4`
    - `requests`

## Customization Options

1. **`maxResults` Parameter**:
   - The script fetches a specific number of emails using the Gmail API, defined by the `maxResults` parameter.
   - By default, this value is set to 30. You can adjust it to fetch more or fewer emails by modifying the following line in the script:

    ```python
    messages = service.users().messages().list(userId='me', q=query, maxResults=30).execute().get('messages', [])
    ```

    - Change `30` to your desired number of emails to retrieve.

## Known Issues

1. **Title Truncation**:
   - If the title of a paper is very long, it may appear truncated with "..." in the email content. The script attempts to search for the full title in PubMed using the truncated title, which may not always yield accurate results.

2. **PMID and Abstract Extraction**:
   - The script relies on PubMed IDs (PMID) to fetch abstracts. If a PMID is not available for a paper (unlike DOI), the script will be unable to extract the abstract. In such cases, the output will indicate that the abstract could not be retrieved.

## Contributing

If you'd like to contribute to this project, please fork the repository and use a feature branch. Pull requests are welcome.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
