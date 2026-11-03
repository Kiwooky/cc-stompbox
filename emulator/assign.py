#!/usr/bin/env python3
"""Play the MOD web UI's part: assign parameters to every box that connects.

Connects to cc-master's socket (the same JSON API mod-ui uses). Whenever a box
registers — at startup, or when it reconnects after a mode switch — it reads
the box's layout and assigns to fit it:

  LIST mode  (one Encoder, one Footswitch): several parameters on the encoder,
             push the encoder to cycle; one bypass on the footswitch.
  PAGES mode (Encoder, Encoder 2, ... / Footswitch, Footswitch 2, ...):
             one parameter per page encoder and a different job per page
             footswitch (on a real Duo a parameter can sit on one control only).

Labels follow the "EFFECT|PARAM" convention (16 characters max). A footswitch
label without "|" is the Duo's default for a plugin's on/off control: just the
plugin name, value 1 = bypassed.

Usage: python3 assign.py   (start vbus.py, master.sh and the boxes first)
Ctrl-C removes the assignments and quits.
"""
import base64, json, os, queue, socket, struct, sys, threading, time

SOCK = "/tmp/control-chain.sock"
CC_MODE_TOGGLE, CC_MODE_REAL, CC_MODE_INTEGER = 0x001, 0x010, 0x020

# Encoder params: (label, min, max, value, unit). Footswitch: (label, is_bypass)
PLANS = [
    {   # first box to connect
        "encoder": [("CANABYSS|D-TIME", 20.0, 5000.0, 500.0, "ms"),
                    ("CANABYSS|FDBK", 0.0, 100.0, 40.0, "%"),
                    ("TAJMAHAL|DECAY", 0.5, 20.0, 4.0, "s")],
        "footswitch": [("TajMahal", True), ("CanAbyss", True), ("CANABYSS|FREEZE", False)],
    },
    {   # second box
        "encoder": [("GRUFFDRV|GAIN", 0.0, 10.0, 6.0, ""),
                    ("TAJMAHAL|MIX", 0.0, 100.0, 30.0, "%")],
        "footswitch": [("GruffDrv", True), ("MOBYWAH|LATCH", False)],
    },
]


class Master:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(path)
        self.buf = b""
        self.replies = []
        self.cond = threading.Condition()
        self.on_event = None
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        while True:
            chunk = self.s.recv(8192)
            if not chunk:
                print("\nMaster closed the connection.")
                os._exit(1)
            self.buf += chunk
            while b"\x00" in self.buf:
                msg, self.buf = self.buf.split(b"\x00", 1)
                if not msg:
                    continue
                obj = json.loads(msg.decode())
                if "event" in obj:
                    if self.on_event:
                        self.on_event(obj)
                else:
                    with self.cond:
                        self.replies.append(obj)
                        self.cond.notify()

    def request(self, name, data=None, timeout=5.0):
        self.s.sendall(json.dumps({"request": name, "data": data}).encode() + b"\x00")
        with self.cond:
            end = time.time() + timeout
            while True:
                for i, r in enumerate(self.replies):
                    if r.get("reply") == name:
                        return self.replies.pop(i).get("data")
                left = end - time.time()
                if left <= 0:
                    raise TimeoutError(f"no reply to '{name}'")
                self.cond.wait(left)


def controls_by_page(desc):
    """Group the descriptor's actuators into pages: [(encoder_id, footswitch_id), ...]."""
    encs = sorted(a["id"] for a in desc.get("actuators", []) if a["name"].lower().startswith("encoder"))
    fss = sorted(a["id"] for a in desc.get("actuators", []) if a["name"].lower().startswith("footswitch"))
    return list(zip(encs, fss)), {a["id"]: a for a in desc.get("actuators", [])}


def enc_assignment(dev, act, p):
    label, lo, hi, val, unit = p
    return {"device_id": dev, "actuator_id": act, "label": label, "value": val, "min": lo,
            "max": hi, "def": val, "mode": CC_MODE_REAL, "steps": 0, "unit": unit, "options": []}


def fs_assignment(dev, act, p):
    label, bypass = p
    return {"device_id": dev, "actuator_id": act, "label": label, "value": 0.0, "min": 0.0,
            "max": 1.0, "def": 0.0, "mode": CC_MODE_TOGGLE | CC_MODE_INTEGER, "steps": 0,
            "unit": "", "options": []}


