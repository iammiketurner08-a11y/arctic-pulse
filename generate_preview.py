"""Generate the full-page preview for Arctic Pulse UI Concept 3 from the DOCX brief."""

from pathlib import Path
import re
from docx import Document
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
BRIEF = ROOT.parent / "upload" / "Website Brief Form (1).docx"
OUT = ROOT.parent / "arctic-pulse-ui-concept-3.jpg"

W, M = 1440, 120
C = {
    "aubergine": "#1B365D", "plum": "#0E4F59", "berry": "#167786",
    "sage": "#66C6D9", "sage_pale": "#EAF7F8", "oat": "#EEF3F5",
    "paper": "#FBFDFE", "ink": "#152B3B", "muted": "#60717D",
    "line": "#D8E3E8", "white": "#FFFFFF", "footer": "#102A46",
}
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size)


def brief_data():
    doc = Document(BRIEF)
    content = "\n".join(" ".join(p.text.split()) for p in doc.paragraphs if p.text.strip())

    def field(name, fallback):
        match = re.search(rf"^{re.escape(name)}:\s*(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else fallback

    return {
        "name": field("Business Name", "ARCTIC PULSE HUMAN PERFORMANCE & WELLNESS LTD"),
        "contact": field("Contact Person", "Samuel Cabrera"),
        "email": field("Email Address", "arcticpulsewellness@gmail.com"),
        "phone": field("Phone Number", "(403) 918-5320"),
    }


DATA = brief_data()


def wrap(draw, text, font, width):
    lines, current = [], ""
    for word in text.split():
        trial = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=font)[2] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(draw, x, y, text, font, fill, width, gap=7, align="left"):
    lines = wrap(draw, text, font, width)
    line_h = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
    for i, line in enumerate(lines):
        line_w = draw.textbbox((0, 0), line, font=font)[2]
        px = x if align == "left" else x + (width - line_w) / 2
        draw.text((px, y + i * (line_h + gap)), line, font=font, fill=fill)
    return len(lines) * line_h + max(0, len(lines) - 1) * gap


def cover(path, box, position="center"):
    x1, y1, x2, y2 = map(int, box)
    width, height = x2 - x1, y2 - y1
    source = Image.open(path).convert("RGB")
    ratio = max(width / source.width, height / source.height)
    source = source.resize((int(source.width * ratio), int(source.height * ratio)), Image.Resampling.LANCZOS)
    left = (source.width - width) // 2
    top = 0 if position == "top" else (source.height - height) // 2
    return source.crop((left, top, left + width, top + height))


def paste_round(canvas, path, box, radius=0, position="center"):
    x1, y1, x2, y2 = map(int, box)
    image = cover(path, box, position)
    if radius:
        mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius=radius, fill=255)
        canvas.paste(image, (x1, y1), mask)
    else:
        canvas.paste(image, (x1, y1))


def paste_circle(canvas, path, box, position="top"):
    x1, y1, x2, y2 = map(int, box)
    image = cover(path, box, position)
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, image.width - 1, image.height - 1), fill=255)
    canvas.paste(image, (x1, y1), mask)


def card(canvas, box, fill, shadow=False, radius=20, outline=None):
    x1, y1, x2, y2 = box
    if shadow:
        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle((x1, y1 + 12, x2, y2 + 12), radius=radius, fill=(42, 25, 51, 36))
        canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(22)))
    ImageDraw.Draw(canvas).rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)


def gradient_rect(canvas, box, start, end, horizontal=False):
    x1, y1, x2, y2 = map(int, box)
    start_rgb, end_rgb = ImageColor.getrgb(start), ImageColor.getrgb(end)
    layer = Image.new("RGBA", (x2 - x1, y2 - y1), start_rgb + (255,))
    ld = ImageDraw.Draw(layer)
    span = (x2 - x1) if horizontal else (y2 - y1)
    for i in range(max(1, span)):
        ratio = i / max(1, span - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(start_rgb, end_rgb)) + (255,)
        if horizontal:
            ld.line((i, 0, i, y2 - y1), fill=color)
        else:
            ld.line((0, i, x2 - x1, i), fill=color)
    canvas.paste(layer, (x1, y1))


