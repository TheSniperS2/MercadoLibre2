class Comment:
    def __init__(self, name, text):
        self.name = name  # Nombre del autor del comentario
        self.text = text  # Contenido del comentario

    def toDBCollection(self):
        return {
            'name': self.name,  # Nombre del autor del comentario
            'text': self.text  # Contenido del comentario
        }
