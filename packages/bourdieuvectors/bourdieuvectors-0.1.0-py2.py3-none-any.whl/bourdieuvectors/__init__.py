import os
import json
import requests
import hashlib
import zipfile
from platformdirs import user_cache_dir


def get_bourdieu_vector(
    event_name: str,
    event_context: str = "",
    skip_not_allowed_texts: bool = True,
    model: str = "bourdieuvectors",
    use_cached: bool = True,
):
    """
    Fetches the vector representation of a cultural event from the Bourdieu Vectors API.

    Parameters:
        event_name (str): Name of the cultural event.
        event_context (str, optional): Additional context to refine the vector. Defaults to empty string.
        use_cached (bool, optional): Whether the request should be cached to user_cache_dir("bourdieu-vectors", model)

    Returns:
        list or dict: The vector as a list if successful; an empty dict if the request fails.
    """

    cachedir = user_cache_dir("bourdieu-vectors", model)
    os.makedirs(cachedir, exist_ok=True)
    cache_path = os.path.join(
        cachedir,
        hashlib.md5(
            f"vector_{str(event_name)}-{str(event_context)}".encode()
        ).hexdigest()
        + ".json",
    )

    if use_cached and os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)["vector"]

    # API endpoint for fetching vectors
    url = f"https://api.bourdieuvectors.com/api/v1/vectors/{model}"

    # Send a POST request with event name and optional context as JSON
    response = requests.post(
        url,
        json={"cultural_event": event_name, "cultural_event_context": event_context},
    )

    # Check if the request was successful
    if response.status_code == 200:
        # Return the vector from the API response
        res = response.json()["vector"]

        if use_cached:
            with open(cache_path, "w") as f:
                json.dump({"vector": res}, f)
        return res
    else:
        exception_text = f"Failed to fetch vector for event: {event_name} (status code: {response.status_code}) - {response.text}"
        print(exception_text)

        if "not_allowed_input_" in response.text and skip_not_allowed_texts:
            if use_cached:
                with open(cache_path, "w") as f:
                    json.dump({"vector": {}}, f)
            return {}

        raise Exception(exception_text)


def save_bourdieu_vector_cache(
    target_zip_file: str,
    model: str = "bourdieuvectors",
):
    cache_dir = user_cache_dir("bourdieu-vectors", model)
    print(f"Zipping cache dir {cache_dir}")

    with zipfile.ZipFile(target_zip_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        [
            zf.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), cache_dir))
            for r, _, files in os.walk(cache_dir)
            for f in files
        ]


def load_bourdieu_vector_cache(
    source_zip_file: str,
    model: str = "bourdieuvectors",
):
    cache_dir = user_cache_dir("bourdieu-vectors", model)
    print(f"Unzipping {source_zip_file} to {cache_dir}")

    os.makedirs(cache_dir, exist_ok=True)
    with zipfile.ZipFile(source_zip_file, "r") as zf:
        zf.extractall(cache_dir)

    print("Cache restored successfully.")
    return cache_dir
