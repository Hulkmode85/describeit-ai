import os
from flask import Flask, request, render_template_string, jsonify
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DescribeIt AI - Product Description Writer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0a;color:#e0e0e0;min-height:100vh}
.container{max-width:900px;margin:0 auto;padding:40px 20px}
h1{font-size:2.2rem;background:linear-gradient(135deg,#f59e0b,#ef4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
p.sub{color:#888;margin-bottom:30px;font-size:1.05rem}
form{background:#151515;border:1px solid #222;border-radius:12px;padding:30px}
label{display:block;margin-bottom:6px;color:#aaa;font-size:.9rem;margin-top:16px}
label:first-child{margin-top:0}
input,textarea,select{width:100%;padding:12px;background:#0a0a0a;border:1px solid #333;border-radius:8px;color:#fff;font-size:1rem}
textarea{height:120px;resize:vertical}
button{width:100%;padding:14px;background:linear-gradient(135deg,#f59e0b,#ef4444);border:none;border-radius:8px;color:#fff;font-size:1.1rem;cursor:pointer;font-weight:600;margin-top:24px}
button:hover{opacity:.9}
.loading{display:none;text-align:center;padding:20px;color:#f59e0b}
.badge{display:inline-block;background:#f59e0b;color:#000;padding:4px 12px;border-radius:20px;font-size:.8rem;margin-bottom:16px;font-weight:600}
</style>
</head>
<body>
<div class="container">
<span class="badge">E-Commerce Copy Engine</span>
<h1>DescribeIt AI</h1>
<p class="sub">Product descriptions, taglines, ad copy, and social posts — generated in seconds for Shopify, Amazon, DTC brands.</p>
<form method="POST" action="/generate" onsubmit="document.getElementById('load').style.display='block'">
<label>Product Name</label>
<input type="text" name="product_name" placeholder="e.g. CloudWalk Pro Running Shoes" required>
<label>Key Features (one per line or comma-separated)</label>
<textarea name="features" placeholder="Ultra-lightweight mesh upper&#10;Responsive foam midsole&#10;Reflective heel tab&#10;Available in 8 colors" required></textarea>
<label>Target Audience</label>
<input type="text" name="audience" placeholder="e.g. Active women 25-40 who run 3-5x per week">
<label>Brand Voice / Tone</label>
<select name="tone">
<option value="premium">Premium / Luxury</option>
<option value="playful">Playful / Fun</option>
<option value="professional">Professional / Clean</option>
<option value="bold">Bold / Edgy</option>
<option value="minimalist">Minimalist / Modern</option>
</select>
<label>Price Point (optional)</label>
<input type="text" name="price" placeholder="e.g. $129">
<button type="submit">Generate Product Copy</button>
</form>
<div id="load" class="loading">Generating product copy...</div>
</div>
</body>
</html>
"""

RESULT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Product Copy - DescribeIt AI</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a0a;color:#e0e0e0;min-height:100vh}
.container{max-width:900px;margin:0 auto;padding:40px 20px}
h1{font-size:1.8rem;background:linear-gradient(135deg,#f59e0b,#ef4444);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:20px}
.section{background:#151515;border:1px solid #222;border-radius:12px;padding:24px;margin-bottom:20px}
.section h3{color:#f59e0b;margin-bottom:12px;font-size:1.1rem}
.section pre{white-space:pre-wrap;line-height:1.7;font-family:'Segoe UI',sans-serif;font-size:1rem}
.copy-btn{display:inline-block;margin-top:12px;padding:8px 20px;background:linear-gradient(135deg,#f59e0b,#ef4444);border:none;border-radius:8px;color:#fff;cursor:pointer;font-size:.9rem;font-weight:600}
.copy-btn:hover{opacity:.9}
a{color:#f59e0b;text-decoration:none}
.back{display:inline-block;margin-top:20px}
</style>
</head>
<body>
<div class="container">
<h1>Generated Copy for {{ product_name }}</h1>
{% for title, content in sections %}
<div class="section">
<h3>{{ title }}</h3>
<pre id="s-{{ loop.index }}">{{ content }}</pre>
<button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('s-{{ loop.index }}').textContent);this.textContent='Copied!'">Copy to Clipboard</button>
</div>
{% endfor %}
<a class="back" href="/">&#8592; Generate More</a>
</div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(FORM_PAGE)

@app.route("/generate", methods=["POST"])
def generate():
    product_name = request.form.get("product_name", "").strip()
    features = request.form.get("features", "").strip()
    audience = request.form.get("audience", "").strip() or "general consumers"
    tone = request.form.get("tone", "professional")
    price = request.form.get("price", "").strip()

    if not product_name or not features:
        return "Product name and features are required.", 400

    price_note = f"Price point: {price}" if price else ""

    prompt = f"""You are an expert e-commerce copywriter. Generate ALL of the following for this product:

Product: {product_name}
Features: {features}
Target Audience: {audience}
Brand Voice: {tone}
{price_note}

Generate these sections, each preceded by its header line:

=== PRODUCT DESCRIPTION ===
Write a compelling 150-200 word product description optimized for e-commerce (Shopify, Amazon). Include benefits, not just features. Use sensory language.

=== TAGLINE ===
One punchy tagline (under 10 words).

=== AD COPY VARIANT 1 ===
Short Facebook/Instagram ad copy (40-60 words). Hook + benefit + CTA.

=== AD COPY VARIANT 2 ===
Google Ads style copy (30-40 words). Direct, benefit-focused.

=== AD COPY VARIANT 3 ===
Email subject line + 3-sentence email preview copy.

=== SOCIAL MEDIA POST ===
Instagram/TikTok caption with emojis, hashtags, and a hook. 50-80 words."""

    msg = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text

    sections = []
    current_title = None
    current_text = []
    for line in raw.split("\n"):
        if line.strip().startswith("===") and line.strip().endswith("==="):
            if current_title:
                sections.append((current_title, "\n".join(current_text).strip()))
            current_title = line.strip().strip("= ").strip()
            current_text = []
        else:
            current_text.append(line)
    if current_title:
        sections.append((current_title, "\n".join(current_text).strip()))

    if not sections:
        sections = [("Generated Copy", raw)]

    return render_template_string(RESULT_PAGE, product_name=product_name, sections=sections)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "DescribeIt AI"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
