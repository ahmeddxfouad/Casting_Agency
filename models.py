import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def setup_db(app):
    """Configure the database for the Flask app.
    - In production/Heroku: reads DATABASE_URL.
    - In tests: if SQLALCHEMY_DATABASE_URI already set, do not override.
    """
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        database_path = os.environ.get("DATABASE_URL")
        if not database_path:
            raise RuntimeError("DATABASE_URL is not set and SQLALCHEMY_DATABASE_URI not provided")

        # Some platforms may still provide postgres://; SQLAlchemy prefers postgresql://
        if database_path.startswith("postgres://"):
            database_path = database_path.replace("postgres://", "postgresql://", 1)

        app.config["SQLALCHEMY_DATABASE_URI"] = database_path

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.app = app
    db.init_app(app)


actor_movie = db.Table(
    "actor_movie",
    db.Column("actor_id", db.Integer, db.ForeignKey("actors.id"), primary_key=True),
    db.Column("movie_id", db.Integer, db.ForeignKey("movies.id"), primary_key=True),
)


class Actor(db.Model):
    __tablename__ = "actors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)

    movies = db.relationship(
        "Movie",
        secondary=actor_movie,
        back_populates="actors",
        lazy="select",
    )

    def format(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "movies": [{"id": m.id, "title": m.title} for m in self.movies],
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    release_date = db.Column(db.Date, nullable=False)

    actors = db.relationship(
        "Actor",
        secondary=actor_movie,
        back_populates="movies",
        lazy="select",
    )

    def format(self):
        return {
            "id": self.id,
            "title": self.title,
            "release_date": self.release_date.isoformat() if self.release_date else None,
            "actors": [{"id": a.id, "name": a.name} for a in self.actors],
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
