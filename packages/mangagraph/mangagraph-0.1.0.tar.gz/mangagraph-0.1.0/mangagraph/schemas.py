import dataclasses
from typing import Dict, Any

@dataclasses.dataclass
class Cover:
    thumbnail: str
    default: str
    md: str

@dataclasses.dataclass
class Rating:
    average: float
    votes: int
    raw_average: str
    raw_votes: str

@dataclasses.dataclass
class SearchData:
    id: int
    name: str
    rus_name: str
    eng_name: str
    slug: str
    slug_url: str
    cover: Cover
    age_restriction: str
    type: str
    release_year: str
    rating: Rating
    status: str
    
    @classmethod
    def de_json(cls, data: Dict[str, Any]) -> 'SearchData':
        """Create SearchData instance from API response dictionary."""
        cover_data = data.get('cover', {})
        cover = Cover(
            thumbnail=cover_data.get('thumbnail', ''),
            default=cover_data.get('default', ''),
            md=cover_data.get('md', '')
        )
        
        rating_data = data.get('rating', {})
        rating = Rating(
            average=float(rating_data.get('average', 0)),
            votes=int(rating_data.get('votes', 0)),
            raw_average=rating_data.get('averageFormated', 'N/A'),
            raw_votes=rating_data.get('votesFormated', 'N/A')
        )
        
        return cls(
            id=data.get('id', 0),
            name=data.get('name', 'Unknown'),
            rus_name=data.get('rus_name', ''),
            eng_name=data.get('eng_name', ''),
            slug=data.get('slug', ''),
            slug_url=data.get('slug_url', ''),
            cover=cover,
            age_restriction=data.get('ageRestriction', {}).get('label', 'Unknown'),
            type=data.get('type', {}).get('label', 'Unknown'),
            release_year=data.get('releaseDate', 'Unknown'),
            rating=rating,
            status=data.get('status', {}).get('label', 'Unknown')
        )