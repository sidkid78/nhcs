import os
from pathlib import Path

renders_dir = Path('renders')
images = sorted([f.name for f in renders_dir.glob('*.png')])

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Renders Gallery</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            background-color: #0a0a0a;
            color: #e2e8f0;
            margin: 0;
            padding: 2rem;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 0.5rem;
            color: #fff;
            font-weight: 300;
            letter-spacing: 0.05em;
        }}
        .stats {{
            text-align: center;
            color: #64748b;
            margin-bottom: 3rem;
            font-family: monospace;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            max-width: 1800px;
            margin: 0 auto;
        }}
        .card {{
            background: #121212;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid #222;
            transition: all 0.2s ease;
            display: flex;
            flex-direction: column;
        }}
        .card:hover {{
            transform: translateY(-2px);
            border-color: #444;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }}
        .card img {{
            width: 100%;
            aspect-ratio: 1;
            object-fit: cover;
            display: block;
            border-bottom: 1px solid #222;
            background: #000;
        }}
        .card .info {{
            padding: 1rem;
            text-align: center;
            font-family: monospace;
            font-size: 0.9em;
            color: #94a3b8;
            background: #111;
        }}
        .highlight {{
            color: #fb7185; /* For beta_2=1 or highest SDR concept mentioned */
        }}
    </style>
</head>
<body>
    <h1>TPMM Concept Renders</h1>
    <div class="stats">{len(images)} unique topological structures translated to physical fields</div>
    <div class="gallery">
"""

for img in images:
    name = img.replace('_hopf.png', '')
    # Highlight 6438cec8 as mentioned by the user
    highlight_class = ' highlight' if '6438cec8' in name else ''
    
    html_content += f"""
        <div class="card">
            <img src="renders/{img}" alt="{name}" loading="lazy">
            <div class="info{highlight_class}">{name}</div>
        </div>
"""

html_content += """
    </div>
</body>
</html>
"""

with open('gallery.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Gallery generated at gallery.html with {len(images)} images.")