def eyebrow(draw, x, y, label, light=False):
    draw.rectangle((x, y + 7, x + 28, y + 9), fill=C["berry"])
    draw.text((x + 40, y), label.upper(), font=f(11, True), fill=C["sage_pale"] if light else C["plum"])


def button(draw, x, y, label, style="dark", width=None):
    font = f(13, True)
    label_w = draw.textbbox((0, 0), label, font=font)[2]
    width = width or label_w + 46
    styles = {
        "dark": (C["aubergine"], C["white"], C["aubergine"]),
        "light": (C["white"], C["aubergine"], C["white"]),
        "sage": (C["sage_pale"], C["aubergine"], C["sage_pale"]),
        "outline": (None, C["aubergine"], C["aubergine"]),
    }
    fill, text, outline = styles[style]
    draw.rounded_rectangle((x, y, x + width, y + 54), radius=27, fill=fill, outline=outline, width=1)
    draw.text((x + (width - label_w) / 2, y + 17), label, font=font, fill=text)
    return width


def logo(draw, x, y, light=False):
    circle_fill = C["paper"] if light else C["aubergine"]
    pulse = C["plum"] if light else C["sage_pale"]
    draw.ellipse((x, y, x + 45, y + 45), fill=circle_fill)
    pts = [(x + 6, y + 27), (x + 14, y + 27), (x + 18, y + 19), (x + 23, y + 34),
           (x + 28, y + 12), (x + 34, y + 27), (x + 40, y + 27)]
    draw.line(pts, fill=pulse, width=3, joint="curve")
    title = C["white"] if light else C["aubergine"]
    subtitle = C["sage_pale"] if light else C["berry"]
    draw.text((x + 58, y + 2), "ARCTIC PULSE", font=f(16, True), fill=title)
    draw.text((x + 58, y + 28), "HUMAN PERFORMANCE & WELLNESS", font=f(7, True), fill=subtitle)


def brand_logo(canvas, box, footer=False):
    x1, y1, x2, y2 = map(int, box)
    if footer:
        ImageDraw.Draw(canvas).rounded_rectangle((x1, y1, x2, y2), radius=14, fill=C["white"])
    logo_img = Image.open(ROOT / "assets" / "arctic-pulse-logo.png").convert("RGB")
    logo_img.thumbnail((x2 - x1 - 16, y2 - y1 - 16), Image.Resampling.LANCZOS)
    px = x1 + ((x2 - x1) - logo_img.width) // 2
    py = y1 + ((y2 - y1) - logo_img.height) // 2
    canvas.paste(logo_img, (px, py))


canvas = Image.new("RGBA", (W, 11000), C["paper"])
draw = ImageDraw.Draw(canvas)
y = 0

# Header + editorial hero
hero_h = 1040
gradient_rect(canvas, (0, y, W, y + hero_h), C["paper"], C["oat"], True)
draw = ImageDraw.Draw(canvas)
draw.ellipse((1110, 60, 1550, 500), outline="#DCCED6", width=1)
draw.ellipse((-180, 740, 290, 1210), fill="#E7E9E1")
draw.line((M, 94, W - M, 94), fill=C["line"], width=1)
brand_logo(canvas, (M, 10, M + 225, 92))
nav_x = 570
for item in ["About", "Services", "First Aid", "Direct Billing", "FAQ", "Contact"]:
    draw.text((nav_x, 40), item, font=f(11, True), fill=C["ink"])
    nav_x += draw.textbbox((0, 0), item, font=f(11, True))[2] + 25
button(draw, 1200, 20, "Book care", "dark", 120)

