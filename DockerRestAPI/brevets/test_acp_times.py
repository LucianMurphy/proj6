import arrow
from nose.tools import assert_equal, raises
from acp_times import open_time, close_time
import app as brevet_app

START ="2017-01-01T00:00:00+00:00"

def at(hours, minutes):
    return arrow.get(START).shift(hours = hours, minutes = minutes).isoformat()

def test_start():
    assert_equal(open_time(0, 200, START), at(0, 0))
    assert_equal(close_time(0, 200, START), at(1, 0))

def test_single_dist():
    assert_equal(open_time(100, 200, START), at(2, 56))
    assert_equal(close_time(100, 200, START), at(6, 40))

def test_early_control():
    assert_equal(close_time(40, 200, START), at(3, 0))
    assert_equal(close_time(60, 200, START), at(4, 0))
    assert_equal(open_time(60, 200, START), at(1, 46))

def test_multiple_dists_open():
    assert_equal(open_time(350, 600, START), at(10, 34))
    assert_equal(close_time(350, 600, START), at(23, 20))

def test_long_brevet():
    assert_equal(open_time(890, 1000, START), at(29, 9))
    assert_equal(close_time(890, 1000, START), at(65, 23))

def test_finish_fixed_close_times():
    assert_equal(close_time(200, 200, START), at(13, 30))
    assert_equal(close_time(400, 400, START), at(27, 0))
    assert_equal(close_time(1000, 1000, START), at(75, 0))

def test_control_past_finish():
    assert_equal(open_time(205, 200, START), open_time(200, 200, START))
    assert_equal(close_time(205, 200, START), at(13, 30))

@raises(ValueError)
def test_invalid_brevet_distance():
    open_time(100, 250, START)
 
 
@raises(ValueError)
def test_control_too_far_past_finish():
    close_time(300, 200, START)

#tests for the buttons

class FakeCollection:
    def __init__(self):
        self.docs = []

    def delete_many(self, query):
        self.docs = []

    def insert_many(self, docs):
        self.docs.extend(dict(d) for d in docs)

    def find(self, query = None, projection = None):
        return [dict(d) for d in self.docs]


class FakeDB:
    def __init__(self):
        self.controls = FakeCollection()


def client():
    brevet_app.db = FakeDB()
    brevet_app.app.config["TESTING"] = True
    return brevet_app.app.test_client()


def submit(c, controls, brevet=200):
    return c.post("/_submit", json = {
        "brevet_dist_km": brevet, "begin_date": "2017-01-01",
        "begin_time": "00:00", "controls": controls})


def test_submit_empty_is_error():
    c = client()
    resp = submit(c, [])
    assert_equal(resp.status_code, 400)
    assert "no control times" in resp.get_json()["result"]["error"]
    assert_equal(brevet_app.db.controls.docs, [])


def test_submit_bad_distance_is_error():
    c = client()
    resp = submit(c, [{"km": 500}])          # far past a 200 km brevet
    assert_equal(resp.status_code, 400)
    assert_equal(brevet_app.db.controls.docs, [])


def test_submit_stores_times():
    c = client()
    resp = submit(c, [{"km": 100, "location": "A"}, {"km": 200}])
    assert_equal(resp.status_code, 200)
    assert_equal(resp.get_json()["result"]["inserted"], 2)
    docs = brevet_app.db.controls.docs
    assert_equal(docs[0]["open"], at(2, 56))
    assert_equal(docs[1]["close"], at(13, 30))


def test_display_shows_submitted_times():
    c = client()
    submit(c, [{"km": 200}, {"km": 100, "location": "Checkpoint A"}])
    page = c.get("/display").get_data(as_text = True)
    assert "Checkpoint A" in page
    assert "Sun 1/1 2:56" in page            # 100 km open time
    assert page.index("100.0") < page.index("200.0")   # sorted by km


def test_display_empty_database():
    c = client()
    page = c.get("/display").get_data(as_text = True)
    assert "No controle times" in page