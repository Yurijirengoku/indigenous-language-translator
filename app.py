from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os

app = Flask(__name__)
translation_df = pd.DataFrame()

def load_translation_data():
    global translation_df
    try:
        if os.path.exists("translation_data.xlsx"):
            translation_df = pd.read_excel("translation_data.xlsx").fillna("")
            print("✅ Translation data loaded.")
        else:
            print("❌ translation_data.xlsx not found.")
    except Exception as e:
        print(f"❌ Error loading translation data: {e}")
        translation_df = pd.DataFrame()

load_translation_data()

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/translate", methods=["POST"])
def translate():
    data = request.get_json()
    text = data.get("text", "").strip()
    direction = data.get("direction", "").strip()

    if translation_df.empty:
        return jsonify({"translated": "Translation data not loaded."})

    # Validate direction format "X to Y"
    if " to " not in direction:
        return jsonify({"translated": "Invalid translation direction."})

    from_lang, to_lang = direction.split(" to ")

    # Check if columns exist exactly in dataframe
    if from_lang not in translation_df.columns or to_lang not in translation_df.columns:
        return jsonify({"translated": f"Language columns '{from_lang}' or '{to_lang}' not found in data."})

    col_from = from_lang
    col_to = to_lang

    # Add helper lowercase column for matching
    translation_df['_from_lower'] = translation_df[col_from].astype(str).str.lower()

    # Lowercase input text for matching
    text_lower = text.lower()

    # Try exact phrase match first
    match = translation_df[translation_df['_from_lower'] == text_lower]
    if not match.empty:
        translated = match.iloc[0][col_to]
        translation_df.drop(columns=['_from_lower'], inplace=True)
        return jsonify({"translated": translated})

    # If no exact phrase match, do word-by-word translation
    translated_words = []
    for word in text_lower.split():
        row = translation_df[translation_df['_from_lower'] == word]
        if not row.empty:
            translated_words.append(str(row.iloc[0][col_to]))
        else:
            translated_words.append(f"[{word}]")

    translation_df.drop(columns=['_from_lower'], inplace=True)
    return jsonify({"translated": " ".join(translated_words)})

if __name__ == "__main__":
    app.run(debug=True)
