import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageChops
import os
import textwrap
import io
import zipfile
import requests
from bs4 import BeautifulSoup
import re
from io import StringIO

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Posts", page_icon="🎨")
st.title("C‒C Generador de Agenda Cultural")
st.markdown("Generación automática de imágenes secuenciales desde la web o CSV.")

# ==============================================================================
# 2. VARIABLES CRÍTICAS (NO BORRAR NI MOVER)
# ==============================================================================
AGENDA_URL = "https://portaluniversidad.org.ar/agenda-cultural/"
CONTENEDOR_CLASE = "entry themeform"

# --- CONFIGURACIÓN GLOBAL BASE ---
ANCHO = 1080
ALTO = 1350
COLOR_FONDO = (242, 101, 50)
COLOR_AZUL = (14, 46, 120)
COLOR_BLANCO = (255, 255, 255)

# ==============================================================================
# 3. CONFIGURACIÓN DEL DISEÑO (PEGAR AQUÍ DATOS DEL CALIBRADOR)
# ==============================================================================

# 1. CONFIGURACIÓN TRAMA
MODO_BLENDING = 'lighten'
OPACIDAD_TRAMA = 1.0
MARGEN_IZQ_TRAMA = 227
OFFSET_TRAMA_Y = 10 # Valor default si no se encuentra en cfg (fallback)

# 2. GEOMETRÍA GLOBAL
MARGEN_IZQ = 230
MARGEN_DER = 50
MIN_Y_FECHA = 110
POSICION_Y_SIDEBAR = 900

# 3. FUENTES (TAMAÑOS)
SIZE_TITULO = 65
SIZE_FECHA = 60
SIZE_CAT = 30
SIZE_INFO = 35
SIZE_SIDEBAR = 50

# 4. INTERLINEADO INTERNO
SALTO_CATEGORIA = 45
SALTO_TITULO_LINEA = 70
MARGIN_POST_TITULO = 15
SALTO_INFO = 45
SALTO_INFO_CUANDO = 35

# 5. TEMPLATES
CFG_COMFORT = {
    "ESPACIO_ENTRE_EVENTOS": 90,
    "DISTANCIA_LINEA_EVENTOS": 60,
    "DISTANCIA_FECHA_LINEA": 80,
    "MARGEN_INFERIOR_CANVAS": 100,
    "OFFSET_TRAMA": 10
}

CFG_COMPACT = {
    "ESPACIO_ENTRE_EVENTOS": 65,
    "DISTANCIA_LINEA_EVENTOS": 50,
    "DISTANCIA_FECHA_LINEA": 70,
    "MARGEN_INFERIOR_CANVAS": 85,
    "OFFSET_TRAMA": 0
}
# ==============================================================================

# --- 4. UTILS RITMO VERTICAL ---
LINEA_BASE = 5 
def to_base(val):
    return round(val / LINEA_BASE) * LINEA_BASE

# --- 5. FUNCIONES DE FUENTES ---
def obtener_fuente(ruta_preferida, tamaño):
    try: return ImageFont.truetype(ruta_preferida, int(tamaño))
    except IOError: return ImageFont.load_default()

@st.cache_resource
def cargar_fuentes():
    return {
        "titulo":      obtener_fuente("assets/Archivo-Bold.ttf", SIZE_TITULO),
        "fecha_header":obtener_fuente("assets/ArchivoBlack-Regular.ttf", SIZE_FECHA),
        "categoria":   obtener_fuente("assets/Archivo-Bold.ttf", SIZE_CAT),
        "info":        obtener_fuente("assets/Archivo-Regular.ttf", SIZE_INFO),
        "info_bold":   obtener_fuente("assets/Archivo-Bold.ttf", SIZE_INFO),
        "sidebar":     obtener_fuente("assets/Coolvetica Rg.otf", SIZE_SIDEBAR) 
    }

# --- 6. LÓGICA DE DIBUJO ---

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
            if pagina_actual: paginas.append(pd.DataFrame(pagina_actual))
            pagina_actual = [fila]
            altura_actual = h_evento
            
    if pagina_actual: paginas.append(pd.DataFrame(pagina_actual))
    return paginas