draw.rounded_rectangle((M, 135, M + 370, 169), radius=17, fill="#F7F4EF", outline=C["line"], width=1)
draw.ellipse((M + 14, 148, M + 21, 155), fill=C["sage"])
draw.text((M + 32, 146), "HEALTHCARE-LED WELLNESS · IQALUIT, NUNAVUT", font=f(8, True), fill=C["plum"])
draw.text((M, 205), "Move Better.", font=f(73, True), fill=C["aubergine"])
draw.text((M, 290), "Recover Stronger.", font=f(73, True), fill=C["aubergine"])
draw.text((M, 375), "Live Well.", font=f(73, True), fill=C["berry"])

lead_y = 505
lead_h = text_block(draw, M, lead_y, "Clinical expertise and human-centred care for movement, recovery, education, and wellness across Iqaluit and Nunavut.", f(16), C["muted"], 455, 7)
action_y = lead_y + lead_h + 28
bw = button(draw, M, action_y, "Book an Appointment", "dark", 215)
button(draw, M + bw + 12, action_y, "Explore services", "outline", 158)
cred_y = action_y + 94
draw.line((M, cred_y, 570, cred_y), fill=C["line"], width=1)
for i, item in enumerate(["RN", "RMT", "FST", "RED CROSS", "HEART & STROKE"]):
    x = M + i * 95
    draw.text((x, cred_y + 20), item, font=f(8, True), fill=C["plum"])

paste_round(canvas, ROOT / "assets" / "massage.jpg", (680, 470, 1320, 930), 35)
paste_round(canvas, ROOT / "assets" / "arctic.jpg", (585, 690, 850, 990), 22)
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle((585, 690, 850, 990), radius=22, outline=C["paper"], width=10)
card(canvas, (1045, 875, 1320, 960), C["aubergine"], True, 14)
draw = ImageDraw.Draw(canvas)
draw.text((1065, 893), "MOBILE CARE AVAILABLE", font=f(8, True), fill=C["sage_pale"])
draw.text((1065, 919), "At home or at your workplace", font=f(12, True), fill=C["white"])
y += hero_h

# Trust bar
proof_h = 100
draw.rectangle((0, y, W, y + proof_h), fill=C["aubergine"])
proofs = [("Licensed & Insured", "Professional care"), ("RN · RMT · CFST", "Clinical expertise"), ("Direct billing", "Available"), ("Mobile services", "Iqaluit & Nunavut")]
for i, (title, subtitle) in enumerate(proofs):
    x = M + i * 300
    if i:
        draw.line((x, y + 24, x, y + 76), fill="#513C58", width=1)
    draw.ellipse((x + 12, y + 31, x + 50, y + 69), outline="#725D78", width=1)
    draw.text((x + 31, y + 50), "✓", font=f(13, True), fill=C["sage_pale"], anchor="mm")
    draw.text((x + 66, y + 31), title, font=f(12, True), fill=C["white"])
    draw.text((x + 66, y + 55), subtitle.upper(), font=f(7, True), fill="#A99BAC")
y += proof_h

# Bento services
services_h = 1000
draw.rectangle((0, y, W, y + services_h), fill=C["paper"])
eyebrow(draw, M, y + 80, "Care with a clear purpose")
draw.text((M, y + 124), "Three ways to move forward.", font=f(48, True), fill=C["ink"])
text_block(draw, 935, y + 126, "Targeted treatment, guided mobility work, and lifesaving education—each delivered with professional clarity and personalized attention.", f(13), C["muted"], 385, 6)

card(canvas, (M, y + 260, 785, y + 740), C["plum"], False, 24)
draw = ImageDraw.Draw(canvas)
draw.text((155, y + 300), "01 · THERAPEUTIC CARE", font=f(8, True), fill=C["sage_pale"])
draw.text((155, y + 345), "Massage", font=f(35, True), fill=C["white"])
draw.text((155, y + 390), "Therapy", font=f(35, True), fill=C["white"])
text_block(draw, 155, y + 445, "Personalized treatment for pain, tension, recovery, stress, and physical performance.", f(13), "#D6CAD9", 285, 6)
paste_round(canvas, ROOT / "assets" / "massage.jpg", (435, y + 475, 785, y + 740), 0)

