"""
Seed sample opportunities into the database.

Local:  python seed.py
Production (one-time demo): run once after deploy with DATABASE_URL pointing at the
persistent SQLite file, or use the Render shell. Skip this if you will add real
opportunities through the admin UI instead.
"""

from database import Base, SessionLocal, engine
from models import Opportunity


SAMPLE_OPPORTUNITIES = [
    {
        "title": "Robotics Club",
        "description": "Build robots and learn engineering with peers.",
        "type": "club",
        "region_name": "Tashkent",
    },
    {
        "title": "Startup Launch Lab",
        "description": "Turn ideas into small startup projects.",
        "type": "project",
        "region_name": "Samarkand",
    },
    {
        "title": "Public Speaking Workshop",
        "description": "Practice confident speaking and presentation skills.",
        "type": "workshop",
        "region_name": "Bukhara",
    },
    {
        "title": "Design Club",
        "description": "Explore visual design, branding, and teamwork.",
        "type": "club",
        "region_name": "Fergana",
    },
    {
        "title": "Community App Project",
        "description": "Build a simple digital product for local communities.",
        "type": "project",
        "region_name": "Namangan",
    },
    {
        "title": "Career Readiness Workshop",
        "description": "Learn CV writing, interviews, and communication.",
        "type": "workshop",
        "region_name": "Tashkent",
    },
    {
        "title": "English Debate Club",
        "description": "Discuss ideas and improve spoken English.",
        "type": "club",
        "region_name": "Samarkand",
    },
    {
        "title": "Youth Media Project",
        "description": "Create social media and storytelling campaigns.",
        "type": "project",
        "region_name": "Bukhara",
    },
    {
        "title": "Leadership Workshop",
        "description": "Build leadership habits through practical exercises.",
        "type": "workshop",
        "region_name": "Fergana",
    },
    {
        "title": "Tech Explorers Club",
        "description": "Meet others interested in code, AI, and startups.",
        "type": "club",
        "region_name": "Namangan",
    },
    {
        "title": "Campus Chess Club",
        "description": "Friendly weekly chess sessions, mini tournaments, and strategy practice.",
        "type": "club",
        "region_name": "Nukus",
    },
    {
        "title": "Green Future Club",
        "description": "Plan eco campaigns, clean-up days, and student sustainability ideas.",
        "type": "club",
        "region_name": "Khodjeyli",
    },
    {
        "title": "Creative Coding Club",
        "description": "Build fun websites, small games, and digital experiments together.",
        "type": "club",
        "region_name": "Beruniy",
    },
    {
        "title": "Volunteer Action Club",
        "description": "Coordinate student volunteering for schools, parks, and local events.",
        "type": "club",
        "region_name": "Turtkul",
    },
    {
        "title": "Local History Story Lab",
        "description": "Collect stories, photos, and interviews about community history.",
        "type": "project",
        "region_name": "Nukus",
    },
    {
        "title": "Student Help Desk Project",
        "description": "Design a simple peer-to-peer support system for campus questions.",
        "type": "project",
        "region_name": "Khodjeyli",
    },
    {
        "title": "Mini Startup Sprint",
        "description": "Launch a tiny student product in four weeks with a small team.",
        "type": "project",
        "region_name": "Beruniy",
    },
    {
        "title": "Youth Podcast Project",
        "description": "Record short podcast episodes about education, careers, and student life.",
        "type": "project",
        "region_name": "Turtkul",
    },
]


def seed_sample_opportunities() -> int:
    db = SessionLocal()
    try:
        existing_titles = {title for (title,) in db.query(Opportunity.title).all()}
        inserted_count = 0
        for item in SAMPLE_OPPORTUNITIES:
            if item["title"] in existing_titles:
                continue
            db.add(Opportunity(**item))
            inserted_count += 1

        db.commit()
        return inserted_count
    finally:
        db.close()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    inserted_count = seed_sample_opportunities()
    print(f"Inserted {inserted_count} sample opportunities.")


if __name__ == "__main__":
    main()
