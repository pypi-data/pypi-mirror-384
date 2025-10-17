# schemas/enums.py
# enums across schemas, dutch coding.
from enum import Enum, IntEnum

from pydantic_core.core_schema import EnumSchema

# Person-related enums
class MatchPersonEnum(IntEnum):
    """Persoon vergelijken op enum"""
    EMPTY = -1  # Empty value
    ZOEK_OP_BCCO = 0  # Zoek op BcCo (Persoons-ID)
    BURGERSERVICENUMMER = 1  # Burgerservicenummer
    NAAM_VOORVOEGSEL_INITIALEN_GESLACHT = 2  # Naam + voorvoegsel + initialen + geslacht
    NAAM_VOORVOEGSEL_INITIALEN_GESLACHT_EMAIL = 3  # Naam + voorvoegsel + initialen + geslacht + e-mail werk
    NAAM_VOORVOEGSEL_INITIALEN_GESLACHT_MOBIEL = 4  # Naam + voorvoegsel + initialen + geslacht + mobiel werk
    NAAM_VOORVOEGSEL_INITIALEN_GESLACHT_TELEFOON = 5  # Naam + voorvoegsel + initialen + geslacht + telefoon werk
    NAAM_VOORVOEGSEL_INITIALEN_GESLACHT_GEBOORTEDATUM = 6  # Naam + voorvoegsel + initialen + geslacht + geboortedatum
    ALTIJD_NIEUW_TOEVOEGEN = 7  # Altijd nieuw toevoegen

class NameUseEnum(IntEnum):
    """Naamgebruik enum"""
    EMPTY = -1  # Empty value
    GEBOORTENAAM = 0  # Geboortenaam
    GEB_NAAM_PARTNER_GEBOORTENAAM = 1  # Geb. naam partner + Geboortenaam
    GEBOORTENAAM_PARTNER = 2  # Geboortenaam partner
    GEBOORTENAAM_GEB_NAAM_PARTNER = 3  # Geboortenaam + Geb. naam partner

class GenderEnum(Enum):
    """Geslacht enum"""
    EMPTY = ""  # Empty value
    MAN = "M"  # Man
    ONBEKEND = "O"  # Onbekend
    VROUW = "V"  # Vrouw
    NON_BINAIR = "X"  # Non-binair

class NationalityEnum(Enum):
    """Nationaliteit enum"""
    EMPTY = ""  # Empty value
    ONBEKEND = "000"  # Onbekend
    NEDERLANDSE = "NL"  # Nederlandse
    ALGERIJNSE = "DZ"  # Algerijnse
    ANGOLESE = "AN"  # Angolese
    BURUNDESE = "RU"  # Burundese
    BOTSWAANSE = "RB"  # Botswaanse
    BURKINESE = "BU"  # Burkinese
    CENTRAAL_AFRIKAANSE = "RCA"  # Centraal-Afrikaanse
    COMORESE = "KM"  # Comorese
    KONGOLESE = "RCB"  # Kongolese
    BENINSE = "DY"  # Beninse
    EGYPTISCHE = "ET"  # Egyptische
    EQUATORIAALGUINESE = "EQ"  # Equatoriaalguinese
    ETHIOPISCHE = "ETH"  # Ethiopische
    DJIBOUTIAANSE = "DJI"  # Djiboutiaanse
    GABONESE = "GA"  # Gabonese
    GAMBIAANSE = "WAG"  # Gambiaanse
    GHANESE = "GH"  # Ghanese
    GUINESE = "GN"  # Guinese
    IVORIAANSE = "CI"  # Ivoriaanse
    KAAPVERDISCHE = "CV"  # Kaapverdische
    KAMEROENSE = "TC"  # Kameroense
    KENYAANSE = "EAK"  # Kenyaanse
    ZAIRESE = "CD"  # Zaïrese
    LESOTHAAANSE = "LS"  # Lesothaanse
    LIBERIAANSE = "LB"  # Liberiaanse
    LIBISCHE = "LAR"  # Libische
    MALAGASSISCHE = "RM"  # Malagassische
    MALAWISCHE = "MW"  # Malawische
    MALINESE = "RMM"  # Malinese
    MAROKKAANSE = "MA"  # Marokkaanse
    MAURITAANSE = "RIM"  # Mauritaanse
    MAURITIAANSE = "MS"  # Mauritiaanse
    MOZAMBIKAANSE = "MOC"  # Mozambikaanse
    NIGERESE = "RN"  # Nigerese
    NIGERIAANSE = "WAN"  # Nigeriaanse
    UGANDESE = "EAU"  # Ugandese
    GUINEE_BISSAUSE = "GW"  # Guinee-Bissause
    ZUID_AFRIKAANSE = "ZA"  # Zuid-Afrikaanse
    ESWATINISCHE = "SD"  # Eswatinische
    ZIMBABWAANSE = "ZW"  # Zimbabwaanse
    RWANDESE = "RWA"  # Rwandese
    BURGER_SAO_TOME_EN_PRINCIPE = "ST"  # Burger van São Tomé en Principe
    SENEGALESE = "SN"  # Senegalese
    SIERRA_LEOONSE = "WAL"  # Sierra Leoonse
    SOEDANESE = "SUD"  # Soedanese
    SOMALISCHE = "SP"  # Somalische
    TANZANIAANSE = "EAT"  # Tanzaniaanse
    TOGOLESE = "TG"  # Togolese
    TSJADISCHE = "TS"  # Tsjadische
    TUNESISCHE = "TN"  # Tunesische
    ZAMBIAANSE = "Z"  # Zambiaanse
    ZUID_SOEDANESE = "SS"  # Zuid-Soedanese
    BAHAMAANSE = "BS"  # Bahamaanse
    BELIZAANSE = "BH"  # Belizaanse
    CANADESE = "CDN"  # Canadese
    COSTA_RICAANSE = "CR"  # Costa Ricaanse
    CUBAANSE = "C"  # Cubaanse
    DOMINICAANSE = "DOM"  # Dominicaanse
    SALVADORAANSE = "EL"  # Salvadoraanse
    GUATEMALAANSE = "GCA"  # Guatemalaanse
    HAITIAANSE = "RH"  # Haïtiaanse
    HONDUREESE = "HON"  # Hondurese
    JAMAICAANSE = "JA"  # Jamaicaanse
    MEXICAANSE = "MEX"  # Mexicaanse
    NICARAGUAANSE = "NIC"  # Nicaraguaanse
    PANAMESE = "PA"  # Panamese
    BURGER_TRINIDAD_EN_TOBAGO = "TT"  # Burger van Trinidad en Tobago
    AMERIKAANS_BURGER = "USA"  # Amerikaans burger
    ARGENTIJNSE = "RA"  # Argentijnse
    BARBADAANSE = "BDS"  # Barbadaanse
    BOLIVIAANSE = "BOL"  # Boliviaanse
    BRAZILIAANSE = "BR"  # Braziliaanse
    CHILEENSE = "RCH"  # Chileense
    COLOMBIAANSE = "CO"  # Colombiaanse
    ECUADORAANSE = "EC"  # Ecuadoraanse
    GUYAANSE = "GUY"  # Guyaanse
    PARAGUAYAANSE = "PY"  # Paraguayaanse
    PERUAANSE = "PE"  # Peruaanse
    SURINAAMSE = "SME"  # Surinaamse
    URUGUAYAANSE = "ROU"  # Uruguayaanse
    VENEZOLAANSE = "YV"  # Venezolaanse
    GRENADAANSE = "WG"  # Grenadaanse
    BURGER_SAINT_KITTS_NEVIS = "KN"  # Burger van Saint Kitts-Nevis
    SLOWAAKSE = "SK"  # Slowaakse
    TSJECHISCHE = "CZ"  # Tsjechische
    BURGER_BOSNIE_HERZEGOVINA = "BA"  # Burger van Bosnië-Herzegovina
    GEORGISCHE = "GE"  # Georgische
    AFGHANSE = "AFG"  # Afghaanse
    BAHREINSE = "BRN"  # Bahreinse
    BHUTAANSE = "BT"  # Bhutaanse
    BURMAANSE = "BM"  # Burmaanse
    BRUNEISE = "BRU"  # Bruneise
    CAMBODJAANSE = "K"  # Cambodjaanse
    SRI_LANKAAANSE = "CL"  # Sri Lankaanse
    CHINESE = "CN"  # Chinese
    CYPRISCHE = "CY"  # Cyprische
    FILIPIJNSE = "RP"  # Filipijnse
    TURKMEENSE = "TMN"  # Turkmeense
    TAIWANESE = "RC"  # Taiwanese
    INDIASE = "IND"  # Indiase
    INDONESISCHE = "RI"  # Indonesische
    IRAKSE = "IRQ"  # Iraakse
    IRAANSE = "IR"  # Iraanse
    ISRAELISCHE = "IL"  # Israëlische
    JAPANSE = "J"  # Japanse
    JORDAANSE = "HKJ"  # Jordaanse
    TADZJIEKSE = "TAD"  # Tadzjiekse
    KOEWEITSE = "KWT"  # Koeweitse
    LAOTIAANSE = "LAO"  # Laotiaanse
    LIBANESE = "RL"  # Libanese
    MALDIVISCHE = "MV"  # Maldivische
    MALEISISCHE = "MAL"  # Maleisische
    MONGOLISCHE = "MON"  # Mongolische
    OMAANSE = "OMA"  # Omaanse
    NEPALESE = "NPL"  # Nepalese
    NOORD_KOREANSE = "KO"  # Noord-Koreaanse
    OEZBEKSE = "OEZ"  # Oezbeekse
    PAKISTAANSE = "PK"  # Pakistaanse
    QATARESE = "QA"  # Qatarese
    SAOEDI_ARABISCHE = "AS"  # Saoedi-Arabische
    SINGAPORESE = "SGP"  # Singaporese
    SYRISCHE = "SYR"  # Syrische
    THAISE = "T"  # Thaise
    BURGER_VER_ARABISCHE_EMIRATEN = "AE"  # Burger van de Ver. Arabische Emiraten
    TURKSE = "TR"  # Turkse
    OEKRAINSE = "UA"  # Oekraïense
    ZUID_KOREANSE = "ROK"  # Zuid-Koreaanse
    VIETNAMESE = "VN"  # Vietnamese
    BENGALESE = "BD"  # Bengalese
    KIRGIZISCHE = "KG"  # Kirgizische
    MOLDAVISCHE = "MD"  # Moldavische
    KAZACHSE = "KZ"  # Kazachse
    BELARUSSISCHE = "BY"  # Belarussische
    AZERBEIDZJAANSE = "AZ"  # Azerbeidzjaanse
    ARMEENSE = "AM"  # Armeense
    AUSTRALISCHE = "AUS"  # Australische
    PAPOEA_NIEUW_GUINESE = "PNG"  # Papoea-Nieuw-Guinese
    NIEUW_ZEELANDSE = "NZ"  # Nieuw-Zeelandse
    WEST_SAMOAAANSE = "WSM"  # West-Samoaanse
    SAMOAAANSE = "WS"  # Samoaanse
    RUSSISCHE = "RUS"  # Russische
    SLOVEENSE = "SLO"  # Sloveense
    BURGER_ANTIGUA_EN_BARBUDA = "AG"  # Burger van Antigua en Barbuda
    VANUATUAANSE = "VU"  # Vanuatuaanse
    FIJISCHE = "FJI"  # Fijische
    BURGER_BRITSE_AFHANKELIJKE_GEBIEDEN = "GB4"  # Burger van Britse afhankelijke gebieden
    KROATISCHE = "HR"  # Kroatische
    TONGAANSE = "TO"  # Tongaanse
    NAURUAANSE = "NR"  # Nauruaanse
    PALAUSE = "PLW"  # Palause
    AMERIKAANS_ONDERDAAN = "USA"  # Amerikaans onderdaan
    LETSE = "LV"  # Letse
    SALOMONSEILANDSE = "SB"  # Salomonseilandse
    MICRONESISCHE = "MIC"  # Micronesische
    SEYCHELSE = "SY"  # Seychelse
    KIRIBATISCHE = "KIR"  # Kiribatische
    TUVALUAANSE = "TV"  # Tuvaluaanse
    SAINT_LUCIAANSE = "WL"  # Saint Luciaanse
    BURGER_DOMINICA = "WD"  # Burger van Dominica
    BURGER_SAINT_VINCENT_EN_DE_GRENADINES = "WV"  # Burger van Saint Vincent en de Grenadines
    ESTISCHE = "EE"  # Estische
    BRITISH_NATIONAL_OVERSEAS = "IOT"  # British National (overseas)
    BURGER_DEMOCRATISCHE_REPUBLIEK_CONGO = "ZRE"  # Burger van Democratische Republiek Congo
    BURGER_TIMOR_LESTE = "TLS"  # Burger van Timor Leste
    BURGER_SERVIE_EN_MONTENEGRO = "SCG"  # Burger van Servië en Montenegro
    SERVISCHE = "SRB"  # Servische
    MONTENEGRIJNSE = "MNE"  # Montenegrijnse
    LITOUWSE = "LT"  # Litouwse
    MARSHALLEILANDSE = "MAR"  # Marshalleilandse
    MYANMARESE = "BUR"  # Myanmarese
    NAMIBISCHE = "SWA"  # Namibische
    VLUCHTELING = "GRF"  # Vluchteling
    STAATLOOS = "499"  # Staatloos
    ALBANESE = "AL"  # Albanese
    ANDORRESE = "AND"  # Andorrese
    BELGISCHE = "B"  # Belgische
    BULGAARSE = "BG"  # Bulgaarse
    DEENSE = "DK"  # Deense
    DUITSE = "D"  # Duitse
    FINSE = "FIN"  # Finse
    FRANSE = "F"  # Franse
    JEMENITISCHE = "YMN"  # Jemenitische
    GRIEKSE = "GR"  # Griekse
    BRITS_BURGER = "GB"  # Brits burger
    HONGAARSE = "H"  # Hongaarse
    IERSE = "IRL"  # Ierse
    IJSLANDSE = "IS"  # IJslandse
    ITALIAANSE = "I"  # Italiaanse
    JOEGOSLAVISCHE = "YU"  # Joegoslavische
    LIECHTENSTEINSE = "FL"  # Liechtensteinse
    LUXEMBURGSE = "L"  # Luxemburgse
    MALTESE = "M"  # Maltese
    MONEASKISCHE = "MC"  # Monegaskische
    NOORSE = "N"  # Noorse
    OOSTENRIJKSE = "A"  # Oostenrijkse
    POOLSE = "PL"  # Poolse
    PORTUGESE = "P"  # Portugese
    ROEMEENSE = "RO"  # Roemeense
    SAN_MARINESE = "RSM"  # San Marinese
    SPAANSE = "E"  # Spaanse
    VATICAANSE = "VAT"  # Vaticaanse
    ZWEEDSE = "S"  # Zweedse
    ZWITSERSE = "CH"  # Zwitserse
    BRITS_ONDERDAAN = "GB2"  # Brits onderdaan
    ERITRESE = "ERI"  # Eritrese
    STAATSBURGER_BRITSE_OVERZEESE_GEBIEDSDELEN = "GB3"  # Staatsburger van de Britse overzeese gebiedsdelen
    KOSOVAARSE = "XK"  # Kosovaarse
    BURGER_REPUBLIEK_NOORD_MACEDONIE = "MK"  # Burger van de Republiek Noord-Macedonië
    PALESTIJN = "PSE"  # Palestijn
    ALAND_ISLANDS = "AX"  # Åland Islands

class MaritalStatusEnum(Enum):
    """Burgerlijke staat enum"""
    EMPTY = ""  # Empty value
    DUURZAAM_GESCHEIDEN = "DZ"  # Duurzaam gescheiden
    GEHUWD = "GH"  # Gehuwd
    GEREGISTREERD_PARTNERSCHAP = "GP"  # Geregistreerd partnerschap
    GESCHEIDEN = "GS"  # Gescheiden
    ONGEHUWD = "OG"  # Ongehuwd
    OVERIG = "OV"  # Overig
    WEDUWE_WEDUWNAAR = "WE"  # Weduwe/Weduwnaar
    SAMENWONEND = "SW"  # Samenwonend
    SAMENLEVINGSCONTRACT = "SC"  # Samenlevingscontract

class PreferredMediumEnum(Enum):
    """Voorkeursmedium enum"""
    EMPTY = ""  # Empty value
    EMAIL = "EMA"  # E-mail
    FAX = "FAX"  # Fax
    PERSOONLIJK = "PRS"  # Persoonlijk
    POST = "PST"  # Post
    TELEFOON = "TEL"  # Telefoonnr.

class AmountOfEmployeesEnum(Enum):
    """Aantal medewerkers enum"""
    EMPTY = ""  # Empty value
    ZERO = "01"  # 01 = 0
    ONE = "02"  # 02 = 1
    TWO_TO_FOUR = "03"  # 03 = 2-4
    FIVE_TO_NINE = "04"  # 04 = 5-9
    TEN_TO_NINETEEN = "05"  # 05 = 10-19
    TWENTY_TO_FORTYNINE = "06"  # 06 = 20-49
    FIFTY_TO_NINETYNINE = "07"  # 07 = 50-99
    HUNDRED_TO_ONENINETYNINE = "08"  # 08 = 100-199
    TWOHUNDRED_TO_FOURNINETYNINE = "09"  # 09 = 200-499
    FIVEHUNDRED_TO_SEVENFORTYNINE = "10"  # 10 = 500-749
    SEVENFIFTY_TO_NINENINETYNINE = "11"  # 11 = 750-999
    THOUSAND_AND_MORE = "12"  # 12 = 1000 en meer

# Organisation-related enums
class MatchOrganisationEnum(IntEnum):
    """Organisatie vergelijken op enum"""
    EMPTY = -1  # Empty value
    ZOEK_OP_BCCO = 0  # Zoek op BcCo
    KVK_NUMMER = 1  # KvK-nummer
    FISCAAL_NUMMER = 2  # Fiscaal nummer
    NAAM = 3  # Naam
    ADRES = 4  # Adres
    POSTADRES = 5  # Postadres
    ALTIJD_NIEUW_TOEVOEGEN = 6  # Altijd nieuw toevoegen

class LegalStructureEnum(IntEnum):
    """Rechtsvorm enum"""
    EMPTY = -1  # Empty value
    NIET_VASTGESTELD = 999  # Niet vastgesteld
    PRIVE_PERSOON = 0  # Privé persoon
    CODE_NOG_NIET_VASTGESTELD = 1  # (code nog niet vastgesteld)
    EENMANSZAAK = 5  # Eenmanszaak
    REDERIJ = 10  # Rederij
    MAATSCHAP = 15  # Maatschap
    VENNOOTSCHAP_ONDER_FIRMA = 20  # Vennootschap onder firma
    COMMANDITAIRE_VENNOOTSCHAP = 25  # Commanditaire vennootschap
    BESLOTEN_VENNOOTSCHAP = 30  # Besloten vennootschap
    NAAMLOZE_VENNOOTSCHAP = 35  # Naamloze vennootschap
    COOPERATIE = 40  # Coöperatie
    VERENIGING = 45  # Vereniging
    KERKGENOOTSCHAP = 50  # Kerkgenootschap
    STICHTING = 55  # Stichting
    ONDERLINGE_WAARBORGMAATSCHAPPIJ = 60  # Onderlinge waarborgmaatschappij
    BUITENLANDSE_RECHTSVORM = 70  # Buitenlandse rechtsvorm cq onderneming
    NEVENVESTIGING_MET_VESTIGING_IN_NL = 71  # Nevenvestiging met vestiging in NL
    EUROPEES_ECONOMISCH_SAMENWERKINGSVERBAND = 80  # Europees economisch samenwerkingsverband
    BUITENLANDSE_EG_VENNOOT_MET_ONDERNEMING_IN_NL = 81  # Buitenlandse EG-vennoot met onderneming in NL
    BUITENLANDSE_EG_VENNOOT_MET_HOOFDONDERNEMING_IN_NL = 82  # Buitenlandse EG-vennoot met hoofdonderneming in NL
    BUITENLANDSE_OP_EG_VENNOOT_LIJKENDE_ONDERNEMING_IN_NL = 83  # Buitenlandse op EG-vennoot lijkende ondern. in NL
    BUITENLANDSE_OP_EG_VENNOOT_LIJKENDE_HOOFDONDERNEMING_IN_NL = 84  # Buitenlandse op EG-vennoot lijkende hfd.ond. in NL
    OVERIGE = 99  # Overige

class BrancheEnum(IntEnum):
    """Branche enum"""
    EMPTY = -1  # Empty value
    LANDBOUW_JACHT_BOSBOUW_VISSERIJ_EN_DELFSTOFFEN = 100  # Landbouw, jacht, bosbouw, visserij en delfstoffen
    INDUSTRIE = 200  # Industrie
    BOUWNIJVERHEID = 300  # Bouwnijverheid
    GROOTHANDEL = 400  # Groothandel
    DETAILHANDEL = 500  # Detailhandel
    HORECA = 600  # Horeca
    VERVOER_TELECOMMUNICATIE = 700  # Vervoer, telecommunicatie
    BANK_VERZEKERINGSWEZEN_EN_ONROEREND_GOED = 800  # Bank-, verzekeringswezen en onroerend goed
    VERHUUR = 900  # Verhuur
    COMPUTER_EN_INFORMATIETECHNOLOGIE = 1000  # Computer en informatietechnologie
    ADMINISTRATIE_EN_ACCOUNTANTSKANTOREN = 1100  # Administratie- en accountantskantoren
    OVERIGE_ZAKELIJKE_DIENSTVERLENING = 1200  # Overige zakelijke dienstverlening
    OVERHEID = 1300  # Overheid
    ONDERWIJS = 1400  # Onderwijs
    GEZONDHEIDSZORG_EN_WELZIJN = 1500  # Gezondheidszorg en welzijn
    MILIEU_CULTUUR_SPORT_EN_RECREATIE = 1600  # Milieu, cultuur, sport en recreatie

# Contact-related enums
class ContactType(Enum):
    """Contact type enum"""
    EMPTY = ""  # Empty value
    AFD = "AFD"  # Afdeling bij organisatie
    PRS = "PRS"  # Persoon bij organisatie
    AFL = "AFL"  # Afleveradres
    ORG = "ORG"  # Organisatie
    PER = "PER"  # Persoon

class FunctionType(IntEnum):
    """Function type enum"""
    EMPTY = -1  # Empty value
    DIRECTEUR = 100  # Directeur
    ADMINISTRATIEF_MEDEWERKER = 200  # Administratief medewerker
    HOOFD_SALARISADMINISTRATIE = 300  # Hoofd salarisadministratie

# Title-related enums
class TitleEnum(Enum):
    """Titel/aanhef enum"""
    # General titles
    EMPTY = ""  # Empty value
    ALG = "ALG"  # Algemeen
    BA = "BA"  # Bachelor of Arts
    BRN = "BRN"  # Baron/Barones
    BSc = "BSc"  # Bachelor of Science
    DIV = "DIV"  # Diversen
    DR = "DR"  # Doctor
    DRS = "DRS"  # Doctorandus
    DU = "DU"  # Algemeen Duits
    DUI = "DUI"  # Duitse aanhef
    EN = "EN"  # Algemeen Engels
    ENG = "ENG"  # Engelse aanhef
    ERV = "ERV"  # Erven
    FR = "FR"  # Algemeen Frans

    # Professional titles
    GRF = "GRF"  # Graaf
    ING = "ING"  # Ingenieur (HBO)
    IR = "IR"  # Ingenieur
    MA = "MA"  # Master of Arts
    MR = "MR"  # Meester
    MSc = "MSc"  # Master of Science
    ONB = "ONB"  # Geslacht onbekend
    PRF = "PRF"  # Professor
    RA = "RA"  # Register accountant
    RH = "RH"  # Raadsheer
    RTR = "RTR"  # Rechter
    ZR = "ZR"  # Zuster

# Bank account-related enums
class CodeDoorberekening(IntEnum):
    """Definieert de toegestane codes voor doorberekening van kosten."""
    EMPTY = -1  # Empty value
    ALLE_KOSTEN_BEGUNSTIGDE = 0  # Alle kosten ten laste van de begunstigde
    ALLE_KOSTEN_OPDRACHTGEVER = 1  # Alle kosten ten laste van de opdrachtgever
    GEDEELDE_KOSTEN = 2  # Gedeelde kosten

class deliveryCondition(IntEnum):
    """Leveringsconditie"""
    EMPTY = -1  # Empty value
    DEELLEVERING_TOESTAAN = 0  # Deellevering toestaan
    REGEL_VOLLEDIG_ULEVEREN = 1  # Regel volledig uitleveren
    ORDER_VOLLEDIG_ULEVEREN = 2  # Order volledig uitleveren
    GEEN_BACKORDERS_LEVEREN = 3  # Geen backorders leveren

class deliveryMethod(Enum):
    EMPTY = ""  # Empty value
    AFDRUKKEN = "A"
    AFDRUKKEN_EMAIL_PDF = "B"
    FACTUREN_PEPPOL_OVERIGE_RAPPORTEN_EMAIL_PDF = "C"
    EMAIL_PDF_EFACTUUR_DICO = "D"
    EMAIL_PDF = "E"
    EVERBINDING_UBL = "F"
    XML_ORDER = "M"
    PORTAL_EMAIL = "O"
    AFDRUKKEN_VERSTUREN_VIA_EDI = "P"
    FACTUUR = "Q"

class barcodeType(IntEnum):
    """Barcode type enum"""
    EMPTY = -1  # Empty value
    GEEN_CONTROLE = 0  # Geen controle
    EAN8 = 1  # Barcode EAN8
    UPC = 2  # Barcode UPC
    EAN13 = 3  # Barcode EAN13
    EAN14 = 4  # Barcode EAN14
    SSCC = 5  # Barcode SSCC
    CODE_128 = 6  # Code 128
    INTERLEAVED_2_5 = 7  # Interleaved 2/5
    INTERLEAVED_2_5_CONTROLEGETAL = 8  # Interleaved 2/5 (controlegetal)

class ProcessingMethod(IntEnum):
    """Verwerking order enum"""
    EMPTY = -1  # Empty value
    PAKBON_FACTUUR_NA_LEVERING = 1  # Pakbon, factuur na levering
    PAKBON_EN_FACTUUR = 2  # Pakbon en factuur
    FACTUUR_LEVERING_NA_VOORUITBETALING = 3  # Factuur, levering na vooruitbetaling
    PAKBON_GEEN_FACTUUR = 4  # Pakbon, geen factuur
    PAKBON_FACTUUR_VIA_NACALCULATIE = 5  # Pakbon, factuur via nacalculatie
    PAKBON_EN_FACTUUR_NIET_AFDRUKKEN_OF_VERZENDEN = 6  # Pakbon en factuur, factuur niet afdrukken of verzenden
    AANBETALEN_LEVERING_NA_AANBETALING = 7  # Aanbetalen, levering na aanbetaling

class collectionMethod(Enum):
    """Incassowijze SEPA"""
    EMPTY = ""  # Empty value
    B2B = "B"      # B2B
    STANDAARD = "S"  # Standaard

class saleRelationType(Enum):
    """Type verkooprelatie: 001 = Brons; 002 = Zilver; 003 = Goud"""
    EMPTY = ""  # Empty value
    BRONS = "001"
    ZILVER = "002"
    GOUD = "003"

# Employee-related enums
class StatusEnum(Enum):
    """Status enum for employee"""
    EMPTY = ""  # Empty value
    IN_DIENST = "I"  # In dienst
    SOLLICITANT = "S"  # Sollicitant
    UIT_DIENST = "U"  # Uit dienst

class StartPhaseEnum(Enum):
    """Startfase enum for employee"""
    EMPTY = ""  # Empty value
    FASE_1 = "1"  # Fase 1
    FASE_1_2 = "12"  # Fase 1-2
    FASE_2 = "2"  # Fase 2
    FASE_3 = "3"  # Fase 3
    FASE_4 = "4"  # Fase 4
    FASE_A = "A"  # Fase A
    FASE_B = "B"  # Fase B
    FASE_C = "C"  # Fase C
    GEEN_FASETELLING = "G"  # Geen fasetelling

class PaymentFrequencyEnum(Enum):
    """Betalingsfrequentie enum for employee"""
    EMPTY = ""  # Empty value
    VIER_WEKEN = "4W"  # 4 weken
    PERIODE = "P"  # Periode

class PayslipDistributionEnum(Enum):
    """Payslip distributie enum for employee"""
    EMPTY = ""  # Empty value
    AFDRUKKEN = "A"  # Afdrukken
    AFDRUKKEN_EN_BERICHT = "B"  # Afdrukken en bericht
    BERICHT = "E"  # Bericht
    NIET_AFDRUKKEN_GEEN_BERICHT = "N"  # Niet afdrukken/Geen bericht

class AnnualStatementDistributionEnum(Enum):
    """Verstrekking jaaropgave enum for employee"""
    EMPTY = ""  # Empty value
    AFDRUKKEN = "A"  # Afdrukken
    AFDRUKKEN_EN_BERICHT = "B"  # Afdrukken en bericht
    BERICHT = "E"  # Bericht
    NIET_AFDRUKKEN_GEEN_BERICHT = "N"  # Niet afdrukken/Geen bericht

class EmailEnum(Enum):
    """E-mail voor digitale documenten enum for employee"""
    EMPTY = ""  # Empty value
    PRIVATE = "P"  # Privé e-mailadres
    BUSINESS = "Z"  # Zakelijk e-mailadres

class TransitionEnum(Enum):
    """Overgangsregeling 2022 enum for employee"""
    EMPTY = ""  # Empty value
    NOG_TE_BEPALEN = "1"  # Nog te bepalen d.m.v. jaarloon BT
    GEEN_OVERGANGSREGELING = "2"  # Geen overgangsregeling
    OVERGANGSREGELING_FASE_A_1_2 = "3"  # Overgangsregeling Fase A/1-2
    OVERGANGSREGELING_FASE_B_3 = "4"  # Overgangsregeling Fase B/3

class ContractTypeEnum(Enum):
    """Type contract enum"""
    EMPTY = ""  # Empty value
    ONBEPAALDE_TIJD = "O"  # Onbepaalde tijd
    HALFJAARCONTRACT = "H"  # Halfjaarcontract
    JAARCONTRACT = "J"  # Jaarcontract
    BEPAALDE_TIJD = "B"  # Bepaalde tijd
    ANDERHALF_JAAR = "AJ"  # Anderhalf jaar
    ZEVEN_MAANDEN = "7M"  # 7 maanden contract
    ACHT_MAANDEN = "8M"  # 8 maanden contract
    NEGEN_MAANDEN = "9M"  # 9 maanden contract

class EmployeeTypeEnum(Enum):
    """Soort medewerker enum"""
    EMPTY = ""  # Empty value
    PERSONEELSLID = "1"  # Personeelslid
    TRANSITIEVERGOEDING = "T"  # Transitievergoeding
    UITZENDKRACHT = "2"  # Uitzendkracht
    VAN_ANDER_BEDRIJF_INGELEEND = "3"  # Van ander bedrijf/filiaal ingeleend
    ONDERNEMER_MET_SALARIS = "4"  # Ondernemer - met salaris
    ONDERNEMER_ZONDER_SALARIS = "5"  # Ondernemer - zonder salaris
    STAGIAIR_MET_SALARIS = "6"  # Stagiair - met salaris/stagevergoeding
    STAGIAIR_ZONDER_SALARIS = "7"  # Stagiair - zonder salaris
    NABETALING_NA_UITDIENST = "N"  # Nabetaling na uitdienst
    INTERIMMER = "8"  # Interimmer
    EXPAT = "E"  # Expat

class EmploymentCodeEnum(Enum):
    """Dienstbetrekking enum"""
    EMPTY = ""  # Empty value
    FULLTIMER = "F"  # Fulltimer
    PARTTIMER = "P"  # Parttimer
    OPROEPKRACHT = "O"  # Oproepkracht
    STAGIAIR = "S"  # Stagiair
    HULPKRACHT = "H"  # Hulpkracht
    VAKANTIEWERKER = "V"  # Vakantiewerker
    UITZENDKRACHT = "U"  # Uitzendkracht

class OutOfServiceReasonEnum(Enum):
    """Reden ontslag enum"""
    EMPTY = ""  # Empty value
    BETREKKING_ELDERS = "0"  # Betrekking elders
    ONTSLAG = "1"  # Ontslag
    ONTSLAG_STAANDE_VOET = "2"  # Ontslag staande voet
    ONTEVREDEN_ARBEIDSVOORWAARDEN = "3"  # Ontevreden arbeidsvoorwaarden
    ONTEVREDEN_WERKSFEER = "4"  # Ontevreden werksfeer
    PENSIOEN = "5"  # Pensioen
    VUT = "6"  # VUT
    ARBEIDSONGESCHIKT = "7"  # Arbeidsongeschikt
    ONBETAALD_VERLOF = "8"  # Onbetaald verlof
    OVERLIJDEN = "9"  # Overlijden
    OVERNAME_NIET_AFREKENEN = "O"  # Overname, niet afrekenen

class TerminationInitiatedByEnum(Enum):
    """Ontslag geïnitieerd door enum"""
    EMPTY = ""  # Empty value
    MEDEWERKER = "M"  # Medewerker
    WERKGEVER = "W"  # Werkgever
    ONDERLING_AKKOORD = "O"  # Onderling akkoord

class ProbationPeriodEnum(Enum):
    """Proeftijd enum"""
    EMPTY = ""  # Empty value
    EEN_MAAND = "1M"  # Een maand
    TWEE_MAANDEN = "2M"  # Twee maanden
    OVERIG = "OM"  # Overig
    EEN_HALFJAAR = "6M"  # Een halfjaar
    EEN_JAAR = "12M"  # Een jaar
    NEGEN_MAANDEN = "9M"  # Negen maanden
    GEEN = "NM"  # Geen
    TWEE_WEKEN = "2W"  # Twee weken
    DRIE_MAANDEN = "3M"  # Drie maanden

class EmploymentStartReasonEnum(Enum):
    """Reden in dienst enum"""
    EMPTY = ""  # Empty value
    AANSLUITING_INSTELLING = "AAN"  # Aansluiting instelling
    INDIENST_TREDEN = "IND"  # Indienst treden
    HERVATTEN_NA_ONBETAALD_VERLOF = "OBV"  # Hervatten na onbetaald verlof
    HERVATTEN_NA_WIA = "REV"  # Hervatten na WIA
    OVERIGE_REDENEN = "OVR"  # Overige redenen

class TerminationReasonEnum(Enum):
    """Reden uit dienst (TKP Vervoer) enum"""
    EMPTY = ""  # Empty value
    REGULIER_ONTSLAG_VUT = "31"  # Regulier ontslag met ingang VUT
    EINDE_DIENSTVERBAND_OVERLIJDEN = "34"  # Einde dienstverband ivm overlijden
    REGULIER_ONTSLAG_PREPENSIOEN = "36"  # Regulier ontslag met ingang prepensioen
    EINDE_DIENSTVERBAND_REGULIER = "4"  # Einde dienstverband (regulier ontslag)
    EINDE_DIENSTVERBAND_PREMIEVRIJE_VOORTZETTING = "41"  # Einde dienstverband met premievrije voortzetting AO

class WorkRelationTypeEnum(Enum):
    """Aard arbeidsrelatie enum"""
    EMPTY = ""  # Empty value
    VAST = "1"  # Vast
    BEPAALDE_TIJD = "2"  # Bepaalde tijd
    BEPAALDE_TIJD_VERVANGING = "3"  # Bepaalde tijd i.v.m. vervanging.
    TEWERKSTELLING_ZONDER_BENOEMING = "4"  # Tewerkstelling zonder benoeming

class FundingSourceEnum(Enum):
    """Financieringsbron enum"""
    EMPTY = ""  # Empty value
    REGULIER = "1"  # Regulier
    VERGOEDINGEN_VERVANGINGSFONDS = "2"  # Vergoedingen door Vervangingsfonds
    LOONKOSTENSUBSIDIE = "3"  # Loonkostensubsidie
    OVERIGE_MIDDELEN = "4"  # Overige middelen
    RISICOFONDS = "5"  # Risicofonds

class InsuranceEnum(Enum):
    """Verzekering enum"""
    EMPTY = ""  # Empty value
    GEEN = "00"  # Geen
    VF_VERPLICHT = "01"  # VF Verplicht
    VF_VRIJWILLIG = "02"  # VF Vrijwillig
    RISICOFONDS = "03"  # Risicofonds

