from enum import Enum


class Locale(Enum):
    JP = "jp"
    EN = "en"
    TW = "tw"
    CN = "cn"
    KR = "kr"

    def __str__(self) -> str:
        return self.value