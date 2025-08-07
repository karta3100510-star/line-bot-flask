import requests
from bs4 import BeautifulSoup

SOCIAL_URLS = [
    "https://www.facebook.com/share/16gt5rCZJD/",
    "https://www.facebook.com/share/16MZC8mAGg/",
    "https://www.facebook.com/share/1D9kKbnNDs/",
    "https://substack.com/@unclestocknotes?fbclid=IwQ0xDSwL_ywZjbGNrAv_K_2V4dG4DYWVtAjExAAEeM386cpgh4Be8yvRY7paGPJPr6YX3oK0cFcbUj4kw4FSXEGWBQ3TEtT1DB0c_aem_x56xFJ1DTptDsknD1lnRLg",
    "https://www.facebook.com/share/1CXEkxxxQY/",
    "https://substack.com/@skilleddriver?utm_source=user-menu&fbclid=IwQ0xDSwL_y0hjbGNrAv_LRGV4dG4DYWVtAjExAAEeo6uz3zPo-Pq6p3gRg9vYJg3hKQNjEfFGPL_cuiNz4TkPtXpOE5OX85yUxwA_aem_AD-OndynIRmqu0f6apISHw",
    "https://www.facebook.com/share/1HhqEJJJqb/",
    "https://www.facebook.com/share/16jsPApAxC/"
]

def crawl_social_data():
    results = []
    for url in SOCIAL_URLS:
        try:
            resp = requests.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            title = soup.title.string if soup.title else ''
            # Placeholder: extract posts list if possible
            results.append({'url': url, 'data': title})
        except Exception as e:
            print(f"Error crawling {url}: {e}")
    return results
