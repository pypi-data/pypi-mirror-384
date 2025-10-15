import io
from collections import defaultdict
from typing import List

from .normalize import short_date, short_date_without_year, keep_alphanumeric
from .entities import ContactInfo
from .entities import Pax
from .entities import Flight


class PNL:

    def __init__(self, contact_info: ContactInfo, pax_list: List[Pax], flight: Flight, split_doc_limit: int = 58,
                 is_adl: bool = False):
        self.prefix = ('PNL', 'ADL')[is_adl]
        self.lines = [self.prefix]
        self.contact_info = contact_info
        self.flight = flight
        self.pax_list = pax_list
        self.split_doc_limit = split_doc_limit
        self.is_adl = is_adl
        self.filename = f"{self.prefix}_{self.flight.flight_number}_{format(self.flight.local_departure_date, '%y%m%d')}_{self.flight.departure_airport_code}.txt"

    def generate(self):
        grouped_list = self.get_grouped()

        for index, (destination_code, pax_list) in enumerate(grouped_list.items()):
            self.lines += self.get_part(index + 1, destination_code, pax_list, total_parts=len(grouped_list.keys()))

        self.lines += [f'END{self.prefix}']

    def get_part(self, part_number, destination_code, pax_list, *, total_parts=None):
        part = [] if part_number == 1 else ['']
        part += [
            self.get_flight_header(part_number),
            f'-{destination_code}{str(len(pax_list)).zfill(3)}Y'
        ]

        for pax in pax_list:
            part += [self.get_pax_info(pax), *self.get_doc_line(pax)]

        if total_parts and total_parts > 1:
            part += [f'ENDPART{part_number}']
        return part

    def get_pax_info(self, pax):
        last_name = keep_alphanumeric(pax.last_name).replace(' ', '')
        first_name = keep_alphanumeric(pax.first_name).replace(' ', '')
        fullname = f'{last_name}/{first_name}'[:35]
        category = pax.get_category(self.flight.local_departure_date)
        marker = ''
        if category == 'CHD':
            marker = ' .R/CHLD'
        elif category == 'INF':
            marker = ' .R/INFT'
        return f'1{fullname}{marker}'

    def get_flight_header(self, index):
        departure_date = short_date_without_year(self.flight.local_departure_date)
        return f'{self.flight.flight_number}/{departure_date} {self.flight.departure_airport_code} PART{index}'

    def get_doc_line(self, pax):
        last_name = keep_alphanumeric(pax.last_name)
        first_name = keep_alphanumeric(pax.first_name)
        second_name = keep_alphanumeric(pax.second_name)
        category = pax.get_category(self.flight.local_departure_date)
        birth_date = short_date(pax.birth_date)
        document_expiry_date = short_date(pax.document_expiry_date)

        marker1 = ''
        if category == 'INF':
            marker1 = 'I'

        doc = f'.R/DOCS HK1/{pax.document_type}/{pax.document_issuer_code}/{pax.document_number}/{pax.nationality_code}/{birth_date}/{pax.gender}{marker1}/{document_expiry_date}/{last_name}/{first_name}/{second_name}'

        if len(doc) < self.split_doc_limit:
            return [doc]
        return [
            doc[:self.split_doc_limit],
            f'.RN/{doc[self.split_doc_limit:self.split_doc_limit + self.split_doc_limit - 4]}'
        ]

    def get_grouped(self):
        grouped_objects = defaultdict(list)
        for pax in self.pax_list:
            grouped_objects[pax.destination_code].append(pax)
        return dict(grouped_objects)

    def to_txt(self):
        content = self.get_content()

        output = io.StringIO()
        output.write(content)
        output.seek(0)
        return output

    def get_content(self):
        self.generate()
        return '\n'.join(self.lines)
