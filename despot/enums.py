import enum


class ItemType(enum.StrEnum):
    TRACK = "track"
    EPISODE = "episode"
    ALBUM = "album"
    ARTIST = "artist"
    SHOW = "show"

    @classmethod
    def human_names(cls, conn: str = "or") -> str:
        _item_type_names = [t.value for t in ItemType]
        return ", ".join(_item_type_names[:-1]) + f" {conn} {_item_type_names[-1]}"
