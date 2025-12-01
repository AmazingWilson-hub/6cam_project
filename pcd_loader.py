import numpy as np
import re
import struct

def load_pcd(file_path):
    """
    Loads a PCD file (ASCII or Binary) and returns points as a numpy array.
    Supports only 'x y z' or 'x y z rgb' fields for now.
    """
    with open(file_path, 'rb') as f:
        header = []
        while True:
            line = f.readline().decode('ascii').strip()
            header.append(line)
            if line.startswith('DATA'):
                break
        
        # Parse header
        header_map = {}
        for line in header:
            parts = line.split()
            header_map[parts[0]] = parts[1:]
            
        data_type = header_map['DATA'][0]
        points_count = int(header_map['POINTS'][0])
        
        # Determine fields and size
        fields = header_map['FIELDS']
        # We only care about x, y, z
        try:
            x_idx = fields.index('x')
            y_idx = fields.index('y')
            z_idx = fields.index('z')
        except ValueError:
            raise ValueError("PCD file must contain x, y, z fields")
            
        if data_type == 'binary':
            # Assuming float32 (4 bytes) for x, y, z. Check SIZE and TYPE if needed.
            # Usually PCD binary is just raw bytes.
            # We need to know the full point size (stride)
            sizes = [int(s) for s in header_map['SIZE']]
            point_step = sum(sizes)
            
            raw_data = f.read(points_count * point_step)
            # Use numpy to read
            # Create a dtype based on fields
            # This is a simplification, assuming standard float32 for xyz
            dt = np.dtype(np.float32)
            
            # If the structure is complex, we might need a structured array
            # But for standard Ouster/Velodyne PCDs, it's usually float32 x, y, z, ...
            
            # Let's try to read as structured array
            # Construct dtype list
            dtype_list = []
            types_map = {'F': 'f', 'I': 'i', 'U': 'u'}
            for i, field in enumerate(fields):
                t = header_map['TYPE'][i]
                s = int(header_map['SIZE'][i])
                dtype_list.append((field, f'{types_map[t]}{s}'))
                
            data = np.frombuffer(raw_data, dtype=dtype_list)
            
            # Extract x, y, z
            points = np.stack([data['x'], data['y'], data['z']], axis=-1)
            return points.astype(np.float32)

        elif data_type == 'ascii':
            data = np.loadtxt(f)
            return data[:, [x_idx, y_idx, z_idx]].astype(np.float32)
            
        else:
            raise ValueError(f"Unsupported DATA type: {data_type}")

if __name__ == "__main__":
    # Test
    import sys
    if len(sys.argv) > 1:
        pts = load_pcd(sys.argv[1])
        print(f"Loaded {len(pts)} points")
        print(pts[:5])
