# filepath: /home/pranay/GRID/Grid-Cortex-Infra/grid-cortex-client/src/grid_cortex_client/cortex_client.py
import logging
from typing import Any, Dict, Optional, Type, Union
from urllib.parse import urlparse, urlunparse

# ---------------------------------------------------------------------------
# NOTE: ModelType enum is now generated automatically in
#       grid_cortex_client/model_type.py by the code-generator
#       `python -m grid_cortex_client.tools.generate_enum`.
# ---------------------------------------------------------------------------

from .model_type import ModelType  # static enum for GRID-Rake scraping

from .client import CortexAPIError, CortexNetworkError, HTTPClient
from .models import BaseModel, registry as _model_registry
from .ws import WebSocketSession  # new import

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime safety-net: warn if the generated enum and registry diverge.
# ---------------------------------------------------------------------------


def _ensure_enum_sync() -> None:
    """Warn if `ModelType` and `BaseModel` registry are out of sync.

    Developers should regenerate the enum via
    `python -m grid_cortex_client.tools.generate_enum` whenever they add or
    rename a wrapper.  This check prevents silent mismatches in production.
    """

    enum_values = {m.value for m in ModelType}
    registered_values = set(_model_registry().keys())

    missing = registered_values - enum_values
    extra = enum_values - registered_values

    if missing:
        logger.warning(
            "Model wrappers %s are not in ModelType enum – run the generator.",
            sorted(missing),
        )

    if extra:
        logger.warning(
            "Enum contains obsolete members %s – run the generator.",
            sorted(extra),
        )


