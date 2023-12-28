import enum


class ItemType(str, enum.Enum):
    TRACK = "track"
    EPISODE = "episode"
    ALBUM = "album"
    ARTIST = "artist"
    SHOW = "show"
    PLAYLIST = "playlist"

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def human_names(cls, conn: str = "or") -> str:
        _item_type_names = [t.value for t in ItemType]
        return ", ".join(_item_type_names[:-1]) + f" {conn} {_item_type_names[-1]}"
