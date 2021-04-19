# Import
import flask
import flask_socketio
import datetime

# Counter class
class Counter:
    def __init__(self, initial_value:int = 0): self.count = initial_value
    def change(self, by:int = 1): self.count += by
        
# Setup
main_app = flask.Flask(__name__, template_folder = "template")
main_app.config["SECRET_KEY"] = "TOTALLY_SECURE"
socket_io = flask_socketio.SocketIO(main_app)
user_database = {}
users_connected = Counter() 
messages_sent = Counter()

LOG_LOCATION = "log.txt"
UTC_TIMEZONE_OFFSET = -4 # EDT

# Misc. functions =================================================================================

# Log
def log(text_to_log:str, file:str = LOG_LOCATION):
    print(text_to_log)
    with open (file = LOG_LOCATION, mode = "a") as log_text_file: log_text_file.write(text_to_log + "\n")

# Get current time (shifted to timezone)
def get_current_time():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours = UTC_TIMEZONE_OFFSET)).strftime("%m/%d/%Y")

# Chatroom functions ==============================================================================

# User connection handler
@socket_io.on("user_connection")
def user_connect_handler(data:dict):
    users_connected.change(by = 1)
    flask_socketio.send(f"{data['username']} has joined the chatroom! There are now {users_connected.count} users in this chatroom.", broadcast = True)
    # Add to database
    user_database[flask.request.sid] = data["username"]

    log(text_to_log = f"{flask.request.sid}: {data['username']} joined | Database: {user_database} | {get_current_time()}")

# User disconnection handler
@socket_io.on("disconnect")
def user_disconnection_handler():
    username = user_database[flask.request.sid]
    users_connected.change(by = -1)
    flask_socketio.send(f"{username} has left the chatroom! There are now {users_connected.count} users in this chatroom.", broadcast = True)
    # Remove from database
    del user_database[flask.request.sid]

    log(text_to_log = f"{flask.request.sid}: {username} left | Database: {user_database} | {get_current_time()}")

# Send message handler
@socket_io.on("send_message")
def send_message_handler(data:dict):
    messages_sent.change(by = 1)
    flask_socketio.send(f"[#{str(messages_sent.count).zfill(4)}] {user_database[flask.request.sid]}: {data['message']}", broadcast = True)

    log(text_to_log = f"{flask.request.sid}: {user_database[flask.request.sid]} sent message with data: \"{data}\" | Database: {user_database} | {get_current_time()}")

# Message handler
@socket_io.on("message")
def message_handler(message:str):
    print(f"Message recieved at {datetime.datetime.utcnow()} (GMT): \"{message}\"")
    flask_socketio.send(message, broadcast = True)

    log(text_to_log = f"Sending message to all: {message} | {get_current_time()}")

# Website navigation ==============================================================================

# Join chatroom
@main_app.route("/")
def join_chatroom(): return flask.render_template("join.html")

# Chatroom
@main_app.route("/chatroom", methods = ["POST", "GET"])
def chatroom():
    # Send to chatroom with username
    try:
        # Get username
        username = flask.request.form["username_input"]
        # Make sure username is not already in database
        for username_db in user_database.values():
            if username_db.lower() == username.lower():
                flask.flash(f"Username \"{username_db}\" is already in use.")
                break
        else: return flask.render_template("chatroom.html", username = username)

    # Either a GET request or username not submitted, either way just sent to join
    except Exception: pass
    return flask.redirect("/")

# Run
if __name__ == "__main__":
    socket_io.run(main_app, debug = True, port = 5002)