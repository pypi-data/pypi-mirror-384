from ..prompts.data import iso_to_adj

# list of cuisines
# AMERICAS
CUI_US_CANADA = "us/canadian"
CUI_LATIN_AMERICAN = "latin american"
CUI_LATIN_AMERICAN_OTHER = "latin american other"
CUI_CARIBBEAN = "caribbean"
# ASIA
CUI_ASIAN = "asian"
CUI_MIDDLE_EASTERN = "middle eastern"
# EUROPE
CUI_GREEK_TURKISH = "greek/turkish"
CUI_BALKAN = "balkan"
CUI_EUROPEAN = "european"
CUI_MEDITERRANEAN = "mediterranean"
CUI_SPAIN_PORTUGAL = "spanish/portuguese"
CUI_GERMANIC = "germanic"
CUI_BRITISH = "british"
CUI_AFRICAN = "african"
# OCEANIA
CUI_AUSTRALIAN_NZ = "australian/nz"

CUI_OTHER = "other"


ent_to_cui = {
    # AMERICAS
    "american": CUI_US_CANADA,
    r"latin american$": CUI_LATIN_AMERICAN,
    r"south(?:ern)? american$": CUI_LATIN_AMERICAN,
    r"central american$": CUI_LATIN_AMERICAN_OTHER,
    "caribbean": CUI_CARIBBEAN,
    # ASIA
    r"\basian$": CUI_ASIAN,
    r"middle eastern$": CUI_MIDDLE_EASTERN,
    r"near east": CUI_MIDDLE_EASTERN,
    # EUROPE
    "balkan": CUI_BALKAN,
    "scandinavian": CUI_EUROPEAN,
    "european": CUI_EUROPEAN,
    "mediterranean": CUI_MEDITERRANEAN,
    "british": CUI_BRITISH,
    "scottish": CUI_BRITISH,
    "irish": CUI_BRITISH,
    "welsh": CUI_BRITISH,
    "english": CUI_BRITISH,
    r"african$": CUI_AFRICAN,
    # OCEANIA
    "oceanian": CUI_AUSTRALIAN_NZ,
}


