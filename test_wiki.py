import json
import urllib.request
import urllib.parse

def fetch_wiki_summary(query):
    # Try to add " programming" or " software" to disambiguate
    search_query = urllib.parse.quote(query + " software")
    url = f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&generator=search&gsrsearch={search_query}&gsrlimit=1"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            pages = data.get("query", {}).get("pages", {})
            if pages:
                # get the first page
                page = list(pages.values())[0]
                extract = page.get("extract", "")
                # get first sentence
                sentences = extract.split(". ")
                if sentences:
                    return sentences[0] + "."
    except Exception as e:
        print(f"Error: {e}")
    return None

print(fetch_wiki_summary("Python"))
print(fetch_wiki_summary("React"))
print(fetch_wiki_summary("Django"))
print(fetch_wiki_summary("AWS"))
