from datetime import datetime
import tzlocal

def now_local() -> datetime:
    return datetime.now(tz=tzlocal.get_localzone())
