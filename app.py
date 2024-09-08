from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from bson.objectid import ObjectId
import database as dbase
from product import Product
import os


# Si la carpeta de carga no existe, crea la carpeta

# Conexión a la base de datos
db = dbase.dbConnection()

# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ruta principal de la aplicación
@app.route("/")
def home():
    products = db['Productos']
    productsReceived = products.find()  # Obtener todos los productos
    categorias = products.distinct("categoria")  # Obtener categorías únicas de los productos
    categoria_seleccionada = request.args.get('categoria')  # Obtener la categoría seleccionada por el usuario
    if categoria_seleccionada:
        productsReceived = products.find({'categoria': categoria_seleccionada})  # Filtrar productos por categoría
    return render_template('index.html', products=productsReceived, categorias=categorias)

# Ruta para la vista de agregar producto
@app.route("/add_product")
def add_product_view():
    return render_template('add_product.html')

# Ruta para la vista de editar producto
@app.route("/edit_product/<string:product_id>")
def edit_product_view(product_id):
    products = db['Productos']
    product = products.find_one({'_id': ObjectId(product_id)})  # Obtener el producto a editar por su ID
    return render_template('edit_product.html', product=product)

# Método POST para agregar un nuevo producto
@app.route('/products', methods=['POST'])
def addProduct():
    if request.method == 'POST':
        products = db['Productos']
        nombreProducto = request.form['nombreProducto']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        stock = request.form['stock']
        imagen_url = request.form['imagen']  # Obtener la URL de la imagen

        # Crear un nuevo objeto Producto y guardarlo en la base de datos
        new_product = {
            'nombreProducto': nombreProducto,
            'precio': precio,
            'descripcion': descripcion,
            'categoria': categoria,
            'stock': stock,
            'imagen': imagen_url  # Guardar la URL de la imagen en la base de datos
        }
        products.insert_one(new_product)

        flash('Producto agregado exitosamente.', 'success')
        return redirect(url_for('home'))
    else:
        flash('Error al agregar el producto.', 'danger')
        return redirect(url_for('add_product_view'))

# Método DELETE para eliminar un producto
@app.route('/delete/<string:product_id>', methods=['GET', 'POST'])
def delete(product_id):
    if request.method == 'POST':
        products = db['Productos']
        products.delete_one({'_id': ObjectId(product_id)})  # Eliminar el producto por su ID
        flash('Producto eliminado exitosamente.', 'success')
    else:
        flash('Error al eliminar el producto.', 'danger')
    return redirect(url_for('home'))

# Método PUT para editar un producto
@app.route('/edit/<string:product_id>', methods=['POST'])
def edit(product_id):
    products = db['Productos']
    nombreProducto = request.form['nombreProducto']
    precio = request.form['precio']
    descripcion = request.form['descripcion']
    categoria = request.form['categoria']
    stock = request.form['stock']
    imagen = request.form['imagen']  # Añadir este campo

    if nombreProducto and precio and descripcion and imagen:
        updated_product = Product(nombreProducto, precio, descripcion, categoria, stock, imagen)
        products.update_one(
            {'_id': ObjectId(product_id)},
            {'$set': updated_product.toDBCollection()}
        )
        flash('Producto actualizado exitosamente.', 'success')
    else:
        flash('Falta información para actualizar el producto.', 'danger')

    return redirect(url_for('home'))