class PeriodicRaiseBehaviorEnum(Enum):
    """Gedrag periodiek toekennen enum"""
    EMPTY = ""  # Empty value
    GEEN_PERIODIEKE_VERHOGING = "0"  # Geen periodieke verhoging
    VOLGENS_LOONSCHALEN = "1"  # Volgens loonschalen
    AFWIJKENDE_FACTOR_MIN_MAX_LOONSCHAAL = "2"  # Afwijkende factor min/max-loonschaal
    VERHOGING_MET_BEDRAG = "3"  # Verhoging met bedrag
    VERHOGING_MET_PERCENTAGE = "4"  # Verhoging met percentage
    VERHOGING_PERCENTAGE_TOV_MAX = "5"  # Verhoging met percentage t.o.v. max (Min/max-loonschaal)
    VERHOGING_PERCENTAGE_TOV_MIDDEN = "6"  # Verhoging met percentage t.o.v. midden (min/max-loonschaal)

class EmploymentPhaseClassificationEnum(Enum):
    """Employment phase classification enum"""
    EMPTY = ""  # Empty value
    ONBEKEND_NVT = "O"  # Onbekend of n.v.t.
    FASE_1_MET_UITZENDBEDING = "1"  # Fase 1 met uitzendbeding (t/m 2019)
    FASE_1_2_MET_UITZENDBEDING = "12"  # Fase 1-2 met uitzendbeding
    FASE_1_2_ZONDER_UITZENDBEDING = "13"  # Fase 1-2 zonder uitzendbeding
    FASE_1_2_ZONDER_UITZENDBEDING_UITSLUITING = "14"  # Fase 1-2 zonder uitzendbeding, met uitsluiting van loondoorbetalingsverplichting
    FASE_A_MET_UITZENDBEDING = "AU"  # Fase A met uitzendbeding
    FASE_B = "B"  # Fase B
    FASE_C = "C"  # Fase C
    FASE_2_MET_UITZENDBEDING = "2"  # Fase 2 met uitzendbeding (t/m 2019)
    FASE_3 = "3"  # Fase 3
    FASE_A_ZONDER_UITZENDBEDING_UITSLUITING = "AZU"  # Fase A zonder uitzendbeding, met uitsluiting van loondoorbetalingsverplichting
    FASE_4 = "4"  # Fase 4
    FASE_A_ZONDER_UITZENDBEDING = "AZ"  # Fase A zonder uitzendbeding
    FASE_1_ZONDER_UITZENDBEDING = "41"  # Fase 1 zonder uitzendbeding (t/m 2019)
    FASE_2_ZONDER_UITZENDBEDING = "42"  # Fase 2 zonder uitzendbeding (t/m 2019)
    FASE_1_ZONDER_UITZENDBEDING_UITSLUITING = "43"  # Fase 1 zonder uitzendbeding, met uitsluiting van loondoorbetalingsverplichting (t/m 2019)
    FASE_2_ZONDER_UITZENDBEDING_UITSLUITING = "44"  # Fase 2 zonder uitzendbeding, met uitsluiting van loondoorbetalingsverplichting (t/m 2019)
    WETTELIJK_REGIME = "W"  # Wettelijk regime
    KETENSYSTEEM = "K"  # Ketensysteem

class FlexEmploymentEndReasonEnum(Enum):
    """Reden einde inkomstenverhouding flexwerker enum"""
    EMPTY = ""  # Empty value
    NIET_VAN_TOEPASSING = "0"  # Niet van toepassing
    EINDE_WERK_GEEN_WERK_AANGEBODEN = "1"  # Einde werk/einde contract, geen werk aangeboden
    EINDE_WERK_WERK_AANGEBODEN = "2"  # Einde werk/einde contract, werk aangeboden
    GEEN_EINDE_WERK_LOPEND_CONTRACT = "3"  # Geen einde werk/einde contract; lopend arbeidscontract
    INLENER_OPDRACHT_INGETROKKEN = "4"  # Inlener heeft opdracht ingetrokken
    UITZENDKRACHT_ONTSLAG_GENOMEN = "5"  # Uitzendkracht heeft ontslag genomen
    EINDE_WERK_WEGENS_ZIEKTE = "6"  # Einde werk/einde contract wegens ziekte

class ChainEnum(Enum):
    """Ketennummer enum"""
    EMPTY = ""  # Empty value
    NIET_VAN_TOEPASSING = "0"  # Niet van toepassing
    BEPAALDE_TIJD_1 = "1"  # Bepaalde tijd 1
    BEPAALDE_TIJD_2 = "2"  # Bepaalde tijd 2
    BEPAALDE_TIJD_3 = "3"  # Bepaalde tijd 3
    BEPAALDE_TIJD_4 = "4"  # Bepaalde tijd 4
    BEPAALDE_TIJD_5 = "5"  # Bepaalde tijd 5
    BEPAALDE_TIJD_6 = "6"  # Bepaalde tijd 6
    NOG_TE_BEPALEN = "Ntb"  # Nog te bepalen

class EducationLevelEnum(Enum):
    """Opleidingsgraad enum"""
    EMPTY = ""  # Empty value
    LAGER_ONDERWIJS_ONBRUIKBAAR = "1"  # (Onbruikbaar Vanaf 01/04/2006)Lager Onderwijs
    LAGER_ONDERWIJS_OF_GEEN = "11"  # Lager Onderwijs Of Geen Onderwijs
    LAGER_SEC_BUSO = "12"  # Lager Sec. Ond./Buso 1,2,3/Dt Lager Sec.Beroepsond
    SECUNDAIR_ONDERWIJS_ONBRUIKBAAR = "2"  # (Onbruikbaar Vanaf 01/04/2006)Secundair Onderwijs
    TWEEDE_JR_3E_GR_BSO = "21"  # 2e Jr. 3e Gr. Bso + 3e Jr. 3e Gr. Bso Z. Gts. Hso
    DERDE_GR_TSO_KSO_BSO = "22"  # 3 Gr.Tso,Kso+Bso Spec.Jr Gts Hso/Buso4 Dip/Gts Hso
    DERDE_GRAAD_ASO = "23"  # 3e Graad Aso
    DEELTIJDS_TECHNISCH = "24"  # Deeltijds Technisch Onderwijs
    DEELTIJDS_BSO_HOGER = "25"  # Deeltijds Bso Hoger Middelbaar
    BUSO_4_ZONDER_DIPLOMA = "26"  # Buso 4 Zonder Getuigschrift Of Diploma Hso
    ZEVENDE_JR_BSO = "27"  # 7E JR BSO MET DIP SO/GTS HSO//>=1E J 4E GR BSO
    HOGER_NIET_UNIV_ONBRUIKBAAR = "3"  # (Onbruikbaar Vanaf 01/04/06)Hoger Niet Univ Onderw
    HOGER_NIET_UNIV_KORT = "31"  # Hoger Niet-Universitair Onderwijs Korte Type
    HOGER_NIET_UNIV_LANG = "32"  # Hoger Niet-Universitair Onderwijs Lange Type
    HOGER_UNIV_ONBRUIKBAAR = "4"  # (Onbruikbaar Vanaf 01/04/06) Hoger Univ Onderwijs
    UNIVERSITAIR = "41"  # Universitair Onderwijs
    POST_UNIVERSITAIR = "42"  # Post-Universitair Onderwijs
    DOCTORAAT = "43"  # Doctoraat Met Proefschrift

class ContractSpecificationEnum(Enum):
    """Precisering contract enum"""
    EMPTY = ""  # Empty value
    GEWONE_MEDEWERKER = "1"  # Gewone medewerker
    INTERIMAIR = "10"  # Interimair
    LEERLING_STAGIAIR_LANG = "11"  # Leerling stagiair (>60 dagen)
    LEERLING_STAGIAIR = "12"  # Leerling stagiair
    CANADA_DRY_PLAN = "13"  # "Canada dry" plan
    NIET_VERBLIJFHOUDER = "14"  # Niet verblijfhouder
    BRUGPENSIOEN_OUD = "15"  # Brugpensioen oud stelsel
    BRUGPENSIOEN_NIEUW = "16"  # Brugpensioen nieuw stelsel
    BUITENLANDSE_BESTUURDER = "17"  # Buitenlandse bestuurder
    GEHANDICAPTE_MEDEWERKER = "18"  # Gehandicapte medewerker
    BRUGPENSIOEN_HALFTIJDS = "19"  # Brugpensioen half-tijds
    GEPENSIONEERDE_MEDEWERKER = "2"  # Gepensioneerde medewerker
    INSTAPSTAGE = "20"  # Instapstage (TRI)
    BEROEPSVORMING_RVA = "21"  # Beroepsvorming - RVA
    GESUBSIDIEERD_CONTRACTUEEL = "22"  # Gesubsidieerd contractueel
    ARTIEST_MUZIKANT = "23"  # Artiest of muzikant (specifieke categorie)
    INDUSTRIELE_LEERLING = "24"  # Industriële leerling
    LEERLING_ONDERNEMINGSHOOFD = "25"  # Leerling ondernemingshoofd
    KB_498 = "26"  # K.B. 498
    KB_495_MIN_18 = "27"  # K.B. 495 (-18 jaar)
    PROGRAMMA_WET = "28"  # Programma Wet (# 1e aangeworven)
    KB_483 = "29"  # K.B. 483
    STAGAIR = "3"  # Stagair
    WERKENDE_VENNOOT = "30"  # Werkende vennoot
    STATUTAIR = "31"  # Statutair
    BEGELEIDINGSPLAN_WERKLOZE = "32"  # Begeleidingsplan werkloze
    JONGE_WERKLOZE_26_6M = "33"  # Jonge werkloze <26 jaar 6m
    JONGE_WERKLOZE_26_9M = "34"  # Jonge werkloze <26 jaar 9m
    JONGE_WERKLOZE_KB_495 = "35"  # Jonge werkloze K.B. 495
    INGROEI_BAAN = "36"  # Ingroei baan
    JONGE_WERKLOZE_FOOI_26_6M = "37"  # Jonge werkloze (betaald met fooien) <26 jaar 6m
    JONGE_WERKLOZE_FOOI_26_9M = "38"  # Jonge werkloze (betaald met fooien) <26 jaar 9m
    WERKLOZE_MEER_1_JAAR = "39"  # Werkloze > 1 jaar
    STUDENT = "4"  # Student
    WERKLOZE_MEER_2_JAAR = "40"  # Werkloze > 2 jaar
    WERKLOZE_FOOI_MEER_1_JAAR = "41"  # Werkloze fooi > 1 jaar
    WERKLOZE_FOOI_MEER_2_JAAR = "42"  # Werkloze fooi > 2 jaar
    EWE_HALFTIJDS = "43"  # EWE; halftijds
    EWE_ANDER = "44"  # EWE ander dan halftijds
    EWE_HALFTIJDS_FOOIEN = "45"  # EWE halftijds met fooien
    EWE_ANDERE_FOOIEN = "46"  # EWE andere / met fooien
    SPORTLUI_WET = "48"  # Sportlui wet 24/02/78
    SPORTLUI_BUITEN_WET = "49"  # Sportlui buiten wet 24/02/78
    BESTUURDER = "5"  # Bestuurder
    PERSONEEL_INKOMSTEN_30 = "50"  # Personeel met inkomsten 30
    PROGRAMME_PRIME = "51"  # Programme prime
    LEERLING_SOCIO_PROF = "52"  # Leerling Socio-prof.Inpas.
    WERKLOZE_VZW = "53"  # Werkloze in een VZW
    LEERLING_BEROEPSINLEVING = "55"  # Leerling beroepsinlevingsovereenk.
    BEROEPSVORMING_AWIPH = "56"  # Beroepsvorming - AWIPH
    SPORTOMKADERING = "57"  # Sportomkadering
    ALTERNERENDE_OPLEIDING_WAALS = "58"  # Alternerende opleiding - Waals Gewest
    ALTERNEREND_LEREN_FRANSTALIG = "59"  # Alternerend leren - Franstalig België
    THUISWERKER = "6"  # Thuiswerker
    FLEXI_JOB = "60"  # Flexi-job
    MEDEWERKER_FOOIEN = "7"  # Medewerker met fooien
    GEPENSIONEERDE_BEDRIJFSLEIDER = "8"  # Gepensioneerde bedrijfsleider
    VERTEGENWOORDIGER = "9"  # Vertegenwoordiger
    WERKLOZE_OVERMACHT = "98"  # Werkloze - overmacht
    NIET_BEZOLDIGD = "99"  # Niet bezoldigd

class EmploymentLegalStatusEnum(Enum):
    """Status dienstverband enum"""
    EMPTY = ""  # Empty value
    CONTRACTUEEL = "1"  # Contractueel
    GEPENSIONEERDE = "10"  # Gepensioneerde
    BRUGGEPENSIONEERDE = "11"  # Bruggepensioneerde
    WEDUWEN = "12"  # Weduwen
    WEES_ANDERE_VERWANTE = "13"  # Wees/andere verwante
    RESERVEMILITAIREN = "14"  # Reservemilitairen/gepensioneerde vep
    VRIJWILLIGER = "16"  # Vrijwilliger
    WERKLOZE = "17"  # Werkloze
    PFI_STAGE_INSERTION = "18"  # Pfi/stage d'insertion
    TIJDSKREDIET_CANADA_DRY = "19"  # Tijdskrediet can dry (decavaa)
    TIJDELIJK = "2"  # Tijdelijk
    WERKLOZE_CANADA_DRY = "20"  # Werkloze canada dry (decavaa)
    BEROEPSINLEVINGSOVEREENKOMST = "21"  # Beroepsinlevingsovereenkomst
    VASTBENOEMD = "3"  # Vastbenoemd
    MANDATARIS = "4"  # Mandataris
    BEDRIJFSLEIDER = "5"  # Bedrijfsleider
    BESTUURDER = "6"  # Bestuurder
    BEHEERDER_VZW = "9"  # Beheerder (vzw)

class ContractCategoryEnum(Enum):
    """Contractcategorie enum"""
    EMPTY = ""  # Empty value
    ONBEPAALDE_DUUR = "1"  # Onbepaalde duur
    WELOMSCHREVEN_WERK_MINDER_3M = "10"  # Welomschreven werk < 3 maanden
    WELOMSCHREVEN_WERK_MEER_3M = "11"  # Welomschreven werk >= 3 maanden
    VERVANGINGSCONTRACT_MINDER_3M = "12"  # Vervangingscontract < 3 maanden
    VERVANGINGSCONTRACT_MEER_3M = "13"  # Vervangingscontract >= 3 maanden
    SEIZOENSARBEIDER_ZONDER_DAGFORFAIT = "14"  # Seizoensarbeider zonder dagforfait
    BEPAALDE_DUUR_MINDER_3M = "15"  # Bepaalde duur < 3 maanden
    FLEXI_MET_PERIODE_DIMONA = "16"  # Flexi met periode dimona
    FLEXI_MET_DAGDIMONA = "17"  # Flexi met dagdimona
    FLEXI_NIET_AANVAARD = "18"  # Flexi niet aanvaard
    GELIMITEERDE_PRESTATIES_BEGRAFENIS = "19"  # Gelimiteerde prestaties (LP) begrafenisonderneming
    BEPAALDE_DUUR = "2"  # Bepaalde duur
    WELOMSCHREVEN_WERK = "3"  # Welomschreven werk
    VERVANGINGSCONTRACT = "4"  # Vervangingscontract
    GELIMITEERDE_PRESTATIES_LP = "5"  # Gelimiteerde prestaties (lp op de aangifte)
    ARBEID_MET_TUSSENPOZEN = "6"  # Arb./bed. Met tussenpozen (t op de aangifte)
    SEIZOENSARB_GROEN_DAGFORFAIT = "7"  # Seizoensarb. Groen/piekextra dagforfait
    BEPAALDE_DUUR_MINDER_3M_ALT = "8"  # Bepaalde duur < 3 maanden
    BEPAALDE_DUUR_MEER_3M = "9"  # Bepaalde duur > 3 maanden
    GEEN = "99"  # Geen

class RSZType1Enum(Enum):
    """Type #1 medewerker enum, seems belgians specific"""
    EMPTY = ""  # Empty value
    GEWONE_CATEGORIE = "11"  # Gewone categorie
    RVA_STAGAIR = "12"  # Rva-stagair
    GESUBSIDIEERDE_CONTRACTUEEL = "13"  # Gesubsidieerde contractueel
    DEELTIJDS_LEERPLICHTIGE = "14"  # Deeltijds leerplichtige
    JOBSTUDENT = "15"  # Jobstudent
    EERSTE_WERKERVARING = "16"  # Eerste werkervaring
    INTERDEPARTEMENTEEL_BEGROTINGSFONDS = "17"  # Interdepartementeel begrotingsfonds
    DERDE_ARBEIDSCIRCUIT = "18"  # Derde arbeidscircuit
    MOEILIJK_PLAATSBARE_MVAL = "19"  # Moeilijk te plaatsen mval werkloze besch. Werkpl.
    GENEESHEER_OPLEIDING = "20"  # Geneesheer in opleid tot specialist
    BURSALEN_ZONDER_BILATERAAL = "21"  # Bursalen zndr bi/multilat.overeenk sz
    PRIME = "22"  # Prime
    CONTRACTUEEL_VERVANGER = "24"  # Contractueel vervanger herverdeling arbeid openbare sector
    TIJDELIJK_ARBEIDER_TUINBOUW = "50"  # Tijdelijk arbeider tuinbouw
    TAXICHAUFFEUR = "51"  # Taxichauffeur (rsz)
    ACAD_WET_PERS_UNIV = "52"  # Acad. En wet. Pers, univ(rsz)
    AMBTENAAR_KINDERBIJSLAG = "53"  # Ambtenaar met kinderbijslag (rsz)
    HOUDER_STAFFUNCTIE = "54"  # Houder staffunctie in overheid
    F1_ARBEIDER = "60"  # F1 arbeider
    F2_ARBEIDER = "61"  # F2 arbeider
    F1_BEDIENDE = "62"  # F1 bediende
    F2_BEDIENDE = "63"  # F2 bediende
    F1_ARBEIDER_GEEN_DIMONA = "64"  # F1 arbeider (geen dimona)
    F2_ARBEIDER_GEEN_DIMONA = "65"  # F2 arbeider (geen dimona)
    F1_BEDIENDE_GEEN_DIMONA = "66"  # F1 bediende (geen dimona)
    F2_BEDIENDE_GEEN_DIMONA = "67"  # F2 bediende (geen dimona)
    GENEESHEER_RSZPPO = "70"  # Geneesheer (rszppo)
    VRIJGESTELDE_GENEESHEER = "71"  # Vrijgestelde geneesheer
    MONITOR = "72"  # Monitor
    BEDIENAARS_EREDIENST = "73"  # Bedienaars van de eredienst(rszppo)
    SCHOUWSPELARTIEST = "74"  # Schouwspelartiest
    VRIJWILLIGE_BRANDWEERMAN = "75"  # Vrijwillige brandweerman (rszppo)
    VRIJGESTELDE_VRIJWILLIGER = "76"  # Vrijgestelde vrijwilliger(rszppo)
    ONBESCHERMDE_MANDATARIS = "77"  # Onbeschermde mandataris
    POLITIEPERSONEEL = "78"  # Politiepersoneel
    BURGERPERSONEEL_POLITIE = "79"  # Burgerpersoneel van de politie
    GESUBSIDIEERD_PERSONEEL_ONDERWIJS = "80"  # Gesubsidieerd personeel onderwijs
    SYNDICAAL_GEDETACHEERDE = "81"  # Syndicaal gedetacheerde werknemer
    DEELTIJDS_LEERPLICHTIGE_SCHOUWSPEL = "82"  # Deeltijds leerplichtige schouwspelartiest
    VERENIGINGSWERKER_SPORT = "84"  # Verenigingswerker (sportactiviteiten)
    VERENIGINGSWERKER_SOCIO_CULT = "85"  # Verenigingswerker (socio-cult. en overige act)
    MEERDERJARIGE_LEERLING_ALTERNERENDE = "86"  # Meerderjarige leerling in alternerende opleiding
    MINDERJARIGE_LEERLING_ALTERNERENDE = "87"  # Minderjarige leerling in alternerende opleiding
    ANDERE_NIET_RSZ = "99"  # Andere niet rsz-onderworpen

class RSZType2Enum(Enum):
    """Type #2 medewerker enum, seems belgians specific"""
    EMPTY = ""  # Empty value
    DEELTIJDS_LEERPLICHTIGE_LEERLING = "1"  # Deelt.leerplichtige leerl. Of beroepsinl.overeenk.
    THUISARBEIDER = "2"  # Thuisarbeider
    DEELTIJDSE_LEERPLICHTIGE_SCHOOLSTAGIAR = "3"  # Deeltijdse leerplichtige of schoolstagiar
    HANDELSVERTEGENWOORDIGER = "4"  # Handelsvertegenwoordiger
    GEPENSIONEERDE_BIJBEROEP = "5"  # Gepensioneerde met bijberoep
    STUDENT_NIET_ONDERWORPEN = "6"  # Student niet onderworpen aan solidariteitsbijdrage
    SECTOR_CAO_NVT = "9"  # Sector-cao of niet van toepassing
    KUNSTENAAR = "10"  # Kunstenaar
    PODIUMKUNSTENAAR = "11"  # Podiumkunstenaar
    KUNSTENAAR_STUDENT = "12"  # Kunstenaar(student)
    PODIUMKUNSTENAAR_STUDENT = "13"  # Podiumkunstenaar(student)
    KUNSTENAAR_GEPENSIONEERDE = "14"  # Kunstenaar(gepensioneerde met bijberoep)
    PODIUMKUNSTENAAR_GEPENSIONEERDE = "15"  # Podiumkunstenaar(gepensioneerde met bijberoep)
    BETAALDE_SPORTBEOEFENAARS = "16"  # Betaalde sportbeoefenaars
    COLLECTIEF_AKKOORD = "17"  # Collectief akkoord
    BETAALDE_SPORTBEOEFENAARS_GEPENS = "18"  # Betaalde sportbeoefenaars (gepens met bijberoep)
    INDIVIDUEEL_AKKOORD = "19"  # Individueel akkoord
    HUISBEDIENDE_ARBEIDER = "20"  # Huisbediende/arbeider

class SalaryCalculationMethodEnum(Enum):
    """Salarisverwerking enum"""
    EMPTY = ""  # Empty value
    PER_MAAND = "1"  # Per maand
    PER_UUR = "2"  # Per uur
    FORFAITAIR = "3"  # Forfaitair
    PER_STUK = "4"  # Per stuk
    MET_BEDIENINGSGELD = "5"  # Met bedieningsgeld
    PER_PRESTATIE = "6"  # Per prestatie
    VOLLEDIG_COMMISSIELOON = "7"  # Volledig met commissieloon
    PER_MAAND_GEDEELTELIJK_COMMISSIE = "8"  # Per maand + gedeeltelijk met commissieloon
    PER_UUR_GEDEELTELIJK_COMMISSIE = "9"  # Per uur + gedeeltelijk met commissieloon

