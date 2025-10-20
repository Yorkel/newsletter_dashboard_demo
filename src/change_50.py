from bs4 import BeautifulSoup
import re

path_in  = "/workspaces/ERP_Newsletter/data_raw/newsletters_15.10.2025/newsletter_50.html"
path_out = "/workspaces/ERP_Newsletter/data_raw/newsletters_15.10.2025/newsletter_50.html"

soup = BeautifulSoup(open(path_in, encoding="utf-8", errors="ignore"), "html.parser")
node = soup.find(string=re.compile(r'^\s*ERP\s*Newsletter\s*#\s*\d+\s*$'))
if node:
    node.replace_with("ERP Newsletter #50")
open(path_out, "w", encoding="utf-8").write(str(soup))
