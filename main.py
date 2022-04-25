from flask import Flask, jsonify, Response
from flask import abort, redirect
from flask import request
import pymongo
import json
from bson.objectid import ObjectId
'''
POST:localhost/urlshorten
Body:<form-data> Key:url VALUE:https://a.very-long.url/foo?lorem=ipsum4433326
'''
_url_start_ = "000000"#the start of the url
_url_prefix = "https://foo.bar/"

DB_PRESENT_KEY = "present"
DB_ORIGINURL_KEY = "original_url"
DB_SHORTENURL_KEY = "short_url"
DB_COUNT_KEY = "count"

app = Flask(__name__)
################################################
#MongoDB initialization
try:
    local = pymongo.MongoClient("mongodb://localhost:27017/")
    url_db = local.url_base
    local.server_info()  # trigger exception if cannot connect to db
    present_url = url_db.lefturl.find_one()
    if present_url is None: # first time boot
        present_url = _url_prefix+_url_start_
        url_db.lefturl.insert_one({DB_PRESENT_KEY:present_url})
except Exception as ex:
    print(ex)
    print("Error, can't connect to db")

################################################
# Find the next alphanumeric characters
def ascii_add_one(url_ascii,index):

    if index>6:
        # out of useable characters
        return "error"
    url_ascii[index] += 1
    asciin = url_ascii[index]
    '''
    ASCII CODE
    0-9:48-57
    A-Z:65-90
    a-z:97-122
    '''
    if asciin>58 and asciin<65:
        url_ascii[index] = 65
    elif asciin>90 and asciin<97:
        url_ascii[index] = 97
    elif asciin>122:
        # carry 'digit'
        url_ascii[index] = 0
        ascii_add_one(url_ascii, index-1)

#update useable url base
def update_used_url(present_url):
    # convert the current url into a ASCII code list
    url_ascii = [ord(present_url[i]) for i in range(6)]
    # get the next alphanumeric characters' ASCII code list
    ascii_add_one(url_ascii, 5)
    # convert back to string
    new_url = ""
    for i in range(6):
        new_url += chr(url_ascii[i])
    # update the useable url base
    url_db.lefturl.update_one({DB_PRESENT_KEY:_url_prefix+present_url},
                              {"$set": {DB_PRESENT_KEY: _url_prefix+new_url}})


# transfer url
def create_new_url(present_url):
    # update useable url base
    update_used_url(present_url)
    # update shortened urls base
    url_data = {DB_SHORTENURL_KEY:present_url,
            DB_ORIGINURL_KEY:request.form["url"],
            DB_COUNT_KEY:1
            }

    db_response = url_db.urls.insert_one(url_data)
    print(db_response.inserted_id)
    return url_data