class RecruitmentTypeEnum(Enum):
    """Aanwervingskader enum - Belgian specific recruitment framework types"""
    EMPTY = ""  # Empty value
    # 10-20 series: Youth employment plans and KB regulations
    JONGERENBANEN_PLAN_J9_VERMIND_WG_WN = "10"  # Jongerenbanen Plan Vermind. Wg + Wn (J9)
    JONGERENBANEN_PLAN_J6_VERMIND_WG = "11"  # Jongerenbanen Plan Vermind. Wg (J6)
    KB_111_EERST_AANGEWORVENE = "20"  # Kb 111 Eerst Aangeworvene
    KB_111_VERVANGER_EERST_AANGEWORVENE = "21"  # Kb 111 Vervanger Eerst Aangeworvene
    KB_494_TWEEDE_WERKNEMER = "30"  # Kb 494 Tweede Werknemer
    # 40-90 series: KB 498 and Program Law 88
    KB_498_JONGE_WERKZ_LANGD_WERKL_T_VERM_ADMIEKOST = "40"  # Kb 498 Jonge Werkz. Langd. Werkl(T),Verm.Admiekost
    KB_498_JONGE_WERKZ_LANGD_WERKL_T_Z_VERM_ADMIEKOST = "41"  # Kb 498 Jonge Werkz.Langd.Werkl(T),Z.Verm.Admiekost
    PROG_WET_88_T1_EERSTE_WERKNEMER = "50"  # Prog. Wet 88: Eerste Werknemer (T1)
    PROG_WET_88_T2_VERVANGER_EERSTE_WERKNEMER = "51"  # Prog. Wet 88: Vervanger Eerste Werknemer (T2)
    PROG_WET_88_T3_BIJK_WN_MET_VERM_ADMIEKOST = "52"  # Prog. Wet 88: Bijk. Wn Met Verm. Admiekost (T3)
    PROG_WET_88_T3_BIJK_WN_ZONDER_VERM_ADMIEKOST = "53"  # Prog. Wet 88: Bijk. Wn Zonder Verm. Admiekost (T3)
    PROG_WET_88_T4_VERV_BIJK_WN_VERM_ADMIEKOST = "54"  # Prog. Wet 88: Verv. Bijk. Wn, Verm. Admiekost (T4)
    PROG_WET_88_T4_VERV_BIJK_WN_ZONDER_VERM_ADMIE = "55"  # Prog. Wet 88: Verv.Bijk.Wn,Zonder Verm. Admie (T4)
    PROG_WET_88_T5_NIEUWE_WN_TVV_VRIJW_ONTSL_VA = "56"  # Prog. Wet 88: Nieuwe Wn.Tvv Vrijw. Ontsl,Va (T5)
    PROG_WET_88_T5_NIEUWE_WN_TVV_VRIJW_ONTSL_ZVA = "57"  # Prog. Wet 88: Nieuwe Wn.Tvv Vrijw. Ontsl,Zva (T5)
    PROG_WET_88_T6_VERVANGER_NIEUWE_WN_VA = "58"  # Prog. Wet 88: Vervanger Nieuwe Wn, Va (T6)
    PROG_WET_88_T6_VERVANGER_NIEUWE_WN_ZVA = "59"  # Prog. Wet 88: Vervanger Nieuwe Wn, Zva (T6)
    PROG_WET_88_T7_BEGELEIDING_WERKL_VA = "60"  # Prog. Wet 88: Begeleiding Werkl., Va (T7)
    PROG_WET_88_T7_BEGELEIDING_WERKL_ZVA = "61"  # Prog. Wet 88: Begeleiding Werkl., Zva (T7)
    PROG_WET_88_T8_VERV_BEGELEIDING_WERKL_VA = "62"  # Prog. Wet 88: Verv. Begeleiding Werkl., Va (T8)
    PROG_WET_88_T8_VERV_BEGELEIDING_WERKL_ZVA = "63"  # Prog. Wet 88: Verv. Begeleiding Werkl., Zva (T8)
    PLUS_1_PLAN_P_ZONDER_VERM_ADMIN_KOSTEN = "70"  # Plus 1 Plan: Zonder Vermindering Admin. Kosten (P)
    PLUS_1_PLAN_P_MET_VERM_ADMIN_KOSTEN = "71"  # Plus 1 Plan: Met Vermindering Admin. Kosten (P)
    PLUS_2_PLAN_P2_ZONDER_VERM_ADMIN_KOSTEN = "72"  # Plus 2 Plan: Zonder Vermindering Admin. Kost. (P2)
    PLUS_2_PLAN_P2_MET_VERM_ADMIN_KOSTEN = "73"  # Plus 2 Plan: Met Vermindering Admin. Kosten (P2)
    PLUS_3_PLAN_P3_ZONDER_VERM_ADMIN_KOSTEN = "74"  # Plus 3 Plan: Zonder Vermindering Admin.Kosten (P3)
    PLUS_3_PLAN_P3_MET_VERM_ADMIN_KOSTEN = "75"  # Plus 3 Plan: Met Vermindering Admin.Kosten (P3)
    VERVANGER_PLUS_2_PLAN_P2_ZONDER_VERM_ADM_K = "76"  # Vervanger Plus 2 Plan: Zonder Vermind. Adm.K (P2)
    VERVANGER_PLUS_2_PLAN_P2_MET_VERM_ADMIN_KO = "77"  # Vervanger Plus 2 Plan: Met Vermind. Admin Ko (P2)
    VERVANGER_PLUS_3_PLAN_P3_ZONDER_VERM_ADM_K = "78"  # Vervanger Plus 3 Plan: Zonder Vermind. Adm. K (P3)
    VERVANGER_PLUS_3_PLAN_P3_MET_VERM_ADM_KO = "79"  # Vervanger Plus 3 Plan: Met Vermind. Adm. Ko (P3)
    VERVANGER_PLUS_1_PLAN_P_ZONDER_VERM_ADM_KO = "80"  # Vervanger Plus 1 Plan: Zonder Vermind. Adm.Ko (P)
    VERVANGER_PLUS_1_PLAN_P_MET_VERM_ADM_K = "81"  # Vervanger Plus 1 Plan: Met Vermindering Adm. K (P)
    PLUS_1_PLAN_GEWEZEN_UITZENDKRACHT = "82"  # Plus 1 Plan: Gewezen Uitzendkracht
    PLUS_2_PLAN_GEWEZEN_UITZENDKRACHT = "83"  # Plus 2 Plan: Gewezen Uitzendkracht
    PLUS_3_PLAN_GEWEZEN_UITZENDKRACHT = "84"  # Plus 3 Plan: Gewezen Uitzendkracht
    PLUS_2_PLAN_GEWEZEN_UITZENDK_ZONDER_VERM_ADM = "85"  # Plus 2 Plan: Gewezen Uitzendkracht Zonder Verm Adm
    EX_RVA_STAGAIR_KB_230_R = "90"  # Ex Rva-Stagiair Kb 230 (R)
    EX_RVA_STAGAIR_EERSTE_JAAR_GEEN_RSZ_VERM = "91"  # Ex Rva-Stagiair (Eerste Jaar Geen Rsz-Verm)
    # 100-200 series: Employment plans (Banenplan, WEP+, etc.)
    BANENPLAN_B1_12_MAANDEN_WERKLOOS = "100"  # Banenplan 12 Maanden Werkloos (B1)
    BANENPLAN_B2_24_MAANDEN_WERKLOOS = "101"  # Banenplan 24 Maanden Werkloos (B2)
    MOEILIJK_PLAATSB_B3_WERKNEMER_PLUS50J = "102"  # Moeilijk Te Plaatsen Werknemer +50j (B3)
    HERINSCHAKELJOBS_B4 = "103"  # Herinschakeljobs (B4)
    INVOEG_WERKNEMERS_B4 = "104"  # Invoeg Werknemers (B4)
    BANENPLAN_12M_WERKLOOS_OUDER_45_JAAR = "105"  # Banenplan 12 Maanden Werkloos Ouder Dan 45 Jaar
    BANENPLAN_24M_WERKLOOS_OUDER_45_JAAR = "106"  # Banenplan 24 Maanden Werkloos Ouder Dan 45 Jaar
    BANENPLAN_24M_WERKL_PLUS45J_60M_UVW_36M_OCMW = "107"  # Banenplan 24 Maanden Werkl. +45 J 60m Uvw/36m Ocmw
    WERKNEMERS_ZONDER_DUURZAME_WERKERVARING = "108"  # Werknemers zonder duurzame werkervaring
    KB495_U_JONGEREN_TUSSEN_18_25_JAAR = "110"  # Kb495: Jongeren Tussen 18 En 25 Jaar (U)
    KB495_U_DEELTIJDS_LEERPLICHTIGE = "111"  # Kb495: Deeltijds Leerplichtige (U)
    KB483_EERSTE_WN_HOEDANIGH_HUISPERSONEEL = "120"  # Kb483: Eerste Wn In Hoedanigh. Huispersoneel
    SMET_BANEN_GEDURENDE_EERSTE_36_MAANDEN = "140"  # Smet-Banen Gedurende Eerste 36 Maanden
    SMET_BANEN_VERHOOGDE_TUSSENKOMST_36_MND = "141"  # Smet-Banen Met Verhoogde Tussenkomst Eerste 36 Mnd
    SMET_BANEN_NA_36_MAANDEN_MIN_45_JAAR = "142"  # Smet-Banen Na 36 Maanden En < 45 Jaar
    SMET_BANEN_NA_36_MAANDEN_PLUS_45_JAAR = "143"  # Smet-Banen Na 36 Maanden En > 45 Jaar
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_50PCT_250_EUR = "145"  # Wep Plus Plan Min. 12m Mi -45 Jaar 50% 250 Eur
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_50PCT_24789_EUR = "146"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 50% 247.89 Eur
    WEP_PLUS_24_MAANDEN_WERKLOOS_3_4TEW_12000FR = "147"  # Wep+ 24 Maanden Werkloos-3/4tew-12000fr
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_50PCT_29747_EUR = "148"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 50% 297.47 Eur
    WEP_PLUS_24_MAANDEN_WERKLOOS_3_4TEW_PWA_14000FR = "149"  # Wep+ 24 Maanden Werkloos-3/4tew-Pwa-14000fr
    BANENPLAN_24MND_WERKLOOS_MET_INTEGRATIE_UITKERING = "150"  # Banenplan 24mnd Werkloos Met Integratie-Uitkering
    WEP_PLUS_12_MAANDEN_WERKLOOS_3_4TEW_12000FR = "156"  # Wep+ 12 Maanden Werkloos-3/4tew-12000fr
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_50PCT_300_EUR = "157"  # Wep Plus Plan Min. 12m Mi -45 Jaar 50% 300 Eur
    WEP_PLUS_12_MAANDEN_WERKLOOS_3_4TEW_PWA_14000FR = "158"  # Wep+ 12 Maanden Werkloos-3/4tew-Pwa-14000fr
    VERVANGER_D1_LOOPBAANONDERBREKING_DEELTIJDS = "160"  # Vervanger Loopbaanonderbreking: Deeltijds (D1)
    VERVANGER_D2_LOOPBAANONDERBREKING_VOLTIJDS = "161"  # Vervanger Loopbaanonderbreking: Voltijds (D2)
    VERVANGER_D3_LOOPBAANONDERBREKING_DEELTIJDS_KMO = "162"  # Vervanger Loopbaanonderbreking: Deeltijds Kmo (D3)
    VERVANGER_G1_BRUGGEPENSIONEERDE_DEELTIJDS = "170"  # Vervanger Bruggepensioneerde: Deeltijds (G1)
    VERVANGER_G2_BRUGGEPENSIONEERDE_VOLTIJDS = "171"  # Vervanger Bruggepensioneerde: Voltijds (G2)
    VERVANGER_G3_BRUGGEPENSIONEERDE_DEELTIJDS_KMO = "172"  # Vervanger Bruggepensioneerde: Deeltijds Kmo (G3)
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_80PCT_32226_EUR = "173"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 80% 322.26 Eur
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_80PCT_37184_EUR = "174"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 80% 371.84 Eur
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_50PCT_43381_EUR = "175"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 50% 433.81 Eur
    WEP_PLUS_PLAN_MIN_24M_UVW_MIN45_JAAR_80PCT_54537_EUR = "176"  # Wep Plus Plan Min. 24m Uvw -45 Jaar 80% 545.37 Eur
    WEP_PLUS_MEER_50PCT_TEWERKST_10000_FR = "177"  # Wep+ (> 50% Tewerkst - 10000 Fr)
    WEP_PLUS_MEER_80PCT_TEWERKST_16000_FR = "178"  # Wep+ (> 80% Tewerkst - 16000 Fr)
    WEP_PLUS_100PCT_TEWERKST_20000_FR = "179"  # Wep+ (100% Tewerkst - 20000 Fr)
    WETENSCHAPPELIJK_PERSONEEL = "180"  # Wetenschappelijk Personeel
    WEP_PR_PLAN_36_48_MND_WERKL_50PCT_TEW_5000_FR = "181"  # Wep-Pr-Plan 36/48 Mnd Werkl,50%Tew,5000 Fr
    WEP_PR_PLAN_36_48_MND_WERKL_80PCT_TEW_8000_FR = "182"  # Wep-Pr-Plan 36/48 Mnd Werkl,80%Tew,8000 Fr
    WEP_PR_PLAN_48_60_MND_WERKL_50PCT_TEW_10000_FR = "183"  # Wep-Pr-Plan 48/60 Mnd Werkl,50%Tew,10000 Fr
    WEP_PR_PLAN_48_60_MND_WERKL_80PCT_TEW_16000_FR = "184"  # Wep-Pr-Plan 48/60 Mnd Werkl,80%Tew,16000 Fr
    WEP_PR_PLAN_MEER_60_MND_WERKL_50PCT_TEW_9000_FR = "185"  # Wep-Pr-Plan > 60 Mnd Werkl,50%Tew, 9000 Fr
    WEP_PR_PLAN_MEER_60_MND_WERKL_80PCT_TEW_18000_FR = "186"  # Wep-Pr-Plan > 60 Mnd Werkl,80%Tew, 18000 Fr
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_50PCT_435_EUR = "187"  # Wep Plus Plan Min. 12m Mi -45 Jaar 50% 435 Eur
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_80PCT_325_EUR = "188"  # Wep Plus Plan Min. 12m Mi -45 Jaar 80% 325 Eur
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_80PCT_375_EUR = "189"  # Wep Plus Plan Min. 12m Mi -45 Jaar 80% 375 Eur
    WEP_PLUS_PLAN_MIN_12M_MI_MIN45_JAAR_80PCT_545_EUR = "190"  # Wep Plus Plan Min. 12m Mi -45 Jaar 80% 545 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_50PCT_250_EUR = "191"  # Wep Plus Plan Min. 24m Mi -45 Jaar 50% 250 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_50PCT_300_EUR = "192"  # Wep Plus Plan Min. 24m Mi -45 Jaar 50% 300 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_50PCT_435_EUR = "193"  # Wep Plus Plan Min. 24m Mi -45 Jaar 50% 435 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_80PCT_325_EUR = "194"  # Wep Plus Plan Min. 24m Mi -45 Jaar 80% 325 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_80PCT_375_EUR = "195"  # Wep Plus Plan Min. 24m Mi -45 Jaar 80% 375 Eur
    WEP_PLUS_PLAN_MIN_24M_MI_MIN45_JAAR_80PCT_545_EUR = "196"  # Wep Plus Plan Min. 24m Mi -45 Jaar 80% 545 Eur
    # 200 series: PTP and DSP plans
    PTP_24_MAANDEN_WERKLOOS_50PCT_TEW_10000FR = "200"  # Ptp 24 Maanden Werkloos-50%Tew-10000fr
    PTP_24_MAANDEN_WERKLOOS_50PCT_TEW_17500FR = "201"  # Ptp 24 Maanden Werkloos-50%Tew-17500fr
    PTP_24_MAANDEN_WERKLOOS_80PCT_TEW_13000FR = "202"  # Ptp 24 Maanden Werkloos-80%Tew-13000fr
    PTP_24_MAANDEN_WERKLOOS_80PCT_TEW_22000FR = "203"  # Ptp 24 Maanden Werkloos-80%Tew-22000fr
    PTP_12_MAANDEN_WERKLOOS_50PCT_TEW_10000FR = "204"  # Ptp 12 Maanden Werkloos-50%Tew-10000fr
    PTP_12_MAANDEN_WERKLOOS_50PCT_TEW_17500FR = "205"  # Ptp 12 Maanden Werkloos-50%Tew-17500fr
    PTP_12_MAANDEN_WERKLOOS_80PCT_TEW_13000FR = "206"  # Ptp 12 Maanden Werkloos-80%Tew-13000fr
    PTP_12_MAANDEN_WERKLOOS_80PCT_TEW_22000FR = "207"  # Ptp 12 Maanden Werkloos-80%Tew-22000fr
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_50PCT_24789_EUR = "208"  # Dsp Brussel Min. 24m Uvw -45 Jaar 50% 247.89 Eur
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_50PCT_29747_EUR = "209"  # Dsp Brussel Min. 24m Uvw -45 Jaar 50% 297.47 Eur
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_50PCT_43381_EUR = "210"  # Dsp Brussel Min. 24m Uvw -45 Jaar 50% 433.81 Eur
    WEP_PLUS_BXL_24_MAANDEN_WERKLOOS_MEER50PCT_TEW_17500FR = "211"  # Wep+ Bxl 24 Maanden Werkloos- >50% Tew -17500fr
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_80PCT_32226_EUR = "212"  # Dsp Brussel Min. 24m Uvw -45 Jaar 80% 322.26 Eur
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_80PCT_37184_EUR = "213"  # Dsp Brussel Min. 24m Uvw -45 Jaar 80% 371.84 Eur
    DSP_BRUSSEL_MIN_24M_UVW_MIN45_JAAR_80PCT_54537_EUR = "214"  # Dsp Brussel Min. 24m Uvw -45 Jaar 80% 545.37 Eur
    WEP_PLUS_BXL_24_MAANDEN_WERKLOOS_MEER80PCT_TEW_22000FR = "215"  # Wep+ Bxl 24 Maanden Werkloos- >80% Tew -22000fr
    WEP_PLUS_BXL_24_MAANDEN_WERKLOOS_MEER75PCT_TEW_12000FR = "216"  # Wep+ Bxl 24 Maanden Werkloos- >75% Tew -12000fr
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_50PCT_250_EUR = "217"  # Dsp Brussel Min. 12m Mi -45 Jaar 50% 250 Eur
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_50PCT_300_EUR = "218"  # Dsp Brussel Min. 12m Mi -45 Jaar 50% 300 Eur
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_50PCT_435_EUR = "219"  # Dsp Brussel Min. 12m Mi -45 Jaar 50% 435 Eur
    WEP_PLUS_BXL_WKL_12M_WERKLOOS_MEER50PCT_TEW_17500FR = "220"  # Wep+ Bxl 12 Maanden Werkloos- >50% Tew -17500fr
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_80PCT_325_EUR = "221"  # Dsp Brussel Min. 12m Mi -45 Jaar 80% 325 Eur
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_80PCT_375_EUR = "222"  # Dsp Brussel Min. 12m Mi -45 Jaar 80% 375 Eur
    DSP_BRUSSEL_MIN_12M_MI_MIN45_JAAR_80PCT_545_EUR = "223"  # Dsp Brussel Min. 12m Mi -45 Jaar 80% 545 Eur
    WEP_PLUS_BXL_12M_WERKLOOS_MEER80PCT_TEW_22000FR = "224"  # Wep+ Bxl 12 Maanden Werkloos- >80% Tew -22000fr
    WEP_PLUS_BXL_12M_WERKLOOS_MEER75PCT_TEW_12000FR = "225"  # Wep+ Bxl 12 Maanden Werkloos- >75% Tew -12000fr
    DSP_BRUSSEL_UVW_LAAGG_MIN25_JAAR_50PCT_24789_EUR = "226"  # Dsp Brussel Uvw Laagg -25 Jaar 50% 247.89 Eur
    DSP_BRUSSEL_MIN_9M_MI_LAAGG_MIN25_JAAR_50PCT_250_EUR = "227"  # Dsp Brussel Min. 9m Mi Laagg -25 Jaar 50% 250 Eur
    WEP_PLUS_BXL_VOLL_WERKL_MIN25J_9M_WZ_MEER50PCT_TEW_10000FR = "228"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >50% Tew -10000fr
    WEP_PLUS_BXL_VOLL_WERKL_12M_WZ_MEER50PCT_TEW_10000FR = "229"  # Wep+ Bxl Voll.Werkl,12m Wz, >50% Tew -10000fr
    DSP_BRUSSEL_MIN_24M_MI_MIN45_JAAR_50PCT_250_EUR = "230"  # Dsp Brussel Min. 24m Mi -45 Jaar 50% 250 Eur
    DSP_BRUSSEL_UVW_LAAGG_MIN25_JAAR_50PCT_29747_EUR = "231"  # Dsp Brussel Uvw Laagg -25 Jaar 50% 297.47 Eur
    DSP_BRUSSEL_LAAGG_MIN_9M_MI_MIN25_JAAR_50PCT_300_EUR = "232"  # Dsp Brussel Laagg Min. 9m Mi -25 Jaar 50% 300 Eur
    WEP_PLUS_BXL_VOLL_WERKL_MIN25J_9M_WZ_MEER50PCT_TEW_12000FR = "233"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >50% Tew -12000fr
    WEP_PLUS_BXL_VOLL_WERKL_12M_WZ_MEER50PCT_TEW_12000FR = "234"  # Wep+ Bxl Voll.Werkl,12m Wz, >50% Tew -12000fr
    DSP_BRUSSEL_MIN_24M_MI_MIN45_JAAR_50PCT_300_EUR = "235"  # Dsp Brussel Min. 24m Mi -45 Jaar 50% 300 Eur
    DSP_BXL_LAAGG_MIN25_43381 = "236"  # Dsp Brussel Laaggeschoold -25 Jaar 50% 433.81 Eur
    DSP_BXL_LAAGG_9M_MIN25_435 = "237"  # Dsp Brussel Laagg Min.9m Mi -25 Jaar 50% 435 Eur
    WEP_BXL_MIN25_9M_50_17500 = "238"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >50% Tew -17500fr
    WEP_BXL_VOLL_12M_50_17500 = "239"  # Wep+ Bxl Voll.Werkl,12m Wz, >50% Tew -17500fr
    DSP_BXL_24M_MIN45_50_435 = "240"  # Dsp Brussel Min. 24m Mi -45 Jaar 50% 435 Eur
    DSP_BXL_LAAGG_MIN25_80_32226 = "241"  # Dsp Brussel Laaggeschoold -25 Jaar 80% 322.26 Eur
    DSP_BXL_LAAGG_9M_MIN25_80_325 = "242"  # Dsp Brussel Laagg Min.9m Mi -25 Jaar 80% 325 Eur
    WEP_BXL_MIN25_9M_80_13000 = "243"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >80% Tew -13000fr
    WEP_BXL_12M_80_13000 = "244"  # Wep+ Bxl Voll.Werkl,12m Wz, >80% Tew -13000fr
    DSP_BXL_24M_MIN45_80_325 = "245"  # Dsp Brussel Min. 24m Mi -45 Jaar 80% 325 Eur
    DSP_BXL_9M_MIN25_80_37184 = "246"  # Dsp Brussel Min. 9 M Uvw -25 Jaar 80% 371.84 Eur
    DSP_BXL_LAAGG_9M_MIN25_80_375 = "247"  # Dsp Brussel Laagg Min.9m Mi -25 Jaar 80% 375 Eur
    WEP_BXL_MIN25_9M_80_15000 = "248"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >80% Tew -15000fr
    WEP_BXL_12M_80_15000 = "249"  # Wep+ Bxl Voll.Werkl,12m Wz, >80% Tew -15000fr
    DSP_BXL_24M_MIN45_80_375 = "250"  # Dsp Brussel Min. 24m Mi -45 Jaar 80% 375 Eur
    DSP_BXL_9M_MIN25_80_54537 = "251"  # Dsp Brussel Min. 9 M Uvw -25 Jaar 80% 545.37 Eur
    DSP_BXL_LAAGG_9M_MIN25_80_545 = "252"  # Dsp Brussel Laagg Min.9m Mi -25 Jaar 80% 545 Eur
    WEP_BXL_MIN25_9M_80_22000 = "253"  # Wep+ Bxl Voll.Werkl<25j, 9m Wz, >80% Tew -22000fr
    WEP_BXL_12M_80_22000 = "254"  # Wep+ Bxl Voll.Werkl,12m Wz, >80% Tew -22000fr
    DSP_BXL_24M_MIN45_80_545 = "255"  # Dsp Brussel Min. 24m Mi -45 Jaar 80% 545 Eur
    WEP_PLUS_24M_PLUS45_50_10000 = "256"  # Wep+ 24 Mnd Werkl. +45j (>50% Tewerkst - 10000 Fr)
    WEP_PLUS_24M_PLUS45_50_12000 = "257"  # Wep+ 24 Mnd Werkl. +45j (>50% Tewerkst - 12000 Fr)
    WEP_PLUS_24M_PLUS45_50_17500 = "258"  # Wep+ 24 Mnd Werkl. +45j (>50% Tewerkst - 17500 Fr)
    WEP_PLUS_24M_PLUS45_80_13000 = "259"  # Wep+ 24 Mnd Werkl. +45j (>80% Tewerkst - 13000 Fr)
    WEP_PLUS_24M_PLUS45_80_15000 = "260"  # Wep+ 24 Mnd Werkl. +45j (>80% Tewerkst - 15000 Fr)
    WEP_PLUS_24M_PLUS45_80_22000 = "261"  # Wep+ 24 Mnd Werkl. +45j (>80% Tewerkst - 22000 Fr)
    ACTIVA_12M_18M_MIN45_MIN25 = "262"  # 12m Wz In 18m Activa +25 En -45 Jaar
    ACTIVA_MIN45_24M_50_500 = "263"  # Activa -45jaar 24m Werkloos In 36 M (+50%Tew)- 500
    ACTIVA_24M_36M_MIN45 = "264"  # 24m Wz In 36m Activa -45 Jaar
    ACTIVA_6M_9M_PLUS45_50 = "265"  # Activa 6m Wz In 9m Ug +45j - 50% Tew
    ACTIVA_6M_9M_PLUS45 = "266"  # 6 M Wz In 9m Activa +45 Jaar
    ACTIVA_12M_18M_PLUS45_50 = "267"  # Activa 12m Wz In 18m Ug +45j - 50% Tew
    ACTIVA_12M_18M_PLUS45 = "268"  # 12m Wz In 18m Activa +45 Jaar
    ACTIVA_PLUS45_24M_50_500 = "269"  # Activa +45jaar 24m Werkloos In 36 M(+50%Tew) - 500
    ACTIVA_PLUS45_24M_50_0 = "270"  # Activa +45jaar 24m Werkloos In 36 M (+50%Tew) - 0
    ACTIVA_24M_36M_MIN45_MI = "271"  # 24m Mi In 36m Activa - 45 Jaar
    ACTIVA_6M_9M_PLUS45_MI = "272"  # 6m Mi In 9m Acitiva +45 Jaar
    ACTIVA_12M_18M_PLUS45_MI = "273"  # 12m Mi In 18m Activa +45 Jaar
    ACTIVA_18M_27M_PLUS45_500 = "274"  # 18m Mi In 27m Activa +45 Jaar 500 Eur M Id +29
    WEP_PLUS_24M_PLUS45_50_24789 = "275"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 50% 247.89 Eur
    WEP_PLUS_24M_PLUS45_50_29747 = "276"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 50% 297.47 Eur
    WEP_PLUS_24M_PLUS45_50_43381 = "277"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 50% 433.81 Eur
    WEP_PLUS_24M_PLUS45_80_32226 = "278"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 80% 322.26 Eur
    WEP_PLUS_24M_PLUS45_80_37184 = "279"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 80% 371.84 Eur
    WEP_PLUS_24M_PLUS45_80_54537 = "280"  # Wep Plus Plan Min. 24m Uvw +45 Jaar 80% 545.37 Eur
    WEP_PLUS_24M_PLUS45_MI_50_250 = "281"  # Wep Plus Plan Min. 24m Mi +45 Jaar 50% 250 Eur
    WEP_PLUS_24M_PLUS45_MI_50_300 = "282"  # Wep Plus Plan Min. 24m Mi +45 Jaar 50% 300 Eur
    WEP_PLUS_24M_PLUS45_MI_50_435 = "283"  # Wep Plus Plan Min. 24m Mi +45 Jaar 50% 435 Eur
    WEP_PLUS_24M_PLUS45_MI_80_325 = "284"  # Wep Plus Plan Min. 24m Mi +45 Jaar 80% 325 Eur
    WEP_PLUS_24M_PLUS45_MI_80_375 = "285"  # Wep Plus Plan Min. 24m Mi +45 Jaar 80% 375 Eur
    WEP_PLUS_24M_PLUS45_MI_80_545 = "286"  # Wep Plus Plan Min. 24m Mi +45 Jaar 80% 545 Eur
    WEP_PLUS_12M_PLUS45_50_250 = "287"  # Wep Plus Plan Min. 12m Mi +45 Jaar 50% 250 Eur
    WEP_PLUS_12M_PLUS45_50_300 = "288"  # Wep Plus Plan Min. 12m Mi +45 Jaar 50% 300 Eur
    WEP_PLUS_12M_PLUS45_50_435 = "289"  # Wep Plus Plan Min. 12m Mi +45 Jaar 50% 435 Eur
    WEP_PLUS_12M_PLUS45_80_325 = "290"  # Wep Plus Plan Min. 12m Mi +45 Jaar 80% 325 Eur
    WEP_PLUS_12M_PLUS45_80_375 = "291"  # Wep Plus Plan Min. 12m Mi +45 Jaar 80% 375 Eur
    WEP_PLUS_12M_PLUS45_80_545 = "292"  # Wep Plus Plan Min. 12m Mi +45 Jaar 80% 545 Eur
    DSP_BXL_UVW_12M_MIN45_24789 = "293"  # Dsp Brussel Uvw 12m -45 Jaar 50% 247.89 Eur
    DSP_BXL_UVW_12M_MIN45_29747 = "294"  # Dsp Brussel Uvw 12m -45 Jaar 50% 297.47 Eur
    DSP_BXL_UVW_12M_MIN45_43381 = "295"  # Dsp Brussel Uvw 12m -45 Jaar 50% 433.81 Eur
    DSP_BXL_UVW_12M_MIN45_80_32226 = "296"  # Dsp Brussel Uvw 12m -45 Jaar 80% 322.26 Eur
    DSP_BXL_UVW_12M_MIN45_80_37184 = "297"  # Dsp Brussel Uvw 12m -45 Jaar 80% 371.84 Eur
    DSP_BXL_UVW_12M_MIN45_80_54537 = "298"  # Dsp Brussel Uvw 12m -45 Jaar 80% 545.37 Eur
    # 300 series: GESCO plans
    GESCO_WET_30_12_88 = "300"  # Gesco Wet 30/12/88
    GESCO_WEP_PLUS_WET_30_12_88 = "301"  # Gesco Wep+ Wet 30/12/88
    GESCO_SOCIALE_WERKPLAATS = "302"  # Gesco Sociale Werkplaats
    SINE_WN_SOCIALE_WERKPLAATS_17500_FR = "303"  # Sine Wn Sociale Werkplaats, 17500 Fr
    SINE_WN_SOCIALE_WERKPLAATS_22000_FR = "304"  # Sine Wn Sociale Werkplaats, 22000 Fr
    GESCO_WEP_PLUS_KB474_RSZPPO = "305"  # Gesco Wep+ Kb474 (Rszppo)
    SINE_WN_SOCIALE_WERKPLAATS_435_EUR = "306"  # Sine Wn Sociale Werkplaats, 435 Euro
    SINE_WN_SOCIALE_WERKPLAATS_545_EUR = "307"  # Sine Wn Sociale Werkplaats, 545 Euro
    GESCO_KB474_RSZPPO_TOT_31_12_1992 = "310"  # Gesco Kb474 (Rszppo - Tot 31/12/1992)
    GESCO_KB474_PREMIE_230000 = "311"  # Gesco Kb474 Premie 230000
    GESCO_KB474_PREMIE_400000 = "312"  # Gesco Kb474 Premie 400000
    LAAGGESCHOOLDE_JONGERE_SBO_RSZPPO = "320"  # Laaggeschoolde Jongere Sbo (Rszppo)
    ERG_LAAGGESCHOOLDE_JONGERE_SBO_RSZPPO = "324"  # Erg Laaggeschoolde Jongere Sbo (Rszppo)
    KUNSTENAAR_PPO = "325"  # Kunstenaar Ppo
    GESCO_KB474_BXL_PREMIE_230000 = "350"  # Gesco Kb474 Bxl Premie 230000
    GESCO_KB474_BXL_PREMIE_400000 = "351"  # Gesco Kb474 Bxl Premie 400000
    GESCO_BXL_VERBETERING_ONTHAAL_LOKETDIENSTEN = "352"  # Gesco Bxl: Verbetering Onthaal Bij Loketdiensten
    GESCO_BXL_TOEVOEGING_MAATSCH_ASSISTENT_OCMW = "353"  # Gesco Bxl: Toevoeging Maatsch. Assistent In Ocmw
    GESCO_BXL_TOEVOEGING_LICENTIATEN_OCMW = "354"  # Gesco Bxl: Toevoeging Licentiaten In Ocmw
    DG_6_MIN45_JAAR_VERMINDERINGSKAART_HERSTRUCTUR = "358"  # Dg 6 -45 Jaar Verminderingskaart Herstructur
    DG_6_PLUS45_JAAR_VERMINDERINGSKAART_HERSTRUCTUR = "359"  # Dg 6 +45 Jaar Verminderingskaart Herstructur
    TEWERKSTELLING_ONTSLAGEN_WN_HERSTRUCTURERING = "360"  # Tewerkstelling Ontslagen Wn Herstructurering
    ACTIVA_MIN25_JAAR_12M_UVW_IN_18M_500_EUR = "361"  # Activa -25 Jaar 12m Uvw In 18m 500 Eur
    ACT_PVP_12M_WZ_IN_18M_UVW_MIN25J = "362"  # Act Pvp 12m Wz In 18m, Uvw, <25j
    ACT_PVP_12M_WZ_IN_18M_MIN25J = "363"  # Act Pvp 12m Wz In 18m, <25j
    # 400 series: GESCO Walloon region
    GESCO_WAALS_BESTRIJDING_SOCIALE_UITSLUITING = "400"  # Gesco Waals: Bestrijding Sociale Uitsluiting
    GESCO_WAALS_PREMIE_205000 = "401"  # Gesco Waals Premie 205000
    GESCO_WAALS_PREMIE_410000 = "402"  # Gesco Waals Premie 410000
    GESCO_WAALS_PREMIE_615000 = "403"  # Gesco Waals Premie 615000
    GESCO_WAALS_PREMIE_700000 = "404"  # Gesco Waals Premie 700000
    # 450 series: GESCO Flemish region
    GESCO_VLAAMS_BESLUIT_27_02_1991_TOT_31_12_1992 = "450"  # Gesco Vlaams - Besluit 27/02/1991 (Tot 31/12/1992)
    GESCO_VLAAMS_BESLUIT_27_10_1993 = "451"  # Gesco Vlaams - Besluit 27/10/1993
    GESCO_VLAAMS_PREMIE_230000_BESLUIT_27_10_1993 = "452"  # Gesco Vlaams - Premie 230000 - Besluit 27/10/1993
    GESCO_VLAAMS_PREMIE_440000_BESLUIT_27_10_199 = "453"  # Gesco Vlaams - Premie 440000 - Besluit 27/10/199
    GESCO_VLAAMS_JEUGDWERKGARANTIEPLAN = "454"  # Gesco Vlaams - Jeugdwerkgarantieplan
    GESCO_VLAAMS_PROJECT_VL_GEMEENSCHAP = "455"  # Gesco Vlaams - Project Vl Gemeenschap
    GESCO_VLAAMS_KINDERDAGVERBLIJVEN = "456"  # Gesco Vlaams - Kinderdagverblijven
    GESCO_VLAAMS_WEERWERK_OP_PROEF = "457"  # Gesco Vlaams - Weerwerk (+ Op Proef)
    GESCO_VLAAMS_WERKERVARINGSPLAN = "458"  # Gesco Vlaams - Werkervaringsplan
    GESCO_VLAAMS_JEUGDWERKGARANTIEPLAN_ALT = "459"  # Gesco Vlaams - Jeugdwerkgarantieplan
    POLITIEPERSONEEL_VLAAMS_GEWEST = "460"  # Politiepersoneel-Vlaams Gewest
    # 500 series: Integration and work experience plans
    INGROEIBANEN = "500"  # Ingroeibanen
    COLLECTIEVE_ARBEIDSDUURVERM_BEDRIJF_HERSTR = "501"  # Collectieve Arbeidsduurverm. Bedrijf In Herstr.
    DSP_BXL_12M_PLUS45_50_250 = "510"  # Dsp Brussel Min. 12m Mi +45 Jaar 50% 250 Eur
    DSP_BXL_12M_PLUS45_50_300 = "511"  # Dsp Brussel Min. 12m Mi +45 Jaar 50% 300 Eur
    DSP_BXL_12M_PLUS45_50_435 = "512"  # Dsp Brussel Min. 12m Mi +45 Jaar 50% 435 Eur
    DSP_BXL_12M_PLUS45_80_325 = "513"  # Dsp Brussel Min. 12m Mi +45 Jaar 80% 325 Eur
    DSP_BXL_12M_PLUS45_80_375 = "514"  # Dsp Brussel Min. 12m Mi +45 Jaar 80% 375 Eur
    DSP_BXL_12M_PLUS45_80_545 = "515"  # Dsp Brussel Min. 12m Mi +45 Jaar 80% 545 Eur
    DSP_BXL_24M_PLUS45_50_24789 = "516"  # Dsp Brussel Min. 24m Uvw +45 Jaar 50% 247.89 Eur
    DSP_BXL_24M_PLUS45_50_29747 = "517"  # Dsp Brussel Min. 24m Uvw +45 Jaar 50% 297.47 Eur
    DSP_BXL_24M_PLUS45_50_43381 = "518"  # Dsp Brussel Min. 24m Uvw +45 Jaar 50% 433.81 Eur
    DSP_BXL_24M_PLUS45_80_32226 = "519"  # Dsp Brussel Min. 24m Uvw +45 Jaar 80% 322.26 Eur
    DSP_BXL_24M_PLUS45_80_37184 = "520"  # Dsp Brussel Min. 24m Uvw +45 Jaar 80% 371.84 Eur
    DSP_BXL_24M_PLUS45_80_54537 = "521"  # Dsp Brussel Min. 24m Uvw +45 Jaar 80% 545.37 Eur
    DSP_BXL_24M_PLUS45_MI_50_250 = "522"  # Dsp Brussel Min. 24m Mi +45 Jaar 50% 250 Eur
    DSP_BXL_24M_PLUS45_MI_50_300 = "523"  # Dsp Brussel Min. 24m Mi +45 Jaar 50% 300 Eur
    DSP_BXL_24M_PLUS45_MI_50_435 = "524"  # Dsp Brussel Min. 24m Mi +45 Jaar 50% 435 Eur
    DSP_BXL_24M_PLUS45_MI_80_325 = "525"  # Dsp Brussel Min. 24m Mi +45 Jaar 80% 325 Eur
    DSP_BXL_24M_PLUS45_MI_80_375 = "526"  # Dsp Brussel Min. 24m Mi +45 Jaar 80% 375 Eur
    DSP_BXL_24M_PLUS45_MI_80_545 = "527"  # Dsp Brussel Min. 24m Mi +45 Jaar 80% 545 Eur
    # 550-600 series: ACTIVA plans and RVA codes
    ACTIVA_MI_MIN25_JAAR_500_EUR = "550"  # Activa Mi - 25 Jaar 500 Eur
    ACTIVA_PLUS_12M_UVW_IN_18M_MIN25_JAAR_500_EUR = "551"  # 12m Uvw In 18m Activa Plus -25 Jaar 500 Eur
    ACTIVA_PLUS_6M_UVW_IN_9M_PLUS45_JAAR_500_EUR = "552"  # 6m Uvw In 9m Activa Plus +45 Jaar 500 Eur
    ACTIVA_PLUS_6M_MI_IN_9M_PLUS45_JAAR_500_EUR = "553"  # 6m Mi In 9m Activa Plus +45 Jaar 500 Eur
    ACTIVA_PLUS_12M_UVW_IN_18M_PLUS45_JAAR_500_EUR = "554"  # 12m Uvw In 18m Activa Plus +45 Jaar 500 Eur
    ACTIVA_PLUS_12M_MI_IN_18M_PLUS45_JAAR_500_EUR = "555"  # 12m Mi In 18m Activa Plus +45 Jaar 500 Eur
    ACTIVA_SLUITING_12M_WZ_IN_9M_PLUS45J_MIN50PCT_TEW = "556"  # Activa Sluiting 12m Wz In 9m +45j -50%Tew
    ACTIVA_SLUITING_6M_WZ_IN_9M_MIN45J_50PCT_TEW = "557"  # Activa Sluiting 6m Wz In 9m -45j - 50% Tew
    ACTIVA_SLUITING_6M_WZ_IN_9M_PLUS45J_50PCT_TEW = "558"  # Activa Sluiting 6m Wz In 9m +45j - 50% Tew
    ACTIVA_24M_UVW_IN_36M_MIN45_JAAR_500_EUR = "559"  # 24m Uvw In 36m Activa -45 Jaar 500 Eur
    ACTIVA_36M_UVW_IN_54M_MIN45_JAAR_500_EUR = "560"  # 36m Uvw In 54m Activa -45 Jaar 500 Eur
    ACTIVA_60M_UVW_IN_90M_MIN45_JAAR_500_EUR = "561"  # 60m Uvw In 90m Activa -45 Jaar 500 Eur
    ACTIVA_18M_UVW_IN_27M_PLUS45_JAAR_500_EUR = "562"  # 18m Uvw In 27m Activa +45 Jaar 500 Eur
    SINE_12M_UVW_IN_18M_MIN45_JAAR_500_EUR = "563"  # 12m Uvw In 18m Sine -45 Jaar 500 Eur
    ACTIVA_SLUITING_6M_WZ_IN_9M_MIN45_JAAR_500_EUR = "564"  # 6m Wz In 9m Activa Sluiting - 45 Jaar 500 Eur
    SINE_6M_MI_IN_9M_MIN45_JAAR_500_EUR = "565"  # 6m Mi In 9m Sine - 45 Jaar 500 Eur
    SINE_24M_UVW_IN_36M_MIN45_JAAR_500_EUR = "567"  # 24m Uvw In 36m Sine - 45 Jaar 500 Eur
    ACTIVA_SLUITING_6M_UVW_IN_9M_PLUS45_JAAR_500_EUR = "568"  # 6m Uvw In 9m Activa Sluiting +45 Jaar 500 Eur
    SINE_12M_WZ_IN_18M_MI_MIN45J = "569"  # Sine 12m Wz In 18m Mi -45j
    SINE_6M_UVW_IN_9M_PLUS45_JAAR_500_EUR = "571"  # 6m Uvw In 9m Sine +45 Jaar 500 Eur
    ACTIVA_36M_WZ_IN_54M_MIN45_JAAR = "572"  # 36m Wz In 54m Activa -45 Jaar
    SINE_6M_MI_IN_9M_PLUS45_JAAR_500_EUR = "574"  # 6m Mi In 9m Sine +45 Jaar 500 Eur
    ACTIVA_12M_MI_IN_18M_MIN25_JAAR_500_EUR = "575"  # 12m Mi In 18m Activa - 25 Jaar 500 Eur
    ACTIVA_24M_MI_IN_36M_MIN25_JAAR_500_EUR = "576"  # 24m Mi In 36m Activa - 25 Jaar 500 Eur
    ACTIVA_36M_MI_IN_54M_MIN25_JAAR_500_EUR = "577"  # 36m Mi In 54m Activa - 25 Jaar 500 Eur
    ACTIVA_60M_MI_IN_90M_MIN25_JAAR_500_EUR = "578"  # 60m Mi In 90m Activa - 25 Jaar 500 Eur
    ACTIVA_12M_MI_IN_18M_MIN45_JAAR = "579"  # 12m Mi In 18m Activa - 45 Jaar
    ACTIVA_36M_MI_MIN45_500 = "580"  # 36m Mi In 54m Activa - 45 Jaar 500 Eur
    ACTIVA_60M_MI_MIN45_500 = "581"  # 60m Mi In 90m Activa - 45 Jaar 500 Eur
    ACTIVA_18M_MI_PLUS45 = "582"  # 18m Mi In 27m Activa +45 Jaar
    ACTIVA_60M_WZ_MIN45 = "583"  # 60m Wz In 90m Activa -45 Jaar
    ACTIVA_18M_WZ_PLUS45 = "584"  # 18 M Wz In 27m Activa +45 Jaar
    GENERATIEPACT_LAAGGESCH = "590"  # Generatiepact (Erg) Laaggeschoolden
    ACTIVA_START_1 = "591"  # Activa Start
    ACTIVA_START_2 = "592"  # Activa Start
    RVA_C24 = "593"  # Rva C24
    RVA_C29 = "594"  # Rva C29
    RVA_C25 = "595"  # Rva C25
    RVA_C26 = "596"  # Rva C26
    RVA_C27 = "597"  # Rva C27
    RVA_C28 = "598"  # Rva C28
    RVA_C30 = "599"  # Rva C30
    RVA_C31 = "600"  # Rva C31
    RVA_C32 = "601"  # Rva C32
    RVA_C33 = "602"  # Rva C33
    RVA_C34 = "603"  # Rva C34
    RVA_D13 = "604"  # Rva D13
    RVA_D14_D15 = "605"  # Rva D14 / D15
    RVA_D16_D17 = "606"  # Rva D16 En D17
    RSZ_VERM_MENTOR = "607"  # Rsz Verm Mentor
    OPLEIDER_HERSTRUCT = "608"  # Opleider Met Herstruct
    WERKERVARING_DSP_BXL = "609"  # Werkervaring Volgens Regels Van Dsp Brussel
    RVA_C24_2011 = "610"  # Rva C24 2011
    RVA_C29_2011 = "611"  # Rva C29 2011
    RVA_C25_2011 = "612"  # Rva C25 2011
    RVA_C26_2011 = "613"  # Rva C26 2011
    RVA_C27_2011 = "614"  # Rva C27 2011
    RVA_C28_2011 = "615"  # Rva C28 2011
    RVA_C30_2011 = "616"  # Rva C30 2011
    RVA_C31_2011 = "617"  # Rva C31 2011
    RVA_C32_2011 = "618"  # Rva C32 2011
    RVA_C33_2011 = "619"  # Rva C33 2011
    RVA_C34_2011 = "620"  # Rva C34 2011
    RVA_D13_2011 = "621"  # Rva D13 2011
    RVA_D14_D15_2011 = "622"  # Rva D14 En D15 2011
    RVA_D16_D17_2011 = "623"  # Rva D16 En D17 2011
    WERKERVARING_MIN45_24789 = "624"  # Werkervaring <45j 247,89
    WERKERVARING_MIN45_29747 = "625"  # Werkervaring <45j 297,47
    WERKERVARING_MIN45_43381 = "626"  # Werkervaring <45j 433,81
    WERKERVARING_MIN45_37184 = "627"  # Werkervaring <45j 371,84
    WERKERVARING_MIN45_54537 = "628"  # Werkervaring <45j 545,37
    WERKERVARING_PLUS45_24789 = "629"  # Werkervaring >45j 247,89
    WERKERVARING_PLUS45_29747 = "630"  # Werkervaring >45j 297,47
    WERKERVARING_PLUS45_43381 = "631"  # Werkervaring >45j 433,81
    WERKERVARING_PLUS45_32226 = "632"  # Werkervaring >45j 322,26
    WERKERVARING_PLUS45_37184 = "633"  # Werkervaring >45j 371,84
    WERKERVARING_PLUS45_54537 = "634"  # Werkervaring >45j 545,37
    RVA_C35 = "635"  # Rva C35
    RVA_D18 = "636"  # Rva D18
    RVA_D19 = "637"  # Rva D19
    RVA_C36 = "638"  # Rva C36
    RVA_D20 = "639"  # Rva D20
    RVA_C40 = "640"  # Rva C37
    RVA_D21_PLUS45 = "643"  # RVA D21 >=45 jr
    RVA_C40_MIN27 = "644"  # Rva C40< 27j
    RVA_C42_MIN27 = "645"  # RVA C42 < 27 jaar
    COPY_563_RSZ = "646"  # copy 563 enkel RSZ verm: 12m UVW in 18m SINE -45 jaar 500 EUR
    COPY_567_RSZ = "647"  # copy 567 enkel RSZ verm: 24m UVW in 36m SINE -45 jaar 500 EUR
    COPY_571_RSZ = "648"  # copy 571 enkel RSZ verm: 6m UVW in 9m SINE +45 jaar 500 EUR
    COPY_563_HERINSCH = "649"  # copy 563 enkel herinsch: 12m UVW in 18m SINE -45 jaar 500 EUR
    COPY_567_HERINSCH = "650"  # copy 567 enkel herinsch: 24m UVW in 36m SINE -45 jaar 500 EUR
    COPY_571_HERINSCH = "651"  # copy 571 enkel herinsch: 6m UVW in 9m SINE +45 jaar 500 EUR
    COPY_303_RSZ = "652"  # copy 303 enkel RSZ verm: SINE wn 17500 fr
    COPY_304_RSZ = "653"  # copy 304 enkel RSZ verm: SINE wn 22000 fr
    COPY_303_HERINSCH = "654"  # copy 303 enkel herinschakeling: SINE wn 17500 fr
    COPY_304_HERINSCH = "655"  # copy 304 enkel herinschakeling: SINE wn 22000 fr
    # 700 series: Public sector and specific programs
    HERVERDELING_ARBEID_OPENB_SECTOR_VERV_4DAGENWEEK = "700"  # Herverdeling Arbeid Openb.Sector (Verv.4dagenweek)
    LOGISTIEK_ASSISTENT_KB_05_02_1997_RSZPPO = "701"  # Logistiek Assistent Kb05-02-1997 (Rszppo)
    KB_VEILIGHEIDSCONTRACT = "702"  # Kb Veiligheidscontract
    GERECHTIGDEN_OP_BESTAANSMINIMUM = "703"  # Gerechtigden Op Bestaansminimum
    MIN18J_VOLDOEN_KB495_INSTAP_JONGBAN_PLAN = "704"  # <18j Voldoen Aan Kb 495, Instap In Jong.Ban.Plan
    MIN18J_ALTERN_TEWERST_OPLEID_KB495_BRUGPROJN = "705"  # <18j Altern Tewerst En Opleid - Kb495 + Brugprojn.
    JONGEREN_SOCIO_PROFESSIONELE_INPASSING = "706"  # Jongeren Socio-Professionele Inpassing
    WN_IN_DIENST_NA_STARTBAANOVEREENKOMST_ENKEL_PPO = "707"  # Wn. In Dienst Na Startbaanovereenkomst (Enkel Ppo)
    CONTR_TER_VERVANGING_OPLEIDING_VERPLEEGKUNDIG = "708"  # Contr. Ter Vervanging Van Opleiding Verpleegkundig
    CONTR_BEZOLDIGD_AFWEZIG_WEGENS_OPLEID_VERPLEEGK = "709"  # Contr. Bezoldigd Afwezig Wegens Opleid Verpleegk.
    ACTIVA_MIN45JR_12_MND_WZ_IN_18_MND = "710"  # Activa -45jr 12 Mnd Wz In 18 Mnd
    ACTIVA_PLUS45JR_6_MND_WZ_IN_9_MND = "711"  # Activa +45jr 6 Mnd Wz In 9 Mnd
    ACTIVA_SLUITING = "712"  # Activa - Sluiting
    ACTIVA_MIN45JR_24_MND_WZ_IN_36_MND = "713"  # Activa -45jr 24 Mnd Wz In 36 Mnd
    ACTIVA_PLUS45JR_WZ_MEER_1_JAAR = "714"  # Activa +45jr Wz > 1 Jaar
    ACTIVA_MIN45JR_36_MND_WZ_IN_54_MND = "715"  # Activa -45jr 36 Mnd Wz In 54 Mnd
    ACTIVA_MIN45JR_60_MND_WZ_IN_90_MND = "716"  # Activa -45jr 60 Mnd Wz In 90 Mnd
    ACTIVA_MIN45JR_PREVENTIE_VEILIGHEID = "717"  # Activa -45jr Preventie & Veiligheid
    ACTIVA_PLUS45JR_PREVENTIE_VEILIGHEID = "718"  # Activa +45jr Preventie & Veiligheid
    DSP_MIN25JR = "720"  # Dsp -25jr
    DSP_MIN45JR_MIN_12MND_UITKERING = "721"  # Dsp -45jr Min 12mnd Uitkering
    DSP_MIN45JR_MIN_24MND_UITKERING = "722"  # Dsp -45jr Min 24mnd Uitkering
    DSP_PLUS45JR_MIN_12MND_UITKERING = "723"  # Dsp +45jr Min 12mnd Uitkering
    DSP_MIN45JR_MIN_24MND_UITKERING_ALT = "724"  # Dsp -45jr Min 24mnd Uitkering
    LOGISTIEK_ASS_OPL_VERPLEEGKUNDIGE_BEZ_AFW = "728"  # Logistiek Ass. + Opl. Verpleegkundige + Bez Afw
    GEEN_LOG_ASS_OPL_VERPLEEGKUNDIGE_BEZ_AFW = "729"  # Geen Log. Ass. + Opl. Verpleegkundige + Bez Afw
    # 795-900 series: GESCO contingent and plans
    GESCO_CONTINGENT = "795"  # Gesco Contingent
    GESCO_PROJECTEN = "796"  # Gesco Projecten
    GESCO_OPENBARE_BESTUREN = "797"  # Gesco Openbare Besturen
    ACTIVA_PLAN_GEEN_BEREKENINGEN_L4 = "798"  # Activa Plan (Geen Berekeningen In L4)
    WEP_PLUS_ALGEMEEN_GEEN_BEREKENINGEN_L4 = "799"  # Wep+ Algemeen (Geen Berekeningen In L4)
    WERKUITKERING_MIN25_JAAR_LAAGGESCHOOLDE_WALLONIE = "800"  # Werkuitkering -25 jaar laaggeschoolde Wallonië
    MIDDENGESCH_6M_WERKZOEKEND_WALLONIE = "801"  # Middengesch. - 6m werkzoekend / Wallonië
    IMPULSION_MIN25_55PLUS_INSERTION = "803"  # Impulsion -25, 55+, insertion
    ACTIVA_BRUSSEL_LANGDURIG_WERKZOEKEND = "900"  # Activa Brussel langdurig werkzoekend
    # Final value
    GEEN_AANWERVINGSKADER = "999"  # Geen Aanwervingskader

