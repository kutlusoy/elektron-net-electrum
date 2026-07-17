# Elektron Electrum fork of Electrum, forked at upstream v4.8.0
# (spesmilo/electrum). Own version lineage deliberately does NOT continue
# upstream's numbering (see UPSTREAM_ELECTRUM_BASE_VERSION below for that) --
# instead it starts at 4.0.4 to match elektron-net's own version at the time
# of this initial release, marking the node version this wallet is known
# compatible with. The two lineages are expected to diverge from here; this
# is a starting marker, not a promise to keep the numbers in lockstep going
# forward. See elektron-net-repo-conventions.md and doc/elektron.md.
PRODUCT_NAME = 'Elektron Electrum'
UPSTREAM_ELECTRUM_BASE_VERSION = '4.8.0'
ELECTRUM_VERSION = '4.0.4'       # version of the client package

PROTOCOL_VERSION_MIN = '1.4'     # electrum protocol
PROTOCOL_VERSION_MAX = '1.6'

# The hash of the mnemonic seed must begin with this
SEED_PREFIX        = '01'      # Standard wallet
SEED_PREFIX_SW     = '100'     # Segwit wallet
SEED_PREFIX_2FA    = '101'     # Two-factor authentication
SEED_PREFIX_2FA_SW = '102'     # Two-factor auth, using segwit


def seed_prefix(seed_type):
    if seed_type == 'standard':
        return SEED_PREFIX
    elif seed_type == 'segwit':
        return SEED_PREFIX_SW
    elif seed_type == '2fa':
        return SEED_PREFIX_2FA
    elif seed_type == '2fa_segwit':
        return SEED_PREFIX_2FA_SW
    raise Exception(f"unknown seed_type: {seed_type!r}")
