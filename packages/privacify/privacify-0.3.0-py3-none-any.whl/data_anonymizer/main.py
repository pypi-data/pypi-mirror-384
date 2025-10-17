import re


# Reguläre Ausdrücke
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
CREDITCARD_RE = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
PHONE_RE = re.compile(
    r'\b(?:\+?\d{1,3}[ \-\.]?)?(?:\(?\d{2,4}\)?[ \-\.]?){2,3}\d{3,4}\b'
)

def anonymize_text(
    text: str,
    email_tag: str = "[EMAIL]",
    credit_card_tag: str = "[CREDIT_CARD]",
    phone_tag: str = "[PHONE]",
    anonymize_email: bool = True,
    anonymize_credit_card: bool = True,
    anonymize_phone: bool = True
) -> str:
    '''Anonymize selected types of sensitive data in the given text.'''
    if anonymize_email:
        text = EMAIL_RE.sub(email_tag, text)
    if anonymize_credit_card:
        text = CREDITCARD_RE.sub(credit_card_tag, text)
    if anonymize_phone:
        text = PHONE_RE.sub(phone_tag, text)
    return text



   
if __name__ == "__main__":
    # Example usage of the anonymize_text function.
    text = """Meine Kreditkarte ist 4111 1111 1111 1111 und die von Max ist 5500-0000-0000-0004. Seine Nummer ist 0123 4567890. und meine +49 123 4567890. Die Zahlung war 123,52€
    Bitte auf der Folgenden E-Mail antworten: hello.world@gmail.com"""
    cleaned_text = anonymize_text(text, anonymize_email=False)
    print(cleaned_text)
