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

from helpers.helper_methods import *

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

@api.route('/filaments/create')
class FilamentCreateResp(Resource):
    @required_apikey
    @api.marshal_with(filamentDetailModel, envelope='data')
    def post(self):
        data = request.get_json()

        max_filament_id = db.session.query(db.func.max(Filament.UserFilamentId).label('max_id'))\
                                    .filter(Filament.UserId == data['UserId'])\
                                    .one()
        filament = Filament()
        filament.Brand = data['Brand']
        filament.Material = data['Material']
        filament.LengthRemain = data['LengthRemain']
        filament.ColorFamilyId = data['ColorId']
        filament.DateAcquired = data['DateAcquired']
        filament.FilamentSource = data['FilamentSource']
        filament.HtmlColor = data['HtmlColor']
        filament.UserId = data['UserId']
        filament.UserFilamentId = max_filament_id.max_id + 1

        db.session.add(filament)
        db.session.commit()

        return filament


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

        printer.PrinterName = data['PrinterName']
        printer.DateAcquired = data['DateAcquired']

        printer.PrinterSource = extract_optional(data, 'PrinterSource')
        printer.BeltMaintInt = extract_optional(data,'BeltMaintInt')
        printer.WireMaintInt = extract_optional(data,'WireMaintInt')
        printer.LubeMaintInt = extract_optional(data,'LubeMaintInt')

        db.session.add(printer)
        db.session.commit()
        return printer

@api.route('/printers/create')
class PrinterCreateResp(Resource):
    @required_apikey
    @api.marshal_with(printerDetailModel, envelope='data')
    def post(self):
        data = request.get_json()
        max_printer_id = db.session.query(db.func.max(Printer.UserPrinterId).label('max_id'))\
            .filter(Printer.UserId == data['UserId'])\
            .one()

        printer = Printer()
        printer.PrinterName = data['PrinterName']
        printer.DateAcquired = data['DateAcquired']
        printer.PrinterSource = extract_optional(data, 'PrinterSource')
        printer.BeltMaintInt = data['BeltMaintInt']
        printer.WireMaintInt = data['WireMaintInt']
        printer.LubeMaintInt = data['LubeMaintInt']
        printer.UserPrinterId = max_printer_id.max_id + 1
        printer.PrintTimeHours = 0
        printer.NumberOfPrints = 0
        printer.UserId = data['UserId']

        db.session.add(printer)
        db.session.commit()

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
        prnt = db.session.query(Print).filter(Print.PrintId == print_id).one_or_none()
        if prnt is None:
            return None, 404

        data = request.get_json()
        prnt.PrintName = data['PrintName']
        prnt.PrintDate = data['PrintDate']

        prnt.SourceUrl = extract_optional(data, 'SourceUrl')
        if 'Success' not in data:
            prnt.Success = False
        else:
            prnt.Success = data['Success']

        old_time = prnt.PrintTimeMinutes
        new_time = data['PrintTimeMinutes']
        prnt.PrintTimeMinutes = data['PrintTimeMinutes']

        old_length = prnt.LengthUsed
        new_length = data['LengthUsed']
        prnt.LengthUsed = data['LengthUsed']

        new_filament = False
        new_printer = False
        if prnt.FilamentId == data['FilamentId'] and old_length != new_length:
            prnt.filaments.LengthRemain = add_quantity(old_length,prnt.filaments.LengthRemain)
            prnt.filaments.LengthRemain = remove_quantity(new_length,prnt.filaments.LengthRemain)
        elif prnt.FilamentId != data['FilamentId']:
            prnt.filaments.LengthRemain = add_quantity(old_length,prnt.filaments.LengthRemain)
            prnt.FilamentId = data['FilamentId']
            new_filament = True

        if prnt.PrinterId == data['PrinterId'] and new_time != old_time:
            prnt.printers.PrintTimeHours = remove_quantity(old_time/60,prnt.printers.PrintTimeHours)
            prnt.printers.PrintTimeHours = add_quantity(new_time/60,prnt.printers.PrintTimeHours)
        elif prnt.PrinterId != data['PrinterId']:
            prnt.printers.PrintTimeHours = remove_quantity(old_time,prnt.printers.PrintTimeHours)
            prnt.PrinterId = data['PrinterId']
            new_printer = True

        db.session.add(prnt)
        db.session.commit()

        if new_filament:
            prnt.filaments.LengthRemain = remove_quantity(new_length,prnt.filaments.LengthRemain)
            db.session.add(prnt.filaments)
        if new_printer:
            prnt.printers.PrintTimeHours = add_quantity(new_time/60,prnt.printers.PrintTimeHours)
            db.session.add(prnt.printers)
        if new_filament or new_printer:
            db.session.commit()

        return prnt

    @required_apikey
    def delete(self, print_id):
        user_id = request.headers.get('UserId')
        n_Deletes = db.session.query(Print).filter(Print.PrintId == print_id and Print.UserId == user_id).delete()

        db.session.commit()

        return {'data': n_Deletes}


@api.route('/prints/create')
class PrintCreateResp(Resource):
    @required_apikey
    @api.marshal_with(printDetailModel, envelope='data')
    def post(self):
        data = request.get_json()

        prnt = Print()
        prnt.UserId = data['UserId']
        prnt.PrintName = data['PrintName']
        prnt.PrintDate = data['PrintDate']
        prnt.FilamentId = data['FilamentId']
        prnt.LengthUsed = data['LengthUsed']
        prnt.PrinterId = data['PrinterId']
        prnt.PrintTimeMinutes = data['PrintTimeMinutes']

        # optional fields
        if 'SourceUrl' in data:
            prnt.SourceUrl = data['SourceUrl']
        if 'Success' in data:
            prnt.Success = data['Success']

        db.session.add(prnt)
        db.session.commit()

        filament = prnt.filaments
        filament.LengthRemain = remove_quantity(prnt.LengthUsed, filament.LengthRemain)
        db.session.add(filament)

        printer = prnt.printers
        printer.PrintTimeHours = add_quantity(prnt.PrintTimeMinutes/60, printer.PrintTimeHours)
        printer.NumberOfPrints = add_quantity(1, printer.NumberOfPrints)
        db.session.add(printer)

        db.session.commit()
        return prnt

@api.route('/images/imagerequest')
class ImageRequestResp(Resource):
    @required_apikey
    def get(self):
        imgHandler = ImageHandler()
        presigned = imgHandler.get_presigned_post()
        data = {'data':presigned}
        return data

    @required_apikey
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
        else:
            entity = None

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

        img.ImagePath = data["ImageUrl"]
        db.session.add(img)
        db.session.commit()

        if entity.images is None:
            entity.images = img
            db.session.add(entity)
            db.session.commit()

        return {'data':'Image path updated', 'errors':err}, 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, ssl_context=('./certs/server.crt', './certs/server.key'))