from flask import request
from iMES import app


@app.route("/GetNormDocumentation", methods=['POST'])
def GetNormDocumentation():
    request_data = request.get_json()
    print(request_data)

    return 'Insert success.'
