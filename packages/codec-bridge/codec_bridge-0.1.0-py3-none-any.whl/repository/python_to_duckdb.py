PYTHON_TO_DUCKDB_ENCODING = {
    # --- UTF-8 ---
    'utf_8': 'utf-8',
    'utf8': 'utf_8',
    'utf_16': 'utf-16',
    'utf-16': 'utf-16',
    'utf_16be': 'utf-16-be',
    'utf_16le': 'utf-16-le',

    # --- ASCII ---
    'ascii': 'ascii',
    'us-ascii': 'ascii',
    'ibm-367_p100-1995': 'ascii',
    'iso-ir-6': 'ascii',

    # --- Latin-1 (Ocidental Europe) ---
    'latin-1': 'latin_1',
    'latin1': 'latin_1',
    'iso-8859-1': 'latin_1',
    'iso_8859_1': 'latin_1',
    'ibm-819': 'latin_1',
    'cp819': 'latin_1',
    'iso8859_1': 'latin_1',
    'iso8859_14': 'ISO_8859_14',
    'iso8859_10': 'ISO_8859_10',

    # --- Windows-1252 ---
    'windows-1252': 'ISO8859_1',
    'cp1252': 'windows_1252',

    # --- Latin-2 (Central Europe / Oriental Europe) ---
    'iso-8859-2': 'latin_2',
    'iso_8859_2': 'latin_2',
    'latin-2': 'latin_2',
    'latin2': 'latin_2',
    'windows-1250': 'CP1250',
    'cp1250': 'windows_1250',
    'cp852': 'cp852',
    "mac_iceland": "MAC_IS",

    # --- Cyrillic ---
    'iso-8859-5': 'iso_8859_5',
    'iso_8859_5': 'iso_8859_5',
    'cyrillic': 'iso_8859_5',
    'windows-1251': 'windows_1251',
    'cp1251': 'windows_1251',
    'koi8-r': 'koi8_r',
    'koi8_r': 'koi8_r',

    # --- Greek ---
    'iso-8859-7': 'iso_8859_7',
    'iso_8859_7': 'iso_8859_7',
    'windows-1253': 'windows_1253',
    'cp1253': 'windows_1253',

    # --- Japenese ---
    'shift_jis': 'shift_jis',
    'sjis': 'shift_jis',
    'ibm-943': 'shift_jis',
    'windows-932': 'shift_jis',
    'euc-jp': 'euc_jp',

    # --- Chinese ---
    'gbk': 'gbk',
    'gb2312': 'gb2312',
    'big5': 'big5',

    # --- Korean ---
    'euc-kr': 'euc_kr',
    'cp949': 'cp949',
    'johab': 'johab',
}

ENCODINGS_UNDERSCORE_CONFLICT = {
    'shift_jis',
    'cp932',
    'big5',
    'gbk',
    'gb2312',
}