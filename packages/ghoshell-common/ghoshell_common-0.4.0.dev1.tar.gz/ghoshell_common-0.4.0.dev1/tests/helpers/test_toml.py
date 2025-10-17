import tomlkit

from ghoshell_common.helpers.toml import from_pydantic_to_toml
from pydantic import BaseModel, Field
from typing import List, Dict


class Foo(BaseModel):
    """ this is foo"""
    a: str = Field("a", description="a description")


class Bar(BaseModel):
    """ this is bar"""
    b: str = Field("b", description="b description")
    foo: Foo = Field(description="foo description", default_factory=Foo)


def test_pydantic_and_toml():
    bar = Bar(b="z")

    doc = from_pydantic_to_toml(bar)

    value = tomlkit.dumps(doc)
    assert "z" in value


def test_deepseek_wrote_parser():
    class DatabaseConfig(BaseModel):
        """Database connection configuration"""
        host: str = Field(..., description="Database server hostname")
        port: int = Field(5432, description="Database server port")
        options: Dict[str, str] = Field(
            default_factory=dict,
            description="Additional connection options"
        )

    class AppConfig(BaseModel):
        """Main application configuration"""
        name: str = Field(..., description="Application name")
        version: str = Field("1.0.0", description="Application version")
        database: DatabaseConfig = Field(..., description="Database settings")
        features: List[str] = Field(
            default_factory=list,
            description="Enabled features"
        )

    # Create sample config
    db_config = DatabaseConfig(
        host="localhost",
        options={"timeout": "30s", "pool_size": "10"}
    )

    app_config = AppConfig(
        name="My App",
        database=db_config,
        features=["auth", "logging", "cache"]
    )

    # Convert to TOML
    toml_doc = from_pydantic_to_toml(app_config)
    assert 'features = ["auth", "logging", "cache"]' in tomlkit.dumps(toml_doc)
