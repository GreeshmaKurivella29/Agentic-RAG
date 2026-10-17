import requests
from bs4 import BeautifulSoup
import trafilatura

def search_indian_kanoon(query: str, max_results: int = 4):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    encoded = requests.utils.quote(query)
    search_url = f"https://indiankanoon.org/search/?formInput={encoded}"
    
    results = []
    try:
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return results
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        result_divs = soup.select('.result')
        
        for div in result_divs[:max_results]:
            title_el = div.select_one('.result_title a')
            headline_el = div.select_one('.headline')
            if not title_el:
                continue
                
            title = title_el.text.strip()
            href = title_el.get('href', '')
            full_url = f"https://indiankanoon.org{href}" if href.startswith('/') else href
            
            # Fetch document fragment or doc text
            snippet = headline_el.text.strip() if headline_el else ""
            
            # If doc URL available, extract top judgment excerpt
            doc_text = snippet
            if '/doc/' in full_url or '/docfragment/' in full_url:
                doc_id = href.split('/')[2] if len(href.split('/')) > 2 else ""
                if doc_id.isdigit():
                    clean_doc_url = f"https://indiankanoon.org/doc/{doc_id}/"
                    try:
                        doc_resp = requests.get(clean_doc_url, headers=headers, timeout=5)
                        if doc_resp.status_code == 200:
                            extracted = trafilatura.extract(doc_resp.text)
                            if extracted:
                                # Keep first 1200 chars containing bench and key holding
                                doc_text = extracted[:1200].replace('\n\n', '\n')
                    except Exception:
                        pass
                        
            results.append({
                "title": title,
                "url": full_url,
                "source": "Live Web: Indian Kanoon",
                "text": doc_text or snippet,
            })
    except Exception as e:
        print("Search error:", e)
        
    return results

if __name__ == '__main__':
    q = "anticipatory bail section 438 crpc"
    print(f"Searching Indian Kanoon live for: {q}")
    res = search_indian_kanoon(q, max_results=3)
    print(f"Found {len(res)} live legal results:")
    for i, r in enumerate(res, 1):
        print(f"[{i}] {r['title']}")
        print(f"    URL: {r['url']}")
        print(f"    Text: {r['text'][:180]}...\n")
