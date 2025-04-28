from flask import Flask, render_template, request, redirect, url_for, session,flash
from models import db, User, Product, CartItem, Category,Order,Notification,Payment,ContactMessage, Admin
from flask_migrate import Migrate
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os,time
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli_anahtar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)



#Admin İşlemleri .................
# ResiYükleme klasörü ayarı
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Dosya türü kontrolü
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Veritabanından admini bul
        admin = Admin.query.filter_by(email=email).first()
        
        if admin and admin.check_password(password):  # Şifreyi kontrol et
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Hatalı giriş!", "danger")  # Hata mesajı göster
            return redirect(url_for('admin_login'))  # Giriş sayfasına yönlendir

    return render_template('admin/login.html')
@app.route('/admins', methods=['GET'])
def view_admins():
    admins = Admin.query.all()  # Tüm adminleri al
    return render_template('admin/admin_view.html', admins=admins)  # Şablon yolu

@app.route('/add_admin', methods=['GET', 'POST'])
def add_admin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        new_admin = Admin(email=email)
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        flash('Admin başarıyla eklendi!', 'success')
        return redirect(url_for('view_admins'))  # Adminleri görüntüleme sayfasına yönlendir
        
    return render_template('admin/admin_add.html')  # Şablon yolu
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    products_count = Product.query.count()  # Toplam ürün sayısı
    categories_count = Category.query.count()  # Toplam kategori sayısı
    orders_count = Order.query.count()  # Toplam sipariş sayısı
    messages_count = ContactMessage.query.count()  # Toplam mesaj sayısı
    completed_orders_count = Order.query.filter_by(payment_status='Completed').count()
    approved_orders_count = Order.query.filter_by(payment_status='Approved').count()
    shipped_orders_count = Order.query.filter_by(payment_status='Shipped').count()
    pending_orders_count = Order.query.filter_by(payment_status='Pending').count()  # Beklemede olan sipariş sayısı
    categories = Category.query.all()
    category_product_counts = {category.name: len(category.products) for category in categories}
    return render_template('admin/dashboard.html', 
                           products_count=products_count, 
                           categories_count=categories_count,
                           orders_count=orders_count,
                           messages_count=messages_count,
                           completed_orders_count=completed_orders_count,
                           approved_orders_count=approved_orders_count,
                           shipped_orders_count=shipped_orders_count,
                           pending_orders_count=pending_orders_count,  
                           category_product_counts=category_product_counts)  # Kategori ürün sayısını ekle
@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products) 
@app.route('/admin/upload_product_image/<int:product_id>', methods=['POST'])
@admin_required
def upload_product_image(product_id):
    # Ürünü veritabanından bul
    product = Product.query.get_or_404(product_id)

    if 'image' not in request.files:
        flash('Resim dosyası seçilmedi!', 'danger')
        return redirect(url_for('admin_products'))

    file = request.files['image']
    if file.filename == '':
        flash('Dosya adı boş olamaz!', 'danger')
        return redirect(url_for('admin_products'))

    if file and allowed_file(file.filename):
        try:
            # Klasör kontrolü
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Dosya adını güvenli hale getir ve benzersiz isim ver
            filename = secure_filename(file.filename)
            unique_filename = f"{int(time.time())}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            # Dosyayı kaydet
            file.save(file_path)

            # Veritabanında ürünün resim URL'sini güncelle
            product.image_url = f"/{file_path}"
            db.session.commit()

            flash('Ürün resmi başarıyla yüklendi!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Bir hata oluştu: {str(e)}', 'danger')
    else:
        flash('Geçersiz dosya türü! Sadece PNG, JPG, JPEG, GIF yüklenebilir.', 'danger')

    return redirect(url_for('admin_products'))
@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form['description']
            price = float(request.form['price'])
            image_url = request.form['image_url']
            category_id = int(request.form['category_id'])

            new_product = Product(
                name=name, 
                description=description, 
                price=price, 
                image_url=image_url,
                category_id=category_id
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            error_message = f"Ürün eklenirken bir hata oluştu: {str(e)}"
            app.logger.error(error_message)
            categories = Category.query.all()
            return render_template('admin/add_product.html', categories=categories, error=error_message)
    
    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)   
