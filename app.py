import streamlit as st
from PIL import Image, ImageEnhance
from rembg import remove
import os
import tempfile
from zipfile import ZipFile
import time

# === Configuration Streamlit ===
st.set_page_config(page_title="Logo Overlay App", layout="centered")

# === CSS personnalisé ===
st.markdown("""
<style>
    @media only screen and (max-width: 600px) {
        .stSlider input { width: 100%; }
        .stButton button { width: 100%; font-size: 16px; padding: 10px; }
        .title h1 { font-size: 24px; }
        .footer { font-size: 12px; }
    }

    body {
        background-color: #f5f7fa;
        font-family: 'Segoe UI', sans-serif;
    }

    .title {
        text-align: center;
        color: #003366;
        margin-bottom: 20px;
    }

    .footer {
        margin-top: 40px;
        text-align: center;
        font-size: 0.9em;
        color: gray;
    }

    .container {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    .preview-box {
        margin-top: 20px;
        display: flex;
        justify-content: center;
    }

    .slider-label {
        font-weight: bold;
        margin-top: 10px;
    }

    .file-uploader {
        border: 2px dashed #007BFF;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .file-uploader:hover {
        border-color: #FFC107;
        background-color: #f8f9fa;
    }

    .image-preview {
        margin-top: 10px;
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .image-preview img {
        max-width: 100px;
        max-height: 100px;
        border-radius: 5px;
        cursor: pointer;
        transition: transform 0.3s ease;
    }

    .image-preview img:hover {
        transform: scale(1.1);
    }
</style>
""", unsafe_allow_html=True)

# === Titre ===
st.markdown('<div class="title"><h1>🖼️ Logo Overlay App</h1><h4>Ajoutez un logo transparent sur vos images</h4></div>', unsafe_allow_html=True)

