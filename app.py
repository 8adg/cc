import streamlit as st

Modifico las funciones `calcular_altura_evento`, `dibujar_evento` y las constantes de espaciado para que todo respete la rejilla de 15px.


import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageChops
import os
import textwrap
import io
import zipfile

# --- CONFIGURACIÓN DE PÁGINA ---
st```python
import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageChops
import os
import textwrap

# --- CONFIGURACIÓN ---
ANCHO = 1080
ALTO = 13.set_page_config(page_title="Generador de Posts", page_icon="🎨")

st.title("🎨 Generador de Agenda Cultural")
st.markdown("""
Sube tu archivo **CSV**. 50
COLOR_FONDO = (242, 101, 50)
COLOR_AZUL = (14, 46, 120)
COLOR_BLANCO =
El sistema usará **Ritmo Vertical (Grilla)** y espaciado adaptativo para un diseño impecable.
""")

# --- CONFIGURACIÓN DISEÑO ---
ANCHO = 1080
ALTO =  (255, 255, 255)

MARGEN_IZQ = 230
MARGEN_DER = 50
MARGEN_IZQ_TRAMA = 21350
COLOR_FONDO = (242, 101, 50)
COLOR_AZUL = (14, 46, 120)
COLOR_BLAN27 

# Restricción Superior
MIN_Y_FECHA = 116 

MODO_BLENDING = 'lighten'  
OPACIDAD_TRAMA = 1.0  

#CO = (255, 255, 255)

MARGEN_IZQ = 230
MARGEN_DER = 50
MARGEN_IZQ_TRAMA = 22 --- RITMO VERTICAL (Módulo Base = 15px) ---

# MODO COMFORT (Para 1, 2 o 3 eventos)
CFG_COMFORT = {
    "TIT7 

# Restricción Superior
MIN_Y_FECHA = 116 

MODO_BLENDING = 'lighten'  
OPACIDAD_TRAMA = 1.0  

#ULO_SALTOLINEA": 75,      # 5 x 15px
    "ESPACIO_ENTRE_EVENTOS": 90,  # 6 x 15px
    "DIST --- MÓDULO DE LÍNEA BASE (Ritmo Vertical) ---
LINEA_BASE = 5 

# Función para forzar un número a ser múltiplo de la Línea Base (redondeo al másANCIA_LINEA_EVENTOS": 60,# 4 x 15px
    "DISTANCIA_FECHA_LINEA": 75,  # 5 x 15px (Ajustado cercano)
def to_base(val):
    return round(val / LINEA_BASE) * LINEA_BASE

# --- DEFINICIÓN DE DOS MODOS DE ESPACIADO ---

# MODO COMFORT (Para)
    "MARGEN_INFERIOR_CANVAS": 90  # 6 x 15px (Ajustado)
}

# MODO COMPACTO (Para 4 eventos)
CFG_COMP 1, 2 o 3 eventos) - Valores originales, ajustados a LINEA_BASE
CFG_COMFORT = {
    "ESPACIO_ENTRE_EVENTOS": to_base(90ACT = {
    "TITULO_SALTOLINEA": 75,      # 5 x 15px
    "ESPACIO_ENTRE_EVENTOS": 60,  # 4 x ),   # 90
    "DISTANCIA_LINEA_EVENTOS": to_base(60), # 60
    "DISTANCIA_FECHA_LINEA": to_base(80),15px (Ajustado para que entren 4)
    "DISTANCIA_LINEA_EVENTOS": 45,# 3 x 15px (Ajustado para que entren 4)
    "   # 80
    "MARGEN_INFERIOR_CANVAS": to_base(100)  # 100
}

# MODO COMPACTO (Para 4 eventos) - ValoresDISTANCIA_FECHA_LINEA": 60,  # 4 x 15px (Ajustado para que entren 4)
    "MARGEN_INFERIOR_CANVAS": 6 compactos, ajustados a LINEA_BASE
CFG_COMPACT = {
    "ESPACIO_ENTRE_EVENTOS": to_base(65),   # 65
    "DISTANCIA_LINEA_EVENTOS": to_base(50), # 50
    "DISTANCIA_FECHA_LINEA": to_base(70),   # 70
    "MAR0  # 4 x 15px (Ajustado para que entren 4)
}

# Saltos internos comunes (múltiplos de 15)
SALTO_CATEGORIA = 45 # GEN_INFERIOR_CANVAS": to_base(85)   # 85
}

# --- FUNCIONES ---

def obtener_fuente(ruta_preferida, tamaño):
    try:
3 x 15px
SALTO_INFO = 45      # 3 x 15px
MARGIN_POST_TITULO = 15 # 1 x 15px

# --- FUNCIONES ---        return ImageFont.truetype(ruta_preferida, tamaño)
    except IOError:
        return ImageFont.load_default()

def cargar_fuentes():
    return {
        "titulo":      obt

def obtener_fuente(ruta_preferida, tamaño):
    try:
        return ImageFont.truetype(ruta_preferida, tamaño)
    except IOError:
        return ImageFont.load_default()ener_fuente("assets/Archivo-Bold.ttf", 65),
        "fecha_header":obtener_fuente("assets/ArchivoBlack-Regular.ttf", 60),
        "categoria":

def cargar_fuentes():
    return {
        "titulo":      obtener_fuente("assets/Archivo-Bold.ttf", 65),
        "fecha_header":obtener_fuente("assets/   obtener_fuente("assets/Archivo-Bold.ttf", 30),
        "info":        obtener_fuente("assets/Archivo-Regular.ttf", 35),
        "info_ArchivoBlack-Regular.ttf", 60),
        "categoria":   obtener_fuente("assets/Archivo-Bold.ttf", 30),
        "info":        obtener_fuente("assetsbold":   obtener_fuente("assets/Archivo-Bold.ttf", 35),
        "sidebar":     obtener_fuente("assets/Coolvetica Rg.otf", 50) 
    /Archivo-Regular.ttf", 35),
        "info_bold":   obtener_fuente("assets/Archivo-Bold.ttf", 35),
        "sidebar":     obtener_fuente}

# --- AJUSTES EN EL RITMO VERTICAL ---

def calcular_altura_evento(fila):
    """ Calcula la altura exacta en píxeles que ocupará un evento, respetando la grilla. """
("assets/Coolvetica Rg.otf", 50) 
    }

def calcular_altura_evento(fila, cfg):
    """ Calcula la altura exacta que ocupará un evento, usando la CFG elegida.    altura_acumulada = 0
    altura_acumulada += to_base(45) # Categoría
    
    titulo = str(fila['Evento']).upper()
    lineas_titulo = """
    altura_acumulada = 0
    altura_acumulada += SALTO_CATEGORIA 
    
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap. textwrap.wrap(titulo, width=18)
    
    # Altura de cada línea de título (70) + Salto extra (15), ambos a la base
    salto_titulo = to_base(70)
    margin_titulo = to_base(15)
    
    altura_acumulada += (len(lineas_titulo) * salto_titulo) + margin_titulo
    
    alturawrap(titulo, width=18)
    # Título (Salto por línea + margen post título)
    altura_acumulada += (len(lineas_titulo) * cfg["TITULO_SALTOLINEA"]) + MARGIN_POST_TITULO
    
    altura_acumulada += SALTO_INFO # Lugar
    altura_acumulada += 35 # Cuándo (El alto del texto)
    return altura__acumulada += to_base(45) # Lugar
    altura_acumulada += to_base(35) # Cuándo
    
    return altura_acumulada

def paginar_eventosacumulada

def paginar_eventos(grupo_eventos):
    """
    Divide los eventos en páginas usando la CFG COMPACTA para determinar la CAPACIDAD MÁXIMA.
    """
(grupo_eventos):
    # (Usa CFG_COMPACT para el cálculo de capacidad)
    cfg = CFG_COMPACT 
    
    tope_superior_eventos = to_base(MIN_Y_FECHA) + cfg["DISTANCIA_FECHA_LINEA"] + cfg["DISTANCIA_LINEA_EVENTOS"]
    tope_inferior_eventos = ALTO - cfg["MAR    cfg = CFG_COMPACT 
    
    # Altura del header y footer basada en la CFG COMPACTA
    altura_header = MIN_Y_FECHA + cfg["DISTANCIA_FECHA_LINEA"] + cfg["DISTANCIA_LINEA_EVENTOS"]
    altura_footer = ALTO - cfg["MARGEN_INFERIOR_CANVAS"]
    max_altura_disponible = altura_footer - altura_GEN_INFERIOR_CANVAS"]
    
    max_altura_disponible = tope_inferior_eventos - tope_superior_eventos
    
    paginas = []
    pagina_actual =header
    
    paginas = []
    pagina_actual = []
    altura_actual = 0
    
    for index, fila in grupo_eventos.iterrows():
        # Calcular altura usando la CF []
    altura_actual = 0
    
    for index, fila in grupo_eventos.iterrows():
        h_evento = calcular_altura_evento(fila)
        
        espacio_necesG Compacta para ver si entra
        h_evento = calcular_altura_evento(fila, cfg)
        
        espacio_necesario = h_evento
        if len(pagina_actual) > 0ario = h_evento
        if len(pagina_actual) > 0:
            espacio_necesario += cfg["ESPACIO_ENTRE_EVENTOS"]
            
        if (altura_actual:
            espacio_necesario += cfg["ESPACIO_ENTRE_EVENTOS"]
            
        if (altura_actual + espacio_necesario) <= max_altura_disponible:
             + espacio_necesario) <= max_altura_disponible:
            pagina_actual.append(fila)
            altura_actual += espacio_necesario
        else:
            if pagina_actual: pagina_actual.append(fila)
            altura_actual += espacio_necesario
        else:
            if pagina_actual: 
                paginas.append(pd.DataFrame(pagina_actual))
            
                paginas.append(pd.DataFrame(pagina_actual))
            
            pagina_actual = [fila]
            altura_actual = h_evento
            
    if pagina_actual:
        paginas
            pagina_actual = [fila]
            altura_actual = h_evento
            
    if pagina_actual:
        paginas.append(pd.DataFrame(pagina_actual))
        
    return pag.append(pd.DataFrame(pagina_actual))
        
    return paginas

def dibujar_evento(draw, y_pos, fila, fuentes):
    """ Dibuja el evento, forzando la posicióninas

def dibujar_evento(draw, y_pos, fila, fuentes, cfg):
    # 1. CATEGORÍA
    cat_texto = f"—{str(fila['Categoria']).upper()}"
    draw.text Y a ser un múltiplo de la Línea Base. """
    # Siempre empezamos en una línea base
    y_pos = to_base(y_pos) 
    
    # 1. CATEGORÍA
    cat((MARGEN_IZQ, y_pos), cat_texto, font=fuentes["categoria"], fill=COLOR_BLANCO)
    y_pos += SALTO_CATEGORIA

    # 2. TÍTULO_texto = f"—{str(fila['Categoria']).upper()}"
    draw.text((MARGEN_IZQ, y_pos), cat_texto, font=fuentes["categoria"], fill=COLOR_BLANCO
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18) 
    for linea in lineas_titulo:
        draw.text(()
    y_pos += to_base(45)

    # 2. TÍTULO
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=MARGEN_IZQ, y_pos), linea, font=fuentes["titulo"], fill=COLOR_AZUL)
        y_pos += cfg["TITULO_SALTOLINEA"] # Salto de línea dinámico
    y_pos += MARGIN_POST_TITULO 

    # 3. LUGAR
    lugar_texto = f"Lugar: {fila['Lugar']}"
    if len(lugar_18)
    salto_titulo = to_base(70) 
    margin_titulo = to_base(15)

    for linea in lineas_titulo:
        draw.text((MARGEN_texto) > 40: lugar_texto = lugar_texto[:37] + "..."
    draw.text((MARGEN_IZQ, y_pos), lugar_texto, font=fuentes["info"],IZQ, y_pos), linea, font=fuentes["titulo"], fill=COLOR_AZUL)
        y_pos += salto_titulo
    y_pos += margin_titulo

    # 3. LUGAR
    lugar_texto = f"Lugar: {fila['Lugar']}"
    if len(lugar_texto) > 40: lugar_texto = lugar_texto[:37] + "..." fill=COLOR_AZUL)
    y_pos += SALTO_INFO

    # 4. CUÁNDO
    cuando_texto = f"Cuándo: {fila['Fecha_Abreviada']} —
    draw.text((MARGEN_IZQ, y_pos), lugar_texto, font=fuentes["info"], fill=COLOR_AZUL)
    y_pos += to_base(45)

 {fila['Hora']}"
    draw.text((MARGEN_IZQ, y_pos), cuando_texto, font=fuentes["info_bold"], fill=COLOR_AZUL)
    return y_pos

def aplicar_blending(fondo, capa_superior, modo):
    fondo_rgb = fondo.convert("RGB")
    capa_rgb = capa_superior.convert("RGB")
    if modo == 'lighten    # 4. CUÁNDO
    cuando_texto = f"Cuándo: {fila['Fecha_Abreviada']} — {fila['Hora']}"
    draw.text((MARGEN_IZQ, y_pos), cuando_texto, font=fuentes["info_bold"], fill=COLOR_AZUL)
    return y_pos

def aplicar_blending(fondo, capa_superior, modo):
    fondo': return ImageChops.lighter(fondo_rgb, capa_rgb)
    elif modo == 'multiply': return ImageChops.multiply(fondo_rgb, capa_rgb)
    elif modo == 'screen': return ImageChops.screen(fondo_rgb, capa_rgb)
    elif modo == 'overlay': return ImageChops.soft_light(fondo_rgb, capa_rgb)
    return capa_rgb

def generar_imagen_en_memoria(fecha_key, datos_grupo, fuentes):
    img = Image.new('RGB', (ANCHO, ALTO), color=COLOR_FONDO)
    draw = ImageDraw.Draw(img)

    # 1. Preparación y Selección de CFG
    if isinstance(datos_grupo, pd.DataFrame):
        lista_filas = list(datos_grupo.iterrows())
        items_para_calcular = [fila for idx, fila in lista_filas]
    else:
        items_para_calcular = datos_grupo

    cantidad_eventos = len(items_para_calcular)

    if cantidad_eventos >= 4:
        cfg = CFG_COMPACT
        mostrar_trama = False
    else:
        cfg = CFG_COMFORT
        mostrar_trama = True

    _rgb = fondo.convert("RGB")
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
        mostrar_# 2. CÁLCULO BOTTOM-UP (Usando la CFG elegida)
    altura_total_contenido = 0
    for fila in items_para_calcular:
        altura_total_contenido += calcular_trama = False
    else:
        cfg = CFG_COMFORT
        mostrar_trama = True

    # 1. CÁLCULO BOTTOM-UP
    altura_total_contenido = 0
    for fila in items_para_calcular:
        altura_total_contenido += calcular_altura_evento(fila)
    
    if cantidad_eventos > 1:
        altura_total_contenido +=altura_evento(fila, cfg)
    
    if cantidad_eventos > 1:
        altura_total_contenido += (cantidad_eventos - 1) * cfg["ESPACIO_ENTRE_EVENTOS"]

    y_inicio_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"] - altura_total_contenido
    y_linea = y_inicio_eventos - cfg (cantidad_eventos - 1) * cfg["ESPACIO_ENTRE_EVENTOS"]

    y_inicio_eventos = ALTO - cfg["MARGEN_INFERIOR_CANVAS"] - altura_["DISTANCIA_LINEA_EVENTOS"]
    y_fecha = y_linea - cfg["DISTANCIA_FECHA_LINEA"]
    
    # RESTRICCIÓN DE SEGURIDAD
    iftotal_contenido
    y_linea = y_inicio_eventos - cfg["DISTANCIA_LINEA_EVENTOS"]
    y_fecha = y_linea - cfg["DISTANCIA_FECHA y_fecha < MIN_Y_FECHA:
        diferencia = MIN_Y_FECHA - y_fecha
        y_fecha = MIN_Y_FECHA
        y_linea += diferencia
_LINEA"]
    
    # RESTRICCIÓN DE SEGURIDAD
    if y_fecha < MIN_Y_FECHA:
        diferencia = MIN_Y_FECHA - y_fecha
        y_inicio_eventos += diferencia

    # 3. TRAMA
    limite_trama = int(y_fecha - 10) 

    if mostrar_trama and os.path        y_fecha = MIN_Y_FECHA
        y_linea += diferencia
        y_inicio_eventos += diferencia
    
    # Ajustar todos los elementos principales a la línea base
    y_.exists("assets/trama.png") and limite_trama > 0:
        # (Lógica de trama se mantiene igual)
        try:
            tira = Image.open("assets/trama.png").convert("RGBA")
            if OPACIDAD_TRAMA < 1.0:
                alpha = tira.split()[3].point(lambda i: i * OPACIDAD_TRAMA)
                tira.putalpha(alpha)

            ancho_util_trama = ANCHO - MARGEN_IZQ_TRAMA
            ratio = ancho_util_trama / tira.width
            alto_tira = int(tira.height * ratio)
            tira = tira.resize((ancho_util_trama, alto_tira), Image.Resampling.LANCZOS)
            
            capfecha = to_base(y_fecha)
    y_linea = to_base(y_linea)
    y_inicio_eventos = to_base(y_inicio_eventos)

    a_trama = Image.new('RGBA', (ANCHO, limite_trama), (0,0,0,0))
            y_pegado = limite_trama - alto_tira
            while# 2. TRAMA
    limite_trama = int(y_fecha - 10) 

    if mostrar_trama and os.path.exists("assets/trama.png") and limite_trama > 0:
        try:
            tira = Image.open("assets/trama.png").convert("RGBA")
            if OPACIDAD_TRAMA < 1.0:
                alpha = tira.split()[3].point(lambda i: i * OPACIDAD_TRAMA)
                tira.putalpha(alpha)

            ancho_util_trama = ANCHO - y_pegado > -alto_tira:
                capa_trama.paste(tira, (MARGEN_IZQ_TRAMA, y_pegado), tira)
                y_pegado MARGEN_IZQ_TRAMA
            ratio = ancho_util_trama / tira.width
            alto_tira = int(tira.height * ratio)
            tira = tira.resize(( -= alto_tira

            if MODO_BLENDING:
                fondo_zona = img.crop((0, 0, ANCHO, limite_trama))
                zona_mezclada = aplicar_blending(fondo_zona, capa_trama, MODO_BLENDING)
                img.paste(zona_mezclada, (0, 0))
            else:
                img.paste(capa_ancho_util_trama, alto_tira), Image.Resampling.LANCZOS)
            
            capa_trama = Image.new('RGBA', (ANCHO, limite_trama),trama, (0, 0), capa_trama)
        except Exception:
            pass

    # 4. Elementos Fijos
    txt_sidebar = "conectando—cultura"
    cap (0,0,0,0))
            y_pegado = limite_trama - alto_tira
            while y_pegado > -alto_tira:
                capa_trama.paste(tira, (MARGEN_IZQ_TRAMA, y_pegado), tira)
                y_pegado -= alto_tira

            if MODO_BLENDING:
                fondo_zona = img.crop((0, 0, ANCHO, limite_trama))
                zona_mezclada = aplicar_blending(fondo_zona, capa_trama, MODO_BLENDING)
                img.a_txt = Image.new('RGBA', (800, 100), (255, 255, 255, 0))
    d_txt = ImageDraw.Drawpaste(zona_mezclada, (0, 0))
            else:
                img.paste(capa_trama, (0, 0), capa_trama)
        except Exception:
            (capa_txt)
    d_txt.text((0, 0), txt_sidebar, font=fuentes["sidebar"], fill=COLOR_AZUL)
    rotado = capa_txt.rotate(pass

    # 3. Elementos Fijos
    txt_sidebar = "conectando—cultura"
    capa_txt = Image.new('RGBA', (800, 100), (90, expand=1)
    img.paste(rotado, (82, ALTO - 900), rotado)

    if os.path.exists("assets/logo.png"):
        try255, 255, 255, 0))
    d_txt = ImageDraw.Draw(capa_txt)
    d_txt.text((0, 0), txt_:
            logo = Image.open("assets/logo.png").convert("RGBA")
            logo.thumbnail((150, 150))
            img.paste(logo, (37, 5sidebar, font=fuentes["sidebar"], fill=COLOR_AZUL)
    rotado = capa_txt.rotate(90, expand=1)
    img.paste(rotado, (82, AL0), logo)
        except: pass

    header_texto = str(fecha_key).replace(" ", "#").upper()
    bbox = draw.textbbox((0, 0), header_texto, font=TO - 900), rotado)

    if os.path.exists("assets/logo.png"):
        try:
            logo = Image.open("assets/logo.png").convert("RGBA")
fuentes["fecha_header"])
    ancho_txt = bbox[2] - bbox[0]
    draw.text((ANCHO - MARGEN_DER - ancho_txt, y_fecha), header_texto            logo.thumbnail((150, 150))
            img.paste(logo, (37, 50), logo)
        except: pass

    header_texto = str(fecha_key, font=fuentes["fecha_header"], fill=COLOR_AZUL)

    draw.line([(MARGEN_IZQ, y_linea), (ANCHO - MARGEN_DER, y_linea)],).replace(" ", "#").upper()
    bbox = draw.textbbox((0, 0), header_texto, font=fuentes["fecha_header"])
    ancho_txt = bbox[2] - bbox fill=COLOR_AZUL, width=5)

    # 5. Eventos
    y_cursor = y_inicio_eventos
    for fila in items_para_calcular:
        y_fin =[0]
    draw.text((ANCHO - MARGEN_DER - ancho_txt, y_fecha), header_texto, font=fuentes["fecha_header"], fill=COLOR_AZUL)

    draw. dibujar_evento(draw, y_cursor, fila, fuentes, cfg)
        y_cursor = y_fin + cfg["ESPACIO_ENTRE_EVENTOS"]
    
    return img

# --- Lline([(MARGEN_IZQ, y_linea), (ANCHO - MARGEN_DER, y_linea)], fill=COLOR_AZUL, width=5)

    # 4. Eventos
    ÓGICA DE LA INTERFAZ ---

uploaded_file = st.file_uploader("Arrastra tu CSV aquí", type=["csv"])

if uploaded_file is not None:
    try:
        try:
y_cursor = y_inicio_eventos
    for fila in items_para_calcular:
        y_fin = dibujar_evento(draw, y_cursor, fila, fuentes)
        y_cursor = y            df = pd.read_csv(uploaded_file, encoding='utf-8', dtype=str)
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin-_fin + cfg["ESPACIO_ENTRE_EVENTOS"] # Usamos el espacio de la config elegida
    
    return img

# --- LÓGICA DE LA INTERFAZ ---

uploaded_file1', dtype=str)
        
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
                        status_text.text(f" = st.file_uploader("Arrastra tu CSV aquí", type=["csv"])

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
            
            if st.button("Analizando: {fecha}...")
                        
                        # PAGINACIÓN
                        paginas = paginar_eventos(grupo)
                        
                        for idx_pag, pagina_data in enumerate(paginas):
                            🚀 Generar Imágenes"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                fuentes = cargar_fuentes()
                
                grupos = df.groupby('Fecha_Abreviada', sort=False)
                total_grupos = len(grupos)
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, (fecha, grupo) in enumerate(grupos):
                        status_text.text(f"Analizando: {fecha}...")
                        
                        # PAGimg = generar_imagen_en_memoria(fecha, pagina_data, fuentes)
                            
                            nombre_base = str(fecha).replace(" ", "_").replace("/", "-")
                            
                            if len(pagINACIÓN
                        paginas = paginar_eventos(grupo)
                        
                        for idx_pag, pagina_data in enumerate(paginas):
                            img = generar_imagen_en_memoria(fecha,inas) > 1:
                                nombre_archivo = f"post_{nombre_base}_{idx_pag + 1}.png"
                            else:
                                nombre_archivo = f"post_{nombre_base}.png pagina_data, fuentes)
                            
                            nombre_base = str(fecha).replace(" ", "_").replace("/", "-")
                            
                            if len(paginas) > 1:
                                nombre_archivo = f"
                            
                            img_bytes = io.BytesIO()
                            img.save(img_bytes, format='PNG')
                            zf.writestr(nombre_archivo, img_bytes.getvalue())
                        
"post_{nombre_base}_{idx_pag + 1}.png"
                            else:
                                nombre_archivo = f"post_{nombre_base}.png"
                            
                            img_bytes = io.BytesIO                        progress_bar.progress((i + 1) / total_grupos)
                
                status_text.text("¡Listo! Imágenes generadas.")
                progress_bar.empty()
                
                st()
                            img.save(img_bytes, format='PNG')
                            zf.writestr(nombre_archivo, img_bytes.getvalue())
                        
                        progress_bar.progress((i + 1) /.download_button(
                    label="📥 Descargar Imágenes (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name="posts_instagram.zip",
                    mime="application/zip"
                )

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
 total_grupos)
                
                status_text.text("¡Listo! Imágenes generadas.")
                progress_bar.empty()
                
                st.download_button(
                    label="📥 Descargar Imágenes```
