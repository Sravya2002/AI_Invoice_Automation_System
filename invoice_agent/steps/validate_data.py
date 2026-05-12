"""
Validation step — rule-based checks for extracted invoice data.
Day 11 Requirement: Validation + Decision Output.
"""
from typing import Dict, Any, List, Tuple
from models.output_schema import ValidationResult
from datetime import datetime

class ValidateDataStep:
    """
    Step 5 — Validate extracted data and assign a confidence status.
    """

    def __init__(self, logger):
        self.logger = logger

    def execute(self, metadata: Dict[str, Any]) -> ValidationResult:
        """
        Run validation rules against extracted metadata.
        """
        issues = []
        recommendations = []
        score = 1.0  # Start with perfect score

        self.logger.log_info(f"[VALIDATE] Validating invoice: {metadata.get('invoice_number')}")

        # 1. Mandatory Field Check
        mandatory_fields = [
            ('invoice_number', 'MISSING_INVOICE_NUMBER'),
            ('invoice_date', 'MISSING_INVOICE_DATE'),
            ('vendor_name', 'MISSING_VENDOR_NAME'),
            ('total_amount', 'MISSING_TOTAL_AMOUNT'),
            ('currency', 'MISSING_CURRENCY')
        ]

        for field, code in mandatory_fields:
            val = metadata.get(field)
            if val is None or val == "" or val == 0.0:
                issues.append(code)
                score -= 0.2
                recommendations.append(f"Manually check the {field} in the PDF.")

        # 2. Rule-based Total Validator
        total = metadata.get('total_amount', 0.0)
        tax = metadata.get('tax_amount', 0.0)

        if total is not None and total < 0:
            issues.append('NEGATIVE_TOTAL')
            score -= 0.3
            recommendations.append("Total amount is negative. Verify if this is a credit note.")

        if total is not None and tax is not None:
            if tax > total:
                issues.append('TAX_EXCEEDS_TOTAL')
                score -= 0.4
                recommendations.append("Tax amount is greater than total. Check for extraction error.")
            elif tax == total and total > 0:
                issues.append('TAX_EQUALS_TOTAL')
                score -= 0.1
                recommendations.append("Tax equals total. Unusual but possible; please verify.")

        # 3. Date Consistency
        date_str = metadata.get('invoice_date')
        if date_str:
            try:
                # Basic check if it's a valid date string
                inv_date = datetime.strptime(date_str, "%Y-%m-%d")
                # Future date check
                if inv_date > datetime.now():
                    issues.append('FUTURE_DATE')
                    score -= 0.2
                    recommendations.append("Invoice date is in the future. Verify document validity.")
            except Exception:
                issues.append('DATE_PARSE_FAILED')
                score -= 0.3
                recommendations.append("Could not parse invoice date format.")

        # 4. Final Status Decision
        # Requirement: If any mandatory fields are missing, status MUST be FAILED
        mandatory_issues = ['MISSING_INVOICE_NUMBER', 'MISSING_INVOICE_DATE', 
                            'MISSING_VENDOR_NAME', 'MISSING_TOTAL_AMOUNT', 'MISSING_CURRENCY']
        
        has_mandatory_issue = any(issue in issues for issue in mandatory_issues)

        if has_mandatory_issue or score <= 0.4:
            status = "FAILED"
        elif issues: # Other non-mandatory issues (like FUTURE_DATE)
            status = "REVIEW"
        else:
            status = "SUCCESS"

        result = ValidationResult(
            status=status,
            confidence=max(0.0, min(1.0, score)),
            issues=issues,
            recommendations=recommendations
        )

        self.logger.log_info(f"[OK] Validation complete. Status: {status} (Score: {score:.2f})")
        if issues:
            self.logger.log_info(f"[!] Issues found: {', '.join(issues)}")

        return result
