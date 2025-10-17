class InvalidURLScheme(Exception):
    """
    Scheme detected in URL is not accepted
    """

    def __init__(self, msg="URL schema is not accepted", *args):
        super().__init__(msg, *args)