if __name__ == "__main__":
    @app.route("/urlshorten", methods=["POST"])
    def shorten_url():
        try:
            # get the current usable charaters
            present_url = url_db.lefturl.find_one()[DB_PRESENT_KEY][len(_url_prefix):]
            print(present_url)
            # try find the if the url in the db
            find_url = url_db.urls.find_one({DB_ORIGINURL_KEY: request.form["url"]})
            if find_url is None:
                # url not in db, is a new url, insert into the db
                url_data=create_new_url(present_url)
                return Response(
                    response=json.dumps({"original": url_data[DB_ORIGINURL_KEY],
                                         "short": _url_prefix+url_data[DB_SHORTENURL_KEY],
                                         "count": url_data[DB_COUNT_KEY]
                                         }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                # url is in db, update the db
                dbResponse = url_db.urls.update_one(
                    {DB_ORIGINURL_KEY: find_url[DB_ORIGINURL_KEY]},
                    {"$set": {DB_COUNT_KEY: find_url[DB_COUNT_KEY]+1}}
                )

                return Response(
                    response=json.dumps({"original": find_url[DB_ORIGINURL_KEY],
                                         "short":_url_prefix+find_url[DB_SHORTENURL_KEY],
                                         "count":find_url[DB_COUNT_KEY]+1
                                         }),
                    status=200,
                    mimetype="application/json"
                )
        except Exception as ex:
            # parse error
            print("********************")
            print(ex)
            print("********************")

            return Response(
                response=json.dumps({"message": "URL parse error"}),
                status=500,
                mimetype="application/json"
            )

    #validate the duplicate data
    @app.route("/validate", methods=["GET"])
    def validate_duplicate():
        try:
            dup = False
            data = list(url_db.urls.find())
            url_set = set()
            dup_dict = dict()
            for url in data:

                if url[DB_SHORTENURL_KEY] in url_set:
                    # same url shows more than ones
                    dup = True
                    if _url_prefix+url[DB_SHORTENURL_KEY] in dup_dict:
                        dup_dict[_url_prefix + url[DB_SHORTENURL_KEY]] += 1
                    else:
                        dup_dict[_url_prefix+url[DB_SHORTENURL_KEY]] = 2
                url_set.add(url[DB_SHORTENURL_KEY])

            if dup:
                print("duplicate urls: ", dup_dict)
                return Response(
                        response=json.dumps({"message": f"Found duplicate urls:{dup_dict}"}),
                        status=200,
                        mimetype="application/json"
                )
            #not found
            return Response(
                response=json.dumps({"message": "No duplicate shorten url"}),
                status=200,
                mimetype="application/json"
            )
        except Exception as ex:
            print(ex)
            return Response(
                response=json.dumps({"message": "database validate error"}),
                status=500,
                mimetype="application/json"
            )

    # update the original url base using the shortened url
    @app.route("/update", methods=["PATCH"])
    def update_url():
        try:
            # first check if the url is in the base
            data = list(url_db.urls.find({DB_SHORTENURL_KEY:request.form[DB_SHORTENURL_KEY][-6:]}))
            if not data:
                return Response(
                    response=json.dumps({"error": "url not found"}),
                    status=200,
                    mimetype="application/json"
                )
            # check if the target url is already in the base, prevent duplicate urls.
            data = list(url_db.urls.find({DB_ORIGINURL_KEY:request.form[DB_ORIGINURL_KEY]}))
            if data:
                return Response(
                    response=json.dumps({"error": "the target url has been found in the base"}),
                    status=200,
                    mimetype="application/json"
                )
            # update the url
            dbResponse = url_db.urls.update_one(
                {DB_SHORTENURL_KEY:request.form[DB_SHORTENURL_KEY]},
                {"$set":{DB_ORIGINURL_KEY:request.form[DB_ORIGINURL_KEY]}}
            )
            # check if anything changed
            if dbResponse.modified_count == 0:
                return Response(
                    response=json.dumps({"message": "same data"}),
                    status=200,
                    mimetype="application/json"
                )

            return Response(
                response=json.dumps({"message": "url updated"}),
                status=200,#200 ok response
                mimetype="application/json"
            )

        except Exception as ex:
            print("################")
            print(ex)
            return Response(
                response=json.dumps({"message":"sorry cannot update url"}),
                status=500,
                mimetype="application/json"
            )

    # backup and delete the url data using the shortened url
    @app.route("/update", methods=["DELETE"])
    def delete_url():
        try:
            # get data first
            data = url_db.urls.find_one({DB_SHORTENURL_KEY:request.form[DB_SHORTENURL_KEY][-6:]})
            # backup in the deleted base
            url_db.deleted.insert_one(data)
            # delete the url
            dbResponse = url_db.urls.delete_one({DB_SHORTENURL_KEY:request.form[DB_SHORTENURL_KEY][-6:]})
            if dbResponse.deleted_count == 1:
                return Response(
                response=json.dumps({"message": f"url {request.form[DB_SHORTENURL_KEY]} deleted"}),
                status=200,#200 ok response
                mimetype="application/json"
            )
        except Exception as ex:
            print("################")
            print(ex)
            return Response(
                response=json.dumps({"message": "sorry cannot delete url"}),
                status=500,
                mimetype="application/json"
            )
    app.run(port=80, debug=True, host="0.0.0.0")

