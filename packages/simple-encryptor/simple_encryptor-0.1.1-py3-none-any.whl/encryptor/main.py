"""
Simple AES-256-GCM Encryptor

A lightweight Python library for encrypting and decrypting data using AES-256-GCM algorithm.
Provides a simple interface for secure data encryption with authentication.

Author: Your Name
License: MIT
Version: 1.0.0
"""

import os
import base64
from typing import Optional
from hashlib import sha256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class Encryptor:
    """
    A simple and secure encryptor using AES-256-GCM algorithm.
    
    This class provides methods to encrypt and decrypt data using the AES-256-GCM
    (Advanced Encryption Standard with Galois/Counter Mode) algorithm, which provides
    both confidentiality and authenticity.
    
    The encryption key is automatically hashed using SHA-256 to ensure it's exactly
    32 bytes long, regardless of the input key length.
    
    Attributes:
        aesgcm (AESGCM): The AES-GCM cipher instance for encryption/decryption.
    
    Example:
        >>> encryptor = Encryptor("my_secret_key")
        >>> encrypted = encryptor.encrypt("Hello, World!")
        >>> decrypted = encryptor.decrypt(encrypted)
        >>> print(decrypted)
        Hello, World!
    
    Args:
        key (str): The encryption key. Can be any length - will be hashed to 32 bytes.
        
    Raises:
        ValueError: If the key is empty or None.
        Exception: If there's an error initializing the AES-GCM cipher.
    """
    
    def __init__(self, key: str) -> None:
        """
        Initialize the Encryptor with a given key.
        
        Args:
            key (str): The encryption key. Can be any length.
            
        Raises:
            ValueError: If the key is empty or None.
            Exception: If there's an error initializing the AES-GCM cipher.
        """
        if not key:
            raise ValueError("Key cannot be empty or None")
        
        try:
            # Hash the key to ensure it's exactly 32 bytes
            hashed_key = sha256(key.encode()).digest()
            self.aesgcm = AESGCM(hashed_key)
        except Exception as e:
            raise Exception(f"Error initializing encryptor: {e}") from e

    def encrypt(self, data: str) -> Optional[str]:
        """
        Encrypt data using AES-256-GCM algorithm.
        
        This method encrypts the provided data using AES-256-GCM with a random nonce.
        The result is base64-encoded for easy storage and transmission.
        
        Args:
            data (str): The plaintext data to encrypt.
            
        Returns:
            Optional[str]: Base64-encoded encrypted data, or None if encryption fails.
            
        Raises:
            ValueError: If the data is None.
            Exception: If there's an error during encryption.
        """
        if data is None:
            raise ValueError("Data cannot be None")
            
        try:
            # Generate a random 12-byte nonce for GCM
            nonce = os.urandom(12)
            # Encrypt the data
            ciphertext = self.aesgcm.encrypt(nonce, data.encode('utf-8'), None)
            # Combine nonce and ciphertext, then base64 encode
            return base64.b64encode(nonce + ciphertext).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encrypting data: {e}") from e

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt data using AES-256-GCM algorithm.
        
        This method decrypts the provided base64-encoded encrypted data.
        
        Args:
            encrypted_data (str): Base64-encoded encrypted data to decrypt.
            
        Returns:
            Optional[str]: The decrypted plaintext data, or None if decryption fails.
            
        Raises:
            ValueError: If the encrypted_data is None or empty.
            Exception: If there's an error during decryption (e.g., invalid data, wrong key).
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be None or empty")
            
        try:
            # Decode from base64
            raw_data = base64.b64decode(encrypted_data)
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            # Decrypt the data
            decrypted_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise Exception(f"Error decrypting data: {e}") from e

if __name__ == "__main__":
    # Example usage
    encryptor = Encryptor("test_key1")
    encrypted_data = encryptor.encrypt("Hello World!")
    decrypted_data = encryptor.decrypt(encrypted_data)
    print(f"Encrypted: {encrypted_data}")
    print(f"Decrypted: {decrypted_data}")