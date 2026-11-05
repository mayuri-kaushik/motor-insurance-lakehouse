"""
Synthetic data generator - UK Motor Insurance Lakehouse (portfolio project)

Produces 30 days of source data with deliberate real-world problems:
  - reference data: products, brokers (one broker missing -> inferred member later)
  - policy admin daily extracts: policyholder + policy (new and changed rows per day -> SCD2 later)
  - broker premium bordereaux (CSV): duplicates, leading-zero broker codes,
    a new column from day 10, a late file, an unknown broker
  - claims events (JSON lines): lifecycle events, some arriving late / out of order
  - skew: one broker holds ~40% of policies (performance lab)

Run in a Databricks notebook:
    %pip install faker
    BASE = "/Volumes/<catalog>/landing/raw"     # a Unity Catalog volume
    %run ./generate_data   (or paste and call main(BASE))
Run locally:
    python generate_data.py ./out
"""
import csv
import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from faker import Faker

SEED = 42
START = date(2026, 1, 1)
DAYS = 30
N_POLICYHOLDERS = 20_000
N_POLICIES = 30_000
IPT_RATE = Decimal("0.12")          # UK Insurance Premium Tax (standard rate)
COMMISSION_RATE = Decimal("0.10")
SKEWED_BROKER = "00007"             # ~40% of policies -> skew for the performance lab
UNKNOWN_BROKER = "00999"            # appears in bordereaux, NOT in ref_broker -> inferred member
NEW_COLUMN_DAY = 10                 # bordereaux gain 'payment_method' from this day
LATE_FILE_DAY = 15                  # this day's bordereau is written to a 'late' folder
DUPLICATE_RATE = 0.01
CLAIM_RATE = 0.05
OUT_OF_ORDER_RATE = 0.03

