from flask import Flask, request
from flask_restplus import Resource, Api, fields
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from printapp_sqlalchemy.printapp_sqlalchemy import (Filament,
                                                     ColorFamily,
                                                     Printer,
                                                     Print,
                                                     connectionUri,
                                                     Image
                                                     )
from auth_decorators import required_apikey
from image_handler import ImageHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = connectionUri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
api = Api(app)
db = SQLAlchemy(app)
CORS(app)

printPrinterModel = api.model('PrintPrinterModel', {
    'PrintId': fields.Integer,
    'PrintName': fields.String,
    'MainPrintImageUrl': fields.String
})

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
    'HtmlColor': fields.String,
    'ColorId': fields.Integer(attribute='ColorFamilyId'),
    'Prints': fields.List(fields.Nested(printPrinterModel))
})

filamentColorModel = api.model('FilamentColor', {
    'ColorId': fields.Integer(attribute='ColorFamilyId'),
    'Color': fields.String(attribute='ColorFamilyName')
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
    'PrintTimeMinutes': fields.Integer,
    'MainPrintImageUrl': fields.String,
    'FilamentId': fields.Integer,
    'FilamentName': fields.String,
    'PrinterId': fields.Integer,
    'PrinterName': fields.String,
    'PrintDate': fields.Date,
    'LengthUsed': fields.Integer,
})

@api.route('/filaments/filamentdetails/<int:filament_id>')
@api.doc(params={'filament_id': 'Global filament id.'})
class FilamentResp(Resource):
    @required_apikey
    @api.marshal_with(filamentDetailModel, envelope='data')
    def get(self, filament_id):
        row = db.session.query(Filament,
                                     ColorFamily.ColorFamilyName)\
                    .outerjoin(ColorFamily)\
                    .filter(Filament.FilamentId == filament_id)\
                    .one_or_none()

        if row is None:
            return None, 404

        prints = db.session.query(Print, Image.ImagePath.label('MainPrintImageUrl'))\
                    .outerjoin(Image, Print.MainPrintImageId == Image.ImageId)\
                    .filter(Print.FilamentId == filament_id)\
                    .all()

        filament = row.filaments
        filament.ColorFamilyName = row.ColorFamilyName
        filament.Prints = []

        for prntRow in prints:
            prnt = prntRow.prints
            prnt.MainPrintImageUrl = prntRow.MainPrintImageUrl
            filament.Prints.append(prnt)

        return filament

    @required_apikey
    @api.marshal_with(filamentDetailModel, envelope='data')
    def put(self, filament_id):
        filament = db.session.query(Filament).filter(Filament.FilamentId == filament_id).one_or_none()
        if filament is None:
            return None, 404

        data = request.get_json()

        filament.Brand = data['Brand'] if data['Brand'] is not None else filament.Brand
        filament.Material = data['Material'] if data['Material'] is not None else filament.Material
        filament.LengthRemain = data['LengthRemain'] if data['LengthRemain'] is not None else filament.LengthRemain

        # careful as this particular property is named differently in json
        filament.ColorFamilyId = data['ColorId'] if data['ColorId'] is not None else filament.ColorFamilyId
        filament.FilamentSource = data['FilamentSource'] if data['FilamentSource'] is not None else filament.FilamentSource
        filament.DateAcquired = data['DateAcquired'] if data['DateAcquired'] is not None else filament.DateAcquired
        filament.HtmlColor = data['HtmlColor'] if data['HtmlColor'] is not None else filament.HtmlColor

        db.session.add(filament)
        db.session.commit()
        return filament


@api.route('/filaments/<int:user_id>')
@api.doc(params={'user_id': 'ID of the user to retrieve info for.'})
class FilamentLibraryResp(Resource):
    @required_apikey
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
    @required_apikey
    @api.marshal_with(filamentColorModel, envelope='data')
    def get(self):
        colors = db.session.query(ColorFamily).order_by(ColorFamily.ColorFamilyName.asc()).all()
        http_resp = 404 if colors is None else 200
        return colors, http_resp

