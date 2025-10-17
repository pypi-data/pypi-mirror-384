import socketio
from rsa import PublicKey, PrivateKey, encrypt, decrypt, pkcs1
from delta.run.config import Settings

_settings: Settings = None


def _get_socketio_adapter_url():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings.socketio_adapter_url


def encrypt_with_rsa(value: str, public_key: PublicKey) -> bytes:
    """
    Encrypts a string using the provided public key.
    """
    try:
        return encrypt(value.encode(), public_key)
    except pkcs1.CryptoError as e:
        raise ValueError(f"Encryption failed: {e}")


def decrypt_with_rsa(value: bytes, private_key: PrivateKey) -> str:
    """
    Decrypts a string encrypted with the corresponding private key.
    """
    try:
        decrypted_value = decrypt(value, private_key).decode("utf-8")
        return decrypted_value
    except pkcs1.CryptoError as e:
        raise ValueError(f"Decryption failed: {e}")


class DependencyResolver:
    def __init__(self):
        self.dependencies = {}
        self.visited = set()

    def add_dependency(self, component, dependency):
        self.dependencies.setdefault(component, []).append(dependency)

    def check_dependency_cycles(self, node):
        try:
            self.visited.clear()
            self.check_cycle(node, set())
            return False
        except ValueError:
            return True

    def check_cycle(self, node, visited):

        if node in visited:
            raise ValueError("Dependency cycle detected, Unable to continue.")

        visited.add(node)

        dependencies = self.dependencies.get(node, [])
        for neighbor in dependencies:
            self.check_cycle(neighbor, visited.copy())


class NotifierManager:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(NotifierManager, cls).__new__(cls)
            cls.__instance._init()
        return cls.__instance

    def _init(self):
        self._users = {}
        self._notifier = socketio.AsyncRedisManager(
            url=_get_socketio_adapter_url(),
            write_only=True,
        )

    def save_user_sid(self, username, sid):
        self._users[username] = sid

    def delete_user_sid(self, sid):
        for key, value in self._users.copy().items():
            if value == sid:
                del self._users[key]

    async def notify_user(self, username, event, data):
        user = self._users.get(username)
        if user:
            await self._notifier.emit(event, data, room=username)