PRODUCTS = [
    ("P01", "Comprehensive"),
    ("P02", "Third Party Fire and Theft"),
    ("P03", "Third Party Only"),
    ("P04", "Telematics Comprehensive"),
]
COVER_PREMIUM = {"P01": (450, 1400), "P02": (380, 1100), "P03": (300, 900), "P04": (400, 1200)}
VEHICLES = ["Ford Fiesta", "VW Golf", "Vauxhall Corsa", "Toyota Yaris", "BMW 3 Series",
            "Nissan Qashqai", "Kia Sportage", "Tesla Model 3", "Audi A3", "Mini Cooper"]


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def day_str(d: date) -> str:
    return d.strftime("%Y%m%d")


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_jsonl(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")


def main(base: str):
    random.seed(SEED)
    fake = Faker("en_GB")
    Faker.seed(SEED)

    # ---------- reference data ----------
    brokers = [f"{i:05d}" for i in range(1, 26)]           # leading zeros on purpose
    write_csv(f"{base}/reference/ref_product.csv",
              ["product_code", "product_name"], PRODUCTS)
    write_csv(f"{base}/reference/ref_broker.csv",
              ["broker_code", "broker_name", "region"],
              [(b, f"{fake.company()} Insurance Brokers",
                random.choice(["London", "South East", "North West", "Midlands", "Scotland"]))
               for b in brokers])

    # ---------- policyholders (initial load spread over the days) ----------
    holders = {}
    holder_day = {}
    for i in range(1, N_POLICYHOLDERS + 1):
        hid = f"PH{i:07d}"
        d = START + timedelta(days=random.randrange(DAYS))
        holders[hid] = {
            "policyholder_id": hid,
            "full_name": fake.name(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=85)
                             if random.random() > 0.01 else "",        # ~1% missing DOB
            "postcode": fake.postcode(),
            "email": fake.email(),
            "updated_at": datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randrange(8, 18)),
        }
        holder_day[hid] = d

    # ---------- policies ----------
    weights = [40 if b == SKEWED_BROKER else 60 / (len(brokers) - 1) for b in brokers]
    policies = {}
    holder_ids = list(holders)
    for i in range(1, N_POLICIES + 1):
        pno = f"POL{i:08d}"
        hid = random.choice(holder_ids)
        start = max(holder_day[hid], START + timedelta(days=random.randrange(DAYS)))
        product = random.choice(PRODUCTS)[0]
        lo, hi = COVER_PREMIUM[product]
        policies[pno] = {
            "policy_number": pno,
            "policyholder_id": hid,
            "broker_code": random.choices(brokers, weights)[0],
            "product_code": product,
            "vehicle": random.choice(VEHICLES),
            "annual_premium": money(random.uniform(lo, hi)),
            "start_date": start,
            "end_date": start + timedelta(days=364),
            "status": "ACTIVE",
            "updated_at": datetime.combine(start, datetime.min.time()) + timedelta(hours=random.randrange(8, 18)),
        }

    # daily buckets
    ph_extract = {START + timedelta(days=k): [] for k in range(DAYS)}
    pol_extract = {START + timedelta(days=k): [] for k in range(DAYS)}
    bordereau = {START + timedelta(days=k): [] for k in range(DAYS)}
    claim_events = {START + timedelta(days=k): [] for k in range(DAYS)}
    line_seq = 0

    def add_line(d, broker, pno, ttype, premium):
        nonlocal line_seq
        line_seq += 1
        bordereau[d].append({
            "bordereau_line_id": f"BL{line_seq:09d}",
            "broker_code": broker,
            "policy_number": pno,
            "transaction_type": ttype,
            "transaction_date": d,
            "written_premium": premium,
            "ipt": money(premium * IPT_RATE),
            "commission": money(premium * COMMISSION_RATE),
            "payment_method": random.choice(["DIRECT_DEBIT", "CARD", "BANK_TRANSFER"]),
        })

    for hid, h in holders.items():
        ph_extract[holder_day[hid]].append(dict(h))

    for pno, p in policies.items():
        pol_extract[p["start_date"]].append(dict(p))
        add_line(p["start_date"], p["broker_code"], pno, "NEW_BUSINESS", p["annual_premium"])

    # ---------- changes: postcode moves (SCD2 on policyholder) ----------
    for hid in random.sample(holder_ids, k=int(N_POLICYHOLDERS * 0.05)):
        d = holder_day[hid] + timedelta(days=random.randint(3, 20))
        if d >= START + timedelta(days=DAYS):
            continue
        h = holders[hid]
        h["postcode"] = fake.postcode()
        h["updated_at"] = datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randrange(8, 18))
        ph_extract[d].append(dict(h))

    # ---------- endorsements and cancellations (SCD2 on policy + premium adjustments) ----------
    pol_ids = list(policies)
    for pno in random.sample(pol_ids, k=int(N_POLICIES * 0.10)):
        p = policies[pno]
        d = p["start_date"] + timedelta(days=random.randint(2, 20))
        if d >= START + timedelta(days=DAYS):
            continue
        old = p["annual_premium"]
        change = random.choice(["vehicle", "product"])
        if change == "vehicle":
            p["vehicle"] = random.choice(VEHICLES)
        else:
            p["product_code"] = random.choice(PRODUCTS)[0]
        lo, hi = COVER_PREMIUM[p["product_code"]]
        p["annual_premium"] = money(random.uniform(lo, hi))
        p["updated_at"] = datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randrange(8, 18))
        pol_extract[d].append(dict(p))
        remaining = Decimal((p["end_date"] - d).days + 1) / Decimal(365)
        add_line(d, p["broker_code"], pno, "ENDORSEMENT", money((p["annual_premium"] - old) * remaining))

    for pno in random.sample(pol_ids, k=int(N_POLICIES * 0.03)):
        p = policies[pno]
        d = p["start_date"] + timedelta(days=random.randint(5, 25))
        if d >= START + timedelta(days=DAYS) or p["status"] != "ACTIVE":
            continue
        p["status"] = "CANCELLED"
        p["updated_at"] = datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randrange(8, 18))
        pol_extract[d].append(dict(p))
        remaining = Decimal((p["end_date"] - d).days + 1) / Decimal(365)
        add_line(d, p["broker_code"], pno, "CANCELLATION", money(-p["annual_premium"] * remaining))

    # ---------- unknown broker lines (inferred member later) ----------
    for _ in range(25):
        d = START + timedelta(days=random.randrange(DAYS))
        add_line(d, UNKNOWN_BROKER, random.choice(pol_ids), "NEW_BUSINESS", money(random.uniform(300, 900)))

    # ---------- claims lifecycle events ----------
    claim_seq = 0
    for pno in random.sample(pol_ids, k=int(N_POLICIES * CLAIM_RATE)):
        p = policies[pno]
        reported = p["start_date"] + timedelta(days=random.randint(1, 15))
        if reported >= START + timedelta(days=DAYS):
            continue
        claim_seq += 1
        cno = f"CLM{claim_seq:07d}"
        reserve = money(random.uniform(500, 8000))
        steps = [("REPORTED", 0, Decimal("0")), ("ASSESSED", random.randint(1, 4), reserve)]
        if random.random() < 0.3:
            steps.append(("RESERVE_CHANGE", random.randint(5, 8), money(reserve * Decimal("1.25"))))
        if random.random() < 0.6:
            steps.append(("PAID", random.randint(9, 14), money(reserve * Decimal(str(random.uniform(0.6, 1.0))))))
            steps.append(("CLOSED", random.randint(15, 20), Decimal("0")))
        for etype, offset, amount in steps:
            ev_day = reported + timedelta(days=offset)
            if ev_day >= START + timedelta(days=DAYS):
                break
            arrival = ev_day
            if random.random() < OUT_OF_ORDER_RATE:
                arrival = min(ev_day + timedelta(days=random.randint(1, 3)), START + timedelta(days=DAYS - 1))
            claim_events[arrival].append({
                "event_id": f"EV{random.getrandbits(48):012x}",
                "claim_number": cno,
                "policy_number": pno,
                "event_type": etype,
                "event_ts": datetime.combine(ev_day, datetime.min.time()) + timedelta(hours=random.randrange(8, 18)),
                "amount": str(amount),
            })

    # ---------- write daily files ----------
    ph_cols = ["policyholder_id", "full_name", "date_of_birth", "postcode", "email", "updated_at"]
    pol_cols = ["policy_number", "policyholder_id", "broker_code", "product_code", "vehicle",
                "annual_premium", "start_date", "end_date", "status", "updated_at"]
    bd_cols = ["bordereau_line_id", "broker_code", "policy_number", "transaction_type",
               "transaction_date", "written_premium", "ipt", "commission"]

    for k in range(DAYS):
        d = START + timedelta(days=k)
        ds = day_str(d)
        write_csv(f"{base}/policy_admin/policyholder/policyholder_{ds}.csv", ph_cols,
                  [[r[c] for c in ph_cols] for r in ph_extract[d]])
        write_csv(f"{base}/policy_admin/policy/policy_{ds}.csv", pol_cols,
                  [[r[c] for c in pol_cols] for r in pol_extract[d]])

        lines = bordereau[d]
        lines += random.sample(lines, k=max(1, int(len(lines) * DUPLICATE_RATE)))   # duplicates
        cols = bd_cols + (["payment_method"] if k + 1 >= NEW_COLUMN_DAY else [])     # schema drift
        folder = "late" if k + 1 == LATE_FILE_DAY else "premium"                     # late file
        write_csv(f"{base}/bordereaux/{folder}/premium_bordereau_{ds}.csv", cols,
                  [[r[c] for c in cols] for r in lines])

        write_jsonl(f"{base}/claims/claims_events_{ds}.json", claim_events[d])

    # ---------- summary (your source-of-truth totals for reconciliation later) ----------
    all_lines = [ln for day_lines in bordereau.values() for ln in day_lines]
    summary = {
        "days": DAYS,
        "policyholders": N_POLICYHOLDERS,
        "policies": N_POLICIES,
        "bordereau_lines_incl_duplicates": len(all_lines),
        "distinct_bordereau_lines": len({l["bordereau_line_id"] for l in all_lines}),
        "written_premium_excl_duplicates": str(sum({l["bordereau_line_id"]: l["written_premium"]
                                                    for l in all_lines}.values())),
        "claims": claim_seq,
        "claim_events": sum(len(v) for v in claim_events.values()),
        "skewed_broker": SKEWED_BROKER,
        "unknown_broker": UNKNOWN_BROKER,
        "new_column_from_day": NEW_COLUMN_DAY,
        "late_file_day": LATE_FILE_DAY,
    }
    os.makedirs(f"{base}/_meta", exist_ok=True)
    with open(f"{base}/_meta/generation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "./out")

