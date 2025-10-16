import os
import hashlib

from ..client import Client

CHUNK_SIZE = 2 ** 17  # 128 KiB


def upload(client: Client, filepath: str, verbose: bool = False) -> str:
    """Uploads a file in chunks.

    Args:
        client (Client): The client used for the upload.
        filepath (str): The path to the file.
        verbose (bool, optional): Whether to print out debug information. Defaults to False.

    Raises:
        Exception: Raises an exception if any request failed or if the final file digest does not match the server.

    Returns:
        str: Returns the File ID of the uploaded file.
    """
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as file:
        content = file.read()
        byte_count = len(content)
    _print_if_verbose("Read file", verbose)

    # start the upload
    start_partial_res = _start_partial(client, filename, byte_count)
    partial_file_id = start_partial_res["payload"]["id"]
    _print_if_verbose(f"Initiated partial upload, Partial File ID: {partial_file_id}", verbose)

    # send all chunks
    _send_chunks(client, partial_file_id, content, byte_count, verbose)
    _print_if_verbose("All chunks sent", verbose)

    # send the completion request
    complete_partial_res = _complete_partial(client, partial_file_id)
    file_id = complete_partial_res["payload"]["id"]
    _print_if_verbose("Partial upload completed", verbose)

    # calculate the server and client digest and compare them
    digest_res = _digest_server(client, file_id)
    sha1_server = digest_res["payload"]["digest"]
    sha1_client = _digest_client(content)
    if sha1_server != sha1_client:
        raise Exception("The server and client digests do not match")
    _print_if_verbose("Server and client file digests match", verbose)

    return file_id


def _print_if_verbose(message: str, verbose: bool):
    if verbose:
        print(message)


def _send_chunks(client: Client, partial_file_id: str, content: bytes, byte_count: int, verbose: bool = False):
    offset = 0
    while offset + CHUNK_SIZE < byte_count:
        _append_partial(client, partial_file_id, content, offset, offset + CHUNK_SIZE)
        offset += CHUNK_SIZE
        _print_if_verbose(f"Sent {offset}/{byte_count} bytes", verbose)

    if offset < byte_count:
        _append_partial(client, partial_file_id, content, offset, byte_count)


def _start_partial(client: Client, filename: str, byte_count: int) -> dict:
    try:
        res = client.send_request(
            "uploaded_files",
            "start_partial",
            {
                "name": filename,
                "size": byte_count,
            }
        ).get_parsed_data()

        if res is None:
            raise Exception("Could not parse response data")
        return res
    except Exception as e:
        raise Exception(f"Could not start partial upload: {e}")


def _append_partial(client: Client, partial_file_id: str, content: bytes, start: int, stop: int) -> dict:
    try:
        res = client.send_request(
            "uploaded_files",
            "append_partial",
            path_params={"id": partial_file_id},
            query_params={"offset": start},
            body=str(content[start:stop].decode('utf-8')),
            raw_body=True,
        ).get_parsed_data()

        if res is None:
            raise Exception("Could not parse response data")
        return res
    except Exception as e:
        raise Exception(f"Could not send chunk: {e}")


def _complete_partial(client: Client, partial_file_id: str) -> dict:
    try:
        res = client.send_request(
            "uploaded_files",
            "complete_partial",
            path_params={"id": partial_file_id},
        ).get_parsed_data()

        if res is None:
            raise Exception("Could not parse response data")
        return res
    except Exception as e:
        raise Exception(f"Could not complete file upload: {e}")


def _digest_server(client: Client, file_id: str) -> dict:
    try:
        res = client.send_request(
            "uploaded_files",
            "digest",
            path_params={"id": file_id},
        ).get_parsed_data()

        if res is None:
            raise Exception("Could not parse response data")
        return res
    except Exception as e:
        raise Exception(f"Could not fetch uploaded file digest: {e}")


def _digest_client(content: bytes) -> str:
    try:
        hash = hashlib.sha1()
        hash.update(content)
        return hash.hexdigest()
    except Exception as e:
        raise Exception(f"Could not compute local file digest: {e}")
