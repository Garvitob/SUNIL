#!/usr/bin/env python3
"""
Builds the Sunil Charora campaign site from src/template.html.

  site/index.html      Hindi (default, canonical "/")
  site/en/index.html   English ("/en/")
  site/404.html        bilingual "page not found" (from src/404.html)
  site/robots.txt, sitemap.xml, llms.txt, humans.txt, site.webmanifest
  preview.html         single file with images inlined (for quick local viewing; not deployed)

Text in the template is written once as  ⟦हिंदी‖English⟧  (page text),
attr="⟪हिंदी‖English⟫" (attributes) and ⟮हिंदी‖English⟯ (head/meta, no switching).
Each page ships its own language in the HTML (clean for Google) plus the other
language as a small dictionary, so the हिंदी/English switch is instant.

The site address used for canonical, hreflang, Open Graph, JSON-LD and the sitemap
is the first of these that is set:
  --site https://www.example.in    command line
  SITE_URL                         environment variable (e.g. in Vercel > Settings > Environment Variables)
  VERCEL_PROJECT_PRODUCTION_URL    set by Vercel during its build: the custom domain once one is
                                   added to the project, otherwise the project's *.vercel.app address
  DEFAULT_SITE_URL                 below, for local builds

Optional environment variables: GOOGLE_SITE_VERIFICATION, BING_SITE_VERIFICATION
(the content="..." value of the verification meta tag from Search Console / Bing Webmaster Tools).

Usage:  python3 src/build.py
        python3 src/build.py --site https://www.example.in
Runs on Python 3.8+ with the standard library only (Vercel runs it on every deploy).
"""
import base64, datetime, hashlib, html, json, os, pathlib, re, sys, urllib.parse

