import os
import csv
from functions.generate_documentos import process_pdf_to_images_and_csv, get_pdf_name_without_extension
from functions.extraer_datos import process_document_ocr

def procesar_directorio_pdfs(directorio_entrada):
    """
    Procesa todos los PDFs en un directorio y extrae sus datos
    """
    # Verificar que el directorio existe
    if not os.path.exists(directorio_entrada):
        print(f"❌ Error: El directorio {directorio_entrada} no existe")
        return False

    # Crear directorios necesarios si no existen
    os.makedirs('input', exist_ok=True)
    os.makedirs('documentos', exist_ok=True)

    # Obtener lista de PDFs en el directorio
    pdfs = [f for f in os.listdir(directorio_entrada) if f.lower().endswith('.pdf')]
    
    if not pdfs:
        print("❌ No se encontraron archivos PDF en el directorio")
        return False

    resultados = []

    for pdf in pdfs:
        try:
            print(f"\n🔄 Procesando: {pdf}")
            
            # Copiar PDF a carpeta input
            pdf_origen = os.path.join(directorio_entrada, pdf)
            pdf_destino = os.path.join('input', pdf)
            
            if os.path.exists(pdf_destino):
                os.remove(pdf_destino)  # Eliminar si ya existe
            
            with open(pdf_origen, 'rb') as src, open(pdf_destino, 'wb') as dst:
                dst.write(src.read())

            # Obtener nombre sin extensión
            pdf_name = get_pdf_name_without_extension(pdf)
            
            # Procesar PDF a imágenes y crear estructura inicial
            if process_pdf_to_images_and_csv(pdf_destino, pdf_name):
                # Extraer datos con OCR
                if process_document_ocr(pdf_name):
                    # Leer datos extraídos
                    csv_path = os.path.join('documentos', pdf_name, f"{pdf_name}.csv")
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            resultados.append({
                                'nombre_pdf': pdf,
                                'path_pdf': pdf_origen,
                                'folio': row.get('folio', ''),
                                'fecha': row.get('fecha', ''),
                                'rut': row.get('rut', ''),
                                'nombre': row.get('nombre', ''),
                                'estado': row.get('estado', '')
                            })

        except Exception as e:
            print(f"❌ Error procesando {pdf}: {str(e)}")

    # Generar CSV con todos los resultados
    if resultados:
        output_csv = 'resultados_pdfs.csv'
        fieldnames = ['nombre_pdf', 'path_pdf', 'folio', 'fecha', 'rut', 'nombre', 'estado']
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resultados)
        
        print(f"\n✅ Proceso completado. Se generó el archivo: {output_csv}")
        print(f"📊 Total de registros procesados: {len(resultados)}")
        return True
    
    return False

if __name__ == "__main__":
    # Directorio que contiene los PDFs a procesar
    DIRECTORIO_PDFS = "pdfs_entrada"  # Ajusta este valor según tu necesidad
    
    print("🚀 Iniciando procesamiento de PDFs...")
    procesar_directorio_pdfs(DIRECTORIO_PDFS)