# Ruta para agregar un producto al carrito
@app.route('/add_to_cart/<string:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = db['Productos'].find_one({'_id': ObjectId(product_id)})
    if 'cart' not in session:
        session['cart'] = []

    cantidad = int(request.form['cantidad'])

    if cantidad <= 0:
        flash('La cantidad debe ser mayor que cero.', 'danger')
        return redirect(request.referrer)

    if cantidad > int(product['stock']):
        flash('No hay suficiente stock disponible.', 'danger')
        return redirect(request.referrer)

    # Verificar si el producto ya está en el carrito
    for item in session['cart']:
        if item['product_id'] == str(product['_id']):
            item['cantidad'] += cantidad
            session.modified = True
            # Reducir el stock en la base de datos
            db['Productos'].update_one(
                {'_id': ObjectId(product_id)},
                {'$set': {'stock': int(product['stock']) - cantidad}}
            )
            flash('Producto agregado al carrito exitosamente.', 'success')
            return redirect(request.referrer)

    # Agregar la información del producto al carrito
    session['cart'].append({
        'product_id': str(product['_id']),
        'nombreProducto': product['nombreProducto'],
        'precio': product['precio'],
        'cantidad': cantidad,
        'imagen': product['imagen']  # Agregar la información de la imagen
    })

    # Reducir el stock en la base de datos
    db['Productos'].update_one(
        {'_id': ObjectId(product_id)},
        {'$set': {'stock': int(product['stock']) - cantidad}}
    )
    flash('Producto agregado al carrito exitosamente.', 'success')
    return redirect(request.referrer)

# Ruta para mostrar el carrito
@app.route('/cart')
def show_cart():
    cart = session.get('cart', [])
    total = sum(float(item['precio'].replace('$', '')) * item['cantidad'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

# Ruta para eliminar un producto del carrito
@app.route('/remove_from_cart/<string:product_id>')
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    removed_item = None
    for item in cart:
        if item['product_id'] == product_id:
            removed_item = item
            break
    if removed_item:
        session['cart'].remove(removed_item)
        # Incrementar el stock en la base de datos según la cantidad eliminada del carrito
        product = db['Productos'].find_one({'_id': ObjectId(product_id)})
        db['Productos'].update_one(
            {'_id': ObjectId(product_id)},
            {'$set': {'stock': int(product['stock']) + removed_item['cantidad']}}
        )
        flash('Producto eliminado del carrito exitosamente.', 'success')
    else:
        flash('El producto no está en el carrito.', 'danger')
    return redirect(url_for('show_cart'))

# Ruta para eliminar una cantidad específica de un producto del carrito
@app.route('/remove_quantity_from_cart/<string:product_id>', methods=['POST'])
def remove_quantity_from_cart(product_id):
    cart = session.get('cart', [])
    cantidad = int(request.form.get('cantidad', 1))
    for item in cart:
        if item['product_id'] == product_id:
            item['cantidad'] -= cantidad
            if item['cantidad'] <= 0:
                cart.remove(item)
                # Incrementar el stock en la base de datos según la cantidad eliminada del carrito
                product = db['Productos'].find_one({'_id': ObjectId(product_id)})
                db['Productos'].update_one(
                    {'_id': ObjectId(product_id)},
                    {'$set': {'stock': int(product['stock']) + cantidad}}
                )
                flash('Producto eliminado del carrito exitosamente.', 'success')
            else:
                # Incrementar el stock en la base de datos según la cantidad eliminada del carrito
                product = db['Productos'].find_one({'_id': ObjectId(product_id)})
                db['Productos'].update_one(
                    {'_id': ObjectId(product_id)},
                    {'$set': {'stock': int(product['stock']) + cantidad}}
                )
                flash('Cantidad de producto eliminada del carrito exitosamente.', 'success')
            break
    session['cart'] = cart
    return redirect(url_for('show_cart'))

# Ruta para actualizar la cantidad de un producto en el carrito
@app.route('/update_cart/<string:product_id>', methods=['POST'])
def update_cart(product_id):
    new_quantity = int(request.form['cantidad'])
    cart = session.get('cart', [])
    for item in cart:
        if item['product_id'] == product_id:
            product = db['Productos'].find_one({'_id': ObjectId(product_id)})
            if new_quantity < item['cantidad']:
                # Incrementar el stock si la nueva cantidad es menor que la cantidad actual
                stock_diff = item['cantidad'] - new_quantity
                db['Productos'].update_one(
                    {'_id': ObjectId(product_id)},
                    {'$inc': {'stock': stock_diff}}
                )
            elif new_quantity > item['cantidad']:
                # Reducir el stock si la nueva cantidad es mayor que la cantidad actual
                stock_diff = new_quantity - item['cantidad']
                db['Productos'].update_one(
                    {'_id': ObjectId(product_id)},
                    {'$inc': {'stock': -stock_diff}}
                )
            item['cantidad'] = new_quantity
            session.modified = True
            flash('Cantidad actualizada exitosamente.', 'success')
            return redirect(url_for('show_cart'))
    flash('Producto no encontrado en el carrito.', 'danger')
    return redirect(url_for('show_cart'))

# Ruta para mostrar los detalles de un producto
@app.route("/product_details/<string:product_id>")
def product_details(product_id):
    products = db['Productos']
    comments = db['Comentarios']
    product = products.find_one({'_id': ObjectId(product_id)})
    product_comments = comments.find({'product_id': product_id})
    return render_template('product_details.html', product=product, comments=product_comments)

# Ruta para agregar un comentario a un producto
@app.route('/add_comment/<string:product_id>', methods=['POST'])
def add_comment(product_id):
    comments = db['Comentarios']
    name = request.form['name']
    text = request.form['text']

    if name and text:
        new_comment = {
            'product_id': product_id,
            'name': name,
            'text': text,
        }
        comments.insert_one(new_comment)
        flash('Comentario agregado exitosamente.', 'success')
    else:
        flash('Falta información para agregar el comentario.', 'danger')

    return redirect(url_for('product_details', product_id=product_id))

# Ruta para editar un comentario
@app.route('/edit_comment/<string:comment_id>', methods=['POST'])
def edit_comment(comment_id):
    comments = db['Comentarios']
    name = request.form['name']
    text = request.form['text']

    if name and text:
        updated_comment = {
            'name': name,
            'text': text,
        }
        comments.update_one(
            {'_id': ObjectId(comment_id)},
            {'$set': updated_comment}
        )
        flash('Comentario actualizado exitosamente.', 'success')
    else:
        flash('Falta información para actualizar el comentario.', 'danger')

    product_id = request.form['product_id']
    return redirect(url_for('product_details', product_id=product_id))

# Ruta para eliminar un comentario
@app.route('/delete_comment/<string:comment_id>/<string:product_id>', methods=['POST'])
def delete_comment(comment_id, product_id):
    comments = db['Comentarios']
    comments.delete_one({'_id': ObjectId(comment_id)})
    flash('Comentario eliminado exitosamente.', 'success')
    return redirect(url_for('product_details', product_id=product_id))

# Manejador de errores 404
@app.errorhandler(404)
def notFound(error=None):
    message = {
        'message': 'No encontrado ' + request.url,
        'status': '404 Not Found'
    }
    response = jsonify(message)
    response.status_code = 404
    return response

# Punto de entrada de la aplicación
if __name__ == '__main__':
    app.run(debug=True, port=4000)
