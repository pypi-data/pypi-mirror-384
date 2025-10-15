def ascii_to_hex(text):
    text2 = text.decode("latin1")
    hex_bytes = [hex(ord(char))[2:].zfill(2) for char in text2] # Use zfill(2) to pad with zeros
    return ''.join(hex_bytes)  