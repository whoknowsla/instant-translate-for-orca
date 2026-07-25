import instant_translate.secret_store as secret_store


class _FakeSchema:
    @staticmethod
    def new(name, flags, attributes):
        return (name, flags, attributes)


class _FakeSecret:
    class SchemaFlags:
        NONE = 0

    class SchemaAttributeType:
        STRING = "string"

    Schema = _FakeSchema
    COLLECTION_DEFAULT = "default"
    password = ""

    @classmethod
    def password_store_sync(cls, schema, attributes, collection, label, password, cancellable):
        cls.password = password
        return True

    @classmethod
    def password_lookup_sync(cls, schema, attributes, cancellable):
        return cls.password

    @classmethod
    def password_clear_sync(cls, schema, attributes, cancellable):
        cls.password = ""
        return True


def test_deepl_key_round_trip_uses_secret_service(monkeypatch):
    _FakeSecret.password = ""
    monkeypatch.setattr(secret_store, "Secret", _FakeSecret)
    store = secret_store.DeepLSecretStore()
    store.store("private-key")
    assert store.lookup() == "private-key"
    store.clear()
    assert store.lookup() == ""


def test_missing_secret_service_never_falls_back_to_plaintext(monkeypatch):
    monkeypatch.setattr(secret_store, "Secret", None)
    store = secret_store.DeepLSecretStore()
    assert store.lookup() == ""
    try:
        store.store("private-key")
    except secret_store.SecretStoreError:
        pass
    else:
        raise AssertionError("storing without Secret Service must fail")
