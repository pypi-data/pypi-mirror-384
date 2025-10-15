import datetime
import io
from typing import List

from .entities import ContactInfo
from .entities import Pax
from .entities import Flight


class API:
    version = 4

    def __init__(self, contact_info: ContactInfo, pax_list: List[Pax], flight: Flight, is_pre_api=True):
        self.contact_info = contact_info
        self.flight = flight
        self.pax_list = pax_list
        self.lines = []
        self.current = datetime.datetime.now()
        self.is_pre_api = is_pre_api
        prefix = ('API', 'PreAPI')[self.is_pre_api]
        self.filename = f"{prefix}-PAX-{self.flight.flight_number}-{self.flight.departure_airport_code}{self.flight.arrival_airport_code}-{format(self.flight.local_departure_date, '%Y%m%d')}.edi"

    def generate(self):

        self.lines = [
            "UNA:+.? '",
            f"UNB+UNOA:{self.version}+APICUBA {self.flight.airline_code}:ZZ+USCSAPIS:ZZ+{format(self.current, '%y%m%d:%H%M')}+{format(self.current, '%y%m%d%H%M')}++APIS'",
            f"UNG+PAXLST+AIR1:ZZ+USCSAPIS:ZZ+{format(self.current, '%y%m%d:%H%M')}+{format(self.current, '%y%m%d%H%M')}+UN+D:02B'",
            f"UNH+{self.contact_info.agency_code}+PAXLST:D:02B:UN:IATA+{self.flight.flight_number}/{format(self.flight.local_departure_date, '%y%m%d')}/{format(self.flight.local_departure_time, '%H%M')}+01:F'",
            "BGM+745'",
            f"NAD+MS+++{self.contact_info.contact_name}'",
            f"COM+{self.contact_info.phone}:TE++{self.contact_info.email}:EM'",
            f"TDT+20+{self.flight.flight_number}'",
            f"LOC+125+{self.flight.departure_airport_code}'",
            f"DTM+189:{format(self.flight.local_departure_date, '%y%m%d')}{format(self.flight.local_departure_time, '%H%M')}:201'",
            f"LOC+87+{self.flight.arrival_airport_code}'",
            f"DTM+232:{format(self.flight.local_arrival_date, '%y%m%d')}{format(self.flight.local_arrival_time, '%H%M')}:201'",
        ]

        self.generate_passengers()
        self.generate_footer()

    def generate_passengers(self):
        for pax in self.pax_list:
            name = f"{pax.last_name}:{pax.first_name}"
            if pax.second_name:
                name += f':{pax.second_name}'

            self.lines += [
                f"NAD+FL+++{name}'",
                f"ATT+2++{pax.gender}'",
                f"DTM+329:{format(pax.birth_date, '%y%m%d')}'",
                f"LOC+178+{pax.origin_code}'",
                f"LOC+179+{pax.destination_code}'",
                f"NAT+2+{pax.nationality_code}'",
                f"RFF+AVF:{pax.reservation_code}'",
                f"DOC+{pax.document_type}:110:111+{pax.document_number}'",
                f"DTM+36:{format(pax.document_expiry_date, '%y%m%d')}'",
                f"LOC+91+{pax.document_issuer_code}'"
            ]

    def generate_footer(self):
        self.lines += [
            f"CNT+42:{len(self.pax_list)}'",
            f"UNT+{len(self.pax_list * 10) + 8}+{self.contact_info.agency_code}'",
            f"UNE+1+{format(self.current, '%y%m%d%H%M')}'",
            f"UNZ+1+{format(self.current, '%y%m%d%H%M')}'"
        ]

    def to_edi(self):
        content = self.get_edi()

        output = io.StringIO()
        output.write(content)
        output.seek(0)
        return output

    def get_edi(self):
        self.generate()
        return '\n'.join(self.lines)