class PerformanceExceptionEnum(Enum):
    """Notie vrijstelling prestaties enum"""
    EMPTY = ""  # Empty value
    GEEN_VRIJSTELLING = "0"  # Geen vrijstelling prestaties
    VRIJSTELLING = "1"  # Vrijstelling van prestaties
    VRIJSTELLING_VOLLEDIG_KWARTAAL = "2"  # Vrijstelling van prestaties tijdens volledig kwartaal
    VRIJSTELLING_VOOR_280917 = "3"  # Vrijstelling van prestaties voorafgaand aan 28/09/2017
    VRIJSTELLING_KWARTAAL_CAO_VOOR_280917 = "4"  # Vrijstelling van prestaties tijdens volledig kwartaal CAO afgesloten voorafgaand aan 28/09/2017
    VRIJSTELLING_KWARTAAL_OPLEIDING_20PCT = "5"  # Vrijstelling van prestaties tijdens volledig kwartaal en opleiding met kost >= 20% brutojaarloon
    VRIJSTELLING_TEWERKSTELLING_MIN_1_3 = "6"  # Vrijstelling van prestaties en tewerkstelling van minstens 1/3 tijd tijdens volledig kwartaal
    VRIJSTELLING_KWARTAAL_MINDER_1_3 = "7"  # Vrijstelling van prestaties tijdens volledig kwartaal tot minder dan 1/3 van een voltijdse tewerkst.
    VRIJSTELLING_MIN_1_3_VORMING_20PCT = "8"  # Vrijst. van prest. tijdens kwartaal tot >= 1/3 van volt. tewerkst. en vorming kost = 20% bt jaarloon

class EducationStatusEnum(Enum):
    """Status vorming enum"""
    EMPTY = ""  # Empty value
    GEEN_VORMING = "0"  # Geen vorming gevolgd door de werknemer
    VERPLICHTE_VORMING = "1"  # Verplichte vorming gevolgd door de werknemer
    VERPLICHTING_OUTPLACEMENT = "2"  # Verplichting tot volgen outplacementbegeleiding

class OccupationCategoryEnum(Enum):
    """Beroepscategorie enum"""
    EMPTY = ""  # Empty value
    DIRECTIELID = "01"  # Directielid
    BEDIENDE = "02"  # Bediende
    ARBEIDER = "03"  # Arbeider

class DFMARiskClassEnum(Enum):
    """Risicoklasse DMFA enum - Belgian specific"""
    EMPTY = ""  # Empty value
    ARBEIDER_ZONDER_VERPLAATSING = "1"  # Arbeider zonder verplaatsing
    ARBEIDER_OP_WERF = "2"  # Arbeider op de werf
    HUISBEWAARDERS_ARBEIDER = "3"  # Huisbewaarders (arbeider)
    SCHOONMAAK_ARBEIDER = "4"  # Schoonmaak- en onderhoudspersoneel(arbeider)
    KEUKENPERSONEEL_ARBEIDER = "5"  # Keukenpersoneel (niet voor horeca) (arbeider)
    CHAUFFEUR_ARBEIDER = "6"  # Chauffeur(arbeider)
    BEDIENDE_ZONDER_VERPLAATSING = "401"  # Bediende zonder verplaatsing
    BEDIENDE_OCCASIONELE_OPDRACHTEN = "402"  # Bediende met occasionele opdrachten buiten ondern.
    BEDIENDE_REGELMATIGE_OPDRACHTEN = "403"  # Bediende met regelmatige opdrachten buiten ondern.
    VERTEGENWOORDIGER_BEDIENDE = "404"  # Vertegenw., reizend person., loopjongen (bediende)
    BEDIENDE_MANUEEL = "405"  # Bediende die manueel werk verricht
    THUISWERKENDE_BEDIENDE = "406"  # Thuiswerkende bediende
    VERPLEGEND_PERSONEEL = "407"  # Verplegend personeel
    VERKOPER_BEDIENDE = "408"  # Verkoper (bediende)
    VOETBALLER_MET_STATUUT = "409"  # Voetballer met statuut betaalde sportbeoefenaar
    VOETBALLER_ZONDER_STATUUT_MEER = "410"  # Voetballer zonder stat bet. Sportbeoef.> 1239,47e
    VOETBALLER_ZONDER_STATUUT_MINDER = "411"  # Voetballer zonder stat bet. Sportbeoef.< 1239,47e
    ANDERE_SPORTBEOEFENAAR = "412"  # Andere sportbeoefenaar dan voetballer

class FixedTermContractEnum(Enum):
    """Contract bepaalde duur enum"""
    EMPTY = ""  # Empty value
    MINDER_DAN_3_MAANDEN = "A"  # Minder dan 3 maanden
    MEER_DAN_3_MAANDEN = "B"  # Meer dan 3 maanden

class WorkTimeRegimeEnum(Enum):
    """Fulltime/parttime enum - Belgian specific"""
    EMPTY = ""  # Empty value
    VOLTIJDS_WERK = "1"  # Voltijds werk
    VRIJWILLIG_DEELTIJDS_VOLLEDIGE_DAGEN = "2"  # Vrijwillig deeltijds - volledige dagen
    VRIJWILLIG_DEELTIJDS_ONVOLLEDIGE_DAGEN = "3"  # Vrijwillig deeltijds - onvolledige dagen
    VOLTIJDS_PLUS_ONVOLLEDIGE = "4"  # Voltijds + bij gelegenheid onvolledige dagen
    VRIJWILLIG_DEELTIJDS_ONBEPAALDE_UUR = "5"  # Vrijwillig deeltijds - onbepaalde uurregeling
    ONVRIJWILLIG_DEELTIJDS_VOLLEDIGE_DAGEN = "6"  # Onvrijwillig deeltijds - volledige dagen
    ONVRIJWILLIG_DEELTIJDS_ONVOLLEDIGE_DAGEN = "7"  # Onvrijwillig deeltijds - onvolledige dagen
    ONVRIJWILLIG_DEELTIJDS_ONBEPAALDE_UUR = "8"  # Onvrijwillig deeltijds – onbepaalde uurregeling

class RetroactivePaymentTypeEnum(Enum):
    """Soort nabetaling enum"""
    EMPTY = ""  # Empty value
    GROENE_TABEL = "G"  # Groene tabel (bv. Ontslaguitkering)
    WITTE_TABEL = "W"  # Witte tabel (bv. Eindafrekening / ontslaguitkering)

class PartenaEducationLevelCodeEnum(Enum):
    """Opleidingsniveau code enum - Partena specific"""
    NO_CODE = "0"  # Geen code
    PRIMARY_EDUCATION = "1"  # Basisonderwijs
    SECONDARY_EDUCATION = "2"  # Sec/voortgezet onderwijs
    HIGHER_NON_UNIVERSITY = "3"  # Hoger niet univ. onderwijs
    UNIVERSITY = "4"  # Universitair onderwijs
    UNKNOWN = "9"  # Onbekend


class PartenaContractPrecisionCodeEnum(Enum):
    """Precisering contract enum - Partena specific"""
    NONE = "0"  # Geen speciaal contract
    INGROEIBAAN = "1"  # Ingroeibaan
    TRAINEE_KB_230 = "2"  # Stagiair K.B. 230
    EWE_PART_TIME_WITH_REDUCTION = "3"  # EWE halftijds met vermind. Netto
    EWE_PART_TIME_NO_REDUCTION = "4"  # EWE halftijds zonder verm. Netto
    EWE_NOT_PART_TIME = "5"  # EWE niet halftijds
    STUDENT = "6"  # Student
    SCHOOL_INTERNSHIP = "7"  # Stage i.v.m. schoolse opleiding
    EXTRA_HORECA = "8"  # Extra HORECA
    SUPER_EXTRA_HORECA = "E"  # Super-Extra HORECA
    OCCASIONAL_HORECA = "F"  # Gelegenheidswerkn. HORECA
    WORKER_UNDER_15 = "J"  # Werknemer -15 jaar
    OCCASIONAL_FUNERAL = "P"  # Gelegenheidswerkn. begrafenissen
    STARTERS_JOB = "S"  # Startersjob
    INTERNSHIP = "T"  # Instapstage
    ALTERNATING_WALLOON = "W"  # Alternerende opleiding in het Waals Gewest
    FLEXI_JOB = "X"  # Flexijobs


class PartenaLearningContractRegionEnum(Enum):
    """Regio leercontract enum - Partena specific"""
    NOT_APPLICABLE = "0"  # Zonder voorwerp
    FLEMISH_COMMUNITY = "1"  # Vlaamse gemeenschap
    FRENCH_COMMUNITY = "2"  # Franse gemeenschap (Waals en Bruss. Hoofdst. Gewest.)
    GERMAN_COMMUNITY = "3"  # Duitse gemeenschap


class PartenaDismissalReasonEnum(Enum):
    """Reden uit dienst enum - Partena specific"""
    IN_SERVICE = "00"  # (In dienst)
    DISMISSAL_BY_EMPLOYER = "01"  # Ontslag (door de werkg)
    DISMISSAL_BY_EMPLOYEE = "02"  # Ontslag (door de werkn)
    SERIOUS_FAULT = "03"  # Zware fout
    FIXED_TERM_OR_WORK = "04"  # Bep.duur/werk
    RETIREMENT = "05"  # Pensioen
    BRIDGE_PENSION = "06"  # Brugpensioen
    DECEASED = "07"  # Overlijden
    STATUS_CHANGE = "08"  # Verandering van statuut
    OTHER = "09"  # Andere
    END_TIME_CREDIT_WITH_RESUMPTION = "11"  # Einde tijdskrediet met werkhervatting
    EARLY_RETIREMENT = "12"  # Vervroegd pensioen
    EARLY_RETIREMENT_MEDICAL = "13"  # Vervroegd pensioen wegens ziekte
    END_CIVIL_SERVANT_STATUS = "15"  # Einde statuut ambtenaar
    COLLECTIVE_DISMISSAL = "16"  # Collectief ontslag
    TERMINATION_MEDICAL_FORCE = "17"  # Beëindiging medische overmacht
    TERMINATED_BY_EMPLOYER = "22"  # Verbreking door de werkgever
    MUTUAL_AGREEMENT = "24"  # In onderling akkoord
    FORCE_MAJEURE = "25"  # Overmacht
    SPECIFIC_WORK_COMPLETED = "27"  # Bepaald werk


class PartenaTemporaryContractEnum(Enum):
    """Tijdelijk contract enum - Partena specific"""
    NOT_APPLICABLE = "0"  # Niet van toepassing
    INTERIM_EMPLOYEE = "I"  # Interimwerknemer
    SEASONAL_EMPLOYEE = "S"  # Seizoenswerknemer
    EMPLOYEE_WITH_BREAKS = "T"  # Wn met tussenpauzen


class PartenaTitleEnum(Enum):
    """Titel enum - Partena specific"""
    MISS = "1"  # Mejuffrouw
    MRS = "2"  # Mevrouw
    MR = "3"  # De heer


class PartenaLearnerTypeEnum(Enum):
    """Type leerling enum - Partena specific"""
    NOT_APPLICABLE = "0"  # Zonder voorwerp
    APPRENTICE_SELF_EMPLOYED = "1"  # Middenstandsleerling
    INDUSTRIAL_APPRENTICE = "2"  # Industriële leerling
    FR_COMMERCIAL_TRAINING = "3"  # Opleiding bedrijfsleider Fr. Gem.
    CEFA_INSERTION_CONTRACT = "4"  # Inschakelingsovereenkomst CEFA
    VL_COMMERCIAL_TRAINING = "5"  # Opleiding bedrijfsleider Vl. Gem.
    PROFESSIONAL_INTEGRATION_AGREEMENT = "6"  # Beroepsinlevingsovereenkomst
    ALTERNATING_AGREEMENT = "7"  # Alternerende overeenkomst
    ALTERNATING_LEARNING_FLANDERS = "8"  # Alternerend Leren. Vlaanderen


class TKPOutOfServiceReasonEnum(Enum):
    """Reden uit dienst (TKP) enum"""
    WORK_ELSEWHERE_WITH_BENEFITS = "01"  # Aanvaarding werk elders en uitk.
    REORGANISATION_NO_SBR = "26"  # Reorganisatie en geen SBR
    VUT = "31"  # VUT
    RETIREMENT = "33"  # Pensioen
    DECEASED = "34"  # Overlijden
    PREPENSION = "36"  # Prépensioen
    FULLY_DISABLED = "41"  # Voll. Arbeidsongeschikt
    PARTIALLY_DISABLED = "42"  # Ged. Arbeidsongeschikt
    PARTIALLY_DISABLED_LT15 = "43"  # Ged. Arbeidsong. <15%
    TRANSFER_PAO = "51"  # Overgant PAO
    DISABILITY_FIXED_TERM = "71"  # AO voor bepaalde tijd
    WORK_ELSEWHERE = "02"  # Aanvaarding werk elders
    DISMISSAL_AND_REHIRE_SAME_DAY = "81"  # Ontslag + idtr zelfde datum
    DISABLED_REDEPLOYED = "86"  # Arb. Ongeschikt herplaatsing
    SUMMARY_DISMISSAL = "09"  # Ontslag op staande voet
    VUT_SUMP = "32"  # VUT SUMP
    PERSONAL_REASONS_WITH_BENEFITS = "03"  # Pers. Redenen en uitkeringen
    OTHER_PERSONAL_REASON = "04"  # Andere persoonlijke reden
    DURING_PROBATION = "11"  # Tijdens proeftijd
    SENIOR_LEAVE = "53"  # Senioren verlof
    INSUFFICIENT_PERFORMANCE = "12"  # Onvoldoende functioneren
    SERIOUS_MISCONDUCT = "13"  # Laakbaar gedrag / verst. A
    SBR_55_PLUS = "22"  # SBR 55+
    SBR_NOT_55_PLUS = "24"  # Wel SBR, geen 55+

class SocialSecurityBenefitEnum(Enum):
    """Sociale voorziening enum"""
    EMPTY = ""  # Empty value
    STEWARD = "1"  # Steward
    PILOOT = "2"  # Piloot
    JOURNALIST = "3"  # Journalist
    PODIUMKUNSTENAAR_NIET_INWONER = "4"  # Podiumkunstenaar niet-inwoner
    BATEN_NIET_INWONER = "5"  # Baten niet-inwoner
    INKOMSTEN_SPORTBEOEF_MAX_30 = "6"  # Inkomsten sportbeoef. Niet-inwoner max. 30 dagen
    ANDER_VLIEGEND_PERSONEEL = "7"  # Ander vliegend personeel
    INKOMSTEN_SCHEIDSR_TRAINER = "8"  # Inkomsten scheidsr,trainer,begel,opleider
    SEIZOENARBEIDER_WAARBORGFONDS = "10"  # Seizoenarbeider waarborgfonds netto 0
    SCHEPENEN = "12"  # Schepenen
    WERKNEMER_PLOEG_NACHT = "50"  # Werknemer met ploeg- of nachtarbeid
    WERKEN_ONROERENDE_STAAT = "51"  # Werken in onroerende staat
    PILOOT_PLOEG_NACHT = "52"  # Piloot met ploeg- of nachtarbeid
    JOURNALIST_PLOEG_NACHT = "53"  # Journalist met ploeg- of nachtarbeid
    BATEN_SPORTBEOEF_MAX_30 = "55"  # Baten sportbeoefenaar niet-inwoner max. 30 dagen
    BATEN_SPORTBEOEF_MEER_30 = "56"  # Baten sportbeoefenaar niet-inwoner meer dan 30 d.
    BATEN_SCHEIDSR_TRAINER = "57"  # Baten scheidsr.,trainer,begel.opl. Niet-inwoner
    SEIZOENARBEIDER_PLOEG_NACHT = "60"  # Seizoenarb. Waarborgfonds netto 0 ploeg/nacht
    ONDERZOEKER_UNIV_50 = "70"  # Onderzoeker universiteiten en hogescholen (-50%)
    ONDERZOEKER_UNIV_75 = "71"  # Onderzoeker universiteiten en hogescholen (-75%)
    ONDERZOEKER_ERKEND_WET = "72"  # Onderzoeker erkende wetenschappelijke instelling
    ONDERZOEKER_PARTNERSHIPS = "73"  # Onderzoeker privé partnerships
    ONDERZOEKER_YIN = "74"  # Onderzoeker yin
    ONDERZOEKER_BURGERLIJK_ING = "75"  # Onderzoeker burgerlijk ingenieurs + doctors
    ONDERZOEKER_MASTERS = "76"  # Onderzoeker masters
    BACHELOR_NIET_KMO = "77"  # Bachelor niet KMO
    BACHELOR_KMO = "78"  # Bachelor KMO
    WERKNEMER_PLOEG_NACHT_NA_2022 = "80"  # Werknemer met ploeg- of nachtarbeid (na 31/03/22)
    WERKNEMER_PLOEGARBEID_NA_2022 = "81"  # Werknemer met ploegarbeid (na 31/03/22)
    WERKNEMER_NACHTARBEID_NA_2022 = "82"  # Werknemer met nachtarbeid (na 31/03/22)
    NACHT_PLOEGDIENST_VOLCONTINU = "90"  # Nacht-/ploegendienstin volcontinu-systeem

class StatuutEnum(Enum):
    """Statuut enum - Legal employment status"""
    EMPTY = ""  # Empty value
    GEEN_STATUUT = "0"  # Geen statuut
    BEDRIJFSLEIDER = "A"  # Bedrijfsleider
    GESUBS_CONTRACTUELE = "CS"  # Gesubs. contractuele
    THUISARBEIDER = "D"  # Thuisarbeider
    THUISARBEIDER_SCHOOLPLICHTIG = "D1"  # Thuisarb. schoolplichtige
    JOBSTUDENT_BEDIENDE = "E"  # Jobstudent bediende
    SCHOOLPLICHTIGE = "ET"  # Schoolplichtige
    GEPENSIONEERDE_ARBEIDER = "F"  # Gepensioneerde arbeider
    GEPENSIONEERDE_BEDIENDE = "F1"  # Gepensioneerde bediende
    TIJDELIJKE_ARBEIDER = "J"  # Tijdelijke arbeider
    MINDERVALIDE_WERKNEMER = "M"  # Mindervalide werknemer
    BEDIENDE_NIET_ONDERWORPEN = "N"  # Bediende niet onderworpen
    JOBSTUDENT_ARBEIDER = "O"  # Jobstudent arbeider
    FOOIEN_GESUB_CT = "PC"  # Ged. met fooien gesub. ct.
    GEDEELTELIJK_FOOIEN = "PP"  # Gedeeltelijk met fooien
    FOOIEN_SCHOOLPL = "PS"  # Ged. met fooien schoolpl.
    BRUGPENSIOEN_BEDIENDE = "Q"  # Brugpensioen bediende
    HANDELSVERTEGENWOORDIGER = "R"  # Handelsvertegenwoordiger
    HANDELSV_GESUBSID = "RC"  # Handelsv. gesubsid. contr.
    HANDELSVERT_MINDERVALIDE = "RM"  # Handelsvert. mindervalide
    HANDELSV_SCHOOLPLICHTIG = "RS"  # Handelsv. schoolplichtige
    STATUTAIRE = "S"  # Statutaire
    SPORTBEOEF_WET = "SP"  # Sportbeoefen. wet 24/2/78
    SPORTMAN_NIET_WET = "ST"  # Sportman niet wet 24/2/78
    BIJZONDER_TIJDELIJK = "T"  # Bijzonder tijdelijk kader
    VOLLEDIG_FOOIEN_GESUB = "TC"  # Vol. met fooien gesub. ct.
    VOLLEDIG_FOOIEN = "TP"  # Volledig met fooien
    VOLLEDIG_FOOIEN_SCHOOLPL = "TS"  # Vol. met fooien schoolpl.
    TAXICHAUFFEUR = "TX"  # Taxichauffeur
    WERKENDE_VENNOOT = "W"  # Werkende vennoot
    ARBEIDER_NIET_ONDERWORPEN = "X"  # Arbeider niet onderworpen
    BRUGPENSIOEN_ARBEIDER = "Y"  # Brugpensioen arbeider
    HUISPERS_NIET_ONDERWORPEN = "Z"  # Huispers. niet onderworpen

class SpecificFunctionTypeEnum(Enum):
    """Specifieke betrekking enum"""
    EMPTY = ""  # Empty value
    ZONDER_VOORWERP = "0"  # zonder voorwerp
    VRIJST_ERKENDE_WET_INST = "1"  # Vrijst. doorst. BV - Erkende Wet. Inst. 274-07
    DIENSTENCHEQUES = "2"  # Tewerkstelling in kader van dienstencheques
    INDIVIDUELE_PROF_OPLEIDING = "3"  # Individuele professionele opleiding
    VRIJST_UNIV_HOGESCHOOL = "4"  # Vrijst. Doorst. BV - Universiteit-Hogeschool 274-05
    VRIJST_SAMENWERKINGSAKKOORD = "5"  # Vrijst. Doorst. BV - Samenwerkingsakkoord 274-09
    VRIJST_DOCTOR_BURG_ING = "6"  # Vrijst. Doorst. BV - Doctor - burgerlijk ing. 274-32
    VRIJST_YOUNG_INNOVATIVE = "7"  # Vrijst. Doorst. BV - Young Innovative Company 274-31
    VRIJST_MASTER_GELIJKWAARDIG = "9"  # Vrijst. Doorst. BV - Master of gelijkwaardig 274-33
    BEROEPSINLEVINGSOVEREENKOMST = "B"  # Beroepsinlevingsovereenkomst
    DIMONA_ZONDER_DMFA = "D"  # Dimona zonder DMFA
    MENTOR = "T"  # Mentor
    VRIJWILLIGER = "V"  # Vrijwilliger
    WERKPLEKLEERPLAATS = "W"  # Werkplekleerplaats
    VRIJST_BACHELOR = "Z"  # Vrijst. Doorst. BV : Bachelor – 274.34

class FunctionTitleEnum(Enum):
    """Titel enum"""
    EMPTY = ""  # Empty value
    ZONDER_TITEL = "1"  # Zonder titel
    AFDELINGSHOOFD = "3"  # Afdelingshoofd
    DIENSTHOOFD = "4"  # Diensthoofd
    PROCURATIEHOUDER = "5"  # Procuratiehouder
    ADJUNCT_DIRECTEUR = "6"  # Adjunct-directeur
    DIRECTEUR = "7"  # Directeur
    ADJUNCT_DIRECTEUR_GENERAAL = "9"  # Adjunct Directeur Generaal
    DIRECTEUR_GENERAAL = "10"  # Directeur Generaal

class DisabilityRiskGroupEnum(Enum):
    """Risicogroep AO enum"""
    EMPTY = ""  # Empty value
    ZONDER_VOORWERP = "000"  # Zonder voorwerp
    # Workers (001-006)
    ARBEIDER_ZONDER_VERPLAATSINGEN = "001"  # Arbeider zonder verplaatsingen
    ARBEIDER_OP_WERF = "002"  # Arbeider op de werf
    HUISBEWAARDERS = "003"  # Huisbewaarders
    SCHOONMAAK_ONDERHOUD = "004"  # Schoonmaak- en onderhoudspersoneel
    KEUKENPERSONEEL = "005"  # Keukenpersoneel (niet te gebruiken door HORECA-ondernemingen)
    CHAUFFEUR = "006"  # Chauffeur
    # Employees (401-412)
    BEDIENDE_ZONDER_VERPLAATSINGEN = "401"  # Bediende zonder verplaatsingen
    BEDIENDE_OCCASIONELE_OPDRACHTEN = "402"  # Bediende met occasionele opdrachten buiten de onderneming
    BEDIENDE_REGELMATIGE_OPDRACHTEN = "403"  # Bediende met regelmatige opdrachten buiten de onderneming
    VERTEGENWOORDIGER = "404"  # Vertegenwoordiger, reizend personeel, loopjongen
    BEDIENDE_MANUEEL_WERK = "405"  # Bediende die manueel werk verricht
    THUISWERKENDE_BEDIENDE = "406"  # Thuiswerkende bediende
    VERZORGEND_PERSONEEL = "407"  # Verzorgend personeel
    VERKOPER = "408"  # Verkoper
    VOETBALLER_BETAALD = "409"  # Voetballer onderworpen aan het statuut van betaalde sportbeoefenaar
    VOETBALLER_HOOG = "410"  # Voetballer niet onderworpen aan het statuut van betaalde sportbeoefenaar van 1239,47 EUR of meer
    VOETBALLER_LAAG = "411"  # Voetballer niet onderworpen aan het statuut van betaalde sportbeoefenaar minder dan 1239,47
    ANDERE_SPORTBEOEFENAAR = "412"  # Andere sportbeoefenaar dan voetballer (niet gebruiken voor werkgeverscategorie 070)

class APEPlanEnum(Enum):
    """A.P.E. plan enum"""
    EMPTY = ""  # Empty value
    ZONDER_VOORWERP = "0"  # zonder voorwerp
    APE_PROFIT_SECTOR = "3"  # A.P.E. profit-sector

class FunctionLevelEnum(Enum):
    """Function level enum"""
    EMPTY = ""  # Empty value
    UITVOEREND_PERSONEEL = "1"  # Uitvoerend personeel
    KADERPERSONEEL = "2"  # Kaderpersoneel
    LEIDINGGEVEND_PERSONEEL = "3"  # Leidinggevend personeel

