def test_encrypt_decrypt(crypto_manager):
    plaintext = "Hello, World!"
    ciphertext = crypto_manager.encrypt(plaintext)
    decrypted_text = crypto_manager.decrypt(ciphertext)
    assert plaintext == decrypted_text
