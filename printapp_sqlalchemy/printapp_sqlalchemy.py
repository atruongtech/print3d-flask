from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from printapp_sqlalchemy_config import RDSCONSTRING, USER, PASSWORD, DATABASE

connectionUri = "mysql://{0}:{1}@{2}/{3}".format(USER,PASSWORD,RDSCONSTRING,DATABASE)

engine = create_engine(connectionUri)
Base = automap_base()

Base.prepare(engine, reflect=True)

User = Base.classes.users
Print = Base.classes.prints
Printer = Base.classes.printers
Filament = Base.classes.filaments
Image = Base.classes.images
ColorFamily = Base.classes.colorfamilies

session = Session(engine)

if __name__ == "__main__":
    testuser = session.query(User).first()
    print(testuser.UserName)