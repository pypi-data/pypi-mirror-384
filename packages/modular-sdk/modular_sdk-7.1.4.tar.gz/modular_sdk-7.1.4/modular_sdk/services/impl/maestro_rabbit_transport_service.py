import binascii
import json
from typing import Any
from modular_sdk.commons import (
    ModularException, generate_id, build_secure_message, build_message,
)
from modular_sdk.commons.constants import (
    Env,
    PLAIN_CONTENT_TYPE,
    SUCCESS_STATUS,
    ERROR_STATUS,
    RESULTS,
    DATA,
)  # todo remove these imports with major release. They can be used from outside
from modular_sdk.commons.log_helper import get_logger
from modular_sdk.connections.rabbit_connection import RabbitMqConnection
from modular_sdk.services.impl.maestro_signature_builder import (
    MaestroSignatureBuilder,
)
from modular_sdk.services.rabbit_transport_service import (
    RabbitMQTransport, RabbitConfig,
)

_LOG = get_logger(__name__)


class MaestroRabbitConfig(RabbitConfig):
    def __init__(self, request_queue: str, response_queue: str,
                 rabbit_exchange: str,
                 sdk_access_key: str, sdk_secret_key: str, maestro_user: str):
        super(MaestroRabbitConfig, self).__init__(
            request_queue=request_queue,
            response_queue=response_queue,
            rabbit_exchange=rabbit_exchange
        )
        self.sdk_access_key = sdk_access_key
        self.sdk_secret_key = sdk_secret_key
        self.maestro_user = maestro_user


class MaestroRabbitMQTransport(RabbitMQTransport):
    def __init__(self, rabbit_connection: RabbitMqConnection,
                 config: MaestroRabbitConfig):
        super().__init__(
            rabbit_connection=rabbit_connection,
            config=config
        )
        self.access_key = config.sdk_access_key
        self.secret_key = config.sdk_secret_key
        self.user = config.maestro_user

    def pre_process_request(self, command_name, parameters, secure_parameters,
                            is_flat_request, async_request, compressed=False,
                            config=None) -> tuple[str | bytes, dict]:
        request_id = generate_id()
        _LOG.debug('Going to pre-process request')
        message = build_message(
            command_name=command_name,
            parameters=parameters,
            request_id=request_id,
            is_flat_request=is_flat_request,
            compressed=compressed
        )

        signer = MaestroSignatureBuilder(
            access_key=config.sdk_access_key if config and config.sdk_access_key else self.access_key,
            secret_key=config.sdk_secret_key if config and config.sdk_secret_key else self.secret_key,
            user=config.maestro_user if config and config.maestro_user else self.user,
        )
        encrypted_body = signer.encrypt(data=message)

        limit = Env.RABBITMQ_MAX_MESSAGE_SIZE.as_int()
        if len(encrypted_body) > limit:
            _LOG.error(f'Message size exceeds maximum allowed size: {limit}')
            raise ModularException(
                code=500,
                content=f'Message size for RabbitMQ exceeds maximum allowed size: {limit} bytes'
            )
        _LOG.debug('Message length is within the limit')

        _LOG.debug('Message encrypted')
        # sign headers
        headers = signer.get_signed_headers(
            async_request=async_request,
            compressed=compressed
        )
        _LOG.debug('Signed headers prepared')
        return encrypted_body, headers

    def post_process_request(self, response: bytes) -> tuple[int, str, Any]:
        # TODO post process does not accept config whereas pre process accepts
        signer = MaestroSignatureBuilder(
            access_key=self.access_key,
            secret_key=self.secret_key,
            user=self.user
        )
        try:
            response_item = signer.decrypt(data=response)
            _LOG.debug('Message from M3-server successfully decrypted')
        except binascii.Error:
            response_item = response.decode('utf-8')
        try:
            _LOG.debug('Received and decrypted message from server')
            response_json = json.loads(response_item).get('results')[0]
        except json.decoder.JSONDecodeError:
            _LOG.error('Response can not be decoded - invalid Json string')
            raise ModularException(code=502, content="Response can't be decoded")
        status = response_json.get('status')
        code = response_json.get('statusCode')
        if status == SUCCESS_STATUS:
            data = response_json.get('data')
        else:
            data = response_json.get('readableError') or response_json.get('error')
        return code, status, data
