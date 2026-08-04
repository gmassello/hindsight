import sys

from hindsight.datahub.graphql_fallback import dataset_description, update_description

TARGET = (
    "urn:li:dataset:(urn:li:dataPlatform:snowflake,b2fd91.order_entry_db.order_entry.orders,PROD)"
)
BLOCK = (
    "\n\n--- SIMULATED MIGRATION 2026-08-04 ---\n"
    "ALTER TABLE order_entry.orders ALTER COLUMN customer_id DROP NOT NULL;\n"
    "Applied by the order_entry service team without downstream notice. "
    "customer_id may now contain NULL values.\n"
    "--- END SIMULATED MIGRATION ---"
)


def main() -> None:
    reset = "--reset" in sys.argv
    description = dataset_description(TARGET)
    if reset:
        updated = description.replace(BLOCK, "")
    else:
        updated = description if BLOCK in description else description + BLOCK
    if updated == description:
        print("Nothing to do.")
        return
    update_description(TARGET, updated)
    action = "removed from" if reset else "appended to"
    print(f"Simulated migration {action} {TARGET}")


if __name__ == "__main__":
    main()
