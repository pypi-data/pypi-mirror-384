# (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

import time

import aria.sdk_gen2 as sdk_gen2


def device_auth():
    # Set up the device client to initiate connection to the device
    device_client = sdk_gen2.DeviceClient()
    # Set up the device client config to specify the device to be connected to e.g. device serial number.
    # If nothing is specified, the first device in the list of connected devices will be connected to
    config = sdk_gen2.DeviceClientConfig()
    device_client.set_client_config(config)

    # Authenticate the device and wait for the user to open the Aria app to accept the pairing request
    print(
        "Authenticating device. Please open the Aria app and accept the pairing request"
    )
    device_client.authenticate()
    time.sleep(5)

    # check if the device is authenticated so the the connection can be established
    try:
        device = device_client.connect()
        print(f"Device authentication successful to device {device.connection_id()}")
    except Exception:
        print(f"Failed to authenticate and connect to device")
        return


if __name__ == "__main__":
    device_auth()
