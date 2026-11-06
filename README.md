# Pakistan Fast News

Fast, SEO-ready Pakistan news site — static HTML, no ads, no trackers, no heavy scripts.

- **Live:** https://usmankalera-dev.github.io/pakistan-fast-news/
- **Sources:** Dawn + ARY News RSS (headlines link to the original publishers)
- **Rebuild:** `python3 build.py` fetches the latest feeds and regenerates all pages.

## SEO checklist (all done)
- Unique title + meta description + canonical on every page
- Open Graph + Twitter Card tags
- JSON-LD: WebSite, NewsMediaOrganization, NewsArticle, CollectionPage
- Semantic HTML5, one H1 per page, proper heading order
- `sitemap.xml` + `robots.txt`, clean URLs, 404 page
- Speed: system fonts only, one small CSS file, deferred JS, no images, no frameworks
