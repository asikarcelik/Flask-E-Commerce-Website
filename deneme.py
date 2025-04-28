from werkzeug.security import generate_password_hash

# Şifrenizi girin
raw_password = "adminasikar"  # Yeni adminin şifresi

# Hashli şifre oluşturma
hashed_password = generate_password_hash(raw_password)

print("Hashli Şifre:", hashed_password)