card(canvas, (805, y + 260, 1320, y + 740), C["sage_pale"], False, 24)
draw = ImageDraw.Draw(canvas)
draw.text((840, y + 300), "02 · GUIDED MOBILITY", font=f(8, True), fill=C["plum"])
draw.text((840, y + 345), "Fascial Stretch", font=f(31, True), fill=C["aubergine"])
draw.text((840, y + 386), "Therapy", font=f(31, True), fill=C["aubergine"])
text_block(draw, 840, y + 435, "Gentle assisted stretching to support flexibility, joint mobility, and confident movement.", f(12), C["muted"], 420, 6)
paste_round(canvas, ROOT / "assets" / "stretch.jpg", (940, y + 535, 1285, y + 730), 80)

card(canvas, (M, y + 760, 1320, y + 930), C["oat"], False, 22)
draw = ImageDraw.Draw(canvas)
draw.text((155, y + 800), "03 · PRACTICAL EDUCATION", font=f(8, True), fill=C["berry"])
draw.text((155, y + 838), "First Aid & CPR Training", font=f(28, True), fill=C["ink"])
text_block(draw, 155, y + 883, "Canadian Red Cross and Heart & Stroke instruction for healthcare professionals, workplaces, and communities.", f(11), C["muted"], 690, 5)
paste_round(canvas, ROOT / "assets" / "cpr-training.jpg", (925, y + 760, 1320, y + 930), 22)
y += services_h

# Practitioner
prac_h = 760
draw.rectangle((0, y, W, y + prac_h), fill=C["aubergine"])
draw.rectangle((0, y, 620, y + prac_h), fill=C["sage_pale"])
draw.ellipse((110, y + 85, 570, y + 545), fill="#F4F1EC")
paste_circle(canvas, ROOT / "assets" / "clinician.jpg", (125, y + 100, 555, y + 530), "top")
draw = ImageDraw.Draw(canvas)
draw.ellipse((430, y + 485, 585, y + 640), fill=C["berry"])
text_block(draw, 451, y + 523, "QUALIFIED CARE WITH A HUMAN APPROACH", f(9, True), C["white"], 112, 4, "center")
eyebrow(draw, 705, y + 92, "Meet your practitioner", True)
title_y = y + 135
title_h = text_block(draw, 705, title_y, "Clinical experience. Thoughtful care.", f(50, True), C["white"], 600, 7)
lead_y = title_y + title_h + 26
lead_h = text_block(draw, 705, lead_y, "Arctic Pulse is led by Samuel Cabrera, combining nursing experience with advanced hands-on therapy and emergency care education. Every appointment begins with careful listening and a practical path forward.", f(15), "#CFC5D2", 600, 7)
quals_y = lead_y + lead_h + 30
quals = ["Registered Nurse", "Registered Massage Therapist", "Certified FST Practitioner", "Heart & Stroke BLS Instructor", "Red Cross Training Partner", "Client-centred care"]
for i, label in enumerate(quals):
    col, row = i % 2, i // 2
    x, yy = 705 + col * 300, quals_y + row * 48
    tw = draw.textbbox((0, 0), label, font=f(9, True))[2] + 26
    draw.rounded_rectangle((x, yy, x + tw, yy + 34), radius=17, outline="#674F6D", width=1)
    draw.text((x + 13, yy + 11), label, font=f(9, True), fill=C["sage_pale"])
button(draw, 705, quals_y + 3 * 48 + 20, "Learn more about Samuel", "light", 215)
y += prac_h

# Billing
billing_h = 760
draw.rectangle((0, y, W, y + billing_h), fill=C["oat"])
eyebrow(draw, M, y + 78, "Insurance & direct billing")
draw.text((M, y + 120), "Less administration.", font=f(48, True), fill=C["ink"])
draw.text((M, y + 178), "More focus on feeling better.", font=f(48, True), fill=C["ink"])
text_block(draw, 900, y + 124, "Eligible claims can often be submitted at your appointment. Coverage depends on your individual plan.", f(14), C["muted"], 420, 6)

