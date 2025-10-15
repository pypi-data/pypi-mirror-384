from __future__ import annotations

import asyncio
import time
from http import HTTPStatus
from types import SimpleNamespace
from typing import Any, Optional, Union

from docudevs.api.cases.create_case import asyncio_detailed as create_case_async
from docudevs.api.cases.get_case import asyncio_detailed as get_case_async
from docudevs.api.cases.list_cases import asyncio_detailed as list_cases_async
from docudevs.api.cases.upload_case_document import asyncio_detailed as upload_case_document_async
from docudevs.api.batch.create_batch import asyncio_detailed as create_batch_async
from docudevs.api.batch.process_batch import asyncio_detailed as process_batch_async
from docudevs.api.batch.upload_batch_document import asyncio_detailed as upload_batch_document_async
from docudevs.api.configuration import (
    delete_configuration,
    get_configuration,
    list_configurations,
    save_configuration,
)
from docudevs.api.document.ocr_document import asyncio_detailed as ocr_document_async
from docudevs.api.document.process_document import (
    asyncio_detailed as process_document_async,
)
from docudevs.api.document.process_document_with_configuration import (
    asyncio_detailed as process_document_with_configuration_async,
)
from docudevs.api.document.upload_document import (
    asyncio_detailed as upload_document_async,
)
from docudevs.api.document.upload_files import asyncio_detailed as upload_files_async
from docudevs.api.job import result, status
from docudevs.api.operations.create_generative_task import (
    asyncio as create_generative_task_async,
)
from docudevs.api.operations.get_operation_result import (
    asyncio_detailed as get_operation_result_async,
)
from docudevs.api.operations.get_operation_status import (
    asyncio as get_operation_status_async,
)
from docudevs.api.operations.submit_operation import (
    asyncio as submit_operation_async,
)
from docudevs.api.template import delete_template, fill, list_templates, metadata
from docudevs.client import AuthenticatedClient
from docudevs.models import UploadCommand, UploadDocumentBody, OcrCommand, OcrType, LlmType
from docudevs.models.map_reduce_header_options import MapReduceHeaderOptions
from docudevs.models.extraction_mode import check_extraction_mode
from docudevs.models.generative_task_request import GenerativeTaskRequest
from docudevs.models.template_fill_request import TemplateFillRequest
from docudevs.models.upload_files_body import UploadFilesBody
from docudevs.types import File, UNSET, Unset


