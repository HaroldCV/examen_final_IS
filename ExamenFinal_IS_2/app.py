from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'lugares_favoritos.db'


def create_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Crear la tabla "lugares"
    c.execute('''CREATE TABLE IF NOT EXISTS lugares
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nombre TEXT NOT NULL,
                  direccion TEXT NOT NULL)''')

    conn.commit()
    conn.close()


def insert_lugar(nombre, direccion):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("INSERT INTO lugares (nombre, direccion) VALUES (?, ?)", (nombre, direccion))

    conn.commit()
    conn.close()


def get_lugares():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM lugares")
    lugares = [{'id': row[0], 'nombre': row[1], 'direccion': row[2]} for row in c.fetchall()]

    conn.close()

    return lugares


def update_lugar(lugar_id, nombre, direccion):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("UPDATE lugares SET nombre = ?, direccion = ? WHERE id = ?", (nombre, direccion, lugar_id))

    conn.commit()
    conn.close()


@app.route('/lugares', methods=['POST'])
def crear_lugar():
    lugar = request.json
    if lugar.get('nombre') and lugar.get('direccion'):
        nombre = lugar['nombre']
        direccion = lugar['direccion']

        insert_lugar(nombre, direccion)

        return jsonify({'message': 'Lugar creado exitosamente'}), 201
    else:
        return jsonify({'error': 'Datos incompletos'}), 400

@app.route('/lugares', methods=['GET'])
def listar_lugares():
    lugares = get_lugares()
    if lugares:
        return jsonify(lugares), 200
    else:
        return jsonify({'error': 'No hay lugares disponibles'}), 404


@app.route('/lugares/<int:lugar_id>', methods=['PUT'])
def actualizar_lugar(lugar_id):
    lugar = request.json
    nombre = lugar.get('nombre')
    direccion = lugar.get('direccion')

    update_lugar(lugar_id, nombre, direccion)

    return jsonify({'message': 'Lugar actualizado exitosamente'}), 200


@app.route('/lugares/<int:lugar_id>', methods=['GET'])
def obtener_lugar(lugar_id):
    lugar = get_lugar_por_id(lugar_id)
    if lugar:
        lugar_dict = {'id': lugar[0], 'nombre': lugar[1], 'direccion': lugar[2]}
        return jsonify(lugar_dict), 200
    else:
        return jsonify({'error 404': 'Lugar no encontrado'}), 404

def get_lugar_por_id(lugar_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT * FROM lugares WHERE id = ?", (lugar_id,))
    lugar = c.fetchone()

    conn.close()

    return lugar

# Ruta para generar un error 500 (Error interno del servidor)
@app.route('/error', methods=['GET'])
def generar_error():
    # Simulación de un error interno del servidor
    # Algo salió mal en el servidor y no se puede procesar la solicitud
    return jsonify({'error': 'Error interno del servidor'}), 500


# Ruta para generar un error 204 (No Content)
@app.route('/lugares/<int:lugar_id>', methods=['DELETE'])
def eliminar_lugar(lugar_id):
    # Eliminar el lugar de la base de datos
    # ...
    return '', 204


# Ruta para generar un error 403 (Forbidden)
@app.route('/lugares', methods=['POST'])
def crear_lugar_forbidden():
    return jsonify({'error': 'Acceso denegado para crear lugares'}), 403


# Ruta para generar un error 422 (Unprocessable Entity)
@app.route('/lugares', methods=['PUT'])
def actualizar_lugar_unprocessable_entity():
    return jsonify({'error': 'Entidad no procesable'}), 422


if __name__ == '__main__':
    #create_database()
    app.run()
