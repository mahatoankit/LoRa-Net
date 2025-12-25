import serial
import pynmea2

def read_gps():
    # Open serial port (NEO-6M default baudrate 9600)
    with serial.Serial('/dev/serial0', baudrate=9600, timeout=1) as ser:
        try:
            line = ser.readline().decode('ascii', errors='replace').strip()
            if line.startswith('$'):
                try:
                    msg = pynmea2.parse(line)
                    if isinstance(msg, pynmea2.types.talker.RMC):
                        if msg.status == 'A':  # 'A' means valid fix
                            if __name__ == "__main__":
                                print(f"Time UTC: {msg.timestamp}")
                                print(f"Latitude: {msg.latitude} {msg.lat_dir}")
                                print(f"Longitude: {msg.longitude} {msg.lon_dir}")
                                print(f"Speed (knots): {msg.spd_over_grnd}")
                                print(f"Date: {msg.datestamp}")
                                print("-" * 20)
                            return {
                                'time':msg.timestamp,
                                'latitude': f"{msg.latitude} {msg.lat_dir}",
                                'longtitude':f"{msg.longitude} {msg.lon_dir}",
                                'speed': msg.spd_over_grnd,
                                'date': msg.datestamp
                            }
                        else:
                            return None
                except pynmea2.ParseError:
                    # Ignore parsing errors
                    return None
        except serial.SerialException as e:
            print("Serial Exception: ", e)
            return None
if __name__ == '__main__':
    read_gps()
