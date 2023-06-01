from flask import jsonify

from app.main import error


@error.app_errorhandler(400)
def errorhandler(error):
    return jsonify(code=400, message="参数错误")