card(canvas, (M, y + 300, 500, y + 670), C["plum"], False, 22)
draw = ImageDraw.Draw(canvas)
draw.text((155, y + 340), "WHAT TO BRING", font=f(8, True), fill=C["sage_pale"])
text_block(draw, 155, y + 390, "Your insurance card and photo ID.", f(26, True), C["white"], 300, 7)
text_block(draw, 155, y + 500, "Contact Arctic Pulse before your visit if you would like coverage confirmed.", f(12), "#D6CAD9", 300, 6)
button(draw, 155, y + 580, "Confirm coverage", "sage", 165)

card(canvas, (520, y + 300, 1320, y + 670), C["white"], True, 22)
draw = ImageDraw.Draw(canvas)
draw.text((555, y + 335), "PARTICIPATING PROVIDERS", font=f(15, True), fill=C["ink"])
draw.ellipse((1180, y + 340, 1190, y + 350), fill=C["sage"])
draw.text((1202, y + 338), "DIRECT BILLING", font=f(7, True), fill=C["plum"])
providers = ["Canada Life", "Manulife", "Sun Life", "Alberta Blue Cross", "Medavie Blue Cross", "GreenShield", "Co-operators", "Desjardins", "Equitable Life", "iA Financial", "ClaimSecure", "+ many more"]
gx, gy, cw, ch = 555, y + 385, 182, 61
for i, label in enumerate(providers):
    col, row = i % 4, i // 4
    x, yy = gx + col * cw, gy + row * ch
    draw.rectangle((x, yy, x + cw, yy + ch), outline=C["line"], width=1)
    tw = draw.textbbox((0, 0), label, font=f(9, True))[2]
    draw.text((x + (cw - tw) / 2, yy + 23), label, font=f(9, True), fill=C["muted"])
draw.text((555, y + 590), "Direct billing is subject to eligibility, plan limitations, and insurer system availability.", font=f(8), fill=C["muted"])
y += billing_h

# Mobile care
mobile_h = 720
paste_round(canvas, ROOT / "assets" / "arctic.jpg", (0, y, W, y + mobile_h), 0)
overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
od = ImageDraw.Draw(overlay)
od.rectangle((0, y, W, y + mobile_h), fill=(27, 54, 93, 42))
canvas.alpha_composite(overlay)
card(canvas, (760, y + 80, 1320, y + 640), "#1B365DEE", True, 24)
draw = ImageDraw.Draw(canvas)
eyebrow(draw, 805, y + 125, "Mobile wellness across the North", True)
title_y = y + 168
title_h = text_block(draw, 805, title_y, "Professional wellness, wherever you need it.", f(45, True), C["white"], 460, 7)
lead_y = title_y + title_h + 25
lead_h = text_block(draw, 805, lead_y, "Healthcare-led wellness delivered directly to homes, workplaces, hotels, and corporate teams across northern schedules.", f(14), "#DDEBF0", 460, 7)
tag_y = lead_y + lead_h + 28
tx = 805
for tag in ["HOME VISITS", "WORKPLACE", "HOTEL", "CORPORATE"]:
    tw = draw.textbbox((0, 0), tag, font=f(8, True))[2] + 24
    draw.rounded_rectangle((tx, tag_y, tx + tw, tag_y + 31), radius=15, outline="#69526F", width=1)
    draw.text((tx + 12, tag_y + 10), tag, font=f(8, True), fill=C["sage_pale"])
    tx += tw + 8
button(draw, 805, tag_y + 58, "Check mobile availability", "light", 215)
y += mobile_h

