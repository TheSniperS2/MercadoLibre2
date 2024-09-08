class Product:
    def __init__(self, nombreProducto, precio, descripcion, categoria, stock, imagen):

        self.nombreProducto = nombreProducto  # Nombre del producto
        self.precio = precio  # Precio del producto
        self.descripcion = descripcion  # Descripción del producto
        self.categoria = categoria  # Categoría del producto
        self.stock = stock  # Cantidad de productos disponibles en stock
        self.imagen = imagen  # URL de la imagen del producto

    def toDBCollection(self):
        return {
            'nombreProducto': self.nombreProducto,  # Nombre del producto
            'precio': self.precio,  # Precio del producto
            'descripcion': self.descripcion,  # Descripción del producto
            'categoria': self.categoria,  # Categoría del producto
            'stock': self.stock,  # Cantidad de productos disponibles en stock
            'imagen': self.imagen  # URL de la imagen del producto
        }
