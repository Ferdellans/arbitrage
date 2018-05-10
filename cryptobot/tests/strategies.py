import string

import hypothesis.strategies as st
from hypothesis_regex import regex

_version = regex('^\d{2}\.\d{2}\.\d{2}$')


ST_TIMESTAMP = ST_CLIENT_ID = st.integers(0, 2**32 - 1)
ST_TIMEZONE = st.integers(-12, 12)
ST_FAKE_CLEINT_ID = st.integers(2**32, 2**64 - 1)
ST_SCOPE = st.integers(-2**31, 2**31 - 1)
ST_WHITELIST_VERSION = st.integers(0, 2**32 - 1)
ST_CONFIG_VERSION = ST_CLIENT_VERSION = _version
ST_RANDOM_JSON = st.text() | st.recursive(
    st.none() | st.text(), lambda child: st.lists(child) | st.dictionaries(st.text(string.printable), child)
)

ST_TRANSACTION_OPENCLOSE = st.tuples(
    ST_CLIENT_ID,  # client_id
    st.uuids().map(str),   # transaction_id
    st.integers(min_value=0, max_value=1),  # transaction_type
    ST_TIMESTAMP,  # transaction_timestamp
    ST_TIMEZONE,  # transaction_timezone
    st.uuids().map(str),  # shift_id
    ST_TIMESTAMP,  # shift_timestamp
    ST_TIMEZONE,  # shift_timezone
    st.integers(0, 2**16 - 1),  # driver_id
    st.integers(0, 2**16 - 1),  # depot_id
    st.integers(0, 2**16 - 1),  # route_id
    st.integers(0, 2**16 - 1)  # exit_id
)

ST_TRANSACTION_EXECUTE = st.tuples(
    ST_CLIENT_ID,  # client_id
    st.uuids().map(str),   # transaction_id
    st.integers(min_value=0, max_value=1),  # transaction_type
    ST_TIMESTAMP,  # transaction_timestamp
    ST_TIMEZONE,  # transaction_timezone
    st.uuids().map(str),  # shift_id
    st.integers(-2**15, 2**15 - 1),  # medium_type
    st.text('ABCDEF0123456789', min_size=40, max_size=40),  # medium_id
    st.text('ABCDEF0123456789', min_size=4, max_size=4),  # medium_descriptor
    st.integers(-2**7, 2**7 - 1),  # zone_id
    st.integers(0, 1),  # client_mode
    st.integers(0, 2**16 - 1),  # depot_id
    st.integers(0, 2**16 - 1),  # route_id
    st.integers(0, 2**16 - 1)  # exit_id
)


ST_TRANSACTION_STARTSTOP = st.tuples(
    ST_CLIENT_ID,  # client_id
    st.uuids().map(str),   # transaction_id
    st.integers(min_value=0, max_value=1),  # transaction_type
    ST_TIMESTAMP,  # transaction_timestamp
    ST_TIMEZONE,  # transaction_timezone
    ST_TIMESTAMP,  # client_switch_timestamp
    ST_TIMEZONE,  # client_switch_timezone
    st.uuids().map(str),  # shift_id
)


ST_RANDOM_VALUE = st.text('ABCDEF0123456789', min_size=1, max_size=100) | st.integers() | st.uuids().map(str)
