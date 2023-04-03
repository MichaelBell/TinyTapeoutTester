import hovalaag_asm

def assemble(text):
    return hovalaag_asm.assemble(tuple(text.split("\n")))