# === Upload avec drag-and-drop stylé ===
with st.container():
    st.markdown('<div class="container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        uploaded_logo = st.file_uploader("📤 Glissez ou sélectionnez votre logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="logo")
        if uploaded_logo:
            st.markdown('<div class="file-uploader">✅ Logo chargé : <b>{}</b></div>'.format(uploaded_logo.name), unsafe_allow_html=True)

    with col2:
        uploaded_images = st.file_uploader("📥 Glissez ou sélectionnez vos images (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
        if uploaded_images:
            st.markdown('<div class="file-uploader">✅ {} image(s) chargée(s)</div>'.format(len(uploaded_images)), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# === Aperçu des images uploadées ===
if uploaded_images:
    st.markdown('<div class="image-preview">', unsafe_allow_html=True)
    for img in uploaded_images:
        st.image(Image.open(img), caption=img.name, use_column_width=False, width=100)
    st.markdown('</div>', unsafe_allow_html=True)

# === Paramètres ===
with st.container():
    st.markdown('<div class="container option-group">', unsafe_allow_html=True)
    st.markdown('<div class="slider-label">📍 Position du logo</div>', unsafe_allow_html=True)
    position = st.selectbox("", [
        "Coin supérieur gauche", "Centre", "Coin inférieur droit",
        "Coin supérieur droit", "Coin inférieur gauche"
    ])

    st.markdown('<div class="slider-label">📏 Taille du logo (%)</div>', unsafe_allow_html=True)
    size = st.slider("", 5, 100, 20)

    st.markdown('<div class="slider-label">🔄 Rotation du logo (°)</div>', unsafe_allow_html=True)
    rotation = st.slider("", 0, 360, 0)

    st.markdown('<div class="slider-label">👁️ Opacité du logo (%)</div>', unsafe_allow_html=True)
    opacity = st.slider("", 0, 100, 100)

    st.markdown('</div>', unsafe_allow_html=True)

# === Boutons ===
preview_col, run_col = st.columns([1, 1])
with preview_col:
    preview_btn = st.button("🔍 Aperçu")

with run_col:
    run_btn = st.button("✨ Traiter & Télécharger")

# === Zone d'affichage des résultats ===
output_placeholder = st.empty()

# === Fonction principale ===
@st.cache_data(show_spinner="Traitement en cours... ⏳")
def apply_settings(img_bg, img_logo, pos, size_percent, rotation_angle, opacity):
    new_size = int(img_bg.width * size_percent / 100), int(img_logo.height * size_percent / 100 * img_bg.width / img_logo.width)
    logo_resized = img_logo.resize(new_size).convert("RGBA")
    logo_resized = logo_resized.rotate(rotation_angle, expand=True)

    alpha = logo_resized.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 100)
    logo_resized.putalpha(alpha)

    if pos == "Coin supérieur gauche":
        pos = (50, 50)
    elif pos == "Coin supérieur droit":
        pos = (img_bg.width - logo_resized.width - 50, 50)
    elif pos == "Coin inférieur gauche":
        pos = (50, img_bg.height - logo_resized.height - 50)
    elif pos == "Coin inférieur droit":
        pos = (img_bg.width - logo_resized.width - 50, img_bg.height - logo_resized.height - 50)
    elif pos == "Centre":
        pos = ((img_bg.width - logo_resized.width) // 2, (img_bg.height - logo_resized.height) // 2)
    else:
        pos = (50, 50)

    img_bg.paste(logo_resized, pos, logo_resized)
    return img_bg.convert("RGB")

# === Gestion des fichiers uploadés ===
if preview_btn or run_btn:
    if not uploaded_logo or not uploaded_images:
        st.error("❌ Veuillez télécharger un logo et au moins une image.")
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            logo_path = os.path.join(temp_dir, uploaded_logo.name)
            with open(logo_path, "wb") as f:
                f.write(uploaded_logo.getvalue())

            logo = Image.open(logo_path).convert("RGBA")
            logo = remove(logo)

            if preview_btn:
                bg_img = Image.open(uploaded_images[0]).convert("RGBA")
                start_time = time.time()
                result = apply_settings(bg_img, logo, position, size, rotation, opacity)
                st.markdown('<div class="preview-box">', unsafe_allow_html=True)
                st.image(result, caption="👁️ Aperçu du logo ajouté", use_column_width=True)
                st.success(f"⏱️ Aperçu généré en {round(time.time() - start_time, 2)} secondes")
                st.markdown('</div>', unsafe_allow_html=True)

            if run_btn:
                output_zip = os.path.join(temp_dir, "logos_ajoutes.zip")
                with ZipFile(output_zip, 'w') as zipf:
                    for img_file in uploaded_images:
                        bg = Image.open(img_file).convert("RGBA")
                        bg_copy = bg.copy()
                        bg_w, bg_h = bg.size

                        new_size = int(bg_w * size / 100), int(logo.height * size / 100 * bg_w / logo.width)
                        logo_resized = logo.resize(new_size).rotate(rotation, expand=True)

                        alpha = logo_resized.split()[3]
                        alpha = ImageEnhance.Brightness(alpha).enhance(opacity / 100)
                        logo_resized.putalpha(alpha)

                        if position == "Coin supérieur gauche":
                            pos = (50, 50)
                        elif position == "Coin supérieur droit":
                            pos = (bg_w - logo_resized.width - 50, 50)
                        elif position == "Coin inférieur gauche":
                            pos = (50, bg_h - logo_resized.height - 50)
                        elif position == "Coin inférieur droit":
                            pos = (bg_w - logo_resized.width - 50, bg_h - logo_resized.height - 50)
                        elif position == "Centre":
                            pos = ((bg_w - logo_resized.width) // 2, (bg_h - logo_resized.height) // 2)

                        bg_copy.paste(logo_resized, pos, logo_resized)
                        result = bg_copy.convert("RGB")

                        out_path = os.path.join(temp_dir, f"{img_file.name}_with_logo.jpg")
                        result.save(out_path, "JPEG")
                        zipf.write(out_path, arcname=f"{img_file.name}_with_logo.jpg")

                with open(output_zip, "rb") as f:
                    st.download_button("📥 Télécharger les résultats", data=f, file_name="logos_ajoutes.zip")

# === Footer ===

st.markdown('<div class="footer">Made with ❤️ by @tombo1998 | Powered by Streamlit & rembg</div>', unsafe_allow_html=True)
