"""
fields_reference.py
Comprehensive list of field names accepted by WikiTree API actions.
Copyright (c) 2025 Steven Harris
License: GPL-3.0-only
"""

# ------------------------------------------------------------
# Common fields used across most actions
# ------------------------------------------------------------
COMMON_FIELDS = [
    "Id", "PageId", "Name", "IsPerson", "FirstName", "MiddleName",
    "MiddleInitial", "LastNameAtBirth", "LastNameCurrent", "Nicknames",
    "LastNameOther", "RealName", "Prefix", "Suffix", "BirthDate",
    "DeathDate", "BirthLocation", "DeathLocation", "Gender",
    "Photo", "IsLiving", "Created", "Touched", "Privacy",
    "Manager", "Creator", "Father", "Mother", "Parents", "Children",
    "Spouses", "Siblings", "HasChildren", "NoChildren", "IsRedirect",
    "DataStatus", "PhotoData", "Connected", "Bio", "IsMember",
    "EditCount", "Derived.ShortName", "Derived.BirthName",
    "Derived.BirthNamePrivate", "Derived.LongName",
    "Derived.LongNamePrivate"
]

# ------------------------------------------------------------
# Additional relational and optional structures
# ------------------------------------------------------------
RELATIVE_FIELDS = ["Parents", "Children", "Spouses", "Siblings"]
SPECIAL_FIELDS = ["Managers", "TrustedList", "Categories", "Templates"]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def list_fields() -> str:
    """Return a comma-delimited list of common field names."""
    return ", ".join(COMMON_FIELDS)

def describe_fields() -> str:
    """Return a formatted multiline description of available fields."""
    return """
Common Field Descriptions
-------------------------
Id                  Integer user/person ID of the profile
PageId              Internal page ID (used for getProfile)
Name                WikiTree ID (spaces replaced by underscores)
IsPerson            1 for person profiles, 0 for free-space pages
FirstName           First name
MiddleName          Middle name
MiddleInitial       First letter of middle name
LastNameAtBirth     Birth surname
LastNameCurrent     Current surname
Nicknames           Nicknames
LastNameOther       Other surnames
RealName            Preferred first name
Prefix              Name prefix
Suffix              Name suffix
BirthDate           Date of birth (YYYY-MM-DD, may include zeros)
DeathDate           Date of death (YYYY-MM-DD, may include zeros)
BirthLocation       Birth location
DeathLocation       Death location
Gender              "Male" or "Female"
Photo               Base filename of the primary photo
IsLiving            1 if living, 0 if deceased
Created             Profile creation timestamp (YYYYMMDDHHMMSS)
Touched             Last modification timestamp (YYYYMMDDHHMMSS)
Privacy             Integer representing privacy level
Manager             User ID of profile manager
Creator             User ID of profile creator
Father / Mother     Parent user IDs
HasChildren         1 if profile has at least one child
NoChildren          1 if "No more children" box is checked
IsRedirect          1 if profile redirects to another
DataStatus          Array of "guess", "certain", etc.
PhotoData           Dictionary with image details
Connected           1 if connected to global tree
Bio                 Biography text
IsMember            1 if profile belongs to an active member
EditCount           Number of edits/contributions

Derived Fields (accessible via "Derived.FieldName")
---------------------------------------------------
ShortName           RealName (LastNameAtBirth) LastNameCurrent Suffix
BirthName           FirstName MiddleName
BirthNamePrivate    RealName LastNameAtBirth Suffix
LongName            FirstName MiddleName (LastNameAtBirth) LastNameCurrent Suffix
LongNamePrivate     RealName MiddleInitial (LastNameAtBirth) LastNameCurrent Suffix

Relative Fields
---------------
Parents, Children, Spouses, Siblings

Optional Collections
--------------------
Managers / TrustedList — Lists of profiles with Id, PageId, and Name.
Categories — Array of connected category titles.
Templates — Array of template data with 'name' and 'params'.
""".strip()
