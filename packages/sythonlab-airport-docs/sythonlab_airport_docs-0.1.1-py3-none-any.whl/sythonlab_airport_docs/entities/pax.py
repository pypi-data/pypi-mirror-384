import datetime


class Pax:

    def __init__(self, first_name: str, second_name: str, last_name: str, gender: str, birth_date: str,
                 nationality_code: str, document_type: str, document_number: str, document_expiry_date: str,
                 document_issuer_code: str, flight_class: str, origin_code: str, destination_code: str,
                 reservation_code: str):
        self.first_name = first_name.strip().upper()
        self.second_name = second_name.strip().upper()
        self.last_name = last_name.strip().upper()
        self.gender = gender.strip().upper()
        self.reservation_code = reservation_code.strip().upper()

        try:
            self.birth_date = datetime.datetime.strptime(birth_date.strip(), '%Y-%m-%d')
        except ValueError:
            raise ValueError('Birth date must be in format YYYY-MM-DD')

        try:
            self.document_expiry_date = datetime.datetime.strptime(document_expiry_date.strip(), '%Y-%m-%d')
        except ValueError:
            raise ValueError('Document expiry date must be in format YYYY-MM-DD')

        self.nationality_code = nationality_code.strip().upper()
        self.document_type = document_type.strip().upper()
        self.document_number = document_number.strip().upper()
        self.document_issuer_code = document_issuer_code.strip().upper()
        self.flight_class = flight_class.strip().upper()
        self.origin_code = origin_code.strip().upper()
        self.destination_code = destination_code.strip().upper()

        self.validate()

    def validate(self):
        if self.gender not in ['M', 'F']:
            raise ValueError('Gender must be "M" or "F"')

        if len(self.nationality_code) != 3:
            raise ValueError('Nationality code must be 3 characters long')

        if len(self.document_issuer_code) != 3:
            raise ValueError('Document issuer country code must be 3 characters long')

        if len(self.origin_code) != 3:
            raise ValueError('Origin code country code must be 3 characters long')

        if len(self.destination_code) != 3:
            raise ValueError('Destination code country code must be 3 characters long')

    def __str__(self):
        return ' '.join(list(filter(lambda x: x is not None, [self.first_name, self.second_name, self.last_name])))

    def get_age(self, date):
        if date and type(date) is str:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        if not date:
            date = datetime.datetime.now().date()
        return date.year - self.birth_date.year - (
                (date.month, date.day) < (self.birth_date.month, self.birth_date.day))

    def get_category(self, date):
        age = self.get_age(date)
        if age < 2:
            return 'INF'
        if age < 12:
            return 'CHD'
        return 'ADU'