def dibujar_evento(draw, y_pos, fila, fuentes, cfg):
    y_pos = to_base(y_pos) 
    cat_texto = f"—{str(fila['Categoria']).upper()}"
    draw.text((MARGEN_IZQ, y_pos), cat_texto, font=fuentes["categoria"], fill=COLOR_BLANCO)
    y_pos += SALTO_CATEGORIA

    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18) 
    for linea in lineas_titulo:
        draw.text((MARGEN_IZQ, y_pos), linea, font=fuentes["titulo"], fill=COLOR_AZUL)
        y_pos += SALTO_TITULO_LINEA 
    y_pos += MARGIN_POST_TITULO

    lugar_texto = f"Lugar: {fila['Lugar']}"
    if len(lugar_texto) > 40: lugar_texto = lugar_texto[:37] + "..."
    draw.text((MARGEN_IZQ, y_pos), lugar_texto, font=fuentes["info"], fill=COLOR_AZUL)
    y_pos += SALTO_INFO

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

    # Selección de Template
    if cantidad_eventos >= 4:
        cfg = CFG_COMPACT
    else:
        cfg = CFG_COMFORT

    # 1. CÁLCULO BOTTOM-UP
    altura_total_contenido = 0
    for fila in items_para_calcular:
        altura_total_contenido += calcular_altura_evento(fila, cfg)
    
    if cantidad_eventos > 1:
        altura_total_contenido += (cantidad_eventos - 1) * cfg["ESPACIO_ENTRE_EVENTOS"]

    y_inicio_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"] - altura_total_contenido
    y_linea = y_inicio_eventos - cfg["DISTANCIA_LINEA_EVENTOS"]
    y_fecha = y_linea - cfg["DISTANCIA_FECHA_LINEA"]
    
    y_fecha = to_base(y_fecha)
    y_linea = to_base(y_linea)
    y_inicio_eventos = to_base(y_inicio_eventos)

    if y_fecha < MIN_Y_FECHA:
        diferencia = MIN_Y_FECHA - y_fecha
        y_fecha = MIN_Y_FECHA
        y_linea = to_base(y_linea + diferencia)
        y_inicio_eventos = to_base(y_inicio_eventos + diferencia)

    # 2. TRAMA
    offset = cfg.get("OFFSET_TRAMA", 10) # Usa el offset del config, o 10 por defecto
    limite_trama = int(y_fecha - offset) 
    
    if os.path.exists("assets/trama.png") and limite_trama > 0:
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

            if MODO_BLENDING and MODO_BLENDING != 'normal':
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
    img.paste(rotado, (82, ALTO - POSICION_Y_SIDEBAR), rotado)

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

# --- 7. FUNCIONES DE SCRAPING ---
@st.cache_data
def obtener_texto_agenda(url, clase_contenedor):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        contenedor = soup.find('div', class_=clase_contenedor)
        if contenedor:
            eventos_en_bruto = []
            dias_semana_base = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
            dia_actual = None
            for tag in contenedor.find_all(['h2', 'h3', 'h4', 'p', 'ul', 'li']):
                texto_limpio = tag.get_text(strip=True).upper()
                for dia_base in dias_semana_base:
                    if texto_limpio.startswith(dia_base):
                        dia_actual = dia_base 
                        break
                if tag.name == 'li' and dia_actual:
                    for fmt_tag in tag.find_all(['strong', 'em', 'a', 'br']):
                         if fmt_tag.name == 'br': fmt_tag.replace_with(' _SEP_ ') 
                         else: fmt_tag.unwrap()
                    lineas_evento = tag.get_text(separator=' ', strip=True).split(' _SEP_ ')
                    lineas_evento = [l.strip() for l in lineas_evento if l.strip()]
                    if len(lineas_evento) >= 3:
                        eventos_en_bruto.append({'Dia': dia_actual, 'Bloque': lineas_evento})
            return eventos_en_bruto
        else: return f"ERROR: Clase '{clase_contenedor}' no encontrada."
    except Exception as e: return f"ERROR: {e}"

def texto_a_dataframe(datos_pre_procesados):
    eventos_procesados = []
    if isinstance(datos_pre_procesados, str) or not datos_pre_procesados: return pd.DataFrame()
    for item in datos_pre_procesados:
        bloque = item['Bloque']
        try:
            partes_evento = bloque[0].split('|', 1)
            categoria = partes_evento[0].strip()
            nombre_evento = partes_evento[1].strip() if len(partes_evento) > 1 else "Sin Título"
            lugar = re.sub(r'\s*\([^)]*\)', '', bloque[1].strip()).strip() 
            partes_fecha_hora = re.split(r'\s*–\s*|\s*-\s*', bloque[2], 1)
            fecha_abreviada = partes_fecha_hora[0].strip()
            hora = partes_fecha_hora[1].strip() if len(partes_fecha_hora) > 1 else "N/A"
            eventos_procesados.append({
                'Dia': item['Dia'].capitalize(), 'Categoria': categoria, 'Evento': nombre_evento,
                'Lugar': lugar, 'Fecha_Abreviada': fecha_abreviada, 'Hora': hora
            })
        except: continue
    return pd.DataFrame(eventos_procesados)