class PensionInsuranceProviderEnum(Enum):
    """Pension/Insurance provider enum (De_gi)"""
    EMPTY = ""  # Empty value
    ZONDER_VOORWERP = "000"  # ING Insurance
    ING_INSURANCE = "001"  # AGF De Schelde
    AGF_DE_SCHELDE = "002"  # APRA: Antwerpse Professionele Assurantie
    AGF_BELG_INSURANCE = "006"  # AGF Belg Insurance Assubel NV
    NOORDSTAR_MERCATOR_1 = "007"  # Noordstar - Mercator
    MERCATOR_NOORDSTAR = "008"  # Mercator - Noordstar
    EAGLE_STAR_BRUSSELSE = "009"  # Groep Eagle Star - Brusselse Maatschappij
    FORTIS_AG = "010"  # Fortis AG
    AXA_BELGIUM = "011"  # AXA Belgium
    KBC_VERZEKERINGEN_ABB = "012"  # KBC Verzekeringen (ABB)
    DE_BIJ_DE_VREDE = "013"  # De Bij - De Vrede
    DE_LUIKSE_VERZEKERING = "014"  # De Luikse Verzekering
    DE_BELGISCHE_LLOYD = "016"  # De Belgische Lloyd
    HELVETIA = "017"  # Helvetia
    PATROONKAS = "018"  # Patroonkas
    ZURICH = "019"  # Zurich
    URBAINE_UAP = "021"  # Urbaine U.A.P.
    SV_DE_SOCIALE_VOORZORG = "023"  # SV De Sociale Voorzorg
    FIDEA = "024"  # Fidea
    WINTERTHUR = "025"  # Winterthur
    FEDERALE_VERZEKERINGEN = "032"  # Federale Verzekeringen
    CENTRALE_VERZEKERING = "042"  # Centrale Verzekeringsmaatschappij
    DE_VERENIGDE_MEESTERS = "045"  # De Verenigde Meesters
    DE_STER = "046"  # De Ster
    UTRECHT = "079"  # Utrecht
    ETHIAS = "080"  # Ethias
    LE_MANS_VERZEKERINGEN = "081"  # Le Mans Verzekeringen
    PRECAM = "084"  # Precam
    ALG_VERZ_FRANKRIJK = "085"  # Algemene Verzekeringen van Frankrijk
    KBC_VERZEKERINGEN = "086"  # KBC Verzekeringen
    PV_VERZEKERINGEN = "087"  # PV Verzekeringen
    DELTA_LLOYD_LIFE = "088"  # Delta Lloyd Life
    GAN_LES_ASSUR_NATION = "094"  # Gan-Les Assur Nation
    SECUREX = "096"  # Securex
    GENERALI_BELGIUM = "098"  # Generali Belgium
    ASBL_ALFOMETAL = "159"  # ASBL Alfometal
    ASLK = "200"  # ASLK
    VOLKSVERZEKERINGEN = "201"  # Volksverzekeringen
    DE_NEDERLANDEN_V_1871 = "202"  # De Nederlanden V 1871
    VITA = "203"  # Vita
    DE_FAMILIE = "204"  # De Familie
    SWISS_LIFE_BELGIUM = "205"  # Swiss Life Belgium
    ENNIA = "206"  # Ennia
    L_INTEGRALE = "207"  # L'Integrale
    DKV_INTERNATIONAL = "208"  # DKV International
    RVS = "209"  # RVS
    NAT_KAS_BEDIENDENPENS = "213"  # Nationale Kas voor Bediendenpensioenen
    JUSTITIA = "214"  # Justitia
    AMF_ASS_MAATSCHAPPIJ = "215"  # Amf Ass Maatschappij Financia
    HAMBURG_MANNHEIMER = "216"  # Hamburg Mannheimer
    THIBAUT_COLSON_DE_NEF = "217"  # Thibaut-Colson-De Nef
    MERBEL = "218"  # Merbel
    CB_DIREKT = "219"  # CB Direkt
    CENTRALE_LEVENSVERZ_JOSI = "220"  # Centrale Levensverzekeringsmaatschappij Gi Josi
    AXA_GEMEENSCHAPPELIJKE_KAS = "221"  # AXA Gemeenschappelijke Kas
    VERZ_MAATSCHAPPIJ_VANBREDA = "223"  # Verzekeringsmaatschappij J. Vanbreda & Co
    NAVIGA_NV = "224"  # Naviga NV
    NORWICH_UNION_LIFE = "225"  # Norwich Union Life Insurance Soc
    GOUDSE_VERZEKERINGEN = "226"  # Goudse Verzekeringen
    DE_VERENIGDE_MEESTERS_NV = "227"  # De Verenigde Meesters NV
    ANTVERPIA_LEVEN_NV = "228"  # Antverpia Leven NV
    ZWITSER_LEVEN = "229"  # Zwitser Leven
    DELPHI = "230"  # Delphi
    COMMERCIAL_UNION_BELGIUM = "231"  # Commercial Union Belgium
    ROYAL_NEDERLAND_LEVENSVERZ = "232"  # Royal Nederland Levensverz NV
    AXA_BELGIUM_233 = "233"  # AXA Belgium
    ETHIAS_234 = "234"  # Ethias
    DVV = "235"  # DVV
    FB_VERZEKERINGEN = "236"  # FB Verzekeringen
    ZURICH_LEVENSVERZEKERING = "237"  # Zurich Levensverzekeringsmaatschappij
    DKV_238 = "238"  # Dkv
    CGU_INSURANCE = "239"  # Cgu Insurance
    LOGICA_BELGIUM_VZW = "240"  # Logica Belgium Vzw
    ETHIAS_241 = "241"  # Ethias
    FINA_LIFE_NV = "242"  # Fina Life NV
    ENERBEL = "243"  # Enerbel
    LEVOB_VERZEKERINGEN = "244"  # Levob Verzekeringen
    ZA_VERZEKERINGEN = "245"  # Za Verzekeringen
    VIVIUM_LIFTE_NV = "246"  # Vivium Lifte NV
    CENTRAAL_BEHEER_ACHMEA = "247"  # Centaal Beheer / Achmea
    # Pension funds (300-371)
    VOORZORGSFONDS_BUNGE = "300"  # Voorzorgsfonds Bunge Vzw
    PENSIOENFONDS_AVANTI = "301"  # Pensioenfonds Avanti Cementw
    SOCIAL_FONDS_SPAARKREDIET = "303"  # Social Fonds Spaarkrediet
    ICI_PENSION_FUND = "304"  # Ici Pension Fund Asbl
    UCBEN_PENSIOENFONDS = "305"  # Ucben pensioenfonds
    PENSIOENPLAN_MONSANTO = "306"  # Pensioenplan Monsanto
    PENSIOENFONDS_MERBEL = "307"  # Pensioenfonds Merbel Vzw
    VOORZORGSFONDS_ADB = "308"  # Voorzorgsfonds A.D.B.
    PENSIOENFONDS_BP_OV = "309"  # Pensioenfonds BP Ov
    ABOTT_BELG_PENSION_FUND = "310"  # Abott Belg Pension Fund
    PENSIOENFONDS_BTMC = "311"  # Pensioenfonds NV Btmc Vzw
    VOORZORGFONDS_BELGOPROCESS = "312"  # Voorzorgfonds Belgoprocess Vzw
    VOORZORGFONDS_EUROCHEMIC = "313"  # Voorzorgfonds Eurochemic Vzw
    PENSIOENFONDS_SPIERS = "314"  # Pensioenfonds Spiers Vzw
    CGR_TECNOMATIC_PENSIOEN = "315"  # Cgr-Tecnomatic Pensioenfonds
    PENSIOENFONDS_FORD = "316"  # Pensioenfonds Ford Vzw
    WELLCOME_PENSIOENFONDS = "317"  # Vzw Wellcome Pensioenfonds
    QUAKER_OATS_EUR_BENEFIT = "318"  # Quaker Oats Eur. Empl. Benefit
    PENSIOENFONDS_INTERBREW = "319"  # Pensioenfonds Interbrew Vzw
    ACTUA_PENSIOEN_GTI = "320"  # Actua Pensioenfonds Groep Gti Vzw
    AZ_VUB_PENSIOENFONDS = "321"  # Az Vub Pensioenfonds Vzw
    ELGABEL_VZW = "322"  # Elgabel Vzw
    PENSIOBEL_OUD_VZW = "323"  # Pensiobel Oud Vzw
    PENSIOENFONDS_MOBIL = "324"  # Pensioenfonds Mobil Belgie Vzw
    LES_MOUSTIQUES_PRVOYANTS = "325"  # Les Moustiques Prvoyants Asbl
    ABN_AMRO_BANK = "326"  # Abn Amro Bank NV
    NIKE_BELGIUM_PENSIOENFONDS = "327"  # Nike Belgium Pensioenfonds Vzw
    PENSIOENFONDS_PHILIPS = "328"  # Pensioenfonds Philips Eindhoven
    SPILLERS_PETFDS_BENEFIT = "329"  # Spillers Petfds Empl Ben Fund
    BELGIAN_SHELL_PENSIOENFONDS = "330"  # Belgian Shell Pensioenfonds Vzw
    ROYALE_LIFE = "331"  # Royale Life
    INFACT_NV = "332"  # Infact NV
    SPAARPLAN_ARB_CDV_50458 = "333"  # Vzw Spaarplan Arb Cdv 50458
    BASF_SPRPL_TARBED_50467 = "334"  # Vzw Basf Sprpl Tarbed Cdv 50467
    BASF_SPRPL_KADER_50462 = "335"  # Vzw Basf Sprpl Kader Cdv 50462
    BASF_SPRPL_HOGKAD_50463 = "336"  # Vzw Basf Sprpl Hogkad Of 50463
    PENSIOENFONDS_BELGIAN_SHELL = "337"  # Pensioenfonds Belgian Shell
    OUDERDOMSTOELAGE_SHELL = "338"  # Ouderdomstoelage Werkloosheid Shell
    WESTINGHOUSE_PENSION = "339"  # Westhinghouse Pension Fund Belgium
    AANV_PENSIOEN_BBL = "340"  # Vzw Aanvullend Pensioen van de BBL
    PENSIOENPLAN_SOLUTIA = "341"  # Ver Vh Pensioenplan Solutia Vzw
    PENSIOENFONDS_AXA_BANK = "342"  # Vzw Pensioenfonds AXA Bank
    OV_PENSIOEN_ARBEIDERSPERS = "343"  # Ov Pensioenfonds Arbeiderspers Decloedt
    PENSIOENFONDS_FURNESS = "344"  # Pensioenfonds Furness Belgium
    PENSION_FUND_NUTRECO = "345"  # Pension Fund Nutreco Belg Ov
    PENSIOBEL_OUD_GAZELEC = "346"  # Pensiobel Oud Gazelec
    PENSIOBEL_SECTOR = "347"  # Pensiobel Sector
    ELGABEL_1943 = "348"  # Elgabel 1943
    PARITAIR_REGIME = "349"  # Paritair Regime
    POWERBEL_DIRECTIE = "350"  # Powerbel Directie
    POWERBEL_KADER = "351"  # Powerbel Kader
    PENSIOENFONDS_RAVAGO = "352"  # Pensioenfonds Ravago Plastics
    PENSIOENFONDS_BASF_BELG = "353"  # Pensioenfonds Basf Belg Vzw
    PENSIOENFONDS_PFIZER = "354"  # Pensioenfonds Pfizer Vzw
    PENSIOENFONDS_SOLVAY = "355"  # Pensioenfonds Solvay
    CERESTAR_PENSIOENFONDS = "356"  # Cerestar Pensioenfonds
    PENSIOENFONDS_DEUTSCHE_BANK = "357"  # Pensioenfonds Deutsche Bank
    PENSIOENFONDS_TEXACO = "358"  # Pensioenfonds Texaco Vzw
    OVV_PENSIOENFONDS_OLEON = "359"  # Ovv Pensioenfonds Oleon
    PENSIOENFONDS_FURNESS_LOG = "360"  # Pensioenfonds Furness Logistics
    PROTECT_PENSIOENFONDS_OVV = "361"  # Protect pensioenfonds OVV
    PENSIOENFONDS_RAVAGO_369 = "369"  # Pensioenfonds Ravago Plastics
    PENSIOEN_HANDEL_BRANDST = "370"  # Vzw Pensioenfonds Handel Brandst
    PENSIOEN_HUISVEST_ANTW = "371"  # Pensioenfonds huisvestingsmaatschappij Antwerpen VZW
    # Insurance companies (400-440)
    THEE_LEE_INT_LIFE = "400"  # Thee Lee Int Life Insurance
    CTRL_BEHEER_PENSIOENVERZ = "401"  # Ctrl Beheer Pensioenverzekering
    DE_NATIONALE_NEDERLANDEN = "402"  # De Nationale Nederlanden
    WINTERTHUR_403 = "403"  # Winterthur
    ENNIA_404 = "404"  # Ennia
    TVD_PENSIOENFONDS = "405"  # Tvd Pensioenfonds
    STICHTING_PENSIOEN_WILMA = "406"  # Stichting Pensioen Wilma
    PENSIONSKLASSE_510 = "407"  # Pensionsklasse 510
    CENTRALE_LEVENSVERZEKERINGSBANK = "408"  # Centrale Levensverzekeringsbank
    DE_AREND = "409"  # De Arend
    SWISS_LIFE_BELGIUM_410 = "410"  # Swiss Life Belgium
    ST_PHV_PUYENBROECK = "411"  # St PHV Puyenbroeck
    BAH_DEITERSFONDS = "412"  # Bah Deitersfonds
    DBV_LEVENSVERZEKERINGSMAATSCHAPPIJ = "413"  # Dbv Levensverzekeringsmaatschappij Nv
    AGF_BELG_INSURANCE_SA = "414"  # Agf Belg Insurance Sa
    ERIDANIA_BEGHIN_SAY = "415"  # Eridania Beghin Say Pensioenfonds
    AXA_INDUSTRY_NV = "416"  # Axa Industry Nv
    PENSIOENFONDS_NESTLE = "417"  # Pensioenfonds Nestle
    AEGON_VERZEKERINGEN = "418"  # Aegon Verzekeringen
    ELVIA = "419"  # Elvia
    PENSIOENKAS_BAZEL = "420"  # Pensioenkas Bazel Vzw
    CONTASSUR = "421"  # Contassur
    AMEV_NV = "422"  # Amev Nv
    PENSIOENFONDS_CPC_GROUP = "423"  # Pensioenfonds Cpc Group Belg Vzw
    DE_INTEGRALE_424 = "424"  # De Integrale
    DHL_INT_PENSIOENFONDS = "425"  # Dhl International Pensioenfonds
    UNAT = "426"  # U.N.A.T.
    STICHTING_PENSIOEN_WESSAMEN = "427"  # Stichting Pensioenfonds Wessamen
    ZENECA_PENSION_FUND = "428"  # Zeneca Pension Fund Belgium Vzw
    ICI_PENSION_FUND_429 = "429"  # Ici Pension Fund Vzw
    BELSTAR = "430"  # Belstar
    OMNIVER_KBC = "431"  # Omniver (Kbc Verzekeringen)
    ALPHA_LIFE = "432"  # Alpha-Life
    DHL_EMPLOYEE_BENEFIT = "433"  # Dhl Employee Benefit Fund
    PENSIOENKAS_TRACTEBEL = "434"  # Pensioenkas Tractebel
    AON_BELGIUM_NV = "435"  # Aon Belgium Nv
    DELTA_LLOYD_LEVENSVERZ = "436"  # Delta Lloyd Levensverzekeringen
    KAPBBL_VZW = "437"  # K.A.P.B.B.L. Vzw
    CAISSE_COMMUNALE_INTEGRALE = "438"  # Caisse Communale L'Integrale
    SA_VERMONT = "439"  # Sa Vermont
    PENSIOENFONDS_BETZ_DEARBORN = "440"  # Pensioenfonds Betz Dearborn
    # Additional providers (450-466)
    FORTIS_PLUS_AXA = "450"  # Fortis +Axa
    CGL = "451"  # Cgl
    ZELIA_NV = "452"  # Zelia Nv
    AGRR = "453"  # Agrr
    VERSPIEREN = "454"  # Verspieren
    CAVCIC = "455"  # Cavcic
    VNPS = "456"  # Vnps
    HERCULES_PENSIOENFONDS = "457"  # Hercules Pensioenfonds Vzw
    DELTA_LLOYD_458 = "458"  # Delta Lloyd
    DEXIA_INSURANCE = "459"  # Dexia Insurance
    LA_LUXEMBOURGEOISE_VIE = "460"  # La Luxembourgeoise Vie
    LION_BELGE = "461"  # Lion Belge
    BELGISCH_NOTARIAAT = "462"  # Belgisch notariaat
    ING_INSURANCE_463 = "463"  # ING Insurance
    PENSIOENSFONDS_SG_BANK = "464"  # Pensioensfonds SG Bank De Maertelaere
    MONROE_PENSIOENFONDS = "465"  # Monroe Pensioenfonds
    CORONA_DIRECT_VERZEKERINGEN = "466"  # Corona Direct Verzekeringen

class ResearchTypeEnum(Enum):
    """Type onderzoek enum"""
    EMPTY = ""  # Empty value
    UNIVERSITEITEN_65 = "1"  # Universiteiten 65%
    SAMENWERKINGSOVEREENKOMST_50 = "2"  # Samenwerkingsovereenkomst met een universiteit 50%
    PHD_DOCTORS_25 = "3"  # PH. D's (doctors) 25%
    YOUNG_INNOVATIVE_50 = "4"  # Young innovative company 50%
    ANDERE_WET_INST_50 = "5"  # Andere wetenschappelijke instellingen 50%
    SPECIFIEKE_MASTERDIPLOMAS = "6"  # Specifieke masterdiploma's
    SPECIFIEKE_BACHELOR = "7"  # Specifieke bachelor

class HealthcareGradeFunctionEnum(Enum):
    """Graad/functie enum - Healthcare specific (MZG)"""
    EMPTY = ""  # Empty value
    # Management (108xx)
    DIRECTIE = "10800"  # Directie (2)
    ADJUNCT_DIRECTIE = "10801"  # Adjunct van de directie (2)
    HOOFDGENEESHEER = "10810"  # Hoofdgeneesheer (2)
    ADMINISTRATIEF_DIRECTEUR = "10830"  # Administratief Directeur (2)
    # Scientific staff (114xx)
    BIOCHEMICUS = "11416"  # Biochemicus (5)
    FYSICUS = "11426"  # Fysicus (5)
    APOTHEKER_BIOCHEMICUS = "11476"  # Apotheker-Biochemicus (5)
    APOTHEKER = "11486"  # Apotheker (5)
    BURGERLIJK_ING_MEDTECH = "11496"  # Burgerlijk ingenieur (in medisch-technische diensten) (5)
    ANDERE_WETENSCHAPPELIJK = "11906"  # Andere (5)
    # Support staff (123xx)
    SCHOONMAAK_KEUKEN = "12326"  # Schoonmaak, keuken, was en linnen personeel en ploegbaas (1)
    BURG_ING_ONDERHOUD = "12336"  # Burgerlijk ingenieur (in de onderhoudsdiensten) (1)
    ONDERHOUDSWERKMAN = "12337"  # Onderhoudswerkman en ploegbaas (1)
    INDUSTRIEEL_ING = "12376"  # Industrieel of technisch ingenieur (1)
    TECHNICUS = "12377"  # Technicus (o.a. onderhoud van medisch materieel) (1)
    BRANCARDIER = "12396"  # Brancardier (1)
    BEWAKINGSAGENT = "12397"  # Bewakingsagent (Generatiepact) (1)
    STUDENT_SUPPORT = "12399"  # Student (1)
    # Administrative staff (135xx)
    DIRECTEUR_DEPARTEMENT = "13502"  # Directeur departement (hoofd van de personeeldienst, enz.) (2)
    BESTUURSCHEF = "13504"  # Bestuurschef (2)
    DIRECTIESECRETARIS = "13516"  # Directiesecretaris (2)
    BESTUURSSECRETARIS = "13517"  # Bestuurssecretaris (2)
    BESTUURSASSISTENT = "13518"  # Bestuursassistent (2)
    MEDISCH_SECRETARIS = "13526"  # Medisch secretaris (2)
    BOEKHOUDER = "13536"  # Boekhouder (2)
    ANALIST = "13546"  # Analist (2)
    PROGRAMMEUR = "13547"  # Programmeur (2)
    OPERATEUR = "13548"  # Operateur (2)
    ECONOOM = "13556"  # Econoom (2)
    ONTHAAL_TELEFONIST = "13566"  # Onthaal-Telefonist (2)
    KLERK = "13596"  # Klerk (2)
    STUDENT_ADMIN = "13599"  # Student (2)
    MAATSCHAPP_ASSIST = "13626"  # Maatschapp.assist. en assist. psycholoog (hoofd inbegrepen) (2)
    OMBUDSMAN = "13627"  # Ombudsman/vrouw patiëntenrechten (2)
    INTERCULTUREEL_BEMIDDELAAR = "13628"  # Intercultureel bemiddelaar (2)
    ONDERWIJZER_ADMIN = "13636"  # Onderwijzer (2)
    OPVOEDER_ADMIN = "13637"  # Opvoeder (2)
    AALMOEZENIER = "13646"  # Aalmoezenier, lekenraadgever, enz. (2)
    # Nursing staff (241xx-251xx)
    HOOFD_VERPLEEGKUNDIG_DEP = "24102"  # Hoofd van het verpleegkundig departement (3)
    VERPLEEGKUNDIG_DIENSTHOOFD = "24103"  # Verpleegkundig-diensthoofd (Middenkader) (3)
    HOOFDVERPLEEGKUNDIGE = "24104"  # Hoofdverpleegkundige (3)
    ADJUNCT_HOOFDVERPLEEGKUNDIGE = "24105"  # Adjunct-hoofdverpleegkundige (3)
    PERSONEEL_54BIS = "24115"  # 54 bis personeel (3)
    GEGRAD_VERPLEEGKUNDIGE = "24116"  # Gegradueerd verpleegkundige (3)
    GEBREV_VERPLEEGKUNDIGE = "24117"  # Gebrevetteerd verpleegkundige (3)
    GEGRAD_PSYCH_VERPLEEGK = "24126"  # Gegradueerd psychiatrisch verpleegkundige (3)
    GEBREV_PSYCH_VERPLEEGK = "24127"  # Gebrevetteerd psychiatrisch verpleegkundige (3)
    GEGRAD_KINDERVERPLEEGK = "24136"  # Gegradueerd kinderverpleegkundige (3)
    GEGRAD_SOCIAAL_VERPLEEGK = "24137"  # Gegradueerd sociaal verpleegkundige (3)
    VERPLEEGK_BBT_INTENSIEF = "24140"  # Verpleegkundige BBT voor de intensieve zorg en spoedgevallen (3)
    VERPLEEGK_BBT_GERIATRIE = "24141"  # Verpleegkundige BBT gespecialiseerd in geriatrie (3)
    VERPLEEGK_BBT_ONCOLOGIE = "24142"  # Verpleegkundige BBT gespecialiseerd in de oncologie (3)
    BBT_PEDIATRIE = "24143"  # BBT pediatrie en neonatologie (3)
    BBT_GEEST_GEZONDHEID = "24144"  # BBT gespecialiseerd in geest. gezondheidszorg en psychiatrie (3)
    BBT_PERI_OPERATIEF = "24145"  # BBT gespecialiseerd in de peri-operatieve zorg (3)
    ANDERE_BBT = "24150"  # Andere verpleegkundige die houder is van een BBT (3)
    BBB_GERIATRIE = "24151"  # Verpleegkundige BBB met bijz. deskundigheid in de geriatrie (3)
    BBB_DIABETOLOGIE = "24152"  # BBB diabetologie (3)
    BBB_GEEST_GEZONDHEID = "24153"  # BBB bijz. desk. in geest. gezondheidszorg en psychiatrie (3)
    BBB_PALLIATIEF = "24154"  # Verpleegkundige BBB met bijz. desk. in de palliatieve zorg (3)
    ANDERE_BBB = "24156"  # Andere verpleegkundige BBB met een bijzondere deskundigheid (3)
    VROEDVROUW_DIENSTHOOFD = "24163"  # Vroedvrouw -Diensthoofd (3)
    HOOFDVROEDVROUW = "24164"  # Hoofdvroedvrouw (3)
    ADJUNCT_HOOFDVROEDVROUW = "24165"  # Adjunct - hoofdvroedvrouw (3)
    VROEDVROUW = "24166"  # Vroedvrouw (3)
    OPVOEDER_VERPLEEG = "24176"  # Opvoeder (3)
    ONDERWIJZER_VERPLEEG = "24186"  # Onderwijzer (3)
    ASSIST_ZIEKENHUISVERZORGING = "24196"  # Assistent in ziekenhuisverzorging (3)
    PSYCH_ASSIST_ZIEKENHUISVERZORGING = "24197"  # Psychiatrisch assistent in ziekenhuisverzorging (3)
    STUDENT_VERPLEEG = "24199"  # Student (3)
    ZORGKUNDIGE = "25200"  # Zorgkundige (3)
    KINDERVERZORGSTER = "25226"  # Kinderverzorgster (3)
    KINDERVERZORGSTER_GENERATIEPACT = "25230"  # Kinderverzorgster (Generatiepact) (3)
    ZIEKENHUISSECRETARIS = "25256"  # Ziekenhuissecretaris (van een verpleegeenheid) (3)
    STUDENT_VERZORGING = "25299"  # Student (3)
    LOGISTIEK_ASSISTENT = "25300"  # Logistiek assistent (3)
    # Paramedical staff (364xx)
    HOOFD_MED_LAB_TECH = "36414"  # Hoofd medisch laboratorium technoloog (4)
    ADJUNCT_HOOFD_MED_LAB = "36415"  # Adjunct - hoofd medisch laboratorium technoloog (4)
    MED_LAB_TECHNOLOOG = "36416"  # Medisch laboratorium technoloog (4)
    HOOFD_TECH_MED_BEELD = "36424"  # Hoofd technoloog medische beeldvorming (4)
    ADJUNCT_HOOFD_TECH_BEELD = "36425"  # Adjunct - hoofd technoloog medische beeldvorming (4)
    TECH_MED_BEELDVORMING = "36426"  # Technoloog medische beeldvorming (4)
    TECHNICUS_MED_MATERIAAL = "36434"  # Technicus van het medisch materiaal (4)
    HOOFDDIETIST = "36444"  # Hoofddiëtist (4)
    ADJUNCT_HOOFDDIETIST = "36445"  # Adjunct - hoofddiëtist (4)
    DIETIST = "36446"  # Diëtist (4)
    HOOFDKINESITHERAPEUT = "36454"  # Hoofdkinesitherapeut of hoofdergotherapeut (4)
    ADJUNCT_HOOFDKINESITHERAPEUT = "36455"  # Adjunct - hoofdkinesitherapeut of adjunct - hoofdergotherap. (4)
    KINESITHERAPEUT = "36456"  # Kinesitherapeut of ergotherapeut (4)
    HOOFDLOGOPEDIST = "36464"  # Hoofdlogopedist (4)
    ADJUNCT_HOOFDLOGOPEDIST = "36465"  # Adjunct - hoofdlogopedist (4)
    LOGOPEDIST = "36466"  # Logopedist (4)
    HOOFDAUDIOLOOG = "36467"  # Hoofdaudioloog - hoofdaudicien (4)
    AUDIOLOOG = "36468"  # Audioloog - audicien (4)
    HOOFDPSYCHOLOOG = "36469"  # Hoofdpsycholoog in verplegeneenheden (4)
    PSYCHOLOOG = "36470"  # Psycholoog in verplegeneenheden (4)
    HOOFDBANDAGIST = "36471"  # Hoofdbandagist, hoofdorthesist, hoofdprothesist (4)
    BANDAGIST = "36472"  # Bandagist, orthesist, prothesist (4)
    ORTHOPEDAGOOG = "36473"  # Orthopedagoog (4)
    PEDAGOOG = "36474"  # Pedagoog (4)
    HOOFDORTHOPTIST = "36475"  # Hoofdorthoptist (4)
    ORTHOPTIST = "36476"  # Orthoptist (4)
    HOOFD_FARM_TECH_ASSIST = "36477"  # Hoofd farmaceutisch-technisch assistent (4)
    FARM_TECH_ASSISTENT = "36478"  # Farmaceutisch-technisch assistent (4)
    HOOFDPODOLOOG = "36479"  # Hoofdpodoloog (4)
    PODOLOOG = "36480"  # Podoloog (4)
    AMBULANCIER = "36481"  # Ambulancier (4)
    MAATSCHAPP_ASSIST_PARAMEDISCH = "36486"  # Maatschappelijk assistent en assistent-psycholoog (4)
    ANDER_PARAMEDISCH = "36496"  # Ander paramedisch personeel (4)
    STUDENT_PARAMEDISCH = "36499"  # Student (4)
    # Medical staff (470xx)
    HOOFDGENEESHEER_CAMPUS = "47000"  # Hoofdgeneesheer van een ziekenhuis campus (0)
    ADJUNCT_HOOFDGENEESHEER = "47001"  # Adjunct - hoofdgeneesheer van een ziekenhuis campus (0)
    GENEESHEER_DIRECTEUR = "47003"  # Geneesheer-directeur van het departement (0)
    GENEESHEER = "47016"  # Geneesheer (0)
    VERBLIJVEND_GENEESHEER = "47026"  # Verblijvend geneesheer (0)
    RAADGEVEND_GENEESHEER = "47036"  # Raadgevend geneesheer (0)
    KANDIDAAT_GENEESHEER_SPECIALIST = "47046"  # Kandidaat geneesheer specialist (0)
    KANDIDAAT_GENEESHEER_ALGEMEEN = "47056"  # Kandidaat geneesheer algemene geneeskunde (0)
    STUDENT_GENEESKUNDE = "47099"  # Student in de geneeskunde (0)
    # Other
    GEEN_CONTROLE = "99999"  # Geen controle op aard en type (X)

class HealthcarePersonnelCategoryEnum(Enum):
    """MZG-personeelscategorie enum - Healthcare personnel category"""
    EMPTY = ""  # Empty value
    VERPLEEGK_UNIV_DIPLOMA = "01"  # Verpleegk./vroedvrouw met univ.diploma
    VERPLEEGK_HO_DIPLOMA = "02"  # Verpleegk./vroedvrouw met diploma HO
    VERPLEEGK_HSO_BREVET = "03"  # Verpleegk. met diploma HSO/brevet
    VERZORGEND_PERSONEEL = "04"  # Verzorgend personeel
    LOGISTIEKE_ONDERSTEUNING = "05"  # Logistieke ondersteuning
    STUDENTEN = "06"  # Studenten

class HealthcareFunctionEnum(Enum):
    """MZG-functie enum - Healthcare function"""
    EMPTY = ""  # Empty value
    HOOFDVERPLEEGKUNDIGE = "F11001"  # Hoofdverpleegkundige
    ADJUNCT_HOOFDVERPLEEGKUNDIGE = "F11002"  # Adjunct-hoofdverpleegkundige
    HOOFDVROEDVROUW = "F12001"  # Hoofdvroedvrouw
    ADJUNCT_HOOFDVROEDVROUW = "F12002"  # Adjunct-hoofdvroedvrouw
    VERPLEEGKUNDIGE = "F21001"  # Verpleegkundige
    REF_VERPL_WONDZORG = "F21002"  # Ref.verpl. voor wondzorg en stomatherapie
    REF_VERPL_PIJNBESTRIJDING = "F21003"  # Ref.verpl. voor pijnbestrijding
    REF_VERPL_DIABETES = "F21004"  # Ref.verpl. voor opvang v diabetespatiënt
    VERPLEEGK_KLINISCH_ONDERZOEK = "F21005"  # Verpleegkundige klinisch onderzoek
    ANDERE_REFERENTIEVERPLEEGK = "F21009"  # Andere referentieverpleegkundigen
    VROEDVROUW = "F22001"  # Vroedvrouw
    VERZORGEND_PERS_ZORGKUNDIGE = "F40001"  # Verzorgend pers: zorgkundige, personeel
    ONDERSTEUNEND_PERS = "F50001"  # Ondersteunend pers in afwachting van eve
    PARAMEDISCH_PERS = "F60001"  # Paramed.pers: ergother., kinesither., lo
    PERS_BLOEDAFNAME = "F60002"  # Personeel voor (bloed)afname
    PERS_OPVOEDING_ONDERWIJS = "F70001"  # Pers opvoeding/onderwijs : opvoeder, spe
    PSYCHOSOC_PERS = "F70002"  # Psychosoc.pers: soc.assistent, cult.bemi
    PERS_INTERN_PATIENTENVERVOER = "F80002"  # Personeel voor intern patiëntenvervoer
    REGISTRATIEPERS_VG_MZG = "F80011"  # Registratiepersoneel VG-MZG
    REGISTRATIEPERS_ICD9 = "F80012"  # Registratiepersoneel ICD9
    REGISTRATIEPERS_ANDERE = "F80019"  # Registratiepersoneel andere gegevens
    ANDERE = "F99999"  # Andere

class HealthcareQualificationEnum(Enum):
    """MZG-kwalificatie enum - Healthcare qualification"""
    EMPTY = ""  # Empty value
    # University diplomas (Q100xx)
    DIPL_DR_SOC_GEZONDHEID = "Q10001"  # Dipl Dr.soc.gezondheidswet. <verpleegk/v
    UNIV_DIPL_SOC_GEZONDHEID = "Q10002"  # Univ dipl soc.gezondheidswet. <verpleegk
    # Graduate nursing (Q200xx)
    DIPL_GEGRAD_ZIEKENHUIS_VERPL = "Q20001"  # Dipl gegrad ziekenhuisverpl/bach verplee
    DIPL_GEGRAD_VROEDVROUW = "Q20002"  # Dipl gegrad vroedvrouw/bach vroedkunde
    # Specialized nursing (Q210xx)
    DIPL_VERPLEEGK_SPEC_INTENSIEF = "Q21001"  # Dipl verpleegk spec.intensieve zorg/spoe
    DIPL_VERPLEEGK_SPEC_PEDIATRIE = "Q21002"  # Dipl verpleegk spec. Pediatrie/neonatolo
    DIPL_VERPLEEGK_SPEC_SOCIAAL = "Q21003"  # Dipl verpleegk spec. sociale gezondheids
    DIPL_VERPLEEGK_SPEC_GEESTELIJK = "Q21004"  # Dipl verpleegk spec. geestelijke gezondh
    DIPL_VERPLEEGK_SPEC_GERIATRIE = "Q21005"  # Dipl verpleegk spec. geriatrie
    DIPL_VERPLEEGK_SPEC_ONCOLOGIE = "Q21006"  # Dipl verpleegk spec. oncologie
    DIPL_VERPLEEGK_SPEC_MED_BEELD = "Q21007"  # Dipl verpleegk spec. medische beeldvormi
    DIPL_VERPLEEGK_SPEC_STOMA = "Q21008"  # Dipl verpleegk spec. Stomatherapie/wondz
    DIPL_VERPLEEGK_SPEC_OPERATIE = "Q21009"  # Dipl verpleegk spec. Operatieass/instrum
    DIPL_VERPLEEGK_SPEC_PERFUSIONIST = "Q21010"  # Dipl verpleegk spec. als perfusionist
    DIPL_VERPLEEGK_SPEC_ANESTHESIE = "Q21011"  # Dipl verpleegk spec. anesthesie
    DIPL_KADEROPL_VERPLEEGK = "Q22001"  # Dipl kaderopl verpleegkunde <verpleegk/v
    # Graduate with special expertise (Q230xx)
    GEGRAD_VERPL_DESK_GEEST = "Q23001"  # Gegrad verpl/bach bijz. desk. geest gezo
    GEGRAD_VERPL_DESK_GERIATRIE = "Q23002"  # Gegrad verpl/bach bijz. desk. geriatrie
    GEGRAD_VERPL_DESK_WONDZORG = "Q23003"  # Gegrad verpl/bach bijz. desk. wondzorg
    GEGRAD_VERPL_DESK_PALLIATIEF = "Q23004"  # Gegrad verpl/bach bijz. desk. palliatiev
    GEGRAD_VERPL_DESK_DIABETOLOGIE = "Q23005"  # Gegrad verpl/bach bijz. desk. diabetolog
    GEGRAD_VERPL_DESK_EVALUATIE = "Q23006"  # Gegrad verpl/bach bijz. desk. Evaluatie/
    # Certificate holders (Q300xx)
    BREVET_VERPLEGER = "Q30001"  # Brevet van verpleger / Dipl verpleegkund
    BREVET_PSYCH_VERPLEEGK = "Q30002"  # Brevet van psychiatrisch verpleegk
    # Certificate with special expertise (Q330xx)
    GEBREV_VERPL_DESK_GEEST = "Q33001"  # Gebrev verpl bijz. desk. geest gezondh e
    GEBREV_VERPL_DESK_GERIATRIE = "Q33002"  # Gebrev verpl bijz. desk. geriatrie
    GEBREV_VERPL_DESK_WONDZORG = "Q33003"  # Gebrev verpl bijz. desk. wondzorg
    GEBREV_VERPL_DESK_PALLIATIEF = "Q33004"  # Gebrev verpl bijz. desk. palliatieve zor
    GEBREV_VERPL_DESK_DIABETOLOGIE = "Q33005"  # Gebrev verpl bijz. desk. diabetologie
    GEBREV_VERPL_DESK_EVALUATIE = "Q33006"  # Gebrev verpl bijz. desk. Evaluatie/behan
    # Care personnel (Q400xx)
    BEROEPSTITEL_ZORGK = "Q40001"  # Beroepstitel zorgk/pers registratie zorg
    PERSONEEL_54BIS = "Q40002"  # Personeel artikel 54bis
    BREVET_ZIEKENHUISASSISTENT = "Q40003"  # Brevet ziekenhuisassistent
    BREVET_PSYCH_ZIEKENHUISASSIST = "Q40004"  # Brevet psychiatrisch ziekenhuisassistent
    # Secondary education (Q500xx)
    DIPL_SEC_OND_ZORGKUNDIGE = "Q50001"  # Dipl sec ond: ev erkenning zorgkundige/k
    # Paramedical diplomas (Q600xx)
    DIPL_ERGOTHERAPEUT = "Q60001"  # Diploma ergotherapeut
    DIPL_KINESITHERAPEUT = "Q60002"  # Diploma kinesitherapeut
    DIPL_LOGOPEDIST = "Q60003"  # Diploma logopedist
    DIPL_DIETIST = "Q60004"  # Diploma diëtist
    DIPL_LABORANT = "Q60005"  # Diploma laborant
    # Education and support (Q700xx)
    DIPL_OPVOEDER = "Q70001"  # Diploma opvoeder
    DIPL_ONDERWIJS = "Q70002"  # Diploma voor onderwijs
    DIPL_SOCIAAL_ASSISTENT = "Q70003"  # Diploma sociaal assistent
    DIPL_PSYCHOLOOG = "Q70004"  # Diploma psycholoog
    DIPL_TECH_MED_BEELDVORMING = "Q70005"  # Dipl technoloog in de medische beeldvorm
    DIPL_GEGRAD_MED_SECRETARIS = "Q70006"  # Dipl gegradueerde medisch secretaris - e
    # Other
    ANDERE = "Q99999"  # Andere

class PersonnelCategoryType1Enum(Enum):
    """Personeelscat-aard1 enum - Personnel category nature 1"""
    EMPTY = ""  # Empty value
    MEDISCH_0 = "0"  # Medisch
    LOONTREKKEND = "1"  # Loontrekkend
    ADMINISTRATIEF_2 = "2"  # Administratief
    VERPLEGEND = "3"  # Verplegend
    PARAMEDISCH = "4"  # Paramedisch
    ANDERE = "5"  # Andere
    MEDISCH_A = "A"  # Medisch
    PARAMEDISCH_B = "B"  # Paramedisch
    VERPLEGEND_C = "C"  # Verplegend
    VERZORGEND = "D"  # Verzorgend
    ADMINISTRATIEF_E = "E"  # Administratief
    KEUKEN = "F"  # Keuken
    ONDERHOUD = "G"  # Onderhoud
    ANDERE_H = "H"  # Andere
    VERZ_OPVOEDEND = "I"  # Verz.&Opvoedend
    SOCIALE_DIENST = "J"  # Sociale dienst
    DIRECTIE = "K"  # Directie
    FACULTATIEF = "L"  # Facultatief
    ANIMATIE = "M"  # Animatie
    PEDAGOGE = "N"  # Pedagoge
    SOC_VERPLEEGK = "O"  # Soc.Verpleegk.
    GEGRAD_VERPL = "P"  # Gegrad.Verpl.
    KINDERVERZORG = "Q"  # Kinderverzorg.
    KLEUTERLEIDING = "R"  # Kleuterleiding

class PersonnelType2Enum(Enum):
    """Personeelstype-aard2 enum - Personnel type nature 2"""
    EMPTY = ""  # Empty value
    NORMAAL = "0"  # Normaal
    STAGIAIR_RVA_SBO = "1"  # Stagiair RVA of SBO (startbaanovereenkomst)
    GESUBSIDIEERDE_CONTRACTUEEL = "2"  # Gesubsidieerde contractueel
    LOGISTIEK_ASSISTENT = "3"  # Logistiek assistent
    SOCIALE_MARIBEL = "4"  # Sociale maribel
    PERS_TER_BESCHIKKING = "5"  # Personen ter beschikking gesteld van het ziekenhuis
    UITZENDKRACHTEN = "6"  # Uitzendkrachten personeel
    STATUTAIREN = "7"  # statutairen
    BRUGGEPENSIONEERDEN = "8"  # bruggepensioneerden

class CommunityEnum(Enum):
    """Gemeenschap enum - Belgian community"""
    EMPTY = ""  # Empty value
    NIET_BEPAALD = "0"  # Niet bepaald
    FRANS = "1"  # Frans
    DUITS = "2"  # Duits
    VLAAMS = "3"  # Vlaams

class RegionEnum(Enum):
    """Gewest enum - Belgian region"""
    EMPTY = ""  # Empty value
    NIET_BEPAALD = "0"  # Niet bepaald
    BRUSSEL = "1"  # Brussel
    VLAANDEREN = "2"  # Vlaanderen
    WALLONIE = "3"  # Wallonië

class ApprenticeshipTypeEnum(Enum):
    """Leerovereenkomst enum - Apprenticeship type"""
    EMPTY = ""  # Empty value
    ALTERNEREND_LEREN_18_PLUS = "1"  # Alternerend leren/werken na 18 jaar
    LEEROVEREENKOMST_MIDDENSTAND = "2"  # Leerovereenkomst middenstand na 18 jaar
    INDUSTRIELE_LEEROVEREENKOMST = "3"  # Industriële leerovereenkomst na 18 jaar
    INDUSTRIELE_SOCIOPROF = "4"  # Industriële socio-professionele leerovereenkomst
    BEROEPSINLEVING_18_PLUS = "5"  # Beroepsinlevingsovereenkomst na 18 jaar (bio-baan)
    ALTERNERENDE_OPL_VLAANDEREN = "6"  # Alternerende opleiding Vlaanderen na 18 jaar
    ALTERNERENDE_OPL_WALLONIE = "7"  # Alternerende opleiding Wallonië na 18 jaar

class EducationLevelAdditionEnum(Enum):
    """Niveau opleiding enum - Education level addition"""
    EMPTY = ""  # Empty value
    LAGER_ONDERWIJS = "1"  # Lager onderwijs
    MIDDELBAAR_ONDERWIJS = "2"  # Middelbaar onderwijs
    BACHELOR = "3"  # Bachelor
    MASTER = "4"  # Master

