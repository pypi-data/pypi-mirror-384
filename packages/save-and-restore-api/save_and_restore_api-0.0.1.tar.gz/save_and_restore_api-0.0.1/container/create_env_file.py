# import socket

if __name__ == "__main__":
    # Get the local IP address
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("8.8.8.8", 80))
    # ip = s.getsockname()[0]

    ip = "127.0.0.1"

    with open(".env", "w") as f:
        f.write(f"HOST_EXTERNAL_IP_ADDRESS={ip}")
