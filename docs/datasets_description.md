"items_all_themes" - The “items_all_themes” dataset is the fully cleaned newsletter dataset where every item has been assigned a standardized theme using the full theme-mapping process.

“items_final_themes” - items_final_themes is the fully cleaned and processed newsletter dataset, with duplicates removed, themes standardised, organisations and categories assigned, and a combined text field ready for analysis. 
“programme_updates.csv.” - programme_updates.csv contains all newsletter items that belong to the ERP Project / Programme Updates theme, fully cleaned and enriched with metadata. It includes each item’s title, description, theme mapping, link, domain, organisation, combined text field, and text-length features (character/word counts), making it a ready-to-analyse dataset of ERP project updates only.
newsletter_full_articles.csv — contains one row per unique article link with the full scraped article text, article title, domain, and scrape status.
newsletter_full_articles_with_items.csv — merges each newsletter item with its corresponding full scraped article text, combining newsletter metadata (theme, title, description) with the article content.

successfully_scraped.csv contains only the newsletter items whose article pages were successfully fetched and fully scraped, including their cleaned text, titles, themes, organisations, and metadata. 
