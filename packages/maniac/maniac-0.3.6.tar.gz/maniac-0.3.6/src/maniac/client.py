# maniac/client_sync.py
from typing import Any, Dict, Iterable, Optional, List
from .transports.httpx_sync import HttpxTransport
from .token_manager import TokenManager
from .types import (
    ChatCompletion,
    ChatCompletionCreateParams,
    ChatCompletionChunk,
    ContainerCreateParams,
    Container,
    RegisterCompletionsParams,
    RegisterCompletionsSuccess,
)

import os
import json
import io
import tarfile
import hashlib
import inspect
import importlib

try:
    import cloudpickle
except Exception as _e:
    cloudpickle = None


from dataclasses import dataclass


@dataclass
class EvalSpec:
    name: str
    requirements: List[str] | None = None
    runtime: Optional[str] = None  # e.g. "python-3.11-dspy-2.5"


# supabase edge functions expect maniac-apikey. the reason it isnt in Authorization: Bearer is that
# those edge functions also need to be able to be called from an authenticated sb client, which handles the bearer token and is not an api key
def _headers(
    api_key: Optional[str], extra: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    h = {"content-type": "application/json", "maniac-apikey": api_key or ""}
    if api_key:
        h["authorization"] = f"Bearer {api_key}"
    if extra:
        h.update(extra)
    return h


class Maniac:
    # initialize with standard arguments
    # we use TokenManager to handle the jwt token minting, so that we dont need to authenticate api keys on every request
    # we also use HttpxTransport which handles retries, reminting tokens on 401, etc
    def __init__(self, opts: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        opts = {**(opts or {}), **kwargs}
        self.apiKey = (
            opts.get("api_key")
            or opts.get("apiKey")
            or os.environ.get("MANIAC_API_KEY")
        )
        self.api_key = self.apiKey
        self.baseURL = (opts.get("baseURL") or "https://api.maniac.ai").rstrip("/")
        self.baseURLIsCustom = opts.get("baseURL") is not None
        tm = TokenManager(self.baseURL, self.apiKey or "")
        self._tx = HttpxTransport(self.baseURL, tm)

    def close(self) -> None:
        if hasattr(self._tx, "close"):
            self._tx.close()

    def __enter__(self):
        return self

    def __exit__(self, et, ev, tb):
        self.close()

    # containers
    class _Containers:
        def __init__(self, p: "Maniac"):
            self._p = p

        # create a new container
        def create(
            self, params: ContainerCreateParams | None = None, **kw
        ) -> Container:
            body = json.dumps({**(params or {}), **kw})
            res = self._p._tx.request_json(
                "/functions/v1/containers-create-client",
                {"method": "POST", "headers": _headers(self._p.apiKey), "body": body},
            )
            return res.get("data")

        # get a container by label. currently, the containers-create-client edge function handles "get or create" logic
        def get(self, label_or_params, **kw) -> Container:
            params = (
                {"label": label_or_params}
                if isinstance(label_or_params, str)
                else {**(label_or_params or {}), **kw}
            )
            body = json.dumps(params)
            res = self._p._tx.request_json(
                "/functions/v1/containers-create-client",
                {"method": "POST", "headers": _headers(self._p.apiKey), "body": body},
            )
            return res.get("data")

    # expose containers to the client
    @property
    def containers(self):
        return Maniac._Containers(self)

    # completions
    class _Completions:
        def __init__(self, p: "Maniac"):
            self._p = p

        # register a new completions dataset
        def register(
            self, input: RegisterCompletionsParams | None = None, **kw
        ) -> RegisterCompletionsSuccess[Any]:
            input = {**(input or {}), **kw}
            container = input.get("container")
            dataset = input.get("dataset")
            if not container:
                raise RuntimeError("container is required")
            if not isinstance(dataset, list) or not dataset:
                raise RuntimeError("dataset must be a non-empty array")
            inferred = dataset[0].get("messages", [])[0].get("content")
            converted = []
            for datapoint in dataset:
                additional_parameters = {
                    k: v
                    for k, v in datapoint.items()
                    if k not in ("messages", "output")
                }
                converted.append(
                    {
                        "input": datapoint.get("messages"),
                        "output": datapoint.get("output"),
                        "system_prompt": datapoint.get("messages", [])[0].get(
                            "content"
                        ),
                        "additional_parameters": additional_parameters,
                    }
                )
            payload = {
                "task": {"system_prompt": inferred, "label": container.get("label")},
                "data": converted,
            }
            raw = self._p._tx.request_json(
                "/functions/v1/direct-insert",
                {
                    "method": "POST",
                    "headers": _headers(self._p.apiKey),
                    "body": json.dumps(payload),
                },
                subdomain="api",
            )
            return {
                "status": "ok",
                "label": container.get("label"),
                "dataCount": len(converted),
                "raw": raw,
            }

        # create a new completions
        def create(
            self, params: ChatCompletionCreateParams | None = None, **kw
        ) -> ChatCompletion:
            p = {**(params or {}), **kw}

            # split out a stream request

            stream = p.get("stream")
            if stream is True:
                print("streaming")
                return self.stream(params, **kw)

            container = p.get("container")
            messages = p.get("messages") or []

            rest = {k: v for k, v in p.items() if k not in ("container", "messages")}
            init = {}
            if not container:
                body = {
                    **rest,
                    "model": rest.get("model") or "openai/gpt-4o-mini",
                    "messages": messages,
                }
                init = {
                    "body": json.dumps(body),
                    "method": "POST",
                    "headers": _headers(self._p.apiKey),
                }
            else:
                cb = container.get("inference_body", {})
                sys = cb.get("system_prompt")
                rest_cb = {k: v for k, v in cb.items() if k != "system_prompt"}
                msgs = (
                    [{"role": "system", "content": sys}] + messages if sys else messages
                )

                body = {
                    **rest,
                    **rest_cb,
                    "messages": msgs,
                    "model": f"maniac/{container.get('label')}",
                }

                init = {
                    "body": json.dumps(body),
                    "method": "POST",
                    "headers": _headers(self._p.apiKey),
                }
            print(init)
            res = self._p._tx.request_json(
                "/v1/chat/completions",
                init,
                subdomain="api" if self._p.baseURLIsCustom else "inference",
            )
            res["output_text"] = (
                (res.get("choices") or [{}])[0].get("message") or {}
            ).get("content", "")
            return res

        def stream(
            self, params: ChatCompletionCreateParams | None = None, **kw
        ) -> Iterable[ChatCompletionChunk]:
            p = {**(params or {}), **kw}
            container = p.get("container")
            messages = p.get("messages") or []
            rest = {k: v for k, v in p.items() if k not in ("container", "messages")}
            if not container:
                body = {
                    **rest,
                    "model": rest.get("model") or "openai/gpt-4o-mini",
                    "messages": messages,
                    "stream": True,
                }
            else:
                cb = container.get("inference_body", {})
                sys = cb.get("system_prompt")
                rest_cb = {k: v for k, v in cb.items() if k != "system_prompt"}
                msgs = (
                    [{"role": "system", "content": sys}] + messages if sys else messages
                )
                body = {**rest, **rest_cb, "messages": msgs, "stream": True}

            sub = "api" if self._p.baseURLIsCustom else "inference"

            for evt in self._p._tx.sse_events("/v1/chat/completions", body, sub):
                yield evt

    @property
    def chat(self):
        class _Chat:
            def __init__(self, p):
                self.completions = Maniac._Completions(p)

        return _Chat(self)

    class _Evals:
        def __init__(self, p: "Maniac"):
            self._p = p

        def register_with_storage(
            self,
            *,
            container_id: str,
            name: str,
            requirements: Any,
            runtime: str,
            artifact_bytes: bytes,
            sha256: str,
            timeout: float = 60.0,
        ) -> Dict[str, Any]:
            """
            Register an eval artifact:
            1) init -> get signed upload URL
            2) PUT artifact to signed URL
            3) finalize
            Returns the JSON from the finalize step.
            """

            # 1) init
            init_payload = {
                "container_id": container_id,
                "name": name,
                "requirements": requirements,
                "runtime": runtime,
                "sha256": sha256,
            }
            init = self._p._tx.request_json(
                "/functions/v1/evals-register-init",
                {
                    "method": "POST",
                    "headers": _headers(self._p.apiKey),
                    "body": json.dumps(init_payload),
                },
            )

            upload_url = init.get("upload_url")
            if not upload_url:
                raise RuntimeError("init did not return upload_url")

            with HttpxTransport(self._p.baseURL, self._p.tm).client(
                timeout=timeout
            ) as client:
                put_resp = client.put(
                    upload_url,
                    headers={
                        "content-type": "application/gzip",
                        "x-upsert": "true",
                    },
                    content=artifact_bytes,
                )
                put_resp.raise_for_status()

            # 3) finalize
            finalize_payload = {
                "eval_artifact_id": init.get("eval_artifact_id"),
                "size_bytes": len(artifact_bytes),
                "sha256": sha256,
            }
            finalize = self._p._tx.request_json(
                "/functions/v1/evals-register-complete",
                {
                    "method": "POST",
                    "headers": _headers(self._p.apiKey),
                    "body": json.dumps(finalize_payload),
                },
            )

            return finalize

        @staticmethod
        def _build_eval_artifact(
            eval_obj: object,
            name: str,
            requirements: List[str] | None = None,
            runtime: Optional[str] = None,
        ) -> tuple[bytes, str]:
            """
            Produce a gzipped tarball containing:
            - manifest.json (entrypoint, runtime, requirements, schema)
            - <module>.py (best-effort full module source)
            - eval_class.pkl (cloudpickled class for direct load)
            Returns: (artifact_bytes, sha256_hex)
            """
            if cloudpickle is None:
                raise RuntimeError(
                    "cloudpickle is required to register evals. Please `pip install cloudpickle`."
                )

            cls = eval_obj.__class__
            module_name = cls.__module__
            class_name = cls.__name__

            manifest = {
                "entrypoint": f"{module_name}:{class_name}",
                "name": name,
                "requirements": requirements or [],
                "runtime": runtime or "python-3.11-dspy",
                "schema": {
                    "forward_args": ["prompt", "ground_truth", "completion"],
                    "returns": ["score", "extracted", "justification"],
                    "schema_version": 1,
                },
            }

            buf = io.BytesIO()
            with tarfile.open(mode="w:gz", fileobj=buf) as tf:
                # manifest.json
                manifest_bytes = json.dumps(manifest).encode("utf-8")
                ti = tarfile.TarInfo("manifest.json")
                ti.size = len(manifest_bytes)
                tf.addfile(ti, io.BytesIO(manifest_bytes))

                # Best-effort: include the module's full source for auditability
                try:
                    mod = importlib.import_module(module_name)
                    src = inspect.getsource(mod)
                    src_path = f"{module_name.replace('.', '/')}.py"
                    src_bytes = src.encode("utf-8")
                    ti = tarfile.TarInfo(src_path)
                    ti.size = len(src_bytes)
                    tf.addfile(ti, io.BytesIO(src_bytes))
                except Exception:
                    # Non-fatal (interactive/REPL or C extensions); we still have the pickled class
                    pass

                # Always include a direct pickled class
                pickled = cloudpickle.dumps(cls)
                ti = tarfile.TarInfo("eval_class.pkl")
                ti.size = len(pickled)
                tf.addfile(ti, io.BytesIO(pickled))

            artifact_bytes = buf.getvalue()
            sha256_hex = hashlib.sha256(artifact_bytes).hexdigest()
            return artifact_bytes, sha256_hex

        def add(
            self,
            *,
            container: dict | str,
            eval_obj: object,
            name: str,
            requirements: List[str] | None = None,
            runtime: Optional[str] = None,
            timeout: float = 60.0,
        ) -> Dict[str, Any]:
            """
            High-level helper:
            - packages the Eval class
            - uploads via signed URL
            - finalizes (and enqueues validation if your EF does that)
            """
            # extract container_id
            if isinstance(container, str):
                container_id = container
            else:
                container_id = container.get("id") or container.get("container_id")
            if not container_id:
                raise RuntimeError(
                    "container (with 'id') or container_id string is required"
                )

            artifact_bytes, sha256_hex = self._build_eval_artifact(
                eval_obj, name, requirements, runtime
            )

            return self.register_with_storage(
                container_id=container_id,
                name=name,
                requirements=requirements or [],
                runtime=runtime or "python-3.11-dspy",
                artifact_bytes=artifact_bytes,
                sha256=sha256_hex,
                timeout=timeout,
            )

    @property
    def evals(self):
        return Maniac._Evals(self)
