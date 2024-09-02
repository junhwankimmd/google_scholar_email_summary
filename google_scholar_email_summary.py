# Install or import libraries
import os
import pickle
import base64
import requests
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from bs4 import BeautifulSoup
from datetime import datetime

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# OAuth 2.0 client file path
CREDENTIALS_FILE = # Path to your credentials file (enclose it with '~' and use /)

# Token file path
TOKEN_PATH = 'token.pickle'

def authenticate_gmail_api():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def get_email_content(service, msg_id):
    message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = message.get('payload', {})

    body = None

    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/html':
                data = part.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

    if not body and 'body' in payload:
        data = payload.get('body', {}).get('data')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    return body

def extract_scholar_links(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if 'scholar.google.com/scholar_url?' in href or 'scholar.google.co.kr/scholar_url?' in href:
            title = a_tag.get_text(strip=True)
            results.append({'title': title, 'link': href})
    
    return results

def clean_title_for_pubmed_search(title):
    title = title.replace('...', '')

    if ':' in title:
        title = title.split(':')[0]

    return title.strip()

def search_pubmed(title):
    cleaned_title = clean_title_for_pubmed_search(title)
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        'db': 'pubmed',
        'term': cleaned_title,
        'retmode': 'json',
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        id_list = data.get('esearchresult', {}).get('idlist', [])
        if id_list:
            return id_list[0]
    return None

def fetch_pubmed_abstract_and_author(pmid):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        'db': 'pubmed',
        'id': pmid,
        'retmode': 'xml',
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        abstract = soup.find('AbstractText')
        authors = soup.find_all('Author')
        title = soup.find('ArticleTitle')
        
        author_list = []
        for author in authors:
            last_name = author.find('LastName')
            fore_name = author.find('ForeName')
            if last_name and fore_name:
                author_list.append(f"{fore_name.get_text()} {last_name.get_text()}")

        if len(author_list) > 2:
            author_info = f"{author_list[0]}, {author_list[1]}, et al."
        else:
            author_info = ', '.join(author_list)
        
        return (title.get_text() if title else None), (abstract.get_text() if abstract else "No abstract found."), author_info
    return None, "The abstract could not be extracted as no PMID was obtained. Please check URL.", None

def format_date(timestamp_ms):
    return datetime.fromtimestamp(int(timestamp_ms) / 1000).strftime('%Y-%m-%d')

def main():
    service = authenticate_gmail_api()
    query = 'from:scholaralerts-noreply@google.com'
    messages = service.users().messages().list(userId='me', q=query, maxResults=2).execute().get('messages', [])

    if not messages:
        print("No messages found.")
        return

    seen_titles = set()
    email_dates = []
    results = []

    for msg in messages:
        msg_id = msg['id']
        email_data = service.users().messages().get(userId='me', id=msg_id).execute()
        email_date = format_date(email_data['internalDate'])
        email_dates.append(email_date)

        email_content = get_email_content(service, msg_id)
        if email_content:
            titles_and_links = extract_scholar_links(email_content)
            if titles_and_links:
                for item in titles_and_links:
                    title = item['title']
                    if title not in seen_titles:
                        seen_titles.add(title)

                        pmid = search_pubmed(title)
                        if pmid:
                            full_title, abstract, author_info = fetch_pubmed_abstract_and_author(pmid)
                            if not full_title:
                                full_title = title
                            results.append({
                                'title': full_title,
                                'link': item['link'],
                                'author': author_info,
                                'abstract': abstract,
                                'pmid': pmid
                            })
                        else:
                            results.append({
                                'title': title,
                                'link': item['link'],
                                'author': "Author information not found.",
                                'abstract': "The abstract could not be extracted as no PMID was obtained. Please check URL.",
                                'pmid': None
                            })

    # Download as a markdown file
    markdown_content = f"## Google Scholar Mailing Literature Summary\n\n"
    markdown_content += f"**Report generated on**: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    if email_dates:
        markdown_content += f"**Date range of emails**: {min(email_dates)} ~ {max(email_dates)}\n\n"

    for result in results:
        markdown_content += f"### {result['title']}\n"
        markdown_content += f"### {result['author']}\n"
        markdown_content += f"### Link: [click]({result['link']})\n"
        if result['pmid']:
            markdown_content += f"### PMID: {result['pmid']}\n"
        markdown_content += f"\n### Abstract:\n{result['abstract']}\n\n"

    # Set up for the name of the markdown file
    if email_dates:
        filename = f"GSEmail_{min(email_dates)}_{max(email_dates)}.md"
    else:
        filename = f"GSEmail_{datetime.now().strftime('%Y-%m-%d')}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Markdown file has been created: {filename}")

if __name__ == '__main__':
    main()