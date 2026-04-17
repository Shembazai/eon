import csv
import hashlib
import tempfile
from dataclasses import replace
from pathlib import Path
import re

from .schemas import TransactionRecord, detect_column_mapping


CATEGORY_RULES = (
	("income", (
		"payroll",
		"salary",
		"direct deposit",
		"income deposit",
	)),
	("rent", (
		"rent",
		"landlord",
		"lease",
	)),
	("food", (
		"grocery",
		"groceries",
		"restaurant",
		"cafe",
		"coffee",
		"uber eats",
		"doordash",
		"skip the dishes",
		"instacart",
	)),
	("transport", (
		"uber trip",
		"lyft",
		"taxi",
		"transit",
		"bus",
		"train",
		"metro pass",
	)),
	("fuel", (
		"fuel",
		"gas station",
		"shell",
		"esso",
		"petro",
		"ultramar",
	)),
	("phone", (
		"phone",
		"mobile",
		"cell",
	)),
	("internet", (
		"internet",
		"wifi",
		"telecom",
	)),
	("electricity", (
		"electricity",
		"hydro",
		"power",
	)),
	("insurance", (
		"insurance",
	)),
	("subscriptions", (
		"subscription",
		"subscriptions",
		"netflix",
		"spotify",
		"youtube premium",
	)),
	("debt", (
		"loan payment",
		"debt payment",
		"credit card payment",
	)),
)


def normalize_category_text(value) -> str:
	if value is None:
		return ""

	return " ".join(str(value).strip().lower().split())



def load_raw_rows(csv_path: Path) -> list[dict[str, str]]:
	with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)

		if reader.fieldnames is None:
			raise ValueError("CSV file is missing a header row")

		rows: list[dict[str, str]] = []
		for row in reader:
			rows.append(dict(row))

	return rows



def normalize_date(raw_date: str) -> str:
	from datetime import datetime

	raw_date = str(raw_date).strip()

	date_formats = [
		"%Y-%m-%d",
		"%m/%d/%Y",
		"%d/%m/%Y",
	]

	for fmt in date_formats:
		try:
			return datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
		except ValueError:
			continue

	raise ValueError(f"Unsupported date format: {raw_date}")



def parse_money_value(raw_value: str) -> float:
	raw_value = str(raw_value).strip().replace(",", "").replace("$", "")

	if raw_value == "":
		return 0.0

	return float(raw_value)



def normalize_amount(
	raw_amount: str | None = None,
	raw_debit: str | None = None,
	raw_credit: str | None = None,
) -> float:
	if raw_amount is not None:
		return parse_money_value(raw_amount)

	debit = parse_money_value(raw_debit or "")
	credit = parse_money_value(raw_credit or "")

	if debit and credit:
		raise ValueError("Row has both debit and credit values")

	if credit:
		return credit

	if debit:
		return -debit

	return 0.0



def normalize_description(raw_description: str) -> str:
	text = str(raw_description).strip().lower()
	text = re.sub(r"\d+", " ", text)
	text = re.sub(r"[^a-z\s]", " ", text)
	text = re.sub(r"\s+", " ", text).strip()
	return text



