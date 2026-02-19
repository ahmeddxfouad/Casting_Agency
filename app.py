from datetime import date
from flask import Flask, jsonify, request
from flask_cors import CORS

from models import setup_db, db, Actor, Movie
from auth import requires_auth, AuthError


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    if test_config:
        app.config.update(test_config)

    setup_db(app)

    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,PATCH,DELETE,OPTIONS")
        return response

    @app.route("/", methods=["GET"])
    def health():
        return jsonify({"success": True, "message": "Casting Agency API is running"}), 200

    # -------------------- ACTORS --------------------
    @app.route("/actors", methods=["GET"])
    @requires_auth("get:actors")
    def get_actors(payload):
        actors = Actor.query.order_by(Actor.id).all()
        return jsonify(
            {"success": True, "actors": [a.format() for a in actors], "total_actors": len(actors)}
        ), 200

    @app.route("/actors", methods=["POST"])
    @requires_auth("post:actors")
    def create_actor(payload):
        body = request.get_json() or {}
        name = body.get("name")
        age = body.get("age")
        gender = body.get("gender")

        if not name or age is None or not gender:
            return jsonify(
                {"success": False, "error": 400, "message": "Missing required actor fields"}
            ), 400

        actor = Actor(name=name, age=int(age), gender=gender)
        actor.insert()
        return jsonify({"success": True, "created": actor.id, "actor": actor.format()}), 201

    @app.route("/actors/<int:actor_id>", methods=["PATCH"])
    @requires_auth("patch:actors")
    def update_actor(payload, actor_id):
        actor = Actor.query.get(actor_id)
        if not actor:
            return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404

        body = request.get_json() or {}
        if "name" in body:
            actor.name = body["name"]
        if "age" in body:
            actor.age = int(body["age"])
        if "gender" in body:
            actor.gender = body["gender"]

        actor.update()
        return jsonify({"success": True, "actor": actor.format()}), 200

    @app.route("/actors/<int:actor_id>", methods=["DELETE"])
    @requires_auth("delete:actors")
    def delete_actor(payload, actor_id):
        actor = Actor.query.get(actor_id)
        if not actor:
            return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404
        actor.delete()
        return jsonify({"success": True, "deleted": actor_id}), 200

    # -------------------- MOVIES --------------------
    @app.route("/movies", methods=["GET"])
    @requires_auth("get:movies")
    def get_movies(payload):
        movies = Movie.query.order_by(Movie.id).all()
        return jsonify(
            {"success": True, "movies": [m.format() for m in movies], "total_movies": len(movies)}
        ), 200

    @app.route("/movies", methods=["POST"])
    @requires_auth("post:movies")
    def create_movie(payload):
        body = request.get_json() or {}
        title = body.get("title")
        release_date_str = body.get("release_date")  # YYYY-MM-DD

        if not title or not release_date_str:
            return jsonify(
                {"success": False, "error": 400, "message": "Missing required movie fields"}
            ), 400

        try:
            y, m, d = [int(x) for x in release_date_str.split("-")]
            rd = date(y, m, d)
        except Exception:
            return jsonify({"success": False, "error": 400, "message": "release_date must be YYYY-MM-DD"}), 400

        movie = Movie(title=title, release_date=rd)
        movie.insert()
        return jsonify({"success": True, "created": movie.id, "movie": movie.format()}), 201

    @app.route("/movies/<int:movie_id>", methods=["PATCH"])
    @requires_auth("patch:movies")
    def update_movie(payload, movie_id):
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404

        body = request.get_json() or {}
        if "title" in body:
            movie.title = body["title"]
        if "release_date" in body:
            try:
                y, m, d = [int(x) for x in body["release_date"].split("-")]
                movie.release_date = date(y, m, d)
            except Exception:
                return jsonify({"success": False, "error": 400, "message": "release_date must be YYYY-MM-DD"}), 400

        movie.update()
        return jsonify({"success": True, "movie": movie.format()}), 200

    @app.route("/movies/<int:movie_id>", methods=["DELETE"])
    @requires_auth("delete:movies")
    def delete_movie(payload, movie_id):
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404
        movie.delete()
        return jsonify({"success": True, "deleted": movie_id}), 200

    # -------------------- ERROR HANDLERS --------------------
    @app.errorhandler(AuthError)
    def handle_auth_error(ex):
        return jsonify({"success": False, "error": ex.status_code, "message": ex.error}), ex.status_code

    @app.errorhandler(400)
    def bad_request(_):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400

    @app.errorhandler(401)
    def unauthorized(_):
        return jsonify({"success": False, "error": 401, "message": "unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(_):
        return jsonify({"success": False, "error": 403, "message": "forbidden"}), 403

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"success": False, "error": 404, "message": "resource not found"}), 404

    @app.errorhandler(422)
    def unprocessable(_):
        return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"success": False, "error": 500, "message": "internal server error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
