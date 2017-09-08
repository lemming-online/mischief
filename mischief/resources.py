from mongoengine import Document, EmailField, StringField, BooleanField, BinaryField


class User(Document):
    # auth information
    email = EmailField(
        required=True,
        unique=True,
        min_length=3,  # .@.
        max_length=(64 + 1 + 255),  # local (64) + @ (1) + domain (255)
        regex='^.{64}@.{255}$',
    )
    password = StringField(
        required=True,
        min_length=10,
        # TODO: implement more OWASP password rules
    ),
    is_active = BooleanField(
        default=False,
    )
    # profile information
    first_name = StringField(
        required=True,
        min_length=1,
        max_length=64,
    )
    last_name = StringField(
        min_length=1,
        max_length=64,
    )


class Token(Document):
    token = BinaryField(required=True)
