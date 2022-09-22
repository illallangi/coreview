from flask import Blueprint, render_template

blueprint = Blueprint("frontend", __name__)


# Our index-page just shows a quick explanation. Check out the template
# "templates/index.html" documentation for more details.
@blueprint.route("/")
def index():
    return render_template("index.html")