class RiskClassAdditionEnum(Enum):
    """Risk class addition enum - Additional risk classification"""
    EMPTY = ""  # Empty value
    ARBEIDER_ZONDER_VERPLAATSINGEN = "001"  # Arbeider zonder verplaatsingen
    ARBEIDER_OP_WERF = "002"  # Arbeider op de werf
    HUISBEWAARDERS = "003"  # Huisbewaarders
    SCHOONMAAK_ONDERHOUD = "004"  # Schoonmaak- en onderhoudspersoneel
    KEUKENPERSONEEL = "005"  # Keukenpersoneel
    CHAUFFEUR = "006"  # Chauffeur
    BEDIENDE_ZONDER_VERPLAATSINGEN = "401"  # Bediende zonder verplaatsingen
    BEDIENDE_OCCASIONEEL_OPDRACHTEN = "402"  # Bediende occasioneel opdrachten buiten bedrijf
    BEDIENDE_REGELMATIG_OPDRACHTEN = "403"  # Bediende regelmatig opdrachten buiten bedrijf
    VERTEGENWOORDIGER = "404"  # Vertegenwoordiger, reizend personeel, loopjongen
    BEDIENDE_MANUEEL_WERK = "405"  # Bediende die manueel werk verricht
    THUISWERKENDE_BEDIENDE = "406"  # Thuiswerkende bediende
    VERZORGEND_PERSONEEL = "407"  # Verzorgend personeel
    VERKOPER = "408"  # Verkoper
    VOETBALLER_BETAALD_STATUUT = "409"  # Voetballer met statuut betaald sportbeoefenaar
    VOETBALLER_HOOG_WEDDE = "410"  # Voetballer zonder statuut betaald sportbeoefenaar, jaarwedde groter dan € 1239,46
    VOETBALLER_LAAG_WEDDE = "411"  # Voetballer zonder statuut betaald sportbeoefenaar, jaarwedde kleiner dan € 1239,47
    ANDERE_SPORTBEOEFENAAR = "412"  # Andere sportbeoefenaar dan voetballer

class ContractTypeAdditionEnum(Enum):
    """Contract type addition enum"""
    EMPTY = ""  # Empty value
    ONBEPAALDE_DUUR = "1"  # Onbepaalde duur
    BEPAALDE_DUUR = "2"  # Bepaalde duur
    BEPAALD_WERK = "3"  # Bepaald werk
    VERVANGING_ONBEPAALDE_DUUR = "4"  # Vervanging van onbepaalde duur
    VERVANGING_BEPAALDE_DUUR = "5"  # Vervanging van bepaalde duur

class CompanyPlanEnum(Enum):
    """Bedrijfsplan enum - Company plan"""
    EMPTY = ""  # Empty value
    HERSTRUCTURERINGSPLAN = "1"  # Herstructureringsplan
    BEDRIJFSPLAN_HERVERDELING_PRIVE = "2"  # Bedrijfsplan tot herverdeling van de arbeid in de privésector
    TEWERKSTELLINGSAKKOORD_1995_1996 = "3"  # Tewerkstellingsakkoord voor periode 1995 - 1996
    TEWERKSTELLINGSAKKOORD_1997_1998 = "4"  # Tewerkstellingsakkoord voor periode 1997 - 1998
    CAO_ADV_DEFENSIE = "5"  # CAO met ADV-defensie plan Van Delanotte
    CAO_ADV_OFFENSIE = "6"  # CAO met ADV-offensie plan Van Delanotte
    BEDRIJFSPLAN_HERVERDELING_OPENBAAR = "7"  # Bedrijfsplan tot herverdeling van de arbeid in de openbare sector

class PreviousWorkerTypeEnum(Enum):
    """Vroegere soort werknemer enum - Previous worker type"""
    EMPTY = ""  # Empty value
    BIJZONDER_TIJDELIJK = "1"  # Bijzonder tijdelijk kader
    DERDE_ARBEIDERSCIRCUIT = "2"  # derde arbeiderscircuit
    TEWERKGESTELDE_WERKLOZE = "3"  # tewerkgestelde werkloze
    ANDERE = "4"  # andere

class IPAGCodeEnum(Enum):
    """IPAG/IZAG code enum - Healthcare specialty codes"""
    EMPTY = ""  # Empty value
    ONBEKEND = "0"  # onbekend
    NIET_GESPECIFIEERD_1 = "1"  # niet gespecifieerd
    NIET_GESPECIFIEERD_2 = "2"  # niet gespecifieerd
    HOGER_ALGEMEEN_SECUNDAIR = "3"  # hoger algemeen secundair
    HOGER_TECHNISCH_SECUNDAIR = "4"  # hoger technisch secundair
    HOGER_KUNST_SECUNDAIR = "5"  # hoger kunst secundair
    NIET_VAN_TOEPASSING = "-5"  # Niet van toepassing
    VERPLEEGASPIRANT = "6"  # verpleegaspirant
    NIET_GESPECIFIEERD_8 = "8"  # niet gespecifieerd
    VERZORGING = "9"  # verzorging
    # Care services (10-19)
    KINDERVERZORGING = "10"  # kinderverzorging
    PERSONENZORG = "11"  # personenzorg
    GEZINS_SANITAIRE_HULP = "12"  # gezins- en sanitaire hulp
    NIET_GESPECIFIEERD_13 = "13"  # niet gespecifieerd
    ZIEKENHUISASSISTENT = "14"  # ziekenhuisassistent
    PSYCHIATRISCHE_VERPLEEGKUNDE = "15"  # psychiatrische verpleegkunde
    ZIEKENHUISVERPLEEGKUNDE = "16"  # ziekenhuisverpleegkunde
    GEBREV_VERPLEEGK = "17"  # gebrev verpleegk
    NIET_GESPECIFIEERD_19 = "19"  # niet gespecifieerd
    # Graduate nursing (20-46)
    GEGRADUEERDE_ZIEKENHUISVERPLEEGK = "20"  # gegradueerde ziekenhuisverpleegk
    GEGRADUEERDE_PEDIATRISCHE = "21"  # gegradueerde pediatrische verpleegk
    GEGRAD_SOCIALE_GEZONDHEIDSZORG = "22"  # gegrad. in de socialegezondheidszorg
    GEGRAD_VERPLEEGK_GEEST_GEZONDH = "23"  # gegrad. verpleegk. geest.Gezondh.zorg
    GEGRADUEERDE_GERIATRISCH = "24"  # gegradueerde geriatrische verpleegk
    GEGRAD_VERPLEEGK_INTENS_SPOED = "25"  # gegrad.verpleegk.intens.en spoedgev.zorg
    BIJZ_BEKW_VERPLEEGK_ONCOLOGIE = "26"  # bijz bekw van verpleegk oncologie
    BIJZ_BEKW_MED_BEELDVORMING = "27"  # bijz.bekwam. in medische beeldvorming
    BIJZ_BEKW_VERPLEEGK_OPERATIE = "29"  # bijz bekw van verpleegk operatiekamer
    BIJZ_BEKW_PALLIATIEVE_ZORG = "30"  # bijz.bekwam. in de palliatieve zorg
    BIJZ_BEKW_VERPLEEGK_ENDOSCOPIE = "31"  # bijz bekw van verpleegk endoscopie
    BIJZ_BEKW_VERPLEEGK_HEMODIALYSE = "32"  # bijz bekw van verpleegk hemodialyse
    BIJZ_BEKW_VERPLEEGK_RADIOTHERAPIE = "33"  # bijz bekw van verpleegk radiotherapie
    BIJZ_BEKW_GEZONDHEIDSOPVOEDING = "34"  # bijz.bekwam. in de gezondheidsopvoeding
    BIJZ_BEKW_ADJUNCT_HOOFDVERPLEEGK = "35"  # bijz bekw van adjunct-hoofdverpleegk
    BIJZ_BEKW_HOOFDVERPLEEGK = "36"  # bijz bekw van hoofdverpleegk
    BIJZ_BEKW_VERPLEEGK_HFD_DIENST = "37"  # bijz bekw van verpleegk hoofd van dienst
    BIJZ_BEKW_HFD_GERIATRISCH = "38"  # bijz.bekwam. hfd (geriatrische)verpleegk
    BIJZ_BEKW_HFD_PEDIATRISCH = "39"  # bijz.bekwam. hfd (pediatrische)verpleegk
    BIJZ_BEKW_HFD_PSYCHIATRISCH = "40"  # bijz.bekwam. hfd (psychiatr.)verpleegk.
    BIJZ_BEKW_HFD_VROEDVROUW = "41"  # bijz.bekwam. hfd (vroedvrouw)verpleegk.
    BIJZ_BEKW_PERMAN_OPLEIDING = "42"  # bijz.bekwam. verpleegk. perman. opleidin
    BIJZ_BEKW_ZIEKENHUISHYGIENIST = "43"  # bijz bekw ziekenhuishygiënist
    BIJZ_BEKW_DIRECTEUR_VERPLEEGK = "44"  # bijz. bekwam. directeur verpleegk. depar
    BIJZ_BEKW_KWALIT_BEWAKING = "45"  # bijz. bekwam. verpleegk. kwalit.bewaking
    VROEDVROUW = "46"  # vroedvrouw
    # Graduated allied health (47-71)
    GEGRADUEERDE_ERGOTHERAPIE = "47"  # gegradueerde ergotherapie
    GEGRADUEERDE_KINESITHERAPIE = "48"  # gegradueerde kinesitherapie
    GEGRADUEERDE_ARBEIDSTHERAPIE = "49"  # gegradueerde arbeidstherapie
    GEGRADUEERDE_OTHOPEDIE = "50"  # gegradueerde othopedie
    GEGRADUEERDE_PODOLOGIE = "51"  # gegradueerde podologie
    GEGRADUEERDE_LOGOPEDIE = "52"  # gegradueerde logopedie
    GEGRADUEERDE_AUDIOLOGIE = "53"  # gegradueerde audiologie
    GEGRADUEERDE_KLINISCHE_CHEMIE = "54"  # gegradueerde klinische chemie
    GEGRADUEERDE_DIEETLEER = "55"  # gegradueerde dieetleer
    GEGRADUEERDE_MED_BEELDVORMING = "56"  # gegradueerde medische beeldvorming
    GEGRADUEERDE_OPTIEK_OPTOMETRIE = "57"  # gegradueerde optiek en optometrie
    GEGRAD_MED_LABORATORIUMTECH = "58"  # gegrad. in de med.laboratoriumtechn.
    DIPLOMA_AMBULANCIER = "59"  # diploma van ambulancier
    DIPLOMA_AUDICIEN = "60"  # diploma van audicien
    DIPLOMA_BANDAGIST = "61"  # diploma van bandagist
    DIPLOMA_ORTHESIST = "62"  # diploma van orthesist
    DIPLOMA_PROTHESIST = "63"  # diploma van prothesist
    DIPLOMA_ASSISTENT_PSYCHOLOGIE = "64"  # diploma van assistent psychologie
    GEGRAD_MAATSCHAPPELIJKE_ADVISERING = "65"  # gegrad. in de maatschappelijke adviserin
    GEGRAD_ALGEMEEN_MAATSCH_WERK = "66"  # gegrad. algemeen maatsch.werk
    GEGRAD_PERSONEELSWERK = "67"  # gegradueerde in het personeelswerk
    GEGRAD_SOCIAAL_CULTUREEL = "68"  # gegrad. in het sociaal-cultureel werk
    GEGRAD_ONDERWIJS = "69"  # gegradueerde in het onderwijs
    GEGRADUEERDE_OTHOPEDAGOGIE = "70"  # gegradueerde othopedagogie
    INDUSTRIEEL_INGENIEUR = "71"  # industrieel ingenieur
    NIET_GESPECIFIEERD_72 = "72"  # niet-gespecificeerd
    # Medical specialists (73-99)
    HUISARTS = "73"  # huisarts
    SPECIALIST_ANESTHESIEREANIMATIE = "74"  # specialist in de anesthesiereanimatie
    SPECIALIST_KLINISCHE_BIOLOGIE = "75"  # geneesheer-specialist klinische biologie
    SPECIALIST_CARDIOLOGIE = "76"  # geneesheer-specialist cardiologie
    SPECIALIST_HEELKUNDE = "77"  # geneesheer-specialist heelkunde
    SPECIALIST_NEUROCHIRURGIE = "78"  # geneesheer-specialist neurochirurgie
    SPEC_PLAST_RECONSTR_ESTHET = "79"  # spec. plast. ,reconstr. en esthet. heelk
    SPECIALIST_DERMATOVENEREOLOGIE = "80"  # specialist in de dermatovenereologie
    SPECIALIST_GASTRO_ENTEROLOGIE = "81"  # geneesheer-specialist gastro-enterologie
    SPECIALIST_GYNAECOLOGIE_VERLOSKUNDE = "82"  # specialist in de gynaecologieverloskunde
    SPECIALIST_INWENDIGE_GENEESKUNDE = "83"  # specialist in de inwendige geneeskunde
    SPECIALIST_NEUROLOGIE = "84"  # geneesheer-specialist neurologie
    SPECIALIST_PSYCHIATRIE = "85"  # geneesheer-specialist psychiatrie
    SPECIALIST_NEUROPSYCHIATRIE = "86"  # geneesheer-specialist neuropsychiatrie
    SPECIALIST_OFTALMOLOGIE = "87"  # geneesheer-specialist oftalmologie
    SPECIALIST_ORTHOPEDISCHE_HEELKUNDE = "88"  # specialist in de orthopedische heelkunde
    SPECIALIST_OTORHINOLARYNGOLOGIE = "89"  # specialist in de otorhinolaryngologie
    SPECIALIST_PEDIATRIE = "90"  # geneesheer-specialist pediatrie
    SPECIALIST_FYS_GENEESK_REVAL = "91"  # specialist in de fys. geneesk.en reval.
    SPECIALIST_PNEUMOLOGIE = "92"  # geneesheer-specialist pneumologie
    SPECIALIST_RONTGENDIAGNOSE = "93"  # geneesheer-specialist röntgendiagnose
    SPECIALIST_RADIOTHERAPIE_ONCOLOGIE = "94"  # specialist in de radiotherapieoncologie
    SPECIALIST_REUMATOLOGIE = "95"  # geneesheer-specialist reumatologie
    SPECIALIST_STOMATOLOGIE = "96"  # geneesheer-specialist stomatologie
    SPECIALIST_UROLOGIE = "97"  # geneesheer-specialist urologie
    SPECIALIST_PATHOLOGISCHE_ANATOMIE = "98"  # specialist in de pathologische anatomie
    SPECIALIST_NUCLEAIRE_GENEESKUNDE = "99"  # specialist in de nucleaire geneeskunde
    # Specialized medical (100-145)
    SPECIALIST_ARBEIDSGENEESKUNDE = "100"  # geneesheer-specialist arbeidsgeneeskunde
    HOUDER_BBT_NUCL_VITRO = "101"  # houder BBT-nucl. in vitro geneesk.
    HOUDER_BBT_FUNCT_REVAL_GEHAND = "102"  # houder BBT-funct./prof. reval.gehand.
    BIJZ_BEROEPSTITEL_GERIATRIE = "103"  # bijz beroepstitel gen-spec geriatrie
    HOUDER_BBT_MOND_KAAK = "104"  # houder BBT-mond,kaak,aangezichtschir.
    HOUDER_BBT_INTENSIEVE_ZORGEN = "105"  # houder BBT-specialist intensieve zorgen
    HOUDER_BBT_URGENTIEGENEESK = "106"  # houder BBT-specialist urgentiegeneesk.
    HOUDER_BBT_PEDIATR_NEUROLOGI = "107"  # houder BBT-specialist pediatr. neurologi
    BIJZ_BEROEPSTITEL_NEFROLOGIE = "108"  # bijz beroepstitel gen-spec nefrologie
    HOUDER_BBT_ENDOCR_DIABETOLOGIE = "109"  # houder BBT-spec. endocr.-diabetologie
    BIJZ_BEROEPSTITEL_ONCOLOGIE = "110"  # bijz beroepstitel gen-spec oncologie
    HOUDER_BBT_MEDISCHE_ONCOLOGIE = "111"  # houder BBT -medische oncologie
    BIJZ_BEROEPSTITEL_NEONATOLOGIE = "112"  # bijz beroepstitel gen-spec neonatologie
    AGGREGAAT_MED_SOC_WETENSCH = "113"  # aggregaat med.-soc. wetensch./zh.beleid
    LICENTIAAT_MED_SOC_WETENSCH = "114"  # licentiaat med.-soc. Wetensch./zhbeleid
    LICENTIAAT_PEDAGOGIE = "115"  # licentiaat pedagogie
    LICENTIAAT_PSYCHOLOGIE = "116"  # licentiaat psychologie
    LICENTIAAT_SOCIOLOGIE = "117"  # licentiaat sociologie
    LICENTIAAT_ECONOMISCHE_WET = "118"  # licentiaat economische wetenschappen
    LICENTIAAT_ZIEKENHUISHYGIENE = "119"  # licentiaat ziekenhuishygiëne
    LICENTIAAT_KINESITHERAPIE = "120"  # licentiaat kinesitherapie
    APOTHEKER_BIOLOOG = "121"  # Apotheker-bioloog
    FYSICUS = "122"  # fysicus
    INTERCULTURELE_BEMIDDELING = "123"  # interculturele bemiddeling gezondh.zorg
    APOTHEKER = "132"  # Apotheker
    GEBREV_VERPLEEGK_GEEST_GEZONDH = "133"  # gebrev.verpleegk.Geest. Gezondheidszorg
    GEBREV_VERPLEEGK_GERIATRIE = "134"  # gebrev.verpleegk. in de geriatrie
    GEBREV_VERPLEEGK_INTENS_SPOED = "135"  # gebrev.verpleegk.intensieve zorg en spoe
    BIJZ_BEKW_GEBREV_ONCOLOGIE = "136"  # bijz.bekwam. Gebrev.verpleegk. oncologie
    BIJZ_BEKW_MED_BEELDVORMING_137 = "137"  # bijz.bekwam. in de medische beeldvormin
    BIJZ_BEKW_OPERATIEKAMER = "138"  # bijz.bekwam. in de operatiekamer
    BIJZ_BEKW_PALLIATIEVE_ZORG_139 = "139"  # bijz.bekwam. in de palliatieve zorg
    BIJZ_BEKW_ENDOSCOPIE = "140"  # bijz.bekwam. in de endoscopie
    BIJZ_BEKW_HEMODIALYSE = "141"  # bijz.bekwam. in de hemodialyse
    BIJZ_BEKW_RADIOTHERAPIE = "142"  # bijz.bekwam. in de radiotherapie
    BIJZ_BEKW_GEZONDHEIDSOPVOEDING_143 = "143"  # bijz.bekwam. gezondheidsopvoeding
    BIJZ_BEKW_ADJ_HOOFDVERPLEEGK = "144"  # bijz.bekwam. Adj.-hoofdverpleegk.
    BIJZ_BEKW_GEBREV_HOOFDVERPLEEGK = "145"  # bijz bekw van gebrev hoofdverpleegk
    # Bachelor degrees (500-534)
    NIET_GESPECIFIEERD_500 = "500"  # Niet gespecifieerd
    BACHELOR_BEDRIJFSVERPLEEGKUNDE = "501"  # Bachelor bedrijfsverpleegkunde
    BACHELOR_BIOMED_LABO_TECH = "502"  # Bachelor biomed.Labo.technologie
    BACHELOR_BIOMED_WETENSCH = "503"  # Bachelor biomedische wetenschappen
    BACHELOR_BIOWETENSCHAPPEN = "504"  # Bachelor biowetenschappen
    BACHELOR_ERGOTHERAPIE = "505"  # Bachelor ergotherapie
    BACHELOR_FARM_WETENSCH = "506"  # Bachelor farmaceutische wetenschappen
    BACHELOR_GEESTELIJKE_GEZONDH = "507"  # Bachelor geestelijke gezondheidszorg
    BACHELOR_GENEESKUNDE = "508"  # Bachelor geneeskunde
    BACHELOR_GERIATRISCHE_GEZONDH = "509"  # Bachelor geriatrische gezondheidszorg
    BACHELOR_INTENSIEVE_ZORGEN_SPOED = "510"  # Bachelor intensieve zorgen in de spoed
    BACHELOR_KINESITHERAPIE = "511"  # Bachelor kinesitherapie
    BACHELOR_LO_BEWEGINGSWETENSCH = "512"  # Bachelor LO/bewegingswetenschappen
    BACHELOR_LOGOPEDIE_AUDIOLOGIE = "513"  # Bachelor logopedie en de audiologie
    BACHELOR_LOGOPED_AUDIOLOG_WETENSCH = "514"  # Bachelor logoped. en audiolog. Wetensch
    BACHELOR_MED_BEELDVORMING = "515"  # Bachelor medische beeldvorming
    BACHELOR_ONCOLOGISCHE_ZORG = "517"  # Bachelor oncologische zorg
    BACHELOR_OPERATIEVERPLEEGKUNDE = "518"  # Bachelor operatieverpleegkunde
    BACHELOR_ORTHOPEDIE = "519"  # Bachelor orthopedie
    BACHELOR_OSTEOPATHIE = "520"  # Bachelor osteopathie
    BACHELOR_PALLIATIEVE_HULPVERLENING = "521"  # Bachelor palliatieve hulpverlening
    BACHELOR_PEDIATRISCHE_GEZONDH = "522"  # Bachelor pediatrische gezondheidszorg
    BACHELOR_PODOLOGIE = "523"  # Bachelor podologie
    BACHELOR_PSYCHOLOGIE = "524"  # Bachelor psychologie
    BACHELOR_RADIOL_MED_BEELDVORMING = "525"  # Bachelor radiol. en de med.beeldvorming
    BACHELOR_REVAL_WETENSCH_KINESITH = "526"  # Bachelor reval.wetensch./kinesitherapie
    BACHELOR_SOCIALE_GEZONDHEIDSZORG = "527"  # Bachelor sociale gezondheidszorg
    BACHELOR_TANDHEELKUNDE = "528"  # Bachelor tandheelkunde
    BACHELOR_THUISGEZONDHEIDSZORG = "529"  # Bachelor thuisgezondheidszorg
    BACHELOR_VERPLEEGKUNDE = "530"  # Bachelor verpleegkunde
    BACHELOR_VOEDINGS_DIEETKUNDE = "531"  # Bachelor voedings- en dieetkunde
    BACHELOR_VROEDKUNDE = "532"  # Bachelor vroedkunde
    BACHELOR_WONDZORG_WEEFSELHERSTEL = "533"  # Bachelor wondzorg en het weefselherstel
    BACHELOR_ZORGMANAGEMENT = "534"  # Bachelor in het zorgmanagement
    # Master degrees (600-655)
    NIET_GESPECIFIEERD_600 = "600"  # Niet gespecifieerd
    MASTER_CONTROLE_MALADIES = "601"  # Master en Contrôle des Maladies
    MASTER_ARBEIDSGENEESKUNDE = "602"  # Master arbeidsgeneeskunde
    MASTER_BIOMED_BEELDVORMING = "603"  # Master biomedische beeldvorming
    MASTER_ENDODONTOLOGIE = "604"  # Master endodontologie
    MASTER_FARM_ZORG = "605"  # Master farmaceutische zorg
    MASTER_GEHANDICAPTENZORG = "606"  # Master gehandicaptenzorg
    MASTER_GENEESKUNDE = "607"  # Master geneeskunde
    MASTER_GENEESMIDDELENONTWIKKELING = "608"  # Master geneesmiddelenontwikkeling
    MASTER_GESPEC_REVAL_KINESITH = "609"  # Master gespec.reval.wetensch./kinesith.
    MASTER_GEZONDH_VRLICHTING = "610"  # Master gezondh.vrlichting/bevord.
    MASTER_HUISARTSGENEESKUNDE = "611"  # Master huisartsgeneeskunde
    MASTER_INDUSTRIELE_FARMACIE = "612"  # Master industriële farmacie
    MASTER_JEUGDGEZONDHEIDSZORG = "613"  # Master jeugdgezondheidszorg
    MASTER_KINDERTANDHEELKUNDE = "614"  # Master kindertandheelkunde
    MASTER_KINESITHERAPIE = "615"  # Master kinesitherapie
    MASTER_KINESITH_BIJZ_GROEPEN = "616"  # Master kinesitherapie bij bijz groepen
    MASTER_KLINISCHE_BIOLOGIE = "617"  # Master klinische biologie
    MASTER_KLIN_BIO_APOTHEKER = "618"  # Master klinische biologie voor apotheke
    MASTER_LOGOP_AUDIOLOG_WETENSCH = "619"  # Master logop. en audiolog.Wetensch.
    MASTER_LYMFEDRAINAGE_VERLOSK_REVAL = "620"  # Master lymfedrainage/verlosk. revalidat
    MASTER_MANUELE_THERAPIE = "621"  # Master manuele therapie
    MASTER_MOLECULAIRE_LEVENSWETENSCH = "622"  # Master moleculaire levenswetenschappen
    MASTER_NEUROLOGISCHE_REVAL = "623"  # Master neurologische revalidatie
    MASTER_ORTHODONTIE = "624"  # Master orthodontie/Master of Orthodonti
    MASTER_PARODONTOLOGIE = "625"  # Master parodontologie
    MASTER_PSYCHOLOGIE = "626"  # Master psychologie
    MASTER_RESTAURATIEVE_TANDHEELK = "627"  # Master restauratieve tandheelkunde
    MASTER_REVALIDATIEWET_KINESITH = "628"  # Master revalidatiewet/kinesitherapie
    MASTER_SEKSUOLOGIE = "629"  # Master seksuologie
    MASTER_SPORTGENEESKUNDE = "630"  # Master sportgeneeskunde
    MASTER_SPORTKINESITHERAPIE = "631"  # Master sportkinesitherapie
    MASTER_TANDHEELKUNDE = "632"  # Master tandheelkunde
    MASTER_VERPLEEGKUNDE_VROEDKUNDE = "633"  # Master verpleegkunde en de vroedkunde
    MASTER_VERZEKER_GENEESK = "635"  # Master verzeker.geneesk. med. expertise
    MASTER_VOEDINGS_GEZONDHEIDSWET = "636"  # Master voedings- en gezondheidswetensch
    MASTER_ZIEKENHUISFARMACIE = "637"  # Master ziekenhuisfarmacie
    MASTER_ZIEKENHUISHYGIENE = "638"  # Master ziekenhuishygiëne
    MASTER_BEHEER_GEZONDHEIDSGEG = "640"  # Master in het beheer van gezondheidsgeg.
    MASTER_MAN_BELEID_GEZONDHEIDSZORG = "641"  # Master man. en beleidgezondheidszorg
    MASTER_MGT_ZORG_BELEID_GERONTOL = "642"  # Master in mgt, zorg en beleid gerontolog
    MASTER_SOCIAAL_WERK = "643"  # Master in het sociaal werk
    MASTER_PUBLIC_HEALTH = "644"  # Master Public Health
    MASTER_APPLIED_PHARM_SCIENCE = "645"  # Master of Applied Pharmaceutical Science
    MASTER_BIO_ETHICS = "646"  # Master of Bio-ethics
    MASTER_BIOMED_ENGINEERING = "647"  # Master of Biomedical Engineering
    MASTER_EXERCISE_SPORT_PSYCHOLOGY = "648"  # Master of Exercise and Sport Psychology
    MASTER_GERONTOLOGICAL_SCIENCES = "649"  # Master of Gerontological Sciences
    MASTER_MEDICAL_IMAGING = "650"  # Master of Medical Imaging
    MASTER_MOLECULAR_BIOTECHNOLOGY = "651"  # Master of Molecular Biotechnology
    MASTER_ORAL_HEALTH_RESEARCH = "652"  # Master of Oral Health Research
    MASTER_PAED_DENTISTRY = "653"  # Master Paed. Dentistry/Special DentalCar
    MASTER_PERIODONTOLOGY = "654"  # Master of Periodontology
    MASTER_RESTORATIVE_DENTISTRY = "655"  # Master of Restorative Dentistry
    # Postgraduate (701-831)
    NA_BIJSCHOL_CARDIOLOGISCHE_VERPL = "701"  # na- of bijscholing: cardiologische verpl
    NA_BIJSCHOL_CHRON_ZIEKE_KIND = "702"  # na- of bijscholing:chron. zieke kind
    NA_BIJSCHOL_HULPVERLENING_HERSEN = "703"  # na- of bijscholing: Hulpverlening hersen
    NA_BIJSCHOL_LOCOM_NEUROL_REV = "704"  # na- of bijscholing: locom. en neurol.rev
    NA_BIJSCHOL_MED_DRING_HULP = "705"  # na- of bijschol.: med. dring. hulp vr le
    NA_BIJSCHOL_NEONATOLOGIE = "706"  # na- of bijscholing: Neonatologie
    NA_BIJSCHOL_OPVOEDINGSONDERSTEUN = "707"  # na- of bijscholing: Opvoedingsondersteun
    NA_BIJSCHOL_PALLIATIEVE_ZORG = "708"  # na- of bijscholing: palliatieve zorg
    NA_BIJSCHOL_PIJNREFERENTIEVERPLE = "709"  # na- of bijscholing: Pijnreferentieverple
    NA_BIJSCHOL_RADIOPROTECTIE = "710"  # na- of bijscholing: radioprotectie
    NA_BIJSCHOL_RADIOTHERAPIE = "711"  # na- of bijscholing: radiotherapie
    NA_BIJSCHOL_REFER_VERPL_CONTI = "712"  # na- of bijscholing: refer.verpl.in)conti
    NA_BIJSCHOL_REFER_VERPLGK_DIABET = "713"  # na- of bijscholing: refer.verplgk.diabet
    NA_BIJSCHOL_REF_VERPL_DIABETES = "714"  # na- of bijscholing: Ref.verpl. diabetes
    NA_BIJSCHOL_REFER_VERPLGK_WONDZ = "715"  # na- of bijscholing: refer.verplgk.wondz.
    NIET_GESPECIFIEERD_716 = "716"  # Niet gespecifieerd
    NIET_GESPECIFIEERD_800 = "800"  # Niet gespecifieerd
    PG_BASISCURSUS_ONCOL_ZORG = "801"  # PG Basiscursus Oncologische Zorg
    PG_DESINFECTIE_STERILISATIE = "802"  # PG Desinfectie en sterilisatietechnieken
    PG_GEDRAGSPROBL_PERS_HANDICAP = "803"  # PG Gedragsprobl. personen handicap
    PG_INTENSIEVE_ZORG_SPOED = "804"  # PG Intensieve zorg en spoedgevallenzorg
    PG_PSYCHODIAGNOSTIEK = "805"  # PG Psychodiagnostiek
    PG_ZORGMANAGEMENT = "806"  # PG Zorgmanagement
    POSTGR_RADIOPROTECTIE = "807"  # postgr. in de radioprotectie
    POSTGR_PALLIATIEVE_ZORG = "808"  # postgr. palliatieve zorg
    POSTGR_RADIOTHERAPIE = "809"  # postgr. radiotherapie
    POSTGR_ANESTHESIOLOGIE_BASIS = "810"  # postgr.: anesthesiologie, basisbeginsele
    POSTGR_ANESTHESIOLOGIE_VERDER = "811"  # postgr.: anesthesiologie, verdergevorder
    POSTGR_AUTISME_SPECTRUM = "812"  # postgr.: autisme spectrum-stoornissen
    POSTGR_DIABETESEDUCATOR = "813"  # postgr.: diabeteseducator
    POSTGR_RADIO_ISOTOPEN = "814"  # postgr.: radio-isotopen vitro diagn. Tec
    POSTGR_GEDRAGSTHERAPIE = "815"  # postgr.: gedragstherapie
    POSTGR_LACTATIEKUNDE = "816"  # postgr.: lactatiekunde
    POSTGR_LYMFEDRAINAGE = "817"  # postgr.: lymfedrainage
    POSTGR_MEDECINE_TROPICALE_1 = "818"  # postgr.: Médecine Tropicale
    POSTGR_MEDECINE_TROPICALE_2 = "819"  # postgr.: Médecine Tropicale
    POSTGR_CONCEPTEN_LEER_ONTW = "820"  # postgr.:concepten leer- en ontw.problemen
    POSTGR_MUSCULOSKELET_KINESITH = "821"  # postgr.: musculoskeletale kinesitherapie
    POSTGR_NEUROL_TAAL_SPRAAKST = "822"  # postgr.: neurologische taal- en spraakst
    POSTGR_ONCOLOGISCHE_ZORG = "823"  # postgr.: oncologische zorg
    POSTGR_PELVISCHE_REVAL = "824"  # postgr.: pelvische revalidatie
    POSTGR_PSYCHOANALYTISCHE_PSYCHOTH = "825"  # postgr.: psychoanalytische psychotherapie
    POSTGR_REFERENTIEPERS_ETHIEK = "826"  # postgr.: Referentiepersoon ethiek
    POSTGR_SOCIALE_EMOTIONELE_ZORG = "827"  # postgr.: sociale en emotionele zorg
    POSTGR_TROPICAL_MEDICIN = "828"  # postgr.: Tropical Medicin
    POSTGR_TROPISCHE_GENEESKUNDE = "829"  # postgr.: Tropische Geneeskunde
    POSTGR_VERLOSKUNDIGE_REVAL = "830"  # postgr.: verloskundige revalidatie
    POSTGR_VERPLEEGK_ANDERE_CULTURE = "831"  # postgr.: verpleegkunde en andere culture

class HistoricContractTypeEnum(Enum):
    """Historisch contracttype sociaal balans enum"""
    EMPTY = ""  # Empty value
    ONBEPAALDE_TIJD = "0"  # Onbepaalde tijd
    BEPAALDE_TIJD = "1"  # Bepaalde tijd
    DUIDELIJK_OMSCHREVEN_WERK = "2"  # Duidelijk omschreven werk
    VERVANGINGSOVEREENKOMST = "3"  # Vervangingsovereenkomst

class ContractDurationUnitEnum(Enum):
    """Duur contract eenheid enum - Contract duration unit"""
    EMPTY = ""  # Empty value
    JAREN = "1"  # Jaren
    MAANDEN = "2"  # Maanden
    WEKEN = "3"  # Weken
    KALENDERDAGEN = "4"  # Kalenderdagen

class FiscalRegimeEnum(Enum):
    """Fiscaal regime enum"""
    EMPTY = ""  # Empty value
    BETAALT_BEDRIJFSVOORHEFFING = "1"  # Betaalt bedrijfsvoorheffing
    BETAALT_GEEN_BEDRIJFSVOORHEFFING = "2"  # Betaalt geen bedrijfsvoorheffing
    VOORHEFFING_NIET_VERBLIJFSHOUDERS = "3"  # Voorheffing niet-verblijfshouders
    FICTIEVE_BEDRIJFSVOORHEFFING = "6"  # Fictieve bedrijfsvoorheffing

class FiscalRegimeExemptionEnum(Enum):
    """Fiscaal regime vrijstelling enum"""
    EMPTY = ""  # Empty value
    VOORHEFFING_ZELFSTANDIGE = "1"  # Betaalt voorheffing als zelfstandige
    VOORHEFFING_BUITENLAND = "2"  # Betaalt voorheffing in het buitenland
    VOORHEFFING_FONDS_MINDERVALIDEN = "3"  # Voorheffing betaald door fonds voor mindervaliden
    WERKSTUDENT = "4"  # Werkstudent
    VRIJSTELLING_JONGE_WERKNEMERS = "5"  # Vrijstelling voorheffing jonge werknemers

class RIZIVPeriodicityEnum(Enum):
    """RIZIV periodiciteit enum"""
    EMPTY = ""  # Empty value
    MAANDELIJKS = "1"  # Maandelijks
    TWEEMAANDELIJKS = "2"  # Tweemaandelijks
    DRIEMAANDELIJKS = "3"  # Driemaandelijks
    OM_DE_VIER_MAAND = "4"  # Om de vier maand
    HALFJAARLIJKS = "6"  # Halfjaarlijks
    UNIEK_BEDRAG = "E"  # Uniek bedrag
    JAARLIJKS_BEDRAG = "J"  # Jaarlijks bedrag
    BEDRAG_KAPITAAL = "K"  # Bedrag in kapitaal

class RegularityCodeEnum(Enum):
    """Regelmaatcode enum - Work regularity code"""
    EMPTY = ""  # Empty value
    ONREGELMATIG_DEELTIJDS = "1"  # Onregelmatig deeltijds
    REGELMATIG_DEELTIJDS = "2"  # Regelmatig deeltijds
    ONREGELMATIG_VOLTIJDS = "3"  # Onregelmatig voltijds
    REGELMATIG_VOLTIJDS = "4"  # Regelmatig voltijds

class InvoluntaryPartTimeEnum(Enum):
    """Onvrijwillig deeltijds enum - Involuntary part-time"""
    EMPTY = ""  # Empty value
    DT_ZONDER_UITKERING = "1"  # Deeltijdse werkn. zonder uitkering inkomensgarantie
    DT_MET_UITKERING = "2"  # Deeltijdse werkn. met uitkering inkomensgarantie
    DT_MET_BEDRIJFSPLAN = "3"  # Deeltijdse werknemer met bedrijfsplan
    DT_MET_UITKERING_TIJDELIJK_VT = "4"  # DT-werkn. met uitkering inkomensgarantie (tijdelijk VT)
    GEEN_ONVRIJWILLIG_DT = "9"  # Geen onvrijwillig deeltijdsewerknemer

