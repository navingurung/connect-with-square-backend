from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Square Samurai Test Backend"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://square_samurai_test_user:xkbujqFOTshuQPkcAtLCPymhTwWKLy5Z@dpg-d83cg00js32c73ca5qa0-a/square_samurai_test"

    SQUARE_ENVIRONMENT: str = "sandbox"
    SQUARE_BASE_URL: str = "https://connect.squareupsandbox.com"
    SQUARE_APPLICATION_ID: str
    SQUARE_APPLICATION_SECRET: str
    SQUARE_REDIRECT_URI: str = "https://connect-with-square-backend.onrender.com/api/square/oauth/callback"
    SQUARE_VERSION: str = "2026-01-22"
    SQUARE_SCOPES: str = "MERCHANT_PROFILE_READ PAYMENTS_READ ORDERS_READ"

    FRONTEND_URL: str = "https://connect-with-square-frontend.onrender.com/"

    @property
    def square_scopes_list(self) -> list[str]:
        return self.SQUARE_SCOPES.split()


settings = Settings() # type: ignore