def main():
    try:
        m = Master(SOCK)
    except (FileNotFoundError, ConnectionRefusedError):
        sys.exit("Can't reach the master. Start it first:  ./master.sh")

    labels = {}        # (device_id, assignment_id) -> (label, unit)
    made = {}          # device_id -> [assignment_id, ...]
    plan_of = {}       # device_id -> plan index
    todo = queue.Queue()

    def on_event(ev):
        d = ev["data"]
        if ev["event"] == "data_update":
            dev = d["device_id"]
            raw = base64.b64decode(d["raw_data"])
            count, body = raw[0], raw[1:]
            for i in range(count):
                aid, val = struct.unpack("<Bf", body[i * 5:i * 5 + 5])
                label, unit = labels.get((dev, aid), (f"assignment {aid}", ""))
                print(f"  device {dev}  {label:<16} -> {val:8.2f} {unit}", flush=True)
        elif ev["event"] == "device_status":
            dev = d.get("device_id")
            if d.get("status"):
                print(f"  [device {dev} connected]", flush=True)
                todo.put(dev)
            else:
                print(f"  [device {dev} gone]", flush=True)
                made.pop(dev, None)

    m.on_event = on_event
    m.request("data_update", {"enable": 1})
    m.request("device_status", {"enable": 1})
    for dev in sorted(m.request("device_list") or []):
        todo.put(dev)

    def assign_box(dev):
        if dev in made:
            return
        desc = m.request("device_descriptor", {"device_id": dev}) or {}
        pages, acts = controls_by_page(desc)
        if not pages:
            return
        # a box that reconnects gets the plan it had before (lowest free one otherwise)
        if dev not in plan_of:
            used = set(plan_of.values())
            plan_of[dev] = next((i for i in range(len(PLANS)) if i not in used), len(plan_of) % len(PLANS))
        plan = PLANS[plan_of[dev]]
        mode = "PAGES" if len(pages) > 1 else "LIST"
        print(f"\n  device {dev} ({desc.get('label', '?')}) — {mode} mode, "
              f"{len(pages)} page(s), encoder holds {acts[pages[0][0]].get('max_assignments', 1)}")

        wanted = []
        if mode == "LIST":
            enc, fs = pages[0]
            cap = acts[enc].get("max_assignments", 1)
            wanted += [enc_assignment(dev, enc, p) for p in plan["encoder"][:cap]]
            wanted.append(fs_assignment(dev, fs, plan["footswitch"][0]))
        else:
            for i, (enc, fs) in enumerate(pages):
                if i < len(plan["encoder"]):
                    wanted.append(enc_assignment(dev, enc, plan["encoder"][i]))
                if i < len(plan["footswitch"]):
                    wanted.append(fs_assignment(dev, fs, plan["footswitch"][i]))

        made[dev] = []
        for a in wanted:
            name = acts[a["actuator_id"]]["name"]
            reply = m.request("assignment", a) or {}
            aid = reply.get("assignment_id", -1)
            if aid < 0:
                print(f"    {name:<13} <- {a['label']}  FAILED ({reply})")
                continue
            labels[(dev, aid)] = (a["label"], a["unit"])
            made[dev].append(aid)
            print(f"    {name:<13} <- {a['label']}")
        print("", flush=True)

    print("Assigning boxes as they connect. In a box tab: + / - turn, p push, d double-click,")
    print("l long press (settings), f stomp. Value changes appear here. Ctrl-C to quit.\n", flush=True)
    try:
        while True:
            try:
                dev = todo.get(timeout=0.5)
            except queue.Empty:
                continue
            time.sleep(0.3)   # let the master finish registering the box
            try:
                assign_box(dev)
            except TimeoutError as e:
                print(f"  device {dev}: {e}")
    except KeyboardInterrupt:
        print("\nRemoving assignments...")
        for dev, ids in made.items():
            for aid in ids:
                try:
                    m.request("unassignment", {"device_id": dev, "assignment_id": aid,
                                               "assignment_pair_id": -1}, timeout=2)
                except TimeoutError:
                    pass
        print("Done.")


if __name__ == "__main__":
    main()
