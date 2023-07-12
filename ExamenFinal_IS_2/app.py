from flask import Flask, request, jsonify
import requests
import sqlite3
import json

app = Flask(__name__)
conn = sqlite3.connect('lugares_favoritos.db')
cursor = conn.cursor()

# Creación de la tabla lugares_favoritos si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS lugares_favoritos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lugar TEXT,
        latitud REAL,
        longitud REAL,
        fecha TEXT,
        temperatura_max_diario REAL,
        temperatura_max_hora REAL,
        eliminado INTEGER DEFAULT 0
    )
''')

conn.commit()

def obtener_conexion():
    return sqlite3.connect('lugares_favoritos.db')

@app.route('/lugares', methods=['POST'])
def guardar_lugar_favorito():
    nombre_lugar = request.form.get('nombre_lugar')

    # Verificar si el lugar ya existe en la base de datos
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM lugares_favoritos WHERE lugar = ?', (nombre_lugar,))
    lugar_existente = cursor.fetchone()
    
    if lugar_existente:
        cursor.close()
        conn.close()
        return jsonify({'message': 'El lugar ya existe como favorito'}), 409

    clima = obtener_clima(nombre_lugar)

    if clima:
        try:
            # Obtener el último ID insertado
            cursor.execute('SELECT MAX(id) FROM lugares_favoritos')
            max_id = cursor.fetchone()[0]
            
            siguiente_id = max_id + 1 if max_id is not None else 1

            cursor.execute('''
                INSERT INTO lugares_favoritos (id, lugar, latitud, longitud, fecha, temperatura_max_diario, temperatura_max_hora)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (siguiente_id, clima['lugar'], clima['latitud'], clima['longitud'], clima['fecha'], clima['temperatura_max_diario'], clima['temperatura_max_hora']))
            conn.commit()

            lugar_guardado = {
                'lugar': clima['lugar'],
                'latitud': clima['latitud'],
                'longitud': clima['longitud'],
                'fecha': clima['fecha'],
                'temperatura_max_diario': clima['temperatura_max_diario'],
                'temperatura_max_hora': clima['temperatura_max_hora']
            }

            cursor.close()
            conn.close()

            return jsonify(lugar_guardado), 201
        except sqlite3.Error as e:
            print(f"Error al guardar el lugar favorito: {e}")
            return jsonify({'message': 'Error al guardar el lugar favorito'}), 500
    else:
        return jsonify({'message': 'No se pudo obtener el clima del lugar'}), 404



@app.route('/lugares', methods=['GET'])
def listar_lugares_favoritos():
    try:
        conn = obtener_conexion()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM lugares_favoritos WHERE eliminado = 0')
        rows = cursor.fetchall()

        lugares_favoritos = []
        for row in rows:
            lugar_favorito = {
                'id': row[0],
                'lugar': row[1],
                'latitud': row[2],
                'longitud': row[3],
                'fecha': row[4],
                'temperatura_max_diario': row[5],
                'temperatura_max_hora': row[6]
            }
            lugares_favoritos.append(lugar_favorito)

        cursor.close()
        conn.close()

        return jsonify(lugares_favoritos), 200
    except sqlite3.Error as e:
        error_message = f"Error al listar los lugares favoritos: {str(e)}"
        print(error_message)
        return jsonify({'message': error_message}), 500



