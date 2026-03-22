import urllib.request
import re

badge_ids = [
    "87703a7a-94d9-4ba0-8586-2e8a1350e152",
    "e66b66dd-e747-424b-b022-62f2db28eb89",
    "32b54f0b-ba99-4655-b40a-15d3d7883d69",
    "7d83a617-ba0b-4e45-9b8a-a70ceef6f4c3",
    "5fe1a562-e4c2-4ab2-95e8-71c96bbf0132"
]

for bid in badge_ids:
    url = f"https://www.credly.com/badges/{bid}/public_url"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        img_match = re.search(r'<meta property="og:image" content="(.*?)"', html)
        title_match = re.search(r'<meta property="og:title" content="(.*?)"', html)
        print(f"ID: {bid}")
        print(f"IMG: {img_match.group(1) if img_match else 'None'}")
        print(f"TITLE: {title_match.group(1) if title_match else 'None'}")
    except Exception as e:
        print(f"Error fetching {bid}: {e}")
