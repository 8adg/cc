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
Sube tu archivo **CSV** y descarga las imágenes. 
Si un día tiene muchos eventos, el sistema generará automáticamente varias imágenes (Parte 1, Parte 2...) respetando los márgenes.
""")

# --- CONFIGURACIÓN DISEÑO ---
ANCHO = 1080
ALTO = 1350
COLOR_FONDO = (242, 101, 50)
COLOR_AZUL = (14, 46, 120)
COLOR_BLANCO = (255, 255, 255)

MARGEN_IZQ = 230
MARGEN_DER = 50
MARGEN_INFERIOR_CANVAS = 100 
MARGEN_IZQ_TRAMA = 227 

# --- RESTRICCIÓN SUPERIOR (NUEVO) ---
# La fecha nunca estará más arriba que este píxel
MIN_Y_FECHA = 116 

MODO_BLENDING = 'lighten'  
OPACIDAD_TRAMA = 1.0  

ESPACIO_ENTRE_EVENTOS = 90
DISTANCIA_LINEA_EVENTOS = 60
DISTANCIA_FECHA_LINEA = 80

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
    """ Calcula la altura exacta en píxeles que ocupará un evento individual """
    altura_acumulada = 0
    altura_acumulada += 45 # Categoría
    
    titulo = str(fila['Evento']).upper()
    lineas_titulo = textwrap.wrap(titulo, width=18)
    altura_acumulada += (len(lineas_titulo) * 70) + 15 # Título + margin
    
    altura_acumulada += 45 # Lugar
    altura_acumulada += 35 # Cuándo
    return altura_acumulada

def paginar_eventos(grupo_eventos):
    """
    Divide una lista de eventos en varias páginas si exceden la altura permitida.
    Retorna una lista de DataFrames (uno por página).
    """
    # 1. Calcular espacio máximo disponible para los eventos
    # Formula: Alto Total - Margen Abajo - (Espacio ocupado por el Header Arriba)
    # El Header Arriba ocupa: MIN_Y_FECHA + AlturaFecha(aprox) + DistanciaLinea + DistanciaEventos
    
    # Altura ocupada por la cabecera antes de empezar a escribir eventos:
    # (El texto fecha mide aprox 60px de alto, pero la coord Y es el top, así que usamos las distancias relativas)
    # y_linea = y_fecha + 80
    # y_inicio_eventos = y_linea + 60
    # Por tanto, el tope de eventos es: MIN_Y_FECHA + 80 + 60 = MIN_Y_FECHA + 140
    
    tope_superior_eventos = MIN_Y_FECHA + DISTANCIA_FECHA_LINEA + DISTANCIA_LINEA_EVENTOS
    tope_inferior_eventos = ALTO - MARGEN_INFERIOR_CANVAS
    
    max_altura_disponible = tope_inferior_eventos - tope_superior_eventos
    
    paginas = []
    pagina_actual = []
    altura_actual = 0
    
    for index, fila in grupo_eventos.iterrows():
        h_evento = calcular_altura_evento(fila)
        
        # Calcular cuánto ocuparía si lo agregamos
        # Si ya hay eventos, sumamos el espacio entre eventos
        espacio_necesario = h_evento
        if len(pagina_actual) > 0:
            espacio_necesario += ESPACIO_ENTRE_EVENTOS
            
        if (altura_actual + espacio_necesario) <= max_altura_disponible:
            # Entra en la página actual
            pagina_actual.append(fila)
            altura_actual += espacio_necesario
        else:
            # No entra, cerramos página actual y creamos una nueva
            if pagina_actual: # Guardar la anterior si tiene algo
                paginas.append(pd.DataFrame(pagina_actual))
            
            # Iniciar nueva página con este evento
            pagina_actual = [fila]
            altura_actual = h_evento
            
    # Guardar la última página pendiente
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

    # 1. CÁLCULO BOTTOM-UP
    altura_total_contenido = 0
    lista_filas = list(datos_grupo.iterrows())
    cantidad_eventos = len(lista_filas)
    
    for index, fila in lista_filas:
        altura_total_contenido += calcular_altura_evento(fila)
    
    if cantidad_eventos > 1:
        altura_total_contenido += (cantidad_eventos - 1) * ESPACIO_ENTRE_EVENTOS

    # Calculamos dónde empiezan los eventos desde abajo
    y_inicio_eventos = ALTO - MARGEN_INFERIOR_CANVAS - altura_total_contenido
    
    # Calculamos las líneas superiores relativas a los eventos
    y_linea = y_inicio_eventos - DISTANCIA_LINEA_EVENTOS
    y_fecha = y_linea - DISTANCIA_FECHA_LINEA 
    
    # --- RESTRICCIÓN DE SEGURIDAD ---
    # Gracias a la paginación, esto casi nunca debería pasar, pero forzamos por si acaso.
    # Si por alguna razón matemática y_fecha quedó muy arriba, la app no se rompe,
    # solo se verá un poco apretado abajo, pero respetará el margen superior.
    if y_fecha < MIN_Y_FECHA:
        diferencia = MIN_Y_FECHA - y_fecha
        y_fecha = MIN_Y_FECHA
        y_linea += diferencia
        y_inicio_eventos += diferencia

    # 2. TRAMA
    limite_trama = int(y_fecha - 10) 
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
    for i, (index, fila) in enumerate(lista_filas):
        y_fin = dibujar_evento(draw, y_cursor, fila, fuentes)
        y_cursor = y_fin + ESPACIO_ENTRE_EVENTOS
    
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
                
                # Agrupamos por fecha
                grupos = df.groupby('Fecha_Abreviada', sort=False)
                total_grupos = len(grupos)
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for i, (fecha, grupo) in enumerate(grupos):
                        status_text.text(f"Analizando: {fecha}...")
                        
                        # PAGINACIÓN: Dividimos el grupo en páginas si es necesario
                        paginas = paginar_eventos(grupo)
                        
                        for idx_pag, pagina_data in enumerate(paginas):
                            # Generamos la imagen para esta página
                            img = generar_imagen_en_memoria(fecha, pagina_data, fuentes)
                            
                            # Nombrado de archivo
                            nombre_base = str(fecha).replace(" ", "_").replace("/", "-")
                            
                            # Si hay más de una página, agregamos sufijo _1, _2
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