# --- 8. FUNCIÓN CENTRALIZADA DE GENERACIÓN (ZIP) ---
def procesar_generacion_zip(df_entrada):
    fuentes = cargar_fuentes()
    grupos = df_entrada.groupby('Fecha_Abreviada', sort=False)
    total_grupos = len(grupos)
    zip_buffer = io.BytesIO()
    contador_secuencial = 1
    progress_bar = st.progress(0)
    status_text = st.empty()

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for i, (fecha, grupo) in enumerate(grupos):
            status_text.text(f"Procesando: {fecha}...")
            paginas = paginar_eventos(grupo)
            for idx_pag, pagina_data in enumerate(paginas):
                img = generar_imagen_en_memoria(fecha, pagina_data, fuentes)
                nombre_fecha_limpio = str(fecha).replace(" ", "").replace("/", "").upper()
                nombre_archivo = f"{contador_secuencial}-POST-{nombre_fecha_limpio}.png"
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG') 
                zf.writestr(nombre_archivo, img_bytes.getvalue())
                contador_secuencial += 1
            progress_bar.progress((i + 1) / total_grupos)
            
    status_text.success("¡Imágenes generadas exitosamente!")
    progress_bar.empty()
    return zip_buffer

# --- 9. INTERFAZ PRINCIPAL (TABS) ---
tab1, tab2 = st.tabs(["🌐 Desde Web (Scraping)", "📂 Subir CSV (Manual)"])

with tab1:
    st.info(f"Fuente de datos: **{AGENDA_URL}**")
    if st.button("🔄 Escanear Web y Generar", key="btn_web"):
        with st.spinner("Conectando a la web..."):
            datos = obtener_texto_agenda(AGENDA_URL, CONTENEDOR_CLASE)
            if isinstance(datos, str) and datos.startswith("ERROR"): st.error(datos)
            else:
                df_web = texto_a_dataframe(datos)
                if df_web.empty: st.warning("⚠️ No se encontraron eventos.")
                else:
                    st.success(f"✅ {len(df_web)} eventos encontrados.")
                    st.dataframe(df_web[['Dia', 'Categoria', 'Evento', 'Fecha_Abreviada']], height=150)
                    zip_file = procesar_generacion_zip(df_web)
                    st.download_button("📥 Descargar ZIP (Web)", zip_file.getvalue(), "posts_agenda_web.zip", "application/zip")

with tab2:
    st.markdown("Sube un CSV con las columnas: `Fecha_Abreviada`, `Evento`, `Categoria`, `Lugar`, `Hora`")
    uploaded_file = st.file_uploader("Sube tu archivo .csv", type=["csv"])
    if uploaded_file is not None:
        try:
            try: df_csv = pd.read_csv(uploaded_file, encoding='utf-8', dtype=str)
            except UnicodeDecodeError: df_csv = pd.read_csv(uploaded_file, encoding='latin-1', dtype=str)
            df_csv.fillna("", inplace=True)
            df_csv.columns = df_csv.columns.str.strip()
            req_cols = ['Fecha_Abreviada', 'Evento', 'Categoria', 'Lugar', 'Hora']
            missing = [c for c in req_cols if c not in df_csv.columns]
            if missing: st.error(f"❌ Faltan columnas: {', '.join(missing)}")
            else:
                st.success(f"✅ Archivo cargado: {len(df_csv)} eventos.")
                st.dataframe(df_csv[['Categoria', 'Evento', 'Fecha_Abreviada']], height=150)
                if st.button("🚀 Generar desde CSV", key="btn_csv"):
                    zip_file = procesar_generacion_zip(df_csv)
                    st.download_button("📥 Descargar ZIP (CSV)", zip_file.getvalue(), "posts_agenda_csv.zip", "application/zip")
        except Exception as e: st.error(f"Error al leer el archivo: {e}")
