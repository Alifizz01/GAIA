"""SOC accuracy against electrochemical truth, and the Studio REST API."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from gaia.soc_benchmark import run_benchmark


@pytest.mark.parametrize("chemistry, ekf_limit", [("NMC", 3.0), ("LFP", 3.5), ("NCA", 8.0)])
def test_kalman_filters_beat_coulomb_counting_against_pybamm(chemistry, ekf_limit):
    """Documents the accuracy GAIA claims in its README; fails if it regresses."""
    r = run_benchmark(chemistry)
    rmse = r["rmse_after_10min"]
    assert rmse["COULOMB_COUNTING"] > 15            # a 20 % wrong start never goes away
    assert rmse["KALMAN_FILTER"] < ekf_limit
    assert rmse["AEKF"] < ekf_limit


@pytest.fixture(scope="module")
def http():
    from gaia.server import make_server
    srv = make_server(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def post(name, body=None, headers=None):
        h = {"Content-Type": "application/json", **(headers or {})}
        req = urllib.request.Request(f"{base}/api/{name}", data=json.dumps(body or {}).encode(), headers=h)
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            return e.code, json.load(e)
    yield post
    srv.shutdown()


def test_pack_trip_and_reset_through_the_api(http):
    code, s = http("pack_reset", {"cells_in_series": 6, "seed": 1})
    assert code == 200 and len(s["cells"]) == 6
    http("pack_command", {"current": 50})
    s = http("pack_step", {"seconds": 120})[1]
    assert s["state"] == "discharging" and s["pack_current"] > 49
    http("pack_fault", {"cell": 2, "kind": "overheat"})
    s = http("pack_step", {"seconds": 2})[1]
    assert s["latched"] == ["overtemperature"] and s["pack_current"] == 0
    assert http("pack_reset_fault")[1]["reset_accepted"] is False
    http("pack_fault", {"cell": 2, "kind": "heal"})
    http("pack_step", {"seconds": 2})
    assert http("pack_reset_fault")[1]["reset_accepted"] is True


def test_cell_lab_through_the_api(http):
    code, r = http("cell_simulate", {"chemistry": "LFP", "model": "SPM", "c_rate": 1})
    assert code == 200 and r["soc"][-1] < 5 and 3.0 < r["voltage"][0] < 3.9


def test_api_refuses_cross_site_and_bad_input(http):
    assert http("info", headers={"Host": "evil.example"})[0] == 403
    assert http("info", headers={"Content-Type": "text/plain"})[0] == 415
    code, body = http("pack_fault", {"cell": 0, "kind": "explode"})
    assert code == 400 and "unknown fault" in body["error"]


def test_studio_is_served_and_traversal_is_not():
    """Regression: STATIC was not normalised, so importing gaia through a
    path containing '..' made every page 404."""
    import os

    from gaia import server
    srv = server.make_server(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        assert server.STATIC == os.path.abspath(server.STATIC)
        with urllib.request.urlopen(base + "/") as r:
            assert r.status == 200 and b"GAIA Studio" in r.read()
        with pytest.raises(urllib.error.HTTPError) as err:
            urllib.request.urlopen(base + "/../pyproject.toml")
        assert err.value.code == 404
    finally:
        srv.shutdown()
