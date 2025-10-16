# Privacify

**Data Anonymizer** is a Python project for anonymizing sensitive information in text and datasets. It provides simple tools to mask, hash, or remove personally identifiable information (PII) such as emails, credit card numbers, and phone numbers, making your data safe for sharing, analysis, or compliance with privacy regulations.

## Features


- **Flexible anonymization:** Detects and replaces emails, credit card numbers, and phone numbers.
- **Customizable tags:** Choose how anonymized data is represented.
- **Easy integration:** Use as a Python module or script.
- **Compliance:** Helps meet GDPR, HIPAA, and other privacy requirements.

## How It Works

The main function processes your text by:
1. Identifying emails, credit card numbers, and phone numbers using regular expressions.
2. Replacing them with customizable tags (e.g., `[EMAIL]`, `[CREDIT_CARD]`, `[PHONE]`).
3. Returning the anonymized text.

### Example: Selective Anonymization
## Parameter Overview

The `anonymize_text` function supports the following parameters to control the anonymization process:

| Parameter              | Type    | Default       | Description                                                        |
|------------------------|---------|---------------|--------------------------------------------------------------------|
| `anonymize_email`      | bool    | `True`        | Anonymize email addresses if set to `True`.                        |
| `anonymize_credit_card`| bool    | `True`        | Anonymize credit card numbers if set to `True`.                    |
| `anonymize_phone`      | bool    | `True`        | Anonymize phone numbers if set to `True`.                          |
| `email_tag`            | str     | `[EMAIL]`     | Placeholder for anonymized email addresses.                        |
| `credit_card_tag`      | str     | `[CREDIT_CARD]` | Placeholder for anonymized credit card numbers.                 |
| `phone_tag`            | str     | `[PHONE]`     | Placeholder for anonymized phone numbers.                          |

These parameters let you flexibly control which types of data are anonymized and how they are represented.

```python
from data_anonymizer import anonymize_text

text = """
Meine Kreditkarte ist 4111 1111 1111 1111 und die von Max ist 5500-0000-0000-0004.
Seine Nummer ist 0123 4567890. und meine +49 123 4567890. Die Zahlung war 123,52€
Bitte auf der Folgenden E-Mail antworten: hello.world@gmail.com
"""

# Only anonymize credit cards and phone numbers, leave emails unchanged
cleaned_text = anonymize_text(
    text,
    anonymize_email=False,
    anonymize_credit_card=True,
    anonymize_phone=True
)
print(cleaned_text)
```

**Output:**
```
Meine Kreditkarte ist [CREDIT_CARD] und die von Max ist [CREDIT_CARD].
Seine Nummer ist [PHONE]. und meine [PHONE]. Die Zahlung war 123,52€
Bitte auf der Folgenden E-Mail antworten: hello.world@gmail.com
```

```python
from data_anonymizer import anonymize_text

text = """
Meine Kreditkarte ist 4111 1111 1111 1111 und die von Max ist 5500-0000-0000-0004.
Seine Nummer ist 0 123 4567890.
Bitte auf der Folgenden E-Mail antworten: hello.world@gmail.com
"""

cleaned_text = anonymize_text(text)
print(cleaned_text)
```

**Output:**
```
Meine Kreditkarte ist [CREDIT_CARD] und die von Max ist [CREDIT_CARD].
Seine Nummer ist [PHONE].
Bitte auf der Folgenden E-Mail antworten: [EMAIL]
```

## License

MIT License

---

*Feel free to contribute or open issues for feature requests!*