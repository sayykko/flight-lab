import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251ADB059"
FIRST_NAME = "Said"
LAST_NAME = "Badalzade"

def invalid_json_constant(value: str):
    raise ValueError(f"Invalid JSON value: {value}")

def read_json(path: str):
    with open(path, encoding="utf-8") as file:
        return json.load(file, parse_constant=invalid_json_constant)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flight query tool")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE")
    source.add_argument("-d", metavar="FOLDER")
    source.add_argument("-j", metavar="FILE")
    parser.add_argument("-a", metavar="FILE")
    parser.add_argument("-o", metavar="FILE")
    parser.add_argument("-q", metavar="FILE")
    parser.add_argument("-r", metavar="FOLDER", default=".")

    try:
        args = parser.parse_args(argv)
        if args.j is None and args.a is None:
            parser.error("-a is required with -i or -d")
        if args.j is not None and args.o is not None:
            parser.error("-o cannot be used with -j")
    except SystemExit as error:
        return int(error.code)

    logger = logging.getLogger("flight_parser")
    handler = None
    try:
        if args.j is not None:
            db = read_json(args.j)
            if not isinstance(db, list) or any(
                not isinstance(record, dict) for record in db
            ):
                raise ValueError("Database must be an array of objects")
        else:
            output = Path(args.o if args.o is not None else "db.json")
            logger.setLevel(logging.INFO)
            handler = logging.FileHandler(
                output.parent / "errors.log", mode="w", encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.addHandler(handler)

            airports = load_airports(args.a)
            if args.i is not None:
                paths = [args.i]
            else:
                paths = [
                    str(path)
                    for path in sorted(Path(args.d).iterdir(), key=lambda p: p.name)
                    if path.is_file() and path.name.endswith(".csv")
                ]
                if not paths:
                    raise ValueError("No CSV files found in the input folder")

            db, errors = parse_files(paths, airports)
            for error in errors:
                logger.warning(error)
            with output.open("w", encoding="utf-8") as file:
                json.dump(db, file, indent=2)

        if args.q is not None:
            queries = read_json(args.q)
            if not isinstance(queries, (dict, list)):
                raise ValueError("Queries must be an object or an array of objects")
            if isinstance(queries, list) and any(
                not isinstance(query, dict) for query in queries
            ):
                raise ValueError("Every query must be an object")

            response = run_queries(db, queries)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{timestamp}.json"
            )
            with (Path(args.r) / filename).open("w", encoding="utf-8") as file:
                json.dump(response, file, indent=2)
        return 0
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()

if __name__ == "__main__":
    sys.exit(main())