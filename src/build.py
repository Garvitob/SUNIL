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
  VERCEL_PROJECT_PRODUCTION_URL    set by Vercel during its build: the SHORTEST custom domain on the
                                   project (set SITE_URL if www is the main address), otherwise the
                                   project's *.vercel.app address. Redeploy after adding a domain.
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
PAGES_DIR = ROOT / "src" / "pages"
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
    for i, arg in enumerate(sys.argv):
        if arg == "--site" or arg.startswith("--site="):
            value = arg[len("--site="):] if "=" in arg else (sys.argv[i + 1] if i + 1 < len(sys.argv) else "")
            if not value or value.startswith("--"):
                sys.exit("--site needs a URL, e.g. --site https://www.example.in")
            return clean(value), "--site"
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
    for tag in re.findall(r"<style\b[^>]*>", s, re.I):
        if tag != "<style>":
            sys.exit("%s: unexpected style tag %s (the CSP only allows plain inline <style> blocks)" % (where, tag))
    if re.search(r"<[^>]+\s(?:style|on[a-z]+)=", s, re.I):
        sys.exit('%s: style="" and on*="" attributes are blocked by the CSP; use a class / addEventListener' % where)
    scripts = [csp_hash(x) for x in re.findall(r"<script>(.*?)</script>", s, re.S)]
    styles = [csp_hash(x) for x in re.findall(r"<style>(.*?)</style>", s, re.S)]
    if same_origin_js:
        scripts.insert(0, "'self'")
    policy = ("default-src 'none'; script-src %s; style-src %s; img-src 'self'; font-src 'self'; connect-src 'self'; "
              "manifest-src 'self'; base-uri 'none'; form-action 'none'; upgrade-insecure-requests") % (
        " ".join(scripts) or "'none'", " ".join(styles) or "'none'")
    return s.replace("{{CSP}}", '<meta http-equiv="Content-Security-Policy" content="%s">' % policy, 1)


def check_jsonld(s, where):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(block)
        except ValueError as e:
            sys.exit("%s: invalid JSON-LD (%s). Check quotes in the ⟮…⟯ head text." % (where, e))


def check_markers(s, where):
    left = re.findall(r"⟦|⟧|⟪|⟫|⟮|⟯|‖|\{\{[A-Z_]+|\{wa(?:-dev)?:", s)
    if left:
        sys.exit("Unprocessed markers in %s: %s" % (where, sorted(set(left))))


def load_pages():
    """Each src/pages/*.html is one page: an <!--page ... --> header (slug, type, title, description,
    og_title, og_desc, crumb) followed by its <main>. It is served at /<slug> (Hindi) and /en/<slug>."""
    pages = []
    for path in sorted(PAGES_DIR.glob("*.html"), key=lambda p: p.name):
        where = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        m = re.match(r"<!--page[ \t]*\n(.*?)\n[ \t]*-->[ \t]*\n", text, re.S)
        if not m:
            sys.exit("%s: missing the <!--page ... --> header" % where)
        meta = {k: v.strip() for k, v in re.findall(r"^(\w+):[ \t]*(.*)$", m.group(1), re.M)}
        for key in ("type", "title", "description", "crumb"):
            if not meta.get(key):
                sys.exit("%s: the page header needs '%s:'" % (where, key))
        meta["og_title"] = meta.get("og_title") or meta["title"]
        meta["og_desc"] = meta.get("og_desc") or meta["description"]
        for key in ("title", "description", "og_title", "og_desc", "crumb"):  # these go into content="..." attributes
            if not re.fullmatch(r'⟮[^‖⟮⟯⟦⟧⟪⟫"<>]+‖[^‖⟮⟯⟦⟧⟪⟫"<>]+⟯', meta[key]):
                sys.exit('%s: %s must be one line written as ⟮हिंदी‖English⟯, without " < >' % (where, key))
        if "slug" not in meta:
            sys.exit("%s: the page header needs 'slug:' (left empty only on the home page)" % where)
        slug = meta["slug"].strip("/")
        if slug and (not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:/[a-z0-9]+(?:-[a-z0-9]+)*)*", slug)
                     or slug.split("/")[0] in ("en", "images", "fonts")):
            sys.exit("%s: slug '%s' must be lowercase-words-with-hyphens and not start with en/, images/ or fonts/" % (where, slug))
        meta["slug"] = slug + "/" if slug else ""
        meta["file"] = where
        meta["body"] = text[m.end():]
        pages.append(meta)
    slugs = [p["slug"] for p in pages]
    dup = sorted({s or "(home)" for s in slugs if slugs.count(s) > 1})
    if dup:
        sys.exit("src/pages: more than one page uses the slug %s" % ", ".join(dup))
    pages.sort(key=lambda p: p["slug"] != "")
    if not pages or pages[0]["slug"] != "":
        sys.exit("src/pages needs a home page with an empty slug")
    return pages


