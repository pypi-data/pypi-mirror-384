# WikiTree API Python Client

A modern Python wrapper for the [WikiTree API](https://api.wikitree.com/).

This library provides authenticated and public access to WikiTree data, with clean method wrappers and consistent JSON responses.

## Features

- Simple `WikiTreeSession` class for all API interactions    
- Built-in login handling, cookie persistence, and error checking  
- Fully typed and documented methods  

## Installation

From GitHub (latest version):

```
pip install git+https://github.com/harrislineage/wikitree-api-python.git
```

## Quick Start

```
from wikitree_api import WikiTreeSession

wt = WikiTreeSession()
wt.authenticate(email="your_email@example.com", password="your_password")

data = wt.getProfile(key="Clemens-1", fields="Id,Name,FirstName,BirthDate,DeathDate")
print(data)
```

## API Coverage

| Action                          | Description                                 |
| ------------------------------- | ------------------------------------------- |
| `getProfile`                    | Retrieve a full person or space profile     |
| `getPerson`                     | Retrieve a minimal person profile           |
| `getPeople`                     | Retrieve multiple profiles                  |
| `getAncestors`                  | Get recursive ancestors                     |
| `getDescendants`                | Get recursive descendants                   |
| `getRelatives`                  | Parents, children, siblings, spouses        |
| `getConnections`                | Find relationship path between two profiles |
| `getWatchlist`                  | Get your trusted-list profiles              |
| `getCategories`                 | List categories linked to a profile         |
| `getBio`                        | Retrieve biography text only                |
| `getPhotos`                     | Retrieve profile photo metadata             |
| `getDNATestsByTestTaker`        | DNA tests assigned to a profile             |
| `getConnectedDNATestsByProfile` | DNA tests connected to a profile            |
| `getConnectedProfilesByDNATest` | Profiles connected by DNA test              |
| `searchPerson`                  | Search by name, date, and filters           |

## Requirements

- Python ≥ 3.8  
- `requests >= 2.28`  
- Optional for examples:  
  - `matplotlib >= 3.7`  
  - `wordcloud >= 1.9`

## Development

```
git clone https://github.com/harrislineage/wikitree-api-python.git
cd wikitree-api-python
pip install -e .
```