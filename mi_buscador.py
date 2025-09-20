import streamlit as st
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np
import tempfile
import os
from PIL import Image

# Configurar la página
st.set_page_config(page_title="Buscador de PDFs", page_icon="🔍", layout="wide")

# Título principal
st.title("🔍 BUSCADOR DE PDFS ESCANEADOS")
st.write("**Sube tus documentos escaneados y encuentra texto fácilmente**")

# Sidebar con instrucciones
with st.sidebar:
    st.header("📋 INSTRUCCIONES")
    st.info("""
    1. **SUBIR** PDF escaneado
    2. **ESCRIBIR** texto a buscar  
    3. **CLIC** en Buscar
    4. **VER** resultados
    """)
    
    st.header("⚙️ CONFIGURACIÓN")
    calidad = st.slider("Calidad de procesamiento", 150, 300, 200)
    busqueda_exacta = st.checkbox("Búsqueda exacta", value=True)

# Área para subir archivo
archivo = st.file_uploader("**📤 SUBE TU PDF ESCANEADO**", type="pdf")

# Texto a buscar  
texto_buscar = st.text_input("**🔍 ¿QUÉ QUIERES BUSCAR?**", placeholder="Ej: 1014217372, nombre, fecha...")

# Función para procesar PDF
def procesar_pdf(archivo_pdf, calidad=200):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(archivo_pdf.read())
        tmp_path = tmp.name
    
    try:
        imagenes = convert_from_path(tmp_path, dpi=calidad)
        return imagenes, tmp_path
    except Exception as e:
        st.error(f"Error al procesar PDF: {str(e)}")
        return None, tmp_path
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

# Función para extraer texto
def extraer_texto(imagen):
    try:
        img_array = np.array(imagen)
        if len(img_array.shape) == 3:
            gris = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gris = img_array
        
        # Mejorar la imagen para OCR
        _, thresh = cv2.threshold(gris, 150, 255, cv2.THRESH_BINARY_INV)
        thresh = 255 - thresh
        
        # Extraer texto
        texto = pytesseract.image_to_string(thresh, config='--psm 6')
        return texto
    except Exception as e:
        return f"Error en OCR: {str(e)}"

# Botón de búsqueda
if st.button("🚀 **INICIAR BÚSQUEDA**", type="primary", use_container_width=True):
    if archivo is None:
        st.warning("⚠️ **PRIMERO SUBE UN ARCHIVO PDF**")
    elif not texto_buscar:
        st.warning("⚠️ **ESCRIBE LO QUE QUIERES BUSCAR**")
    else:
        with st.spinner("🔍 **PROCESANDO DOCUMENTO...**"):
            try:
                # Procesar PDF
                imagenes, _ = procesar_pdf(archivo, calidad)
                
                if imagenes:
                    resultados = []
                    total_paginas = len(imagenes)
                    
                    # Barra de progreso
                    progreso = st.progress(0)
                    estado = st.empty()
                    
                    # Buscar en cada página
                    for i, imagen in enumerate(imagenes):
                        estado.text(f"📄 Analizando página {i+1}/{total_paginas}")
                        progreso.progress((i + 1) / total_paginas)
                        
                        texto_pagina = extraer_texto(imagen)
                        
                        # Buscar texto
                        if busqueda_exacta:
                            if texto_buscar.lower() in texto_pagina.lower():
                                resultados.append(i + 1)
                        else:
                            if texto_buscar in texto_pagina:
                                resultados.append(i + 1)
                    
                    # Mostrar resultados
                    progreso.empty()
                    estado.empty()
                    
                    if resultados:
                        st.success(f"🎉 **TEXTO ENCONTRADO EN {len(resultados)} PÁGINA(S)**")
                        st.info(f"**📑 PÁGINAS:** {', '.join(map(str, resultados))}")
                    else:
                        st.error("❌ **TEXTO NO ENCONTRADO**")
                        st.info("💡 Intenta con búsqueda no exacta o verifica el texto")
                
            except Exception as e:
                st.error(f"❌ **ERROR:** {str(e)}")
                st.info("⚠️ Verifica que Tesseract y poppler estén instalados")

# Pie de página
st.markdown("---")
st.caption("🛠️ **Herramienta con reconocimiento de texto OCR**")