def convert_row_to_transaction_record(headers, raw_row, source_file, row_index):
	if not isinstance(headers, (list, tuple)) or not headers:
		raise ValueError("headers must be a non-empty sequence.")

	if not isinstance(raw_row, dict):
		raise ValueError("raw_row must be a dict keyed by CSV headers.")

	if not source_file:
		raise ValueError("source_file is required.")

	if not isinstance(row_index, int) or row_index < 1:
		raise ValueError("row_index must be a positive integer.")

	column_mapping = detect_column_mapping(headers)

	required_fields = ("date", "description", "amount")
	missing_fields = [field for field in required_fields if field not in column_mapping]
	if missing_fields:
		raise ValueError(
			f"Missing required column mapping(s): {', '.join(missing_fields)}."
		)

	date_header = column_mapping["date"]
	description_header = column_mapping["description"]
	amount_header = column_mapping["amount"]

	for header_name in (date_header, description_header, amount_header):
		if header_name not in raw_row:
			raise ValueError(
				f"Row {row_index}: expected header '{header_name}' is missing from the raw row."
			)

	raw_date = raw_row[date_header]
	raw_description = raw_row[description_header]
	raw_amount = raw_row[amount_header]

	try:
		normalized_date = normalize_date(raw_date)
	except Exception as exc:
		raise ValueError(f"Row {row_index}: invalid date value {raw_date!r}.") from exc

	try:
		normalized_amount = normalize_amount(raw_amount)
	except Exception as exc:
		raise ValueError(f"Row {row_index}: invalid amount value {raw_amount!r}.") from exc

	try:
		normalized_description = normalize_description(raw_description)
	except Exception as exc:
		raise ValueError(f"Row {row_index}: invalid description value {raw_description!r}.") from exc

	if normalized_date in (None, ""):
		raise ValueError(f"Row {row_index}: normalized date is empty.")

	if normalized_description in (None, ""):
		raise ValueError(f"Row {row_index}: normalized description is empty.")

	original_description = "" if raw_description is None else str(raw_description).strip()

	transaction_key = (
		f"{source_file}|{row_index}|{normalized_date}|"
		f"{normalized_amount}|{normalized_description}"
	)
	transaction_id = hashlib.sha256(transaction_key.encode("utf-8")).hexdigest()

	return TransactionRecord(
		transaction_id=transaction_id,
		date=normalized_date,
		amount=normalized_amount,
		description=original_description,
		normalized_desc=normalized_description,
		category="uncategorized",
		source_file=str(source_file),
		row_index=row_index,
	)



def convert_rows_to_transaction_records(headers, raw_rows, source_file, start_row_index=2):
	if not isinstance(headers, (list, tuple)) or not headers:
		raise ValueError("headers must be a non-empty sequence.")

	if not isinstance(raw_rows, list):
		raise ValueError("raw_rows must be a list of row dictionaries.")

	if not source_file:
		raise ValueError("source_file is required.")

	if not isinstance(start_row_index, int) or start_row_index < 1:
		raise ValueError("start_row_index must be a positive integer.")

	detect_column_mapping(headers)

	accepted_records = []
	rejected_rows = []

	for offset, raw_row in enumerate(raw_rows):
		row_index = start_row_index + offset

		try:
			record = convert_row_to_transaction_record(
				headers=headers,
				raw_row=raw_row,
				source_file=source_file,
				row_index=row_index,
			)
			accepted_records.append(record)
		except ValueError as exc:
			rejected_rows.append({
				"source_file": str(source_file),
				"row_index": row_index,
				"error": str(exc),
				"raw_row": dict(raw_row) if isinstance(raw_row, dict) else raw_row,
			})

	return accepted_records, rejected_rows



def structure_csv_file(csv_path):
	if not csv_path:
		raise ValueError("csv_path is required.")

	csv_path = Path(csv_path)

	if not csv_path.exists():
		raise ValueError(f"CSV file does not exist: {csv_path}")

	if not csv_path.is_file():
		raise ValueError(f"CSV path is not a file: {csv_path}")

	with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
		reader = csv.DictReader(handle)
		headers = list(reader.fieldnames or [])

	if not headers:
		raise ValueError(f"CSV file has no headers: {csv_path}")

	raw_rows = load_raw_rows(csv_path)

	accepted_records, rejected_rows = convert_rows_to_transaction_records(
		headers=headers,
		raw_rows=raw_rows,
		source_file=csv_path.name,
		start_row_index=2,
	)

	return {
		"source_file": csv_path.name,
		"headers": headers,
		"total_rows": len(raw_rows),
		"accepted_records": accepted_records,
		"rejected_rows": rejected_rows,
	}



def structure_csv_files(csv_paths):
	if not isinstance(csv_paths, list):
		raise ValueError("csv_paths must be a list.")

	if not csv_paths:
		raise ValueError("csv_paths must not be empty.")

	structured_files = []
	rejected_files = []
	accepted_records = []
	rejected_rows = []

	for raw_path in csv_paths:
		try:
			file_result = structure_csv_file(raw_path)
			structured_files.append(file_result)
			accepted_records.extend(file_result["accepted_records"])
			rejected_rows.extend(file_result["rejected_rows"])
		except ValueError as exc:
			rejected_files.append({
				"source_file": str(raw_path) if raw_path is not None else "",
				"error": str(exc),
			})

	return {
		"structured_files": structured_files,
		"rejected_files": rejected_files,
		"accepted_records": accepted_records,
		"rejected_rows": rejected_rows,
		"total_files": len(csv_paths),
		"successful_files": len(structured_files),
		"failed_files": len(rejected_files),
		"total_accepted_records": len(accepted_records),
		"total_rejected_rows": len(rejected_rows),
	}