# Training
training_h = 830
draw.rectangle((0, y, W, y + training_h), fill=C["paper"])
eyebrow(draw, M, y + 85, "Education that builds confidence")
title_y = y + 128
title_h = text_block(draw, M, title_y, "Lifesaving skills people remember.", f(48, True), C["ink"], 530, 7)
lead_y = title_y + title_h + 25
text_block(draw, M, lead_y, "Calm instruction, realistic practice, and clear guidance help learners feel prepared when an emergency happens.", f(14), C["muted"], 510, 7)
courses_y = lead_y + 120
courses = [("01", "Canadian Red Cross Standard First Aid & CPR", "For workplaces and communities"), ("02", "Heart & Stroke Basic Life Support", "For healthcare professionals"), ("03", "Customized workplace education", "Adapted for organizations and teams")]
for i, (num, title, sub) in enumerate(courses):
    yy = courses_y + i * 93
    card(canvas, (M, yy, 610, yy + 78), C["white"], False, 14, C["line"])
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((142, yy + 20, 180, yy + 58), fill=C["berry"])
    draw.text((161, yy + 39), num, font=f(8, True), fill=C["white"], anchor="mm")
    draw.text((200, yy + 18), title, font=f(11, True), fill=C["ink"])
    draw.text((200, yy + 45), sub, font=f(8), fill=C["muted"])
button(draw, M, courses_y + 3 * 93 + 25, "Register for a course", "dark", 185)

paste_round(canvas, ROOT / "assets" / "cpr-training.jpg", (700, y + 80, 1320, y + 700), 24)
paste_round(canvas, ROOT / "assets" / "clinician.jpg", (630, y + 555, 900, y + 790), 18, "top")
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle((630, y + 555, 900, y + 790), radius=18, outline=C["paper"], width=12)
card(canvas, (1015, y + 640, 1285, y + 760), C["sage_pale"], True, 16)
draw = ImageDraw.Draw(canvas)
draw.text((1040, y + 670), "HANDS-ON", font=f(22, True), fill=C["aubergine"])
draw.text((1040, y + 710), "SKILLS-FIRST LEARNING", font=f(8, True), fill=C["plum"])
y += training_h

# Why choose Arctic Pulse
journey_h = 600
draw.rectangle((0, y, W, y + journey_h), fill=C["sage_pale"])
eyebrow(draw, M, y + 75, "Why choose Arctic Pulse")
draw.text((M, y + 118), "Clinical expertise. Northern strength.", font=f(42, True), fill=C["ink"])
text_block(draw, 1000, y + 123, "Evidence-informed care delivered with professionalism, warmth, and a commitment to helping every client perform at their best.", f(12), C["muted"], 320, 6)
steps = [("01", "Clinical Expertise", "Care informed by nursing, registered massage therapy, and certified Fascial Stretch Therapy."), ("02", "Professional Training", "Heart & Stroke BLS instruction and Canadian Red Cross education."), ("03", "Trusted Access", "Direct billing and mobile care serving Iqaluit and Nunavut.")]
for i, (num, title, body) in enumerate(steps):
    x = M + i * 405
    card(canvas, (x, y + 265, x + 385, y + 520), "#F7F7F2", False, 18)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((x + 28, y + 295, x + 78, y + 345), outline=C["plum"], width=1)
    draw.text((x + 53, y + 320), num, font=f(9, True), fill=C["plum"], anchor="mm")
    draw.text((x + 28, y + 385), title, font=f(21, True), fill=C["ink"])
    text_block(draw, x + 28, y + 425, body, f(11), C["muted"], 320, 5)
y += journey_h

# Impact
impact_h = 670
draw.rectangle((0, y, W, y + impact_h), fill=C["paper"])
card(canvas, (M, y + 70, 710, y + 600), C["aubergine"], False, 24)
card(canvas, (730, y + 70, 1320, y + 600), C["oat"], False, 24)
draw = ImageDraw.Draw(canvas)
draw.rounded_rectangle((155, y + 105, 345, y + 137), radius=16, outline=C["sage_pale"], width=1)
draw.text((173, y + 116), "GIVING BACK THROUGH EDUCATION", font=f(7, True), fill=C["sage_pale"])
draw.text((155, y + 190), "CARE", font=f(61, True), fill=C["sage_pale"])
draw.text((155, y + 270), "THAT GIVES BACK", font=f(8, True), fill="#B8DDE4")
draw.text((155, y + 340), "Every appointment helps", font=f(27, True), fill=C["white"])
draw.text((155, y + 378), "create opportunity.", font=f(27, True), fill=C["white"])
text_block(draw, 155, y + 430, "Eligible services support deserving students through the APEAP Scholarship Program.", f(12), "#D5E4EA", 470, 6)

