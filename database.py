from pymongo import MongoClient

def dbConnection():
    """
    Establece una conexión con la base de datos MongoDB y devuelve la base de datos 'TruequeLibre'.
    
    Returns:
        db: Objeto de la base de datos MongoDB.
    """
    try:
        # Intentar conectar al servidor MongoDB en la dirección y puerto especificados
        client = MongoClient('mongodb://localhost:27017/')
        # Seleccionar la base de datos 'TruequeLibre'
        db = client['TruequeLibre']
    except ConnectionError:
        # Manejar el error de conexión
        print('Error de conexión con la base de datos')
    return db
