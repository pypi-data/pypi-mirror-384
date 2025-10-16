from typing import Optional

from .langfuse_service import _LangfuseService


class LangfuseInitializer:
    @classmethod
    def initialize(
        cls,
        langfuse_public_key: str,
        langfuse_secret_key: str,
        langfuse_host: str,
        release: str,
        environment: str,
    ) -> None:
        """Initialize the Langfuse client singleton."""
        _LangfuseService.initialize(
            langfuse_public_key=langfuse_public_key,
            langfuse_secret_key=langfuse_secret_key,
            langfuse_host=langfuse_host,
            release=release,
            environment=environment,
        )

    @classmethod
    def get_instance(cls) -> Optional[_LangfuseService]:
        """Get the Langfuse client instance."""
        return _LangfuseService.get_instance()

    @classmethod
    def close(cls) -> None:
        """Close the Langfuse client instance."""
        _LangfuseService.close()
