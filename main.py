import os
import csv
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import numpy as np
from functions.extraer_datos import (
    extract_first_folio_token, 
    extract_rut_from_text,
    extract_fecha_from_text,
    extract_nombre_from_q1,
    ocr_text_from_region
)

def pdf_primera_pagina_a_imagen(pdf_path):
    """
    Convierte la primera página de un PDF a imagen usando PyMuPDF
    Retorna una imagen PIL
    """
    try:
        # Abrir PDF con PyMuPDF
        doc = fitz.open(pdf_path)
        if doc.page_count < 1:
            return None
        
        # Obtener primera página
        page = doc[0]
        
        # Convertir a imagen con resolución aumentada para mejor OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        
        # Convertir a imagen PIL
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        doc.close()
        return img
        
    except Exception as e:
        print(f"Error convirtiendo PDF a imagen: {str(e)}")
        return None

def procesar_primera_pagina_pdf(pdf_path):
    """
    Procesa solo la primera página de un PDF y extrae sus datos
    Retorna un diccionario con los datos extraídos
    """
    try:
        # Convertir primera página a imagen
        primera_pagina = pdf_primera_pagina_a_imagen(pdf_path)
        if primera_pagina is None:
            return None
        
        # Realizar OCR en la página completa
        ocr_page_text = pytesseract.image_to_string(primera_pagina, lang="spa+eng")
        
        # Extraer folio
        folio = extract_first_folio_token(ocr_page_text)
        
        # Si hay folio, extraer los demás datos
        datos = {
            'folio': '',
            'fecha': '',
            'rut': '',
            'nombre': '',
            'estado': ''
        }
        
        if folio:
            # Convertir PIL Image a archivo temporal para poder usar ocr_text_from_region
            temp_img_path = "temp_page.jpg"
            primera_pagina.save(temp_img_path)
            
            # Extraer texto de regiones específicas
            q1_text = ocr_text_from_region(temp_img_path, (0, 0, 515, 190))
            q2_text = ocr_text_from_region(temp_img_path, (1154, 0, 10**9, 174))
            
            # Eliminar imagen temporal
            os.remove(temp_img_path)
            
            # Extraer datos
            datos['folio'] = folio
            datos['rut'] = extract_rut_from_text(q1_text)
            datos['fecha'] = extract_fecha_from_text(q2_text)
            datos['nombre'] = extract_nombre_from_q1(q1_text, datos['rut'])
            
        return datos
        
    except Exception as e:
        print(f"Error procesando PDF: {str(e)}")
        return None

def procesar_directorio_pdfs(directorio_entrada):
    """
    Procesa todos los PDFs en un directorio y extrae sus datos
    """
    # Verificar que el directorio existe
    if not os.path.exists(directorio_entrada):
        print(f"❌ Error: El directorio {directorio_entrada} no existe")
        return False

    # Obtener lista de PDFs en el directorio
    pdfs = [f for f in os.listdir(directorio_entrada) if f.lower().endswith('.pdf')]
    
    if not pdfs:
        print("❌ No se encontraron archivos PDF en el directorio")
        return False

    resultados = []
    total_pdfs = len(pdfs)

    print(f"🔍 Procesando {total_pdfs} archivos PDF...")

    for i, pdf in enumerate(pdfs, 1):
        try:
            print(f"\n📄 Procesando {pdf} ({i}/{total_pdfs})...")
            pdf_path = os.path.join(directorio_entrada, pdf)
            
            # Procesar primera página del PDF
            datos = procesar_primera_pagina_pdf(pdf_path)
            
            if datos:
                datos['nombre_pdf'] = pdf
                datos['path_pdf'] = pdf_path
                resultados.append(datos)
                print(f"✅ Datos extraídos exitosamente:")
                print(f"   📎 Folio: {datos['folio']}")
                print(f"   🆔 RUT: {datos['rut']}")
                print(f"   📅 Fecha: {datos['fecha']}")
                print(f"   👤 Nombre: {datos['nombre'][:50]}{'...' if len(datos['nombre'])>50 else ''}")
            else:
                print(f"⚠️ No se pudieron extraer datos de {pdf}")
                resultados.append({
                    'nombre_pdf': pdf,
                    'path_pdf': pdf_path,
                    'folio': '',
                    'fecha': '',
                    'rut': '',
                    'nombre': '',
                    'estado': ''
                })

        except Exception as e:
            print(f"❌ Error procesando {pdf}: {str(e)}")

    # Generar CSV con los resultados
    if resultados:
        output_csv = 'resultados_pdfs.csv'
        fieldnames = ['nombre_pdf', 'path_pdf', 'folio', 'fecha', 'rut', 'nombre', 'estado']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resultados)
        
        print(f"\n✅ Proceso completado. Se generó el archivo: {output_csv}")
        print(f"📊 Total de documentos procesados: {len(resultados)}")
        return True
    
    return False

if __name__ == "__main__":
    # Directorio que contiene los PDFs a procesar
    DIRECTORIO_PDFS = "pdfs_entrada"  # Ajusta este valor según tu necesidad
    
    print("🚀 Iniciando procesamiento de PDFs...")
    procesar_directorio_pdfs(DIRECTORIO_PDFS)