import requests
from bs4 import BeautifulSoup
import datetime
import json
import os
import subprocess
import dateparser

# === Absolute comics URLs ===
comic_urls = [
    "https://readcomicsonline.ru/comic/absolute-batman-2024",
    "https://readcomicsonline.ru/comic/absolute-wonder-woman-2024",
    "https://readcomicsonline.ru/comic/absolute-superman-2024",
    "https://readcomicsonline.ru/comic/absolute-flash-2025",
    "https://readcomicsonline.ru/comic/absolute-martian-manhunter-2025",
    "https://readcomicsonline.ru/comic/absolute-green-lantern-2025"
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTERS_FILE = os.path.join(BASE_DIR, "chapters.json")
OUTPUT_HTML = os.path.join(BASE_DIR, "absolute_chapters.html")
OUTPUT_HTML_LOCAL = os.path.join(BASE_DIR, "absolute_chapters_local.html")

PC_BG = "absolute_roster_card_1.jpg"
PHONE_BG = "absolute_roster_card_0.jpg"

# === Fetch chapters from sites ===
def fetch_chapters(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    chap_titles = soup.select("h5.chapter-title-rtl a")
    chap_dates = soup.select("div.date-chapter-title-rtl")
    chapters = []
    for title_elem, date_elem in zip(chap_titles, chap_dates):
        chap_title = title_elem.get_text(strip=True)
        link = title_elem.get("href")
        date_str = date_elem.get_text(strip=True)
        chapters.append({"title": chap_title, "url": link, "date": date_str, "checked": False})
    return chapters

# === Load or initialize chapters.json ===
def load_chapters():
    if os.path.exists(CHAPTERS_FILE):
        with open(CHAPTERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"all_chapters": []}

def save_chapters(chapters):
    with open(CHAPTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(chapters, f, indent=2, ensure_ascii=False)

# === Generate HTML ===
def generate_html(chapters, output_file, local=True):
    sorted_chapters = sorted(
        chapters["all_chapters"],
        key=lambda c: dateparser.parse(c["date"], settings={'DATE_ORDER': 'DMY'}) if c.get("date") else datetime.datetime.min
    )

    chapter_items = ""
    for idx, chap in enumerate(sorted_chapters):
        link_html = f'<a href="{chap["url"]}" target="_blank">{chap["title"]}</a>' if local else chap["title"]
        date_text = chap["date"]
        chapter_items += f"""
        <li id="chapter-{idx}" class="{'checked' if chap.get('checked') else 'unchecked'}">
            <input type="checkbox" {'checked' if chap.get('checked') else ''} onchange="toggleChapter({idx})">
            <span>{link_html}</span>
            <span class="date">{date_text}</span>
        </li>
        """

    html = f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Absolute Universe Reading Order</title>
<style>
body {{ margin:0; padding:0; font-family:Arial,sans-serif; color:white; overflow:hidden; }}
.background {{ position:fixed; top:0; left:0; width:100%; height:100%; z-index:-1; background:url('{PC_BG}') no-repeat center center; background-size:cover; }}
@media only screen and (max-width:768px) {{ .background {{ background:url('{PHONE_BG}') no-repeat center center; background-size:cover; }} }}
.content {{ position:relative; height:100%; width:100%; overflow-y:auto; -webkit-overflow-scrolling: touch; padding:20px; }}
h1 {{ text-align:center; margin-top:20px; }}
ul {{ list-style:none; padding:0; margin:20px; }}
li {{ display:flex; justify-content:space-between; align-items:center; margin:5px 0; padding:10px; border-radius:8px; background: rgba(0,0,0,0.5); }}
li.unchecked span:first-child, li.unchecked span:first-child a {{ color:white !important; text-decoration:none !important; }}
li.checked span:first-child, li.checked span:first-child a {{ color:black !important; text-decoration:line-through !important; }}
.date {{ margin-left:20px; }}
.filters {{ text-align:center; margin-bottom:20px; }}
.filters button {{ margin:0 10px; padding:5px 10px; }}
@media only screen and (max-width:768px) {{
    h1 {{ font-size:2em; }}
    li {{ flex-direction:column; align-items:flex-start; padding:10px; }}
    .date {{ font-size:0.7em; margin-left:0; margin-top:5px; }}
}}
</style>
</head>
<body>
<div class="background"></div>
<div class="content">
<h1>Absolute Universe Reading Order</h1>
<div class="filters">
    <button onclick="filterChapters('all')">All</button>
    <button onclick="filterChapters('unread')">Unread</button>
    <button onclick="filterChapters('read')">Read</button>
</div>
<ul id="chapters">{chapter_items}</ul>
<script>
function toggleChapter(index) {{
    const li = document.getElementById('chapter-'+index);
    const checkbox = li.querySelector('input[type=checkbox]');
    if (checkbox.checked) {{ li.classList.remove('unchecked'); li.classList.add('checked'); }}
    else {{ li.classList.remove('checked'); li.classList.add('unchecked'); }}
    localStorage.setItem('chapter-'+index, checkbox.checked);
}}

function filterChapters(mode) {{
    const lis = document.querySelectorAll('#chapters li');
    lis.forEach(li => {{
        if(mode==='all') li.style.display='flex';
        else if(mode==='read') li.style.display = li.classList.contains('checked') ? 'flex':'none';
        else if(mode==='unread') li.style.display = li.classList.contains('unchecked') ? 'flex':'none';
    }});
    localStorage.setItem('filterMode', mode);
}}

window.onload = function() {{
    const lis = document.querySelectorAll('#chapters li');
    lis.forEach((li,index) => {{
        const saved = localStorage.getItem('chapter-'+index);
        if(saved!==null){{
            const checkbox = li.querySelector('input[type=checkbox]');
            checkbox.checked = saved==='true';
            li.classList.remove('checked','unchecked');
            li.classList.add(checkbox.checked?'checked':'unchecked');
        }}
    }});
    const savedFilter = localStorage.getItem('filterMode') || 'unread';
    filterChapters(savedFilter);
}}
</script>
</div>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

# === Git auto-update for your new repo ===
def update_and_push():
    try:
        # Make sure your repo is initialized and remote is set
        subprocess.run(["git", "-C", BASE_DIR, "add", OUTPUT_HTML, OUTPUT_HTML_LOCAL, PC_BG, PHONE_BG, CHAPTERS_FILE], check=True)
        subprocess.run(["git", "-C", BASE_DIR, "commit", "-m", "Auto-update Absolute Universe reading order"], check=True)
        subprocess.run(["git", "-C", BASE_DIR, "push", "origin", "main"], check=True)
        print("✅ GitHub updated successfully!")
    except subprocess.CalledProcessError as e:
        print("❌ Git push failed:", e)

# === Main ===
if __name__ == "__main__":
    all_chapters = []
    for url in comic_urls:
        try:
            all_chapters.extend(fetch_chapters(url))
        except Exception as e:
            print(f"Error fetching {url}: {e}")

    chapters_data = load_chapters()
    existing_titles = {c["title"] for c in chapters_data.get("all_chapters", [])}
    new_chaps = [c for c in all_chapters if c["title"] not in existing_titles]
    chapters_data.setdefault("all_chapters", []).extend(new_chaps)

    save_chapters(chapters_data)
    generate_html(chapters_data, OUTPUT_HTML, local=False)
    generate_html(chapters_data, OUTPUT_HTML_LOCAL, local=True)
    update_and_push()
    print(f"✅ {len(new_chaps)} new chapters added and HTML updated!")
