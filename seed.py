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
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing_count = db.query(Opportunity).count()
        if existing_count > 0:
            print(f"Seed skipped: opportunities table already has {existing_count} records.")
            return

        for item in SAMPLE_OPPORTUNITIES:
            db.add(Opportunity(**item))

        db.commit()
        print(f"Inserted {len(SAMPLE_OPPORTUNITIES)} sample opportunities.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