@app.route('/admin/delete_product/<int:product_id>')
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
    return redirect(url_for('admin_products'))
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get(product_id)
    if product is None:
        flash('Ürün bulunamadı!', 'danger')
        return redirect(url_for('admin_products'))  # Ürünler sayfasına yönlendir

    if request.method == 'POST':
        # Formdan gelen verileri güncelle
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.image_url = request.form['image_url']
        product.category_id = request.form['category_id']  # Kategori ID'sini güncelle

        try:
            db.session.commit()
            flash('Ürün başarıyla güncellendi!', 'success')
            return redirect(url_for('admin_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Güncelleme sırasında bir hata oluştu: {str(e)}', 'danger')

    categories = Category.query.all()  # Kategorileri al
    return render_template('admin/edit_product.html', product=product, categories=categories)
@app.route('/admin/categories')
@admin_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)
# Kategori ekleme route'u (admin için)
@app.route('/admin/add_category', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        name = request.form['name']
        new_category = Category(name=name)
        try:
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('admin_categories'))
        except Exception as e:
            db.session.rollback()
            # Hata mesajını daha açıklayıcı hale getiriyoruz
            error_message = f"Kategori eklenirken bir hata oluştu: {str(e)}"
            app.logger.error(error_message)
            # Oturumu kapatıp yeni bir oturum açıyoruz
            db.session.remove()
            return render_template('admin/add_category.html', error=error_message)
    return render_template('admin/add_category.html')

@app.route('/admin/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    category = Category.query.get(category_id)
    if category is None:
        flash('Kategori bulunamadı!', 'danger')
        return redirect(url_for('admin_categories'))  # Kategoriler sayfasına yönlendir

    if request.method == 'POST':
        # Formdan gelen verileri güncelle
        category.name = request.form['name']
        try:
            db.session.commit()
            flash('Kategori başarıyla güncellendi!', 'success')
            return redirect(url_for('admin_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Güncelleme sırasında bir hata oluştu: {str(e)}', 'danger')

    return render_template('admin/edit_category.html', category=category)
@app.route('/admin/orders')
def admin_orders():
    # Tüm siparişleri al
    orders = Order.query.all()
    
    # Siparişleri durumlarına göre ayır
    pending_orders = [order for order in orders if order.payment_status == 'Pending']
    approved_orders = [order for order in orders if order.payment_status == 'Approved']
    shipped_orders = [order for order in orders if order.payment_status == 'Shipped']
    completed_orders = [order for order in orders if order.payment_status == 'Completed']
    
    return render_template('admin/orders.html', 
                           pending_orders=pending_orders,
                           approved_orders=approved_orders,
                           shipped_orders=shipped_orders,
                           completed_orders=completed_orders)

@app.route('/admin/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    order = Order.query.get(order_id)
    if order is None:
        flash('Sipariş bulunamadı!', 'danger')
        return redirect(url_for('admin_orders'))

    new_status = request.form.get('payment_status')
    order.payment_status = new_status  # Yeni durumu güncelle

    try:
        db.session.commit()
        flash('Sipariş durumu başarıyla güncellendi!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Sipariş durumu güncellenirken bir hata oluştu: {str(e)}', 'danger')

    return redirect(url_for('admin_orders'))
@app.route('/admin/send_notification', methods=['GET', 'POST'])
def send_notification():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        title = request.form.get('title')
        message = request.form.get('message')

        # Yeni bildirim oluştur
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
        )

        try:
            db.session.add(notification)
            db.session.commit()
            flash('Bildirim başarıyla gönderildi!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Bildirim gönderilirken bir hata oluştu: {str(e)}', 'danger')

    users = User.query.all()  # Tüm kullanıcıları al
    return render_template('admin/send_notification.html', users=users)
@app.route('/admin/contact_messages')
def admin_contact_messages():
    unread_messages = ContactMessage.query.filter_by(is_read=False).all()  # Okunmamış mesajlar
    read_messages = ContactMessage.query.filter_by(is_read=True).all()  # Okunmuş mesajlar
    return render_template('admin/contact_messages.html', unread_messages=unread_messages, read_messages=read_messages)
@app.route('/admin/mark_as_read/<int:message_id>', methods=['POST'])
def mark_as_read(message_id):
    message = ContactMessage.query.get(message_id)
    if message is None:
        flash('Mesaj bulunamadı!', 'danger')
        return redirect(url_for('admin_contact_messages'))

    message.is_read = True  # Mesajı okundu olarak işaretle
    db.session.commit()  # Değişiklikleri kaydet
    flash('Mesaj başarıyla okundu olarak işaretlendi!', 'success')
    return redirect(url_for('admin_contact_messages'))
@app.route('/admin/mark_as_unread/<int:message_id>', methods=['POST'])
def mark_as_unread(message_id):
    message = ContactMessage.query.get(message_id)
    if message is None:
        flash('Mesaj bulunamadı!', 'danger')
        return redirect(url_for('admin_contact_messages'))

    message.is_read = False  # Mesajı okunmadı olarak işaretle
    db.session.commit()  # Değişiklikleri kaydet
    flash('Mesaj başarıyla okunmadı olarak işaretlendi!', 'success')

    return redirect(url_for('admin_contact_messages'))
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))



