# from __future__ import annotations

from pydantic import Field, AnyUrl
from typing import Optional, Union, Any, List

# dynamic registering
from .definitions import register_model, model_dependence

# basic definitions
from .definitions import Text


# base imports
from .creativework import CreativeWork


@register_model
class HyperTocEntry(CreativeWork):
    """A HyperToEntry is an item within a HyperToc which represents a hypertext table of contents for complex media objects such as VideoObject AudioObject The media object itself is indicated using associatedMedia Each section of interest within that content can be described with a HyperTocEntry with associated startOffset and endOffset When several entries are all from the same file associatedMedia is used on the overarching HyperTocEntry if the content has been split into multiple files they can be referenced using associatedMedia on each HyperTocEntry"""

    associatedMedia: Optional[
        Union["MediaObject", str, List["MediaObject"], List[str]]
    ] = Field(
        None,
        description="A media object that encodes this CreativeWork This property is a synonym for encoding",
    )
    tocContinuation: Optional[
        Union["HyperTocEntry", str, List["HyperTocEntry"], List[str]]
    ] = Field(
        None,
        description="A HyperTocEntry can have a tocContinuation indicated which is another HyperTocEntry that would be the default next item to play or render",
    )
    utterances: Optional[Union[str, List[str]]] = Field(
        None,
        description="Text of an utterances spoken words lyrics etc that occurs at a certain section of a media object represented as a HyperTocEntry",
    )


# parent dependences
model_dependence("HyperTocEntry", "CreativeWork")


# attribute dependences
model_dependence(
    "HyperTocEntry",
    "MediaObject",
)
