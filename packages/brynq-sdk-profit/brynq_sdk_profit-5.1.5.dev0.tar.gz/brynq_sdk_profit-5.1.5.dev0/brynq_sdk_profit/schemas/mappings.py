# schemas/mappings.py
"""
Mappings for all enums in enums.py with proper human-readable descriptions.
Provides bidirectional mappings between enum codes and human-readable labels (with proper hyphens and capitalization).
"""

from typing import Dict


class Mappings:
    """
    Provides bidirectional mappings for all AFAS Profit enums.
    Uses proper human-readable descriptions from the AFAS documentation (with hyphens, proper capitalization).

    For each enum, provides:
    - code_to_string: Map from enum value (code) to human-readable description
    - string_to_code: Map from human-readable description to enum value (code)

    Example usage:
        # Convert code to string
        gender_name = Mappings.gender_code_to_string['M']  # Returns 'Man'
        nationality = Mappings.nationality_code_to_string['ZA']  # Returns 'Zuid-Afrikaanse'

        # Convert string to code
        gender_code = Mappings.gender_string_to_code['Man']  # Returns 'M'
        nat_code = Mappings.nationality_string_to_code['Zuid-Afrikaanse']  # Returns 'ZA'
    """

    # ===== Person-related mappings =====

    # GenderEnum mappings
    gender_code_to_string: Dict[str, str] = {
        "M": "Man",
        "O": "Onbekend",
        "V": "Vrouw",
        "X": "Non-binair"
    }
    gender_string_to_code: Dict[str, str] = {v: k for k, v in gender_code_to_string.items()}

    # MaritalStatusEnum mappings
    marital_status_code_to_string: Dict[str, str] = {
        "DZ": "Duurzaam gescheiden",
        "GH": "Gehuwd",
        "GP": "Geregistreerd partnerschap",
        "GS": "Gescheiden",
        "OG": "Ongehuwd",
        "OV": "Overig",
        "WE": "Weduwe/Weduwnaar",
        "SW": "Samenwonend",
        "SC": "Samenlevingscontract",

    }
    marital_status_string_to_code: Dict[str, str] = {v: k for k, v in marital_status_code_to_string.items()}

    # NationalityEnum mappings (with proper hyphens)
    nationality_code_to_string: Dict[str, str] = {
        "AX": "Aland Islands", # Åland Islands
        "000": "Onbekend",
        "NL": "Nederlandse",
        "DZ": "Algerijnse",
        "AN": "Angolese",
        "RU": "Burundese",
        "RB": "Botswaanse",
        "BU": "Burkinese",
        "RCA": "Centraal-Afrikaanse",
        "KM": "Comorese",
        "RCB": "Kongolese",
        "DY": "Beninse",
        "ET": "Egyptische",
        "EQ": "Equatoriaalguinese",
        "ETH": "Ethiopische",
        "DJI": "Djiboutiaanse",
        "GA": "Gabonese",
        "WAG": "Gambiaanse",
        "GH": "Ghanese",
        "GN": "Guinese",
        "CI": "Ivoriaanse",
        "CV": "Kaapverdische",
        "TC": "Kameroense",
        "EAK": "Kenyaanse",
        "CD": "Zaïrese",
        "LS": "Lesothaanse",
        "LB": "Liberiaanse",
        "LAR": "Libische",
        "RM": "Malagassische",
        "MW": "Malawische",
        "RMM": "Malinese",
        "MA": "Marokkaanse",
        "RIM": "Mauritaanse",
        "MS": "Mauritiaanse",
        "MOC": "Mozambikaanse",
        "RN": "Nigerese",
        "WAN": "Nigeriaanse",
        "EAU": "Ugandese",
        "GW": "Guinee-Bissause",
        "ZA": "Zuid-Afrikaanse",
        "SD": "Eswatinische",
        "ZW": "Zimbabwaanse",
        "RWA": "Rwandese",
        "ST": "Burger van São Tomé en Principe",
        "SN": "Senegalese",
        "WAL": "Sierra Leoonse",
        "SUD": "Soedanese",
        "SP": "Somalische",
        "EAT": "Tanzaniaanse",
        "TG": "Togolese",
        "TS": "Tsjadische",
        "TN": "Tunesische",
        "Z": "Zambiaanse",
        "SS": "Zuid-Soedanese",
        "BS": "Bahamaanse",
        "BH": "Belizaanse",
        "CDN": "Canadese",
        "CR": "Costa Ricaanse",
        "C": "Cubaanse",
        "DOM": "Dominicaanse",
        "EL": "Salvadoraanse",
        "GCA": "Guatemalaanse",
        "RH": "Haïtiaanse",
        "HON": "Hondurese",
        "JA": "Jamaicaanse",
        "MEX": "Mexicaanse",
        "NIC": "Nicaraguaanse",
        "PA": "Panamese",
        "TT": "Burger van Trinidad en Tobago",
        "USA": "Amerikaans burger",
        "RA": "Argentijnse",
        "BDS": "Barbadaanse",
        "BOL": "Boliviaanse",
        "BR": "Braziliaanse",
        "RCH": "Chileense",
        "CO": "Colombiaanse",
        "EC": "Ecuadoraanse",
        "GUY": "Guyaanse",
        "PY": "Paraguayaanse",
        "PE": "Peruaanse",
        "SME": "Surinaamse",
        "ROU": "Uruguayaanse",
        "YV": "Venezolaanse",
        "WG": "Grenadaanse",
        "KN": "Burger van Saint Kitts-Nevis",
        "SK": "Slowaakse",
        "CZ": "Tsjechische",
        "BA": "Burger van Bosnië-Herzegovina",
        "GE": "Georgische",
        "AFG": "Afghanse",
        "BRN": "Bahreinse",
        "BT": "Bhutaanse",
        "BM": "Burmaanse",
        "BRU": "Bruneise",
        "K": "Cambodjaanse",
        "CL": "Sri Lankaaanse",
        "CN": "Chinese",
        "CY": "Cyprische",
        "RP": "Filipijnse",
        "TMN": "Turkmeense",
        "RC": "Taiwanese",
        "IND": "Indiase",
        "RI": "Indonesische",
        "IRQ": "Iraakse",
        "IR": "Iraanse",
        "IL": "Israëlische",
        "J": "Japanse",
        "HKJ": "Jordaanse",
        "TAD": "Tadzjiekse",
        "KWT": "Koeweitse",
        "LAO": "Laotiaanse",
        "RL": "Libanese",
        "MV": "Maldivische",
        "MAL": "Maleisische",
        "MON": "Mongolische",
        "OMA": "Omaanse",
        "NPL": "Nepalese",
        "KO": "Noord-Koreaanse",
        "OEZ": "Oezbeekse",
        "PK": "Pakistaanse",
        "QA": "Qatarese",
        "AS": "Saoedi-Arabische",
        "SGP": "Singaporese",
        "SYR": "Syrische",
        "T": "Thaise",
        "AE": "Burger van de Ver. Arabische Emiraten",
        "TR": "Turkse",
        "UA": "Oekraïense",
        "ROK": "Zuid-Koreaanse",
        "VN": "Vietnamese",
        "BD": "Bengalese",
        "KG": "Kirgizische",
        "MD": "Moldavische",
        "KZ": "Kazachse",
        "BY": "Belarussische",
        "AZ": "Azerbeidzjaanse",
        "AM": "Armeense",
        "AUS": "Australische",
        "PNG": "Papoea-Nieuw-Guinese",
        "NZ": "Nieuw-Zeelandse",
        "WSM": "West-Samoaaanse",
        "WS": "Samoaanse",
        "RUS": "Russische",
        "SLO": "Sloveense",
        "AG": "Burger van Antigua en Barbuda",
        "VU": "Vanuatuaanse",
        "FJI": "Fijische",
        "GB4": "Burger van Britse afhankelijke gebieden",
        "HR": "Kroatische",
        "TO": "Tongaanse",
        "NR": "Nauruaanse",
        "PLW": "Palause",
        "LV": "Letse",
        "SB": "Salomonseilandse",
        "MIC": "Micronesische",
        "SY": "Seychelse",
        "KIR": "Kiribatische",
        "TV": "Tuvaluaanse",
        "WL": "Saint Luciaanse",
        "WD": "Burger van Dominica",
        "WV": "Burger van Saint Vincent en de Grenadines",
        "EE": "Estische",
        "IOT": "British National (overseas)",
        "ZRE": "Burger van Democratische Republiek Congo",
        "TLS": "Burger van Timor Leste",
        "SCG": "Burger van Servië en Montenegro",
        "SRB": "Servische",
        "MNE": "Montenegrijnse",
        "LT": "Litouwse",
        "MAR": "Marshalleilandse",
        "BUR": "Myanmarese",
        "SWA": "Namibische",
        "GRF": "Vluchteling",
        "499": "Staatloos",
        "AL": "Albanese",
        "AND": "Andorrese",
        "B": "Belgische",
        "BG": "Bulgaarse",
        "DK": "Deense",
        "D": "Duitse",
        "FIN": "Finse",
        "F": "Franse",
        "YMN": "Jemenitische",
        "GR": "Griekse",
        "GB": "Brits burger",
        "H": "Hongaarse",
        "IRL": "Ierse",
        "IS": "IJslandse",
        "I": "Italiaanse",
        "YU": "Joegoslavische",
        "FL": "Liechtensteinse",
        "L": "Luxemburgse",
        "M": "Maltese",
        "MC": "Monegaskische",
        "N": "Noorse",
        "A": "Oostenrijkse",
        "PL": "Poolse",
        "P": "Portugese",
        "RO": "Roemeense",
        "RSM": "San Marinese",
        "E": "Spaanse",
        "VAT": "Vaticaanse",
        "S": "Zweedse",
        "CH": "Zwitserse",
        "GB2": "Brits onderdaan",
        "ERI": "Eritrese",
        "GB3": "Staatsburger van de Britse overzeese gebiedsdelen",
        "XK": "Kosovaarse",
        "MK": "Burger van de Republiek Noord-Macedonië",
        "PSE": "Palestijn"
    }
    nationality_string_to_code: Dict[str, str] = {v: k for k, v in nationality_code_to_string.items()}

    # MatchPersonEnum mappings
    match_person_code_to_string: Dict[int, str] = {
        0: "Zoek op BcCo (Persoons-ID)",
        1: "Burgerservicenummer",
        2: "Naam + voorvoegsel + initialen + geslacht",
        3: "Naam + voorvoegsel + initialen + geslacht + e-mail werk",
        4: "Naam + voorvoegsel + initialen + geslacht + mobiel werk",
        5: "Naam + voorvoegsel + initialen + geslacht + telefoon werk",
        6: "Naam + voorvoegsel + initialen + geslacht + geboortedatum",
        7: "Altijd nieuw toevoegen"
    }
    match_person_string_to_code: Dict[str, int] = {v: k for k, v in match_person_code_to_string.items()}

    # NameUseEnum mappings
    name_use_code_to_string: Dict[int, str] = {
        0: "Geboortenaam",
        1: "Geb. naam partner + Geboortenaam",
        2: "Geboortenaam partner",
        3: "Geboortenaam + Geb. naam partner"
    }
    name_use_string_to_code: Dict[str, int] = {v: k for k, v in name_use_code_to_string.items()}

    # PreferredMediumEnum mappings
    preferred_medium_code_to_string: Dict[str, str] = {
        "EMA": "E-mail",
        "FAX": "Fax",
        "PRS": "Persoonlijk",
        "PST": "Post",
        "TEL": "Telefoonnr."
    }
    preferred_medium_string_to_code: Dict[str, str] = {v: k for k, v in preferred_medium_code_to_string.items()}

    # AmountOfEmployeesEnum mappings
    amount_of_employees_code_to_string: Dict[str, str] = {
        "01": "0",
        "02": "1",
        "03": "2-4",
        "04": "5-9",
        "05": "10-19",
        "06": "20-49",
        "07": "50-99",
        "08": "100-199",
        "09": "200-499",
        "10": "500-749",
        "11": "750-999",
        "12": "1000 en meer"
    }
    amount_of_employees_string_to_code: Dict[str, str] = {v: k for k, v in amount_of_employees_code_to_string.items()}

    # ===== Organisation-related mappings =====

    # MatchOrganisationEnum mappings
    match_organisation_code_to_string: Dict[int, str] = {
        0: "Zoek op BcCo",
        1: "KvK-nummer",
        2: "Fiscaal nummer",
        3: "Naam",
        4: "Adres",
        5: "Postadres",
        6: "Altijd nieuw toevoegen"
    }
    match_organisation_string_to_code: Dict[str, int] = {v: k for k, v in match_organisation_code_to_string.items()}

    # LegalStructureEnum mappings
    legal_structure_code_to_string: Dict[int, str] = {
        999: "Niet vastgesteld",
        0: "Privé persoon",
        1: "(code nog niet vastgesteld)",
        5: "Eenmanszaak",
        10: "Rederij",
        15: "Maatschap",
        20: "Vennootschap onder firma",
        25: "Commanditaire vennootschap",
        30: "Besloten vennootschap",
        35: "Naamloze vennootschap",
        40: "Coöperatie",
        45: "Vereniging",
        50: "Kerkgenootschap",
        55: "Stichting",
        60: "Onderlinge waarborgmaatschappij",
        70: "Buitenlandse rechtsvorm cq onderneming",
        71: "Nevenvestiging met vestiging in NL",
        80: "Europees economisch samenwerkingsverband",
        81: "Buitenlandse EG-vennoot met onderneming in NL",
        82: "Buitenlandse EG-vennoot met hoofdonderneming in NL",
        83: "Buitenlandse op EG-vennoot lijkende ondern. in NL",
        84: "Buitenlandse op EG-vennoot lijkende hfd.ond. in NL",
        99: "Overige"
    }
    legal_structure_string_to_code: Dict[str, int] = {v: k for k, v in legal_structure_code_to_string.items()}

    # BrancheEnum mappings
    branche_code_to_string: Dict[int, str] = {
        100: "Landbouw, jacht, bosbouw, visserij en delfstoffen",
        200: "Industrie",
        300: "Bouwnijverheid",
        400: "Groothandel",
        500: "Detailhandel",
        600: "Horeca",
        700: "Vervoer, telecommunicatie",
        800: "Bank-, verzekeringswezen en onroerend goed",
        900: "Verhuur",
        1000: "Computer en informatietechnologie",
        1100: "Administratie- en accountantskantoren",
        1200: "Overige zakelijke dienstverlening",
        1300: "Overheid",
        1400: "Onderwijs",
        1500: "Gezondheidszorg en welzijn",
        1600: "Milieu, cultuur, sport en recreatie"
    }
    branche_string_to_code: Dict[str, int] = {v: k for k, v in branche_code_to_string.items()}

    # ===== Contact-related mappings =====

    # ContactType mappings
    contact_type_code_to_string: Dict[str, str] = {
        "AFD": "Afdeling bij organisatie",
        "PRS": "Persoon bij organisatie",
        "AFL": "Afleveradres",
        "ORG": "Organisatie",
        "PER": "Persoon"
    }
    contact_type_string_to_code: Dict[str, str] = {v: k for k, v in contact_type_code_to_string.items()}

    # FunctionType mappings
    function_type_code_to_string: Dict[int, str] = {
        100: "Directeur",
        200: "Administratief medewerker",
        300: "Hoofd salarisadministratie"
    }
    function_type_string_to_code: Dict[str, int] = {v: k for k, v in function_type_code_to_string.items()}

    # TitleEnum mappings
    title_code_to_string: Dict[str, str] = {
        "ALG": "Algemeen",
        "BA": "Bachelor of Arts",
        "BRN": "Baron/Barones",
        "BSc": "Bachelor of Science",
        "DIV": "Diversen",
        "DR": "Doctor",
        "DRS": "Doctorandus",
        "DU": "Algemeen Duits",
        "DUI": "Duitse aanhef",
        "EN": "Algemeen Engels",
        "ENG": "Engelse aanhef",
        "ERV": "Erven",
        "FR": "Algemeen Frans",
        "GRF": "Graaf",
        "ING": "Ingenieur (HBO)",
        "IR": "Ingenieur",
        "MA": "Master of Arts",
        "MR": "Meester",
        "MSc": "Master of Science",
        "ONB": "Geslacht onbekend",
        "PRF": "Professor",
        "RA": "Register accountant",
        "RH": "Raadsheer",
        "RTR": "Rechter",
        "ZR": "Zuster"
    }
    title_string_to_code: Dict[str, str] = {v: k for k, v in title_code_to_string.items()}

    # ===== Bank account-related mappings =====

    # CodeDoorberekening mappings
    code_doorberekening_code_to_string: Dict[int, str] = {
        0: "Alle kosten ten laste van de begunstigde",
        1: "Alle kosten ten laste van de opdrachtgever",
        2: "Gedeelde kosten"
    }
    code_doorberekening_string_to_code: Dict[str, int] = {v: k for k, v in code_doorberekening_code_to_string.items()}

    # deliveryCondition mappings
    delivery_condition_code_to_string: Dict[int, str] = {
        0: "Deellevering toestaan",
        1: "Regel volledig uitleveren",
        2: "Order volledig uitleveren",
        3: "Geen backorders leveren"
    }
    delivery_condition_string_to_code: Dict[str, int] = {v: k for k, v in delivery_condition_code_to_string.items()}

    # deliveryMethod mappings
    delivery_method_code_to_string: Dict[str, str] = {
        "A": "Afdrukken",
        "B": "Afdrukken email PDF",
        "C": "Facturen Peppol overige rapporten email PDF",
        "D": "Email PDF efactuur DICO",
        "E": "Email PDF",
        "F": "Everbinding UBL",
        "M": "XML order",
        "O": "Portal email",
        "P": "Afdrukken versturen via EDI",
        "Q": "Factuur"
    }
    delivery_method_string_to_code: Dict[str, str] = {v: k for k, v in delivery_method_code_to_string.items()}

    # barcodeType mappings
    barcode_type_code_to_string: Dict[int, str] = {
        0: "Geen controle",
        1: "Barcode EAN8",
        2: "Barcode UPC",
        3: "Barcode EAN13",
        4: "Barcode EAN14",
        5: "Barcode SSCC",
        6: "Code 128",
        7: "Interleaved 2/5",
        8: "Interleaved 2/5 (controlegetal)"
    }
    barcode_type_string_to_code: Dict[str, int] = {v: k for k, v in barcode_type_code_to_string.items()}

    # ProcessingMethod mappings
    processing_method_code_to_string: Dict[int, str] = {
        1: "Pakbon, factuur na levering",
        2: "Pakbon en factuur",
        3: "Factuur, levering na vooruitbetaling",
        4: "Pakbon, geen factuur",
        5: "Pakbon, factuur via nacalculatie",
        6: "Pakbon en factuur, factuur niet afdrukken of verzenden",
        7: "Aanbetalen, levering na aanbetaling"
    }
    processing_method_string_to_code: Dict[str, int] = {v: k for k, v in processing_method_code_to_string.items()}

    # collectionMethod mappings
    collection_method_code_to_string: Dict[str, str] = {
        "B": "B2B",
        "S": "Standaard"
    }
    collection_method_string_to_code: Dict[str, str] = {v: k for k, v in collection_method_code_to_string.items()}

    # saleRelationType mappings
    sale_relation_type_code_to_string: Dict[str, str] = {
        "001": "Brons",
        "002": "Zilver",
        "003": "Goud"
    }
    sale_relation_type_string_to_code: Dict[str, str] = {v: k for k, v in sale_relation_type_code_to_string.items()}
