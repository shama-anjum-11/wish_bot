import gradio as gr
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import os
import textwrap
import emoji
import re

with open("style.css", "r") as f:
    custom_css = f.read()


# Configure Gemini
genai.configure(api_key="AIzaSyAKDp_FeISIi0hh1yuHJPTHNYHRn3SJR38")
model = genai.GenerativeModel("gemini-1.5-flash")

def extract_keywords(user_text):
    prompt = f"""
You are a helpful assistant. Extract structured data from this sentence:
"{user_text}"
Return only this format (do NOT add extra explanation):
{{
  "name": "<recipient's name or blank>",
  "occasion": "<event like birthday, marriage, farewell, etc or blank>",
  "relationship": "<relationship like sister, friend, teacher or blank>"
}}
If anything is missing, keep it blank.
"""
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.strip())
    except:
        return {"name": "", "occasion": "", "relationship": ""}

def generate_wish(name, occasion, relationship, tone, use_emoji=False):
    emoji_part = " Add emojis to match the tone." if use_emoji else ""
    if name or occasion or relationship:
        context = []
        if name:
            context.append(f"to {name}")
        if occasion:
            context.append(f"for their {occasion}")
        if relationship:
            context.append(f"who is my {relationship}")
        context_text = " ".join(context)
    else:
        context_text = "someone special"
    prompt = f"""
Write a {tone.lower()} wish {f'{context_text}' if context_text else ''}.
It should be polite, thoughtful, and creative. Keep it to 2–3 lines. {emoji_part}
Avoid repeating sender names.
If you don’t have enough details, generate a beautiful, general-purpose wish like:
‘Have a wonderful day ahead!’
"""
    response = model.generate_content(prompt)
    return response.text.strip()

def is_emoji(char):
    return char in emoji.EMOJI_DATA

def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map
        u"\U0001F700-\U0001F77F"  # alchemical
        u"\U0001F780-\U0001F7FF"  # geometric
        u"\U0001F800-\U0001F8FF"  # arrows
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA00-\U0001FA6F"  # chess
        u"\U0001FA70-\U0001FAFF"  # legacy computing
        u"\U00002700-\U000027BF"  # Dingbats
        u"\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def create_gradient_background(color, width, height):
    img = Image.new("RGB", (width, height), color)
    return img

