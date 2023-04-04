from phew import server, logging, connect_to_wifi
from phew import render_template

import secrets

import re

from tt import TT

tt = TT()

ip = connect_to_wifi(secrets.wlan_ssid, secrets.wlan_password)
logging.info(f"Connected, IP: {ip}")

@server.route("/", methods=["GET"])
def index(request):
    return await render_template("index.html", byte_out="-", byte_in="00000000", design_num="9")

@server.route("/send_byte", methods=["GET", "POST"])
def send_byte(request):
    byte_in = request.query.get("byte_in", "")
    design_num = int(request.query.get("design_num", 2))
    clock = request.query.get("clock", "off") == "on"

    if re.search(r"[^01]", byte_in):
        logging.warn(f"Input byte must only contain 0s and 1s, it was \"{byte_in}\" replacing with 0")
        byte_in = "00000000"

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

    if clock:
        b &= 0xFE
        logging.info(f"Sending byte {b:08b} to design {design_num}")
        byte_out = tt.send_receive_byte(b, design_num)
        logging.debug(f"Received byte {byte_out:08b} from design {design_num}")
        b |= 1
    
    logging.info(f"Sending byte {b:08b} to design {design_num}")
    byte_out = tt.send_receive_byte(b, design_num)
    byte_out = "{:08b}".format(byte_out)
    logging.info(f"Received byte {byte_out} from design {design_num}")

    return await render_template("index.html", design_num=str(design_num), byte_in=original_byte_in, byte_out=byte_out, clock="checked" if clock else "")

# catchall example
@server.catchall()
def catchall(request):
  return "Not found", 404

@server.route("/ttlogo.png")
def logo(request):
    return server.FileResponse("ttlogo.png", headers={"Cache-Control": "max-age=3600"})

# start the webserver
server.run()
