# Artist.py

from mongoengine import (
    DynamicDocument,
    EmbeddedDocument,
    StringField,
    ListField,
    EmbeddedDocumentField,
    IntField,
    FloatField,
    BooleanField
)
from models.BaseSchema import BaseSchema

# -----------------------
# Embedded Document Classes
# -----------------------

class Tag(EmbeddedDocument):
    """
    Represents a Tag associated with an Artist.
    """
    name = StringField()
    count = IntField()


class Genre(EmbeddedDocument):
    """
    Represents a Genre associated with an Artist.
    """
    name = StringField()
    count = IntField()
    disambiguation = StringField()
    id = StringField()


class LifeSpan(EmbeddedDocument):
    """
    Represents the LifeSpan of an Artist.
    """
    begin = StringField()  # Alternatively, use DateTimeField if dates are available
    end = StringField()  # Alternatively, use DateTimeField
    ended = BooleanField(default=False)


class Alias(EmbeddedDocument):
    """
    Represents an Alias for an Artist.
    """
    name = StringField()
    locale = StringField()
    type = StringField()
    primary = BooleanField(default=False)


class Relation(EmbeddedDocument):
    """
    Represents a Relation of an Artist to another entity.
    """
    type = StringField()
    target_type = StringField(db_field='target-type')

class Ipi(EmbeddedDocument):
    """
    Represents an IPI (Interested Parties Information) identifier.
    """
    ipi = StringField()


class Isni(EmbeddedDocument):
    """
    Represents an ISNI (International Standard Name Identifier).
    """
    isni = StringField()

class Area(EmbeddedDocument):
    """
    Represents an Area (geographical or otherwise) associated with an Artist.
    """
    id = StringField()
    name = StringField()
    sort_name = StringField(db_field='sort-name')

class Rating(EmbeddedDocument):
    """
    Represents the Rating of an Artist.
    """
    value = FloatField(default=0.0)
    votes_count = IntField(default=0, db_field='votes-count')

# -----------------------
# Main Artist Document
# -----------------------

class Artist(BaseSchema, DynamicDocument):
    """
    Represents an Artist with various attributes and relations.
    """

    # Basic Fields
    #type           = StringField(choices=["Group", "Person"])
    #country        = StringField()
    #annotation     = StringField()
    #sort_name      = StringField(db_field='sort-name')
    id             = StringField()
    #gender         = StringField()
    #disambiguation = StringField(default="")
    
    # Embedded Documents and Lists
    tags       = ListField(EmbeddedDocumentField(Tag), default=[])
    genres     = ListField(EmbeddedDocumentField(Genre), default=[])
    #life_span  = EmbeddedDocumentField(LifeSpan, db_field='life-span')
    #aliases    = ListField(EmbeddedDocumentField(Alias), default=[])
    #relations  = ListField(EmbeddedDocumentField(Relation), default=[])
    #ipis       = ListField(EmbeddedDocumentField(Ipi), default=[])
    #isnis      = ListField(EmbeddedDocumentField(Isni), default=[])
    #begin_area = EmbeddedDocumentField(Area, db_field='begin-area')
    #end_area   = EmbeddedDocumentField(Area, db_field='end-area')
    rating     = EmbeddedDocumentField(Rating)
    #area       = EmbeddedDocumentField(Area)

    # Additional Fields
    # Add other fields as necessary based on your data

    meta = {
        'collection': 'artists',
        'indexes': [
            {'fields': ['genres.name']}
        ]
    }