class CortexClient:
    """Client for interacting with Grid Cortex Ray Serve deployments."""

    # Live registry from BaseModel metaclass
    _MODEL_ID_TO_HANDLER_CLASS: Dict[str, Type[BaseModel]] = _model_registry()

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[
            str
        ] = None,  # This will be used to set HTTPClient's base_url
        timeout: float = 30.0,
    ):
        """
        Initializes the CortexClient.

        Args:
            api_key: API key. Uses GRID_CORTEX_API_KEY env var if None.
            base_url: Base URL of the Cortex API. If None, uses GRID_CORTEX_BASE_URL env var or HTTPClient's default.
            timeout: Default timeout for HTTP requests in seconds.
        """
        # Ensure enum stays in sync with registered models
        _ensure_enum_sync()

        # Pass base_url to HTTPClient constructor
        self.http_client = HTTPClient(
            api_key=api_key, base_url=base_url, timeout=timeout
        )

        effective_http_base_url = (
            self.http_client._client.base_url
        )  # Access the actual base_url used by httpx.Client
        logger.info(
            f"CortexClient initialized. HTTPClient target: {effective_http_base_url}"
        )

    def _http_to_ws(self, http_url: str) -> str:
        """Convert an HTTP(S) base URL to a WS(S) base URL."""
        parsed = urlparse(http_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))

    def _resolve_route(self, model: str | ModelType) -> str:
        """Return route prefix for *model* (including leading slash)."""
        model_str = model.value if isinstance(model, ModelType) else str(model)
        # Fast path: wrapper classes store explicit ROUTE_PREFIX attribute
        HandlerClass = None
        for keyword, HClass in self._MODEL_ID_TO_HANDLER_CLASS.items():
            if keyword in model_str.lower():
                HandlerClass = HClass
                break
        if HandlerClass is not None and hasattr(HandlerClass, "ROUTE_PREFIX"):
            return getattr(HandlerClass, "ROUTE_PREFIX")  # type: ignore[return-value]
        # Fallback: assume "/{model_id}"
        return f"/{model_str}"

    def _make_request(
        self,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,  # Added timeout parameter
    ) -> Dict[str, Any]:
        """Helper method to make POST requests to the /run endpoint."""
        try:
            # All model interactions go through a unified /run endpoint via POST
            # Use msgpack for binary transport
            import grid_cortex_client.utils as _u
            packed = _u.packb(payload)
            return self.http_client.post(endpoint, data=packed, timeout=timeout)
        except (CortexAPIError, CortexNetworkError) as e:
            logger.error(f"Request to {endpoint} failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during request to {endpoint}: {e}")
            raise CortexNetworkError(f"An unexpected error occurred: {e}") from e

    def _run_model(
        self,
        model: BaseModel,
        input_data: Any,
        preprocess_kwargs: Optional[Dict[str, Any]] = None,
        postprocess_kwargs: Optional[Dict[str, Any]] = None,
        visualize: bool = False,
        visualization_kwargs: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,  # Added timeout parameter
    ) -> Any:
        """
        Framework helper: execute *model* end-to-end.

        This method orchestrates the preprocessing, API request, postprocessing,
        and optional visualization steps. This is **not** part of the public API.
        External callers should use
        :py:meth:`CortexClient.run` or call ``WrapperClass.run`` directly.

        Args:
            model: An instance of a BaseModel subclass (e.g., DepthModel).
            input_data: The raw input data for the model.
            preprocess_kwargs: Additional keyword arguments for the model's preprocess method.
            postprocess_kwargs: Additional keyword arguments for the model's postprocess method.
            visualize: If True, attempts to run the model's visualize method.
            visualization_kwargs: Additional keyword arguments for the model's visualize method.
            timeout: Optional timeout in seconds for the request.

        Returns:
            The processed output from the model.

        Raises:
            CortexAPIError: If the API returns an error.
            CortexNetworkError: If a network error occurs.
            ValueError: If preprocessing or postprocessing fails.
        """
        logger.info(
            f"[internal] _run_model {model.model_id} input type: {type(input_data)}"
        )

        _preprocess_kwargs = preprocess_kwargs or {}
        _postprocess_kwargs = postprocess_kwargs or {}
        _visualization_kwargs = visualization_kwargs or {}

        try:
            # If preprocess now uses explicit keywords, forward the dict.
            try:
                payload = model.preprocess(input_data, **_preprocess_kwargs)
            except TypeError:
                payload = model.preprocess(**input_data)
            # Ensure model_id from the model instance is in the payload.
            # Only warn if 'model_id' is present in the payload but incorrect.
            # If 'model_id' is missing, run_model will add it, which is expected.
            if "model_id" in payload and payload["model_id"] != model.model_id:
                logger.warning(
                    f"Payload 'model_id' ('{payload.get('model_id')}') from preprocess "
                    f"does not match model instance's model_id ('{model.model_id}'). "
                    f"Overwriting with instance's model_id."
                )
            elif "model_id" not in payload:
                logger.debug(  # Log at debug level if model_id is simply missing from preprocess output
                    f"Payload from preprocess for model '{model.model_id}' does not contain 'model_id'. "
                    f"'{self.__class__.__name__}._run_model' will add it."
                )
            payload["model_id"] = model.model_id  # Ensure it's there and correct.

        except Exception as e:
            logger.error(
                f"Preprocessing failed for model {model.model_id}: {e}", exc_info=True
            )
            raise ValueError(f"Preprocessing error for {model.model_id}: {e}") from e

        # Construct the endpoint using the model's model_id
        # e.g., /depth-anything-v2-large/run
        # The HTTPClient will prepend its base_url (e.g., https://cortex-stage.generalrobotics.dev)
        specific_model_endpoint = f"/{model.model_id}/run"

        logger.info(
            f"Requesting model execution from: {specific_model_endpoint} for model_id: {model.model_id}"
        )

        # Pass timeout to _make_request
        api_response = self._make_request(
            specific_model_endpoint, payload=payload, timeout=timeout
        )
        logger.info(
            f"API response for model {model.model_id}: {api_response}"
        )  # Log the API response

        try:
            _postprocess_kwargs["model_name"] = model.model_id
            processed_output = model.postprocess(api_response, **_postprocess_kwargs)
        except Exception as e:
            logger.error(
                f"Postprocessing failed for model {model.model_id}: {e}", exc_info=True
            )
            # Consider re-raising a more specific error or just re-raising
            raise ValueError(f"Postprocessing error for {model.model_id}: {e}") from e

        if visualize:
            try:
                logger.info(f"Attempting visualization for model {model.model_id}.")
                # Pass original input data to visualize method if it might be needed
                model.visualize(
                    processed_output, original_input=input_data, **_visualization_kwargs
                )
            except Exception as e:
                logger.error(
                    f"Visualization failed for model {model.model_id}: {e}",
                    exc_info=True,
                )
                # Do not re-raise visualization errors, just log them.

        logger.info(f"Successfully ran model {model.model_id}.")
        return processed_output

    def available_models(self) -> list[str]:
        """Return all registered model identifiers.

        This method provides a complete list of all available models that can be
        used with the CortexClient. Essential for LLM agents to discover what
        models are available before attempting to use them.

        Returns:
            A sorted list of model identifiers (e.g., ["gsam2", "owlv2", "zoedepth"]).
            These strings can be used directly with :py:meth:`run` and :py:meth:`help`.

        Examples:
            >>> client = CortexClient()
            >>> models = client.available_models()
            >>> print(models)  # ['gsam2', 'owlv2', 'zoedepth']
            >>> client.run(models[0], image_input=img)  # Use first available model
        """
        return sorted(self._MODEL_ID_TO_HANDLER_CLASS.keys())

    # ------------------------------------------------------------------
    # Public helper: full docs for a model
    # ------------------------------------------------------------------

    def help(self, model_id: str) -> str:  # noqa: D401 simple helper
        """Return comprehensive documentation for a model.

        This method provides complete API documentation for any registered model,
        including usage examples, parameter descriptions, return types, and error
        conditions. Essential for LLM agents to understand how to interact with
        specific models before calling :py:meth:`run`.

        Args:
            model_id: Canonical model identifier (e.g., "zoedepth", "owlv2", "gsam2").

        Returns:
            A formatted string containing:
            - Class-level docstring with usage examples and parameter descriptions
            - Preprocess method documentation (input parameters and validation)
            - Postprocess method documentation (output format and data types)

        Raises:
            NotImplementedError: If model_id is not registered or not found.

        Examples:
            >>> client = CortexClient()
            >>> docs = client.help("zoedepth")
            >>> print(docs)  # Shows complete zoedepth documentation
            >>>
            >>> # For LLM agents: discover model capabilities
            >>> models = client.available_models()
            >>> for model in models:
            ...     print(f"=== {model} ===")
            ...     print(client.help(model))
        """

        handler_cls = None
        for keyword, cls in self._MODEL_ID_TO_HANDLER_CLASS.items():
            if keyword in model_id.lower():
                handler_cls = cls
                break
        if handler_cls is None:
            raise NotImplementedError(
                f"No model handler registered for model_id containing '{model_id}'."
            )

        cls_doc = (handler_cls.__doc__ or "").strip()
        pre_doc = (handler_cls.preprocess.__doc__ or "").strip()
        post_doc = (handler_cls.postprocess.__doc__ or "").strip()

        return (
            f"Model: {model_id}\n\n{cls_doc}\n\n"
            f"---\nPreprocess\n---\n{pre_doc}\n\n"
            f"---\nPostprocess\n---\n{post_doc}\n"
        )

    def run(
        self,
        model_id: Union[str, ModelType],
        timeout: Optional[float] = None,
        debug: bool = False,  # Added debug parameter
        **kwargs: Any,
    ) -> Any:
        """Execute inference using a specified model with given inputs.

        This is the primary method for running AI model inference. It automatically
        handles model discovery, input preprocessing, API communication, and output
        postprocessing. Essential for LLM agents to perform actual model inference
        after discovering available models and understanding their requirements.

        Args:
            model_id: The identifier of the model to run (use :py:meth:`available_models`
                to see all available options). Examples: "zoedepth", "owlv2", "gsam2".
            timeout: Optional timeout in seconds for the HTTP request. If None, uses
                the client's default timeout.
            debug: If True, enables detailed logging for this specific call to help
                troubleshoot issues.
            **kwargs: Model-specific input parameters. Use :py:meth:`help` to see
                required parameters for each model. Common parameters include:
                - image_input: Image data (path, URL, PIL.Image, or np.ndarray)
                - prompt: Text prompt for detection/segmentation models
                - box_threshold: Confidence threshold for detection models

        Returns:
            Model-specific output object. Exact shape/type depends on the chosen model and is fully documented in ``grid_cortex_client.model_type.ModelType``.

        Raises:
            NotImplementedError: If model_id is not found in available models.
            CortexAPIError: If the API returns an error response.
            CortexNetworkError: If network communication fails.
            ValueError: If input validation or processing fails.

        Examples:
            >>> client = CortexClient()
            >>>
            >>> # Depth estimation
            >>> depth = client.run("zoedepth", image_input=img)
            >>> print(depth.values.shape)  # (H, W)
            >>>
            >>> # Object detection
            >>> dets = client.run("owlv2", image_input=img, prompt="cat")
            >>> print(dets["scores"])  # [0.83, 0.79, ...]
            >>>
            >>> # Image segmentation
            >>> mask = client.run("gsam2", image_input=img, prompt="cat")
            >>> print(mask.values.shape)  # (H, W)

        Note:
            Before calling this method, LLM agents should:
            1. Call :py:meth:`available_models` to see what's available
            2. Call :py:meth:`help` to understand required parameters
            3. Prepare inputs according to the model's requirements
        """
        # Store original logging level
        original_level = None
        library_logger = logging.getLogger(
            "grid_cortex_client"
        )  # Get the library's root logger

        if debug:
            original_level = library_logger.getEffectiveLevel()
            library_logger.setLevel(logging.DEBUG)
            # Ensure there's a handler that outputs debug messages, e.g., to console for the debug session
            # This is tricky as libraries shouldn't add handlers.
            # For a temporary debug flag, we might add a temporary console handler if none exist
            # or rely on the application to have configured one.
            # For simplicity here, we'll assume if debug=True, the user wants to see logs
            # and might have a handler. If not, they won't see them despite level change.
            # A more robust solution might involve a context manager for logging level.
            logger.info(
                "Debug mode enabled for this run. Setting grid_cortex_client logger to DEBUG."
            )

        # Accept either raw string or ModelType member
        model_id_str = (
            model_id.value if isinstance(model_id, ModelType) else str(model_id)
        )

        logger.info(
            f"Attempting to run model '{model_id_str}' with inputs: {list(kwargs.keys())}"
        )

        HandlerClass = None
        for keyword, HClass in self._MODEL_ID_TO_HANDLER_CLASS.items():
            if keyword in model_id_str.lower():
                HandlerClass = HClass
                logger.info(
                    f"Found handler {HandlerClass.__name__} for model_id '{model_id_str}' based on keyword '{keyword}'."
                )
                break

        if HandlerClass is None:
            logger.error(
                f"No suitable model handler found for model_id: {model_id}. "
                f"Available handlers are for keywords: {list(self._MODEL_ID_TO_HANDLER_CLASS.keys())}"
            )
            raise NotImplementedError(
                f"No model handler configured for model_id containing typical keywords for known types: '{model_id_str}'. "
                f"Please ensure the model_id is correct or update the client's model handler registry."
            )

        try:
            # Instantiate the handler
            model_handler = HandlerClass(transport=self.http_client)
            # Forward kwargs and optional timeout to the internal helper.
            output = self._run_model(
                model=model_handler,
                input_data=kwargs,  # Pass all kwargs as the input_data dictionary
                timeout=timeout,  # Pass timeout here
            )
            return output

        except (
            CortexAPIError,
            CortexNetworkError,
            ValueError,
            NotImplementedError,
        ) as e:
            # Re-raise known errors
            logger.error(f"Error running model '{model_id}': {e}", exc_info=True)
            raise
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(
                f"Unexpected error running model '{model_id}': {e}", exc_info=True
            )
            raise CortexNetworkError(
                f"An unexpected error occurred while running model {model_id}: {e}"
            ) from e
        finally:
            if debug and original_level is not None:
                library_logger.setLevel(original_level)
                logger.info(
                    f"Debug mode disabled. Restored grid_cortex_client logger level to {logging.getLevelName(original_level)}."
                )

    # ------------------------------------------------------------------
    # Discovery helpers
    # ------------------------------------------------------------------

    def start_session(
        self,
        model: str | ModelType,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: float | None = 30.0,
    ) -> WebSocketSession:
        """Open a WebSocket session for a *stateful* model.

        This method establishes a WebSocket connection to stateful models that
        maintain session state across multiple frames (e.g., SAM2 video tracking).

        Parameters
        ----------
        model:
            ModelType enum member or plain string identifying the stateful model.
        headers:
            Optional extra HTTP headers (e.g. {"x-api-key": "..."}).
        timeout:
            Socket timeout in seconds.

        Returns
        -------
        WebSocketSession
            A context-managed WebSocket session for streaming data.

        Examples
        --------
        >>> client = CortexClient()
        >>> with client.start_session(ModelType.SAM2VIDEO) as ws:
        ...     ws.send_json({"frame": b64_jpeg, "points": [[585, 182]], "labels": [1]})
        ...     reply = ws.recv_json()
        ...     # Continue streaming frames...
        """
        route = self._resolve_route(model)
        base_ws = self._http_to_ws(str(self.http_client._client.base_url))
        # Convention: tracking services expose "/track" sub-path.
        url = f"{base_ws}{route}/track"
        return WebSocketSession(url, headers=headers or {}, timeout=timeout)

    def close(self):
        """Closes the underlying HTTP client."""
        self.http_client.close()
        logger.info("CortexClient closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------------------------------------------------------
    # Public: start WebSocket session
    # ------------------------------------------------------------------

    def start_session(
        self,
        model: str | ModelType,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: float | None = 30.0,
    ) -> WebSocketSession:
        """Open a WebSocket session for a *stateful* model.

        Parameters
        ----------
        model:
            ModelType enum member or plain string identifying the stateful model.
        headers:
            Optional extra HTTP headers (e.g. {"x-api-key": "..."}).
        timeout:
            Socket timeout in seconds.
        """
        route = self._resolve_route(model)
        base_ws = self._http_to_ws(str(self.http_client._client.base_url))
        # Convention: tracking services expose "/track" sub-path.
        url = f"{base_ws}{route}/track"
        return WebSocketSession(url, headers=headers or {}, timeout=timeout)