def page_ld(page):
    """The page's own node(s) in the JSON-LD @graph (marker strings are resolved per language later)."""
    node = {"@type": page["type"], "@id": "{{PAGE_URL}}#webpage", "url": "{{PAGE_URL}}", "name": page["title"],
            "description": page["description"], "inLanguage": "⟮hi-IN‖en-IN⟯", "isPartOf": {"@id": "{{SITE}}/#website"},
            "about": {"@id": "{{SITE}}/#person"}}
    if page["type"] == "ProfilePage":
        node["mainEntity"] = {"@id": "{{SITE}}/#person"}
    node["primaryImageOfPage"] = {"@id": "{{SITE}}/#portrait"}
    node["dateModified"] = "{{LASTMOD}}"
    nodes = [node]
    if page["slug"]:
        node["breadcrumb"] = {"@id": "{{PAGE_URL}}#breadcrumb"}
        nodes.append({"@type": "BreadcrumbList", "@id": "{{PAGE_URL}}#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "⟮सुनील चरौरा‖Sunil Charora⟯", "item": "{{HOME_URL}}"},
            {"@type": "ListItem", "position": 2, "name": page["crumb"], "item": "{{PAGE_URL}}"}]})
    dump = lambda n: "\n".join("    " + line for line in json.dumps(n, ensure_ascii=False, indent=2).split("\n"))
    return ",\n".join(dump(n) for n in nodes)


def compose(shell, page, pages):
    """Shared shell + one page: head values, <main>, and links that work from any page in either language.
    {{LINK:slug/#anchor}} in a page links to another page (and swaps with the language switch);
    {{HOME_LINK:anchor}} in the shell is an in-page anchor on the home page and a link to it elsewhere."""
    slugs = {p["slug"] for p in pages}
    page.setdefault("targets", set())  # (slug, anchor) pairs, checked against the rendered pages in main()

    def link(target):
        slug, _, anchor = target.partition("#")
        if slug not in slugs:
            sys.exit("%s: link to unknown page '%s'" % (page["file"], target))
        if anchor:
            page["targets"].add((slug, anchor))
        return "⟪/%s‖/en/%s⟫" % (target, target)

    def home_link(m):
        if not page["slug"]:
            page["targets"].add(("", m.group(1)))
            return "#" + m.group(1)
        return link("" if m.group(1) == "top" else "#" + m.group(1))

    s = shell.replace("{{MAIN}}\n", page["body"])
    s = re.sub(r"\{\{HOME_LINK:([\w-]+)\}\}", home_link, s)
    s = re.sub(r"\{\{LINK:([^}]*)\}\}", lambda m: link(m.group(1)), s)
    for k, v in {"{{P_TITLE}}": page["title"], "{{P_DESC}}": page["description"], "{{P_OG_TITLE}}": page["og_title"],
                 "{{P_OG_DESC}}": page["og_desc"], "{{SLUG}}": page["slug"], "{{PAGE_LD}}": page_ld(page)}.items():
        s = s.replace(k, v)
    return s


def resolve(text, lang):
    """⟮hi‖en⟯ / ⟦hi‖en⟧ -> one language (for plain-text outputs such as llms.txt)."""
    i = 0 if lang == "hi" else 1
    return re.sub(r"[⟮⟦](.*?)‖(.*?)[⟯⟧]", lambda m: m.group(1 + i), text, flags=re.S)


