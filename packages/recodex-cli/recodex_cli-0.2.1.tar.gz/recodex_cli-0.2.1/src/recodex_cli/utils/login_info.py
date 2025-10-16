class LoginInfo:
    api_url: str | None
    api_token: str | None
    username: str | None
    password: str | None
    use_credentials_prompt: bool
    use_token_prompt: bool

    def __init__(
        self,
        api_url: str | None,
        api_token: str | None,
        username: str | None,
        password: str | None,
        use_credentials_prompt: bool,
        use_token_prompt: bool,
    ) -> None:
        self.api_url = api_url
        self.api_token = api_token
        self.username = username
        self.password = password
        self.use_credentials_prompt = use_credentials_prompt
        self.use_token_prompt = use_token_prompt
