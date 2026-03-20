"""
Конфигурации парсеров для разных банков
Добавляйте новый банк просто описав его формат
"""

BANK_CONFIGS = {
    'revolut': {
        'name': 'Revolut',
        'patterns': ['revolut', 'antonijas.*revolut'],
        'file_type': 'csv',
        'encoding': 'utf-8',
        'delimiter': ',',
        'headers': {
            'date': 'Date completed (UTC)',
            'amount': 'Amount',
            'currency': 'Payment currency',
            'description': 'Description',
            'type': 'Type',
            'reference': 'Reference',
            'balance': 'Balance'
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'article_pattern': r'\((\d+\.\d+\.\d+\.?\d*)\)',
        'skip_rows': 0,
        'skip_footer': 0
    },
    
    'industra': {
        'name': 'Industra Bank',
        'patterns': ['industra', 'plavas', 'antonijas.*industra'],
        'file_type': 'csv',
        'encoding': 'utf-8-sig',
        'delimiter': ',',
        'has_header': False,
        'header_marker': 'Дата транзакции',
        'headers': {
            'date': 0,
            'value_date': 1,
            'transaction_id': 2,
            'reference': 3,
            'type': 4,
            'payee': 5,
            'payee_code': 6,
            'payee_account': 7,
            'payee_bank': 8,
            'payee_bic': 9,
            'description': 10,
            'debit': 11,
            'credit': 12
        },
        'amount_sign': 'debit_credit',
        'date_format': '%d.%m.%Y',
        'article_pattern': r'\((\d+\.\d+\.\d+\.?\d*)\)',
        'skip_rows': 9,
        'skip_footer': 0
    },
    
    'wise': {
        'name': 'Wise',
        'patterns': ['wise', 'saida.*wise'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'All transactions',
        'headers': {
            'date': 'Дата',
            'amount': 'Сумма',
            'currency': 'Валюта',
            'description': 'Описание',
            'payee': 'Имя получателя',
            'payer': 'Имя плательщика',
            'type': 'Тип транзакции'
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'article_pattern': r'(\d+\.\d+\.\d+\.?\d*)'
    },
    
    'n26': {
        'name': 'N26',
        'patterns': ['n26', 'saida.*n26', 'N26', 'MAMMADBAYLI.*N26', 'ES2615632626363261721570'],
        'file_type': 'pdf',
        'encoding': 'utf-8',
        'description': 'Испанский N26'
    },
    
    'pasha_azn': {
        'name': 'Pasha Bank AZN',
        'patterns': ['pasha.*azn', 'bunda.*azn'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Statement',
        'headers': {
            'date': 'Əməliyyat tarixi',
            'exec_date': 'İcra tarixi',
            'payee': 'Ödəyən/Benefisiar',
            'description': 'Təyinat',
            'reference': 'İstinad No',
            'credit': 'Mədaxil',
            'debit': 'Məxaric',
            'balance': 'Balans'
        },
        'amount_sign': 'debit_credit',
        'date_format': '%d.%m.%Y',
        'skip_rows': 8,
        'has_header': True
    },
    
    'pasha_aed': {
        'name': 'Pasha Bank AED',
        'patterns': ['pasha.*aed', 'bunda.*aed'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Statement',
        'headers': {
            'date': 'Əməliyyat tarixi',
            'exec_date': 'İcra tarixi',
            'payee': 'Ödəyən/Benefisiar',
            'description': 'Təyinat',
            'reference': 'İstinad No',
            'credit': 'Mədaxil',
            'debit': 'Məxaric',
            'azn_equiv': 'AZN ekvivalent',
            'balance': 'Balans'
        },
        'amount_sign': 'debit_credit',
        'date_format': '%d.%m.%Y',
        'skip_rows': 8,
        'has_header': True
    },
    
    'kapital': {
        'name': 'Kapital Bank',
        'patterns': ['kapital'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Sheet0',
        'headers': {
            'date': 'Дата',
            'debit': 'Расход',
            'credit': 'Доход',
            'balance': 'Баланс',
            'description': 'Комментарии'
        },
        'amount_sign': 'debit_credit',
        'date_format': '%d-%m-%Y',
        'skip_rows': 8,
        'has_header': True
    },
    
    'mashreq': {
        'name': 'Mashreq Bank',
        'patterns': ['mashreq'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Account transactions Statement',
        'headers': {
            'date': 'Date',
            'value_date': 'Value Date',
            'reference': 'Reference Number',
            'description': 'Description',
            'credit': 'Credit',
            'debit': 'Debit',
            'balance': 'Balance'
        },
        'amount_sign': 'debit_credit',
        'date_format': '%d %b %Y',
        'skip_rows': 7,
        'has_header': True
    },
    
    'paysera_property': {
        'name': 'Paysera BS Property',
        'patterns': ['paysera.*property', 'BS PROPERTY', 'EVP7310016207804', 'LT573500010016207804'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Sheet1',
        'headers': {
            'type': 0,
            'statement_no': 1,
            'payment_id': 2,
            'date_time': 3,
            'payee': 4,
            'account': 5,
            'code': 6,
            'amount': 7,
            'currency': 8,
            'description': 9,
            'reference': 10,
            'credit_debit': 11,
            'balance': 12
        },
        'amount_sign': 'debit_credit',
        'date_format': '%Y-%m-%d',
        'skip_rows': 5,
        'has_header': False
    },
    
    'paysera_rerum': {
        'name': 'Paysera BS Rerum',
        'patterns': ['paysera.*rerum', 'BS RERUM', 'EVP4310016207887', 'LT473500010016207887'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Sheet1',
        'headers': {
            'type': 0,
            'statement_no': 1,
            'payment_id': 2,
            'date_time': 3,
            'payee': 4,
            'account': 5,
            'code': 6,
            'amount': 7,
            'currency': 8,
            'description': 9,
            'reference': 10,
            'credit_debit': 11,
            'balance': 12
        },
        'amount_sign': 'debit_credit',
        'date_format': '%Y-%m-%d',
        'skip_rows': 5,
        'has_header': False
    },
    
    'paysera_sveciy': {
        'name': 'Paysera Sveciy Namai',
        'patterns': ['paysera.*sveciy', 'sveciy', 'EVP0810011688673', 'LT033500010011688673'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'Sheet1',
        'headers': {
            'type': 0,
            'statement_no': 1,
            'payment_id': 2,
            'date_time': 3,
            'payee': 4,
            'account': 5,
            'code': 6,
            'amount': 7,
            'currency': 8,
            'description': 9,
            'reference': 10,
            'credit_debit': 11,
            'balance': 12
        },
        'amount_sign': 'debit_credit',
        'date_format': '%Y-%m-%d',
        'skip_rows': 3,
        'has_header': False
    },
    
    'unicredit_czk': {
        'name': 'UniCredit CZK',
        'patterns': ['unicredit', 'garpiz', 'koruna', 'twohills', 'molly', 'GARPIZ INTERNATIONAL', 'KORUNA KARLOVY VARY', 'UniCredit Bank'],
        'file_type': 'csv',
        'encoding': 'utf-8',
        'delimiter': ';',
        'headers': {
            'account': 'From Account',
            'amount': 'Amount',
            'currency': 'Currency',
            'date': 'Booking Date',
            'value_date': 'Value Date',
            'description': 'Transaction Details'
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'has_header': True,
        'skip_rows': 1
    },
    
    'csob_czk': {
        'name': 'CSOB CZK',
        'patterns': ['csob', 'džibik', 'dzibik'],
        'file_type': 'csv',
        'encoding': 'cp1250',
        'delimiter': ';',
        'headers': {
            'account': 'account number',
            'currency': 'account currency',
            'date': 'posting date',
            'amount': 'payment amount',
            'balance': 'balance',
            'type': 'transaction type',
            'counterparty': 'counterparty',
            'description': 'message to beneficiary and payer'
        },
        'amount_sign': 'as_is',
        'date_format': '%d.%m.%Y',
        'has_header': True
    },
    
    'budapest_eur': {
        'name': 'Budapest Bank EUR',
        'patterns': ['budapest.*eur'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'F122',
        'headers': {
            'date': 1,
            'type': 2,
            'payee': 4,
            'amount': 9,
            'currency': 10,
            'description': 11
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'skip_rows': 6,
        'has_header': True
    },
    
    'budapest_huf': {
        'name': 'Budapest Bank HUF',
        'patterns': ['budapest.*huf'],
        'file_type': 'excel',
        'encoding': 'utf-8',
        'sheet_name': 'F122',
        'headers': {
            'date': 1,
            'type': 2,
            'amount': 9,
            'currency': 10,
            'description': 11
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'skip_rows': 6,
        'has_header': True
    },
    
    'wio': {
        'name': 'WIO Bank',
        'patterns': ['wio', 'WIO'],
        'file_type': 'csv',
        'encoding': 'utf-8',
        'delimiter': ',',
        'headers': {
            'date': 'Date',
            'amount': 'Amount',
            'currency': 'Account currency',
            'description': 'Description',
            'payee': 'Recipient / Payer',
            'type': 'Transaction type'
        },
        'amount_sign': 'as_is',
        'date_format': '%Y-%m-%d',
        'has_header': True
    }
}


# Маппинг статей из описаний (для банков, где нет кодов)
ARTICLE_KEYWORDS = {
    '1.1.1.3 Арендная плата (счёт)': ['rent', 'apmaksa', 'rekins', 'invoice', 'īre', 'наем', 'money added from'],
    '1.1.1.1 Арендная плата (наличные)': ['cash', 'наличные'],
    '1.1.1.2 Поступления систем бронирования': ['airbnb', 'booking', 'бронирование'],
    '1.1.2.3 Компенсация по коммунальным расходам': ['utility', 'komunālie', 'коммунальные'],
    '1.2.8.1 Обслуживание объектов': ['maintenance', 'обслуживание', 'уборка', 'lifti'],
    '1.2.10 Коммунальные платежи': ['electricity', 'latvenergo', 'rigas udens', 'электричество', 'вода', 'газ'],
    '1.2.15.1 Зарплата': ['salary', 'darba alga', 'зарплата', 'algas izmaksa'],
    '1.2.17 РКО': ['fee', 'комиссия', 'bank charge', 'maintenance fee', 'service fee', 'monthly fee'],
    '1.2.9.1 Связь , интернет': ['tele', 'bite', 'tele2', 'интернет', 'связь', 'google one'],
    '1.1.4.1 Комиссия за продажу недвижимости': ['commission', 'комиссия', 'agency'],
    '1.2.10.1 Мусор': ['clean r', 'eco baltia', 'мусор'],
    '1.2.10.3 Вода': ['ūdens', 'вода', 'water'],
    '1.2.10.5 Электричество': ['electricity', 'latvenergo', 'электричество'],
    '1.2.2 Командировочные расходы': ['taxi', 'careem', 'uber', 'flydubai', 'parkonic', 'transport']
}


# Маппинг направлений
DIRECTION_KEYWORDS = {
    'Latvia': ['latvia', 'riga', 'рига', 'латвия', 'lv', 'caka', 'čaka', 'matisa', 'antonijas'],
    'Europe': ['europe', 'czech', 'чехия', 'budapest', 'prague', 'praha', 'karlovy', 'csob', 'unicredit'],
    'Nomiqa': ['nomiqa', 'dubai', 'дубай', 'baku', 'баку', 'uae', 'pasha', 'mashreq'],
    'East-Восток': ['east', 'восток', 'baku', 'azerbaijan', 'азербайджан'],
    'UK Estate': ['uk', 'estate', 'unelma']
}