from markitdown_api.services.anonymization import anonymize_content, anonymize_json_value


def test_anonymize_content_redacts_person_and_email() -> None:
    result = anonymize_content("Meu nome é João Silva, e-mail joao@example.com.")
    assert "João Silva" not in result.anonymized
    assert "joao@example.com" not in result.anonymized
    entity_types = {e.entity_type for e in result.entities_found}
    assert "PERSON" in entity_types
    assert "EMAIL_ADDRESS" in entity_types


def test_anonymize_content_redacts_valid_cpf() -> None:
    result = anonymize_content("CPF: 123.456.789-09.")
    assert "123.456.789-09" not in result.anonymized
    assert any(e.entity_type == "CPF" for e in result.entities_found)


def test_anonymize_content_rejects_invalid_cpf_checksum() -> None:
    result = anonymize_content("CPF: 111.111.111-11.")
    assert "111.111.111-11" in result.anonymized
    assert not any(e.entity_type == "CPF" for e in result.entities_found)


def test_anonymize_content_redacts_valid_cnpj() -> None:
    result = anonymize_content("CNPJ: 11.222.333/0001-81.")
    assert "11.222.333/0001-81" not in result.anonymized
    assert any(e.entity_type == "CNPJ" for e in result.entities_found)


def test_anonymize_content_redacts_rg() -> None:
    result = anonymize_content("Meu RG é 12.345.678-9.")
    assert "12.345.678-9" not in result.anonymized
    assert any(e.entity_type == "RG" for e in result.entities_found)


def test_anonymize_content_redacts_br_phone() -> None:
    result = anonymize_content("Meu telefone é (11) 98888-7777.")
    assert "98888-7777" not in result.anonymized
    assert any(e.entity_type == "PHONE_NUMBER_BR" for e in result.entities_found)


def test_anonymize_content_preserves_markup_around_redacted_span() -> None:
    result = anonymize_content("<p>joao@example.com</p>")
    assert result.anonymized.startswith("<p>")
    assert result.anonymized.endswith("</p>")
    assert "joao@example.com" not in result.anonymized


def test_anonymize_json_value_redacts_nested_strings_and_tracks_path() -> None:
    data = {"user": {"email": "joao@example.com"}, "notes": ["contato: joao@example.com"]}
    result = anonymize_json_value(data)
    assert "joao@example.com" not in result.anonymized["user"]["email"]
    assert "joao@example.com" not in result.anonymized["notes"][0]
    paths = {e.path for e in result.entities_found}
    assert "user.email" in paths
    assert "notes[0]" in paths


def test_anonymize_json_value_leaves_non_string_values_untouched() -> None:
    data = {"age": 30, "active": True, "score": None}
    result = anonymize_json_value(data)
    assert result.anonymized == data
    assert result.entities_found == []
