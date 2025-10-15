from clvm_rs import Program


def generate_hash_bytes(clvm_bytes: bytes) -> bytes:
    serialized_hash = Program.from_bytes(clvm_bytes).tree_hash()
    return serialized_hash
