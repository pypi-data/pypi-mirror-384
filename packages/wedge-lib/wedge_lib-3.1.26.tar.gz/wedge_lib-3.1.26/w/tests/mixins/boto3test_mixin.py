import boto3

from moto import mock_s3

from w.services.technical.boto3_service import Boto3Service


class Boto3TestMixin:
    def setup_method(self, method):
        super().setup_method(method)
        self.s3_mock = mock_s3()
        self.s3_mock.start()
        Boto3Service._get_client = lambda x: boto3.client("s3", region_name="us-east-1")
        Boto3Service._get_ressource = lambda x: boto3.resource("s3")
        Boto3Service.init()
        self.mock_generate_signed_url = {
            "service": Boto3Service,
            "method_name": "generate_signed_url",
            "return_value": "https://bucket-name.s3.amazonaws.com/media/"
            "customers/2/2023/2023_01_recapitulatif_mensuel_2.pdf"
            "?AWSAccessKeyId=foobar_key"
            "&Signature=YQETFSxfOmcY16ufLu3y5ZxBMjg%3D&Expires=1685111716",
        }

    def teardown_method(self, method):
        self.s3_mock.stop()