@api.route('/printers/<int:user_id>')
@api.doc(params={'user_id': 'ID of user to retrieve info for.'})
class PrinterLibraryResp(Resource):
    @required_apikey
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
    @required_apikey
    @api.marshal_with(printerDetailModel, envelope='data')
    def get(self, printer_id):
        printer = db.session.query(Printer, Image.ImagePath.label("MainPrinterImageUrl"))\
                    .outerjoin(Image, Image.ImageId == Printer.MainPrinterImageId)\
                    .filter(Printer.PrinterId == printer_id).one_or_none()

        if printer is None:
            return None, 404

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

    @required_apikey
    @api.marshal_with(printerDetailModel, envelope="data")
    def put(self, printer_id):
        data = request.get_json()
        printer = db.session.query(Printer).filter(Printer.PrinterId == printer_id).one_or_none()
        if printer is None:
            return None, 404

        printer.PrinterName = data['PrinterName'] if data['PrinterName'] is not None else printer.PrinterName
        printer.DateAcquired = data['DateAcquired'] if data['DateAcquired'] is not None else printer.DateAcquired
        printer.PrinterSource = data['PrinterSource'] if data['PrinterSource'] is not None else printer.PrinterSource
        printer.BeltMaintInt = data['BeltMaintInt'] if data['BeltMaintInt'] is not None else printer.BeltMaintInt
        printer.WireMaintInt = data['WireMaintInt'] if data['WireMaintInt'] is not None else printer.WireMaintInt
        printer.LubeMaintInt = data['LubeMaintInt'] if data['LubeMaintInt'] is not None else printer.LubeMaintInt

        db.session.add(printer);
        db.session.commit();
        return printer




@api.route('/prints/<int:user_id>')
@api.doc(params={'user_id': 'ID of user to retrieve info for.'})
class PrintLibraryResp(Resource):
    @required_apikey
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
    @required_apikey
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

        if rows is None:
            return None, 404

        pt = rows.prints
        pt.PrinterId = rows.PrinterId
        pt.FilamentId = rows.FilamentId
        pt.FilamentName = "{0} {1} ({2}) - Spool {3}".format(rows.Brand, rows.Material, rows.ColorFamilyName, rows.UserFilamentId)
        pt.PrinterName = "{0} - Printer {1}".format(rows.PrinterName, rows.UserPrinterId)
        pt.MainPrintImageUrl = rows.MainPrintImageUrl

        http_resp = 404 if rows is None else 200
        return pt, http_resp

    @required_apikey
    @api.marshal_with(printDetailModel, envelope='data')
    def put(self, print_id):
        prnt = db.session.query(Print).filter(Print.PrintId == print_id).one_or_none();
        if prnt is None:
            return None, 404

        data = request.get_json()
        prnt.PrintName = data['PrintName'] if data['PrintName'] is not None else prnt.PrintName
        prnt.PrintDate = data['PrintDate'] if data['PrintDate'] is not None else prnt.PrintDate
        prnt.SourceUrl = data['SourceUrl'] if data['SourceUrl'] is not None else prnt.SourceUrl

        prnt.PrintTimeMinutes = data['PrintTimeMinutes'] if data['PrintTimeMinutes'] is not None else prnt.PrintTimeMinutes

        prnt.FilamentId = data['FilamentId'] if data['FilamentId'] is not None else prnt.FilamentId
        prnt.LengthUsed = data['LengthUsed'] if data['LengthUsed'] is not None else prnt.LengthUsed
        prnt.PrinterId = data['PrinterId'] if data['PrinterId'] is not None else prnt.PrinterId

        db.session.add(prnt)
        db.session.commit()
        return prnt

@api.route('/images/imagerequest')
class ImageRequestResp(Resource):
    def get(self):
        imgHandler = ImageHandler()
        presigned = imgHandler.get_presigned_post()
        data = {'data':presigned}
        return data

    def put(self):
        data = request.get_json()

        if data['PrintId'] is None and data['PrinterId'] is None:
            return {'data':'Bad request. PrintId or PrinterId needs to be populated.'}, 400
        elif data['PrintId'] is not None and data['PrinterId'] is not None:
            return {'data':'Bad request. Only one of PrintId or PrinterId can be populated.'}, 400
        elif data['PrintId'] is not None:
            entity = db.session.query(Print).filter(Print.PrintId == data['PrintId']).one_or_none()
        elif data['PrinterId'] is not None:
            entity = db.session.query(Printer).filter(Printer.PrinterId == data['PrinterId']).one_or_none()

        if entity is None:
            return None, 404

        img = entity.images
        imgHandler = ImageHandler()

        err = None
        if img is not None:
            try:
                delete_resp = imgHandler.delete_file_by_key(img.ImagePath[img.ImagePath.rfind('/')+1:])
            except:
                err = 'Error deleting image from S3'
        else:
            img = Image()
            img.PrintId = data['PrintId']
            img.PrinterId = data['PrinterId']

        img.ImagePath = data["ImageUrl"];
        db.session.add(img);
        db.session.commit();

        if entity.images is None:
            entity.images = img
            db.session.add(entity)
            db.session.commit()

        return {'data':'Image path updated', 'errors':err}, 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, ssl_context=('./certs/server.crt', './certs/server.key'))