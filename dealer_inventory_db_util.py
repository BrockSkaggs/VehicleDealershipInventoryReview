import datetime as dt
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.dealer_vehicle import DealerVehicle

class DealerVehicleDbUtil:

    def __init__(self):
        self.db_path = r"dealer_inv.db"
        self.url = f"sqlite:///{self.db_path}"
        self.engine = None
        self.session = None    

    def create_alchemy_engine(self):
        self.engine = create_engine(self.url)
    
    def create_alchemy_session(self):
        if self.engine is None:
            self.create_alchemy_engine()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

    def create_sqlite_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        #Ref: https://www.sqlitetutorial.net/sqlite-python/create-tables/
        #Ref: https://www.sqlite.org/datatype3.html
        table_create_sql = """CREATE TABLE IF NOT EXISTS dealer_vehicle(
                                dealer text not null,
                                desc text not null,
                                year integer not null,
                                engine text,
                                transmission text,
                                odometer integer,
                                mpg text,
                                stock_number text,
                                vin text,
                                price integer,
                                scan_time text not null
                                );"""

        c.execute(table_create_sql)

        print("HERE")
    
    def build_dealer_vehicle(self, dealer: str, desc: str, year: int, eng: str, trans: str, odometer: str, mpg: str, stock_num: str, vin: str, price: int, scan_time: dt.datetime) -> DealerVehicle:
        vehicle = DealerVehicle()
        vehicle.dealer = dealer
        vehicle.desc = desc
        vehicle.year = year
        vehicle.engine = eng
        vehicle.transmission = trans
        vehicle.odometer = odometer
        vehicle.mpg = mpg
        vehicle.stock_number = stock_num
        vehicle.vin = vin
        vehicle.price = price
        vehicle.scan_time = scan_time
        return vehicle

    def store_vehicles(self, vehicles: []):
        if self.session is None:
            self.create_alchemy_session()
        
        for v in vehicles:
            self.session.add(v)
        self.session.commit()


def test():
    db_util = DealerVehicleDbUtil()
    # db_util.create_sqlite_db()

if __name__ == '__main__':
    test()