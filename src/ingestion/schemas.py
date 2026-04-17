from dataclasses import dataclass
from typing import Optional

@dataclass
class TransactionRecord:
	transaction_id: str
	date: str			# YYYY-MM-DD
	amount: float		# income positive, expense negative
	description: str		# raw description
	normalized_desc: str
	category: str
	source_file: str
	row_index: int
	account: Optional[str] = None
	notes: Optional[str] = None

ACCEPTED_COLUMN_ALIASES = {
	"date": [
		"date",
		"transaction date",
		"posted date",
	],
	"description": [
		"description",
		"memo",
		"details",
		"transaction",
	],
	"amount": [
		"amount",
	],
	"debit": [
		"debit",
		"withdrawal",
	],
	"credit": [
		"credit",
		"deposit",
	],
}

def normalize_header_name(name: str) -> str:
	return " ".join(name.strip().lower().split())


def detect_column_mapping(headers: list[str]) -> dict[str, str]:
	normalized_to_original = {
		normalize_header_name(header): header
		for header in headers
	}

	mapping: dict[str, str] = {}

	for canonical_name, aliases in ACCEPTED_COLUMN_ALIASES.items():
		for alias in aliases:
			if alias in normalized_to_original:
				mapping[canonical_name] = normalized_to_original[alias]
				break

	has_amount = "amount" in mapping
	has_debit_credit = "debit" in mapping and "credit" in mapping

	if "date" not in mapping:
		raise ValueError("Missing required column: date")

	if "description" not in mapping:
		raise ValueError("Missing required column: description")

	if not has_amount and not has_debit_credit:
		raise ValueError(
			"Missing required amount columns: need either 'amount' or both 'debit' and 'credit'"
		)

	return mapping
