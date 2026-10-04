def drop_trailing_slash_duplicates(endpoints, **kwargs):
    """
    Every route is registered with and without a trailing slash. Document each once (the
    slash-less form) so operation ids do not collide.
    """
    paths = {path for path, *_ in endpoints}
    return [
        endpoint for endpoint in endpoints
        if not (endpoint[0].endswith('/') and endpoint[0].rstrip('/') in paths)
    ]
