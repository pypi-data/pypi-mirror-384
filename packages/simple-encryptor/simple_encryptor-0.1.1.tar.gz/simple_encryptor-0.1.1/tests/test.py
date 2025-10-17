from encryptor import Encryptor

encryptor = Encryptor("my_secret_key")
encrypted = encryptor.encrypt("Hello, World!")
print(encrypted)
decrypted = encryptor.decrypt(encrypted)
print(decrypted)
