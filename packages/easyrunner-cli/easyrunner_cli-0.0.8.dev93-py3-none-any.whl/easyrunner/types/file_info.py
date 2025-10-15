import datetime
from dataclasses import dataclass


@dataclass
class FileInfo:
    block_count: int
    permissions: str
    hard_links: int
    owner: str
    group: str
    size: int
    last_modified_datetime: str
    fullname: str
    name: str
    extension: str

    @classmethod
    def from_ls_entry(cls, entry: list[str]) -> 'FileInfo':
        month = entry[6]
        day = entry[7]
        time_or_year = entry[8]
        fullname = entry[9]

        # strip the full path if it was returned (when glob is used)
        if "/" in fullname:
            fullname = fullname.split("/")[-1]

        # handle file name and extension extraction
        if fullname.startswith(".") and fullname.count(".") == 1:
            name = fullname
            extension = ""
        elif "." in fullname:
            name = ".".join(fullname.split(".")[:-1])
            extension = fullname.split(".")[-1]
        else:
            name = fullname
            extension = ""

        # handle last modified datetime
        try:
            if ":" in time_or_year:
                dt = datetime.datetime.strptime(f"{month} {day} {datetime.datetime.now().year} {time_or_year}", "%b %d %Y %H:%M")
            else:
                dt = datetime.datetime.strptime(f"{month} {day} {time_or_year}", "%b %d %Y")
            last_modified_datetime = dt.isoformat(sep=" ")
        except Exception:
            last_modified_datetime = f"{month} {day} {time_or_year}"
        return cls(
            block_count=int(entry[0]),
            permissions=entry[1],
            hard_links=int(entry[2]),
            owner=entry[3],
            group=entry[4],
            size=int(entry[5]),
            last_modified_datetime=last_modified_datetime,
            fullname=fullname,
            name=name,
            extension=extension,
        )
