"""
IM8 Validator Service
Validates IM8 assessment document structure and data
"""

import re
from typing import Dict, List, Any, Tuple
from datetime import datetime


class IM8ValidationError(Exception):
    """Custom exception for IM8 validation errors"""
    def __init__(self, message: str, error_code: str, field: str = None):
        self.message = message
        self.error_code = error_code
        self.field = field
        super().__init__(self.message)


class IM8Validator:
    """Validate IM8 assessment documents"""
    
    # Valid status values
    VALID_STATUSES = ["Implemented", "Partial", "Not Started"]
    
    # Control ID format: IM8-DD-CC (e.g., IM8-01-01, IM8-02-05)
    CONTROL_ID_PATTERN = r"^IM8-\d{2}-\d{2}$"
    
    # Expected domain IDs
    EXPECTED_DOMAINS = ["Domain 1", "Domain 2"]
    
    # Required metadata fields
    REQUIRED_METADATA_FIELDS = [
        "project_id",
        "project_name",
        "framework",
        "assessment_period",
        "agency",
        "contact_email"
    ]
    
    def validate_im8_document(
        self, 
        parsed_data: Dict[str, Any],
        strict_mode: bool = False
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate complete IM8 document
        
        Args:
            parsed_data: Parsed IM8 data from ExcelProcessor
            strict_mode: If True, treat warnings as errors
            
        Returns:
            Tuple of (is_valid, list of validation errors/warnings)
        """
        errors = []
        
        # 1. Validate metadata
        try:
            self._validate_metadata(parsed_data.get("metadata", {}))
        except IM8ValidationError as e:
            errors.append({
                "type": "error",
                "code": e.error_code,
                "field": e.field,
                "message": e.message
            })
        
        # 2. Validate domains structure
        domains = parsed_data.get("domains", [])
        if len(domains) != 2:
            errors.append({
                "type": "error",
                "code": "INVALID_DOMAIN_COUNT",
                "field": "domains",
                "message": f"Expected 2 domains, found {len(domains)}"
            })
        
        # 3. Validate each domain
        for idx, domain in enumerate(domains):
            domain_errors = self._validate_domain(domain, idx + 1)
            errors.extend(domain_errors)
        
        # 4. Validate reference policies
        policies = parsed_data.get("reference_policies", [])
        policy_errors = self._validate_reference_policies(policies)
        errors.extend(policy_errors)
        
        # 5. Cross-validate summary with actual data
        summary_errors = self._validate_summary(
            parsed_data.get("summary", {}),
            domains
        )
        errors.extend(summary_errors)
        
        # Determine if valid (no errors, or only warnings if not strict)
        error_count = sum(1 for e in errors if e["type"] == "error")
        is_valid = error_count == 0
        
        if strict_mode:
            warning_count = sum(1 for e in errors if e["type"] == "warning")
            is_valid = is_valid and warning_count == 0
        
        return is_valid, errors
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate metadata section"""
        # Check required fields
        for field in self.REQUIRED_METADATA_FIELDS:
            if field not in metadata or not metadata[field]:
                raise IM8ValidationError(
                    f"Required metadata field '{field}' is missing or empty",
                    "MISSING_REQUIRED_FIELD",
                    field=field
                )
        
        # Validate framework is IM8
        if metadata.get("framework", "").upper() != "IM8":
            raise IM8ValidationError(
                f"Framework must be 'IM8', found '{metadata.get('framework')}'",
                "INVALID_FRAMEWORK",
                field="framework"
            )
        
        # Validate email format
        email = metadata.get("contact_email", "")
        if email and not self._is_valid_email(email):
            raise IM8ValidationError(
                f"Invalid email format: {email}",
                "INVALID_EMAIL",
                field="contact_email"
            )
        
        # Validate project_id is numeric or valid format
        project_id = metadata.get("project_id")
        if project_id and not str(project_id).strip():
            raise IM8ValidationError(
                "Project ID cannot be empty",
                "INVALID_PROJECT_ID",
                field="project_id"
            )
    
    def _validate_domain(
        self, 
        domain: Dict[str, Any], 
        expected_number: int
    ) -> List[Dict[str, Any]]:
        """Validate single domain"""
        errors = []
        
        # Check domain structure
        if "domain_name" not in domain:
            errors.append({
                "type": "error",
                "code": "MISSING_DOMAIN_NAME",
                "field": f"domains[{expected_number-1}].domain_name",
                "message": f"Domain {expected_number} missing domain_name"
            })
        
        # Validate controls
        controls = domain.get("controls", [])
        if len(controls) == 0:
            errors.append({
                "type": "error",
                "code": "NO_CONTROLS",
                "field": f"domains[{expected_number-1}].controls",
                "message": f"Domain {expected_number} has no controls"
            })
        
        for idx, control in enumerate(controls):
            control_errors = self._validate_control(
                control, 
                expected_number, 
                idx + 1
            )
            errors.extend(control_errors)
        
        return errors
    
    def _validate_control(
        self, 
        control: Dict[str, Any],
        domain_number: int,
        control_index: int
    ) -> List[Dict[str, Any]]:
        """Validate single control"""
        errors = []
        field_prefix = f"domains[{domain_number-1}].controls[{control_index-1}]"
        
        # 1. Validate Control ID format
        control_id = control.get("control_id", "")
        if not control_id:
            errors.append({
                "type": "error",
                "code": "MISSING_CONTROL_ID",
                "field": f"{field_prefix}.control_id",
                "message": f"Control {control_index} in Domain {domain_number} missing Control ID"
            })
        elif not re.match(self.CONTROL_ID_PATTERN, control_id):
            errors.append({
                "type": "error",
                "code": "INVALID_CONTROL_ID_FORMAT",
                "field": f"{field_prefix}.control_id",
                "message": f"Invalid Control ID format: {control_id}. Expected format: IM8-DD-CC"
            })
        else:
            # Validate domain number matches control ID
            expected_domain = f"{domain_number:02d}"
            control_domain = control_id.split("-")[1] if "-" in control_id else ""
            if control_domain != expected_domain:
                errors.append({
                    "type": "error",
                    "code": "CONTROL_DOMAIN_MISMATCH",
                    "field": f"{field_prefix}.control_id",
                    "message": f"Control ID {control_id} domain mismatch. Expected Domain {domain_number}"
                })
        
        # 2. Validate Control Name
        if not control.get("control_name", "").strip():
            errors.append({
                "type": "error",
                "code": "MISSING_CONTROL_NAME",
                "field": f"{field_prefix}.control_name",
                "message": f"Control {control_id} missing Control Name"
            })
        
        # 3. Validate Description
        if not control.get("description", "").strip():
            errors.append({
                "type": "warning",
                "code": "MISSING_DESCRIPTION",
                "field": f"{field_prefix}.description",
                "message": f"Control {control_id} missing Description"
            })
        
        # 4. Validate Status
        status = control.get("status", "")
        if not status:
            errors.append({
                "type": "error",
                "code": "MISSING_STATUS",
                "field": f"{field_prefix}.status",
                "message": f"Control {control_id} missing Status"
            })
        elif status not in self.VALID_STATUSES:
            errors.append({
                "type": "error",
                "code": "INVALID_STATUS",
                "field": f"{field_prefix}.status",
                "message": f"Control {control_id} has invalid Status: {status}. Valid values: {', '.join(self.VALID_STATUSES)}"
            })
        
        # 5. Validate Evidence
        if not control.get("has_embedded_evidence", False):
            errors.append({
                "type": "error",
                "code": "MISSING_EVIDENCE",
                "field": f"{field_prefix}.evidence",
                "message": f"Control {control_id} missing embedded PDF evidence"
            })
        
        # 6. Validate Implementation Date (if status is Implemented)
        if status == "Implemented":
            if not control.get("implementation_date"):
                errors.append({
                    "type": "warning",
                    "code": "MISSING_IMPLEMENTATION_DATE",
                    "field": f"{field_prefix}.implementation_date",
                    "message": f"Control {control_id} marked as Implemented but missing Implementation Date"
                })
        
        # 7. Validate Notes (optional but recommended)
        if not control.get("notes", "").strip():
            errors.append({
                "type": "info",
                "code": "MISSING_NOTES",
                "field": f"{field_prefix}.notes",
                "message": f"Control {control_id} has no implementation notes (recommended)"
            })
        
        return errors
    
    def _validate_reference_policies(
        self, 
        policies: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate reference policies section"""
        errors = []
        
        if len(policies) == 0:
            errors.append({
                "type": "warning",
                "code": "NO_REFERENCE_POLICIES",
                "field": "reference_policies",
                "message": "No reference policies provided"
            })
        
        for idx, policy in enumerate(policies):
            if not policy.get("policy_name", "").strip():
                errors.append({
                    "type": "warning",
                    "code": "EMPTY_POLICY_ROW",
                    "field": f"reference_policies[{idx}].policy_name",
                    "message": f"Reference policy row {idx+1} has no policy name"
                })
        
        return errors
    
    def _validate_summary(
        self, 
        summary: Dict[str, Any],
        domains: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate summary calculations match actual data"""
        errors = []
        
        # Calculate actual stats from domains
        actual_stats = self._calculate_actual_stats(domains)
        
        # Compare with summary (if summary has these fields)
        summary_total = summary.get("total_controls")
        if summary_total is not None and summary_total != actual_stats["total_controls"]:
            errors.append({
                "type": "warning",
                "code": "SUMMARY_MISMATCH",
                "field": "summary.total_controls",
                "message": f"Summary shows {summary_total} controls, but found {actual_stats['total_controls']}"
            })
        
        return errors
    
    def _calculate_actual_stats(self, domains: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate actual statistics from domain data"""
        stats = {
            "total_controls": 0,
            "implemented": 0,
            "partial": 0,
            "not_started": 0
        }
        
        for domain in domains:
            for control in domain.get("controls", []):
                stats["total_controls"] += 1
                status = control.get("status", "")
                
                if status == "Implemented":
                    stats["implemented"] += 1
                elif status == "Partial":
                    stats["partial"] += 1
                elif status == "Not Started":
                    stats["not_started"] += 1
        
        return stats
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
    
    def format_validation_report(
        self, 
        validation_errors: List[Dict[str, Any]]
    ) -> str:
        """Format validation errors into human-readable report"""
        if not validation_errors:
            return "✅ All validations passed"
        
        report_lines = ["IM8 Validation Report", "=" * 50, ""]
        
        # Group by type
        errors = [e for e in validation_errors if e["type"] == "error"]
        warnings = [e for e in validation_errors if e["type"] == "warning"]
        infos = [e for e in validation_errors if e["type"] == "info"]
        
        if errors:
            report_lines.append(f"❌ ERRORS ({len(errors)}):")
            for e in errors:
                report_lines.append(f"  [{e['code']}] {e['message']}")
                if e.get("field"):
                    report_lines.append(f"    Field: {e['field']}")
            report_lines.append("")
        
        if warnings:
            report_lines.append(f"⚠️  WARNINGS ({len(warnings)}):")
            for w in warnings:
                report_lines.append(f"  [{w['code']}] {w['message']}")
            report_lines.append("")
        
        if infos:
            report_lines.append(f"ℹ️  INFO ({len(infos)}):")
            for i in infos:
                report_lines.append(f"  [{i['code']}] {i['message']}")
            report_lines.append("")
        
        return "\n".join(report_lines)


# Singleton instance
_validator = None

def get_im8_validator() -> IM8Validator:
    """Get or create IM8Validator instance"""
    global _validator
    if _validator is None:
        _validator = IM8Validator()
    return _validator