draw.rounded_rectangle((770, y + 105, 940, y + 137), radius=16, outline=C["plum"], width=1)
draw.text((791, y + 116), "DIGITAL GIFT CERTIFICATES", font=f(7, True), fill=C["plum"])
draw.ellipse((770, y + 175, 880, y + 285), fill=C["berry"])
draw.text((825, y + 230), "GIFT", font=f(14, True), fill=C["white"], anchor="mm")
draw.text((770, y + 335), "Give better movement,", font=f(29, True), fill=C["aubergine"])
draw.text((770, y + 373), "recovery, and time to feel well.", font=f(29, True), fill=C["aubergine"])
text_block(draw, 770, y + 425, "Digital certificates can be emailed directly to the recipient—perfect for thoughtful care from afar.", f(12), C["muted"], 480, 6)
button(draw, 770, y + 510, "Purchase a gift", "dark", 150)
y += impact_h

# Reviews
reviews_h = 620
draw.rectangle((0, y, W, y + reviews_h), fill=C["plum"])
eyebrow(draw, M, y + 75, "The client experience", True)
draw.text((M, y + 118), "Professional care that earns trust.", font=f(47, True), fill=C["white"])
draw.text((1110, y + 110), "★★★★★", font=f(19, True), fill=C["sage_pale"])
draw.text((1040, y + 150), "SAMPLE PRESENTATION · CONNECT VERIFIED REVIEWS", font=f(7, True), fill="#A99BAC")
quotes = [
    "The treatment felt focused and professional. I understood what we were working on and left moving more comfortably.",
    "Having a mobile visit made care possible around my schedule. The experience was organized and respectful.",
    "Clear instruction, practical learning, and a calm teaching style. Our team finished feeling prepared.",
]
for i, quote in enumerate(quotes):
    x = M + i * 405
    card(canvas, (x, y + 245, x + 385, y + 535), C["paper"], False, 18)
    draw = ImageDraw.Draw(canvas)
    text_block(draw, x + 28, y + 280, f"“{quote}”", f(13), C["muted"], 325, 7)
    draw.text((x + 28, y + 468), "VERIFIED CLIENT", font=f(9, True), fill=C["ink"])
    draw.text((x + 28, y + 493), "SAMPLE TESTIMONIAL PLACEHOLDER", font=f(7, True), fill=C["berry"])
y += reviews_h

# FAQ
faq_h = 700
draw.rectangle((0, y, W, y + faq_h), fill=C["paper"])
eyebrow(draw, M, y + 80, "Before your appointment")
faq_title_y = y + 122
faq_title_h = text_block(draw, M, faq_title_y, "Clear answers, before care begins.", f(45, True), C["ink"], 440, 7)
faq_lead_y = faq_title_y + faq_title_h + 25
faq_lead_h = text_block(draw, M, faq_lead_y, "Not sure which service is right for you? Contact Arctic Pulse for guidance.", f(14), C["muted"], 420, 6)
button(draw, M, faq_lead_y + faq_lead_h + 28, "Ask a question", "outline", 145)
questions = [("Do you offer direct billing?", "Yes. Direct billing is available with many major Canadian insurers when eligible."), ("What is Fascial Stretch Therapy?", None), ("Do I need a doctor's referral?", None), ("What should I wear?", None), ("What is the cancellation policy?", None)]
qx, qy = 620, y + 75
for question, answer in questions:
    row_h = 120 if answer else 88
    draw.line((qx, qy, 1320, qy), fill=C["line"], width=1)
    draw.text((qx, qy + 30), question, font=f(14, True), fill=C["ink"])
    draw.ellipse((1279, qy + 23, 1318, qy + 62), fill=C["berry"])
    draw.text((1298.5, qy + 42.5), "−" if answer else "+", font=f(15, True), fill=C["white"], anchor="mm")
    if answer:
        draw.text((qx, qy + 72), answer, font=f(9), fill=C["muted"])
    qy += row_h
