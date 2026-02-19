import os
import unittest
import datetime

from app import create_app
from models import db, Actor, Movie


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


class CastingAgencyTestCase(unittest.TestCase):
    def setUp(self):
        self.assistant_token = os.environ.get("ASSISTANT_TOKEN", "")
        self.director_token = os.environ.get("DIRECTOR_TOKEN", "")
        self.producer_token = os.environ.get("PRODUCER_TOKEN", "")

        # Use in-memory SQLite for tests (fast, no external DB required)
        self.app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://"})
        self.client = self.app.test_client

        with self.app.app_context():
            db.create_all()

            # Seed one actor + one movie if empty
            if Actor.query.count() == 0:
                db.session.add(Actor(name="Seed Actor", age=30, gender="male"))
            if Movie.query.count() == 0:
                db.session.add(Movie(title="Seed Movie", release_date=datetime.date(2020, 1, 1)))

            db.session.commit()

            self.seed_actor_id = Actor.query.first().id
            self.seed_movie_id = Movie.query.first().id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ---------- ACTORS success + error ----------
    def test_get_actors_success(self):
        res = self.client().get("/actors", headers=auth_header(self.assistant_token))
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("actors", data)

    def test_get_actors_unauthorized_no_token(self):
        res = self.client().get("/actors")
        self.assertEqual(res.status_code, 401)

    def test_post_actor_success(self):
        payload = {"name": "New Actor", "age": 25, "gender": "female"}
        res = self.client().post("/actors", headers=auth_header(self.director_token), json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("created", data)

    def test_post_actor_error_missing_fields(self):
        payload = {"name": "Bad Actor"}
        res = self.client().post("/actors", headers=auth_header(self.director_token), json=payload)
        self.assertEqual(res.status_code, 400)

    def test_patch_actor_success(self):
        res = self.client().patch(
            f"/actors/{self.seed_actor_id}",
            headers=auth_header(self.director_token),
            json={"age": 99},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["actor"]["age"], 99)

    def test_patch_actor_error_not_found(self):
        res = self.client().patch(
            "/actors/999999", headers=auth_header(self.director_token), json={"age": 40}
        )
        self.assertEqual(res.status_code, 404)

    def test_delete_actor_success(self):
        # create one then delete it
        payload = {"name": "Delete Me", "age": 22, "gender": "male"}
        created = self.client().post(
            "/actors", headers=auth_header(self.director_token), json=payload
        ).get_json()["created"]

        res = self.client().delete(f"/actors/{created}", headers=auth_header(self.director_token))
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["deleted"], created)

    def test_delete_actor_error_not_found(self):
        res = self.client().delete("/actors/999999", headers=auth_header(self.director_token))
        self.assertEqual(res.status_code, 404)

    # ---------- MOVIES success + error ----------
    def test_get_movies_success(self):
        res = self.client().get("/movies", headers=auth_header(self.assistant_token))
        self.assertEqual(res.status_code, 200)

    def test_post_movie_success(self):
        payload = {"title": "New Movie", "release_date": "2021-05-06"}
        res = self.client().post("/movies", headers=auth_header(self.producer_token), json=payload)
        self.assertEqual(res.status_code, 201)

    def test_post_movie_error_bad_date(self):
        payload = {"title": "Bad Date Movie", "release_date": "06-05-2021"}
        res = self.client().post("/movies", headers=auth_header(self.producer_token), json=payload)
        self.assertEqual(res.status_code, 400)

    def test_patch_movie_success(self):
        res = self.client().patch(
            f"/movies/{self.seed_movie_id}",
            headers=auth_header(self.director_token),
            json={"title": "Updated Title"},
        )
        self.assertEqual(res.status_code, 200)

    def test_patch_movie_error_not_found(self):
        res = self.client().patch(
            "/movies/999999", headers=auth_header(self.director_token), json={"title": "X"}
        )
        self.assertEqual(res.status_code, 404)

    def test_delete_movie_success(self):
        payload = {"title": "Delete Movie", "release_date": "2022-01-01"}
        created = self.client().post(
            "/movies", headers=auth_header(self.producer_token), json=payload
        ).get_json()["created"]
        res = self.client().delete(f"/movies/{created}", headers=auth_header(self.producer_token))
        self.assertEqual(res.status_code, 200)

    def test_delete_movie_error_not_found(self):
        res = self.client().delete("/movies/999999", headers=auth_header(self.producer_token))
        self.assertEqual(res.status_code, 404)

    # ---------- RBAC: >=2 per role ----------
    def test_rbac_assistant_can_view(self):
        res = self.client().get("/actors", headers=auth_header(self.assistant_token))
        self.assertEqual(res.status_code, 200)

        res = self.client().get("/movies", headers=auth_header(self.assistant_token))
        self.assertEqual(res.status_code, 200)

    def test_rbac_assistant_cannot_post_actor(self):
        res = self.client().post(
            "/actors",
            headers=auth_header(self.assistant_token),
            json={"name": "Nope", "age": 20, "gender": "male"},
        )
        self.assertEqual(res.status_code, 403)

    def test_rbac_director_can_post_actor(self):
        res = self.client().post(
            "/actors",
            headers=auth_header(self.director_token),
            json={"name": "Allowed", "age": 20, "gender": "male"},
        )
        self.assertEqual(res.status_code, 201)

    def test_rbac_director_cannot_post_movie(self):
        res = self.client().post(
            "/movies",
            headers=auth_header(self.director_token),
            json={"title": "Nope", "release_date": "2020-01-01"},
        )
        self.assertEqual(res.status_code, 403)

    def test_rbac_producer_can_post_movie(self):
        res = self.client().post(
            "/movies",
            headers=auth_header(self.producer_token),
            json={"title": "Allowed", "release_date": "2020-01-01"},
        )
        self.assertEqual(res.status_code, 201)

    def test_rbac_producer_can_delete_movie(self):
        created = self.client().post(
            "/movies",
            headers=auth_header(self.producer_token),
            json={"title": "Temp", "release_date": "2020-01-01"},
        ).get_json()["created"]
        res = self.client().delete(f"/movies/{created}", headers=auth_header(self.producer_token))
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
