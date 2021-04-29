
from sqlalchemy import Column, Integer, String, DateTime, PrimaryKeyConstraint
from models.base import Base

class DealerVehicle(Base):
    __tablename__ = 'dealer_vehicle'
    __table_args__ = (
        PrimaryKeyConstraint('vin', 'scan_time'),
    )

    dealer = Column(String, nullable=False)
    desc = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    engine = Column(String)
    transmission = Column(String)
    odometer = Column(String)
    mpg = Column(String)
    stock_number = Column(String)
    vin = Column(String)
    price = Column(Integer)
    scan_time = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<DealerVehicle(dealer='{self.dealer}', desc='{self.desc}', year='{self.year}', scan_time='{self.scan_time}')>"