def render(shell, page, pages, lang, mode, site_url, lastmod):
    tpl = compose(shell, page, pages)
    nested = re.search(r"⟦[^⟧]*⟪", tpl)
    if nested:  # the language switch swaps a ⟦⟧ span's HTML first, so a ⟪⟫ attribute inside it would swap wrongly
        sys.exit("%s: put links/attributes with ⟪…⟫ outside ⟦…⟧ text: ...%s" % (page["file"], nested.group(0)[-80:]))
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
    home_url = site_url + ("/" if lang == "hi" else "/en/")
    page_url = home_url + page["slug"]
    hi_href, en_href = ("/" + page["slug"], "/en/" + page["slug"]) if mode == "site" else ("./", "en/")
    verify = verification_meta() if (lang == "hi" and not page["slug"]) else ""
    s = s.replace("{{VERIFY}}\n", verify + "\n" if verify else "")
    for k, v in {"{{SITE}}": site_url, "{{PAGE_URL}}": page_url, "{{HOME_URL}}": home_url, "{{LANG}}": lang,
                 "{{BASE}}": base, "{{HI_HREF}}": hi_href, "{{EN_HREF}}": en_href, "{{LASTMOD}}": lastmod,
                 "{{FONT_FACES}}": font_faces(base, mode)}.items():
        s = s.replace(k, v)

    where = "%s %s/%s" % (page["file"], lang, mode)
    strip = lambda h: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
    qa = re.findall(r"<details>\s*<summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", s, re.S)
    if qa:
        faq = {"@context": "https://schema.org", "@type": "FAQPage", "@id": page_url + "#faq",
               "inLanguage": "hi-IN" if lang == "hi" else "en-IN", "isPartOf": {"@id": page_url + "#webpage"},
               "mainEntity": [{"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(re.sub(r"\s*<a\b[^>]*>.*?</a>", "", a, flags=re.S))}} for q, a in qa]}
        s = s.replace("{{FAQ_JSONLD}}", json.dumps(faq, ensure_ascii=False, indent=2).replace("</", "<\\/"))
    else:
        s = s.replace('<script type="application/ld+json">\n{{FAQ_JSONLD}}\n</script>\n', "")
    s = s.replace("{{DICT}}", json.dumps(D, ensure_ascii=False).replace("</", "<\\/"))
    s = add_csp(s, where) if mode == "site" else s.replace("{{CSP}}\n", "")
    check_jsonld(s, where)
    check_markers(s, where)
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
    by_name = lambda p: (p.parent.name, p.name)
    files = [SRC, SRC_404, pathlib.Path(__file__).resolve()] + sorted(PAGES_DIR.glob("*.html"), key=by_name)
    files += sorted((p for d in ("images", "fonts") for p in (SITE / d).iterdir()
                     if p.is_file() and p.suffix.lower() in (".webp", ".jpg", ".jpeg", ".png", ".ico", ".woff2", ".txt")), key=by_name)
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


def seo_files(site_url, pages, fingerprint, lastmod):
    urls = ""
    for page in pages:
        slug = page["slug"]
        alt = ('    <xhtml:link rel="alternate" hreflang="hi" href="{u}/{s}"/>\n'
               '    <xhtml:link rel="alternate" hreflang="en" href="{u}/en/{s}"/>\n'
               '    <xhtml:link rel="alternate" hreflang="x-default" href="{u}/{s}"/>\n').format(u=site_url, s=slug)
        imgs = "" if slug else "".join("    <image:image><image:loc>%s/images/%s</image:loc></image:image>\n" % (site_url, f) for f in PHOTOS)
        for prefix in ("/", "/en/"):
            urls += "  <url>\n    <loc>%s%s%s</loc>\n%s    <lastmod>%s</lastmod>\n%s  </url>\n" % (site_url, prefix, slug, alt, lastmod, imgs)
    page_list = "\n".join("- [%s](%s/%s): %s\n- [%s](%s/en/%s): %s" % (
        resolve(p["crumb"], "hi") + " (हिंदी)", site_url, p["slug"], resolve(p["description"], "en"),
        resolve(p["crumb"], "en") + " (English)", site_url, p["slug"], resolve(p["description"], "en")) for p in pages)
    write(SITE / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<!-- content %s %s -->\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml"'
          ' xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' % (fingerprint, lastmod)
          + urls + "</urlset>\n")
    write(SITE / "robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % site_url)
    write(SITE / "llms.txt", f"""# Sunil Charora (सुनील चरौरा)

> Rashtriya Lok Dal (RLD) leader from the Jahangirabad–Anupshahr area of Bulandshahr district, Uttar Pradesh, India. Twice a member of the Bulandshahr Zila Panchayat (2010–2015 Ward No. 43, 2015–2020 Ward No. 50). A probable candidate (contender) for the 2027 Anupshahr Assembly (Vidhan Sabha, No. 67) election and a strong contender from Zila Panchayat Ward No. 50. Works on farmers' issues, youth employment, students' welfare, women's safety and the development of Anupshahr.

Key facts:
- Name: Sunil Charora. Hindi: सुनील चरौरा (also written सुनील चरोरा; Latin variant Sunil Charaura)
- Party: Rashtriya Lok Dal (RLD, राष्ट्रीय लोक दल, रालोद); national president Jayant Chaudhary
- Zila Panchayat record: member, Bulandshahr, 2010–2015 (Ward No. 43) and 2015–2020 (Ward No. 50). In 2021 the seat was reserved for women; his wife Smt. Geeta Charora contested and won (2021–2026).
- 2027: probable candidate / contender for Anupshahr Vidhan Sabha (No. 67), अनूपशहर विधानसभा 2027 के संभावित प्रत्याशी. Official candidates are announced by parties.
- Zila Panchayat: strong contender from Ward No. 50 (वार्ड नं. 50) in the next Bulandshahr Zila Panchayat election
- Known for: simple manner, direct phone/WhatsApp contact, grassroots work (जनता से जुड़े, सरल स्वभाव)
- Area of work: Jahangirabad–Anupshahr, Bulandshahr district, Uttar Pradesh
- Assembly constituency: Anupshahr (No. 67; officially also spelt Anoopshahr), part of the Bulandshahr Lok Sabha constituency
- Phone / WhatsApp: +91 97191 66039
- Facebook: https://www.facebook.com/SunilCharoraRLD/
- Public-service help desk: assistance with forms for PM-Kisan, Kisan Credit Card, crop insurance, Ayushman card, pensions, scholarships, skill training, housing and Ujjwala. This is a private initiative, not a government portal.

## Pages
{page_list}

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
    shell = SRC.read_text(encoding="utf-8")
    pages = load_pages()
    fingerprint, lastmod = content_date()

    # Render everything first, so a failing page never leaves site/ half-written.
    built = {}
    for page in pages:
        for lang, prefix in (("hi", ""), ("en", "en/")):
            built["site/%s%sindex.html" % (prefix, page["slug"])] = render(shell, page, pages, lang, "site", site_url, lastmod)
    ids = {p["slug"]: set(re.findall(r'\sid="([^"]+)"', built["site/%sindex.html" % p["slug"]])) for p in pages}
    for page in pages:
        for slug, anchor in sorted(page["targets"]):
            if anchor not in ids[slug]:
                sys.exit("%s: link to /%s#%s, but that page has no id=\"%s\"" % (page["file"], slug, anchor, anchor))
    built["site/404.html"] = render_404(site_url)
    preview = not os.environ.get("VERCEL") and "--no-preview" not in sys.argv
    if preview:
        built["preview.html"] = render(shell, pages[0], pages, "hi", "preview", site_url, lastmod)

    for out, html_text in built.items():
        write(ROOT / out, html_text)
    keep = {(ROOT / out).resolve() for out in built}
    for old in sorted(SITE.rglob("index.html")):  # a renamed or removed page must not stay online
        if old.resolve() not in keep:
            old.unlink()
            print("Removed stale page %s" % old.relative_to(ROOT).as_posix())
    seo_files(site_url, pages, fingerprint, lastmod)
    for p in built:
        print("%-48s %7.1f KB" % (p, (ROOT / p).stat().st_size / 1024))
    print("Content date: %s" % lastmod)


if __name__ == "__main__":
    main()