DEFAULT_SITE_URL = "https://sunilcharora.in"   # no trailing slash
WA_NUMBER = "919719166039"
DEV_WA_NUMBER = "917017304973"   # First Compile (website developer), footer credit

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "template.html"
SRC_404 = ROOT / "src" / "404.html"
SITE = ROOT / "site"
MIME = {".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

# Self-hosted Google Fonts (SIL Open Font License), files: site/fonts/<family>-<weight>-<subset>.woff2
FONTS = [("Khand", 700), ("Martel Sans", 400), ("Martel Sans", 700)]
SUBSETS = [
    ("devanagari", "U+0900-097F,U+1CD0-1CF9,U+200C-200D,U+20A8,U+20B9,U+20F0,U+25CC,U+A830-A839,U+A8E0-A8FF,U+11B00-11B09"),
    ("latin-ext", "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,"
                  "U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"),
    ("latin", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,"
              "U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
]

# Photos listed in the image sitemap
PHOTOS = ["sunil-charora-portrait.webp", "sunil-charora-sabha.webp", "sunil-charora-naujawan-1200.webp", "sunil-charora-gyapan-1200.webp"]


def write(path, text):
    """UTF-8 with LF line endings on every OS, so rebuilding on Windows does not change every line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def site_address():
    def clean(url):
        url = url.strip().rstrip("/")
        return url if re.match(r"https?://", url) else "https://" + url
    if "--site" in sys.argv:
        i = sys.argv.index("--site")
        if i + 1 >= len(sys.argv):
            sys.exit("--site needs a URL, e.g. --site https://www.example.in")
        return clean(sys.argv[i + 1]), "--site"
    for var in ("SITE_URL", "VERCEL_PROJECT_PRODUCTION_URL"):
        if os.environ.get(var, "").strip():
            return clean(os.environ[var]), var
    return DEFAULT_SITE_URL, "DEFAULT_SITE_URL"


_versions = {}


def version(path):
    """Short content hash, appended as ?v= so browsers can cache files for a year and still see changes."""
    if path not in _versions:
        if not path.is_file():
            sys.exit("Missing file: %s" % path.relative_to(ROOT))
        _versions[path] = hashlib.sha256(path.read_bytes()).hexdigest()[:10]
    return _versions[path]


def data_uri(path):
    return "data:%s;base64,%s" % (MIME[path.suffix], base64.b64encode(path.read_bytes()).decode())


def asset(kind, name, base, mode):
    path = SITE / kind / name
    v = version(path)
    if mode == "preview":  # preview.html sits in the project root, next to site/
        return data_uri(path) if kind == "images" else "site/%s/%s" % (kind, name)
    return "%s%s/%s?v=%s" % (base, kind, name, v)


def icon(name, mode):
    """Favicons keep a stable, unversioned URL (search engines expect the favicon URL not to change)."""
    path = SITE / "images" / name
    version(path)  # fails the build if the file is missing
    return data_uri(path) if mode == "preview" else "/images/" + name


def font_faces(base, mode):
    rules = []
    for family, weight in FONTS:
        for subset, unicode_range in SUBSETS:
            f = "%s-%d-%s.woff2" % (family.lower().replace(" ", "-"), weight, subset)
            rules.append('@font-face{font-family:"%s";font-style:normal;font-weight:%d;font-display:swap;'
                         'src:url(%s) format("woff2");unicode-range:%s}' % (family, weight, asset("fonts", f, base, mode), unicode_range))
    return "\n".join(rules)


def wa_links(s):
    """{wa:text} opens a WhatsApp chat with Sunil ji, {wa-dev:text} with the website developer, text prefilled."""
    link = lambda number: lambda m: "https://wa.me/%s?text=%s" % (number, urllib.parse.quote(m.group(1), safe=""))
    s = re.sub(r"\{wa-dev:(.*?)\}", link(DEV_WA_NUMBER), s)
    return re.sub(r"\{wa:(.*?)\}", link(WA_NUMBER), s)


def verification_meta():
    tags = []
    for var, name in (("GOOGLE_SITE_VERIFICATION", "google-site-verification"), ("BING_SITE_VERIFICATION", "msvalidate.01")):
        value = os.environ.get(var, "").strip()
        if value:
            tags.append('<meta name="%s" content="%s">' % (name, html.escape(value)))
    return "\n".join(tags)


def csp_hash(text):
    return "'sha256-%s'" % base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode()


def add_csp(s, where):
    """Content-Security-Policy as a <meta>, allowing exactly the inline <script>/<style> blocks on this page
    (by hash), plus same-origin script files such as <script defer src="/_vercel/insights/script.js"></script>.
    frame-ancestors and the other response headers are set in vercel.json. form-action 'none' keeps a
    no-JavaScript submit of the contact form from putting names and numbers into URLs and server logs."""
    same_origin_js = False
    for tag in re.findall(r"<script\b[^>]*>", s):
        if tag in ("<script>", '<script type="application/ld+json">'):
            continue
        if re.fullmatch(r'<script(?: (?:defer|async))? src="/[^"/][^"]*"(?: (?:defer|async))?>', tag):
            same_origin_js = True
            continue
        sys.exit('%s: unexpected script tag %s (use inline <script> or <script defer src="/...">)' % (where, tag))
    if re.search(r"<[^>]+\s(?:style|on[a-z]+)=", s):
        sys.exit('%s: style="" and on*="" attributes are blocked by the CSP; use a class / addEventListener' % where)
    scripts = [csp_hash(x) for x in re.findall(r"<script>(.*?)</script>", s, re.S)]
    styles = [csp_hash(x) for x in re.findall(r"<style>(.*?)</style>", s, re.S)]
    if same_origin_js:
        scripts.insert(0, "'self'")
    policy = ("default-src 'none'; script-src %s; style-src %s; img-src 'self'; font-src 'self'; connect-src 'self'; "
              "manifest-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests") % (
        " ".join(scripts) or "'none'", " ".join(styles) or "'none'")
    return s.replace("{{CSP}}", '<meta http-equiv="Content-Security-Policy" content="%s">' % policy, 1)


def check_markers(s, where):
    left = re.findall(r"⟦|⟧|⟪|⟫|⟮|⟯|‖|\{\{[A-Z_]+|\{wa(?:-dev)?:", s)
    if left:
        sys.exit("Unprocessed markers in %s: %s" % (where, sorted(set(left))))


def render(tpl, lang, mode, site_url, lastmod):
    pick = (lambda hi, en: hi) if lang == "hi" else (lambda hi, en: en)
    other = (lambda hi, en: en) if lang == "hi" else (lambda hi, en: hi)
    title = re.search(r"<title>⟮(.*?)‖(.*?)⟯</title>", tpl, re.S)
    D = {"cur": lang, "t": {}, "a": {}, "title": {"hi": title.group(1), "en": title.group(2)}}
    counter = [0]

    def nid():
        counter[0] += 1
        return str(counter[0])

    s = wa_links(tpl)

    if mode == "preview":  # one inlined image per <img>, no responsive variants, no preload
        s = re.sub(r'\s(?:srcset|sizes)="[^"]*"', "", s)
        s = re.sub(r'<link rel="preload" as="image"[^>]*>\n?', "", s)

    def attr(m):
        name, hi, en = m.group(1), m.group(2), m.group(3)
        k = nid()
        D["a"][k] = other(hi, en)
        return '%s="%s" data-ia-%s="%s"' % (name, pick(hi, en), name, k)

    s = re.sub(r'([a-zA-Z][\w:-]*)="⟪(.*?)‖(.*?)⟫"', attr, s)
    s = re.sub(r"⟮(.*?)‖(.*?)⟯", lambda m: pick(m.group(1), m.group(2)), s, flags=re.S)

    def text(m):
        hi, en = m.group(1), m.group(2)
        k = nid()
        D["t"][k] = other(hi, en)
        return '<span data-i="%s">%s</span>' % (k, pick(hi, en))

    s = re.sub(r"⟦(.*?)‖(.*?)⟧", text, s, flags=re.S)

    # Root-absolute on the site: the language switch changes the address between / and /en/ without
    # reloading, so relative URLs (lazy images, srcset) would resolve against the wrong folder.
    base = "/" if mode == "site" else ""
    s = re.sub(r"\{\{IMG:([^}]+)\}\}", lambda m: asset("images", m.group(1), base, mode), s)
    s = re.sub(r"\{\{ICON:([^}]+)\}\}", lambda m: icon(m.group(1), mode), s)
    page_url = site_url + ("/" if lang == "hi" else "/en/")
    hi_href, en_href = ("/", "/en/") if mode == "site" else ("./", "en/")
    verify = verification_meta() if lang == "hi" else ""
    s = s.replace("{{VERIFY}}\n", verify + "\n" if verify else "")
    for k, v in {"{{SITE}}": site_url, "{{PAGE_URL}}": page_url, "{{LANG}}": lang, "{{BASE}}": base,
                 "{{HI_HREF}}": hi_href, "{{EN_HREF}}": en_href, "{{LASTMOD}}": lastmod,
                 "{{FONT_FACES}}": font_faces(base, mode)}.items():
        s = s.replace(k, v)

    strip = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
    qa = re.findall(r"<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", s, re.S)
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "@id": page_url + "#faq",
           "inLanguage": "hi-IN" if lang == "hi" else "en-IN", "isPartOf": {"@id": site_url + "/#website"},
           "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]}
    s = s.replace("{{FAQ_JSONLD}}", json.dumps(faq, ensure_ascii=False, indent=2).replace("</", "<\\/"))
    s = s.replace("{{DICT}}", json.dumps(D, ensure_ascii=False).replace("</", "<\\/"))
    s = add_csp(s, "%s/%s" % (lang, mode)) if mode == "site" else s.replace("{{CSP}}\n", "")
    check_markers(s, "%s/%s" % (lang, mode))
    return s


def render_404(site_url):
    """Served by Vercel for any unknown path at any depth, so every URL in it is root-relative."""
    s = wa_links(SRC_404.read_text(encoding="utf-8"))
    s = re.sub(r"\{\{IMG:([^}]+)\}\}", lambda m: asset("images", m.group(1), "/", "site"), s)
    s = re.sub(r"\{\{ICON:([^}]+)\}\}", lambda m: icon(m.group(1), "site"), s)
    s = s.replace("{{FONT_FACES}}", font_faces("/", "site")).replace("{{SITE}}", site_url)
    s = add_csp(s, "404")
    check_markers(s, "404")
    return s


def content_date():
    """The sitemap <lastmod>/dateModified should change only when the content does (Google ignores
    lastmod that changes on every deploy). A fingerprint of every source file is kept in sitemap.xml;
    the date carries over while the fingerprint matches, and becomes today's date when it does not."""
    h = hashlib.sha256()
    files = [SRC, SRC_404, pathlib.Path(__file__).resolve()]
    files += sorted(p for d in ("images", "fonts") for p in (SITE / d).iterdir() if p.is_file())
    for p in files:
        data = p.read_bytes()
        if p.suffix in (".html", ".py"):
            data = data.replace(b"\r\n", b"\n")
        h.update(p.name.encode("utf-8") + b"\0" + data + b"\0")
    fingerprint = h.hexdigest()[:16]
    old = SITE / "sitemap.xml"
    m = re.search(r"<!-- content ([0-9a-f]+) (\d{4}-\d{2}-\d{2}) -->", old.read_text(encoding="utf-8")) if old.exists() else None
    if m and m.group(1) == fingerprint:
        return fingerprint, m.group(2)
    return fingerprint, datetime.date.today().isoformat()


def seo_files(site_url, fingerprint, lastmod):
    alt = ('    <xhtml:link rel="alternate" hreflang="hi" href="{u}/"/>\n'
           '    <xhtml:link rel="alternate" hreflang="en" href="{u}/en/"/>\n'
           '    <xhtml:link rel="alternate" hreflang="x-default" href="{u}/"/>\n').format(u=site_url)
    imgs = "".join("    <image:image><image:loc>%s/images/%s</image:loc></image:image>\n" % (site_url, f) for f in PHOTOS)
    urls = "".join("  <url>\n    <loc>%s</loc>\n%s    <lastmod>%s</lastmod>\n%s  </url>\n" % (site_url + p, alt, lastmod, imgs) for p in ("/", "/en/"))
    write(SITE / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<!-- content %s %s -->\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml"'
          ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' % (fingerprint, lastmod)
          + urls + "</urlset>\n")
    write(SITE / "robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % site_url)
    write(SITE / "llms.txt", f"""# Sunil Charora (सुनील चरौरा)

> Rashtriya Lok Dal (RLD) leader from the Jahangirabad–Anupshahr area of Bulandshahr district, Uttar Pradesh, India, and a former member of the Bulandshahr Zila Panchayat (Ward No. 50). Works on farmers' issues, youth employment, students' welfare, women's safety and the development of Anupshahr Assembly constituency (No. 67).

Key facts:
- Name: Sunil Charora. Hindi: सुनील चरौरा (also written सुनील चरोरा; Latin variant Sunil Charaura)
- Party: Rashtriya Lok Dal (RLD, राष्ट्रीय लोक दल, रालोद); national president Jayant Chaudhary
- Former post: Zila Panchayat Member, Ward No. 50, Bulandshahr
- Area of work: Jahangirabad–Anupshahr, Bulandshahr district, Uttar Pradesh
- Assembly constituency: Anupshahr (No. 67; officially also spelt Anoopshahr), part of the Bulandshahr Lok Sabha constituency
- Phone / WhatsApp: +91 97191 66039
- Facebook: https://www.facebook.com/SunilCharoraRLD/
- Public-service help desk: assistance with forms for PM-Kisan, Kisan Credit Card, crop insurance, Ayushman card, pensions, scholarships, skill training, housing and Ujjwala. This is a private initiative, not a government portal.

## Pages
- [Hindi, default]({site_url}/): about, pledges, scheme help, FAQ, contact
- [English]({site_url}/en/): the same content in English

## Optional
- Website designed and developed by First Compile (Garvit Oberoi, +91 70173 04973)
""")
    write(SITE / "humans.txt", f"""/* TEAM */
Client: Shri Sunil Charora, Rashtriya Lok Dal, Anupshahr (67), Bulandshahr
Design, development and digital marketing: First Compile
Developer: Garvit Oberoi
Phone / WhatsApp: +91 70173 04973
Location: India

/* SITE */
Last update: {lastmod}
Languages: Hindi, English
Standards: HTML5, CSS3, schema.org JSON-LD
Fonts: Khand, Martel Sans (SIL Open Font License)
Hosting: Vercel
""")
    write(SITE / "site.webmanifest", json.dumps({
        "id": "/", "name": "सुनील चरौरा | Sunil Charora", "short_name": "सुनील चरौरा",
        "description": "सुनील चरौरा, राष्ट्रीय लोक दल, अनूपशहर विधानसभा (67), बुलंदशहर",
        "lang": "hi", "dir": "ltr", "start_url": "/", "scope": "/", "display": "browser",
        "theme_color": "#0B7A3C", "background_color": "#FFFFFF",
        "icons": [{"src": "/images/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "/images/icon-512.png", "sizes": "512x512", "type": "image/png"}]},
        ensure_ascii=False, indent=2) + "\n")


def main():
    site_url, source = site_address()
    print("Site URL: %s  (from %s)" % (site_url, source))
    tpl = SRC.read_text(encoding="utf-8")
    fingerprint, lastmod = content_date()
    write(SITE / "index.html", render(tpl, "hi", "site", site_url, lastmod))
    write(SITE / "en" / "index.html", render(tpl, "en", "site", site_url, lastmod))
    write(SITE / "404.html", render_404(site_url))
    seo_files(site_url, fingerprint, lastmod)
    outputs = ["site/index.html", "site/en/index.html", "site/404.html"]
    if not os.environ.get("VERCEL") and "--no-preview" not in sys.argv:
        write(ROOT / "preview.html", render(tpl, "hi", "preview", site_url, lastmod))
        outputs.append("preview.html")
    for p in outputs:
        print("%-20s %7.1f KB" % (p, (ROOT / p).stat().st_size / 1024))
    print("Content date: %s" % lastmod)


if __name__ == "__main__":
    main()
