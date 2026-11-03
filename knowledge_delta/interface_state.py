"""Keep displayed form tokens stable until an explicit refresh."""


def displayed_tokens(state, key, info, *, refresh=False):
    if refresh or key not in state:
        epoch = state[key]["epoch"] + 1 if key in state else 0
        state[key] = {"binding_hash": info["binding_hash"], "revision": info["revision"], "epoch": epoch}
    return state[key]


def tokens_changed(tokens, info):
    return tokens["binding_hash"] != info["binding_hash"] or tokens["revision"] != info["revision"]
