import json
from typing import Union

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService
from w.services.technical.json_service import JsonService
from w.services.technical.models.request_response import RequestResponse
from w.services.technical.models.yousign import (
    YousignSignatureRequestCreation,
    YousignProcedureStart,
    YousignProcedure,
)
from w.services.technical.request_service import RequestService


class YousignService(AbstractService):
    """
    Service that allows to interact with the APIs of Yousign, a secure electronic
    document signature system.
    Compatible with Yousign version 3 (and so not compatible with older versions).
    """

    _api_url = None
    _headers = None
    _request_session = None

    @classmethod
    def init(cls, api_url: str, api_key: str):
        cls._api_url = api_url
        cls._headers = {
            "accept": "application/json",
            "authorization": f"Bearer {api_key}",
        }

    @classmethod
    def clear(cls):
        super().clear()
        cls._api_url = None
        cls._headers = None
        cls._request_session = None

    @classmethod
    def _is_initialized(cls):
        return cls._api_url and cls._headers

    @classmethod
    def _manage_call_to_yousign_post_api(
        cls,
        url: str,
        payload: Union[dict, str],
        error_msg: str,
        **request_options,
    ):
        if not cls._request_session:
            cls._request_session = RequestService.init_session(
                cls._api_url, headers=cls._headers
            )
        if "Content-Type" in request_options:
            request_options["headers"] = {
                **cls._request_session.request.headers,
                "Content-Type": request_options.pop("Content-Type"),
            }
        response = RequestService.post(
            url,
            data=payload,
            session=cls._request_session,
            **request_options,
        )
        return cls._manage_yousign_api_response(error_msg, response)

    @classmethod
    def _manage_call_to_yousign_get_api(cls, url: str, error_msg: str):
        if not cls._request_session:
            cls._request_session = RequestService.init_session(
                cls._api_url, headers=cls._headers
            )
        response = RequestService.get(url, session=cls._request_session)
        return cls._manage_yousign_api_response(error_msg, response)

    @classmethod
    def _manage_yousign_api_response(cls, error_msg: str, response: RequestResponse):
        if not response.success:
            cls._raise_yousign_api_failure_exception(response, error_msg)
        return response.content

    @classmethod
    def _raise_yousign_api_failure_exception(cls, response, msg):
        """
        raise RuntimeError for yousign api failure
        """
        error = json.loads(response.orig_content)
        if "detail" in error:
            error = error["detail"]
        else:
            error = "no detail"
        raise RuntimeError(
            f"{msg} ({response.status_code} - {response.content}) : {error}"
        )

    @classmethod
    def start_procedure(cls, data: YousignProcedureStart) -> YousignProcedure:
        """
        Start a Yousign procedure by performing the 3 required steps to have an active
        signature procedure :
        - 1) Upload the provided document
        - 2) Create a signature request linked to this document for the provided signer
        - 3) Activate this signature request

        Args:
            data(YousignProcedureStart): custom part of the data required to perform
            the 3 steps of the procedure start

        Returns:
            YousignProcedure

        Raises:
            RuntimeError if service not initialized or call to Yousign API fails
        """
        cls._check_is_initialized()
        cls._request_session = RequestService.init_session(
            cls._api_url, headers=cls._headers
        )
        uploaded_document = cls.upload_document(data.filename)
        signature_request_creation_data = YousignSignatureRequestCreation(
            name=data.signature_request_name,
            documents=[uploaded_document["id"]],
            signers=[data.signer],
            signature_field=data.signature_field,
            mention_field=data.mention_field,
        )
        signature_request = cls.create_signature_request(
            signature_request_creation_data
        )
        return cls.activate_signature_request(signature_request["id"])

    @classmethod
    def upload_document(cls, filename: str) -> dict:
        """
        Upload the document with the provided filename.
        This document must be a PDF file.
        For now, the document will always be treated as a signable document (treating
        it as a simple attachment might be managed later).

        Args:
            filename(str): name of the file to upload (full path)

        Returns:
            dict

        Raises:
            RuntimeError if upload cannot be done or call to Yousign API fails
        """
        cls._check_document_upload_can_be_done(filename)
        payload = {"nature": "signable_document"}
        request_args = {
            # Content-Type and Content-length are set automatically
            "files": {"file": (filename, open(filename, "rb"), "application/pdf")}
        }
        return cls._manage_call_to_yousign_post_api(
            url="/v3/documents",
            payload=payload,
            error_msg=f"Failed to upload {filename}",
            **request_args,
        )

    @classmethod
    def _check_document_upload_can_be_done(cls, filename: str):
        cls._check_is_initialized()
        FilesystemService.check_file_exists(filename)
        cls._check_file_type_is_supported(filename)

    @classmethod
    def _check_file_type_is_supported(cls, filename: str):
        if not FilesystemService.has_suffix(filename, ".pdf"):
            raise RuntimeError(
                "Unsupported file type (only pdf file type is supported)"
            )

    @classmethod
    def create_signature_request(cls, data: YousignSignatureRequestCreation) -> dict:
        """
        Create a signature request, linked to the provided document and signer.
        Once created, the signature request has a "draft" status and thus needs to be
        activated so that the document can be signed.

        Args:
            data(YousignSignatureRequestCreation): custom part of the data required to
            perform signature request creation

        Returns:
            dict

        Raises:
            RuntimeError if service not initialized or call to Yousign API fails
        """
        cls._check_is_initialized()
        payload = JsonService.dump(data.get_payload())
        request_options = {
            # Don't know why Content-Type is not automatically set in this case ?!
            "Content-Type": "application/json",
        }
        return cls._manage_call_to_yousign_post_api(
            url="/v3/signature_requests",
            payload=payload,
            error_msg="Failed to create signature request",
            **request_options,
        )

    @classmethod
    def activate_signature_request(cls, signature_request_id: str) -> YousignProcedure:
        """
        Activate the signature request with the provided id.

        Args:
            signature_request_id(str): id of the signature request to activate

        Returns:
            YousignProcedure

        Raises:
            RuntimeError if service not initialized or call to Yousign API fails
        """
        cls._check_is_initialized()
        response = cls._manage_call_to_yousign_post_api(
            url=f"/v3/signature_requests/{signature_request_id}/activate",
            payload={},
            error_msg=f"Failed to activate signature request "
            f"(id = {signature_request_id})",
        )
        return YousignProcedure.create_from_yousign_activate_api_response(response)

    @classmethod
    def download_signature_request_document(cls, signature_request_id: str) -> bytes:
        """
        Download the document linked to the signature request with the provided id.

        Args:
            signature_request_id(str): id of the signature request

        Returns:
            bytes: bytes of the downloaded document

        Raises:
            RuntimeError if service not initialized or call to Yousign API fails
        """
        cls._check_is_initialized()
        return cls._manage_call_to_yousign_get_api(
            url=f"/v3/signature_requests/{signature_request_id}/documents/download",
            error_msg=f"Failed to download signature request document "
            f"(id = {signature_request_id})",
        )