#Kullanıcı için İşlemler-------------------------------------



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Bu sayfayı görüntülemek için giriş yapmalısınız.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        password = request.form.get('password')
        
        # Kontroller
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kayıtlı!')
            return redirect(url_for('register'))
            
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor!')
            return redirect(url_for('register'))
        
        # Yeni kullanıcı oluştur
        new_user = User(
            username=username,
            name=name,
            surname=surname,
            email=email,
            address=address,
            city=city
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Kayıt sırasında bir hata oluştu: {str(e)}')
            return redirect(url_for('register'))
            
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Başarıyla giriş yaptınız!')
            return redirect(url_for('index'))
        else:
            flash('E-posta veya şifre hatalı!')
            
    return render_template('login.html')
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)
@app.route("/home")
def home():
    return render_template("index.html")   
@app.route("/success")
def success():
    return render_template("success.html")
@app.route('/search', methods=['GET'])
def search_products():
    query = request.args.get('query')
    products = Product.query.filter(Product.name.contains(query)).all()
    return render_template('search_results.html', products=products)
@app.route('/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)
@app.route('/category/<int:category_id>')
def category_products(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category_id).all()
    return render_template('category_products.html', category=category, products=products)
@app.route('/best_sellers')
def best_sellers():
    # En çok satan ürünleri al
    best_selling_products = Product.query.order_by(Product.sales_count.desc()).limit(10).all()  # En çok satan 10 ürünü al
    return render_template('index.html', products=best_selling_products)
@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return "Ürün bulunamadı", 404
    return render_template('product.html', product=product)
@app.route("/hakkimizda")
def aboutus():
    return render_template("aboutus.html")
@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # Yeni bir ContactMessage oluştur
        new_message = ContactMessage(
            name=name,
            email=email,
            message=message
        )

        try:
            db.session.add(new_message)
            db.session.commit()
            flash('Mesajınız başarıyla gönderildi!', 'success')  # Başarı mesajı
            return redirect(url_for('success'))  # Başarı sayfasına yönlendir
        except Exception as e:
            db.session.rollback()
            flash(f'Mesaj gönderilirken bir hata oluştu: {str(e)}', 'danger')  # Hata mesajı
    return render_template("contact.html")
@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Sepeti görüntülemek için giriş yapmalısınız!', 'danger')
        return redirect(url_for('login'))  # Giriş sayfasına yönlendir

    cart = session.get('cart', {})
    cart_items = {int(k): v for k, v in cart.items()}
    products = Product.query.all()

    # Sepetteki ürünleri cart_items tablosuna kaydet
    if cart:
        try:
            # Önce mevcut cart_items'ı temizle
            db.session.query(CartItem).filter_by(user_id=session['user_id']).delete()

            for product_id, quantity in cart_items.items():
                # Yeni bir CartItem oluştur
                cart_item = CartItem(
                    user_id=session['user_id'],  # Kullanıcı ID'si
                    product_id=product_id,        # Ürün ID'si
                    quantity=quantity             # Miktar
                )
                db.session.add(cart_item)  # CartItem'ı veritabanına ekle

            db.session.commit()  # Değişiklikleri kaydet
        except Exception as e:
            db.session.rollback()  # Hata durumunda geri al
            app.logger.error(f"Sepet ürünleri kaydedilirken hata: {e}")

    try:
        total_price = sum(
            next((p.price for p in products if p.id == pid), 0) * quantity
            for pid, quantity in cart_items.items()
        )
    except Exception as e:
        app.logger.error(f"Sepet işlenirken hata: {e}")
        return "Bir hata oluştu.", 500

    return render_template('cart.html', products=products, cart_items=cart_items, total_price=total_price)
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash('Sepete ürün eklemek için giriş yapmalısınız!', 'danger')
        return redirect(url_for('login'))  # Giriş sayfasına yönlendir

    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    # Toplam ürün sayısını hesapla
    total_items = sum(cart.values())
    session['cart_count'] = total_items
    
    session.modified = True
    flash('Ürün sepete eklendi!', 'success')
    return redirect(url_for('cart'))
@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            # Ürünü sepetten sil
            del cart[product_id_str]
            
            # Toplam ürün sayısını güncelle
            total_items = sum(cart.values())
            session['cart_count'] = total_items
            
            session.modified = True
            flash('Ürün sepetten kaldırıldı!', 'success')

            # CartItem'ı veritabanından sil
            if 'user_id' in session:
                try:
                    db.session.query(CartItem).filter_by(user_id=session['user_id'], product_id=product_id).delete()
                    db.session.commit()  # Değişiklikleri kaydet
                except Exception as e:
                    db.session.rollback()  # Hata durumunda geri al
                    flash(f'Ürün sepetten kaldırılırken bir hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('cart'))
@app.route('/clear_cart')
def clear_cart():
    # Kullanıcının sepetini temizle
    session.pop('cart', None)
    session['cart_count'] = 0

    # CartItem'ları temizle
    if 'user_id' in session:
        try:
            db.session.query(CartItem).filter_by(user_id=session['user_id']).delete()
            db.session.commit()  # Değişiklikleri kaydet
        except Exception as e:
            db.session.rollback()  # Hata durumunda geri al
            flash(f'Sepet temizlenirken bir hata oluştu: {str(e)}', 'danger')

    flash('Sepet boşaltıldı!', 'info')
    return redirect(url_for('cart'))
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        user_id = session.get('user_id')
        total_price = request.form.get('total_price')
        name = request.form.get('name')
        surname = request.form.get('surname')
        gsm_number = request.form.get('gsm_number')
        email = request.form.get('email')
        identity_number = request.form.get('identity_number')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')

        # Yeni siparişi oluştur
        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            payment_status='Completed'  # Ödeme durumu tamamlandı
        )

        try:
            db.session.add(new_order)
            db.session.commit()  # Siparişi kaydet

            # Sepetteki ürünleri al
            cart = session.get('cart', {})
            for product_id, quantity in cart.items():
                product = Product.query.get(product_id)
                if product:
                    # Satış sayısını güncelle
                    product.sales_count += quantity
                    db.session.commit()  # Satış sayısını güncelle

            # Yeni bir Payment kaydı oluştur
            new_payment = Payment(
                order_id=new_order.id,
                created_at=datetime.utcnow()  # Ödeme tarihi
            )
            db.session.add(new_payment)
            db.session.commit()  # Ödeme kaydını kaydet
            
            # Sepeti boşalt
            session.pop('cart', None)  # Sepeti temizle
            session['cart_count'] = 0  # Sepet sayısını sıfırla

            flash('Siparişiniz onaylandı! Sepetiniz boşaltıldı.', 'success')  # Başarı mesajı
            return redirect(url_for('payment_success'))  # Başarı sayfasına yönlendir
        except Exception as e:
            db.session.rollback()
            flash(f'Sipariş oluşturulurken bir hata oluştu: {str(e)}', 'danger')  # Hata mesajı

    # Sepetteki ürünlerin toplam fiyatını hesapla
    cart = session.get('cart', {})
    total_price = sum(
        next((p.price for p in Product.query.filter(Product.id == pid).all()), 0) * quantity
        for pid, quantity in cart.items()
    )

    return render_template("checkout.html", total_price=total_price)
@app.route("/payment_success")
def payment_success():
    return render_template("payment_success.html")
@app.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    notifications = Notification.query.filter_by(user_id=user_id).all()  # Kullanıcıya ait bildirimleri al
    return render_template('notifications.html', notifications=notifications)
@app.route('/order_history')
@login_required
def order_history():
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).all()  # Kullanıcının siparişlerini al
    for order in orders:
        order.items = CartItem.query.filter_by(order_id=order.id).all()  # Siparişe ait ürünleri al
        for item in order.items:
            item.product = Product.query.get(item.product_id)  # Ürün bilgilerini al
    return render_template('order_history.html', orders=orders)
@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        # E-posta veya kullanıcı adı değişikliği için kontrol
        if user.email != request.form['email'] and User.query.filter_by(email=request.form['email']).first():
            flash('Bu e-posta adresi zaten kullanılıyor!')
            return redirect(url_for('edit_profile'))
            
        if user.username != request.form['username'] and User.query.filter_by(username=request.form['username']).first():
            flash('Bu kullanıcı adı zaten kullanılıyor!')
            return redirect(url_for('edit_profile'))
        
        # Bilgileri güncelle
        user.username = request.form['username']
        user.name = request.form['name']
        user.surname = request.form['surname']
        user.email = request.form['email']
        user.address = request.form['address']
        user.city = request.form['city']
        
        try:
            db.session.commit()
            flash('Profil başarıyla güncellendi!')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('Güncelleme sırasında bir hata oluştu!')
            
    return render_template('edit_profile.html', user=user)
@app.route('/logout')
def logout():
    session.clear()
    flash('Başarıyla çıkış yaptınız!')
    return redirect(url_for('index'))
def create_tables():
    with app.app_context():
        db.create_all()
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)