from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


class Vehicle(db.Model):
    __tablename__ = "vehicle"
    id = db.Column(db.Integer, primary_key=True)
    kenteken = db.Column(db.String(20), nullable=False, unique=True)
    merk = db.Column(db.String(50))
    model = db.Column(db.String(50))
    actief = db.Column(db.Boolean, default=True)
    trips = db.relationship("Trip", backref="vehicle", lazy=True)

    def __repr__(self):
        return f"{self.kenteken} ({self.merk} {self.model})"


class Driver(db.Model):
    __tablename__ = "driver"
    id = db.Column(db.Integer, primary_key=True)
    naam = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    odoo_user_id = db.Column(db.Integer)
    trips = db.relationship("Trip", backref="driver", lazy=True)

    def __repr__(self):
        return self.naam


class Trip(db.Model):
    __tablename__ = "trip"
    id = db.Column(db.Integer, primary_key=True)
    datum = db.Column(db.Date, nullable=False, default=date.today)
    driver_id = db.Column(db.Integer, db.ForeignKey("driver.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    startlocatie = db.Column(db.String(200), nullable=False)
    eindlocatie = db.Column(db.String(200), nullable=False)
    beginstand_km = db.Column(db.Numeric(10, 1), nullable=False)
    eindstand_km = db.Column(db.Numeric(10, 1), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'zakelijk' of 'prive'
    odoo_partner_id = db.Column(db.Integer)
    odoo_partner_naam = db.Column(db.String(200))
    odoo_project_id = db.Column(db.Integer)
    odoo_project_naam = db.Column(db.String(200))
    omschrijving = db.Column(db.String(500), nullable=False)
    notitie = db.Column(db.Text)
    bijlage_pad = db.Column(db.String(300))
    aangemaakt_op = db.Column(db.DateTime, default=datetime.utcnow)
    gewijzigd_op = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def kilometers(self):
        return float(self.eindstand_km) - float(self.beginstand_km)

    def validate(self):
        errors = []
        if float(self.eindstand_km) <= float(self.beginstand_km):
            errors.append("Eindstand km moet hoger zijn dan beginstand km.")
        return errors