@app.route('/lugares/<int:lugar_id>', methods=['PUT'])
def actualizar_lugar_favorito(lugar_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM lugares_favoritos WHERE id = ?', (lugar_id,))
        lugar = cursor.fetchone()

        if lugar:
            # Obtener los datos parciales del cuerpo de la solicitud JSON
            datos_actualizados = request.json

            # Convertir la tupla en una lista para poder modificar sus elementos
            lugar_lista = list(lugar)

            # Actualizar solo los campos presentes en los datos parciales
            if 'latitud' in datos_actualizados:
                lugar_lista[2] = datos_actualizados['latitud']
            if 'longitud' in datos_actualizados:
                lugar_lista[3] = datos_actualizados['longitud']

            # Convertir la lista de vuelta a una tupla antes de la actualización
            lugar_actualizado = tuple(lugar_lista)

            cursor.execute('''
                UPDATE lugares_favoritos
                SET latitud = ?, longitud = ?
                WHERE id = ?
            ''', (lugar_actualizado[2], lugar_actualizado[3], lugar_id))
            conn.commit()

            return jsonify({'message': 'Lugar favorito actualizado correctamente'}), 200
        else:
            return jsonify({'message': 'Lugar favorito no encontrado'}), 404
    except sqlite3.Error as e:
        print(f"Error al actualizar el lugar favorito: {e}")
        return jsonify({'message': 'Error al actualizar el lugar favorito'}), 500
    finally:
        cursor.close()
        conn.close()

# ...


def obtener_clima(nombre_lugar):
    url_lugar = f"https://nominatim.openstreetmap.org/search?q={nombre_lugar}&format=json"
    response_lugar = requests.get(url_lugar)

    if response_lugar.status_code == 200:
        data_lugar = response_lugar.json()

        if data_lugar:
            latitud = float(data_lugar[0]['lat'])
            longitud = float(data_lugar[0]['lon'])

            url_diario = f"https://api.open-meteo.com/v1/forecast?latitude={latitud}&longitude={longitud}&forecast_days=2&daily=temperature_2m_max&timezone=PST"
            url_horario = f"https://api.open-meteo.com/v1/forecast?latitude={latitud}&longitude={longitud}&forecast_days=2&hourly=temperature_2m&timezone=PST"

            response_diario = requests.get(url_diario)
            response_horario = requests.get(url_horario)

            if response_diario.status_code == 200 and response_horario.status_code == 200:
                data_diario = response_diario.json()
                data_horario = response_horario.json()

                fecha = data_diario['daily']['time'][1]
                clima_diario = data_diario['daily']['temperature_2m_max'][1]
                clima_horario = data_horario['hourly']['temperature_2m'][24]

                return {
                    'lugar': nombre_lugar,
                    'latitud': latitud,
                    'longitud': longitud,
                    'fecha': fecha,
                    'temperatura_max_diario': clima_diario,
                    'temperatura_max_hora': clima_horario
                }
            else:
                print(f"Error al obtener los datos meteorológicos para {nombre_lugar}")
                return None
        else:
            print(f"No se encontró el lugar: {nombre_lugar}")
            return None
    else:
        print(f"Error al obtener los datos del lugar: {response_lugar.status_code}")
        return None
    

@app.route('/lugares/<int:lugar_id>', methods=['GET'])
def obtener_lugar_favorito(lugar_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM lugares_favoritos WHERE id = ?', (lugar_id,))
        lugar = cursor.fetchone()

        if lugar:
            lugar_favorito = {
                'id': lugar[0],
                'lugar': lugar[1],
                'latitud': lugar[2],
                'longitud': lugar[3],
                'fecha': lugar[4],
                'temperatura_max_diario': lugar[5],
                'temperatura_max_hora': lugar[6]
            }
            return jsonify(lugar_favorito), 200
        else:
            return jsonify({'message': 'Lugar favorito no encontrado'}), 404
    except sqlite3.Error as e:
        print(f"Error al obtener el lugar favorito: {e}")
        return jsonify({'message': 'Error al obtener el lugar favorito'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/lugares/<int:lugar_id>', methods=['DELETE'])
def borrar_lugar_favorito(lugar_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM lugares_favoritos WHERE id = ?', (lugar_id,))
        lugar = cursor.fetchone()

        if lugar:
            cursor.execute('DELETE FROM lugares_favoritos WHERE id = ?', (lugar_id,))
            conn.commit()

            return jsonify({'message': 'Lugar favorito eliminado correctamente'}), 200
        else:
            return jsonify({'message': 'Lugar favorito no encontrado'}), 404
    except sqlite3.Error as e:
        print(f"Error al borrar el lugar favorito: {e}")
        return jsonify({'message': 'Error al borrar el lugar favorito'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/lugares/<int:lugar_id>', methods=['PATCH'])
def actualizar_parcial_lugar_favorito(lugar_id):
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM lugares_favoritos WHERE id = ?', (lugar_id,))
        lugar = cursor.fetchone()

        if lugar:
            # Analizar los datos JSON enviados en el cuerpo de la solicitud
            datos_actualizados = json.loads(request.data)

            # Actualizar selectivamente los campos del lugar favorito con los nuevos valores
            for campo, valor in datos_actualizados.items():
                # Validar si el campo existe en la base de datos antes de actualizarlo
                if campo in ['lugar', 'latitud', 'longitud', 'fecha', 'temperatura_max_diario', 'temperatura_max_hora']:
                    cursor.execute(f'UPDATE lugares_favoritos SET {campo} = ? WHERE id = ?', (valor, lugar_id))

            # Guardar los cambios en la base de datos
            conn.commit()

            return jsonify({'message': 'Lugar favorito actualizado correctamente'}), 200
        else:
            return jsonify({'message': 'Lugar favorito no encontrado'}), 404
    except sqlite3.Error as e:
        print(f"Error al actualizar parcialmente el lugar favorito: {e}")
        return jsonify({'message': 'Error al actualizar parcialmente el lugar favorito'}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
    app.add_url_rule('/lugares/<int:lugar_id>', view_func=borrar_lugar_favorito, methods=['DELETE'])
