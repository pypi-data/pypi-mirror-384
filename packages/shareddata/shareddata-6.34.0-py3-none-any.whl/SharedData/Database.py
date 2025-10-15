DATABASE_PKEYS = {
    'Symbols':          ['symbol'],
        
    'TimeSeries':       ['date'],
    'MarketData':       ['date', 'symbol'],
    'Relationships':    ['date', 'symbol', 'symbol1'],
    'Options':          ['date', 'symbol', 'expiry', 'strike', 'callput'],
    
    'Tags':             ['date', 'tag', 'symbol'],
    'Text':             ['date', 'hash'],
    
    'Accounts':         ['portfolio'],
    'Portfolios':       ['date', 'portfolio'],
    'Signals':          ['date', 'portfolio', 'symbol'],
    'Risk':             ['date', 'portfolio', 'symbol'],
    'Positions':        ['date', 'portfolio', 'symbol'],
    'Requests':         ['date', 'portfolio', 'requestid'],
    'Orders':           ['date', 'portfolio', 'clordid'],
    'Trades':           ['date', 'portfolio', 'symbol', 'tradeid']
}

STRING_FIELDS = ['symbol', 'tag', 'portfolio', 'requestid', 'clordid', 'tradeid', 'hash']

PERIODS = ['D1', 'M15', 'M1', 'RT']

# Index schema configurations for JIT-compiled functions
# Each entry defines how indices are created for a specific primary key combination
INDEX_SCHEMAS = {
    # Simple single-field keys
    'symbol': {
        'fields': ['symbol'],
        'secondary_indices': []
    },
    'date': {
        'fields': ['date'],
        'secondary_indices': []
    },
    'portfolio': {
        'fields': ['portfolio'],
        'secondary_indices': []
    },
    'hash': {
        'fields': ['hash'],
        'secondary_indices': []
    },
    
    # Two-field composite keys
    'date_symbol': {
        'fields': ['date', 'symbol'],
        'secondary_indices': ['symbol']
    },
    'date_portfolio': {
        'fields': ['date', 'portfolio'],
        'secondary_indices': ['portfolio']
    },
    'date_tag': {
        'fields': ['date', 'tag'],
        'secondary_indices': ['tag']
    },
    'date_hash': {
        'fields': ['date', 'hash'],
        'secondary_indices': []
    },
    
    # Three-field composite keys
    'date_symbol_symbol1': {
        'fields': ['date', 'symbol', 'symbol1'],
        'secondary_indices': ['symbol'],
        'custom_hash': True  # Special: optimize when symbol == symbol1
    },
    'date_tag_symbol': {
        'fields': ['date', 'tag', 'symbol'],
        'secondary_indices': ['tag', 'symbol']
    },
    'date_portfolio_symbol': {
        'fields': ['date', 'portfolio', 'symbol'],
        'secondary_indices': ['portfolio', 'symbol']
    },
    'date_portfolio_requestid': {
        'fields': ['date', 'portfolio', 'requestid'],
        'secondary_indices': ['portfolio']
    },
    'date_portfolio_clordid': {
        'fields': ['date', 'portfolio', 'clordid'],
        'secondary_indices': ['portfolio']
    },
    
    # Four-field composite keys
    'date_portfolio_symbol_tradeid': {
        'fields': ['date', 'portfolio', 'symbol', 'tradeid'],
        'secondary_indices': ['portfolio', 'symbol']
    },
    
    # Five-field composite key (Options)
    'date_symbol_expiry_strike_callput': {
        'fields': ['date', 'symbol', 'expiry', 'strike', 'callput'],
        'secondary_indices': ['symbol'],
        'numeric_fields': ['expiry', 'strike']  # Non-string fields for hash computation
    },
}

# Helper to auto-generate schema key from field list
def get_schema_key(fields):
    """
    Convert a list of field names to the corresponding schema key.
    
    Args:
        fields: List of field names (e.g., ['date', 'symbol'])
    
    Returns:
        Schema key string (e.g., 'date_symbol')
    
    Example:
        >>> get_schema_key(['date', 'portfolio', 'symbol'])
        'date_portfolio_symbol'
    """
    return '_'.join(fields)

# Validate that all DATABASE_PKEYS have corresponding schemas
def validate_schemas():
    """Ensure all database primary keys have corresponding index schemas."""
    missing = []
    for db_name, fields in DATABASE_PKEYS.items():
        schema_key = get_schema_key(fields)
        if schema_key not in INDEX_SCHEMAS:
            missing.append((db_name, schema_key, fields))
    
    if missing:
        raise ValueError(
            f"Missing index schemas for databases:\n" +
            "\n".join(f"  {db}: {key} (fields: {fields})" for db, key, fields in missing)
        )

# Run validation at import time
validate_schemas()