from abc import ABC, abstractmethod
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from functools import cached_property
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, Self
from maleo.crypto.key.rsa.enums import KeyType
from maleo.crypto.key.rsa.loader import with_cryptography
from maleo.types.misc import PathOrStr
from maleo.types.string import OptStr


class Key(BaseModel, ABC):
    raw: Annotated[str, Field(..., description="Raw key")]

    @abstractmethod
    def _validate_raw(self):
        """Validate raw key"""

    @model_validator(mode="after")
    def validate_raw(self) -> Self:
        self._validate_raw()
        return self

    @cached_property
    def as_rsa(self) -> RSA.RsaKey:
        """Convert raw to RSA"""
        self._validate_raw()
        passphrase = getattr(self, "password", None)
        return RSA.import_key(extern_key=self.raw, passphrase=passphrase)


class Private(Key):
    password: Annotated[OptStr, Field(None, description="Key's password")] = None

    def _validate_raw(self):
        if not RSA.import_key(
            extern_key=self.raw, passphrase=self.password
        ).has_private():
            raise ValueError(
                "Invalid key type, the private key did not have private inside it"
            )


class Public(Key):
    def _validate_raw(self):
        if RSA.import_key(extern_key=self.raw).has_private():
            raise ValueError("Invalid key type, the public key had private inside it")


class Keys(BaseModel):
    private: Annotated[Private, Field(..., description="Private key")]
    public: Annotated[Public, Field(..., description="Public key")]

    @model_validator(mode="after")
    def validate_complete_keys(self) -> Self:
        try:
            # Import private key with password
            private_key = self.private.as_rsa

            # Import public key
            public_key = self.public.as_rsa

            # Validate keys match by comparing public components
            if (
                private_key.publickey().n != public_key.n
                or private_key.publickey().e != public_key.e
            ):
                raise ValueError("Public key does not match the private key")

            # Optional: Test encrypt/decrypt functionality
            test_message = b"validation_test"
            try:
                # Encrypt with public key
                cipher = PKCS1_OAEP.new(public_key)
                encrypted = cipher.encrypt(test_message)

                # Decrypt with private key
                cipher = PKCS1_OAEP.new(private_key)
                decrypted = cipher.decrypt(encrypted)

                if decrypted != test_message:
                    raise ValueError(
                        "Keys do not work together for encryption/decryption"
                    )

            except Exception as e:
                raise ValueError(f"Keys failed encryption/decryption test: {str(e)}")

        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            raise ValueError(f"Key validation failed: {str(e)}")

        return self

    @classmethod
    def from_path(
        cls,
        private: PathOrStr,
        public: PathOrStr,
        password: OptStr = None,
    ) -> Self:
        raw_private = with_cryptography(
            KeyType.PRIVATE,
            path=private,
            password=password,
        )
        raw_public = with_cryptography(
            KeyType.PUBLIC,
            path=public,
        )
        return cls(
            private=Private(raw=raw_private, password=password),
            public=Public(raw=raw_public),
        )

    @classmethod
    def from_string(
        cls,
        private: str,
        public: str,
        password: OptStr = None,
    ) -> Self:
        return cls(
            private=Private(raw=private, password=password), public=Public(raw=public)
        )


class KeysMixin(BaseModel):
    keys: Annotated[Keys, Field(..., description="RSA Keys")]
