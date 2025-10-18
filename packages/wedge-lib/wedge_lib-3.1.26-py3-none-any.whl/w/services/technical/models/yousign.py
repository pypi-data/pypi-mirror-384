from dataclasses import dataclass
from typing import List

from w.mixins.dataclasses_mixin import DataclassMixin

DEFAULT_SIGNER_FIELD_WIDTH = 100
DEFAULT_SIGNER_FIELD_HEIGHT = 40


@dataclass
class YousignSigner(DataclassMixin):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    locale: str


@dataclass
class YousignSignerField(DataclassMixin):
    page_number: int
    # Note: one can use Yousign tool ("placeit") to easily determine the coordinates
    top_left_x_coordinate: int
    top_left_y_coordinate: int


@dataclass
class YousignSignatureField(YousignSignerField, DataclassMixin):
    pass


@dataclass
class YousignMentionField(YousignSignerField, DataclassMixin):
    text: str


@dataclass
class YousignSignatureRequestCreation(DataclassMixin):
    name: str
    documents: List[str]
    signers: List[YousignSigner]
    signature_field: YousignSignatureField
    mention_field: YousignMentionField = None

    def get_payload(self) -> dict:
        signers = [
            {
                "info": signer.to_dict(),
                "fields": self._list_signer_fields(),
                "signature_level": "electronic_signature",
                "signature_authentication_mode": "otp_sms",
            }
            for signer in self.signers
        ]
        return {
            "documents": self.documents,
            "signers": signers,
            "name": self.name,
            # We don't want Yousign to send an email to the signer with the signature
            # link
            # But get the signature link from the activation response and use it as we
            # want
            # => Improvement : make this configurable
            "delivery_mode": "none",
        }

    def _list_signer_fields(self) -> List[dict]:
        signature_field = {
            "document_id": self.documents[0],
            "type": "signature",
            "page": self.signature_field.page_number,
            "width": DEFAULT_SIGNER_FIELD_WIDTH,
            "height": DEFAULT_SIGNER_FIELD_HEIGHT,
            "x": self.signature_field.top_left_x_coordinate,
            "y": self.signature_field.top_left_y_coordinate,
        }
        signer_fields = [signature_field]
        if self.mention_field:
            mention_field = {
                "document_id": self.documents[0],
                "type": "mention",
                "mention": f"{self.mention_field.text} %date%",
                "page": self.mention_field.page_number,
                "width": DEFAULT_SIGNER_FIELD_WIDTH,
                "height": DEFAULT_SIGNER_FIELD_HEIGHT,
                "x": self.mention_field.top_left_x_coordinate,
                "y": self.mention_field.top_left_y_coordinate,
            }
            signer_fields.append(mention_field)
        return signer_fields


@dataclass
class YousignProcedureStart(DataclassMixin):
    signature_request_name: str
    filename: str
    signer: YousignSigner
    signature_field: YousignSignatureField
    mention_field: YousignMentionField = None


@dataclass
class YousignProcedure(DataclassMixin):
    signature_request_id: str
    signature_request_status: str
    document_id: str
    signer_id: str
    signature_link: str

    @classmethod
    def create_from_yousign_activate_api_response(cls, api_response):
        return cls(
            signature_request_id=api_response["id"],
            signature_request_status=api_response["status"],
            document_id=api_response["documents"][0]["id"],
            signer_id=api_response["signers"][0]["id"],
            signature_link=api_response["signers"][0]["signature_link"],
        )
