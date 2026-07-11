from flask import Blueprint, Response, url_for

seo_bp = Blueprint("seo", __name__)

PUBLIC_ENDPOINTS = [
    "main.landing", "main.about", "main.contact", "main.faq",
    "main.privacy", "main.terms", "main.cookies",
    "auth.login", "auth.register", "auth.driver_register", "auth.business_register",
]


@seo_bp.route("/robots.txt")
def robots():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /dashboard/\n"
        "Disallow: /driver/\n"
        "Disallow: /business/\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        f"Sitemap: {url_for('seo.sitemap', _external=True)}\n"
    )
    return Response(body, mimetype="text/plain")


@seo_bp.route("/sitemap.xml")
def sitemap():
    urls = [url_for(endpoint, _external=True) for endpoint in PUBLIC_ENDPOINTS]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f"<url><loc>{u}</loc></url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")
