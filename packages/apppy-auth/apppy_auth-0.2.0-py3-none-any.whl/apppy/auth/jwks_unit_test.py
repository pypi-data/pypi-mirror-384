import datetime

from apppy.auth.jwks import JwkPemFile


def test_jwk_parse_file_name_private():
    service_name, version, generated_at = JwkPemFile._parse_file_name(
        "test_jwk_pem_file_public.v0.20250905215639.key.pem"
    )
    assert service_name == "test_jwk_pem_file_public"
    assert version == 0
    assert generated_at == datetime.datetime(2025, 9, 5, 21, 56, 39, 0)


def test_jwk_parse_file_name_public():
    service_name, version, generated_at = JwkPemFile._parse_file_name(
        "test_jwk_pem_file_public.v0.20250905215639.pub.pem"
    )
    assert service_name == "test_jwk_pem_file_public"
    assert version == 0
    assert generated_at == datetime.datetime(2025, 9, 5, 21, 56, 39, 0)
