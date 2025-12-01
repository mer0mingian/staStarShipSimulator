"""Main routes for the web application."""

from flask import Blueprint, render_template, redirect, url_for
from sta.database import get_session, EncounterRecord

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page - list encounters."""
    session = get_session()
    try:
        encounters = session.query(EncounterRecord).filter_by(is_active=True).all()
        return render_template("index.html", encounters=encounters)
    finally:
        session.close()
