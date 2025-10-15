class ContactInfo:

    def __init__(self, contact_name: str, phone: str, email: str, agency_code: str):
        self.contact_name = contact_name
        self.phone = phone
        self.email = email
        self.agency_code = agency_code

    def __str__(self):
        return self.contact_name