class WorkScheduleCodeEnum(Enum):
    """Code werkschema enum - Work schedule code"""
    EMPTY = ""  # Empty value
    VARIABEL_WERKSCHEMA = "VAR"  # Variabel werkschema
    VAST_WERKSCHEMA_1_WEEK = "VST"  # Vast werkschema van 1 week
    DEELTIJDS_WISSELEND = "WIS"  # Deeltijds werkschema voor vast mndloon met mnd zonder prest. of met sterk wisselende prest.
    VAST_WERKSCHEMA_MEERDERE_WEKEN = "WMW"  # Vast werkschema van meerdere weken

class CDocumentsEnum(Enum):
    """C-Documenten enum"""
    EMPTY = ""  # Empty value
    C131B = "1"  # C131B
    C78BIS = "2"  # C78Bis
    C78_4 = "3"  # C78.4
    C131B_EN_C78_4 = "4"  # C131B en C78.4
    C78_ACTIVA = "5"  # C78 Activa
    C131B_EN_C78_ACTIVA = "6"  # C131B en C78 Activa
    C78_ACTIVA_START = "7"  # C78 Activa start
    DOORSTROOMPROGRAMMA_ASR = "8"  # Doorstroomprogramma voor ASR WECH008
    C131B_EN_DOORSTROOM_ASR = "9"  # C131B en doorstroomprogramma ASR WECH008

class CAO42Enum(Enum):
    """CAO 42 enum"""
    EMPTY = ""  # Empty value
    CAO_42 = "1"  # CAO 42

class ShiftNightReductionEnum(Enum):
    """Ploeg/nachtvermindering enum"""
    EMPTY = ""  # Empty value
    WERKNEMER_PLOEG_NACHT = "1"  # Werknemer in ploeg- en/of nachtarbeid

class WorkTimeReorganizationEnum(Enum):
    """Reorganisatie arbeidstijd enum - Work time reorganization"""
    EMPTY = ""  # Empty value
    COLLECTIEVE_ARB_HERVERDELING = "1"  # Collectieve Arb.Herverdeling Met Loonverlies
    INVOERING_NWE_ARBEIDSSTELSELS = "2"  # Invoering Nwe Arbeidsstelsels (Cao 42 21/06/87)
    VOLLEDIGE_LOOPBAANONDERBREKING = "3"  # Volledige Loopbaanonderbreking
    GEDEELTELIJKE_LOOPBAANONDERBREKING = "4"  # Gedeeltelijke Loopbaanonderbreking
    AANGEPASTE_ARBEID_LOONVERLIES = "5"  # Aangepaste Arbeid Met Loonverlies
    HALFTIJDS_BRUGPENSIOEN = "6"  # Halftijds Brugpensioen
    VERMINDERING_PREST_OPENB_SECTOR = "7"  # Vermindering Prest. In Openb.Sector (Wet 10/04/95)
    OPLEIDINGSPROJECT_VERPLEEGK = "107"  # Opleidingsproject Verpleegkundige Soc.M.(Proj 600)
    # Public sector specific (500 series)
    AFW_DIENSTACTIVITEIT = "501"  # Afw Dienstactiviteit
    ONBEZOLD_AFW_GELIJKGEST_DIENSTACT = "502"  # Onbezold Afw Gelijkgest Met Dienstact
    ONBEZ_AFW_DIENSTACT_PENS = "503"  # Onbez Afw Gelijkgest Met Dienstact Voor Pens
    OUDERSCHAPSVERLOF = "504"  # Ouderschapsverlof
    ONBEZ_AFW_DIENSTACT_BEROEPSACT = "505"  # Onbez Afw Gelijkgest Met Dienstact Voor Beroepsact
    VERMIN_PREST_PERSOONLIJKE = "506"  # Vermin Prest Persoonlijke Redenen
    TERBESCH_WACHTWEDDE_BEHOUD = "507"  # Terbesch Stelling Wachtwedde En Behoud Recht Verh
    TERBESCH_WACHTWEDDE_VERLIES = "508"  # Terbesch Stelling Wachtwedde En Verlies Recht Verh
    TERBESCH_WACHTWEDDE_PENSIOEN = "509"  # Terbesch Stelling Wachtwedde Voor Pensioen
    ONBEZ_AFW_NON_ACTIV_ZONDER = "510"  # Onbez Afw. Non-Activ Of Terbesch Zonder Wachtwedde
    BEZOLD_AFW_NON_ACTIV = "511"  # Bezold Afw Non-Activ
    VERLOF_ZONDER_WEDDE_NON_ACTIV = "512"  # Verlof Zonder Wedde In Non-Activ
    AMBTSHALVE_VERLOF_ALG_BELANG = "513"  # Ambtshalve Verlof Opdracht Algemeen Belang
    TERBESCH_ONTSLAG_ZONDER_WACHTWEDDE = "531"  # Terbesch Stelling Onst Betr Zonder Wachtwedde
    TIJDEL_AMBTSONTH_LBO = "541"  # Tijdel Ambtsonth Lbo Of Loopbaanonderbr Verg Wg
    TIJDEL_AMBTSONTH_GEZONDHEID = "542"  # Tijdel Ambtsonth Owv Gezondheisredenen (Mil)
    TIJDEL_AMBTSONTH_DISCIPL = "543"  # Tijdel Ambtsonth Owv Discipl Maatr (Mil)
    VERLOF_LBO_PALLIATIEVE = "544"  # Verlof Of Lbo Palliatieve Zorgen,...Verg Wg
    AUTOMAT_INDISPONIBILITEIT = "545"  # Automat Indisponibiliteitsstelling (Mil)
    VRIJW_INDISPONIBILITEIT = "546"  # Vrijw Indisponibiliteitsstelling (Mil)

class ScheduleTypeEnum(Enum):
    """Type rooster enum - Schedule type"""
    EMPTY = ""  # Empty value
    UREN_PER_DAG_GELIJKE_WEKEN = "1"  # Uren per dag, gelijke weken
    UREN_PER_DAG_WISSELENDE_WEKEN = "2"  # Uren per dag, wisselende weken
    WERKTIJDEN_GELIJKE_WEKEN = "3"  # Werktijden, gelijke weken
    WERKTIJDEN_WISSELENDE_WEKEN = "4"  # Werktijden, wisselende weken
    UREN_PER_WEEK = "5"  # Uren per week
    FTE_PER_DAG_GELIJKE_WEKEN = "6"  # FTE per dag, gelijke weken

class HoursPromisePeriodEnum(Enum):
    """Urenbelofte enum - Hours promise period"""
    EMPTY = ""  # Empty value
    TWEE_WEKEN = "2"  # 2 weken
    VIER_WEKEN = "4"  # 4 weken
    HALFJAAR = "H"  # Halfjaar
    JAAR = "J"  # Jaar
    KWARTAAL = "K"  # Kwartaal
    MAAND = "M"  # Maand
    TWAALF_WEKEN = "T"  # 12 weken
    WEEK = "W"  # Week

class SalaryTypeEnum(Enum):
    """Soort salaris enum - Salary type"""
    EMPTY = ""  # Empty value
    UURLOON = "U"  # Uurloon
    VAST_SALARIS = "V"  # Vast salaris
    SCHAALSALARIS = "S"  # Schaalsalaris
    SCHAAL_UURLOON = "Su"  # Schaal uurloon

class SalaryScaleEnum(Enum):
    """Loonschaal enum - Salary scale (also used for function scale)"""
    EMPTY = ""  # Empty value
    SCHAAL_A = "A"  # Schaal A
    SCHAAL_B = "B"  # Schaal B
    SCHAAL_C = "C"  # Schaal C
    SCHAAL_D = "D"  # Schaal D
    SCHAAL_E = "E"  # Schaal E
    SCHAAL_F = "F"  # Schaal F
    SCHAAL_G = "G"  # Schaal G
    SCHAAL_H = "H"  # Schaal H
    SCHAAL_I = "I"  # Schaal I

class SalaryScaleTypeEnum(Enum):
    """Type loonschaal enum - Salary scale type"""
    EMPTY = ""  # Empty value
    SECTORALE_LOONSCHAAL = "1"  # Sectorale loonschaal
    EIGEN_LOONSCHAAL = "2"  # Eigen loonschaal

class PartenaReasonEnum(Enum):
    """Reden Partena enum"""
    EMPTY = ""  # Empty value
    ANDERE = "0"  # Andere
    INDEXERING = "1"  # Indexering
    VERHOGING = "2"  # Verhoging
    BAREMA_VERHOGING = "3"  # Barema verhoging
    CONVENTIONELE_VERHOGING = "4"  # Conventionele verhoging
    WIJZIGING_UURROOSTER = "5"  # Wijziging uurrooster
    VERANDERING_FUNCTIE = "6"  # Verandering van functie
    EINDE_PROEFPERIODE = "7"  # Einde proefperiode
    PROMOTIE = "8"  # Promotie
    VERANDERING_STATUUT = "9"  # Verandering van statuut
    VERANDERING_CONTRACT = "A"  # Verandering van contract

class StockOptionsCodeEnum(Enum):
    """Code % van opties enum - Stock options code"""
    EMPTY = ""  # Empty value
    PERCENTAGE = "1"  # Percentage
    NIHIL = "2"  # Nihil
    TERUGNAME = "3"  # Terugname

class RemunerationMethodEnum(Enum):
    """Bezoldigingswijze enum - Remuneration method"""
    EMPTY = ""  # Empty value
    STUK_TAAK_PRESTATIE = "1"  # Stuk- of taakloon, per prestatie betaald
    COMMISSIELOON = "2"  # Geheel of gedeeltelijk met commissieloon
    DIENSTENCHEQUES = "3"  # Tewerkgesteld via dienstencheques

class HealthcareSalaryIncreaseReasonEnum(Enum):
    """Reden loonsverhoging (zorg) enum - Healthcare salary increase reason"""
    EMPTY = ""  # Empty value
    ANCIENNITEITSVERHOGING = "01"  # Anciënniteitsverhoging
    LOONSVERHOGING = "02"  # Loonsverhoging
    INDEXERING = "03"  # Indexering
    INDEX_EN_ANCIENNITEIT = "04"  # Index en anciënniteitsverhoging

class ReplacementReasonEnum(Enum):
    """Reden vervanging enum - Replacement reason (shared for RRe1-5)"""
    EMPTY = ""  # Empty value
    ONGEVAL = "01"  # Ongeval (arbeidsongeval)
    ZIEKTE = "02"  # Ziekte (arbeidsongeval)
    BIJSTAND_ZWAAR_ZIEKE = "03"  # Bijstand zwaar zieke
    BORSTVOEDINGSVERLOF = "04"  # Borstvoedingsverlof
    BRUGPENSIOEN = "05"  # Brugpensioen
    EXTRA_LEGAAL_VERLOF = "06"  # Extra legaal verlof
    MOEDERSCHAPSRUST = "07"  # Moederschapsrust
    OUDERSCHAPSVERLOF = "08"  # Ouderschapsverlof
    PALLIATIEF_VERLOF = "09"  # Palliatief verlof
    PROFYLACTISCH_VERLOF = "10"  # Profylactisch verlof
    TIJDSKREDIET = "11"  # Tijdskrediet
    VERLOF_ZONDER_WEDDE = "12"  # Verlof zonder wedde
    SCHORSING_ONDERLING_AKKOORD = "13"  # Schorsing onderling akkoord
    PROJECT_600 = "14"  # Project 600
    PETER_METERSCHAP = "15"  # Peter/meterschap
    MENTOR = "16"  # Mentor
    ANDERE = "17"  # Andere
    EINDE_LOOPBAAN_MAATREGELEN = "18"  # Einde loopbaan maatregelen
    PROJECT_BIJKOMEND_VERLOF = "98"  # Project bijkomend verlof
    CAO45_PLUS = "99"  # CAO45+

class SocialMaribelTypeEnum(Enum):
    """Soc. Maribel type enum - Social Maribel type"""
    EMPTY = ""  # Empty value
    LOGISTIEK_ASSISTENT = "001"  # Logistiek assistent
    ANDER_PERSONEEL = "002"  # Ander personeel sociale maribel
    BIJKOMENDE_TEWERKSTL_2011 = "003"  # bijkomende tewerkstl soc.akk.ZH 2011
    FISCALE_MARIBEL = "F"  # Fiscale maribel

class BBTBBKEnum(Enum):
    """BBT/BBK enum - Special professional title/competence"""
    EMPTY = ""  # Empty value
    BIJZONDERE_BEROEPSTITEL = "1"  # Bijzondere beroepstitel
    BIJZONDERE_BEROEPSBEKWAAMHEID = "2"  # Bijzondere beroepsbekwaamheid
    ARTSEN = "J"  # Artsen

class Choice45YearEnum(Enum):
    """Keuze 45 jaar enum - Choice at 45 years"""
    EMPTY = ""  # Empty value
    GELD_45 = "45G"  # geld
    TIJD_45 = "45T"  # tijd
    NIET_TOEPASBAAR = "NT"  # niet toepasbaar

class Choice50YearEnum(Enum):
    """Keuze 50 jaar enum - Choice at 50 years"""
    EMPTY = ""  # Empty value
    GELD_45 = "45G"  # geld
    TIJD_45 = "45T"  # tijd
    GELD_50 = "50G"  # geld
    TIJD_50 = "50T"  # tijd
    TIJD_50_BONOBO = "50TOV"  # tijd (bonobo's)
    NIET_TOEPASBAAR = "NT"  # niet toepasbaar

class Choice52YearEnum(Enum):
    """Keuze 52 jaar enum - Choice at 52 years"""
    EMPTY = ""  # Empty value
    GELD_45 = "45G"  # geld
    TIJD_45 = "45T"  # tijd
    GELD_50 = "50G"  # geld
    TIJD_50 = "50T"  # tijd
    TIJD_50_BONOBO = "50TOV"  # tijd (bonobo's)
    TIJD_52_BONOBO = "52TOV"  # tijd (bonobo's)
    NIET_TOEPASBAAR = "NT"  # niet toepasbaar

class Choice55YearEnum(Enum):
    """Keuze 55 jaar enum - Choice at 55 years"""
    EMPTY = ""  # Empty value
    GELD_45 = "45G"  # geld
    TIJD_45 = "45T"  # tijd
    GELD_50 = "50G"  # geld
    TIJD_50 = "50T"  # tijd
    TIJD_50_BONOBO = "50TOV"  # tijd (bonobo's)
    TIJD_52_BONOBO = "52TOV"  # tijd (bonobo's)
    GELD_55 = "55G"  # geld
    TIJD_55 = "55T"  # tijd
    TIJD_55_BONOBO = "55TOV"  # tijd (bonobo's)
    NIET_TOEPASBAAR = "NT"  # niet toepasbaar

class LocationFunctionAllowanceEnum(Enum):
    """Standplaats functie enum - Location function allowance"""
    EMPTY = ""  # Empty value
    HAARDVERGOEDING_NIET_BAREMA = "1"  # haardvergoeding (niet uit barema)
    STANDPLAATSVERGOEDING_NIET_BAREMA = "2"  # standplaatsvergoeding (niet uit barema)
    FUNCTIETOESLAG_NIET_BAREMA = "3"  # functietoeslag (niet uit barema)
    FUNCTIECOMPLEMENT_NIET_BAREMA = "4"  # functiecomplement (niet uit barema)
    FUNCTIETOESLAG_COMPLEMENT_NIET_BAREMA = "5"  # functietoeslag en -complement (niet uit barema)
    FUNCTIECOMPLEMENT = "C"  # functiecomplement
    FUNCTIETOESLAG = "F"  # functietoeslag
    HAARDVERGOEDING = "H"  # haardvergoeding
    STANDPLAATSVERGOEDING = "S"  # standplaatsvergoeding
    FUNCTIETOESLAG_COMPLEMENT = "T"  # functietoeslag en -complement
    RH_FORFAITAIRE_CAT8 = "X"  # RH - forfaitaire vergoed cat.8 (uit barema)
    RH_FORFAITAIRE_CAT9 = "Y"  # RH - forfaitaire vergoed cat.9 (uit barema)

class ProrataTheoreticalHourlyWageEnum(Enum):
    """Prorata theor. uurloon enum - Prorata theoretical hourly wage"""
    EMPTY = ""  # Empty value
    VAST_GEMIDDELD_JAAR = "A"  # Vast gemiddeld jaaruurloon
    VAST_GEMIDDELD_MAAND = "B"  # Vast gemiddeld maanduurloon
    VARIABEL_EFFECTIEF_MAAND = "C"  # Variabel effectief maanduurloon

class ProrataLocationEnum(Enum):
    """Prorata standplaats enum - Prorata location"""
    EMPTY = ""  # Empty value
    Z1_Z2_Z3 = "01"  # Z1/Z2*Z3
    KINDERDAGVERBLIJVEN = "02"  # Kinderdagverblijven
    BASIS_TE_WERKEN_UREN = "03"  # Op basis van te werken uren
    KDV_WERKREGIME_40 = "04"  # KDV werkregime 40 uren
    GEWERKTE_GELIJKGESTELDE = "05"  # Gewerkte + gelijkgestelde/te werken uren

class ProrataAllowancesEnum(Enum):
    """Prorata-toeslagen enum - Prorata allowances"""
    EMPTY = ""  # Empty value
    GEWERKTE_TE_WERKEN_DAGEN = "01"  # Gewerkte dagen / te werken dagen
    GEWERKTE_TE_WERKEN_UREN = "02"  # Gewerkte uren / te werken uren
    GEWERKTE_GELIJKGEST_UREN = "03"  # Gewerkte+gelijkgest.uren/te werken uren
    VERREKENING_25_DAGEN = "04"  # Verrekening in functie van 25 dagen
    VAST_BEDRAG_OF_0 = "05"  # Vast bedrag of 0
    Z2_Z3_Z4 = "06"  # Z2/Z3 * Z4

class EmploymentRelationTypeEnum(Enum):
    """Aard arbeidsverhouding enum - Employment relation type (Dutch tax)"""
    EMPTY = ""  # Empty value
    ARBEIDSOVEREENKOMST = "1"  # Arbeidsovereenkomst (exclusief BBL)
    WSW = "10"  # Wet sociale werkvoorziening (WSW) (geldig t/m 2021)
    UITZENDKRACHT = "11"  # Uitzendkracht
    PERSOONLIJKE_ARBEID = "12"  # Persoonlijke arbeid

class TableColorEnum(Enum):
    """Tabelkleur enum - Tax table color (Dutch)"""
    EMPTY = ""  # Empty value
    WIT = "W"  # Wit
    GROEN = "G"  # Groen

class TableCodeEnum(Enum):
    """Tabelcode enum - Tax table code (Dutch)"""
    EMPTY = ""  # Empty value
    ZONDER_HERLEIDINGSREGEL = "0"  # Tabel toegepast zonder herleidingsregel
    ALLEEN_PREMIEPLICHTIG = "3"  # Alleen premieplichtig (A, G)
    BUITEN_ARTIEST_SPORT_VERLAAGD = "221"  # Buitenlandse artiesten of beroepssporters (verlaagd tarief)
    ANONIEME_MEDEWERKERS_52 = "940"  # 52%-tarief in verband met anonieme medewerkers
    OVERIGE_GEEN_TABEL = "999"  # Overige gevallen waarin geen tabel is toegepast
    BUITEN_ARTIEST_GEZELSCHAP = "224"  # Buitenlandse artiestengezelschappen en sportploegen
    BUITEN_SPORT_VERLAAGD_MIN = "225"  # Buitenlandse beroepssporters (verlaagd tarief o.g.v. ministerieel besluit)
    PERCENTAGE_BIJSTAND = "250"  # Percentagetarief bijstand
    NEGATIEVE_UITGAVEN_52 = "950"  # 52%-tarief in verband met negatieve uitgaven bij afkoop van inkomensvoorzieningen
    ALLEEN_BELASTINGPLICHTIG = "5"  # Alleen belastingplichtig (B, H)
    BRONHEFFING_CURACAO = "252"  # Bronheffing pensioenen Curaçao (geldig t/m 2016)
    BELASTING_PREMIE_AOW_ANW = "6"  # Belasting- en Premieplichtig AOW en ANW (C, I)
    BELASTING_PREMIE_WLZ = "7"  # Belasting- en Premieplichtig Wlz (D, J)
    ALLEEN_AOW_ANW = "228"  # Werknemer niet belastingplichtig en alleen premieplichtig voor de AOW/ANW (E)
    ALLEEN_WLZ = "226"  # Werknemer niet belastingplichtig en alleen premieplichtig voor de Wlz (F, L)
    ALLEEN_ANW = "227"  # Werknemer niet belastingplichtig en alleen premieplichtig voor de ANW (K)
    AANNEMERS_WERK = "210"  # Aannemers van werk, thuiswerkers, sekswerkers en andere gelijkgestelden
    BINNENLAND_ARTIESTEN = "220"  # Binnenlandse artiesten

class WageTaxCreditEnum(Enum):
    """Loonheffingskorting enum - Wage tax credit (Dutch)"""
    EMPTY = ""  # Empty value
    NIET_TOEPASSEN = "0"  # Niet toepassen
    TOEPASSEN = "1"  # Toepassen

class HealthInsuranceEnum(Enum):
    """Zvw enum - Health insurance (Dutch)"""
    EMPTY = ""  # Empty value
    NIET_VERZEKERD_GEEN_WLZ = "A"  # Niet verzekeringsplichtig omdat persoon ook niet verzekerd is voor Wlz
    WEL_VERZEKERD_NORMAAL = "K"  # Wel verzekeringsplichtig, normaal tarief werkgeversheffing
    WEL_VERZEKERD_NUL_ZEELIEDEN = "L"  # Wel verzekeringsplichtig, 0%-tarief werkgeversheffing (zeelieden)
    WEL_VERZEKERD_INGEHOUDEN = "M"  # Wel verzekeringsplichtig, ingehouden bijdrage
    NIET_VERZEKERD_MILITAIR = "B"  # Niet verzekeringsplichtig, persoon militair ambt. in werkelijke dienst of met buitengewoon verlof
    WEL_VERZEKERD_NORMAAL_OUDE = "C"  # Wel verzekeringsplichtig, normaal tarief (geldig t/m 2006)
    WEL_VERZEKERD_AFWIJKEND_OUDE = "D"  # Wel verzekeringsplichtig, afwijkend tarief zeelieden (geldig t/m 2012)
    WEL_VERZEKERD_VERLAAGD_OUDE = "E"  # Wel verzekeringsplichtig, verlaagd tarief (geldig t/m 2012)
    WEL_VERZEKERD_MEER_OUDE = "F"  # Wel verzekeringsplichtig, meer tarieven toegepast (geldig t/m 2006)
    NIET_VERZEKERD_ARTIEST = "G"  # Niet verzekeringsplichtig, buitenlandse artiest/beroepssporter met code LB 221, 224, 225
    WEL_VERZEKERD_GEEN_TARIEF = "H"  # Wel verzekeringsplichtig, geen tarief toegepast, binnenlands artiest met code LB 220
    NIET_VERZEKERD_PSEUDOBIJDRAGE = "I"  # Niet verzekeringsplichtig omdat persoon ook niet verzekerd is voor Wlz, pseudobijdrage verschuldigd
    WEL_VERZEKERD_BEPAALD_OUDE = "CEF"  # Wel verzekeringsplichtig (tarief bepaald in berekening) (geldig t/m 2012)

class SeniorDiscountEnum(Enum):
    """Alleenstaande ouderenkorting enum - Senior discount (Dutch)"""
    EMPTY = ""  # Empty value
    NIET_TOEPASSEN = "0"  # Alleenstaande ouderenkorting niet toepassen
    TOEPASSEN = "1"  # Alleenstaande ouderenkorting toepassen

class PremiumDiscountEnum(Enum):
    """Premiekorting enum - Premium discount (Dutch)"""
    EMPTY = ""  # Empty value
    GEEN = "0"  # Geen premiekorting
    ARB_GEH_JONG_INDIENSTNAME = "1"  # Arb.geh.korting in dienst genomen jonggeh. of pers. met REA-voorziening (geldig t/m 2007)
    JONGERE_WERKNEMER = "10"  # Jongere werknemer
    ARB_GEH_JONG_HERPLAATSING = "2"  # Arb.geh.korting voor herplaatste jonggeh. of pers. met REA-voorziening (geldig t/m 2007)
    ARB_GEH_INDIENSTNAME = "3"  # Arb.geh.korting voor in dienst genomen arbeidsgehandicapte (geldig t/m 2007)
    ARB_GEH_HERPLAATSING = "4"  # Arb.geh.korting voor herplaatste arbeidsgehandicapte (geldig t/m 2007)
    ARBEIDSHANDICAP = "5"  # Werknemer met een arbeidshandicap (geldig t/m 2016)
    NIEUWE_OUDERE = "6"  # Nieuwe arbeidsverhouding oudere werknemers
    WERKNEMER_62_64 = "7"  # Werknemer van 62, 63 of 64 jaar op wie code 6 niet van toepassing is (geldig t/m 2012)
    BEIDE_5_6 = "8"  # Werknemer op wie code 5 en 6 beide van toepassing zijn (geldig t/m 2012)
    BEIDE_5_7 = "9"  # Werknemer op wie code 5 en 7 beide van toepassing zijn (geldig t/m 2012)

class VacationVouchersEnum(Enum):
    """Vakantiebonnen enum - Vacation vouchers (Dutch)"""
    EMPTY = ""  # Empty value
    GEEN = "0"  # Geen vakantiebonnen
    MINDER_19_DAGEN = "1"  # 19 dagen of minder (t/m 2019)
    MEER_20_DAGEN = "2"  # 20 Dagen of meer (t/m 2019)
    GEEN_WEL_TIJDSPAREN = "9"  # Geen vakantiebonnen, wel tijdsparen

class NoCarAdditionReasonEnum(Enum):
    """Reden geen bijtelling auto enum - Reason no car addition (Dutch)"""
    EMPTY = ""  # Empty value
    NIET_VAN_TOEPASSING = "0"  # Niet van toepassing
    AFSPRAAK_BELASTINGDIENST = "1"  # Afspraak via werkgever met Belastingdienst
    VERKLARING_GEEN_PRIVE = "2"  # Werknemer heeft verklaring geen privégebruik auto Belastingdienst
    ANDER_BEWIJS = "3"  # Ander bewijs personen- en bestelauto
    BESTELAUTO_GEEN_PRIVE_OUD = "4"  # Bestelauto zonder privé-gebruik (geldig t/m 2006)
    DOORLOPEND_AFWISSELEND = "5"  # Doorlopend afwisselend gebruik bestelauto
    NUL_PROCENT_OUD = "6"  # 0% bijtelling (geldig t/m 2018)
    VERKLARING_ZAKELIJK = "7"  # Werknemer heeft verklaring uitsluitend zakelijk gebruik bestelauto Belastingdienst

class DayTableApplicationEnum(Enum):
    """Toepassing dagtabel enum - Day table application"""
    EMPTY = ""  # Empty value
    STANDAARD = "1"  # Standaard regelgeving
    GEFORCEERD_DAG = "2"  # Geforceerd dagtabel toepassen
    GEFORCEERD_PERIODE = "3"  # Geforceerd periodetabel toepassen

class IncomeRelationTypeEnum(Enum):
    """Soort inkomstenverhouding enum - Income relation type (Dutch tax)"""
    EMPTY = ""  # Empty value
    # Salary and wage income (11-18)
    AMBTENAREN = "11"  # Loon of salaris ambtenaren in de zin van de Ambtenarenwet
    GEPREMIEERD_GESUBSIDIEERD = "12"  # Loon werknemers van gepremieerde, gesubsidieerde of gebudgetteerde instellingen (geldig t/m 2015)
    DIRECTEUR_NV_VERZEKERD = "13"  # Loon of salaris directeuren van een nv/bv, wel verzekerd voor de werknemersverzekeringen
    OVERIGE_NIET_WIA_WAO = "14"  # Loon of salaris overige werknemers niet verzekerd voor de WIA of WAO (geldig t/m 2015)
    OVERIG_LOON = "15"  # Loon of salaris niet onder te brengen onder 11 tot en met 14 of 17
    DGA_NIET_VERZEKERD = "17"  # Loon of salaris DGA's van een nv/bv, niet verzekerd voor de werknemersverzekeringen
    WACHTGELD_OVERHEID = "18"  # Wachtgeld van een overheidsinstelling
    # Pensions and annuities (21-24)
    OVERIGE_PENSIOENEN = "21"  # Overige pensioenen, lijfrenten, enz. (niet 23) (geldig t/m 2016)
    AOW = "22"  # Uitkering in het kader van de Algemene Ouderdomswet (AOW)
    OORLOG_VERZET = "23"  # Oorlogs- en verzetspensioenen
    ANW = "24"  # Uitkering in het kader van de Algemene nabestaandenwet (ANW)
    # Social security benefits (31-46, 50-55)
    ZW_WAZO = "31"  # Uitkering in het kader van de Ziektewet (ZW), verzekering Ziektewet en de Wet arbeid en zorg (WAZO)
    WAO_PARTICULIER = "32"  # Uitkering in het kader van de WAO en particuliere verzekering ziekte, invaliditeit en ongeval
    NWW = "33"  # Uitkering in het kader van de Nieuwe Werkloosheidswet (nWW)
    IOAW = "34"  # Uitkering in het kader van de Wet inkomensvoorz. oud. en ged. arbeidsong. werkloze werknemers (IOAW)
    VERVOLGUITKERING_NWW = "35"  # Vervolguitkering in het kader van de Nieuwe Werkloosheidswet (nWW) (geldig t/m 2021)
    WAZ = "36"  # Uitkering in het kader van de Wet arbeidsongeschiktheidsverzekering zelfstandigen (WAZ)
    WAJONG = "37"  # Wet arbeidsongeschiktheidsvoorziening jonggehandicapten (Wajong)
    SAMENLOOP_WAJONG = "38"  # Samenloop (gelijktijdig of volgtijdelijk) van uitkeringen van WAJONG met WAZ WAO/IVA of WGA
    IVA = "39"  # Uitkering in het kader van de Regeling inkomensvoorziening volledig arbeidsongeschikten (IVA)
    WGA = "40"  # Uitkering in het kader van de Regeling werkhervatting gedeeltelijk arbeidsgeschikten (WGA)
    BIJSTANDSBESLUIT_ZELFSTANDIGEN = "42"  # Uitkering in het kader van bijstandsbesluit Zelfstandigen
    PARTICIPATIEWET = "43"  # Uitkering in het kader van de Participatiewet (voorheen WWB)
    WWIK = "44"  # Uitkering in het kader van de Wet Werk en Inkomen Kunstenaars (WWIK) (geldig t/m 2013)
    IOAZ = "45"  # Uitkering in het kader van de Wet inkomensvoorz. oud. en ged. arbeidsong. gew. zelfstandigen (IOAZ)
    TOESLAGENWET = "46"  # Uitkering uit hoofde van de Toeslagenwet.
    OVERIGE_SOC_VERZEKERINGEN = "50"  # Uitkeringen in het kader van overige soc. verzekeringswetten (niet 22, 24, 31 t/m 45 of 52)
    WIJ = "51"  # Uitkering in het kader van de Wet investeren in jongeren (WIJ) (geldig t/m 2013)
    IOW = "52"  # Uitkering in het kader van de Wet inkomensvoorziening oudere werklozen (IOW)
    VERVROEGDE_UITTREDING = "53"  # Uitkering in het kader van vervroegde uittreding
    LEVENSLOOP_61_PLUS = "54"  # Opname levenslooptegoed door een werknemer die op 1 januari 61 jaar of ouder is (t/m 2021)
    APPA = "55"  # Uitkering in het kader van de Algemene Pensioenwet Politieke Ambtsdragers (APPA)
    # Employer pensions (56-63)
    OUDERDOM_WERKGEVER = "56"  # Ouderdomspensioen dat via de werkgever is opgebouwd
    NABESTAANDEN_WERKGEVER = "57"  # Nabestaandenpensioen dat via de werkgever is opgebouwd
    ARBEIDSONGESCH_WERKGEVER = "58"  # Arbeidsongeschiktheidspensioen dat via de werkgever is opgebouwd
    LIJFRENTE_ARBEIDSOVEREENKOMST = "59"  # Lijfrenten die zijn afgesloten ihkv een individuele of collectieve arbeidsovereenkomst
    LIJFRENTE_NIET_ARBEIDSOVEREENKOMST = "60"  # Lijfrenten die niet zijn afgesloten ihkv een individuele of collectieve arbeidsovereenkomst
    AANVULLING_UITKERING = "61"  # Aanvulling van de werkgever op een uitkering werknemersverzekeringen; dienstbetrekking is beëindigd
    ONTSLAGVERGOEDING = "62"  # Ontslagvergoeding / transitievergoeding
    OVERIGE_PENSIOENEN_SAMENLOOP = "63"  # Overige pensioenen of samenloop van pensioenen/lijfrenten of betaling na einde dienstbetrekking

