import requests
from typing import Any, Dict


def register_eval_artifact(
    base: str,
    jwt: str,
    container_id: str,
    name: str,
    requirements: Any,
    runtime: str,
    artifact_bytes: bytes,
    sha256: str,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Registers an eval artifact by:
      1) init: getting a signed upload URL
      2) uploading the artifact via PUT to Storage
      3) finalizing the registration
    Returns the JSON from the finalize step.
    """

    # 1) init
    init_resp = requests.post(
        f"{base}/functions/v1/evals-register-init",
        headers={
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        },
        json={
            "container_id": container_id,
            "name": name,
            "requirements": requirements,
            "runtime": runtime,
            "sha256": sha256,
        },
        timeout=timeout,
    )
    init_resp.raise_for_status()
    init = init_resp.json()

    # 2) direct upload to Storage (signed URL)
    put_resp = requests.put(
        init["upload_url"],
        headers={
            "content-type": "application/gzip",
            "x-upsert": "true",
        },
        data=artifact_bytes,
        timeout=timeout,
    )
    put_resp.raise_for_status()

    # 3) finalize
    finalize_resp = requests.post(
        f"{base}/functions/v1/evals-register-complete",
        headers={
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        },
        json={
            "eval_artifact_id": init["eval_artifact_id"],
            "size_bytes": len(artifact_bytes),
            "sha256": sha256,
        },
        timeout=timeout,
    )
    finalize_resp.raise_for_status()
    return finalize_resp.json()
