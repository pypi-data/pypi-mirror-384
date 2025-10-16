import pickle


class SerializerException(Exception):
    pass


class Serializer:
    @staticmethod
    def dump(data):
        return pickle.dumps(data).hex()

    @staticmethod
    def load(s):
        try:
            return pickle.loads(bytes.fromhex(s))
        except (EOFError, ValueError):
            raise SerializerException(f"Load failed: {s}")


serializer = Serializer()