class HistoricSalaryScaleEnum(Enum):
    """Hist. barema-aanduiding enum - Historic salary scale indication (Belgian healthcare)"""
    EMPTY = ""  # Empty value
    BUITEN_BAREMA = "000000"  # Buiten barema
    ARTSEN_OPLEIDING = "ASO"  # Artsen in opleiding
    # Disabled care facilities (G series)
    G_A1 = "G A1"  # GEHAND.- ADMIN.+ LOGIS. PERS. KLASSE 1
    G_A2 = "G A2"  # GEHAND.- ADMIN.+ LOGIS. PERS. KLASSE 2
    G_A2_2 = "G A2.2"  # GEHAND.- ADMIN. PERS. BOEKH. KLASSE II
    G_A3 = "G A3"  # GEHAND.- ADMIN. PERSONEEL KLASSE 3
    G_B1A = "G B1A"  # GEHAND.- OPVOERDER-GROEPCHEF
    G_B1B = "G B1B"  # GEHAND.- HOOFDOPVOEDER
    G_B1C = "G B1C"  # GEHAND.- OPVOEDEND PERSONEEL KLASSE 1
    G_B2A = "G B2A"  # GEHAND.- BEGELEID.EN VERZ PERS KLASSE 2A
    G_B2B = "G B2B"  # GEHAND.- BEGELEID.EN VERZ PERS KLASSE 2B
    G_B3 = "G B3"  # GEHAND.- BEGELEID. EN VERZ PERS KLASSE 3
    G_G1 = "G G1"  # GEHAND.- GENEESHEER OMNIPRACTICUS
    G_GS = "G GS"  # GEHAND.- GENEESHEER SPECIALIST
    G_HM = "G HM"  # GEHAND.-HOOFDMAATSCHAPPELIJK ASSISTENT
    G_K1 = "G K1"  # GEHAND.- DIRECTEUR +90 BEDDEN
    G_K2 = "G K2"  # GEHAND.- DIRECTEUR 60-89 BEDDEN
    G_K3 = "G K3"  # GEHAND.- DIRECTEUR 30-59 BEDDEN
    G_K5 = "G K5"  # GEHAND.- ONDERDIRECTEUR
    G_L1 = "G L1"  # GEHAND.- LICENTIATEN EN TANDARTS
    G_L2 = "G L2"  # GEHAND.- LOGISTIEK PERSONEEL KLASSE 2
    G_L2_5 = "G L2.5"  # GEHAND.- LOGIS. PERSONEEL ONDERH. CAT V
    G_L3 = "G L3"  # GEHAND.- LOGIS. PERS. KLASSE 3 (NA 11/93
    G_L3_4 = "G L3.4"  # GEHAND.- LOGIS. PERSONEEL ONDERH. CAT IV
    G_L3A = "G L3A"  # GEHAND.-LOGIS.PERS.KLASSE 3 (VOOR 11/93)
    G_L4 = "G L4"  # GEHAND.- LOGISTIEK PERSONEEL KLASSE 4
    G_L4_2 = "G L4.2"  # GEHAND.- LOGIST.PERSONEEL ONDERH. CAT II
    G_L4_3 = "G L4.3"  # GEHAND.- LOGIS.PERSONEEL ONDERH. CAT III
    G_MV1 = "G MV1"  # GEHAND.- SOC. PARAM. EN THERAP. PERSON.
    G_MV1B = "G MV1B"  # GEHAND.-DIENSTVERANTW.OPVANGGEZINNEN
    G_MV2 = "G MV2"  # GEHAND.- VERZORGEND PERSONEEL
    # Public sector (I series)
    I_NA = "I NA"  # FCUD-NIVEAU A-ATTACHE
    I_NB = "I NB"  # FCUD-NIVEAU B-TECHNISCH DESKUNDIGE
    I_NC = "I NC"  # FCUD-NIVEAU C-ADMINISTRATIEF ASSISTENT
    I_ND = "I ND"  # FCUD-NIVEAU D-ADMINISTRATIEF MEDEWERKER
    # Daycare (K series)
    K_A1 = "K A1"  # KRIBBE-ADMIN.+ LOGISTIEK PERS. KLASSE 1
    K_A2 = "K A2"  # KRIBBE-ADMIN. + LOGISTIEK PERS. KLASSE 2
    K_A2_2 = "K A2.2"  # KRIBBE-ADMIN. PERS. BOEKH. KLASSE II
    K_A3 = "K A3"  # KRIBBE-ADMINISTRATIEF PERSONEEL KLASSE 3
    K_B1A = "K B1A"  # KRIBBE-OPVOERDER-GROEPCHEF
    K_B1B = "K B1B"  # KRIBBE-DIENSTHOOFD
    K_B1C = "K B1C"  # KRIBBE-BEGELEIDEND PERSONEEL KLASSE 1
    K_B2A = "K B2A"  # KRIBBE-BEGELEIDEND PERSONEEL KLASSE 2A
    K_B2B = "K B2B"  # KRIBBE-BEGELEIDEND PERSONEEL KLASSE 2B
    K_B3 = "K B3"  # KRIBBE-BEGELEIDEND PERSONEEL KLASSE 3
    K_G1 = "K G1"  # KRIBBE-GENEESHEER OMNIPRACTICUS
    K_GS = "K GS"  # KRIBBE-GENEESHEER SPECIALIST
    K_HM = "K HM"  # KRIBBE-HOOFDMAATSCHAPPELIJK ASSISTENT
    K_K1 = "K K1"  # KRIBBE- DIRECTEUR +90 BEDDEN
    K_K2 = "K K2"  # KRIBBE- DIRECTEUR 60-89 BEDDEN
    K_K3 = "K K3"  # KRIBBE-DIRECTIE
    K_K5 = "K K5"  # KRIBBE- ONDERDIRECTEUR
    K_L1 = "K L1"  # KRIBBE-LICENTIATEN
    K_L2 = "K L2"  # KRIBBE-LOGISTIEK PERSONEEL KLASSE 2
    K_L2_5 = "K L2.5"  # KRIBBE- LOGIS. PERSONEEL ONDERH. CAT V
    K_L3 = "K L3"  # KRIBBE-LOGISTIEK PERSONEEL KLASSE 3
    K_L3_4 = "K L3.4"  # KRIBBE- LOGIS. PERSONEEL ONDERH. CAT IV
    K_L3A = "K L3A"  # KRIBBE-LOGIS.PERS.KLASSE 3 (VOOR 11/93)
    K_L4 = "K L4"  # KRIBBE-LOGISTIEK PERSONEEL KLASSE 4
    K_L4_2 = "K L4.2"  # KRIBBE- LOGIST.PERSONEEL ONDERH. CAT II
    K_L4_3 = "K L4.3"  # KRIBBE- LOGIS.PERSONEEL ONDERH. CAT III
    K_MV1 = "K MV1"  # KRIBBE-SOC.VERPL. PARAM. EN THERAP. PERS
    K_MV1B = "K MV1B"  # KRIBBE- DIENSTVERANTW.OPVANGGEZINNEN
    K_MV2 = "K MV2"  # KRIBBE-GEBREVETEERD VERPLEEGKUNDIGE
    # Care homes blue scales (RB series)
    RB01 = "RB01"  # RH/RVT BLAUW SCHAAL 01: 1.12
    RB04 = "RB04"  # RH EN RVT BLAUW : SCHAAL 04: 1.26
    RB05 = "RB05"  # RH/RVT BLAUW : SCHAAL 5 : 1.50
    RB06 = "RB06"  # RH/RVT BLAUW : SCHAAL : 1.35
    RB09 = "RB09"  # RH/RVT BLAUW : SCHAAL 09 : 1.40/1.57
    RB10 = "RB10"  # RH/RVT BLAUW : SCHAAL 10 : 1.40
    RB12 = "RB12"  # RH/RVT BLAUW : SCHAAL 12 : 1.43-1.55
    RB13 = "RB13"  # RH/RVT BLAUW : SCHAAL 13 : 1.59
    RB15 = "RB15"  # RH/RVT BLAUW : SCHL15 : 1.55-1.61-1.77
    RB16 = "RB16"  # RH/RVT BLAUW : SCHL16:1.55/1.61/1.77(+2J
    RB17 = "RB17"  # RH/RVT BLAUW : SCHAAL 17 : 1.80
    RB18 = "RB18"  # RH/RVT-BLAUW : SCHAAL 18: 1.22
    RB28 = "RB28"  # Zh-blauw: schaal 28: 1.78SP
    RB29 = "RB29"  # RH/RVT Blauw : Schaal 1.78
    # Care homes management scales (RD series)
    RD01 = "RD01"  # RH/RVT-directie: schaal 01:schaal 3.40.A
    RD02 = "RD02"  # RH/RVT-directie: schaal 02:schaal 3.40.B
    RD03 = "RD03"  # RH/RVT-directie: schaal 03:schaal 3.43.A
    RD04 = "RD04"  # RH/RVT-directie: schaal 04:schaal 3.43.B
    RD05 = "RD05"  # RH/RVT-directie: schaal 05:schaal 3.55.A
    RD06 = "RD06"  # RH/RVT-directie: schaal 06:schaal 3.55.B
    RD07 = "RD07"  # RH/RVT-directie: schaal 07:schaal 3.78.A
    RD08 = "RD08"  # RH/RVT-directie: schaal 08:schaal 3.78.B
    RD09 = "RD09"  # RH/RVT-directie: schaal 09:schaal 3.78.C
    RD10 = "RD10"  # RH/RVT-directie: schaal 10:schaal 3.79.A
    RD11 = "RD11"  # RH/RVT-directie: schaal 11:schaal 3.79.B
    RD12 = "RD12"  # RH/RVT-directie: schaal 12:schaal 3.80.A
    RD13 = "RD13"  # RH/RVT-directie: schaal 13:schaal 3.80.B
    RD14 = "RD14"  # RH/RVT-directie: schaal 14:schaal 3.80.C
    RD15 = "RD15"  # RH/RVT-directie: schaal 15:schaal 3.81.A
    RD16 = "RD16"  # RH/RVT-directie: schaal 16:schaal 3.81.B
    RD17 = "RD17"  # RH/RVT-directie: schaal 17:schaal 3.81.C
    RD18 = "RD18"  # RH/RVT-directie: schaal 18:schaal 3.87.A
    RD19 = "RD19"  # RH/RVT-directie: schaal 19:schaal 3.87.B
    RD20 = "RD20"  # RH/RVT-directie: SCHL27: 3.78.ABIS
    RD21 = "RD21"  # RH/RVT-directie: schaal 3.40.ABIS
    RD22 = "RD22"  # RH/RVT-directie: schaal 3.40.BBIS
    RD23 = "RD23"  # RH/RVT-directie: schaal 3.43.ABIS
    RD24 = "RD24"  # RH/RVT-directie: schaal 3.43.BBIS
    RD25 = "RD25"  # RH/RVT-directie: schaal 3.55.ABIS
    RD26 = "RD26"  # RH/RVT-directie :schaal 3.55.BBIS
    RD27 = "RD27"  # RH/RVT-directie: schaal 3.78.BBIS
    RD28 = "RD28"  # RH/RVT-directie: :schaal 3.78.CBIS
    RD29 = "RD29"  # RH/RVT-directie: :schaal 3.78.CBIS+5
    RD30 = "RD30"  # RH/RVT-directie: :schaal 3.78.CBIS+8
    RD31 = "RD31"  # RH/RVT-directie: :schaal 3.78.CBIS+10
    RD32 = "RD32"  # RH/RVT-directie: schaal 3.79.ABIS
    RD33 = "RD33"  # RH/RVT-directie: schaal 3.79.ABIS+5
    RD34 = "RD34"  # RH/RVT-directie: schaal 3.79.ABIS+8
    RD35 = "RD35"  # RH/RVT-directie: schaal 3.79.BBIS
    RD36 = "RD36"  # RH/RVT-directie: schaal 3.79.BBIS+5
    RD37 = "RD37"  # RH/RVT-directie: schaal 3.79.BBIS+8
    RD38 = "RD38"  # RH/RVT-directie: schaal 3.79.ABIS+10
    RD39 = "RD39"  # RH/RVT-directie: schaal 3.79.BBIS+10
    RD40 = "RD40"  # RH/RVT-directie: schaal 3.80.ABIS
    RD41 = "RD41"  # RH/RVT-directie: schaal 3.80.ABIS+5
    RD42 = "RD42"  # RH/RVT-directie: schaal 3.80.ABIS+8
    RD43 = "RD43"  # RH/RVT-directie: schaal 3.80.BBIS
    RD44 = "RD44"  # RH/RVT-directie: schaal 3.80.BBIS+5
    RD45 = "RD45"  # RH/RVT-directie: schaal 3.80.BBIS+8
    RD46 = "RD46"  # RH/RVT-directie: schaal 3.80.CBIS
    RD47 = "RD47"  # RH/RVT-directie: schaal 3.80.CBIS+5
    RD48 = "RD48"  # RH/RVT-directie: schaal 3.80.CBIS+8
    RD49 = "RD49"  # RH/RVT-directie: schaal 3.80.ABIS+10
    RD50 = "RD50"  # RH/RVT-directie: schaal 3.80.BBIS+10
    RD51 = "RD51"  # RH/RVT-directie: schaal 3.80.CBIS+10
    RD52 = "RD52"  # RH/RVT-directie: schaal 3.81.ABIS
    RD53 = "RD53"  # RH/RVT-directie: schaal 3.81.ABIS+5
    RD54 = "RD54"  # RH/RVT-directie: schaal 3.81.ABIS+8
    RD55 = "RD55"  # RH/RVT-directie: schaal 3.81.BBIS
    RD56 = "RD56"  # RH/RVT-directie: schaal 3.81.BBIS+5
    RD57 = "RD57"  # RH/RVT-directie: schaal 3.81.BBIS+8
    RD58 = "RD58"  # RH/RVT-directie: schaal 3.81.CBIS
    RD59 = "RD59"  # RH/RVT-directie: schaal 3.81.CBIS+5
    RD60 = "RD60"  # RH/RVT-directie: schaal 3.81.CBIS+8
    RD61 = "RD61"  # RH/RVT-directie: schaal 3.81.ABIS+10
    RD62 = "RD62"  # RH/RVT-directie: schaal 3.81.BBIS+10
    RD63 = "RD63"  # RH/RVT-directie: schaal 3.81.CBIS+10
    RD64 = "RD64"  # RH/RVT-directie: schaal 3.87.ABIS
    RD65 = "RD65"  # RH/RVT-directie: schaal 3.87.ABIS+5
    RD66 = "RD66"  # RH/RVT-directie: schaal 3.87.ABIS+8
    RD67 = "RD67"  # RH/RVT-directie: schaal 3.87.BBIS
    RD68 = "RD68"  # RH/RVT-directie: schaal 3.87.BBIS+5
    RD69 = "RD69"  # RH/RVT-directie: schaal 3.87.BBIS+8
    RD70 = "RD70"  # RH/RVT-directie: schaal 3.87.ABIS+10
    RD71 = "RD71"  # RH/RVT-directie: schaal 3.87.BBIS+10
    # Care homes pink scales (RR series)
    RR01 = "RR01"  # RH/RVT ROZE SCHAAL 01: 1.12
    RR04 = "RR04"  # RH EN RVT ROZE : SCHAAL 04: 1.26
    RR05 = "RR05"  # RH/RVT ROZE : SCHAAL 5 : 1.50
    RR06 = "RR06"  # RH/RVT ROZE : SCHAAL : 1.35
    RR09 = "RR09"  # RH/RVT ROZE : SCHAAL 09 : 1.40/1.57
    RR10 = "RR10"  # RH/RVT ROZE : SCHAAL 10 : 1.40
    RR12 = "RR12"  # RH/RVT ROZE : SCHAAL 12 : 1.43-1.55
    RR13 = "RR13"  # RH/RVT ROZE : SCHAAL 13 : 1.59
    RR15 = "RR15"  # RH/RVT ROZE : SCHAAL 15 : 1.55-1.61-1.77
    RR16 = "RR16"  # RH/RVT ROZE : SCHL16:1.55/1.61/1.77(+2J)
    RR17 = "RR17"  # RH/RVT ROZE : SCHAAL 17 : 1.80
    RR18 = "RR18"  # RH/RVT-ROZE : SCHAAL 18: 1.22
    # Care homes white scales (RW series)
    RW01 = "RW01"  # Rh/rvt-wit: schaal 01: 1.00
    RW02 = "RW02"  # Rh/rvt-wit: schaal 02: 1.01
    RW03 = "RW03"  # Rh/rvt-wit: schaal 03: 1.79
    RW04 = "RW04"  # Rh/rvt-wit: schaal 04: 1.81
    RW05 = "RW05"  # Rh/rvt-wit: schaal 05: 1.87
    RW06 = "RW06"  # Rh/rvt-wit: schaal 06: 1.91
    RW07 = "RW07"  # Rh/rvt-wit: schaal 07: 1.92
    RW08 = "RW08"  # Rh/rvt-wit: schaal 08: 1.93
    RW09 = "RW09"  # Rh/rvt-wit: schaal 09: 1.94
    RW10 = "RW10"  # Rh/rvt-wit: schaal 10: 1.95
    RW11 = "RW11"  # Rh/rvt-wit: schaal 11: 1.99
    RW12 = "RW12"  # Rh/rvt-wit: schaal 12: 13.3
    # Education sector (SN series)
    SN158 = "SN158"  # Hoger Onderw 1 cyclus < 9J Anc
    SN200 = "SN200"  # Sec.Onderw.2Grd of lager < 9J
    SN201 = "SN201"  # Sec.Onderw.2Grd of lager >= 9J
    SN202 = "SN202"  # Sec.Onderwijs < 9 Jaar Anc.
    SN203 = "SN203"  # Sec.Onderwijs >= 9 Jaar Anc.
    SN345 = "SN345"  # Hoger Onderw. 1 cyclus >= 9J
    SN542 = "SN542"  # Academisch niveau
    SNCAT1 = "SNCAT1"  # Ongeschoolden
    SNCAT2 = "SNCAT2"  # Eenvoudig geoefenden
    SNCAT3 = "SNCAT3"  # Volledig geoefenden
    SNCAT4 = "SNCAT4"  # Geschoolden
    SNCAT5 = "SNCAT5"  # Meergeschoolden en vaklieden
    SNCAT6 = "SNCAT6"  # Ploegbazen
    # Hospital blue scales (ZB series)
    ZB02 = "ZB02"  # Zh-blauw: schaal 02: 1.11/1.12
    ZB03 = "ZB03"  # Zh-blauw: schaal 03: 1.14
    ZB04 = "ZB04"  # Zh-blauw: schaal 04: 1.16
    ZB05 = "ZB05"  # Zh-blauw: schaal 05: 1.18
    ZB06 = "ZB06"  # Zh-blauw: schaal 06: 1.22
    ZB07 = "ZB07"  # Zh-blauw: schaal 07: 1.24
    ZB08 = "ZB08"  # Zh-blauw: schaal 08: 1.26
    ZB09 = "ZB09"  # Zh-blauw: schaal 09: 1.30
    ZB10 = "ZB10"  # Zh-blauw: schaal 10: 1.31
    ZB11 = "ZB11"  # Zh-blauw: schaal 11: 1.35
    ZB12 = "ZB12"  # Zh-blauw: schaal 12: 1.39
    ZB13 = "ZB13"  # Zh-blauw: schaal 13: 1.40
    ZB14 = "ZB14"  # Zh-blauw: schaal 14: 1.40/1.57
    ZB15 = "ZB15"  # Zh-blauw: schaal 15: 1.43/1.55
    ZB16 = "ZB16"  # Zh-blauw: schaal 16: 1.45
    ZB17 = "ZB17"  # Zh-blauw: schaal 17: 1.47
    ZB18 = "ZB18"  # Zh-blauw: schaal 18: 1.50
    ZB19 = "ZB19"  # Zh-blauw: schaal 19: 1.53
    ZB20 = "ZB20"  # Zh-blauw: schaal 20: 1.54
    ZB21 = "ZB21"  # Zh-blauw: schaal 21: 1.55/1.61/1.77
    ZB22 = "ZB22"  # Zh-blauw: schaal 22: 1.55/1.61/1.77(+2J)
    ZB23 = "ZB23"  # Zh-blauw: schaal 23: 1.59
    ZB24 = "ZB24"  # Zh-blauw: schaal 24: 1.61/1.77
    ZB25 = "ZB25"  # Zh-blauw: schaal 25: 1.62
    ZB26 = "ZB26"  # Zh-blauw: schaal 26: 1.63
    ZB27 = "ZB27"  # Zh-blauw: schaal 27: 1.66
    ZB28 = "ZB28"  # Zh-blauw: schaal 28: 1.78SP
    ZB29 = "ZB29"  # Zh-blauw: schaal 29: 1.79
    ZB30 = "ZB30"  # Zh-blauw: schaal 30: 1.80
    ZB31 = "ZB31"  # Zh-blauw: schaal 31: 1.81
    # Hospital management (ZD series)
    ZD01 = "ZD01"  # Zh-Dep.Hoofd-Alg.Dir.: 200 / 300
    ZD02 = "ZD02"  # Zh-Dep.Hoofd-Alg.Dir.: 201 / 300
    ZD03 = "ZD03"  # Zh-Dep.Hoofd-Alg.Dir.: 100 / 300
    ZD04 = "ZD04"  # Zh-Dep.Hoofd-Alg.Dir.: 101 / 300
    # Hospital green scales (ZG series)
    ZG01 = "ZG01"  # Zh-groen: schaal 01: 1.16
    ZG02 = "ZG02"  # Zh-groen: schaal 02: 1.30
    ZG03 = "ZG03"  # Zh-groen: schaal 03: 1.43
    ZG04 = "ZG04"  # Zh-groen: schaal 04: 1.58
    ZG05 = "ZG05"  # Zh-groen: schaal 05: 1.59
    ZG06 = "ZG06"  # Zh-groen: schaal 06: 1.67
    ZG07 = "ZG07"  # Zh-groen: schaal 07: 1.75
    ZG08 = "ZG08"  # Zh-groen: schaal 08: 1.86
    # Hospital white scales (ZW series)
    ZW01 = "ZW01"  # Zh-wit: schaal 01: 1.00
    ZW02 = "ZW02"  # Zh-wit: schaal 02: 1.01
    ZW03 = "ZW03"  # Zh-wit: schaal 03: 1.79
    ZW04 = "ZW04"  # Zh-wit: schaal 04: 1.81
    ZW05 = "ZW05"  # Zh-wit: schaal 05: 1.87
    ZW06 = "ZW06"  # Zh-wit: schaal 06: 1.91
    ZW07 = "ZW07"  # Zh-wit: schaal 07: 1.92
    ZW08 = "ZW08"  # Zh-wit: schaal 08: 1.93
    ZW09 = "ZW09"  # Zh-wit: schaal 09: 1.94
    ZW10 = "ZW10"  # Zh-wit: schaal 10: 1.95
    ZW11 = "ZW11"  # Zh-wit: schaal 11: 1.99
    ZW12 = "ZW12"  # Zh-wit: schaal 12: 13.3
    # Hospital yellow scales (ZY series)
    ZY01 = "ZY01"  # Zh-geel schaal 1.11
    ZY02 = "ZY02"  # Zh-geel schaal 1.12
    ZY03 = "ZY03"  # Zh-geel schaal 1.14
    ZY04 = "ZY04"  # Zh-geel schaal 1.16
    ZY05 = "ZY05"  # Zh-geel schaal 1.18
    ZY06 = "ZY06"  # Zh-geel schaal 1.22
    ZY07 = "ZY07"  # Zh-geel schaal 1.22/1.30
    ZY08 = "ZY08"  # Zh-geel schaal 1.24
    ZY09 = "ZY09"  # Zh-geel schaal 1.26
    ZY10 = "ZY10"  # Zh-geel schaal 1.30
    ZY11 = "ZY11"  # Zh-geel schaal 1.31
    ZY12 = "ZY12"  # Zh-geel schaal 1.39
    ZY13 = "ZY13"  # Zh-geel schaal 1.40
    ZY14 = "ZY14"  # Zh-geel schaal 1.40/1.57
    ZY15 = "ZY15"  # Zh-geel schaal 1.43/1.55
    ZY16 = "ZY16"  # Zh-geel schaal 1.45
    ZY17 = "ZY17"  # Zh-geel schaal 1.47
    ZY18 = "ZY18"  # Zh-geel schaal 1.50
    ZY19 = "ZY19"  # Zh-geel schaal 1.53
    ZY20 = "ZY20"  # Zh-geel schaal 1.54
    ZY21 = "ZY21"  # Zh-geel schaal 1.55/1.61/1.77
    ZY22 = "ZY22"  # Zh-geel schaal 1.55/16/1.77(+2J)
    ZY23 = "ZY23"  # Zh-geel schaal 1.59
    ZY24 = "ZY24"  # Zh-geel schaal 1.61/1.77
    ZY25 = "ZY25"  # Zh-geel schaal 1.62
    ZY26 = "ZY26"  # Zh-geel schaal 1.63
    ZY27 = "ZY27"  # Zh-geel schaal 1.66
    ZY28 = "ZY28"  # Zh-geel schaal 1.78
    ZY29 = "ZY29"  # Zh-geel schaal 1.80
    ZY30 = "ZY30"  # Zh-geel schaal 1.81

class SectorRiskGroupCAOEnum(Enum):
    """
    Sector risicogroep / CBS CAO code enum
    Shared enum for: ViRi (Afwijkende sector risicogroep), ViFc (Afwijkende CBS cao), CAHi (Cao-code inlener)
    Dutch sector classification codes for risk groups and collective labor agreements
    """
    EMPTY = ""  # Empty value
    NIET_VAN_TOEPASSING = "0000"  # Niet van toepassing
    # Note: This enum contains 1000+ values representing Dutch CAO codes and risk group sectors
    # The full list includes all Dutch collective labor agreements and industry sectors
    # Values range from codes like "10" (BOUW & INFRA) to "9999" (GEEN REGULIERE CAO VAN TOEPASSING)
    # For brevity and maintainability, representative samples are included below
    # Full validation is handled by AFAS API

    BOUW_INFRA = "10"  # BOUW & INFRA
    TRANSAVIA_GROND = "100"  # TRANSAVIA AIRLINES GRONDPERSONEEL
    HANDELSVAART = "1029"  # HANDELSVAART
    THUISZORG = "1045"  # THUISZORG
    MBO = "1022"  # BEROEPSONDERWIJS EN VOLWASSENENEDUCATIE, MBO
    VOLKSBANK = "1027"  # DE VOLKSBANK
    RECREATIE = "1165"  # RECREATIE
    RECLASSERING = "117"  # RECLASSERING
    ZIEKENHUIZEN = "156"  # ZIEKENHUIZEN
    OPENBAAR_VERVOER = "163"  # OPENBAAR VERVOER
    HORECA = "182"  # HORECA- EN AANVERWANTE BEDRIJF
    JEUGDZORG = "234"  # JEUGDZORG
    GLASTUINBOUW = "1869"  # GLASTUINBOUW
    WELZIJN = "301"  # WELZIJN MAATSCHAPPELIJKE DIENSTVERLENING SOCIAAL WERK
    GEHANDICAPTENZORG = "317"  # GEHANDICAPTENZORG
    ENERGIE_NUTSBEDRIJVEN = "468"  # ENERGIE- EN NUTSBEDRIJVEN
    METALEKTRO = "487"  # METALEKTRO
    METALEKTRO_HP = "488"  # METALEKTRO HOGER PERSONEEL
    VERZEKERINGSBEDRIJF = "637"  # VERZEKERINGSBEDRIJF, CAO VOOR HET
    BANKEN_CAO = "632"  # BANKEN CAO
    UITZENDKRACHTEN = "633"  # UITZENDKRACHTEN
    BEROEPSGOEDERENVERVOER = "21"  # BEROEPSGOEDERENVERVOER OVER DE WEG
    SOCIALE_WERKVOORZIENING = "1345"  # SOCIALE WERKVOORZIENING
    PRIMAIR_ONDERWIJS = "1494"  # PRIMAIR ONDERWIJS
    VOORTGEZET_ONDERWIJS = "1188"  # VOORTGEZET ONDERWIJS VO
    HOGER_BEROEPSONDERWIJS = "625"  # HOGER BEROEPSONDERWIJS
    UNIVERSITEITEN = "1536"  # NEDERLANDSE UNIVERSITEITEN
    UMC = "1618"  # UNIVERSITAIRE MEDISCHE CENTRA
    GGZ = "1574"  # GEESTELIJKE GEZONDHEIDSZORG (GGZ)
    VERPLEEG_VERZORG = "49"  # VERPLEEG- EN VERZORGINGSHUIZEN EN THUISZORG ONDERDEEL VERPLEEG- EN VERZORGINGSHUIZEN
    KINDEROPVANG = "1612"  # KINDEROPVANG VOOR KINDERCENTRA EN GASTOUDEROPVANG
    GEMEENTEN = "1630"  # BRANCHE CAO GEMEENTEN
    RIJK_CAO = "1646"  # RIJK CAO
    PROVINCIALE_SECTOR = "1637"  # PROVINCIALE SECTOR
    POLITIE = "1636"  # SECTOR POLITIE
    DEFENSIE = "1597"  # SECTOR DEFENSIE
    WATERSCHAPPEN = "1294"  # WERKEN VOOR WATERSCHAPPEN
    RAILINFRA = "1393"  # RAILINFRASTRUCTUUR
    NS = "603"  # NEDERLANDSE SPOORWEGEN (NS)
    SCHOONMAAK_GLAZENWASSERS = "433"  # SCHOONMAAK- EN GLAZENWASSERSBEDRIJF
    BEVEILIGING = "496"  # PARTICULIERE BEVEILIGING
    RETAIL_NON_FOOD = "727"  # RETAIL NON-FOOD
    KAPPERS = "405"  # KAPPERSBEDRIJF
    AMBULANCEZORG = "696"  # AMBULANCEZORG (PERSONEEL)
    ZORGVERZEKERAARS = "615"  # ZORGVERZEKERAARS
    APOTHEKEN = "50"  # APOTHEKEN
    HUISARTSENZORG = "721"  # HUISARTSENZORG
    TANDARTSASSISTENTEN = "1774"  # TANDARTSASSISTENTEN
    GRAFIMEDIA = "1287"  # GRAFIMEDIA
    ICT = "1296"  # INFORMATIE-, COMMUNICATIE- EN KANTOORTECHNOLOGIEBRANCHE (ICK)
    GEEN_CAO = "9999"  # GEEN REGULIERE CAO VAN TOEPASSING


class PartenaContractCategoryEnum(Enum):
    """Contract categorie enum - Partena specific"""
    EMPTY = ""  # Empty value
    ARBEIDER = "A"  # Arbeider
    BEDIENDE = "B"  # Bediende
    LEERCONTRACT_ARBEIDER = "C"  # Leercontract arbeider
    LEERCONTRACT_BEDIENDE = "D"  # Leercontract bediende
    NIET_ONDERWORPEN = "E"  # Niet onderworpen
    HUIS_PERSONEEL = "F"  # Huis Personeel

class PartenaContractTypeEnum(Enum):
    """Type Contract enum - Partena specific"""
    EMPTY = ""  # Empty value
    ZONDER_VOORWERP = "0"  # Zonder voorwerp
    ONBEKEND = "9"  # Onbekend
    ONBEPAALDE_DUUR = "A"  # Onbepaalde duur
    BEPAALDE_DUUR = "B"  # Bepaalde duur
    DUIDELIJK_OMSCHREVEN_WERK = "C"  # Duidelijk omschreven werk
    VERVANGING = "D"  # Vervanging

class RSZCategoryEnum(Enum):
    """RSZ-categorie enum - Belgian specific"""
    EMPTY = ""  # Empty value
    ZONDER_BETEKENIS_0 = "0"  # Zonder betekenis
    ZONDER_BETEKENIS_000 = "000"  # Zonder betekenis
    TIJDEL_ARB_LAND_010 = "010"  # Tijdel. arb.land-tuinb./SUPextra horeca
    ARB_FORFAIT_011 = "011"  # Arb.betaald m.forfait
    GEHANDICAPTE_ARB_012 = "012"  # Gehandicapte arbeider beschutte werkplaats
    ARBEIDER_BIJZONDER_013 = "013"  # Arbeider bijzonder geval
    ARBEIDER_GEWONE_014 = "014"  # Arbeider gewone categorie
    ARBEIDER_GEWONE_015 = "015"  # Arbeider gewone categorie
    MIJNWERKER_BOVEN_016 = "016"  # Mijnwerker bovengronds
    MIJNWERKER_ONDER_017 = "017"  # Mijnwerker ondergronds
    LEERL_ARB_020 = "020"  # Leerl.arb. SUPextra Horeca
    LEERLING_ARB_FORFAIT_022 = "022"  # Leerling arbeider & stagiair met forfaitair loon
    GESUBSIDIEERD_CONTR_023 = "023"  # Gesubsidieerd contractueel
    GESUBSIDIEERD_CONTR_024 = "024"  # Gesubsidieerd contractueel
    GEHANDICAPTE_GESUBSID_025 = "025"  # Gehandicapte gesubsidieerd contract
    GEWONE_LEERLING_026 = "026"  # Gewone leerling arbeider & stagiair
    GEWONE_LEERLING_027 = "027"  # Gewone leerling arbeider & stagiair
    GEHANDICAPTE_FORFAIT_028 = "028"  # Gehandicapte gesubsidieerde contractueel met forfaitair loon
    GESUBSID_FORFAIT_029 = "029"  # Gesubsidieerde contractueel met forfaitair loon
    ERKENDE_LEERLING_035 = "035"  # Erkende leerling arbeider
    LEERJONGEN_039 = "039"  # Leerjongen hoofdarbeider
    ARBEIDSONGEVAL_041 = "041"  # Arbeidsongeval
    DIENSTBODE_045 = "045"  # Dienstbode
    ARTIEST_046 = "046"  # Artiest
    ARTIEST_DEELTIJDS_047 = "047"  # Artiest-deeltijds leerplichtige
    FLEXI_JOB_050 = "050"  # Flexi-job
    TIJDEL_ARB_LAND_10 = "10"  # Tijdel. arb.land-tuinb./SUPextra horeca
    ARB_FORFAIT_11 = "11"  # Arb.betaald m.forfait
    GEHANDICAPTE_ARB_12 = "12"  # Gehandicapte arbeider beschutte werkplaats
    ARBEIDER_BIJZONDER_13 = "13"  # Arbeider bijzonder geval
    ARBEIDER_GEWONE_14 = "14"  # Arbeider gewone categorie
    ARBEIDER_GEWONE_15 = "15"  # Arbeider gewone categorie
    MIJNWERKER_BOVEN_16 = "16"  # Mijnwerker bovengronds
    MIJNWERKER_ONDER_17 = "17"  # Mijnwerker ondergronds
    LEERL_ARB_20 = "20"  # Leerl.arb. SUPextra Horeca
    LEERLING_ARB_FORFAIT_22 = "22"  # Leerling arbeider & stagiair met forfaitair loon
    GESUBSIDIEERD_CONTR_23 = "23"  # Gesubsidieerd contractueel
    GESUBSIDIEERD_CONTR_24 = "24"  # Gesubsidieerd contractueel
    GEHANDICAPTE_GESUBSID_25 = "25"  # Gehandicapte gesubsidieerd contract
    GEWONE_LEERLING_26 = "26"  # Gewone leerling arbeider & stagiair
    GEWONE_LEERLING_27 = "27"  # Gewone leerling arbeider & stagiair
    GEHANDICAPTE_FORFAIT_28 = "28"  # Gehandicapte gesubsidieerde contractueel met forfaitair loon
    GESUBSID_FORFAIT_29 = "29"  # Gesubsidieerde contractueel met forfaitair loon
    ERKENDE_LEERLING_35 = "35"  # Erkende leerling arbeider
    LEERJONGEN_39 = "39"  # Leerjongen hoofdarbeider
    ARBEIDSONGEVAL_41 = "41"  # Arbeidsongeval
    HUISPERSONEEL_EERSTE_43 = "43"  # Huispersoneel 1ste aangeworven
    LEERLING_BED_439 = "439"  # Leerling bediende
    DIENSTBODE_45 = "45"  # Dienstbode
    BEDIENDE_FLEXI_450 = "450"  # Bediende Flexi-job
    ARTIEST_46 = "46"  # Artiest
    ARTIEST_DEELTIJDS_47 = "47"  # Artiest-deeltijds leerplichtige
    LEERL_BED_480 = "480"  # Leerl.bed. SUPextra Horeca
    GESUBSID_BED_484 = "484"  # Gesubsidieerde contractuele bediende
    GEHANDICAPTE_BED_485 = "485"  # Gehandicapte gesubsidieerde contractuele bediende
    LEERPL_FORF_486 = "486"  # Leerpl.gelegenh.bed.(forf)
    GEW_LEERL_BED_487 = "487"  # Gew.leerl.bed. & stag.
    BEDIENDE_SUP_490 = "490"  # Bediende SUPextra Horeca
    BEDIENDE_ANPCB_491 = "491"  # Bediende anpcb
    MINDER_VALIDE_BED_492 = "492"  # Minder valide bediende
    BEDIENDE_SPECIAAL_493 = "493"  # Bediende (speciaal geval)
    BEDIENDE_SPECIAAL_494 = "494"  # Bediende (speciaal geval)
    GEWONE_BED_495 = "495"  # Gewone bediende
    GELEGENH_BED_496 = "496"  # Gelegenh.bed.(forf)
    ONTHAALOUDER_497 = "497"  # Onthaalouder
    DOCTORAATSBEURS_498 = "498"  # Doctoraatsbeurs buiten EV
    FLEXI_JOB_50 = "50"  # Flexi-job
    STATUTAIR_675 = "675"  # Statutair
    ENKEL_VRZ_A_74 = "74"  # Enkel vrz.gz (a) (vrij onderwijs)
    ENKEL_VRZ_B_75 = "75"  # Enkel vrz.gz (b) (Universitair onderwij
    LEERLING_BED_ANPCB_82 = "82"  # Leerling bediende & stagiair (anpcb)
    BED_HUISPERSONEEL_83 = "83"  # Bediende huispersoneel
    GESUBSID_B_84 = "84"  # Gesubsidieerde contractueel (b)
    STUDENT_840 = "840"  # Student
    GESUBSID_GEHAND_85 = "85"  # Gesubsidieerde contractueel gehandicapte beschutte werkplaats
    LEERLING_BED_87 = "87"  # Leerling bediende & stagiair
    BRUGGEPENSIONEERDE_879 = "879"  # Bruggepensioneerde
    PSEUDO_BRUG_CANADA_883 = "883"  # Pseudo-bruggepensioneerde (canada dry)
    PSEUDO_BRUG_TIJDSKREDIET_885 = "885"  # Pseudo-bruggepensioneerde (tijdskrediet)
    BEDIENDE_ANPCB_91 = "91"  # Bediende (anpcb)
    GEHANDICAPTE_HOOFD_92 = "92"  # Gehandicapte hoofdarbeider beschutte werkplaats
    GEWOON_BED_SPORTLUI_95 = "95"  # Gewoon bed.& betaalde sportlui

# Subscription-related enums
class ItemTypeEnum(Enum):
    """Item type enum for subscription lines (VaIt)"""
    EMPTY = ""
    WERKSOORT = "1"  # Werksoort
    ARTIKEL = "2"  # Artikel
    TEKST = "3"  # Tekst
    SUBTOTAAL = "4"  # Subtotaal
    TOESLAG = "5"  # Toeslag
    KOSTEN = "6"  # Kosten
    SAMENSTELLING = "7"  # Samenstelling
    CURSUS = "8"  # Cursus
    PRODUCTIE_INDICATOR = "10"  # Productie-indicator
    DEEG = "11"  # Deeg
    ARTIKELDIMENSIETOTAAL = "14"  # Artikeldimensietotaal

class AccountReferenceEnum(Enum):
    """
    used by journal entry create schema, part of AFAS Mutaties API
    schema: JournalFinancialEntryCreate (FiEntries), field: account_reference (VaAs)
    Kenmerk rekening 1 = Grootboekrekening; 2 = Debiteur; 3 = Crediteur"""
    EMPTY = ""
    GROOTBOEKREKENING = "1"   # Grootboekrekening
    DEBITEUR = "2"            # Debiteur
    CREDITEUR = "3"           # Crediteur
