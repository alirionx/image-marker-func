from flask import Flask, request, jsonify
from PIL import Image, ImageFont, ImageDraw
from minio import Minio 
from datetime import datetime
from io import BytesIO
import uuid
import platform
import os


app = Flask(__name__)

#----------------------------------------
# Just a Test
@app.route("/", methods=["GET"] )
def main_get():
    res = request.args.to_dict()
    return jsonify(res)

#---------------
@app.route("/image", methods=["POST"] )
def main():
    info_str = request.form.get("info", "")
    image_id = str(uuid.uuid4())
    upload_timestamp = str(datetime.now())

    file = request.files['file']
    fl_bytes = BytesIO()
    file.save(fl_bytes)

    #-----------------
    image = Image.open(fl_bytes) 
    if image.width > 1000: font_size = 48
    else: font_size = 24
    spacer = font_size + 10

    draw = ImageDraw.Draw(image) 
    if platform.system() == "Windows":
        font = ImageFont.truetype(font="C:\\Windows\\Boot\\Fonts\malgun_boot.ttf", size=font_size)
    else:
        font = ImageFont.truetype(font="/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf", size=font_size)

    input_meta = {
        "id": image_id,
        "filename": file.filename,
        "info": info_str,
        "size": len(fl_bytes.getvalue()),
        "uploaded": upload_timestamp
    }

    i = 10
    for key,val in input_meta.items():
        try:
            draw.text( (10, i), "%s: %s" %(key,val), align ="left", fill="black", font=font ) 
            i += spacer
        except:
            inf = "never mind ;)"

    # image.save("test.jpg", format="JPEG")
    #-----------------
    bucket_name = os.environ.get("MINIO_BUCKET_NAME", "images")
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key = os.environ.get("MINIO_ACCESS_KEY", "minio")
    minio_secret_key = os.environ.get("MINIO_SECRET_KEY", "password")
    minio_cli = Minio(
        endpoint=minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False
    )

    payload = BytesIO()
    image.save(payload, format="JPEG")
    payload.seek(0)
    payload_len = len(payload.getvalue())
    
    if not minio_cli.bucket_exists(bucket_name):
        minio_cli.make_bucket(bucket_name)
    
    minio_cli.put_object(
        bucket_name=bucket_name, 
        object_name= "%s.jpeg"%image_id,
        data=payload,
        length=payload_len
    )

    #-----------------
    return jsonify(input_meta)


#----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)