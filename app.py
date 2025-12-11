import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageChops
import os
import textwrap
import io
import zipfile

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Posts", page_icon="🎨")

st.title("🎨 Generador de Agenda Cultural")
st.markdown("""
Sube tu archivo **CSV**.
El sistema generará las imágenes **numeradas secuencialmente** (1-POST..., 2-POST...) para facilitar el orden de publicación.
""")

# --- CONFIGURACIÓN DISEÑO ---
ANCHO = 1080
ALTO = 1350
COLOR_FONDO = (242, 101, 50)
COLOR_AZUL = (14, 46, 120)
COLOR_BLANCO = (255, 255, 255)

MARGEN_IZQ = 230
MARGEN_DER = 50
MARGEN_IZQ_TRAMA = 227 

# Restricción Superior
MIN_Y_FECHA = 116 

MODO_BLENDING = 'lighten'  
OPACIDAD_TRAMA = 1.0  

# --- MÓDULO DE LÍNEA BASE (Ritmo Vertical) ---
LINEA_BASE = 5 
def to_base(val):
    return round(val / LINEA_BASE) * LINEA_BASE

# Saltos internos
SALTO_CATEGORIA = to_base(45)   
SALTO_INFO = to_base(45)        
MARGIN_POST_TITULO = to_base(15)
SALTO_TITULO_LINEA = to_base(70) 
SALTO_INFO_CUANDO = to_base(35) 

# MODO COMFORT 
CFG_COMFORT = {
    "ESPACIO_ENTRE_EVENTOS": to_base(90),
    "DISTANCIA_LINEA_EVENTOS": to_base(60),
    "DISTANCIA_FECHA_LINEA": to_base(80),
    "MARGEN_INFERIOR_CANVAS": to_base(100)
}

# MODO COMPACTO 
CFG_COMPACT = {
    "ESPACIO_ENTRE_EVENTOS": to_base(65),
    "DISTANCIA_LINEA_EVENTOS": to_base(50),
    "DISTANCIA_FECHA_LINEA": to_base(70),
    "MARGEN_INFERIOR_CANVAS": to_base(85)
}

# --- FUNCIONES ---

def obtener_fuente(ruta_preferida, tamaño):
    try:
        return ImageFont.truetype(ruta_preferida, tamaño)
    except IOError:
        return ImageFont.load_default()

def cargar_fuentes():
    return {
        "titulo":      obtener_fuente("assets/Archivo-Bold.ttf", 65),
        "fecha_header":obtener_fuente("assets/ArchivoBlack-Regular.ttf", 60),
        "categoria":   obtener_fuente("assets/Archivo-Bold.ttf", 30),
        "info":        obtener_fuente("assets/Archivo-Regular.ttf", 35),
        "info_bold":   obtener_fuente("assets/Archivo-Bold.ttf", 35),
        "sidebar":     obtener_fuente("assets/Coolvetica Rg.otf", 50) 
    }

def calcular_altura_evento(fila, cfg):
    altura_acumulada = 0
    altura_acumulada += SALTO_CATEGORIA
    
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18)
    
    altura_acumulada += (len(lineas_titulo) * SALTO_TITULO_LINEA) + MARGIN_POST_TITULO
    
    altura_acumulada += SALTO_INFO 
    altura_acumulada += SALTO_INFO_CUANDO 
    return altura_acumulada

def paginar_eventos(grupo_eventos):
    cfg = CFG_COMPACT 
    
    altura_header = MIN_Y_FECHA + cfg["DISTANCIA_FECHA_LINEA"] + cfg["DISTANCIA_LINEA_EVENTOS"]
    altura_footer = ALTO - cfg["MARGEN_INFERIOR_CANVAS"]
    max_altura_disponible = altura_footer - altura_header
    
    paginas = []
    pagina_actual = []
    altura_actual = 0
    
    for index, fila in grupo_eventos.iterrows():
        h_evento = calcular_altura_evento(fila, cfg)
        
        espacio_necesario = h_evento
        if len(pagina_actual) > 0:
            espacio_necesario += cfg["ESPACIO_ENTRE_EVENTOS"]
            
        if (altura_actual + espacio_necesario) <= max_altura_disponible:
            pagina_actual.append(fila)
            altura_actual += espacio_necesario
        else:
            if pagina_actual: 
                paginas.append(pd.DataFrame(pagina_actual))
            
            pagina_actual = [fila]
            altura_actual = h_evento
            
    if pagina_actual:
        paginas.append(pd.DataFrame(pagina_actual))
        
    return paginas

