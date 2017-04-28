from flask import Flask
from flask_restplus import Resource, Api
from flask_restplus import Resource, fields
from flask_sqlalchemy import SQLAlchemy

from printapp_sqlalchemy.printapp_sqlalchemy import (Filament,
                                                     ColorFamily,
                                                     Printer, Print, connectionUri, Image
                                                     )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connectionUri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app)
db = SQLAlchemy(app)

filamentDetailModel = api.model('FilamentModel', {
    'FilamentId': fields.Integer,
    'UserId': fields.Integer,
    'UserFilamentId': fields.Integer,
    'Material': fields.String,
    'Brand': fields.String,
    'Color': fields.String,
    'LengthRemain': fields.Integer,
    'DateAcquired': fields.Date,
    'FilamentSource': fields.String,
    'HtmlColor': fields.String
})

filamentColorModel = api.model('FilamentColor', {
    'ColorId': fields.Integer(attribute='ColorFamilyId'),
    'Color': fields.String(attribute="ColorFamilyName")
})

printerDetailModel = api.model('PrinterModel', {
    'PrinterId': fields.Integer,
    'UserId': fields.Integer,
    'UserPrinterId': fields.Integer,
    'PrinterName': fields.String,
    'DateAcquired': fields.Date,
    'NumberOfPrints': fields.Integer,
    'PrintTimeHours': fields.Integer,
    'PrinterSource': fields.String,
    'BeltMaintInt': fields.Integer,
    'BeltMaintLast': fields.Integer,
    'WireMaintInt': fields.Integer,
    'WireMaintLast': fields.Integer,
    'LubeMaintInt': fields.Integer,
    'LubeMaintLast': fields.Integer,
    'MainPrinterImageUrl': fields.String
})

printDetailModel = api.model('PrintModel', {
    'PrintId': fields.Integer,
    'UserId': fields.Integer,
    'PrintName': fields.String,
    'SourceUrl': fields.String,
    'ModelPath': fields.String,
    'Success': fields.Boolean,
    'PrintTimeHours': fields.Integer,
    'PrintTimeMinutes': fields.Integer,
    'MainPrintImageUrl': fields.String,
    'FilamentId': fields.Integer,
    'FilamentName': fields.String,
    'FilamentBrand': fields.String,
    'FilamentMaterial': fields.String,
    'FilamentColor': fields.String,
    'PrinterId': fields.Integer,
    'PrinterName': fields.String,
    'PrintDate': fields.Date,
    'LengthUsed': fields.Integer,
})

@api.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello':'world'}

@api.route('/filaments/filamentdetails/<int:filament_id>')
@api.doc(params={'filament_id': 'Global filament id.'})
class FilamentResp(Resource):
    @api.marshal_with(filamentDetailModel)
    def get(self, filament_id):
        filament = db.session.query(Filament).filter(Filament.FilamentId == filament_id).one_or_none()
        http_resp = 404 if filament is None else 200
        return filament, http_resp

@api.route('/filaments/<int:user_id>')
@api.doc(params={'user_id': 'ID of the user to retrieve info for.'})
class FilamentLibraryResp(Resource):
    @api.marshal_with(filamentDetailModel, envelope="data")
    def get(self, user_id):
        filaments = db.session.query(Filament)\
                    .filter(Filament.UserId == user_id)\
                    .order_by(Filament.UserFilamentId.asc())\
                    .all()
        http_resp = 404 if filaments is None else 200
        return filaments, http_resp

@api.route('/filaments/colors')
@api.doc()
class FilamentColorsResp(Resource):
    @api.marshal_with(filamentColorModel, envelope='data')
    def get(self):
        colors = db.session.query(ColorFamily).order_by(ColorFamily.ColorFamilyName.asc()).all()
        http_resp = 404 if colors is None else 200
        return colors, http_resp

@api.route('/printers/<int:user_id>')
@api.doc(params={'user_id': 'ID of user to retrieve info for.'})
class PrinterLibraryResp(Resource):
    @api.marshal_with(printerDetailModel, envelope='data')
    def get(self, user_id):
        rows = db.session.query(Printer,
                                Image.ImagePath.label('MainPrinterImageUrl'))\
                    .outerjoin(Image, Image.ImageId == Printer.MainPrinterImageId)\
                    .filter(Printer.UserId == user_id)\
                    .order_by(Printer.UserPrinterId.asc())\
                    .all()

        printers = []
        for row in rows:
            printer = row.printers
            printer.MainPrinterImageUrl = row.MainPrinterImageUrl
            printers.append(printer)

        http_resp = 404 if rows is None else 200
        return printers, http_resp

@api.route('/printers/printerdetails/<int:printer_id>')
@api.doc(params={'printer_id': 'Global ID of printer.'})
class PrinterDetailResp(Resource):
    @api.marshal_with(printerDetailModel)
    def get(self, printer_id):
        printer = db.session.query(Printer, Image.ImagePath.label("MainPrinterImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Printer.MainPrinterImageId)\
                    .filter(Printer.PrinterId == printer_id).one_or_none()
        retPrinter = printer.printers
        retPrinter.MainPrinterImageUrl = printer.MainPrinterImageUrl

        http_resp = 404 if printer is None else 200
        return retPrinter, http_resp


@api.route('/prints/<int:user_id>')
@api.doc(params={'user_id': 'ID of user to retrieve info for.'})
class PrintLibraryResp(Resource):
    @api.marshal_with(printDetailModel)
    def get(self, user_id):
        rows = db.session.query(Print,
                                Filament.FilamentId,
                                Printer.PrinterId,
                                Image.ImagePath.label("MainPrintImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Print.MainPrintImageId)\
                    .outerjoin(Filament, Filament.FilamentId == Print.FilamentId)\
                    .outerjoin(Printer, Printer.PrinterId == Print.PrinterId)\
                    .filter(Print.UserId == user_id).all()

        prints = []
        for row in rows:
            pt = row.prints
            pt.MainPrintImageUrl = row.MainPrintImageUrl
            pt.FilamentId = row.FilamentId
            pt.PrinterId = row.PrinterId
            prints.append(pt)

        http_resp = 404 if rows is None else 200
        return prints, http_resp


@api.route('/prints/printdetails/<int:print_id>')
@api.doc(params={'print_id': 'Global ID of print to retrieve.'})
class PrintDetailResp(Resource):
    @api.marshal_with(printDetailModel)
    def get(self, print_id):
        rows = db.session.query(Print,
                                Filament.FilamentId,
                                Filament.Brand,
                                Filament.Material,
                                ColorFamily.ColorFamilyName,
                                Printer.PrinterId,
                                Image.ImagePath.label("MainPrintImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Print.MainPrintImageId)\
                    .outerjoin(Filament, Filament.FilamentId == Print.FilamentId)\
                    .outerjoin(ColorFamily, ColorFamily.ColorFamilyId == Filament.ColorFamilyId)\
                    .outerjoin(Printer, Printer.PrinterId == Print.PrinterId)\
                    .filter(Print.PrintId == print_id).one_or_none()

        pt = rows.prints
        pt.FilamentBrand = rows.Brand
        pt.FilamentMaterial = rows.Material
        pt.FilamentColor = rows.ColorFamilyName
        pt.PrinterId = rows.PrinterId
        pt.FilamentId = rows.FilamentId

        http_resp = 404 if rows is None else 200
        return pt, http_resp

if __name__ == "__main__":
    app.run(debug=True)