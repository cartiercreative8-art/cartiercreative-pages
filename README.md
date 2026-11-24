# cartiercreative-pages
Static site for Cartier Creative, served by GitHub Pages at cartiercreativeco.com (see `CNAME`). Pushing to `main` publishes it.

- `/` agency homepage: missed calls, pricing tiers, work, booking link
- `/snow/` snow and plow crew campaign page
- `/privacy/`, `/terms/` A2P compliance pages. Keep the address and wording in sync with the carrier registration.

The homepage chat widget is the only SMS consent capture on the page. Don't add another form that collects a phone number.

## Field Notes blog (`/blog/`)
Posts are Markdown in `blog/_src/posts/` (underscore folders are not published). To add one, drop in a new `.md` file with the front matter shown in `blog/_src/build.py`, then run `python3 blog/_src/build.py`. It rebuilds the post pages, `/blog/index.html` and `/blog/feed.xml`. Commit the generated files too. Posts marked `draft: true` or dated in the future are held back.
