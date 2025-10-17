import hashlib
from io import BufferedReader

from labels.model.metadata import Digest


def new_digests_from_file(file_object: BufferedReader, hashes: list[str]) -> list[Digest]:
    hash_objects = [hashlib.new(hash_key, usedforsecurity=False) for hash_key in hashes]

    while chunk := file_object.read(4096):
        for hasher in hash_objects:
            hasher.update(chunk)

    if file_object.tell() == 0:
        return []

    return [
        Digest(
            algorithm=hash_name,
            value=hasher.hexdigest(),
        )
        for hash_name, hasher in zip(hashes, hash_objects, strict=False)
    ]


def artifact_id_matches_filename(artifact_id: str, filename: str, artifacts_map: set[str]) -> bool:
    if not artifact_id or not filename:
        return False

    # Ensure true is returned when filename matches the artifact ID exactly,
    # prevent random retrieval by checking if filename is in artifacts_map
    if filename in artifacts_map:
        return artifact_id == filename

    # Use fallback check with suffix and prefix if no POM properties file
    # matches the exact artifact name
    return artifact_id.startswith(filename) or filename.endswith(artifact_id)
