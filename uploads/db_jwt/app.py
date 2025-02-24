from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import timedelta

app = Flask(__name__)
CORS(app)

# Configurations
db_config = {
    "host": "100.125.25.71",
    "user": "root",
    "password": "root",
    "database": "machine_data"
}
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "bf4b561e63effbce487349de7148c7765c7feaa8a26a1665cd9c2716f90cf9ea201d9d2b7aec12bbad2a1b39479849c6ce260098fbd9b06ffc244560fcdf86a36da8d88e80699788f340c6ee634719dda699131d1e99abd5d9425698aaa84a9dbefb03cc8ec2a1f38acb5d15f619a2240cca112b707e287b8083797b61e6edc333b2c7f57b20c44f3b6df6298b2137654f7e61578671e9029cf1cda10969ef5c7546b153b39d50986334f4284928f5d32d92e4d2a2d2fa5d3946419e21a0aa8523a46b9bea268628a6c2680929f04439d04dd9d5ac8169968145b381620d62ddaa2963641b5c8cd5ff43eee9f02cf889bb671791803000af56cb422947a6d127"
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=5) 

db = SQLAlchemy(app)
jwt = JWTManager(app)
BLACKLIST = set()

# Database Model
class SensorData(db.Model):
    __tablename__ = "sensor_data"
    id = db.Column(db.Integer, primary_key=True)
    power = db.Column(db.Float)
    voltage_l1_gnd = db.Column(db.Float)
    voltage_l2_gnd = db.Column(db.Float)
    voltage_l3_gnd = db.Column(db.Float)
    pressure = db.Column(db.Float)
    forces = db.Column(db.Float)
    cycle_count = db.Column(db.Integer)
    position = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.json.get('username')
    password = request.json.get('password')
    if username == 'user' and password == 'pass': 
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Invalid credentials"}), 401

@app.route("/sensor_data", methods=["POST"])
@jwt_required()
def add_sensor_data():
    data = request.json
    sensor_record = SensorData(**data)
    db.session.add(sensor_record)
    db.session.commit()
    return jsonify({"msg": "Sensor data added", "id": sensor_record.id}), 201

@app.route("/sensor_data", methods=["GET"])
@jwt_required()
def get_sensor_data():
    sensor_data_records = SensorData.query.all()
    result = [
        {
            "id": record.id,
            "power": record.power,
            "voltage_l1_gnd": record.voltage_l1_gnd,
            "voltage_l2_gnd": record.voltage_l2_gnd,
            "voltage_l3_gnd": record.voltage_l3_gnd,
            "pressure": record.pressure,
            "forces": record.forces,
            "cycle_count": record.cycle_count,
            "position": record.position,
            "timestamp": record.timestamp.isoformat(),
        }
        for record in sensor_data_records
    ]
    return jsonify(result)

@app.route("/sensor_data/<int:id>", methods=["PUT"])
@jwt_required()
def update_sensor_data(id):
    data = request.json
    sensor_record = SensorData.query.get_or_404(id)
    for key, value in data.items():
        setattr(sensor_record, key, value)
    db.session.commit()
    return jsonify({"msg": "Sensor data updated successfully"})

@app.route("/sensor_data/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_sensor_data(id):
    sensor_record = SensorData.query.get_or_404(id)
    db.session.delete(sensor_record)
    db.session.commit()
    return jsonify({"msg": "Sensor data deleted successfully"})


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt_identity()  # Token identity or unique token ID
    BLACKLIST.add(jti)  # Add token to blacklist
    return jsonify(msg="Successfully logged out"), 200

# Add this callback to check if a token is blacklisted
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in BLACKLIST