def dibujar_evento(draw, y_pos, fila, fuentes, cfg):
    y_pos = to_base(y_pos) 
    
    # 1. CATEGORÍA
    cat_texto = f"—{str(fila['Categoria']).upper()}"
    draw.text((MARGEN_IZQ, y_pos), cat_texto, font=fuentes["categoria"], fill=COLOR_BLANCO)
    y_pos += SALTO_CATEGORIA

    # 2. TÍTULO
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18) 
    for linea in lineas_titulo:
        draw.text((MARGEN_IZQ, y_pos), linea, font=fuentes["titulo"], fill=COLOR_AZUL)
        y_pos += SALTO_TITULO_LINEA 
    y_pos += MARGIN_POST_TITULO

    # 3. LUGAR
    lugar_texto = f"Lugar: {fila['Lugar']}"
    if len(lugar_texto) > 40: lugar_texto = lugar_texto[:37] + "..."
    draw.text((MARGEN_IZQ, y_pos), lugar_texto, font=fuentes["info"], fill=COLOR_AZUL)
    y_pos += SALTO_INFO

    # 4. CUÁNDO
    cuando_texto = f"Cuándo: {fila['Fecha_Abreviada']} — {fila['Hora']}"
    draw.text((MARGEN_IZQ, y_pos), cuando_texto, font=fuentes["info_bold"], fill=COLOR_AZUL)
    
    return y_pos

def aplicar_blending(fondo, capa_superior, modo):
    fondo_rgb = fondo.convert("RGB")
    capa_rgb = capa_superior.convert("RGB")
    if modo == 'lighten': return ImageChops.lighter(fondo_rgb, capa_rgb)
    elif modo == 'multiply': return ImageChops.multiply(fondo_rgb, capa_rgb)
    elif modo == 'screen': return ImageChops.screen(fondo_rgb, capa_rgb)
    elif modo == 'overlay': return ImageChops.soft_light(fondo_rgb, capa_rgb)
    return capa_rgb

def generar_imagen_en_memoria(fecha_key, datos_grupo, fuentes):
    img = Image.new('RGB', (ANCHO, ALTO), color=COLOR_FONDO)
    draw = ImageDraw.Draw(img)

    if isinstance(datos_grupo, pd.DataFrame):
        items_para_calcular = [fila for idx, fila in list(datos_grupo.iterrows())]
    else:
        items_para_calcular = datos_grupo

    cantidad_eventos = len(items_para_calcular)

    # --- SELECCIÓN DINÁMICA DE CONFIGURACIÓN ---
    if cantidad_eventos >= 4:
        cfg = CFG_COMPACT
        mostrar_trama = False
    else:
        cfg = CFG_COMFORT
        mostrar_trama = True

    # 1. CÁLCULO BOTTOM-UP
    altura_total_contenido = 0
    for fila in items_para_calcular:
        altura_total_contenido += calcular_altura_evento(fila, cfg)
    
    if cantidad_eventos > 1:
        altura_total_contenido += (cantidad_eventos - 1) * cfg["ESPACIO_ENTRE_EVENTOS"]

    y_inicio_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"] - altura_total_contenido
    y_linea = y_inicio_eventos - cfg["DISTANCIA_LINEA_EVENTOS"]
    y_fecha = y_linea - cfg["DISTANCIA_FECHA_LINEA"]
    
    # RESTRICCIÓN DE SEGURIDAD
    y_fecha = to_base(y_fecha)
    y_linea = to_base(y_linea)
    y_inicio_eventos = to_base(y_inicio_eventos)

    if y_fecha < MIN_Y_FECHA: 
        diferencia = MIN_Y_FECHA - y_fecha
        y_fecha = MIN_Y_FECHA
        y_linea = to_base(y_linea + diferencia)
        y_inicio_eventos = to_base(y_inicio_eventos + diferencia)

    # 2. TRAMA
    limite_trama = int(y_fecha - 10) 

    if mostrar_trama and os.path.exists("assets/trama.png") and limite_trama > 0:
        try:
            tira = Image.open("assets/trama.png").convert("RGBA")
            if OPACIDAD_TRAMA < 1.0:
                alpha = tira.split()[3].point(lambda i: i * OPACIDAD_TRAMA)
                tira.putalpha(alpha)

            ancho_util_trama = ANCHO - MARGEN_IZQ_TRAMA
            ratio = ancho_util_trama / tira.width
            alto_tira = int(tira.height * ratio)
            tira = tira.resize((ancho_util_trama, alto_tira), Image.Resampling.LANCZOS)
            
            capa_trama = Image.new('RGBA', (ANCHO, limite_trama), (0,0,0,0))
            y_pegado = limite_trama - alto_tira
            while y_pegado > -alto_tira:
                capa_trama.paste(tira, (MARGEN_IZQ_TRAMA, y_pegado), tira)
                y_pegado -= alto_tira

            if MODO_BLENDING:
                fondo_zona = img.crop((0, 0, ANCHO, limite_trama))
                zona_mezclada = aplicar_blending(fondo_zona, capa_trama, MODO_BLENDING)
                img.paste(zona_mezclada, (0, 0))
            else:
                img.paste(capa_trama, (0, 0), capa_trama)
        except Exception:
            pass

    # 3. Elementos Fijos
    txt_sidebar = "conectando—cultura"
    capa_txt = Image.new('RGBA', (800, 100), (255, 255, 255, 0))
    d_txt = ImageDraw.Draw(capa_txt)
    d_txt.text((0, 0), txt_sidebar, font=fuentes["sidebar"], fill=COLOR_AZUL)
    rotado = capa_txt.rotate(90, expand=1)
    img.paste(rotado, (82, ALTO - 900), rotado)

    if os.path.exists("assets/logo.png"):
        try:
            logo = Image.open("assets/logo.png").convert("RGBA")
            logo.thumbnail((150, 150))
            img.paste(logo, (37, 50), logo)
        except: pass

    header_texto = str(fecha_key).replace(" ", "#").upper()
    bbox = draw.textbbox((0, 0), header_texto, font=fuentes["fecha_header"])
    ancho_txt = bbox[2] - bbox[0]
    draw.text((ANCHO - MARGEN_DER - ancho_txt, y_fecha), header_texto, font=fuentes["fecha_header"], fill=COLOR_AZUL)

    draw.line([(MARGEN_IZQ, y_linea), (ANCHO - MARGEN_DER, y_linea)], fill=COLOR_AZUL, width=5)

    # 4. Eventos
    y_cursor = y_inicio_eventos
    for fila in items_para_calcular:
        y_fin = dibujar_evento(draw, y_cursor, fila, fuentes, cfg)
        y_cursor = y_fin + cfg["ESPACIO_ENTRE_EVENTOS"] 
    
    return img

