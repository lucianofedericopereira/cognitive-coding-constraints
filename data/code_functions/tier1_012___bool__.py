# Source : https://github.com/Textualize/rich/blob/master/rich/text.py (line 60)
# License: MIT
# Complexity: 1
# Tier   : tier1

def __bool__(self) -> bool:
    return self.end > self.start