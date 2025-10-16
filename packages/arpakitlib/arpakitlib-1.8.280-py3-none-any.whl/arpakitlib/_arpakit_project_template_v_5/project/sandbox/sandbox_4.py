import asyncio

from arpakitlib.ar_pydantic_schema_from_sqlalchemy_model import _get_property_name_to_type_from_model_class
from project.sqlalchemy_db_.sqlalchemy_model import UserDBM


def __sandbox():
    res = _get_property_name_to_type_from_model_class(
        model_class=UserDBM
    )
    for a,b in res.items():
        print(a, b)


async def __async_sandbox():
    pass


if __name__ == '__main__':
    __sandbox()
    asyncio.run(__async_sandbox())