def create_card(wish_text, font_name, background_style, font_color, sender_name="", tone="Natural", background_image_path=None, quote_style=True):
    width, height = 1000, 600
    if background_image_path and os.path.exists(background_image_path):
        img = Image.open(background_image_path).convert("RGB").resize((width, height))
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 120))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
    else:
        gradient_colors = {
            "Sunset": (255, 153, 153),
            "Ocean Blue": (102, 178, 255),
            "Lavender": (204, 153, 255),
            "Peach Glow": (255, 204, 153),
            "Midnight Sky": (51, 51, 102),
            "Mint Breeze": (153, 255, 204),
            "Rose Cloud": (255, 179, 230),
            "Golden Hour": (255, 214, 102)
        }
        color = gradient_colors.get(background_style, (240, 240, 240))
        img = create_gradient_background(color, width, height).convert("RGBA")

    draw = ImageDraw.Draw(img)

    font_paths = {
        "Cursive": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/PlaywriteRO-VariableFont_wght.ttf",
        "Handwritten": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/PlaywriteAUSA-VariableFont_wght.ttf",
        "Handwritten 2": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/Caveat-VariableFont_wght.ttf",
        "Normal": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/NationalPark-VariableFont_wght.ttf",
        "Default": "seguiemj.ttf",
        "Times New Roman": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/PlayfairDisplay-VariableFont_wght.ttf",
        "Italic" : "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/PlayfairDisplay-Italic-VariableFont_wght.ttf",
        "Retro": "C:/Users/shama/OneDrive/Desktop/wishbot/fonts/Tagesschrift-Regular.ttf",
    }

    try:
        font_path = font_paths.get(font_name, "arial.ttf")
        font = ImageFont.truetype(font_path, 44)
        emoji_font = ImageFont.truetype("seguiemj.ttf", 44)
    except:
        font = ImageFont.load_default()
        emoji_font = font

    wrapped_text = textwrap.wrap(wish_text, width=30)
    if sender_name and "with love" not in wish_text.lower():
        wrapped_text.append("")
        wrapped_text.append(f"With love,\n{sender_name}")

    if quote_style:
        max_width = max(draw.textlength(line, font=font) for line in wrapped_text)
        line_height = font.getbbox('A')[3] + 10
        box_width = int(max_width + 40)
        box_height = int(len(wrapped_text) * line_height + 40)
        box_x = int((width - box_width) // 2)
        box_y = int(80)

        box_overlay = Image.new("RGBA", (box_width, box_height), (255, 255, 255, int(255 * 0.3)))
        img.paste(box_overlay, (box_x, box_y), box_overlay)
        y_text = box_y + 20
    else:
        y_text = 100

    for line in wrapped_text:
        x = (width - draw.textlength(line, font=font)) // 2
        for char in line:
            current_font = emoji_font if is_emoji(char) else font
            draw.text((x, y_text), char, font=current_font, fill=font_color)
            x += draw.textlength(char, font=current_font)
        y_text += 60

    file_path = "generated_card.png"
    img.convert("RGB").save(file_path)
    return file_path

def full_wish_bot(user_text, tone, font_name, background_style, font_color, sender_name, bg_image, use_emoji):
    extracted = extract_keywords(user_text)
    name = extracted.get("name", "").strip()
    occasion = extracted.get("occasion", "").strip()
    relationship = extracted.get("relationship", "").strip()

    wish = generate_wish(name, occasion, relationship, tone, use_emoji)

    if sender_name and "with love" not in wish.lower():
        wish += f"\n\nWith love,\n{sender_name}"

    wish_for_card = remove_emojis(wish)

    card_file = create_card(wish_for_card, font_name, background_style, font_color, sender_name=sender_name, tone=tone, background_image_path=bg_image)

    return wish, wish, card_file

with gr.Blocks(css=custom_css, theme="soft") as demo:
    demo.title = "WishBot"
    gr.Markdown("<h1 class='custom-title'>✨WishBot💌</h1>")
    gr.Markdown("<h2 class='subtitle'>Beautiful Wishes for Your Loved Ones!🎀</h2>")
    with gr.Row():
        user_text = gr.Textbox(label="Describe your wish request")
        tone_dropdown = gr.Dropdown([
            "Formal", "Natural", "Funny", "Emotional", "Romantic", "Motivational", "Calm", "Exciting", "Poetic"
        ], label="Choose tone", value="Natural")
    with gr.Row():
        font_dropdown = gr.Dropdown([
            "Cursive", "Handwritten", "Handwritten 2", "Normal", "Default", "Times New Roman", "Italic", "Retro"
        ], label="Font (Emoji-safe supported)", value="Handwritten")
        background_dropdown = gr.Dropdown([
            "Sunset", "Ocean Blue", "Lavender", "Peach Glow", "Midnight Sky", "Mint Breeze", "Rose Cloud", "Golden Hour"
        ], label="Background Style", value="Sunset")
        color_dropdown = gr.Dropdown(["black", "white"], label="Font Color", value="black")
    with gr.Row():
        sender_name = gr.Textbox(label="Your Name (optional)")
        bg_image = gr.Image(type="filepath", label="Upload Background (optional)")
    use_emoji = gr.Checkbox(label="Add Emojis to Wish", elem_id="emoji_checkbox" , value= True)


    with gr.Column(scale=1):
        output_text = gr.Textbox(label="Generated Wish", lines=5, interactive=False, show_copy_button=True)
    card_output = gr.Image(type="filepath", label="Downloadable Card")
    generate_btn = gr.Button("Generate Wish")

    generate_btn.click(
        fn=full_wish_bot,
        inputs=[user_text, tone_dropdown, font_dropdown, background_dropdown, color_dropdown, sender_name, bg_image, use_emoji],
        outputs=[output_text, output_text, card_output]
    )



demo.launch()