draw.line((qx, qy, 1320, qy), fill=C["line"], width=1)
y += faq_h

# CTA
cta_h = 360
draw.rectangle((0, y, W, y + cta_h), fill=C["oat"])
card(canvas, (M, y + 60, 1320, y + 300), C["aubergine"], False, 26)
draw = ImageDraw.Draw(canvas)
draw.ellipse((1110, y + 105, 1390, y + 385), outline="#4D384F", width=35)
draw.text((165, y + 115), "Ready to Move Better,", font=f(35, True), fill=C["white"])
draw.text((165, y + 162), "Recover Stronger, and Live Well?", font=f(35, True), fill=C["white"])
button(draw, 905, y + 145, "Book an Appointment", "light", 220)
button(draw, 1140, y + 145, "Contact Us", "sage", 120)
y += cta_h

# Detailed footer
footer_h = 620
draw.rectangle((0, y, W, y + footer_h), fill=C["footer"])
brand_logo(canvas, (M, y + 58, M + 270, y + 218), True)
text_block(draw, M, y + 150, "Healthcare-led therapeutic care and lifesaving education for individuals, workplaces, and communities across Iqaluit and Nunavut.", f(11), "#9F929F", 350, 6)
draw.text((M, y + 280), "f     ◎", font=f(17, True), fill=C["sage_pale"])
cols = [
    (510, "SERVICES", ["Massage Therapy", "Fascial Stretch Therapy", "First Aid & CPR", "Direct Billing", "Mobile Services", "Gift Certificates"]),
    (760, "CONTACT", [DATA["phone"], DATA["email"], "Iqaluit, Nunavut", "Mobile area varies"]),
    (1060, "WELLNESS, DELIVERED", ["Mobility tips, course dates,", "and occasional practice updates."]),
]
for x, heading, items in cols:
    draw.text((x, y + 83), heading, font=f(9, True), fill=C["sage_pale"])
    for i, item in enumerate(items):
        draw.text((x, y + 128 + i * 34), item, font=f(9), fill="#9F929F")
draw.rounded_rectangle((1060, y + 223, 1320, y + 271), radius=24, fill=C["white"])
draw.text((1078, y + 239), "Email address", font=f(8), fill=C["muted"])
draw.ellipse((1273, y + 224, 1319, y + 270), fill=C["berry"])
draw.text((1296, y + 247), "→", font=f(14, True), fill=C["white"], anchor="mm")
draw.rounded_rectangle((1060, y + 305, 1320, y + 395), radius=13, outline="#4A374C", width=1)
draw.text((1078, y + 323), "APPOINTMENTS BY BOOKING", font=f(7, True), fill=C["white"])
text_block(draw, 1078, y + 350, "Mobile, in-home, and workplace visits are subject to availability.", f(8), "#9F929F", 220, 4)
draw.line((M, y + 505, W - M, y + 505), fill="#403043", width=1)
draw.text((M, y + 535), "© 2026 Arctic Pulse Human Performance & Wellness Ltd.", font=f(7), fill="#837683")
draw.text((690, y + 535), "PRIVACY  ·  TERMS  ·  ACCESSIBILITY  ·  CANCELLATION POLICY", font=f(7, True), fill="#837683")
draw.text((M, y + 580), "Modern editorial UI Concept 3 · Stock photography: Unsplash & Pexels", font=f(7), fill="#685B68")
y += footer_h

canvas = canvas.crop((0, 0, W, y)).convert("RGB")
canvas.save(OUT, quality=92, optimize=True, progressive=True, subsampling=0)
print(f"Saved {OUT} ({canvas.width}x{canvas.height}) from {BRIEF.name}")
