import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # Keep modes for AES-GCM
from cryptography.hazmat.primitives.ciphers import aead # Corrected import for ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding # Corrected 'hazhat' to 'hazmat'
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization # Import for key serialization
from cryptography.exceptions import InvalidTag, UnsupportedAlgorithm
from typing import Tuple, Union

class CipherSuite:
    """
    A Python class providing common encryption functionalities for strings
    using AES-GCM, ChaCha20-Poly1305, RSA-OAEP, and data hashing.

    Note: This class handles string to bytes conversion internally (UTF-8).
    All encryption functions return bytes, and decryption functions expect bytes
    and return a string.
    """

    def __init__(self):
        """
        Initializes the CipherSuite. The backend is implicitly loaded when
        cryptographic operations are performed, preventing pickling issues.
        """
        # We explicitly don't store default_backend() here as an instance variable
        # because it causes pickling issues with Spark UDFs.
        # Instead, we'll get the backend when needed within the methods.
        pass

    def _get_backend(self):
        """Helper to get the cryptography backend."""
        return default_backend()

    def _string_to_bytes(self, text: str) -> bytes:
        """Helper to encode a string to bytes."""
        return text.encode('utf-8')

    def _bytes_to_string(self, data: bytes) -> str:
        """Helper to decode bytes to a string."""
        return data.decode('utf-8')

    # --- Data Hashing ---

    def compute_hash(self, data_string: str, algorithm: str = 'sha256') -> str:
        """
        Computes the cryptographic hash of a string.

        Args:
            data_string (str): The string to hash.
            algorithm (str): The hashing algorithm to use (e.g., 'sha256', 'sha512', 'md5').
                             Note: MD5 is considered insecure for cryptographic purposes.

        Returns:
            str: The hexadecimal representation of the hash.

        Raises:
            ValueError: If an unsupported hashing algorithm is specified.
        """
        data_bytes = self._string_to_bytes(data_string)
        hasher = None
        if algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha512':
            hasher = hashlib.sha512()
        elif algorithm == 'md5':
            # MD5 is provided for completeness but not recommended for security-critical uses
            print("Warning: MD5 is not recommended for cryptographic security.")
            hasher = hashlib.md5()
        else:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}. Choose from 'sha256', 'sha512', 'md5'.")

        hasher.update(data_bytes)
        return hasher.hexdigest()

    # --- AES-GCM (Symmetric Encryption) ---

    def generate_aes_key(self, key_size_bits: int = 256) -> bytes:
        """
        Generates a new AES symmetric key.
        AES supports 128, 192, or 256-bit keys.

        Args:
            key_size_bits (int): The desired key size in bits (128, 192, or 256).

        Returns:
            bytes: The randomly generated AES key.

        Raises:
            ValueError: If an unsupported key size is requested.
        """
        if key_size_bits not in [128, 192, 256]:
            raise ValueError("AES key size must be 128, 192, or 256 bits.")
        return os.urandom(key_size_bits // 8) # Convert bits to bytes

    def encrypt_aes(self, plaintext_string: str, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts a string using AES in GCM (Galois/Counter Mode).
        GCM provides both confidentiality and integrity (authentication).

        Args:
            plaintext_string (str): The string to encrypt.
            key (bytes): The AES key (16, 24, or 32 bytes).

        Returns:
            Tuple[bytes, bytes, bytes]: A tuple containing (nonce, ciphertext, tag).
                                       All three are required for successful decryption.
        """
        plaintext_bytes = self._string_to_bytes(plaintext_string)
        # Nonce (Initialization Vector) must be unique for each encryption with the same key
        # For GCM, 12 bytes (96 bits) is the recommended nonce length.
        nonce = os.urandom(12)

        # Get backend locally within the method
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=self._get_backend())
        encryptor = cipher.encryptor()

        # Encrypt the data
        ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()
        tag = encryptor.tag # Get the authentication tag

        return nonce, ciphertext, tag

    def decrypt_aes(self, nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> Union[str, None]:
        """
        Decrypts AES-GCM encrypted bytes back to a string.

        Args:
            nonce (bytes): The nonce used during encryption.
            ciphertext (bytes): The encrypted data.
            tag (bytes): The authentication tag.
            key (bytes): The AES key.

        Returns:
            Union[str, None]: The decrypted string, or None if decryption/authentication fails.
        """
        try:
            # Get backend locally within the method
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=self._get_backend())
            decryptor = cipher.decryptor()

            # Decrypt the data and verify the tag
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            return self._bytes_to_string(plaintext_bytes)
        except InvalidTag:
            print("AES Decryption failed: Authentication tag is invalid. Data may be tampered with or key is incorrect.")
            return None
        except Exception as e:
            print(f"AES Decryption failed: {e}")
            return None

    # --- ChaCha20-Poly1305 (Symmetric Stream Cipher with Authentication) ---

    def generate_chacha20_key(self) -> bytes:
        """
        Generates a new ChaCha20 symmetric key (32 bytes / 256 bits).

        Returns:
            bytes: The randomly generated ChaCha20 key.
        """
        return os.urandom(32)

    def encrypt_chacha20(self, plaintext_string: str, key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts a string using ChaCha20-Poly1305.
        This provides both confidentiality and integrity.

        Args:
            plaintext_string (str): The string to encrypt.
            key (bytes): The ChaCha20 key (32 bytes).

        Returns:
            Tuple[bytes, bytes, bytes]: A tuple containing (nonce, ciphertext, tag).
                                       All three are required for successful decryption.
        """
        plaintext_bytes = self._string_to_bytes(plaintext_string)
        # Nonce for ChaCha20-Poly1305 is usually 12 bytes (96 bits).
        nonce = os.urandom(12) 

        # Instantiate ChaCha20Poly1305 directly from aead module
        chacha_cipher = aead.ChaCha20Poly1305(key)
        
        # The encrypt method of ChaCha20Poly1305 returns ciphertext concatenated with the tag
        # associated_data is None for simple string encryption
        encrypted_with_tag = chacha_cipher.encrypt(nonce, plaintext_bytes, None)

        # Separate ciphertext and tag. Poly1305 tag is always 16 bytes.
        ciphertext = encrypted_with_tag[:-16]
        tag = encrypted_with_tag[-16:]

        return nonce, ciphertext, tag


    def decrypt_chacha20(self, nonce: bytes, ciphertext: bytes, tag: bytes, key: bytes) -> Union[str, None]:
        """
        Decrypts ChaCha20-Poly1305 encrypted bytes back to a string.

        Args:
            nonce (bytes): The nonce used during encryption.
            ciphertext (bytes): The encrypted data.
            tag (bytes): The authentication tag.
            key (bytes): The ChaCha20 key.

        Returns:
            Union[str, None]: The decrypted string, or None if decryption/authentication fails.
        """
        try:
            # Instantiate ChaCha20Poly1305 directly from aead module
            chacha_cipher = aead.ChaCha20Poly1305(key)

            # The decrypt method of ChaCha20Poly1305 expects ciphertext concatenated with the tag
            # associated_data is None for simple string encryption
            plaintext_bytes = chacha_cipher.decrypt(nonce, ciphertext + tag, None)
            return self._bytes_to_string(plaintext_bytes)
        except InvalidTag:
            print("ChaCha20-Poly1305 Decryption failed: Authentication tag is invalid. Data may be tampered with or key is incorrect.")
            return None
        except Exception as e:
            print(f"ChaCha20-Poly1305 Decryption failed: {e}")
            return None

    # --- RSA (Asymmetric Encryption) ---

    def generate_rsa_key_pair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """
        Generates a new RSA public/private key pair and returns them in PEM format.
        Recommended key size is 2048 bits or higher.

        Args:
            key_size (int): The desired key size in bits.

        Returns:
            Tuple[bytes, bytes]: A tuple containing (private_key_pem, public_key_pem).
                                 These are byte strings in PEM format.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537, # Common public exponent
            key_size=key_size,
            backend=self._get_backend() # Get backend locally for key generation
        )
        public_key = private_key.public_key()

        # Serialize keys to PEM format (bytes)
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            # No encryption for simplicity in this example, but recommended for production
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem, public_pem

    def _load_rsa_public_key(self, public_key_pem: bytes) -> rsa.RSAPublicKey:
        """Helper to load an RSA public key from PEM bytes."""
        return serialization.load_pem_public_key(public_key_pem, backend=self._get_backend())

    def _load_rsa_private_key(self, private_key_pem: bytes) -> rsa.RSAPrivateKey:
        """Helper to load an RSA private key from PEM bytes."""
        return serialization.load_pem_private_key(private_key_pem, password=None, backend=self._get_backend()) # No password since we exported without one

    def encrypt_rsa(self, plaintext_string: str, public_key_pem: bytes) -> bytes:
        """
        Encrypts a string using RSA with OAEP padding.
        The public key is expected in PEM byte format.

        Args:
            plaintext_string (str): The string to encrypt.
            public_key_pem (bytes): The RSA public key in PEM byte format.

        Returns:
            bytes: The RSA-encrypted ciphertext.

        Raises:
            ValueError: If the plaintext is too long for the given RSA key.
        """
        public_key = self._load_rsa_public_key(public_key_pem)
        plaintext_bytes = self._string_to_bytes(plaintext_string)
        try:
            ciphertext = public_key.encrypt(
                plaintext_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return ciphertext
        except ValueError as e:
            # Re-raise the error after printing, as this is a critical input constraint
            raise ValueError(f"RSA Encryption failed: {e}. Plaintext too long for key size or padding.")
        except Exception as e:
            print(f"RSA Encryption failed: {e}")
            raise


    def decrypt_rsa(self, ciphertext: bytes, private_key_pem: bytes) -> Union[str, None]:
        """
        Decrypts RSA-encrypted bytes back to a string using OAEP padding.
        The private key is expected in PEM byte format.

        Args:
            ciphertext (bytes): The RSA-encrypted ciphertext.
            private_key_pem (bytes): The RSA private key in PEM byte format.

        Returns:
            Union[str, None]: The decrypted string, or None if decryption fails.
        """
        private_key = self._load_rsa_private_key(private_key_pem)
        try:
            plaintext_bytes = private_key.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return self._bytes_to_string(plaintext_bytes)
        except ValueError as e:
            print(f"RSA Decryption failed (bad decryption or padding): {e}")
            return None
        except Exception as e:
            print(f"RSA Decryption failed: {e}")
            return None

# --- Example Usage with Spark DataFrames ---
if __name__ == "__main__":
    # Import Spark-related components only if in the main execution block
    # This prevents import errors if the class is used without Spark
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import udf, lit
        from pyspark.sql.types import StringType, BinaryType, StructType, StructField
        from pyspark.sql.types import ArrayType, ByteType # For potential tuple-like returns as array
    except ImportError:
        SparkSession = None
        udf = None
        lit = None
        StringType = None
        BinaryType = None
        StructType = None
        StructField = None
        ArrayType = None
        ByteType = None

    if SparkSession is None:
        print("PySpark is not installed. Skipping Spark DataFrame examples.")
        print("Please install it using: pip install pyspark")
    else:
        print("--- Initializing Spark Session ---")
        spark = SparkSession.builder \
            .appName("EncryptionDemo") \
            .getOrCreate()

        # Instantiate CipherSuite for key generation and initial setup on the driver
        # For UDFs, a new instance will be created on the worker
        driver_cipher_suite = CipherSuite()

        # --- Sample Data ---
        data = [
            (1, "123 Main St, Anytown, USA", "user1@example.com"),
            (2, "456 Oak Ave, Otherville, CA", "user2@example.com"),
            (3, "789 Pine Ln, Somewhere, TX", "user3@example.com"),
            (4, "101 Maple Rd, Nowhere, FL", "user4@example.com")
        ]
        columns = ["id", "address", "email"]
        df = spark.createDataFrame(data, columns)

        print("\n--- Original DataFrame ---")
        df.show(truncate=False)

        # --- Data Hashing Example (address column) ---
        print("\n--- Hashing 'address' column with SHA256 ---")
        # Instantiate CipherSuite within the UDF lambda to avoid pickling FFI object
        hash_udf = udf(lambda addr: CipherSuite().compute_hash(addr, 'sha256'), StringType())
        df_hashed = df.withColumn("address_hashed", hash_udf(df["address"]))
        df_hashed.show(truncate=False)

        # --- AES-GCM Encryption/Decryption (address column) ---
        print("\n--- AES-GCM Encryption/Decryption of 'address' column ---")
        # Generate key on driver and broadcast it
        aes_key = spark.sparkContext.broadcast(driver_cipher_suite.generate_aes_key())

        # Define UDF for AES encryption - CipherSuite instantiated within lambda
        aes_encrypt_udf = udf(lambda addr: CipherSuite().encrypt_aes(addr, aes_key.value),
                               StructType([
                                   StructField("nonce", BinaryType(), True),
                                   StructField("ciphertext", BinaryType(), True),
                                   StructField("tag", BinaryType(), True)
                               ]))

        df_aes_encrypted = df.withColumn("address_aes_encrypted", aes_encrypt_udf(df["address"]))
        print("DataFrame with AES Encrypted Address:")
        df_aes_encrypted.select("id", "address_aes_encrypted").show(truncate=False)

        # Define UDF for AES decryption - CipherSuite instantiated within lambda
        # Access elements by index [0] for nonce, [1] for ciphertext, [2] for tag
        aes_decrypt_udf = udf(lambda encrypted_tuple: \
                                CipherSuite().decrypt_aes(
                                    encrypted_tuple[0],  # nonce
                                    encrypted_tuple[1],  # ciphertext
                                    encrypted_tuple[2],  # tag
                                    aes_key.value
                                ), StringType())

        df_aes_decrypted = df_aes_encrypted.withColumn("address_aes_decrypted", aes_decrypt_udf(df_aes_encrypted["address_aes_encrypted"]))
        print("DataFrame with AES Decrypted Address (and original for comparison):")
        df_aes_decrypted.select("id", "address", "address_aes_decrypted").show(truncate=False)

        # Verify decryption
        df_aes_decrypted.createOrReplaceTempView("aes_data")
        match_count = spark.sql("SELECT COUNT(*) FROM aes_data WHERE address = address_aes_decrypted").collect()[0][0]
        total_count = df_aes_decrypted.count()
        print(f"AES Decryption Verification: {match_count}/{total_count} rows match original. {'SUCCESS' if match_count == total_count else 'FAILURE'}\n")

        # --- ChaCha20-Poly1305 Encryption/Decryption (address column) ---
        print("\n--- ChaCha20-Poly1305 Encryption/Decryption of 'address' column ---")
        # Generate key on driver and broadcast it
        chacha_key = spark.sparkContext.broadcast(driver_cipher_suite.generate_chacha20_key())

        # Define UDF for ChaCha20 encryption - CipherSuite instantiated within lambda
        chacha_encrypt_udf = udf(lambda addr: CipherSuite().encrypt_chacha20(addr, chacha_key.value),
                                 StructType([
                                     StructField("nonce", BinaryType(), True),
                                     StructField("ciphertext", BinaryType(), True),
                                     StructField("tag", BinaryType(), True)
                                 ]))

        df_chacha_encrypted = df.withColumn("address_chacha_encrypted", chacha_encrypt_udf(df["address"]))
        print("DataFrame with ChaCha20 Encrypted Address:")
        df_chacha_encrypted.select("id", "address_chacha_encrypted").show(truncate=False)

        # Define UDF for ChaCha20 decryption - CipherSuite instantiated within lambda
        # Access elements by index [0] for nonce, [1] for ciphertext, [2] for tag
        chacha_decrypt_udf = udf(lambda encrypted_tuple: \
                                  CipherSuite().decrypt_chacha20(
                                      encrypted_tuple[0],  # nonce
                                      encrypted_tuple[1],  # ciphertext
                                      encrypted_tuple[2],  # tag
                                      chacha_key.value
                                  ), StringType())

        df_chacha_decrypted = df_chacha_encrypted.withColumn("address_chacha_decrypted", chacha_decrypt_udf(df_chacha_encrypted["address_chacha_encrypted"]))
        print("DataFrame with ChaCha20 Decrypted Address (and original for comparison):")
        df_chacha_decrypted.select("id", "address", "address_chacha_decrypted").show(truncate=False)

        # Verify decryption
        df_chacha_decrypted.createOrReplaceTempView("chacha_data")
        match_count_chacha = spark.sql("SELECT COUNT(*) FROM chacha_data WHERE address = address_chacha_decrypted").collect()[0][0]
        print(f"ChaCha20 Decryption Verification: {match_count_chacha}/{total_count} rows match original. {'SUCCESS' if match_count_chacha == total_count else 'FAILURE'}\n")

        # --- RSA-OAEP Encryption/Decryption (address column) ---
        print("\n--- RSA-OAEP Encryption/Decryption of 'address' column ---")
        # For RSA, keys are large and should generally be managed externally.
        # Generate key pair on driver, get PEM bytes
        rsa_private_key_pem, rsa_public_key_pem = driver_cipher_suite.generate_rsa_key_pair(key_size=2048)

        # Broadcast public key PEM bytes for encryption UDF
        rsa_public_key_broadcast = spark.sparkContext.broadcast(rsa_public_key_pem)
        # Private key PEM bytes will be passed directly into the decryption UDF lambda
        # (This is less ideal for security in large clusters, but works around pickling issues)

        # Define UDF for RSA encryption - CipherSuite instantiated within lambda
        # It will load the public key from PEM bytes within the UDF
        rsa_encrypt_udf = udf(lambda addr: CipherSuite().encrypt_rsa(addr, rsa_public_key_broadcast.value), BinaryType())

        # Note: RSA has a plaintext size limit. If your address strings are too long,
        # this will raise a ValueError from `encrypt_rsa`.
        try:
            df_rsa_encrypted = df.withColumn("address_rsa_encrypted", rsa_encrypt_udf(df["address"]))
            print("DataFrame with RSA Encrypted Address:")
            df_rsa_encrypted.select("id", "address_rsa_encrypted").show(truncate=False)

            # Define UDF for RSA decryption - CipherSuite instantiated within lambda.
            # It will load the private key from PEM bytes within the UDF.
            rsa_decrypt_udf = udf(lambda encrypted_bytes: CipherSuite().decrypt_rsa(encrypted_bytes, rsa_private_key_pem), StringType())

            df_rsa_decrypted = df_rsa_encrypted.withColumn("address_rsa_decrypted", rsa_decrypt_udf(df_rsa_encrypted["address_rsa_encrypted"]))
            print("DataFrame with RSA Decrypted Address (and original for comparison):")
            df_rsa_decrypted.select("id", "address", "address_rsa_decrypted").show(truncate=False)

            # Verify decryption
            df_rsa_decrypted.createOrReplaceTempView("rsa_data")
            match_count_rsa = spark.sql("SELECT COUNT(*) FROM rsa_data WHERE address = address_rsa_decrypted").collect()[0][0]
            print(f"RSA Decryption Verification: {match_count_rsa}/{total_count} rows match original. {'SUCCESS' if match_count_rsa == total_count else 'FAILURE'}\n")

        except ValueError as e:
            print(f"RSA encryption/decryption demo skipped due to plaintext length constraint: {e}")
            print("Please try with shorter 'address' strings for the RSA example.")
        except Exception as e:
            print(f"An unexpected error occurred during RSA demo: {e}")

        spark.stop()
        print("Spark Session Stopped.")
