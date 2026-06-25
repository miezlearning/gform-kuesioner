import kuesioner
fd = kuesioner.extract_form_structure(kuesioner.FORM_URL)
print(f"\nhas_email_page: {fd['has_email_page']}")
print(f"page_history: {fd['page_history']}")