def apply_category_baseline(records, default_category="uncategorized"):
	if not isinstance(records, list):
		raise ValueError("records must be a list.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	normalized_records = []
	category_counts = {}

	for idx, record in enumerate(records, 1):
		if not isinstance(record, TransactionRecord):
			raise ValueError(f"records[{idx}] is not a TransactionRecord.")

		category = normalize_category_text(getattr(record, "category", None))
		if not category:
			category = default_category

		normalized_record = replace(record, category=category)
		normalized_records.append(normalized_record)
		category_counts[category] = category_counts.get(category, 0) + 1

	uncategorized_count = category_counts.get(default_category, 0)
	total_records = len(normalized_records)
	categorized_count = total_records - uncategorized_count

	return {
		"records": normalized_records,
		"category_counts": category_counts,
		"uncategorized_count": uncategorized_count,
		"categorized_count": categorized_count,
		"total_records": total_records,
	}



def classify_normalized_description(normalized_desc, category_rules=None):
	rules = CATEGORY_RULES if category_rules is None else category_rules

	if not isinstance(rules, (list, tuple)):
		raise ValueError("category_rules must be a sequence of rule entries.")

	desc = " ".join(str(normalized_desc or "").strip().lower().split())
	if not desc:
		return None

	for idx, rule in enumerate(rules, 1):
		if not isinstance(rule, (list, tuple)) or len(rule) != 2:
			raise ValueError(f"category_rules[{idx}] must be a 2-item sequence: (category, phrases).")

		category, phrases = rule
		category = normalize_category_text(category)
		if not category:
			raise ValueError(f"category_rules[{idx}] has an empty category.")

		if not isinstance(phrases, (list, tuple)):
			raise ValueError(f"category_rules[{idx}] phrases must be a sequence.")

		for phrase in phrases:
			phrase_n = " ".join(str(phrase or "").strip().lower().split())
			if phrase_n and phrase_n in desc:
				return category

	return None



def apply_category_rules(records, default_category="uncategorized", category_rules=None):
	if not isinstance(records, list):
		raise ValueError("records must be a list.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	baseline = apply_category_baseline(records, default_category=default_category)
	assigned_records = []
	category_counts = {}
	assigned_count = 0

	for idx, record in enumerate(baseline["records"], 1):
		if not isinstance(record, TransactionRecord):
			raise ValueError(f"records[{idx}] is not a TransactionRecord.")

		category = normalize_category_text(getattr(record, "category", None)) or default_category
		if category == default_category:
			matched = classify_normalized_description(
				getattr(record, "normalized_desc", ""),
				category_rules=category_rules,
			)
			if matched is not None:
				category = matched
				assigned_count += 1

		normalized_record = replace(record, category=category)
		assigned_records.append(normalized_record)
		category_counts[category] = category_counts.get(category, 0) + 1

	uncategorized_count = category_counts.get(default_category, 0)
	total_records = len(assigned_records)
	categorized_count = total_records - uncategorized_count

	return {
		"records": assigned_records,
		"category_counts": category_counts,
		"uncategorized_count": uncategorized_count,
		"categorized_count": categorized_count,
		"assigned_count": assigned_count,
		"total_records": total_records,
	}



def transaction_record_to_review_dict(record, default_category="uncategorized"):
	if not isinstance(record, TransactionRecord):
		raise ValueError("record must be a TransactionRecord.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	category = normalize_category_text(getattr(record, "category", None)) or default_category

	return {
		"transaction_id": getattr(record, "transaction_id", ""),
		"date": getattr(record, "date", ""),
		"amount": getattr(record, "amount", 0.0),
		"description": getattr(record, "description", ""),
		"normalized_desc": getattr(record, "normalized_desc", ""),
		"category": category,
		"source_file": getattr(record, "source_file", ""),
		"row_index": getattr(record, "row_index", None),
		"needs_category_review": category == default_category,
	}



def review_dict_to_transaction_record(review_record, default_category="uncategorized"):
	if not isinstance(review_record, dict):
		raise ValueError("review_record must be a dict.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	transaction_id = str(review_record.get("transaction_id", "")).strip()
	if not transaction_id:
		raise ValueError("review_record.transaction_id is required.")

	date = str(review_record.get("date", "")).strip()
	if not date:
		raise ValueError("review_record.date is required.")

	try:
		amount = float(review_record.get("amount", 0.0))
	except (TypeError, ValueError) as exc:
		raise ValueError("review_record.amount must be numeric.") from exc

	description = str(review_record.get("description", "")).strip()
	normalized_desc = str(review_record.get("normalized_desc", "")).strip()
	source_file = str(review_record.get("source_file", "")).strip()
	row_index = review_record.get("row_index")
	if not isinstance(row_index, int) or row_index < 1:
		raise ValueError("review_record.row_index must be a positive integer.")

	category = normalize_category_text(review_record.get("category", None)) or default_category

	return TransactionRecord(
		transaction_id=transaction_id,
		date=date,
		amount=amount,
		description=description,
		normalized_desc=normalized_desc,
		category=category,
		source_file=source_file,
		row_index=row_index,
	)



def build_source_file_summary(records, rejected_rows=None, structured_files=None, rejected_files=None, default_category="uncategorized"):
	if not isinstance(records, list):
		raise ValueError("records must be a list.")

	rejected_rows = [] if rejected_rows is None else rejected_rows
	structured_files = [] if structured_files is None else structured_files
	rejected_files = [] if rejected_files is None else rejected_files
	default_category = normalize_category_text(default_category)

	if not isinstance(rejected_rows, list):
		raise ValueError("rejected_rows must be a list.")
	if not isinstance(structured_files, list):
		raise ValueError("structured_files must be a list.")
	if not isinstance(rejected_files, list):
		raise ValueError("rejected_files must be a list.")

	summary_map = {}
	file_order = []

	def ensure_summary(source_file):
		source_file = str(source_file)
		if source_file not in summary_map:
			summary_map[source_file] = {
				"source_file": source_file,
				"status": "structured",
				"total_rows": None,
				"accepted_records": 0,
				"categorized_records": 0,
				"uncategorized_records": 0,
				"rejected_rows": 0,
				"error": None,
			}
			file_order.append(source_file)
		return summary_map[source_file]

	for file_result in structured_files:
		if not isinstance(file_result, dict):
			raise ValueError("structured_files must contain dict entries.")
		source_file = file_result.get("source_file")
		if not source_file:
			raise ValueError("structured_files entries must include source_file.")
		summary = ensure_summary(source_file)
		summary["total_rows"] = file_result.get("total_rows")

	for idx, record in enumerate(records, 1):
		if not isinstance(record, TransactionRecord):
			raise ValueError(f"records[{idx}] is not a TransactionRecord.")
		summary = ensure_summary(getattr(record, "source_file", ""))
		summary["accepted_records"] += 1
		category = normalize_category_text(getattr(record, "category", None)) or default_category
		if category == default_category:
			summary["uncategorized_records"] += 1
		else:
			summary["categorized_records"] += 1

	for idx, row in enumerate(rejected_rows, 1):
		if not isinstance(row, dict):
			raise ValueError(f"rejected_rows[{idx}] is not a dict.")
		summary = ensure_summary(row.get("source_file", ""))
		summary["rejected_rows"] += 1

	for file_info in rejected_files:
		if not isinstance(file_info, dict):
			raise ValueError("rejected_files must contain dict entries.")
		source_file = file_info.get("source_file")
		if not source_file:
			raise ValueError("rejected_files entries must include source_file.")
		summary = ensure_summary(source_file)
		summary["status"] = "failed"
		summary["total_rows"] = None
		summary["accepted_records"] = 0
		summary["categorized_records"] = 0
		summary["uncategorized_records"] = 0
		summary["rejected_rows"] = 0
		summary["error"] = file_info.get("error")

	return [summary_map[source_file] for source_file in file_order]



def generate_review_bundle(structured_data, default_category="uncategorized", category_rules=None):
	if not isinstance(structured_data, dict):
		raise ValueError("structured_data must be a dict.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	structured_files = structured_data.get("structured_files", [])
	rejected_files = structured_data.get("rejected_files", [])
	accepted_records = structured_data.get("accepted_records", [])
	rejected_rows = structured_data.get("rejected_rows", [])

	if not isinstance(structured_files, list):
		raise ValueError("structured_data.structured_files must be a list.")
	if not isinstance(rejected_files, list):
		raise ValueError("structured_data.rejected_files must be a list.")
	if not isinstance(accepted_records, list):
		raise ValueError("structured_data.accepted_records must be a list.")
	if not isinstance(rejected_rows, list):
		raise ValueError("structured_data.rejected_rows must be a list.")

	categorized = apply_category_rules(
		accepted_records,
		default_category=default_category,
		category_rules=category_rules,
	)
	categorized_records = categorized["records"]
	review_records = [
		transaction_record_to_review_dict(record, default_category=default_category)
		for record in categorized_records
	]
	uncategorized_records = [
		record for record in review_records
		if normalize_category_text(record.get("category")) == default_category
	]
	source_file_summary = build_source_file_summary(
		categorized_records,
		rejected_rows=rejected_rows,
		structured_files=structured_files,
		rejected_files=rejected_files,
		default_category=default_category,
	)
	records_needing_attention = list(uncategorized_records) + list(rejected_rows)

	return {
		"structured_files": structured_files,
		"rejected_files": rejected_files,
		"accepted_records": review_records,
		"uncategorized_records": uncategorized_records,
		"rejected_rows": rejected_rows,
		"records_needing_attention": records_needing_attention,
		"source_file_summary": source_file_summary,
		"category_counts": categorized["category_counts"],
		"uncategorized_count": categorized["uncategorized_count"],
		"categorized_count": categorized["categorized_count"],
		"assigned_count": categorized["assigned_count"],
		"total_records": categorized["total_records"],
		"total_rejected_rows": len(rejected_rows),
		"total_attention_items": len(records_needing_attention),
	}



def apply_user_category_corrections(review_bundle, corrections, default_category="uncategorized", category_rules=None):
	if not isinstance(review_bundle, dict):
		raise ValueError("review_bundle must be a dict.")
	if not isinstance(corrections, list):
		raise ValueError("corrections must be a list.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	accepted_records = review_bundle.get("accepted_records", [])
	if not isinstance(accepted_records, list):
		raise ValueError("review_bundle.accepted_records must be a list.")

	seen_targets = set()
	correction_map = {}

	for idx, correction in enumerate(corrections, 1):
		if not isinstance(correction, dict):
			raise ValueError(f"corrections[{idx}] is not a dict.")

		transaction_id = str(correction.get("transaction_id", "")).strip()
		if not transaction_id:
			raise ValueError(f"corrections[{idx}] missing transaction_id.")
		if transaction_id in seen_targets:
			raise ValueError(f"Duplicate correction target(s): {transaction_id}.")
		seen_targets.add(transaction_id)

		category = normalize_category_text(correction.get("category", None))
		if not category:
			raise ValueError(f"corrections[{idx}] missing category.")

		correction_map[transaction_id] = category

	known_ids = {str(record.get("transaction_id", "")).strip() for record in accepted_records if isinstance(record, dict)}
	unknown_targets = [transaction_id for transaction_id in correction_map if transaction_id not in known_ids]
	if unknown_targets:
		raise ValueError(f"Unknown correction target(s): {', '.join(unknown_targets)}.")

	updated_review_records = []
	corrections_applied = 0
	unchanged_corrections = 0

	for idx, record in enumerate(accepted_records, 1):
		if not isinstance(record, dict):
			raise ValueError(f"review_bundle.accepted_records[{idx}] is not a dict.")

		updated_record = dict(record)
		transaction_id = str(updated_record.get("transaction_id", "")).strip()
		current_category = normalize_category_text(updated_record.get("category", None)) or default_category

		if transaction_id in correction_map:
			new_category = correction_map[transaction_id]
			if new_category == current_category:
				unchanged_corrections += 1
			else:
				updated_record["category"] = new_category
				updated_record["needs_category_review"] = (new_category == default_category)
				corrections_applied += 1

		updated_review_records.append(updated_record)

	updated_records = [
		review_dict_to_transaction_record(record, default_category=default_category)
		for record in updated_review_records
	]

	rebuilt = generate_review_bundle(
		{
			"structured_files": review_bundle.get("structured_files", []),
			"rejected_files": review_bundle.get("rejected_files", []),
			"accepted_records": updated_records,
			"rejected_rows": review_bundle.get("rejected_rows", []),
		},
		default_category=default_category,
		category_rules=category_rules,
	)

	rebuilt["corrections_requested"] = len(corrections)
	rebuilt["corrections_applied"] = corrections_applied
	rebuilt["unchanged_corrections"] = unchanged_corrections

	return rebuilt



def _append_validation_issue(issues, label, reported, rebuilt):
	if reported != rebuilt:
		issues.append(f"{label} mismatch: reported {reported}, rebuilt {rebuilt}.")



def revalidate_review_bundle(review_bundle, default_category="uncategorized", category_rules=None):
	if not isinstance(review_bundle, dict):
		raise ValueError("review_bundle must be a dict.")

	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	accepted_records = review_bundle.get("accepted_records", [])
	if not isinstance(accepted_records, list):
		raise ValueError("review_bundle.accepted_records must be a list.")

	canonical_records = [
		review_dict_to_transaction_record(record, default_category=default_category)
		for record in accepted_records
	]

	rebuilt = generate_review_bundle(
		{
			"structured_files": review_bundle.get("structured_files", []),
			"rejected_files": review_bundle.get("rejected_files", []),
			"accepted_records": canonical_records,
			"rejected_rows": review_bundle.get("rejected_rows", []),
		},
		default_category=default_category,
		category_rules=category_rules,
	)

	validation_issues = []
	_append_validation_issue(validation_issues, "total_records", review_bundle.get("total_records"), rebuilt.get("total_records"))
	_append_validation_issue(validation_issues, "uncategorized_count", review_bundle.get("uncategorized_count"), rebuilt.get("uncategorized_count"))
	_append_validation_issue(validation_issues, "categorized_count", review_bundle.get("categorized_count"), rebuilt.get("categorized_count"))
	_append_validation_issue(validation_issues, "total_rejected_rows", review_bundle.get("total_rejected_rows"), rebuilt.get("total_rejected_rows"))
	_append_validation_issue(validation_issues, "total_attention_items", review_bundle.get("total_attention_items"), rebuilt.get("total_attention_items"))
	_append_validation_issue(validation_issues, "category_counts", review_bundle.get("category_counts"), rebuilt.get("category_counts"))
	_append_validation_issue(validation_issues, "source_file_summary", review_bundle.get("source_file_summary"), rebuilt.get("source_file_summary"))

	result = dict(rebuilt)
	for key in ("corrections_requested", "corrections_applied", "unchanged_corrections"):
		if key in review_bundle:
			result[key] = review_bundle[key]

	result["validation_passed"] = len(validation_issues) == 0
	result["validation_issues"] = validation_issues
	return result



def finalize_review_bundle(review_bundle, default_category="uncategorized", category_rules=None):
	validated = revalidate_review_bundle(
		review_bundle,
		default_category=default_category,
		category_rules=category_rules,
	)

	blocking_issues = list(validated.get("validation_issues", []))
	uncategorized_count = int(validated.get("uncategorized_count", 0))
	if uncategorized_count > 0:
		blocking_issues.append(f"uncategorized records remain: {uncategorized_count}.")

	finalized_records = [
		review_dict_to_transaction_record(record, default_category=default_category)
		for record in validated.get("accepted_records", [])
	]

	ready_for_save = bool(validated.get("validation_passed")) and uncategorized_count == 0

	result = dict(validated)
	result["finalized_records"] = finalized_records
	result["ready_for_save"] = ready_for_save
	result["blocking_issues"] = blocking_issues
	result["excluded_rejected_row_count"] = len(validated.get("rejected_rows", []))
	return result



def run_phase3_acceptance_pass(default_category="uncategorized"):
	default_category = normalize_category_text(default_category)
	if not default_category:
		raise ValueError("default_category must be a non-empty string.")

	passes = []
	failures = []

	def check(name, actual, expected):
		if actual == expected:
			passes.append(name)
		else:
			failures.append({
				"name": name,
				"expected": expected,
				"actual": actual,
			})

	with tempfile.TemporaryDirectory(prefix="phase3_acceptance_") as temp_dir:
		temp_path = Path(temp_dir)
		a_csv = temp_path / "a.csv"
		b_csv = temp_path / "b.csv"
		c_csv = temp_path / "c.csv"

		a_csv.write_text(
			"date,description,amount\n"
			"2026-01-01,Metro grocery,-25.00\n"
			"2026-01-02,Uber trip,-18.00\n",
			encoding="utf-8",
		)
		b_csv.write_text(
			"date,description,amount\n"
			"2026-01-03,Payroll deposit,1000.00\n"
			"2026-01-04,Shell station,-60.00\n"
			"2026-01-05,Unknown thing,-12.00\n"
			"2026-01-06,Bad amount,abc\n",
			encoding="utf-8",
		)
		c_csv.write_text("", encoding="utf-8")

		structured = structure_csv_files([a_csv, b_csv, c_csv])
		check("structured total files", structured["total_files"], 3)
		check("structured successful files", structured["successful_files"], 2)
		check("structured failed files", structured["failed_files"], 1)
		check("structured accepted records", structured["total_accepted_records"], 5)
		check("structured rejected rows", structured["total_rejected_rows"], 1)

		seeded_records = []
		unknown_id = None
		fuel_id = None
		for record in structured["accepted_records"]:
			if record.normalized_desc == "shell station":
				record = replace(record, category="fuel")
				fuel_id = record.transaction_id
			if record.normalized_desc == "unknown thing":
				unknown_id = record.transaction_id
			seeded_records.append(record)

		baseline = apply_category_baseline(seeded_records, default_category=default_category)
		check("baseline total records", baseline["total_records"], 5)
		check("baseline fuel preserved", [r.category for r in baseline["records"] if r.transaction_id == fuel_id][0], "fuel")

		rules_applied = apply_category_rules(seeded_records, default_category=default_category)
		check("rules assigned count", rules_applied["assigned_count"], 3)
		check("rules uncategorized count", rules_applied["uncategorized_count"], 1)
		check("rules category counts", rules_applied["category_counts"], {
			"food": 1,
			"transport": 1,
			"income": 1,
			"fuel": 1,
			"uncategorized": 1,
		})

		review_bundle = generate_review_bundle({
			"structured_files": structured["structured_files"],
			"rejected_files": structured["rejected_files"],
			"accepted_records": seeded_records,
			"rejected_rows": structured["rejected_rows"],
		}, default_category=default_category)
		check("review total records", review_bundle["total_records"], 5)
		check("review attention items", review_bundle["total_attention_items"], 2)
		check("review source summary count", len(review_bundle["source_file_summary"]), 3)

		corrected = apply_user_category_corrections(review_bundle, [
			{"transaction_id": unknown_id, "category": "household"},
			{"transaction_id": fuel_id, "category": "fuel"},
		], default_category=default_category)
		check("corrections requested", corrected["corrections_requested"], 2)
		check("corrections applied", corrected["corrections_applied"], 1)
		check("unchanged corrections", corrected["unchanged_corrections"], 1)
		check("post-correction uncategorized count", corrected["uncategorized_count"], 0)

		validated = revalidate_review_bundle(corrected, default_category=default_category)
		check("validation passed", validated["validation_passed"], True)
		check("validation issues", validated["validation_issues"], [])

		corrupted = dict(corrected)
		corrupted["total_records"] = 999
		validated_bad = revalidate_review_bundle(corrupted, default_category=default_category)
		check("corrupted validation passed", validated_bad["validation_passed"], False)
		check("corrupted validation issue", validated_bad["validation_issues"], ["total_records mismatch: reported 999, rebuilt 5."])

		finalized_ok = finalize_review_bundle(corrected, default_category=default_category)
		check("finalized ready", finalized_ok["ready_for_save"], True)
		check("finalized blocking issues", finalized_ok["blocking_issues"], [])
		check("finalized rejected row count", finalized_ok["excluded_rejected_row_count"], 1)

		finalized_blocked = finalize_review_bundle(review_bundle, default_category=default_category)
		check("blocked finalized ready", finalized_blocked["ready_for_save"], False)
		check("blocked finalized issues", finalized_blocked["blocking_issues"], ["uncategorized records remain: 1."])

	return {
		"passed": len(failures) == 0,
		"checks_passed": len(passes),
		"checks_failed": len(failures),
		"pass_names": passes,
		"failures": failures,
	}
