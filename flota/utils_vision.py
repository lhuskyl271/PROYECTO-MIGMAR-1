# flota/utils_vision.py
import re
from google.cloud import vision
from django.conf import settings

def detectar_texto_en_imagen(imagen_memoria):
    """
    Recibe un archivo de imagen en memoria (request.FILES['foto']),
    lo envía a Google Vision y retorna el número más probable encontrado.
    """
    try:
        # Instanciar el cliente con tus credenciales
        client = vision.ImageAnnotatorClient.from_service_account_json(
            settings.GOOGLE_APPLICATION_CREDENTIALS_PATH
        )

        # Leer el contenido de la imagen
        content = imagen_memoria.read()
        image = vision.Image(content=content)

        # Realizar la detección de texto
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if not texts:
            return None

        # El primer elemento (texts[0]) contiene todo el texto encontrado en bloque
        description = texts[0].description
        
        # --- LÓGICA DE LIMPIEZA ---
        # Buscamos patrones numéricos. 
        # Eliminamos espacios para casos como "241 178" -> "241178"
        # Reemplazamos 'O' o 'o' por '0' (error común de OCR)
        texto_limpio = description.replace(' ', '').replace('O', '0').replace('o', '0')
        
        # Regex para buscar números (enteros o decimales)
        # Busca secuencias de dígitos que pueden tener un punto decimal
        numeros = re.findall(r'\d+\.?\d+', texto_limpio)

        if numeros:
            # Lógica simple: Devolver el número más largo encontrado (suele ser el odómetro)
            # O podrías devolver el valor numérico más grande.
            # Aquí tomamos el que tenga más caracteres numéricos para evitar confundir con "km" o "mph"
            numero_final = max(numeros, key=len)
            return float(numero_final)
        
        return None

    except Exception as e:
        print(f"Error en OCR Google Vision: {e}")
        return None