# --- LÓGICA DE LA INTERFAZ ---

uploaded_file = st.file_uploader("Arrastra tu CSV aquí", type=["csv"])

if uploaded_file is not None:
    try:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin-1', dtype=str)
        
        df.fillna("", inplace=True)
        df.columns = df.columns.str.strip()

        if 'Fecha_Abreviada' not in df.columns:
            st.error("❌ El CSV no tiene la columna 'Fecha_Abreviada'. Revisa el formato.")
        else:
            st.success(f"✅ Archivo cargado. {len(df)} eventos detectados.")
            
            if st.button("🚀 Generar Imágenes"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                fuentes = cargar_fuentes()
                
                # Agrupamos por fecha manteniendo el orden del CSV
                grupos = df.groupby('Fecha_Abreviada', sort=False)
                total_grupos = len(grupos)
                
                zip_buffer = io.BytesIO()
                
                # --- CONTADOR GLOBAL SECUENCIAL ---
                # Este contador NO se reinicia. Empieza en 1 y sigue subiendo.
                contador_secuencial = 1
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, (fecha, grupo) in enumerate(grupos):
                        status_text.text(f"Analizando: {fecha}...")
                        
                        # PAGINACIÓN
                        paginas = paginar_eventos(grupo)
                        
                        for idx_pag, pagina_data in enumerate(paginas):
                            img = generar_imagen_en_memoria(fecha, pagina_data, fuentes)
                            
                            # Limpieza de nombre: quitamos espacios para que quede tipo "MIE10"
                            nombre_fecha_limpio = str(fecha).replace(" ", "").replace("/", "").upper()
                            
                            # Nombre final: 1-POST-MIE10.png, 2-POST-JUE11.png, etc.
                            nombre_archivo = f"{contador_secuencial}-POST-{nombre_fecha_limpio}.png"
                            
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            zf.writestr(nombre_archivo, img_bytes.getvalue())
                            
                            # Incrementamos el contador por cada imagen generada
                            contador_secuencial += 1
                        
                        progress_bar.progress((i + 1) / total_grupos)
                
                status_text.text("¡Listo! Imágenes generadas.")
                progress_bar.empty()
                
                st.download_button(
                    label="📥 Descargar Imágenes (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="posts_instagram_ordenados.zip",
                    mime="application/zip"
                )

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
