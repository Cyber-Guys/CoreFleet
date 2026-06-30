import argparse
import json
import os
import signal
import threading

import zenoh

KEY_PREFIX = 'core/fleet'

def build_config(router: str) -> zenoh.Config:
    config = zenoh.Config()
    config.insert_json5("mode", json.dumps("client"))
    config.insert_json5("connect/endpoints", json.dumps([router]))
    config.insert_json5("scouting/multicast/enabled", json.dumps(False))
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Subscribe to random data from Zenoh publishers")
    parser.add_argument("--router", default=os.getenv("ZENOH_ROUTER", "tcp/zenoh-router:7447"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stop_event = threading.Event()

    def handle_signal(_signum, _frame) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    zenoh.init_log_from_env_or("info")
    config = build_config(args.router)

    with zenoh.open(config) as session:
        def on_alive(sample: zenoh.Sample) -> None:
            payload = sample.payload.to_string()
            print(f'[+] Alive vehicle: {payload}', flush=True)

        def on_dead(sample: zenoh.Sample) -> None:
            payload = sample.payload.to_string()
            print(f'[-] Dead vehicle: {payload}', flush=True)

        print(f"subscribing to {KEY_PREFIX}/alive via {args.router}", flush=True)
        with session.declare_subscriber(f"{KEY_PREFIX}/alive", on_alive):
            stop_event.wait()
        print(f"subscribing to {KEY_PREFIX}/dead via {args.router}", flush=True)
        with session.declare_subscriber(f"{KEY_PREFIX}/dead", on_dead):
            stop_event.wait()


if __name__ == "__main__":
    main()