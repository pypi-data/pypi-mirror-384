import runpy

from google.genai import Client


def with_opik(client: Client) -> Client:
    from opik.integrations.genai import track_genai
    runpy.run_path('../opik.py')
    return track_genai(client)
