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
El sistema usará un diseño **aireado** para pocos eventos y uno **compacto** (pero legible) si detecta 4 eventos.
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

# Restricción Superior (Pixel mínimo donde puede empezar la fecha)
MIN_Y_FECHA = 116 

MODO_BLENDING = 'lighten'  
OPACIDAD_TRAMA = 1.0  

# --- DEFINICIÓN DE DOS MODOS DE ESPACIADO ---

# MODO COMFORT (Para 1, 2 o 3 eventos) - Valores originales
CFG_COMFORT = {
    "ESPACIO_ENTRE_EVENTOS": 90,
    "DISTANCIA_LINEA_EVENTOS": 60,
    "DISTANCIA_FECHA_LINEA": 80,
    "MARGEN_INFERIOR_CANVAS": 100
}

# MODO COMPACTO (Para 4 eventos) - Valores intermedios
# Ajustados para que no estén pegados, ya que me dijiste que sobraba espacio arriba.
CFG_COMPACT = {
    "ESPACIO_ENTRE_EVENTOS": 60,     # Antes puse 45 (muy pegado), ahora 65
    "DISTANCIA_LINEA_EVENTOS": 50,   # Antes 40, ahora 50
    "DISTANCIA_FECHA_LINEA": 70,     # Antes 60, ahora 70
    "MARGEN_INFERIOR_CANVAS": 75     # Antes 70, ahora 85
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

def calcular_altura_evento(fila):
    altura_acumulada = 0
    altura_acumulada += 45 # Categoría
    
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18)
    altura_acumulada += (len(lineas_titulo) * 70) + 15 
    
    altura_acumulada += 45 # Lugar
    altura_acumulada += 35 # Cuándo
    return altura_acumulada

def paginar_eventos(grupo_eventos):
    """
    Divide los eventos. 
    IMPORTANTE: Para calcular si entran, usamos las métricas COMPACTAS.
    Esto permite que el paginador sea permisivo y acepte agrupar 4 eventos.
    Si luego son menos, el renderizador usará las métricas COMFORT.
    """
    
    # Usamos configuración compacta para el cálculo de capacidad máxima
    cfg = CFG_COMPACT 
    
    tope_superior_eventos = MIN_Y_FECHA + cfg["DISTANCIA_FECHA_LINEA"] + cfg["DISTANCIA_LINEA_EVENTOS"]
    tope_inferior_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"]
    
    max_altura_disponible = tope_inferior_eventos - tope_superior_eventos
    
    paginas = []
    pagina_actual = []
    altura_actual = 0
    
    for index, fila in grupo_eventos.iterrows():
        h_evento = calcular_altura_evento(fila)
        
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

def dibujar_evento(draw, y_pos, fila, fuentes):
    cat_texto = f"—{str(fila['Categoria']).upper()}"
    draw.text((MARGEN_IZQ, y_pos), cat_texto, font=fuentes["categoria"], fill=COLOR_BLANCO)
    y_pos += 45

    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18) 
    for linea in lineas_titulo:
        draw.text((MARGEN_IZQ, y_pos), linea, font=fuentes["titulo"], fill=COLOR_AZUL)
        y_pos += 70
    y_pos += 15 

    lugar_texto = f"Lugar: {fila['Lugar']}"
    if len(lugar_texto) > 40: lugar_texto = lugar_texto[:37] + "..."
    draw.text((MARGEN_IZQ, y_pos), lugar_texto, font=fuentes["info"], fill=COLOR_AZUL)
    y_pos += 45

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

    # Convertir datos a lista para contar
    if isinstance(datos_grupo, pd.DataFrame):
        lista_filas = list(datos_grupo.iterrows())
        items_para_calcular = [fila for idx, fila in lista_filas]
    else:
        items_para_calcular = datos_grupo

    cantidad_eventos = len(items_para_calcular)

    # --- SELECCIÓN DINÁMICA DE CONFIGURACIÓN ---
    if cantidad_eventos >= 4:
        cfg = CFG_COMPACT
        mostrar_trama = False # Si hay 4 o más, ocultamos trama para limpiar
    else:
        cfg = CFG_COMFORT
        mostrar_trama = True

    # 1. CÁLCULO BOTTOM-UP
    altura_total_contenido = 0
    for fila in items_para_calcular:
        altura_total_contenido += calcular_altura_evento(fila)
    
    if cantidad_eventos > 1:
        altura_total_contenido += (cantidad_eventos - 1) * cfg["ESPACIO_ENTRE_EVENTOS"]

    y_inicio_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"] - altura_total_contenido
    y_linea = y_inicio_eventos - cfg["DISTANCIA_LINEA_EVENTOS"]
    y_fecha = y_linea - cfg["DISTANCIA_FECHA_LINEA"]
    
    # RESTRICCIÓN DE SEGURIDAD
    if y_fecha < MIN_Y_FECHA:
        diferencia = MIN_Y_FECHA - y_fecha
        y_fecha = MIN_Y_FECHA
        y_linea += diferencia
        y_inicio_eventos += diferencia

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
        y_fin = dibujar_evento(draw, y_cursor, fila, fuentes)
        y_cursor = y_fin + cfg["ESPACIO_ENTRE_EVENTOS"] # Usamos el espacio de la config elegida
    
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
                
                grupos = df.groupby('Fecha_Abreviada', sort=False)
                total_grupos = len(grupos)
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, (fecha, grupo) in enumerate(grupos):
                        status_text.text(f"Analizando: {fecha}...")
                        
                        # PAGINACIÓN
                        paginas = paginar_eventos(grupo)
                        
                        for idx_pag, pagina_data in enumerate(paginas):
                            img = generar_imagen_en_memoria(fecha, pagina_data, fuentes)
                            
                            nombre_base = str(fecha).replace(" ", "_").replace("/", "-")
                            
                            if len(paginas) > 1:
                                nombre_archivo = f"post_{nombre_base}_{idx_pag + 1}.png"
                            else:
                                nombre_archivo = f"post_{nombre_base}.png"
                            
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            zf.writestr(nombre_archivo, img_bytes.getvalue())
                        
                        progress_bar.progress((i + 1) / total_grupos)
                
                status_text.text("¡Listo! Imágenes generadas.")
                progress_bar.empty()
                
                st.download_button(
                    label="📥 Descargar Imágenes (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="posts_instagram.zip",
                    mime="application/zip"
                )

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")