class DocuDevsClient:
    def __init__(self, api_url: str = "https://api.docudevs.ai", token: Optional[str] = None):
        # Create the openapi-python-client AuthenticatedClient
        if token is None:
            raise ValueError("token is required")
        self._client = AuthenticatedClient(base_url=api_url, token=token)

    async def list_configurations(self):
        """List all named configurations."""
        return await list_configurations.asyncio_detailed(client=self._client)

    # --------------------------- LLM Providers Management ---------------------------
    # Raw endpoint wrappers because openapi generator doesn't yet expose these controller routes.
    # Endpoint base: /llm

    async def list_llm_providers(self):
        """List LLM providers for the organization."""
        return await self._client._async_client.get("/llm/providers")  # type: ignore[attr-defined]

    async def create_llm_provider(self, name: str, type_: str, base_url: str | None = None, api_key: str | None = None, model: str | None = None, description: str | None = None):
        """Create an LLM provider.

        Args:
            name: Provider display name
            type_: Backend type (e.g. AZURE_OPENAI, OPENAI, ANTHROPIC)
            base_url: Optional base URL override
            api_key: Optional default key (may be managed separately)
            model: Optional default model id
            description: Optional description
        """
        payload = {"name": name, "type": type_}
        if base_url is not None:
            payload["baseUrl"] = base_url
        if api_key is not None:
            payload["apiKey"] = api_key
        if model is not None:
            payload["model"] = model
        if description is not None:
            payload["description"] = description
        return await self._client._async_client.post("/llm/providers", json=payload)  # type: ignore[attr-defined]

    async def get_llm_provider(self, provider_id: int):
        """Get a single LLM provider."""
        return await self._client._async_client.get(f"/llm/providers/{provider_id}")  # type: ignore[attr-defined]

    async def update_llm_provider(self, provider_id: int, *, name: str | None = None, base_url: str | None = None, model: str | None = None, description: str | None = None):
        """Patch update LLM provider fields (only sends provided keys)."""
        payload: dict[str, str] = {}
        if name is not None:
            payload["name"] = name
        if base_url is not None:
            payload["baseUrl"] = base_url
        if model is not None:
            payload["model"] = model
        if description is not None:
            payload["description"] = description
        return await self._client._async_client.patch(f"/llm/providers/{provider_id}", json=payload)  # type: ignore[attr-defined]

    async def delete_llm_provider(self, provider_id: int):
        """Soft delete an LLM provider."""
        return await self._client._async_client.delete(f"/llm/providers/{provider_id}")  # type: ignore[attr-defined]

    async def list_llm_keys(self):
        """List LLM key bindings."""
        return await self._client._async_client.get("/llm/keys")  # type: ignore[attr-defined]

    async def update_llm_key_binding(self, key: str, provider_id: int | None):
        """Assign/unassign a provider to a logical LLM key binding.

        Pass provider_id=None to clear binding (if API allows null)."""
        payload = {"providerId": provider_id}
        return await self._client._async_client.put(f"/llm/keys/{key}", json=payload)  # type: ignore[attr-defined]

    # --------------------------- OCR Providers Management ---------------------------
    # Endpoint base: /ocr (parallel structure to LLM)

    async def list_ocr_providers(self):
        """List OCR providers for the organization."""
        return await self._client._async_client.get("/ocr/providers")  # type: ignore[attr-defined]

    async def create_ocr_provider(self, name: str, endpoint: str | None = None, api_key: str | None = None, model: str | None = None, description: str | None = None):
        """Create an OCR provider (Azure Document Intelligence configuration).

        Args:
            name: Provider display name
            endpoint: Azure endpoint base URL
            api_key: Optional API key (if not using managed identity)
            model: Optional model ID (e.g., prebuilt-document)
            description: Optional description
        """
        payload = {"name": name}
        if endpoint is not None:
            payload["endpoint"] = endpoint
        if api_key is not None:
            payload["apiKey"] = api_key
        if model is not None:
            payload["model"] = model
        if description is not None:
            payload["description"] = description
        return await self._client._async_client.post("/ocr/providers", json=payload)  # type: ignore[attr-defined]

    async def get_ocr_provider(self, provider_id: int):
        """Get an OCR provider by id."""
        return await self._client._async_client.get(f"/ocr/providers/{provider_id}")  # type: ignore[attr-defined]

    async def update_ocr_provider(self, provider_id: int, *, name: str | None = None, endpoint: str | None = None, model: str | None = None, description: str | None = None):
        """Patch update OCR provider fields."""
        payload: dict[str, str] = {}
        if name is not None:
            payload["name"] = name
        if endpoint is not None:
            payload["endpoint"] = endpoint
        if model is not None:
            payload["model"] = model
        if description is not None:
            payload["description"] = description
        return await self._client._async_client.patch(f"/ocr/providers/{provider_id}", json=payload)  # type: ignore[attr-defined]

    async def delete_ocr_provider(self, provider_id: int):
        """Soft delete an OCR provider."""
        return await self._client._async_client.delete(f"/ocr/providers/{provider_id}")  # type: ignore[attr-defined]

    async def list_ocr_keys(self):
        """List OCR key bindings."""
        return await self._client._async_client.get("/ocr/keys")  # type: ignore[attr-defined]

    async def update_ocr_key_binding(self, key: str, provider_id: int | None):
        """Assign/unassign a provider to an OCR key binding."""
        payload = {"providerId": provider_id}
        return await self._client._async_client.put(f"/ocr/keys/{key}", json=payload)  # type: ignore[attr-defined]

    async def get_configuration(self, name: str):
        """Get a named configuration."""
        return await get_configuration.asyncio_detailed(client=self._client, name=name)

    async def save_configuration(self, name: str, body: UploadCommand):
        """Save a named configuration."""
        return await save_configuration.asyncio_detailed(client=self._client, name=name, body=body)

    async def delete_configuration(self, name: str):
        """Delete a named configuration."""
        return await delete_configuration.asyncio_detailed(client=self._client, name=name)

    async def upload_files(self, body: UploadFilesBody):
        """Upload multiple files."""
        return await upload_files_async(client=self._client, body=body)

    async def upload_document(self, body: UploadDocumentBody):
        """Upload a single document."""
        return await upload_document_async(client=self._client, body=body)

    async def list_templates(self):
        """List document templates."""
        return await list_templates.asyncio_detailed(client=self._client)

    async def metadata(self, template_id: str):
        """Get metadata for a template."""
        return await metadata.asyncio_detailed(client=self._client, name=template_id)

    async def delete_template(self, template_id: str):
        """Delete template by ID."""
        return await delete_template.asyncio_detailed(client=self._client, name=template_id)

    async def ocr_document(self, guid: str, body: OcrCommand, ocr_format: Optional[str] = None):
        """Process document with OCR-only mode."""
        return await ocr_document_async(client=self._client, guid=guid, body=body, format_=ocr_format)

    async def process_document(self, guid: str, body: UploadCommand):
        """Process a document."""
        return await process_document_async(client=self._client, guid=guid, body=body)

    # --------------------------- Map-Reduce Convenience ---------------------------
    def build_upload_command_map_reduce(
        self,
        *,
        prompt: str = "",
        schema: str = "",
        mime_type: str,
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
        pages_per_chunk: int = 1,
        overlap_pages: int = 0,
        dedup_key: Optional[str] = None,
        header_options: Optional[dict[str, Any]] = None,
        header_schema: Optional[str] = None,
        header_prompt: Optional[str] = None,
    ) -> UploadCommand:
        """Build an UploadCommand with map-reduce (chunked) parameters.

        Validation rules (mirrors server):
        - pages_per_chunk >= 1
        - overlap_pages >= 0
        - overlap_pages < pages_per_chunk
        - if overlap_pages > 0 then dedup_key must be provided and non-empty
        """
        if pages_per_chunk < 1:
            raise ValueError("pages_per_chunk must be >= 1")
        if overlap_pages < 0:
            raise ValueError("overlap_pages must be >= 0")
        if overlap_pages >= pages_per_chunk:
            raise ValueError("overlap_pages must be < pages_per_chunk")
        if overlap_pages > 0 and not dedup_key:
            raise ValueError("dedup_key is required when overlap_pages > 0")

        header_model: Union[MapReduceHeaderOptions, Unset]
        header_model = UNSET
        if header_options is not None or header_schema is not None or header_prompt is not None:
            opts: dict[str, Any] = dict(header_options or {})
            enabled = bool(opts.get("enabled", True))
            raw_page_limit = opts.get("page_limit")
            if enabled:
                effective_page_limit = raw_page_limit if raw_page_limit is not None else 1
                if effective_page_limit < 1:
                    raise ValueError("header.page_limit must be >= 1 when header is enabled")
            else:
                effective_page_limit = raw_page_limit
                if effective_page_limit is not None and effective_page_limit < 1:
                    raise ValueError("header.page_limit must be >= 1 when provided")

            if header_schema is not None:
                opts["schema"] = header_schema
            if header_prompt is not None:
                opts["prompt"] = header_prompt

            def _value_or_unset(key: str) -> Union[Any, Unset]:
                if key not in opts:
                    return UNSET
                value = opts[key]
                if value is None:
                    return UNSET
                return value

            header_model = MapReduceHeaderOptions(
                enabled=enabled,
                page_limit=effective_page_limit if effective_page_limit is not None else UNSET,
                include_in_rows=_value_or_unset("include_in_rows"),
                schema=_value_or_unset("schema"),
                schema_file_name=_value_or_unset("schema_file_name"),
                prompt=_value_or_unset("prompt"),
                prompt_file_name=_value_or_unset("prompt_file_name"),
                row_prompt_augmentation=_value_or_unset("row_prompt_augmentation"),
            )

        if extraction_mode is not None:
            extraction_mode_value = check_extraction_mode(extraction_mode)
        else:
            extraction_mode_value = UNSET

        # Build base command
        cmd = UploadCommand(
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            ocr=ocr if ocr is not None else UNSET,
            barcodes=barcodes if barcodes is not None else UNSET,
            llm=llm if llm is not None else UNSET,
            extraction_mode=extraction_mode_value,
            describe_figures=describe_figures if describe_figures is not None else UNSET,
        )
        # Populate typed MapReduceCommand so it serializes via to_dict -> mapReduce
        from docudevs.models.map_reduce_command import MapReduceCommand
        mr_model = MapReduceCommand(
            enabled=True,
            pages_per_chunk=pages_per_chunk,
            overlap_pages=overlap_pages,
            dedup_key=dedup_key if dedup_key else UNSET,
        )
        if not isinstance(header_model, Unset):
            mr_model.header = header_model
        cmd.map_reduce = mr_model
        # Add camelCase alias attribute for backward/compat tests expecting getattr(cmd, "mapReduce")
        mr_dict = mr_model.to_dict()
        try:
            setattr(cmd, "mapReduce", mr_dict)
        except Exception:
            # Likely slots preventing dynamic attribute; store in additional_properties and patch class with property
            try:
                cmd.additional_properties["mapReduce"] = mr_dict
                if not hasattr(UploadCommand, "mapReduce"):
                    def _get_mapReduce(self):  # type: ignore
                        return self.additional_properties.get("mapReduce")
                    def _set_mapReduce(self, value):  # type: ignore
                        self.additional_properties["mapReduce"] = value
                    UploadCommand.mapReduce = property(_get_mapReduce, _set_mapReduce)  # type: ignore[attr-defined]
            except Exception:
                pass
        return cmd

    async def process_document_map_reduce(
        self,
        guid: str,
        *,
        prompt: str = "",
        schema: str = "",
        mime_type: str,
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
        pages_per_chunk: int = 1,
        overlap_pages: int = 0,
        dedup_key: Optional[str] = None,
        header_options: Optional[dict[str, Any]] = None,
        header_schema: Optional[str] = None,
        header_prompt: Optional[str] = None,
    ):
        """Process an already-uploaded document using map-reduce chunking parameters."""

        def _fallback_header_payload() -> dict[str, Any] | None:
            if (
                header_options is None
                and header_schema is None
                and header_prompt is None
            ):
                return None
            opts: dict[str, Any] = dict(header_options or {})
            enabled = bool(opts.get("enabled", True))
            raw_page_limit = opts.get("page_limit")
            effective_page_limit = (
                raw_page_limit if raw_page_limit is not None else 1
                if enabled
                else raw_page_limit
            )
            header_payload: dict[str, Any] = {"enabled": enabled}
            if effective_page_limit is not None:
                header_payload["pageLimit"] = effective_page_limit
            if "include_in_rows" in opts and opts.get("include_in_rows") is not None:
                header_payload["includeInRows"] = opts["include_in_rows"]
            if header_schema is not None:
                header_payload["schema"] = header_schema
            if "schema_file_name" in opts and opts.get("schema_file_name"):
                header_payload["schemaFileName"] = opts["schema_file_name"]
            if header_prompt is not None:
                header_payload["prompt"] = header_prompt
            if "prompt_file_name" in opts and opts.get("prompt_file_name"):
                header_payload["promptFileName"] = opts["prompt_file_name"]
            if (
                "row_prompt_augmentation" in opts
                and opts.get("row_prompt_augmentation")
            ):
                header_payload["rowPromptAugmentation"] = opts["row_prompt_augmentation"]
            return header_payload

        cmd = self.build_upload_command_map_reduce(
            prompt=prompt,
            schema=schema,
            mime_type=mime_type,
            ocr=ocr,
            barcodes=barcodes,
            llm=llm,
            extraction_mode=extraction_mode,
            describe_figures=describe_figures,
            pages_per_chunk=pages_per_chunk,
            overlap_pages=overlap_pages,
            dedup_key=dedup_key,
            header_options=header_options,
            header_schema=header_schema,
            header_prompt=header_prompt,
        )

        # Ensure JSON body includes mapReduce block even if model ignored attribute
        if not getattr(cmd, "mapReduce", None):  # ensure alias present
            try:
                mr_model = getattr(cmd, "map_reduce", None)
                if mr_model and mr_model is not UNSET:
                    try:
                        setattr(cmd, "mapReduce", mr_model.to_dict())
                    except Exception:
                        # fallback to additional_properties mechanism
                        try:
                            mr_dict = mr_model.to_dict()
                            cmd.additional_properties["mapReduce"] = mr_dict
                            if not hasattr(UploadCommand, "mapReduce"):
                                def _get_mapReduce(self):  # type: ignore
                                    return self.additional_properties.get("mapReduce")
                                def _set_mapReduce(self, value):  # type: ignore
                                    self.additional_properties["mapReduce"] = value
                                UploadCommand.mapReduce = property(_get_mapReduce, _set_mapReduce)  # type: ignore[attr-defined]
                        except Exception:
                            pass
                else:
                    base_map_reduce = {
                        "enabled": True,
                        "pagesPerChunk": pages_per_chunk,
                        "overlapPages": overlap_pages,
                        **({"dedupKey": dedup_key} if dedup_key else {}),
                    }
                    header_dict = _fallback_header_payload()
                    if header_dict:
                        base_map_reduce["header"] = header_dict
                    setattr(cmd, "mapReduce", base_map_reduce)
            except Exception:
                header_dict = _fallback_header_payload()
                base_map_reduce = {
                    "enabled": True,
                    "pagesPerChunk": pages_per_chunk,
                    "overlapPages": overlap_pages,
                    **({"dedupKey": dedup_key} if dedup_key else {}),
                }
                if header_dict:
                    base_map_reduce["header"] = header_dict
                setattr(cmd, "mapReduce", base_map_reduce)
        return await process_document_async(client=self._client, guid=guid, body=cmd)

    async def submit_and_process_document_map_reduce(
        self,
        document,
        document_mime_type: str,
        *,
        prompt: str = "",
        schema: str = "",
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
        pages_per_chunk: int = 1,
        overlap_pages: int = 0,
        dedup_key: Optional[str] = None,
        header_options: Optional[dict[str, Any]] = None,
        header_schema: Optional[str] = None,
        header_prompt: Optional[str] = None,
    ) -> str:
        """Upload a document then process it using map-reduce chunking.

        Returns the job guid.
        """
        if not document_mime_type:
            raise ValueError("document_mime_type is required")
        if document is None:
            raise ValueError("document is required")

        file_obj = File(payload=document, file_name="omitted", mime_type=document_mime_type)
        upload_body = UploadDocumentBody(document=file_obj)
        upload_response = await self.upload_document(body=upload_body)
        if upload_response.status_code != HTTPStatus.OK:
            content_str = upload_response.content.decode("utf-8", errors="replace")
            raise Exception(f"Error uploading document: {content_str}")
        parsed_upload = getattr(upload_response, "parsed", None)
        guid = getattr(parsed_upload, "guid", None) if parsed_upload else None
        if not guid:
            raise Exception("Upload response missing guid")

        process_resp = await self.process_document_map_reduce(
            guid=guid,
            prompt=prompt,
            schema=schema,
            mime_type=document_mime_type,
            ocr=ocr,
            barcodes=barcodes,
            llm=llm,
            extraction_mode=extraction_mode,
            describe_figures=describe_figures,
            pages_per_chunk=pages_per_chunk,
            overlap_pages=overlap_pages,
            dedup_key=dedup_key,
            header_options=header_options,
            header_schema=header_schema,
            header_prompt=header_prompt,
        )
        if process_resp.status_code != HTTPStatus.OK:
            content_str = process_resp.content.decode("utf-8", errors="replace")
            raise Exception(f"Error processing document: {content_str}")
        return guid

    # --------------------------- Batch Processing Convenience ---------------------------
    async def create_batch(self, max_concurrency: int | None = None) -> str:
        """Create a new batch processing job using generated client.

        Note: The generated CreateBatchBody requires orgId; server will infer from auth so we send a placeholder.
        """
        from docudevs.models.create_batch_body import CreateBatchBody
        body = CreateBatchBody(org_id="placeholder", max_concurrency=max_concurrency if max_concurrency is not None else UNSET)
        resp = await create_batch_async(client=self._client, body=body)
        if resp.status_code != HTTPStatus.OK or not resp.parsed:
            raise Exception(f"Error creating batch job: {getattr(resp,'content', b'').decode('utf-8','ignore') if hasattr(resp,'content') else resp}")
        guid = getattr(resp.parsed, "job_guid", None) or getattr(resp.parsed, "jobGuid", None)
        if not guid:
            raise Exception("Batch creation response missing jobGuid")
        return guid

    async def upload_batch_document(
        self,
        batch_guid: str,
        document,
        mime_type: str,
        file_name: str | None = None,
    ) -> dict:
        """Upload a single document into an existing batch job using generated client."""
        from docudevs.models.upload_batch_document_body import UploadBatchDocumentBody
        # Normalize to bytes
        if isinstance(document, str) and not hasattr(document, "read"):
            file_name = file_name or document.split("/")[-1]
            with open(document, "rb") as f:
                payload = f.read()
        else:
            if hasattr(document, "read"):
                payload = document.read()  # type: ignore
            else:
                payload = document
            file_name = file_name or "document"
        file_obj = File(payload=payload, file_name=file_name, mime_type=mime_type)
        body = UploadBatchDocumentBody(document=file_obj, org_id="placeholder")
        resp = await upload_batch_document_async(guid=batch_guid, client=self._client, body=body)
        if resp.status_code != HTTPStatus.OK or not resp.parsed:
            raise Exception(f"Error uploading batch document: status={resp.status_code}")
        # Return dict representation
        parsed = resp.parsed
        return {
            "jobGuid": getattr(parsed, "job_guid", None) or getattr(parsed, "jobGuid", None),
            "index": getattr(parsed, "index", None),
            "totalDocuments": getattr(parsed, "total_documents", None) or getattr(parsed, "totalDocuments", None),
        }

    async def process_batch(
        self,
        batch_guid: str,
        *,
        prompt: str = "",
        schema: str = "",
        mime_type: str,
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
    ) -> str:
        """Finalize and start processing a batch using generated client."""
        if not mime_type:
            raise ValueError("mime_type is required for batch processing")
        from docudevs.models.process_batch_body import ProcessBatchBody
        from docudevs.models.map_reduce_command import MapReduceCommand  # potential future reuse
        # Normalize optional enums
        ocr_enum = ocr if ocr is not None else UNSET
        llm_enum = llm if llm is not None else UNSET
        if extraction_mode is not None:
            try:
                from docudevs.models.extraction_mode import check_extraction_mode
                extraction_mode_value = check_extraction_mode(extraction_mode)
            except Exception:
                raise ValueError("Invalid extraction_mode value; expected one of 'OCR','SIMPLE','STEPS'")
        else:
            extraction_mode_value = UNSET
        body = ProcessBatchBody(
            org_id="placeholder",
            prompt=prompt if prompt else UNSET,
            schema=schema if schema else UNSET,
            mime_type=mime_type,
            ocr=ocr_enum,
            llm=llm_enum,
            extraction_mode=extraction_mode_value,
            barcodes=barcodes if barcodes is not None else UNSET,
            describe_figures=describe_figures if describe_figures is not None else UNSET,
        )
        resp = await process_batch_async(guid=batch_guid, client=self._client, body=body)
        if resp.status_code != HTTPStatus.OK or not resp.parsed:
            raise Exception(f"Error initiating batch processing: status={resp.status_code}")
        return batch_guid

    async def schedule_batch(self, batch_guid: str) -> dict:
        """Call the scheduling endpoint for a batch (concurrency-aware scheduling)."""
        resp = await self._client._async_client.post(  # type: ignore[attr-defined]
            f"/document/batch/{batch_guid}/schedule", json={}
        )
        if resp.status_code != HTTPStatus.OK:
            raise Exception(f"Error scheduling batch: {resp.text}")
        return resp.json() if hasattr(resp, "json") else {}

    async def submit_and_process_batch(
        self,
        documents,
        document_mime_type: str,
        *,
        prompt: str = "",
        schema: str = "",
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
        max_concurrency: int | None = None,
    ) -> str:
        """High-level convenience to create a batch, upload multiple documents, and start processing.

        Args:
            documents: Iterable of paths, bytes, or file-like objects
            document_mime_type: Shared MIME type for all documents
            prompt, schema, ocr, barcodes, llm, extraction_mode, describe_figures: As per single doc helpers
            max_concurrency: Optional concurrency parameter when creating batch

        Returns:
            The batch job GUID.
        """
        guid = await self.create_batch(max_concurrency=max_concurrency)
        for doc in documents:
            await self.upload_batch_document(guid, doc, document_mime_type)
        await self.process_batch(
            guid,
            prompt=prompt,
            schema=schema,
            mime_type=document_mime_type,
            ocr=ocr,
            barcodes=barcodes,
            llm=llm,
            extraction_mode=extraction_mode,
            describe_figures=describe_figures,
        )
        return guid

    async def process_document_with_configuration(self, guid: str, configuration: str):
        """Process a document using a named configuration.

        Args:
            guid: Upload GUID
            configuration: Name of the saved configuration to apply
        """
        if not configuration:
            raise ValueError("configuration name is required")
        return await process_document_with_configuration_async(
            client=self._client,
            guid=guid,
            configuration_name=configuration,
        )

    async def result(self, uuid: str):
        """Get job result."""
        return await result.asyncio_detailed(client=self._client, uuid=uuid)

    # --------------------------- New Result Format Helpers ---------------------------
    async def result_json(self, uuid: str):
        """Get job result explicitly as JSON via /job/result/{uuid}/json.

        Falls back to legacy endpoint if the server responds 404 (older server) or 415 (non-JSON / markdown result).
        Returns:
            - If JSON: parsed JSON object (dict/list/etc) when possible, else raw text.
            - If fallback due to markdown/plain: raw text string.
        Raises:
            Exception on unexpected non-2xx responses other than 404/415 fallback cases.
        """
        resp = await self._client._async_client.get(f"/job/result/{uuid}/json")  # type: ignore[attr-defined]
        if resp.status_code == 200:
            text = resp.text
            try:
                import json
                return json.loads(text)
            except Exception:
                return text
        if resp.status_code in (404, 415):  # fallback path (legacy or markdown/plain text)
            legacy = await self.result(uuid)
            if legacy.status_code == 200:
                # Try parse JSON then fallback to text
                try:
                    import json
                    return json.loads(legacy.content.decode("utf-8", errors="replace"))
                except Exception:
                    return legacy.content.decode("utf-8", errors="replace")
            raise Exception(f"Legacy result fetch failed: {legacy.status_code}")
        raise Exception(f"Unexpected status fetching JSON result: {resp.status_code} - {getattr(resp,'text','')}")

    async def result_csv(self, uuid: str) -> str:
        """Get job result as CSV via /job/result/{uuid}/csv.

        Returns CSV text. If the server replies 415 (non-JSON content) a descriptive Exception is raised.
        """
        resp = await self._client._async_client.get(f"/job/result/{uuid}/csv")  # type: ignore[attr-defined]
        if resp.status_code == 200:
            return resp.text
        if resp.status_code == 404:
            raise FileNotFoundError(f"Result not found for job {uuid}")
        if resp.status_code == 415:
            raise Exception("Result is not JSON (markdown/plain); CSV export unsupported.")
        raise Exception(f"Unexpected status fetching CSV result: {resp.status_code} - {getattr(resp,'text','')}")

    async def result_excel(self, uuid: str, save_to: str | None = None) -> bytes:
        """Get job result as Excel (XLSX) via /job/result/{uuid}/excel.

        Args:
            uuid: Job GUID
            save_to: Optional path; if provided writes the binary content to this file.

        Returns:
            Raw XLSX bytes.
        Raises:
            - FileNotFoundError if 404
            - Exception with message for 415 (non-JSON) or other non-2xx codes.
        """
        resp = await self._client._async_client.get(f"/job/result/{uuid}/excel")  # type: ignore[attr-defined]
        if resp.status_code == 200:
            data = resp.content
            if save_to:
                with open(save_to, "wb") as f:  # pragma: no cover (filesystem side effect)
                    f.write(data)
            return data
        if resp.status_code == 404:
            raise FileNotFoundError(f"Result not found for job {uuid}")
        if resp.status_code == 415:
            raise Exception("Result is not JSON (markdown/plain); Excel export unsupported.")
        raise Exception(f"Unexpected status fetching Excel result: {resp.status_code}")

    async def status(self, guid: str):
        """Get job status."""
        return await status.asyncio_detailed(client=self._client, guid=guid)

    async def fill(self, name: str, body: TemplateFillRequest):
        """Fill a template."""
        return await fill.asyncio_detailed(client=self._client, name=name, body=body)

    async def fill_with_retry(
        self,
        name: str,
        body: TemplateFillRequest,
        timeout: float = 30.0,
        poll_interval: float = 1.0,
        retry_on_statuses: tuple[int, ...] = (404, 500),
        initial_delay: float = 0.5,
    ):
        """Fill a template, retrying transient readiness errors.

        Some template fills (especially immediately after upload) can race with
        blob availability or background job initialization causing 404/500.
        This helper retries those transient failures until success or timeout.

        Args:
            name: Template name
            body: TemplateFillRequest with substitution fields
            timeout: Max seconds to keep retrying (default 30)
            poll_interval: Delay between retries (default 1.0s)
            retry_on_statuses: HTTP status codes considered transient
            initial_delay: Optional sleep before first attempt

        Returns:
            The successful Response object (status_code 200) or the last Response encountered.
        """
        start = time.time()
        if initial_delay > 0:
            await asyncio.sleep(initial_delay)
        last_response = None
        while True:
            last_response = await self.fill(name=name, body=body)
            if last_response.status_code == 200:
                return last_response
            # Stop if non-retryable status
            if last_response.status_code not in retry_on_statuses:
                return last_response
            if time.time() - start >= timeout:
                return last_response
            await asyncio.sleep(poll_interval)

    # Cases management methods
    async def create_case(self, body):
        """Create a new case."""
        return await create_case_async(client=self._client, body=body)

    async def list_cases(self):
        """List all cases."""
        return await list_cases_async(client=self._client)

    async def get_case(self, case_id: Union[int, str]):
        """Get a specific case. Accepts int or str (will coerce)."""
        try:
            cid = int(case_id)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            raise ValueError("case_id must be convertible to int")
        return await get_case_async(client=self._client, case_id=cid)

    async def upload_case_document(self, case_id: Union[int, str], body):
        """Upload a document to a case."""
        try:
            cid = int(case_id)
        except (TypeError, ValueError):  # pragma: no cover
            raise ValueError("case_id must be convertible to int")
        return await upload_case_document_async(client=self._client, case_id=cid, body=body)

    async def submit_operation(self, job_guid: str, operation_type: str):
        """Submit an operation for a completed job."""
        from docudevs.models.submit_operation_request import SubmitOperationRequest
        body = SubmitOperationRequest(job_guid=job_guid, type_=operation_type)
        return await submit_operation_async(client=self._client, body=body)

    async def submit_operation_with_parameters(self, job_guid: str, operation_type: str, llm_type: Optional[str] = None, custom_parameters: Optional[dict] = None):
        """Submit an operation for a completed job with parameters.
        
        Args:
            job_guid: The job GUID to submit operation for
            operation_type: The type of operation to submit (e.g., "error-analysis")
            llm_type: Optional LLM type to use ("DEFAULT", "MINI", "PREMIUM")
            custom_parameters: Optional dict of custom parameters
            
        Returns:
            The operation submission response
        """
        from docudevs.models.submit_operation_request import SubmitOperationRequest
        from docudevs.models.operation_parameters import OperationParameters
        from docudevs.models.operation_parameters_custom_parameters_type_1 import OperationParametersCustomParametersType1

        parameters = UNSET
        if llm_type is not None or custom_parameters is not None:
            custom_params_model = UNSET
            if custom_parameters:
                custom_params_model = OperationParametersCustomParametersType1()
                for key, value in custom_parameters.items():
                    custom_params_model[key] = str(value)

            llm_type_value = UNSET
            if llm_type:
                from docudevs.models.llm_type import check_llm_type
                llm_type_value = check_llm_type(llm_type)

            parameters = OperationParameters(
                llm_type=llm_type_value,
                custom_parameters=custom_params_model,
            )

        body = SubmitOperationRequest(job_guid=job_guid, type_=operation_type, parameters=parameters)
        return await submit_operation_async(client=self._client, body=body)

    async def get_operation_status(self, job_guid: str):
        """Get status of all operations for a job."""
        return await get_operation_status_async(client=self._client, job_guid=job_guid)

    async def get_operation_result(self, job_guid: str, operation_type: str):
        """Get result of a specific operation."""
        response = await get_operation_result_async(client=self._client, job_guid=job_guid, operation_type=operation_type)
        if response.status_code == HTTPStatus.OK:
            # Parse JSON response manually since the generated parser doesn't handle it
            import json
            response_data = json.loads(response.content.decode('utf-8'))
            return SimpleNamespace(**response_data)
        return response

    async def submit_and_wait_for_operation(self, job_guid: str, operation_type: str, timeout: int = 120, poll_interval: float = 2.0):
        """Submit an operation and wait for result.
        
        Args:
            job_guid: The job GUID to submit operation for
            operation_type: The type of operation to submit (e.g., "error-analysis")
            timeout: Maximum time to wait in seconds (default: 120)
            poll_interval: Time between status checks in seconds (default: 2.0)
            
        Returns:
            The operation result once complete
            
        Raises:
            TimeoutError: If the operation doesn't complete within the timeout
            Exception: If the operation fails or errors occur
        """
        # Submit the operation
        submit_response = await self.submit_operation(job_guid=job_guid, operation_type=operation_type)
        if not submit_response:
            raise Exception(f"Error submitting {operation_type} operation: No response received")
        
        # Get the operation job GUID from the response  
        operation_job_guid = submit_response.job_guid
        
        if not operation_job_guid:
            raise Exception(f"No operation job GUID returned from submit {operation_type} operation")
        
        # Wait for the operation to complete using operation status polling
        import asyncio
        import time
        start_time = time.time()
        operation_completed = False
        
        while time.time() - start_time < timeout:
            status_response = await self.get_operation_status(job_guid=job_guid)
            if status_response and hasattr(status_response, 'operations'):
                target_ops = [op for op in status_response.operations if op.operation_type == operation_type]
                
                if target_ops and target_ops[0].status == "COMPLETED":
                    operation_completed = True
                    break
                elif target_ops and target_ops[0].status == "ERROR":
                    raise Exception(f"Operation failed with error: {target_ops[0].error}")
            
            await asyncio.sleep(poll_interval)
        
        if not operation_completed:
            raise TimeoutError(f"Operation {operation_type} did not complete within {timeout} seconds")
        
        # Get the result
        result_response = await self.get_operation_result(job_guid=job_guid, operation_type=operation_type)
        # The get_operation_result method returns either a SimpleNamespace (success) or Response (failure)
        # If it's a SimpleNamespace, it's already parsed; if it's a Response, check status code
        if hasattr(result_response, 'status_code'):
            if result_response.status_code != HTTPStatus.OK:
                content_str = result_response.content.decode('utf-8', errors='replace')
                raise Exception(f"Error getting operation result: {content_str}")
            # Parse the response manually
            import json
            response_data = json.loads(result_response.content.decode('utf-8'))
            return SimpleNamespace(**response_data)
        else:
            # Already parsed as SimpleNamespace
            return result_response

    async def submit_and_wait_for_error_analysis(self, job_guid: str, timeout: int = 120, poll_interval: float = 2.0):
        """Submit error analysis operation and wait for result.
        
        Args:
            job_guid: The job GUID to analyze errors for
            timeout: Maximum time to wait in seconds (default: 120)
            poll_interval: Time between status checks in seconds (default: 2.0)
            
        Returns:
            The error analysis result once complete
            
        Raises:
            TimeoutError: If the operation doesn't complete within the timeout
            Exception: If the operation fails or errors occur
        """
        return await self.submit_and_wait_for_operation(job_guid=job_guid, operation_type="error-analysis", timeout=timeout, poll_interval=poll_interval)

    async def create_generative_task(self, parent_job_id: str, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        """Create a generative task for a completed job.
        
        Args:
            parent_job_id: The parent job GUID to create generative task for
            prompt: The prompt to send to the AI model
            model: Optional model to use
            temperature: Optional temperature parameter (0.0 to 1.0)
            max_tokens: Optional maximum tokens to generate
            
        Returns:
            The generative task creation response
        """
    # Build request model with UNSET for omitted optional values
        
        body = GenerativeTaskRequest(
            prompt=prompt,
            model=model if model is not None else UNSET,
            temperature=temperature if temperature is not None else UNSET,
            max_tokens=max_tokens if max_tokens is not None else UNSET,
        )
        return await create_generative_task_async(client=self._client, parent_job_id=parent_job_id, body=body)

    async def submit_and_wait_for_generative_task(self, parent_job_id: str, prompt: str, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None, timeout: int = 120, poll_interval: float = 2.0):
        """Create a generative task and wait for result.
        
        Args:
            parent_job_id: The parent job GUID to create generative task for
            prompt: The prompt to send to the AI model
            model: Optional model to use
            temperature: Optional temperature parameter (0.0 to 1.0)
            max_tokens: Optional maximum tokens to generate
            timeout: Maximum time to wait in seconds (default: 120)
            poll_interval: Time between status checks in seconds (default: 2.0)
            
        Returns:
            The generative task result once complete
            
        Raises:
            TimeoutError: If the operation doesn't complete within the timeout
            Exception: If the operation fails or errors occur
        """
        # Create the generative task
        response = await self.create_generative_task(
            parent_job_id=parent_job_id,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        if not response:
            raise Exception("Error creating generative task: No response received")
        
        # Get the generative task job GUID from the response  
        task_job_guid = response.job_guid
        
        if not task_job_guid:
            raise Exception("No job GUID returned from create generative task")
        
        # Wait for the generative task to complete using operation status polling
        start_time = time.time()
        task_completed = False
        
        while time.time() - start_time < timeout:
            status_response = await self.get_operation_status(job_guid=parent_job_id)
            if status_response and hasattr(status_response, 'operations'):
                generative_ops = [op for op in status_response.operations if op.operation_type == "generative-task"]
                
                if generative_ops and generative_ops[0].status == "COMPLETED":
                    task_completed = True
                    break
                elif generative_ops and generative_ops[0].status == "ERROR":
                    raise Exception(f"Generative task failed with error: {generative_ops[0].error}")
            
            await asyncio.sleep(poll_interval)
        
        if not task_completed:
            raise TimeoutError(f"Generative task did not complete within {timeout} seconds")
        
        # Get the result
        result_response = await self.get_operation_result(job_guid=parent_job_id, operation_type="generative-task")
        # The get_operation_result method returns either a SimpleNamespace (success) or Response (failure)
        # If it's a SimpleNamespace, it's already parsed; if it's a Response, check status code
        if hasattr(result_response, 'status_code'):
            if result_response.status_code != HTTPStatus.OK:
                content_str = result_response.content.decode('utf-8', errors='replace')
                raise Exception(f"Error getting generative task result: {content_str}")
            # Parse the response manually
            import json
            response_data = json.loads(result_response.content.decode('utf-8'))
            return SimpleNamespace(**response_data)
        else:
            # Already parsed as SimpleNamespace
            return result_response

    async def submit_and_wait_for_operation_with_parameters(self, job_guid: str, operation_type: str, llm_type: Optional[str] = None, custom_parameters: Optional[dict] = None, timeout: int = 120, poll_interval: float = 2.0):
        """Submit an operation with parameters and wait for result.
        
        Args:
            job_guid: The job GUID to submit operation for
            operation_type: The type of operation to submit (e.g., "error-analysis")
            llm_type: Optional LLM type to use ("DEFAULT", "MINI", "PREMIUM")
            custom_parameters: Optional dict of custom parameters
            timeout: Maximum time to wait in seconds (default: 120)
            poll_interval: Time between status checks in seconds (default: 2.0)
            
        Returns:
            The operation result once complete
            
        Raises:
            TimeoutError: If the operation doesn't complete within the timeout
            Exception: If the operation fails or errors occur
        """
        # Submit the operation with parameters
        submit_response = await self.submit_operation_with_parameters(
            job_guid=job_guid, 
            operation_type=operation_type, 
            llm_type=llm_type, 
            custom_parameters=custom_parameters
        )
        if not submit_response:
            raise Exception(f"Error submitting {operation_type} operation: No response received")
        
        # Get the operation job GUID from the response  
        operation_job_guid = submit_response.job_guid
        
        if not operation_job_guid:
            raise Exception(f"No operation job GUID returned from submit {operation_type} operation")
        
        # Wait for the operation to complete using operation status polling
        start_time = time.time()
        operation_completed = False
        
        while time.time() - start_time < timeout:
            status_response = await self.get_operation_status(job_guid=job_guid)
            if status_response and hasattr(status_response, 'operations'):
                target_ops = [op for op in status_response.operations if op.operation_type == operation_type]
                
                if target_ops and target_ops[0].status == "COMPLETED":
                    operation_completed = True
                    break
                elif target_ops and target_ops[0].status == "ERROR":
                    raise Exception(f"Operation failed with error: {target_ops[0].error}")
            
            await asyncio.sleep(poll_interval)
        
        if not operation_completed:
            raise TimeoutError(f"Operation {operation_type} did not complete within {timeout} seconds")
        
        # Get the result
        result_response = await self.get_operation_result(job_guid=job_guid, operation_type=operation_type)
        # The get_operation_result method returns either a SimpleNamespace (success) or Response (failure)
        # If it's a SimpleNamespace, it's already parsed; if it's a Response, check status code
        if hasattr(result_response, 'status_code'):
            if result_response.status_code != HTTPStatus.OK:
                content_str = result_response.content.decode('utf-8', errors='replace')
                raise Exception(f"Error getting operation result: {content_str}")
            # Parse the response manually
            import json
            response_data = json.loads(result_response.content.decode('utf-8'))
            return SimpleNamespace(**response_data)
        else:
            # Already parsed as SimpleNamespace
            return result_response

    async def submit_and_process_document(
        self,
        document,
        document_mime_type: str,
        prompt: str = "",
        schema: str = "",
        ocr: Optional[OcrType] = None,
        barcodes: Optional[bool] = None,
        llm: Optional[LlmType] = None,
        extraction_mode: Optional[str] = None,
        describe_figures: Optional[bool] = None,
    ) -> str:
        """Convenience helper: upload then process a document.

        Returns the job guid for later status/result polling.
        """
        if not document_mime_type:
            raise ValueError("document_mime_type is required")
        if document is None:
            raise ValueError("document is required")

        file_obj = File(payload=document, file_name="omitted", mime_type=document_mime_type)
        upload_body = UploadDocumentBody(document=file_obj)
        upload_response = await self.upload_document(body=upload_body)
        if upload_response.status_code != HTTPStatus.OK:
            content_str = upload_response.content.decode("utf-8", errors="replace")
            raise Exception(f"Error uploading document: {content_str}")
        parsed_upload = getattr(upload_response, "parsed", None)
        guid = getattr(parsed_upload, "guid", None) if parsed_upload else None
        if not guid:
            raise Exception("Upload response missing guid")

        # Normalize extraction_mode
        if extraction_mode is not None:
            try:
                from docudevs.models.extraction_mode import check_extraction_mode
                extraction_mode_value = check_extraction_mode(extraction_mode)
            except Exception:
                raise ValueError("Invalid extraction_mode value; expected one of 'OCR','SIMPLE','STEPS'")
        else:
            extraction_mode_value = UNSET

        process_body = UploadCommand(
            prompt=prompt,
            schema=schema,
            mime_type=document_mime_type,
            ocr=ocr if ocr is not None else UNSET,
            barcodes=barcodes if barcodes is not None else UNSET,
            llm=llm if llm is not None else UNSET,
            extraction_mode=extraction_mode_value,
            describe_figures=describe_figures if describe_figures is not None else UNSET,
        )
        process_resp = await self.process_document(guid=guid, body=process_body)
        if process_resp.status_code != HTTPStatus.OK:
            content_str = process_resp.content.decode("utf-8", errors="replace")
            raise Exception(f"Error processing document: {content_str}")
        return guid

    async def submit_and_process_document_with_configuration(
        self,
        document,
        document_mime_type: str,
        configuration_name: str,
    ) -> str:
        if not document_mime_type:
            raise ValueError("document_mime_type is required")
        if document is None:
            raise ValueError("document is required")
        file_obj = File(payload=document, file_name="omitted", mime_type=document_mime_type)
        upload_body = UploadDocumentBody(document=file_obj)
        upload_response = await self.upload_document(body=upload_body)
        if upload_response.status_code != HTTPStatus.OK:
            content_str = upload_response.content.decode("utf-8", errors="replace")
            raise Exception(f"Error uploading document: {content_str}")
        parsed_upload = getattr(upload_response, "parsed", None)
        guid = getattr(parsed_upload, "guid", None) if parsed_upload else None
        if not guid:
            raise Exception("Upload response missing guid")
        process_resp = await self.process_document_with_configuration(guid=guid, configuration=configuration_name)
        if process_resp.status_code != HTTPStatus.OK:
            content_str = process_resp.content.decode("utf-8", errors="replace")
            raise Exception(f"Error processing document: {content_str}")
        return guid

    async def submit_and_ocr_document(
        self,
        document,
        document_mime_type: str,
        ocr: str = "DEFAULT",
        ocr_format: str = "markdown",
        describe_figures: Optional[bool] = None,
    ) -> str:
        if not document_mime_type:
            raise ValueError("document_mime_type is required")
        if document is None:
            raise ValueError("document is required")
        # Allow LOW OCR to ignore describe_figures per server semantics; for others, plain+describe_figures is invalid
        ocr_upper = (ocr or "DEFAULT").upper()
        if describe_figures is True and ocr_format == "plain" and ocr_upper != "LOW":
            raise ValueError("describe_figures=True is not supported with ocr_format='plain'")
        file_obj = File(payload=document, file_name="omitted", mime_type=document_mime_type)
        upload_body = UploadDocumentBody(document=file_obj)
        upload_response = await self.upload_document(body=upload_body)
        if upload_response.status_code != HTTPStatus.OK:
            content_str = upload_response.content.decode("utf-8", errors="replace")
            raise Exception(f"Error uploading document: {content_str}")
        parsed_upload = getattr(upload_response, "parsed", None)
        guid = getattr(parsed_upload, "guid", None) if parsed_upload else None
        if not guid:
            raise Exception("Upload response missing guid")
        from docudevs.models.ocr_type import check_ocr_type
        ocr_enum = check_ocr_type(ocr) if ocr is not None else UNSET
        ocr_body = OcrCommand(
            ocr=ocr_enum,
            ocr_format=ocr_format,
            mime_type=document_mime_type,
            # For LOW OCR, ignore describe_figures by not sending it; server also ignores it defensively
            describe_figures=(
                UNSET if ocr_upper == "LOW" else (describe_figures if describe_figures is not None else UNSET)
            ),
        )
        ocr_resp = await self.ocr_document(guid=guid, body=ocr_body, ocr_format=ocr_format)
        if ocr_resp.status_code != HTTPStatus.OK:
            content_str = ocr_resp.content.decode("utf-8", errors="replace")
            raise Exception(f"Error processing document with OCR: {content_str}")
        return guid

    async def wait_until_ready(self, guid: str, timeout: int = 180, poll_interval: float = 5.0, result_format: str | None = None, excel_save_to: str | None = None):
        """Wait for a job to complete (by polling status) and then return the result.

        Args:
            guid: The job GUID to wait for
            timeout: Maximum time to wait in seconds (default: 180)
            poll_interval: Time between status checks in seconds (default: 5.0)
            result_format: Optional explicit format: 'json', 'csv', 'excel'. None => legacy behavior (auto / raw).
            excel_save_to: Optional path when requesting 'excel' to persist the file.

        Returns:
            Parsed JSON (dict/list) for json format, CSV string for csv, bytes for excel, or legacy parsed/simple namespace for None.

        Raises:
            TimeoutError: If the job doesn't complete within the timeout
            Exception: If the job fails or errors occur or unsupported format for content
        """
        start_time = time.time()

        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {guid} did not complete within {timeout} seconds")

            # Poll status endpoint to know if job finished
            status_response = await self.status(guid=guid)
            if status_response.status_code == HTTPStatus.OK:
                job = status_response.parsed
                if job is not None:
                    job_status = getattr(job, "status", None)
                    if job_status == "COMPLETED":
                        break
                    if job_status == "ERROR":
                        job_error = getattr(job, "error", None)
                        raise Exception(f"Job {guid} failed: {job_error}")
                # Not completed yet, continue polling
            elif status_response.status_code != HTTPStatus.NOT_FOUND:
                content_str = status_response.content.decode("utf-8", errors="replace")
                raise Exception(
                    f"Error getting status: {content_str} (status code: {status_response.status_code})"
                )

            await asyncio.sleep(poll_interval)

        # When completed, fetch in desired format
        if result_format == "json":
            return await self.result_json(guid)
        if result_format == "csv":
            return await self.result_csv(guid)
        if result_format == "excel":
            return await self.result_excel(guid, save_to=excel_save_to)

        # Legacy fetch
        result_response = await self.result(uuid=guid)
        if result_response.status_code == HTTPStatus.OK:
            parsed = result_response.parsed
            if parsed is not None:
                return parsed
            # Fallback for plain-text / OCR responses
            text = result_response.content.decode("utf-8", errors="replace")
            try:
                import json
                json_parsed = json.loads(text)
                return SimpleNamespace(result=text, parsed=json_parsed)
            except Exception:
                return SimpleNamespace(result=text)

        content_str = result_response.content.decode('utf-8', errors='replace')
        raise Exception(
            f"Error getting result after completion: {content_str} (status code: {result_response.status_code})"
        )


# Convenience facade: synchronous client wrapping sync_detailed and blocking calls


__all__ = [
    "DocuDevsClient",
    "UploadDocumentBody",
    "UploadCommand",
    "File",
    "UploadFilesBody",
    "TemplateFillRequest",
    "GenerativeTaskRequest",
    # ... add other models if needed ...
]
