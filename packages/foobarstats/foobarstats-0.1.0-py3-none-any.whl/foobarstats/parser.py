from datetime import datetime
from typing import IO, Generator
from xml.etree import ElementTree as ET

from foobarstats.models import TrackStat

def load(fp : IO[bytes]) -> Generator[TrackStat, None, None]:
    """loading objects using a generator from a file pointer, similar to the function json.load()"""
    for _, entry in ET.iterparse(fp, events=('end',)):
        if entry.tag == 'Entry':
            try:
                #if no filepath, the object is inconsistent
                item = entry[0]
                Path = item.attrib['Path']

                if (Subsong:=item.attrib.get('Subsong')) is not None:
                    Subsong = int(Subsong)

                if (Count:=entry.attrib.get('Count')) is not None:
                    Count = int(Count)

                if (Added:=entry.attrib.get('AddedFriendly')) is not None:
                    Added = datetime.strptime(Added, '%Y-%m-%d %H:%M:%S')

                if (FirstPlayed:=entry.attrib.get('FirstPlayedFriendly')) is not None:
                    FirstPlayed = datetime.strptime(FirstPlayed, '%Y-%m-%d %H:%M:%S')

                if (LastPlayed:=entry.attrib.get('LastPlayedFriendly')) is not None:
                    LastPlayed = datetime.strptime(LastPlayed, '%Y-%m-%d %H:%M:%S')

                yield TrackStat(Path=Path,
                                Subsong=Subsong,
                                Count=Count,
                                Added=Added,
                                FirstPlayed=FirstPlayed,
                                LastPlayed=LastPlayed)

            except (IndexError, KeyError):
                continue
            finally:
                entry.clear()