# dictionary containing cuisines and their corresponding countries (alpha-2 codes)
cui_to_iso = {
    # AMERICAS
    CUI_US_CANADA: [
        "US",  # United States
        "CA",  # Canada
    ],
    CUI_LATIN_AMERICAN: [
        "AR",  # Argentina
        "BZ",  # Belize
        "BO",  # Bolivia
        "BR",  # Brazil
        "CL",  # Chile
        "CO",  # Colombia
        "CR",  # Costa Rica
        "CU",  # Cuba
        "DO",  # Dominican Republic
        "EC",  # Ecuador
        "GT",  # Guatemala
        "HN",  # Honduras
        "MX",  # Mexico
        "NI",  # Nicaragua
        "PA",  # Panama
        "PE",  # Peru
        "PR",  # Puerto Rico
        "PY",  # Paraguay
        "SV",  # El Salvador
        "UY",  # Uruguay
        "VE",  # Venezuela
    ],
    CUI_LATIN_AMERICAN_OTHER: [
        "BZ",  # Belize
        "BO",  # Bolivia
        "CO",  # Colombia
        "CR",  # Costa Rica
        "CU",  # Cuba
        "DO",  # Dominican Republic
        "EC",  # Ecuador
        "GT",  # Guatemala
        "HN",  # Honduras
        "NI",  # Nicaragua
        "PA",  # Panama
        "PE",  # Peru
        "PR",  # Puerto Rico
        "PY",  # Paraguay
        "SV",  # El Salvador
        "UY",  # Uruguay
        "VE",  # Venezuela
    ],
    CUI_CARIBBEAN: [
        "AG",  # Antigua and Barbuda
        "AW",  # Aruba
        "AI",  # Anguilla
        "BB",  # Barbados
        "BS",  # Bahamas
        "BM",  # Bermuda
        "CU",  # Cuba
        "CW",  # Curaçao
        # "DM",  # Dominica
        "DO",  # Dominican Republic
        "GD",  # Grenada
        "GY",  # Guyana
        "HT",  # Haiti
        "JM",  # Jamaica
        "KN",  # Saint Kitts and Nevis
        "KY",  # Cayman Islands
        "LC",  # Saint Lucia
        "VC",  # Saint Vincent and the Grenadines
        "TT",  # Trinidad and Tobago
    ],
    # ASIA
    CUI_ASIAN: [
        "AF",  # Afghanistan
        "AM",  # Armenia
        "AZ",  # Azerbaijan
        "BD",  # Bangladesh
        "BT",  # Bhutan
        "CN",  # China
        "ID",  # Indonesia
        "IN",  # India
        "JP",  # Japan
        "KH",  # Cambodia
        "KP",  # North Korea
        "KR",  # South Korea
        "KG",  # Kyrgyzstan
        "KZ",  # Kazakhstan
        "LA",  # Laos
        "LK",  # Sri Lanka
        "MM",  # Myanmar
        "MN",  # Mongolia
        "MO",  # Macau
        "MV",  # Maldives
        "MY",  # Malaysia
        "NP",  # Nepal
        "PH",  # Philippines
        "PK",  # Pakistan
        "SG",  # Singapore
        "TH",  # Thailand
        "TJ",  # Tajikistan
        "TL",  # East Timor
        "TM",  # Turkmenistan
        "UZ",  # Uzbekistan
        "TW",  # Taiwan
        "VN",  # Vietnam
    ],
    CUI_MIDDLE_EASTERN: [
        "AE",  # United Arab Emirates
        "BH",  # Bahrain
        "CY",  # Cyprus
        "EG",  # Egypt
        "IR",  # Iran
        "IQ",  # Iraq
        "JO",  # Jordan
        "KW",  # Kuwait
        "LB",  # Lebanon
        "OM",  # Oman
        "IL",  # Israel
    ],
    # EUROPE
    CUI_EUROPEAN: [
        "AD",  # Andorra
        "AL",  # Albania
        "AT",  # Austria
        "BA",  # Bosnia and Herzegovina
        "BE",  # Belgium
        "BG",  # Bulgaria
        "BY",  # Belarus
        "CH",  # Switzerland
        "CZ",  # Czech Republic
        "DE",  # Germany
        "DK",  # Denmark
        "EE",  # Estonia
        "ES",  # Spain
        "FI",  # Finland
        "FO",  # Faroe Islands
        "FR",  # France
        "GB",  # United Kingdom
        "GE",  # Georgia
        "GI",  # Gibraltar
        "GR",  # Greece
        "HR",  # Croatia
        "HU",  # Hungary
        "IE",  # Ireland
        "IS",  # Iceland
        "IT",  # Italy
        "LI",  # Liechtenstein
        "LT",  # Lithuania
        "LU",  # Luxembourg
        "LV",  # Latvia
        "MC",  # Monaco
        "MD",  # Moldova
        "ME",  # Montenegro
        "MK",  # North Macedonia
        "MT",  # Malta
        "NL",  # Netherlands
        "NO",  # Norway
        "PL",  # Poland
        "PT",  # Portugal
        "RO",  # Romania
        "RS",  # Serbia
        "RU",  # Russia
        "SE",  # Sweden
        "SI",  # Slovenia
        # "SJ",  # Svalbard and Jan Mayen
        "SK",  # Slovakia
        "SM",  # San Marino
        "TR",  # Turkey
        "UA",  # Ukraine
        # "VA",  # Vatican City
    ],
    CUI_GERMANIC: [
        "AT",  # Austria
        "CH",  # Switzerland
        "DE",  # Germany
        "LI",  # Liechtenstein
        "LU",  # Luxembourg
    ],
    CUI_BRITISH: [
        "GB",  # United Kingdom
        "IE",  # Ireland
    ],
    CUI_SPAIN_PORTUGAL: [
        "ES",  # Spain
        "PT",  # Portugal
    ],
    CUI_GREEK_TURKISH: [
        "GR",  # Greece
        "TR",  # Turkey
    ],
    CUI_MEDITERRANEAN: [
        "AD",  # Andorra
        "AL",  # Albania
        "BA",  # Bosnia and Herzegovina
        "CY",  # Cyprus
        "EG",  # Egypt
        "GI",  # Gibraltar
        "HR",  # Croatia
    ],
    CUI_BALKAN: [
        "AL",  # Albania
        "BA",  # Bosnia and Herzegovina
        "BG",  # Bulgaria
        "GR",  # Greece
        "HR",  # Croatia
        "MK",  # North Macedonia
        "ME",  # Montenegro
        "RO",  # Romania
        "RS",  # Serbia
        "SI",  # Slovenia
        "XK",  # Kosovo
    ],
    CUI_AFRICAN: [
        "AO",  # Angola
        "BF",  # Burkina Faso
        "BI",  # Burundi
        "BJ",  # Benin
        "BW",  # Botswana
        # "CD",  # Democratic Republic of the Congo
        "CF",  # Central African Republic
        "CG",  # Republic of the Congo
        "CI",  # Ivory Coast
        "CM",  # Cameroon
        "CV",  # Cape Verde
        "DJ",  # Djibouti
        "DZ",  # Algeria
        "ER",  # Eritrea
        "ET",  # Ethiopia
        "GA",  # Gabon
        "GH",  # Ghana
        "GM",  # Gambia
        "GN",  # Guinea
        "GQ",  # Equatorial Guinea
        "GW",  # Guinea-Bissau
        "KE",  # Kenya
        "KM",  # Comoros
        "LR",  # Liberia
        "LS",  # Lesotho
        "LY",  # Libya
        "MA",  # Morocco
        "MG",  # Madagascar
        "ML",  # Mali
        "MR",  # Mauritania
        "MU",  # Mauritius
        "MW",  # Malawi
        "MZ",  # Mozambique
        "NA",  # Namibia
        "NE",  # Niger
        "NG",  # Nigeria
        "RW",  # Rwanda
        "SC",  # Seychelles
        "SD",  # Sudan
        "SL",  # Sierra Leone
        "SN",  # Senegal
        "SO",  # Somalia
        # "SS",  # South Sudan
        "ST",  # São Tomé and Príncipe
        "SZ",  # Eswatini
        "TD",  # Chad
        "TG",  # Togo
        "TN",  # Tunisia
        "TZ",  # Tanzania
        "UG",  # Uganda
        "ZA",  # South Africa
        "ZM",  # Zambia
        "ZW",  # Zimbabwe
    ],
    CUI_AUSTRALIAN_NZ: [
        "AU",  # Australia
        "NZ",  # New Zealand
    ],
}


cui_list = [
    CUI_AFRICAN,
    CUI_ASIAN,
    CUI_EUROPEAN,
    CUI_CARIBBEAN,
    CUI_BALKAN,
    CUI_BRITISH,
    CUI_GERMANIC,
    CUI_MEDITERRANEAN,
    CUI_GREEK_TURKISH,
    CUI_SPAIN_PORTUGAL,
    CUI_US_CANADA,
    CUI_LATIN_AMERICAN,
    CUI_LATIN_AMERICAN_OTHER,
    CUI_MIDDLE_EASTERN,
    CUI_AUSTRALIAN_NZ,
    # CUI_OTHER,
]


iso_to_cui = {iso: [iso_to_adj[iso]] for iso in iso_to_adj.keys()}

# iterate over cuisines backwards so that the first one is the most important
for cui in reversed(cui_list):
    for iso in cui_to_iso[cui]:
        # add to start
        iso_to_cui[iso] = [cui] + iso_to_cui[iso]


# def cuisine_from_country(country):
#     return iso_to_cui.get(country, CUI_OTHER)
