import struct

MAGIC = b'PXDB'

def create_db(filename, rows, cols):
    with open(filename, 'wb') as f:
        f.write(MAGIC)
        f.write(struct.pack('<HH', rows, cols))
        
def append_cell(filename, row, col, text):
    data = text.encode('utf-8')
    with open(filename, 'ab') as f:
        f.write(struct.pack('<HHH', row, col, len(data)))
        f.write(data)
    
def read_cell(filename, row, col):
    with open(filename, 'rb') as f:
        magic = f.read(4)
        if magic != b'PXDB':
            raise Exception("File is not exiting")
        rows, cols = struct.unpack('<HH', f.read(4))
        while True:
            chunk = f.read(6)
            if not chunk:
                break
            r, c, length = struct.unpack('<HHH', chunk)
            data = f.read(length).decode('utf-8')
            if r == row and c == col:
                return data
    return None
def read_all(filename):
    data = {}
    with open(filename, 'rb') as f:
        if f.read(4) != MAGIC:
            raise Exception("❌ Invalid file")
        rows, cols = struct.unpack('<HH', f.read(4))
        while True:
            chunk = f.read(6)
            if not chunk:
                break
            r, c, length = struct.unpack('<HHH', chunk)
            text = f.read(length).decode('utf-8')
            data[(r, c)] = text
    return data, rows, cols
