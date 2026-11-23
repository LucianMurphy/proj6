# Laptop Service
import csv
import io
import os

import arrow
from flask import Flask, Response, request
from flask_restful import Resource, Api
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)

client = MongoClient(os.environ.get("DB_HOST", "db"), 27017)
db = client.tododb

TIME_FORMAT = "MM/DD/YYYY HH:mm"

KM_TO_MI = 0.621371

class ListTimes(Resource):
    fields = ("open", "close")
    sort_by = "km"
    def get(self, fmt = "json"):
        fmt = fmt.lower()
        if fmt not in ("json", "csv"):
            return {"error": "Unknown format '{}'. Use json or csv.".format(fmt)}, 400

        top = request.args.get("top")
        if top is not None:
            try:
                top = int(top)
            except ValueError:
                return {"error": "top must be a whole number"}, 400
            if top < 1:
                return {"error": "top must be at least 1"}, 400

        controls = self.load_controls(top)

        if fmt == "csv":
            return self.to_csv(controls)
        return self.to_json(controls)

    def load_controls(self, top):
        docs = list(db.controls.find({}, {"_id": 0}))
        if self.sort_by == "km":
            docs.sort(key = lambda d: d["km"])
        else:
            docs.sort(key = lambda d: arrow.get(d[self.sort_by]))
        if top is not None:
            docs = docs[:top]

        controls = []
        for d in docs:
            row = {
                "distance": d["brevet_dist_km"],
                "km": d["km"],
                "mi": round(d["km"] * KM_TO_MI),
                "location": d.get("location", ""),
            }
            for field in self.fields:
                row[field] = arrow.get(d[field]).format(TIME_FORMAT)
            controls.append(row)
        return controls

    def to_json(self, controls):
        brevets = {}
        for c in controls:
            brevet = brevets.setdefault(c["distance"],
                                        {"distance": c["distance"], "controls": []})
            control = {key: value for key, value in c.items() if key != "distance"}
            brevet["controls"].append(control)
        return {"brevets": list(brevets.values())}

    def to_csv(self, controls):
        columns = ["distance", "km", "mi", "location"] + list(self.fields)
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames = columns)
        writer.writeheader()
        writer.writerows(controls)
        return Response(output.getvalue(), mimetype = "text/csv")


class ListAll(ListTimes):
    fields = ("open", "close")
    sort_by = "km"


class ListOpenOnly(ListTimes):
    fields = ("open",)
    sort_by = "open"


class ListCloseOnly(ListTimes):
    fields = ("close",)
    sort_by = "close"


api.add_resource(ListAll, "/listAll", "/listAll/<string:fmt>")
api.add_resource(ListOpenOnly, "/listOpenOnly", "/listOpenOnly/<string:fmt>")
api.add_resource(ListCloseOnly, "/listCloseOnly", "/listCloseOnly/<string:fmt>")

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 80, debug = True)
