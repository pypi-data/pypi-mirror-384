import typing

import strawberry


def get_books():
    return [
        Book(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
        ),
        Book(
            title="Antony and Cleopatra",
            author="Ralph Waldo Emerson",
        ),
    ]


@strawberry.type
class Book:
    title: str
    author: str


@strawberry.type
class Query:
    books: typing.List[Book] = strawberry.field(resolver=get_books)


schema = strawberry.Schema(query=Query)
