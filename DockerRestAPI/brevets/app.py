import os

from flask import Flask, redirect, url_for, request, render_template, jsonify
from pymongo import MongoClient
import arrow

import acp_times

app = Flask(__name__)

client = MongoClient(os.environ.get("DB_HOST", "db"), 27017)
db = client.tododb

DISPLAY_FORMAT = "ddd M/D H:mm"

@app.route("/")
@app.route("/index")
def index():
    return render_template("calc.html")

@app.route("/display")
def display():
    items = sorted(db.controls.find({}, {"_id": 0}), key = lambda d: d["km"])
    for item in items:
        item["open"] = arrow.get(item["open"]).format(DISPLAY_FORMAT)
        item["close"] = arrow.get(item["close"]).format(DISPLAY_FORMAT)
    return render_template("todo.html", items = items)

@app.route("/_calc_times")
def _calc_times():
    km = request.args.get("km", type = float)
    brevet_dist = request.args.get("brevet_dist_km", 200, type=int)
    begin_date = request.args.get("begin_date", "2017-01-01")
    begin_time = request.args.get("begin_time", "00:00")
    if km is None:
        return jsonify(result = {"error": "Distance must be a number"})
    try:
        start = arrow.get("{} {}".format(begin_date, begin_time), "YYYY-MM-DD HH:mm")
        result = {
            "open": acp_times.open_time(km, brevet_dist, start.isoformat()),
            "close": acp_times.close_time(km, brevet_dist, start.isoformat()),
        }
    except (ValueError, arrow.parser.ParserError) as err:
        result = {"error": str(err)}
    return jsonify(result = result)

@app.route("/_submit", methods = ["POST"])
def _submit():
    
    data = request.get_json(silent = True)
    if not data:
        return error("Request must be JSON")
    controls = data.get("controls") or []
    if not controls:
        return error("There are no control times to submit")

    try:
        brevet_dist = int(data.get("brevet_dist_km"))
        start = arrow.get("{} {}".format(data.get("begin_date"), data.get("begin_time")),
                          "YYYY-MM-DD HH:mm").isoformat()
    except (TypeError, ValueError, arrow.parser.ParserError):
        return error("Invalid brevet distance or start date/time")

    docs = []
    seen = set()
    for c in controls:
        try:
            km = float(c.get("km"))
        except (TypeError, ValueError):
            return error("Control distance '{}' is not a number".format(c.get("km")))
        if km in seen:
            return error("Duplicate control at {} km".format(km))
        seen.add(km)
        try:
            docs.append({
                "brevet_dist_km": brevet_dist,
                "km": km,
                "location": (c.get("location") or "").strip(),
                "open": acp_times.open_time(km, brevet_dist, start),
                "close": acp_times.close_time(km, brevet_dist, start),
            })
        except ValueError as err:
            return error("{} km: {}".format(km, err))
    db.controls.delete_many({})
    db.controls.insert_many(docs)
    return jsonify(result = {"inserted": len(docs)})


def error(message, status = 400):
    return jsonify(result = {"error": message}), status


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 5000, debug = True)

