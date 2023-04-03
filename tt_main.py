from phew import server, connect_to_wifi
from phew import render_template

import secrets

import re

from tt import TT

tt = TT()

ip = connect_to_wifi(secrets.wlan_ssid, secrets.wlan_password)
print(ip)

@server.route("/", methods=["GET"])
def index(request):
    return await render_template("index.html", byte_out="", byte_in="00000000", design_num="9")

@server.route("/send_byte", methods=["GET", "POST"])
def send_byte(request):
    byte_in = ""
    if "byte_in" in request.query: byte_in = request.query["byte_in"]
    elif "byte_in" in request.form: byte_in = request.form["byte_in"]

    design_num = 2
    if "design_num" in request.query: design_num = int(request.query["design_num"])
    if "design_num" in request.form: design_num = int(request.form["design_num"])

    print(byte_in, design_num)
    if re.search(r"[^01]", byte_in):
        byte_in = "00000000"
    print(byte_in, design_num)

    b = 0
    byte_in = "00000000" + byte_in
    if len(byte_in) > 8: byte_in = byte_in[-8:]
    original_byte_in = byte_in
    for i in range(8):
        b <<= 1
        if len(byte_in) == 0:
            break

        if byte_in[0] == "1":
            b += 1
        byte_in = byte_in[1:]
    print(b, design_num)

    byte_out = tt.send_receive_byte(b, design_num)
    print(byte_out)
    byte_out = "{0:b}".format(byte_out)

    return await render_template("index.html", design_num=str(design_num), byte_in=original_byte_in, byte_out=byte_out)

# catchall example
@server.catchall()
def catchall(request):
  return "Not found", 404

@server.route("/ttlogo.png")
def logo(request):
    return server.serve_file("ttlogo.png")

# start the webserver
server.run()
