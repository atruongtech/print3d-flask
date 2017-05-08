from flask import Flask, request
from flask_restplus import Resource, Api, fields
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from printapp_sqlalchemy.printapp_sqlalchemy import (Filament,
                                                     ColorFamily,
                                                     Printer, Print, connectionUri, Image
                                                     )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connectionUri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app)
db = SQLAlchemy(app)
CORS(app)

filamentDetailModel = api.model('FilamentModel', {
    'FilamentId': fields.Integer,
    'UserId': fields.Integer,
    'UserFilamentId': fields.Integer,
    'Material': fields.String,
    'Brand': fields.String,
    'Color': fields.String(attribute='ColorFamilyName'),
    'LengthRemain': fields.Integer,
    'DateAcquired': fields.Date,
    'FilamentSource': fields.String,
    'HtmlColor': fields.String
})

filamentColorModel = api.model('FilamentColor', {
    'ColorId': fields.Integer(attribute='ColorFamilyId'),
    'Color': fields.String(attribute='ColorFamilyName')
})


printPrinterModel = api.model('PrintPrinterModel', {
    'PrintId': fields.Integer,
    'PrintName': fields.String,
    'MainPrintImageUrl': fields.String
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
    'MainPrinterImageUrl': fields.String,
    'Prints': fields.List(fields.Nested(printPrinterModel), attribute='PrintList')
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
    @api.marshal_with(filamentDetailModel, envelope='data')
    def get(self, filament_id):
        row = db.session.query(Filament,
                                     ColorFamily.ColorFamilyName)\
                    .outerjoin(ColorFamily)\
                    .filter(Filament.FilamentId == filament_id)\
                    .one_or_none()

        filament = row.filaments
        filament.ColorFamilyName = row.ColorFamilyName

        http_resp = 404 if row is None else 200
        return filament, http_resp

@api.route('/filaments/<int:user_id>')
@api.doc(params={'user_id': 'ID of the user to retrieve info for.'})
class FilamentLibraryResp(Resource):
    @api.marshal_with(filamentDetailModel, envelope="data")
    def get(self, user_id):
        rows = db.session.query(Filament,
                                     ColorFamily.ColorFamilyName)\
                    .outerjoin(ColorFamily)\
                    .filter(Filament.UserId == user_id)\
                    .order_by(Filament.UserFilamentId.asc())\
                    .all()

        filaments = []
        for row in rows:
            filament = row.filaments
            filament.ColorFamilyName = row.ColorFamilyName
            filaments.append(filament)

        http_resp = 404 if rows is None else 200
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
    @api.marshal_with(printerDetailModel, envelope='data')
    def get(self, printer_id):
        printer = db.session.query(Printer, Image.ImagePath.label("MainPrinterImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Printer.MainPrinterImageId)\
                    .filter(Printer.PrinterId == printer_id).one_or_none()

        prints = db.session.query(Print, Image.ImagePath.label("MainPrintImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Print.MainPrintImageId)\
                    .filter(Print.PrinterId == printer_id).all()

        retPrinter = printer.printers
        retPrinter.MainPrinterImageUrl = printer.MainPrinterImageUrl
        retPrinter.PrintList = []

        for prt in prints:
            retPrint = prt.prints
            retPrint.MainPrintImageUrl = prt.MainPrintImageUrl
            retPrinter.PrintList.append(retPrint)

        http_resp = 404 if printer is None else 200
        return retPrinter, http_resp

    @api.marshal_with(printerDetailModel, envelope="data")
    def put(self, printer_id):
        data = request.get_json()
        printer = db.session.query(Printer).filter(Printer.PrinterId == printer_id).one_or_none()

        printer.PrinterName = data['PrinterName']
        printer.DateAcquired = data['DateAcquired']
        printer.PrinterSource = data['PrinterSource']
        printer.BeltMaintInt = data['BeltMaintInt']
        printer.WireMaintInt = data['WireMaintInt']
        db.session.add(printer);
        db.session.commit();
        return printer




@api.route('/prints/<int:user_id>')
@api.doc(params={'user_id': 'ID of user to retrieve info for.'})
class PrintLibraryResp(Resource):
    @api.marshal_with(printDetailModel, envelope='data')
    def get(self, user_id):
        rows = db.session.query(Print,
                                Filament.FilamentId,
                                Filament.Brand,
                                Filament.Material,
                                Printer.PrinterId,
                                Printer.PrinterName,
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
            pt.FilamentName = '{0} {1}'.format(row.Brand, row.Material)
            pt.PrinterId = row.PrinterId
            pt.PrinterName = row.PrinterName
            prints.append(pt)

        http_resp = 404 if rows is None else 200
        return prints, http_resp


@api.route('/prints/printdetails/<int:print_id>')
@api.doc(params={'print_id': 'Global ID of print to retrieve.'})
class PrintDetailResp(Resource):
    @api.marshal_with(printDetailModel, envelope='data')
    def get(self, print_id):
        rows = db.session.query(Print,
                                Filament.UserFilamentId,
                                Filament.FilamentId,
                                Filament.Brand,
                                Filament.Material,
                                ColorFamily.ColorFamilyName,
                                Printer.PrinterId,
                                Printer.PrinterName,
                                Printer.UserPrinterId,
                                Image.ImagePath.label("MainPrintImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Print.MainPrintImageId)\
                    .outerjoin(Filament, Filament.FilamentId == Print.FilamentId)\
                    .outerjoin(ColorFamily, ColorFamily.ColorFamilyId == Filament.ColorFamilyId)\
                    .outerjoin(Printer, Printer.PrinterId == Print.PrinterId)\
                    .filter(Print.PrintId == print_id).one_or_none()

        pt = rows.prints
        pt.PrinterId = rows.PrinterId
        pt.FilamentId = rows.FilamentId
        pt.FilamentName = "{0} {1} ({2}) - Spool {3}".format(rows.Brand, rows.Material, rows.ColorFamilyName, rows.UserFilamentId)
        pt.PrinterName = "{0} - Printer {1}".format(rows.PrinterName, rows.UserPrinterId)
        pt.MainPrintImageUrl = rows.MainPrintImageUrl

        http_resp = 404 if rows is None else 200
        return pt, http_resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)