"""

Constants for Toy API

Contains all constant values used throughout the application including dummy data
and configuration defaults.

License: BSD 3-Clause

"""

#
# IMPORTS
#
from typing import Any, Dict, List


#
# CONSTANTS
#
DEFAULT_CONFIG_PATH: str = "config/v1.yaml"
DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 8000

# Dummy data for user generation
FIRST_NAMES: List[str] = [
    # English/Western names
    "Alice", "Charlie", "Diana", "Edward", "George", "Helen", "Luna", "Oscar",
    # Arabic/Middle Eastern names
    "Amara", "Hassan", "Layla", "Omar", "Zara", "Khalil", "Nadia", "Tariq",
    # East Asian names
    "Akiko", "Chen", "Hiroshi", "Li", "Mei", "Taro", "Yuki", "Zhang",
    # South Asian names
    "Ananya", "Dev", "Kavya", "Raj", "Priya", "Arjun", "Sita", "Vikram",
    # Parsi names
    "Cyrus", "Delna", "Farhad", "Golnar", "Hormuz", "Jasmin", "Keki", "Roshan",
    # African names
    "Amara", "Koffi", "Nia", "Olumide", "Thandiwe", "Uzoma", "Zuri", "Kwame",
    # Latin American names
    "Carlos", "Elena", "Diego", "Isabella", "Miguel", "Sofia", "Alejandro", "Camila",
    # Nordic names
    "Erik", "Astrid", "Magnus", "Ingrid", "Lars", "Freya", "Nils", "Sigrid",
    # Slavic names
    "Dimitri", "Katya", "Pavel", "Anya", "Sergei", "Natasha", "Viktor", "Olga",
    # Silly names
    "Zigzag", "Sparkle", "Moonbeam", "Pickle", "Bubblegum", "Stardust", "Rainbow", "Fizzbuzz"
]

LAST_NAMES: List[str] = [
    # English/Western surnames
    "Anderson", "Brown", "Davis", "Evans", "Foster", "Harris", "Miller", "Parker",
    # Arabic/Middle Eastern surnames
    "Al-Rashid", "Benali", "El-Amin", "Farouk", "Hakim", "Ibrahim", "Khoury", "Mansour",
    # East Asian surnames
    "Chen", "Kim", "Takahashi", "Wang", "Yamamoto", "Zhou", "Tanaka", "Liu",
    # South Asian surnames
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Joshi", "Mehta", "Reddy",
    # Parsi surnames
    "Mistry", "Wadia", "Tata", "Modi", "Barucha", "Daruwalla", "Sethna", "Cama",
    # African surnames
    "Adebayo", "Mwangi", "Okafor", "Sithole", "Traore", "Benabou", "Diouf", "Kone",
    # Latin American surnames
    "Garcia", "Rodriguez", "Martinez", "Lopez", "Gonzalez", "Hernandez", "Silva", "Santos",
    # Nordic surnames
    "Andersen", "Johansson", "Nielsen", "Larsson", "Eriksson", "Petersen", "Hansen", "Berg",
    # Slavic surnames
    "Petrov", "Volkov", "Smirnov", "Ivanov", "Kozlov", "Sokolov", "Popov", "Lebedev",
    # Silly surnames
    "Gigglebottom", "Snugglepuff", "Wibblewobble", "Twinkletoes", "Bumblebee", "Sparklehorn", "Jellybeans", "Moonwalker"
]

# Dummy data for post generation
POST_TITLES: List[str] = [
    "Introduction to APIs", "Building Scalable Systems", "Database Design Patterns",
    "Security Best Practices", "Testing Strategies", "DevOps Fundamentals",
    "Code Review Guidelines", "Performance Optimization", "Documentation Standards"
]

# Locations for user profiles
LOCATIONS: List[str] = [
    "San Francisco", "New York", "London", "Tokyo", "Berlin", "Toronto", "Sydney",
    "Amsterdam", "Barcelona", "Singapore", "Austin", "Seattle", "Portland"
]

# Permissions for user access control
PERMISSIONS: List[str] = [
    "read", "write", "delete", "admin", "create", "update", "execute", "manage"
]

# Themes for user settings
THEMES: List[str] = ["light", "dark", "auto"]

# Languages for user settings
LANGUAGES: List[str] = ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh"]

# Tags for posts
POST_TAGS: List[str] = [
    "tech", "api", "tutorial", "guide", "tips", "best-practices", "development",
    "programming", "web", "mobile", "database", "security", "performance"
]

# Recent activities for admin dashboard
ADMIN_ACTIVITIES: List[str] = [
    "User login", "Data backup", "System update", "Security scan",
    "Cache refresh", "Database maintenance", "Log rotation", "Config update"
]

# Job titles for user bios
JOBS: List[str] = [
    "Rainbow Chaser", "Professional Cloud Watcher", "Unicorn Trainer", "Dragon Whisperer",
    "Bubble Wrap Popper", "Professional Daydreamer", "Sock Puppet Engineer", "Chief Giggle Officer",
    "Ninja Cat Herder", "Professional Nap Taker", "Jelly Bean Sommelier", "Moonbeam Collector",
    "Professional Time Traveler", "Chief Fun Officer", "Butterfly Migration Coordinator",
    "Professional Ice Cream Tester", "Wind Direction Consultant", "Professional Hugger",
    "Chief Happiness Officer", "Puddle Jump Instructor", "Professional Tickle Fighter",
    "Invisible Friend Coordinator", "Chief Cookie Monster", "Professional Laughing Expert",
    "Snowflake Designer", "Professional High-Five Giver", "Chief Smile Spreader",
    "Professional Thumb Wrestler", "Shooting Star Catcher", "Chief Silliness Officer",
    "Professional Belly Laugh Technician", "Magic Carpet Test Pilot", "Chief Giggling Scientist",
    "Professional Marshmallow Architect", "Rainbow Painting Specialist", "Chief Wonder Officer"
]