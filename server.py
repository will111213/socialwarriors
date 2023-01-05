print (" [+] Loading basics...")
import os
import json
import urllib
if os.name == 'nt':
    os.system("color")

os.system("title Social Wars Server")

print (" [+] Loading game config...")
from get_game_config import get_game_config

print (" [+] Loading players...")
from get_player_info import get_player_info, get_neighbor_info
from sessions import load_saved_villages, all_saves_userid, all_saves_info, save_info, new_village
load_saved_villages()

print (" [+] Loading auction house data...")
from auctions import get_auctions
print (" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session
from flask.debughelpers import attach_enctype_error_multidict
from command import command
from engine import timestamp_now
from version import version_name
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR

host = '127.0.0.1'
port = 5055

app = Flask(__name__, template_folder=TEMPLATES_DIR)

print (" [+] Configuring server routes...")

##########
# ROUTES #
##########

__STATIC_ROOT = "/static/socialwars"
__DYNAMIC_ROOT = "/dynamic/menvswomen/srvsexwars"

## PAGES AND RESOURCES

@app.route("/", methods=['GET', 'POST'])
def login():
    # Log out previous session
    session.pop('USERID', default=None)
    session.pop('GAMEVERSION', default=None)
    # Reload saves. Allows saves modification without server reset
    load_saved_villages()
    # If logging in, set session USERID, and go to play
    if request.method == 'POST':
        session['USERID'] = request.form['USERID']
        session['GAMEVERSION'] = request.form['GAMEVERSION']
        print("[LOGIN] USERID:", request.form['USERID'])
        print("[LOGIN] GAMEVERSION:", request.form['GAMEVERSION'])
        return redirect("/play.html")
    # Login page
    if request.method == 'GET':
        saves_info = all_saves_info()
        return render_template("login.html", saves_info=saves_info, version=version_name)

@app.route("/play.html")
def play():
    if 'USERID' not in session:
        return redirect("/")
    if 'GAMEVERSION' not in session:
        return redirect("/")

    if session['USERID'] not in all_saves_userid():
        return redirect("/")
    
    USERID = session['USERID']
    GAMEVERSION = session['GAMEVERSION']
    print("[PLAY] USERID:", USERID)
    print("[PLAY] GAMEVERSION:", GAMEVERSION)
    return render_template("play.html", save_info=save_info(USERID), serverTime=timestamp_now(), version=version_name, GAMEVERSION=GAMEVERSION, SERVERIP=host, SERVERPORT=port)

@app.route("/new.html")
def new():
    session['USERID'] = new_village()
    session['GAMEVERSION'] = "Basesec_1.5.4.swf"
    return redirect("play.html")

@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/img/<path:path>")
def images(path):
    return send_from_directory(TEMPLATES_DIR + "/img", path)

@app.route("/css/<path:path>")
def css(path):
    return send_from_directory(TEMPLATES_DIR + "/css", path)

## GAME STATIC

@app.route(__STATIC_ROOT + "/<path:path>")
def static_assets_loader(path):
    return send_from_directory(ASSETS_DIR, path)

## GAME DYNAMIC

@app.route(__DYNAMIC_ROOT + "/track_game_status.php", methods=['POST'])
def track_game_status_response():
    status = request.values['status']
    installId = request.values['installId']
    user_id = request.values['user_id']

    # print(f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --", request.values)
    print(f"[STATUS] USERID {user_id}: {status}")
    return ("", 200)

@app.route(__DYNAMIC_ROOT + "/get_game_config.php")
def get_game_config_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"get_game_config: USERID: {USERID}. --", request.values)
    print(f"[CONFIG] USERID {USERID}.")
    return get_game_config()

@app.route(__DYNAMIC_ROOT + "/get_player_info.php", methods=['POST'])
def get_player_info_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    user = request.values['user'] if 'user' in request.values else None
    client_id = int(request.values['client_id']) if 'client_id' in request.values else None
    map = int(request.values['map']) if 'map' in request.values else None

    # print(f"get_player_info: USERID: {USERID}. --", request.values)
    if not user: print(f"[PLAYER INFO] USERID {USERID}.")
    else:        print(f"[VISIT] USERID {USERID} visiting user: {user}.")

    # Current Player
    if user is None:
        return (get_player_info(USERID), 200)
    # General Mike
    elif user in ["100000030","100000031"]:
        return (get_neighbor_info("100000030", map), 200)
    # Quest Maps
    elif user.startswith("100000"):
        return (get_neighbor_info(user, map), 200)
    # Static Neighbours
    else:
        return (get_neighbor_info(user, map), 200)
    
## AUCTION HOUSE

@app.route(__DYNAMIC_ROOT + "/bets/get_bets_list.php", methods=['POST'])
def get_bets_list():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    bets = get_auctions()
    for bet in bets:
        bet["isPrivate"] =  0
        bet["isWinning"] =  0
        bet["won"] =  0
        bet["finished"] =  0

    r = {}
    r["result"] = "success"
    r["data"] = {"bets": bets}

    response = json.dumps(r)
    # print("RESPONSE:")
    # print(response)

    return (response, 200)

@app.route(__DYNAMIC_ROOT + "/bets/get_bet_detail.php", methods=['POST'])
def get_bet_detail():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)
    uuid = data["uuid"]

    print(f"Get bet details for BET UUID {uuid}")

    r = {}
    r["result"] = "success"
    r["data"] = {}

    response = json.dumps(r)
    # print("RESPONSE:")
    # print(response)

    return (response, 200)

@app.route(__DYNAMIC_ROOT + "/bets/set_bet.php", methods=['POST'])
def set_bet():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']
    data = request.values['data']

    if not data.startswith("{"):
        data = data[65:]
    
    data = json.loads(data)

    r = {}
    r["result"] = "success"
    r["data"] = {}

    response = json.dumps(r)
    # print("RESPONSE:")
    # print(response)

    return (response, 200)

@app.route(__DYNAMIC_ROOT + "/sync_error_track.php", methods=['POST'])
def sync_error_track_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"sync_error_track: USERID: {USERID}. --", request.values)
    return ("", 200)

@app.route("/null")
def flash_sync_error_response():
    sp_ref_cat = request.values['sp_ref_cat']

    if sp_ref_cat == "flash_sync_error":
        reason = "reload On Sync Error"
    elif sp_ref_cat == "flash_reload_quest":
        reason = "reload On End Quest"
    elif sp_ref_cat == "flash_reload_attack":
        reason = "reload On End Attack"

    print("flash_sync_error", reason, ". --", request.values)
    return redirect("/play.html")

@app.route(__DYNAMIC_ROOT + "/command.php", methods=['POST'])
def command_response():
    USERID = request.values['USERID']
    user_key = request.values['user_key']
    language = request.values['language']

    # print(f"command: USERID: {USERID}. --", request.values)

    data_str = request.values['data']
    data_hash = data_str[:64]
    assert data_str[64] == ';'
    data_payload = data_str[65:]
    data = json.loads(data_payload)

    command(USERID, data)
    
    return ({"result": "success"}, 200)


########
# MAIN #
########

print (" [+] Running server...")

if __name__ == '__main__':
    app.secret_key = 'SECRET_KEY'
    app.run(host=host, port=port, debug=False)
