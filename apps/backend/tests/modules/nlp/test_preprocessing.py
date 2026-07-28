from app.modules.nlp.preprocessing import (
    EMAIL_TOKEN,
    PHONE_TOKEN,
    URL_TOKEN,
    clean_text,
    preprocess_text,
    tokenize_cleaned_text,
)


def test_clean_text_normalizes_unicode_case_html_controls_and_punctuation() -> None:
    text = (
        "\uff1cb\uff1e\uff33\uff21\uff39\uff21 BOOKING\uff1c/b\uff1e"
        "\x00 tukang &lt;i&gt;harian&lt;/i&gt;!!!"
    )

    assert clean_text(text) == "saya booking tukang harian"


def test_clean_text_replaces_url_email_and_indonesian_phone() -> None:
    text = "Hubungi 0812 3456 7890, CS@Example.com, atau https://contoh.id/a."

    assert clean_text(text) == (f"hubungi {PHONE_TOKEN} {EMAIL_TOKEN} atau {URL_TOKEN}")


def test_preprocessing_keeps_informative_stopwords_and_numbers() -> None:
    result = preprocess_text("Saya mau BOOKING tukang utk 02/08/2026.")

    assert result.cleaned == "saya mau booking tukang utk 02 08 2026"
    assert result.tokens == ("saya", "mau", "booking", "tukang", "utk", "02", "08", "2026")


def test_documented_preprocessing_examples_are_exact() -> None:
    first = preprocess_text("Halo Kak!! Ada jasa tukang listrik?")
    ticket = preprocess_text("Cek tiket TKT-20260728-AB12CD dong")

    assert first.cleaned == "halo kak ada jasa tukang listrik"
    assert first.tokens == ("halo", "kak", "ada", "jasa", "tukang", "listrik")
    assert ticket.cleaned == "cek tiket tkt 20260728 ab12cd dong"
    assert ticket.tokens == ("cek", "tiket", "tkt", "20260728", "ab12cd", "dong")


def test_tokenizer_accepts_cleaned_text() -> None:
    assert tokenize_cleaned_text("harga rumah 5000000") == ["harga", "rumah", "5000000"]


def test_empty_text_has_empty_output() -> None:
    result = preprocess_text(" \n\t ")

    assert result.cleaned == ""
    assert result.tokens == ()
