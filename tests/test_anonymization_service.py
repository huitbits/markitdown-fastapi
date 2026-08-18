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


def test_anonymize_content_redacts_unformatted_cpf() -> None:
    # 12345678909 is a valid CPF checksum
    result = anonymize_content("CPF 12345678909 do cliente.")
    assert "12345678909" not in result.anonymized
    assert any(e.entity_type == "CPF" for e in result.entities_found)


def test_anonymize_content_rejects_invalid_cpf_checksum() -> None:
    result = anonymize_content("CPF: 111.111.111-11.")
    assert "111.111.111-11" in result.anonymized
    assert not any(e.entity_type == "CPF" for e in result.entities_found)


def test_anonymize_content_rejects_invalid_unformatted_cpf() -> None:
    result = anonymize_content("CPF: 12345678900.")
    assert "12345678900" in result.anonymized
    assert not any(e.entity_type == "CPF" for e in result.entities_found)


def test_anonymize_content_redacts_valid_cnpj() -> None:
    result = anonymize_content("CNPJ: 11.222.333/0001-81.")
    assert "11.222.333/0001-81" not in result.anonymized
    assert any(e.entity_type == "CNPJ" for e in result.entities_found)


def test_anonymize_content_redacts_unformatted_cnpj() -> None:
    result = anonymize_content("CNPJ 11222333000181 da empresa.")
    assert "11222333000181" not in result.anonymized
    assert any(e.entity_type == "CNPJ" for e in result.entities_found)


def test_anonymize_content_rejects_invalid_cnpj_checksum() -> None:
    result = anonymize_content("CNPJ: 11.222.333/0001-00.")
    assert "11.222.333/0001-00" in result.anonymized
    assert not any(e.entity_type == "CNPJ" for e in result.entities_found)


def test_anonymize_content_redacts_rg() -> None:
    result = anonymize_content("Meu RG é 12.345.678-9.")
    assert "12.345.678-9" not in result.anonymized
    assert any(e.entity_type == "RG" for e in result.entities_found)


def test_anonymize_content_redacts_br_phone() -> None:
    result = anonymize_content("Meu telefone é (11) 98888-7777.")
    assert "98888-7777" not in result.anonymized
    assert any(e.entity_type == "PHONE_NUMBER_BR" for e in result.entities_found)


def test_anonymize_content_redacts_phone_list_and_toll_free() -> None:
    text = "Telefone: (11) 4704-2555/4704-2556/4704-2005 e SAC 0800 123 4567"
    result = anonymize_content(text)
    assert "4704-2555" not in result.anonymized
    assert "4704-2556" not in result.anonymized
    assert "4704-2005" not in result.anonymized
    assert "0800 123 4567" not in result.anonymized
    phone_entities = [e for e in result.entities_found if e.entity_type == "PHONE_NUMBER_BR"]
    assert len(phone_entities) == 4


def test_anonymize_content_redacts_company_names() -> None:
    text = "A empresa CIRCULO TRANSPORTES E LOGÍSTICA EIRELI e a ALFA LTDA firmaram acordo."
    result = anonymize_content(text)
    assert "CIRCULO TRANSPORTES E LOGÍSTICA EIRELI" not in result.anonymized
    assert "ALFA LTDA" not in result.anonymized
    assert any(e.entity_type == "ORGANIZATION" for e in result.entities_found)


def test_anonymize_content_redacts_cep() -> None:
    result = anonymize_content("CEP: 06833-370")
    assert "06833-370" not in result.anonymized
    assert any(e.entity_type == "CEP" for e in result.entities_found)


def test_anonymize_content_redacts_address() -> None:
    result = anonymize_content("Local: Avenida Elias Yasbek, nº 1515 - Centro")
    assert "Avenida Elias Yasbek" not in result.anonymized
    assert any(e.entity_type == "LOCATION" for e in result.entities_found)


def test_anonymize_content_redacts_cnj_process() -> None:
    result = anonymize_content("Processo CNJ nº 0001234-56.2023.8.26.0100 em andamento.")
    assert "0001234-56.2023.8.26.0100" not in result.anonymized
    assert any(e.entity_type == "PROCESS_NUMBER_CNJ" for e in result.entities_found)


def test_anonymize_content_redacts_vehicle_plates() -> None:
    result = anonymize_content("Veículos com placas ABC1D23 e XYZ-9876.")
    assert "ABC1D23" not in result.anonymized
    assert "XYZ-9876" not in result.anonymized
    assert any(e.entity_type == "VEHICLE_PLATE_BR" for e in result.entities_found)


def test_anonymize_content_suppresses_false_positive_spacy_tokens() -> None:
    text = "Tel: (11) 4704-2555. Atividades: CARGA E DESCARGA, ARMAZÉNS GERAIS."
    result = anonymize_content(text)
    assert "Tel:" in result.anonymized
    assert "CARGA E DESCARGA" in result.anonymized
    assert "ARMAZÉNS GERAIS" in result.anonymized
    assert "4704-2555" not in result.anonymized


def test_anonymize_content_full_alvara_document() -> None:
    doc = (
        "# PREFEITURA MUNICIPAL\n"
        "## ALVARÁ DE LICENÇA\n"
        "Razão Social\nCIRCULO TRANSPORTES E LOGÍSTICA EIRELI\n"
        "CNPJ: 11.222.333/0001-81\n"
        "Endereço: R JOSE SEMIAO RODRIGUES AGOSTINHO, nº 1370 - CEP 06833-370\n"
        "Atividade: CARGA E DESCARGA\n"
        "Tel: (11) 4704-2555/4704-2556\n"
    )
    result = anonymize_content(doc)
    assert "CIRCULO TRANSPORTES E LOGÍSTICA EIRELI" not in result.anonymized
    assert "11.222.333/0001-81" not in result.anonymized
    assert "06833-370" not in result.anonymized
    assert "4704-2555" not in result.anonymized
    assert "4704-2556" not in result.anonymized
    assert "CARGA E DESCARGA" in result.anonymized


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
