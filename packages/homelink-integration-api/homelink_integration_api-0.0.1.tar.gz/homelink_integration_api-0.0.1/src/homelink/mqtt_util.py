from OpenSSL import crypto
import re
from homelink.settings import (
    MQTT_ROOT_CA,
    MQTT_ROOT_CA_REPOSITORY,
    MQTT_PRIVATE_KEY_SIZE,
)
from aiohttp import ClientTimeout, request


def format_csr(csr_pem):
    return (
        re.search(
            r"-+BEGIN CERTIFICATE REQUEST-+\s+(.*?)\s+-+END CERTIFICATE REQUEST-+",
            csr_pem,
            flags=re.DOTALL,
        )
        .group(1)
        .strip()
        .replace("\n", "")
    )


async def generate_csr():
    url = f"{MQTT_ROOT_CA_REPOSITORY}/{MQTT_ROOT_CA}"
    client_timeout = ClientTimeout(total=60)
    async with request("GET", url=url, timeout=client_timeout) as response:
        cert_data = await response.text()
        if response.status != 200 or "error" in cert_data:
            raise Exception("Failed to get root certificate")
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, MQTT_PRIVATE_KEY_SIZE)
    key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8")
    bytes_private_key = key_pem.encode("utf-8")

    csr = crypto.X509Req()
    csr.get_subject().CN = "gentex"
    csr.set_pubkey(key)
    csr.sign(key, "sha512")

    csr_pem = crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr).decode(
        encoding="utf-8"
    )

    return bytes_private_key, format_csr(csr_pem)
