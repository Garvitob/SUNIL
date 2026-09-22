# Sunil Charora campaign website

Bilingual static website for Shri Sunil Charora (Rashtriya Lok Dal, Anupshahr Assembly 67, Bulandshahr).
Hindi is the default page at `/`, English is at `/en/`.

Designed and developed by **First Compile** (Garvit Oberoi, +91 70173 04973).

## How it is built

| Path | What it is |
| --- | --- |
| `src/template.html` | The whole page. Every line is written once as `⟦हिंदी‖English⟧` (text), `attr="⟪हिंदी‖English⟫"` (attributes) or `⟮हिंदी‖English⟯` (head only). |
| `src/404.html` | The bilingual "page not found" page. |
| `src/build.py` | Builds everything into `site/` (Python 3 standard library only, no packages). |
| `src/make_og.py` | Redraws the WhatsApp/Facebook preview images and icons (needs Pillow and the fonts listed in the file). |
| `site/` | The finished website that Vercel serves. Generated; edit `src/` instead. |
| `vercel.json` | Vercel settings: build command, output folder, clean URLs, security and cache headers. |

`python3 src/build.py` writes:

- `site/index.html` (Hindi) and `site/en/index.html` (English), each with canonical, hreflang, Open Graph, X card, JSON-LD (ProfilePage, Person, FAQ) and a Content-Security-Policy that allows exactly the page's own inline code
- `site/404.html`, `sitemap.xml` (with image entries), `robots.txt`, `llms.txt`, `humans.txt` and `site.webmanifest`
- `preview.html` in the project root: one file with the images inlined, for a quick look. It is not deployed.

Images and fonts get a `?v=<content hash>` so browsers can cache them for a year and still pick up a changed file straight away.

## Deploy on Vercel

1. Vercel → **Add New… → Project** → import the GitHub repo `Garvitob/SUNIL`.
2. Leave every setting as it is. `vercel.json` already sets Framework "Other", Build Command `python3 src/build.py` and Output Directory `site`.
3. Click **Deploy**.

On every deploy Vercel rebuilds the site. It sets the canonical URL, sitemap and share links to the project's production address:

- If no domain is added, that is the `*.vercel.app` address.
- Once a domain is added, it becomes that domain.

To pin a specific address, add an Environment Variable `SITE_URL` (for example `https://sunilcharora.in`) and redeploy.

## Custom domain (recommended)

On 22 Sep 2026 `sunilcharora.in` was still available to register.

1. Buy the domain.
2. In Vercel, open **Project → Settings → Domains** and add both `sunilcharora.in` and `www.sunilcharora.in`. Set `www` to redirect (308) to the apex domain.
3. Click **Redeploy** so the canonical URLs, sitemap and preview images switch to the new domain.

## After going live

1. **Google Search Console:** add a *Domain* property and verify it with the DNS TXT record. For a `*.vercel.app` address, use a *URL-prefix* property instead:
   1. Copy only the `content="…"` value of the HTML tag.
   2. Save it as the Vercel Environment Variable `GOOGLE_SITE_VERIFICATION`.
   3. Redeploy.
   4. Submit `https://<your-domain>/sitemap.xml`.
2. **Bing Webmaster Tools** (optional): import from Search Console, or use `BING_SITE_VERIFICATION` the same way.
3. **Share previews:** paste the URL into the [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) and send it once on WhatsApp to check the preview card.
4. **Facebook:** add the website URL in the Facebook page's *Website* field. The site links to https://www.facebook.com/SunilCharoraRLD/.
5. **Vercel Web Analytics** (optional):
   1. Enable it in the Vercel dashboard.
   2. Add `<script defer src="/_vercel/insights/script.js"></script>` just before `</body>` in `src/template.html`.
   3. Push. The build sees the same-origin script and allows it in the page's Content-Security-Policy.

## Confirm with Sunil ji before launch

- Spelling चरौरा (primary) and the variants चरोरा / Charaura listed in the FAQ and structured data.
- "Former" (पूर्व) Zila Panchayat member and **Ward No. 50**. I could not confirm the ward number from any public source.
- The message and pledge text.

## Editing

- **Text:** edit `src/template.html`, run `python3 src/build.py`, then commit both `src/` and `site/`. Vercel rebuilds anyway, but committing `site/` keeps the sitemap `lastmod` date accurate.
- **More photos:**
  1. Add WebP files to `site/images/`.
  2. Copy a `<figure class="photo">` block in the template and use `{{IMG:file.webp}}` for the path.
  3. Add the file name to `PHOTOS` in `build.py` to list it in the image sitemap.
- **Preview images:** if the name, ward or slogan changes, run `python3 src/make_og.py`, then rename the output files, for example `og-image-v2.jpg`, and update the template. WhatsApp and Facebook cache preview images by URL.
- **Inline code:** do not add `style="…"` attributes or `<script src>` tags. The Content-Security-Policy would block them, and the build stops with a message if it finds them. Use CSS classes instead.

## Check locally

```bash
python3 src/build.py
python3 -m http.server 8000 --directory site   # open http://localhost:8000/
```
