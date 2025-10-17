# MediLink_Display_Utils.py
# Display utility functions extracted from MediLink_UI.py to eliminate circular dependencies
# Provides centralized display functions for insurance options and patient summaries

from datetime import datetime

# Use core utilities for standardized imports
from MediCafe.core_utils import get_shared_config_loader, extract_medilink_config
MediLink_ConfigLoader = get_shared_config_loader()

def display_insurance_options(insurance_options=None):
    """Display insurance options, loading from config if not provided"""
    
    if insurance_options is None:
        config, _ = MediLink_ConfigLoader.load_configuration()
        medi = extract_medilink_config(config)
        insurance_options = medi.get('insurance_options', {})
    
    print("\nInsurance Type Options (SBR09 Codes):")
    print("-" * 50)
    for code, description in sorted(insurance_options.items()):
        print("{:>3}: {}".format(code, description))
    print("-" * 50)
    print("Note: '12' (PPO) is the default if no selection is made.")
    print()  # Add a blank line for better readability

def display_patient_summaries(detailed_patient_data):
    """
    Displays summaries of all patients and their suggested endpoints.
    """
    print("\nSummary of patient details and suggested endpoint:")
    
    # Sort by insurance_type_source priority for clearer grouping
    priority = {'API': 0, 'MANUAL': 1, 'DEFAULT': 2, 'DEFAULT_FALLBACK': 2}
    def sort_key(item):
        src = item.get('insurance_type_source', '')
        return (priority.get(src, 2), item.get('surgery_date', ''), item.get('patient_name', ''))
    sorted_data = sorted(detailed_patient_data, key=sort_key)

    for index, summary in enumerate(sorted_data, start=1):
        try:
            display_file_summary(index, summary)
        except KeyError as e:
            print("Summary at index {} is missing key: {}".format(index, e))
    print() # add blank line for improved readability.
    print("Legend: Src=API (auto), MAN (manual), DEF (default) | [DUP] indicates a previously submitted matching claim")

def display_file_summary(index, summary):
    # Ensure surgery_date is converted to a datetime object
    surgery_date = datetime.strptime(summary['surgery_date'], "%m-%d-%y")
    
    # Add header row if it's the first index
    if index == 1:
        print("{:<3} {:5} {:<10} {:<20} {:<15} {:<3} {:<5} {:<8} {:<20}".format(
            "No.", "Date", "ID", "Name", "Primary Ins.", "IT", "Src", "Flag", "Current Endpoint"
        ))
        print("-"*100)

    # Check if insurance_type is available; if not, set a default placeholder (this should already be '12' at this point)
    insurance_type = summary.get('insurance_type', '--')
    insurance_source = summary.get('insurance_type_source', '')
    duplicate_flag = '[DUP]' if summary.get('duplicate_candidate') else ''
    
    # Get the effective endpoint (confirmed > user preference > suggestion > default)
    effective_endpoint = (summary.get('confirmed_endpoint') or 
                         summary.get('user_preferred_endpoint') or 
                         summary.get('suggested_endpoint', 'AVAILITY'))

    # Format insurance type for display - prioritize code (SBR09/insuranceTypeCode)
    if insurance_type and len(insurance_type) <= 3:
        insurance_display = insurance_type
    else:
        # If description was provided instead of code, truncate respectfully
        insurance_display = insurance_type[:3] if insurance_type else '--'

    # Shorten source for compact display
    if insurance_source in ['DEFAULT_FALLBACK', 'DEFAULT']:
        source_display = 'DEF'
    elif insurance_source == 'MANUAL':
        source_display = 'MAN'
    elif insurance_source == 'API':
        source_display = 'API'
    else:
        source_display = ''

    print("{:02d}. {:5} ({:<8}) {:<20} {:<15} {:<3} {:<5} {:<8} {:<20}".format(
        index,
        surgery_date.strftime("%m-%d"),
        summary['patient_id'],
        summary['patient_name'][:20],
        summary['primary_insurance'][:15],
        insurance_display,
        source_display,
        duplicate_flag,
        effective_endpoint[:20]))

def display_enhanced_deductible_table(data, context="pre_api", title=None):
    """
    Enhanced deductible table display with unified philosophy for both pre-API and post-API contexts.
    
    Args:
        data: List of patient records (CSV rows for pre_api, or eligibility results for post_api)
        context: "pre_api" (valid rows identification) or "post_api" (eligibility results)
        title: Custom title for the table
    """
    if not data:
        print("No data to display.")
        return
    
    # Set default titles based on context
    if title is None:
        if context == "pre_api":
            title = "Valid Patients for Deductible Lookup ({} patients found)".format(len(data))
        else:
            title = "Eligibility Lookup Results"
    
    print("\n{}".format(title))
    print()
    
    # Normalize data for consistent processing
    normalized_data = []
    for item in data:
        if context == "pre_api":
            # Pre-API: working with CSV row data
            normalized_item = _normalize_pre_api_data(item)
        else:
            # Post-API: working with eligibility results
            normalized_item = _normalize_post_api_data(item)
        
        if normalized_item:
            normalized_data.append(normalized_item)
    
    if not normalized_data:
        print("No valid data to display after normalization.")
        return
    
    # Sort data: by patient name, then by service date
    normalized_data.sort(key=lambda x: (
        x.get('patient_name', '').upper(),
        x.get('service_date_sort', datetime.min),
        x.get('patient_id', '')
    ))
    
    # Group by patient for enhanced display
    grouped_data = _group_by_patient(normalized_data)
    
    # Calculate column widths for proper alignment
    col_widths = _calculate_column_widths(normalized_data, context)
    
    # Display header
    _display_table_header(col_widths, context)
    
    # Display data with grouping
    line_number = 1
    for patient_id, patient_records in grouped_data.items():
        for idx, record in enumerate(patient_records):
            if idx == 0:
                # Primary line with line number
                _display_primary_line(record, line_number, col_widths, context)
                line_number += 1
            else:
                # Secondary lines with dashes
                _display_secondary_line(record, col_widths, context)
    
    print()  # Add blank line after table

def _normalize_pre_api_data(row):
    """Normalize CSV row data for pre-API display"""
    try:
        # Extract patient name
        patient_name = _format_patient_name_from_csv(row)
        
        # Extract service date
        service_date_display, service_date_sort = _extract_service_date_from_csv(row)
        
        # Extract other fields
        dob = row.get('Patient DOB', row.get('DOB', ''))
        member_id = row.get('Primary Policy Number', row.get('Ins1 Member ID', '')).strip()
        payer_id = row.get('Ins1 Payer ID', '')
        patient_id = row.get('Patient ID #2', row.get('Patient ID', ''))

        # Surrogate key and warnings if patient_id missing/blank
        if not str(patient_id).strip():
            surrogate = "{}:{}".format(dob, member_id)
            patient_id = surrogate
            try:
                # Print visible warning and log as WARNING event
                print("Warning: Missing Patient ID in CSV row; using surrogate key {}".format(surrogate))
                MediLink_ConfigLoader.log(
                    "Missing Patient ID in CSV; using surrogate key {}".format(surrogate),
                    level="WARNING"
                )
            except Exception:
                pass
        
        return {
            'patient_id': str(patient_id),
            'patient_name': patient_name,
            'dob': dob,
            'member_id': member_id,
            'payer_id': str(payer_id),
            'service_date_display': service_date_display,
            'service_date_sort': service_date_sort,
            'status': 'Ready',
            'insurance_type': '',
            'policy_status': '',
            'remaining_amount': ''
        }
    except Exception as e:
        MediLink_ConfigLoader.log("Error normalizing pre-API data: {}".format(e), level="WARNING")
        return None

def _normalize_post_api_data(eligibility_result):
    """Normalize eligibility result data for post-API display"""
    try:
        # Handle the enhanced format that comes from convert_eligibility_to_enhanced_format
        if isinstance(eligibility_result, dict):
            normalized = {
                'patient_id': str(eligibility_result.get('patient_id', '')),
                'patient_name': str(eligibility_result.get('patient_name', '')),
                'dob': str(eligibility_result.get('dob', '')),
                'member_id': str(eligibility_result.get('member_id', '')),
                'payer_id': str(eligibility_result.get('payer_id', '')),
                'service_date_display': str(eligibility_result.get('service_date_display', '')),
                'service_date_sort': eligibility_result.get('service_date_sort', datetime.min),
                'status': str(eligibility_result.get('status', 'Processed')),
                'insurance_type': str(eligibility_result.get('insurance_type', '')),
                'policy_status': str(eligibility_result.get('policy_status', '')),
                'remaining_amount': str(eligibility_result.get('remaining_amount', '')),
                'data_source': str(eligibility_result.get('data_source', '')),
                'error_reason': str(eligibility_result.get('error_reason', '')),
                'is_successful': bool(eligibility_result.get('is_successful', False))
            }

            # Default unknown patient name when blank
            try:
                if not normalized['patient_name'].strip():
                    normalized['patient_name'] = 'Unknown Patient'
            except Exception:
                normalized['patient_name'] = 'Unknown Patient'

            # Surrogate key and warnings if patient_id missing/blank
            try:
                if not normalized['patient_id'].strip():
                    surrogate = "{}:{}".format(normalized.get('dob', ''), normalized.get('member_id', ''))
                    normalized['patient_id'] = surrogate
                    print("Warning: Missing Patient ID in eligibility result; using surrogate key {}".format(surrogate))
                    MediLink_ConfigLoader.log(
                        "Missing Patient ID in eligibility result; using surrogate key {}".format(surrogate),
                        level="WARNING"
                    )
            except Exception:
                pass

            return normalized
        else:
            MediLink_ConfigLoader.log("Unexpected eligibility result format: {}".format(type(eligibility_result)), level="WARNING")
            return None
    except Exception as e:
        MediLink_ConfigLoader.log("Error normalizing post-API data: {}".format(e), level="WARNING")
        return None

def _format_patient_name_from_csv(row):
    """Format patient name as LAST, FIRST from CSV data"""
    try:
        # Check if Patient Name is already constructed
        if 'Patient Name' in row and row['Patient Name']:
            return str(row['Patient Name'])[:25]  # Limit length
        
        # Otherwise construct from parts
        first_name = row.get('Patient First', '').strip()
        last_name = row.get('Patient Last', '').strip()
        middle_name = row.get('Patient Middle', '').strip()
        
        if last_name or first_name:
            # Format as "LAST, FIRST MIDDLE"
            name_parts = []
            if last_name:
                name_parts.append(last_name)
            if first_name:
                if name_parts:
                    name_parts.append(", {}".format(first_name))
                else:
                    name_parts.append(first_name)
            if middle_name:
                name_parts.append(" {}".format(middle_name[:1]))  # Just first initial
            
            return ''.join(name_parts)[:25]  # Limit length
        
        return "Unknown Patient"
    except Exception:
        return "Unknown Patient"

def _extract_service_date_from_csv(row):
    """Extract and format service date from CSV data"""
    try:
        # Try Surgery Date first
        surgery_date = row.get('Surgery Date')
        if surgery_date:
            if isinstance(surgery_date, datetime):
                if surgery_date != datetime.min:
                    return surgery_date.strftime('%m-%d'), surgery_date
            elif isinstance(surgery_date, str) and surgery_date.strip() and surgery_date != 'MISSING':
                try:
                    # Try to parse common date formats
                    for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = datetime.strptime(surgery_date.strip(), fmt)
                            return parsed_date.strftime('%m-%d'), parsed_date
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        # Try other possible date fields
        for date_field in ['Date of Service', 'Service Date', 'DOS']:
            date_value = row.get(date_field)
            if date_value and isinstance(date_value, str) and date_value.strip():
                try:
                    for fmt in ['%m-%d-%Y', '%m/%d/%Y', '%Y-%m-%d']:
                        try:
                            parsed_date = datetime.strptime(date_value.strip(), fmt)
                            return parsed_date.strftime('%m-%d'), parsed_date
                        except ValueError:
                            continue
                except Exception:
                    pass
        
        # Default to unknown
        return "Unknown", datetime.min
    except Exception:
        return "Unknown", datetime.min

def _group_by_patient(normalized_data):
    """Group normalized data by patient ID"""
    grouped = {}
    for record in normalized_data:
        patient_id = record.get('patient_id', 'Unknown')
        if patient_id not in grouped:
            grouped[patient_id] = []
        grouped[patient_id].append(record)
    return grouped

def _calculate_column_widths(normalized_data, context):
    """Calculate optimal column widths based on data"""
    widths = {
        'patient_id': max(10, max(len(str(r.get('patient_id', ''))) for r in normalized_data) if normalized_data else 10),
        'patient_name': max(20, max(len(str(r.get('patient_name', ''))) for r in normalized_data) if normalized_data else 20),
        'dob': 10,
        'member_id': max(12, max(len(str(r.get('member_id', ''))) for r in normalized_data) if normalized_data else 12),
        'payer_id': 8,
        'service_date': 10,
        'status': 8
    }
    
    if context == "post_api":
        widths.update({
            'insurance_type': max(15, max(len(str(r.get('insurance_type', ''))) for r in normalized_data) if normalized_data else 15),
            'policy_status': 12,
            'remaining_amount': 12,
            'data_source': 10
        })
    
    return widths

def _display_table_header(col_widths, context):
    """Display table header based on context"""
    if context == "pre_api":
        header_format = "No.  {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        header = header_format.format(
            "Patient ID", col_widths['patient_id'],
            "Patient Name", col_widths['patient_name'],
            "DOB", col_widths['dob'],
            "Member ID", col_widths['member_id'],
            "Payer ID", col_widths['payer_id'],
            "Service Date", col_widths['service_date'],
            "Status", col_widths['status']
        )
        print(header)
        print("-" * len(header))
    else:
        header_format = "No.  {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        header = header_format.format(
            "Patient ID", col_widths['patient_id'],
            "Patient Name", col_widths['patient_name'],
            "DOB", col_widths['dob'],
            "Member ID", col_widths['member_id'],
            "Payer ID", col_widths['payer_id'],
            "Service Date", col_widths['service_date'],
            "Insurance Type Code", col_widths['insurance_type'],
            "Policy Status", col_widths['policy_status'],
            "Remaining Amt", col_widths['remaining_amount']
        )
        header_format += " | {:<{}}"
        header += " | {}".format("Data Source", col_widths.get('data_source', 10))
        print(header)
        print("-" * len(header))

def _display_primary_line(record, line_number, col_widths, context):
    """Display primary line with line number"""
    if context == "pre_api":
        # Enhanced status display for pre-API context
        status = record.get('status', '')
        if status == 'Ready':
            status_display = '[READY]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "{:03d}: {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            line_number,
            str(record.get('patient_id', ''))[:col_widths['patient_id']], col_widths['patient_id'],
            str(record.get('patient_name', ''))[:col_widths['patient_name']], col_widths['patient_name'],
            str(record.get('dob', ''))[:col_widths['dob']], col_widths['dob'],
            str(record.get('member_id', ''))[:col_widths['member_id']], col_widths['member_id'],
            str(record.get('payer_id', ''))[:col_widths['payer_id']], col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            status_display[:col_widths['status']], col_widths['status']
        ))
    else:
        # Enhanced status display for post-API context
        status = record.get('status', '')
        if status == 'Processed':
            status_display = '[DONE]'
        elif status == 'Error':
            status_display = '[ERROR]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "{:03d}: {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            line_number,
            str(record.get('patient_id', ''))[:col_widths['patient_id']], col_widths['patient_id'],
            str(record.get('patient_name', ''))[:col_widths['patient_name']], col_widths['patient_name'],
            str(record.get('dob', ''))[:col_widths['dob']], col_widths['dob'],
            str(record.get('member_id', ''))[:col_widths['member_id']], col_widths['member_id'],
            str(record.get('payer_id', ''))[:col_widths['payer_id']], col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            str(record.get('insurance_type', ''))[:col_widths['insurance_type']], col_widths['insurance_type'],
            str(record.get('policy_status', ''))[:col_widths['policy_status']], col_widths['policy_status'],
            str(record.get('remaining_amount', ''))[:col_widths['remaining_amount']], col_widths['remaining_amount'],
            str(record.get('data_source', ''))[:col_widths['data_source']], col_widths['data_source']
        ))

        # After primary line in post-API view, display an explanatory error row when appropriate
        _maybe_display_error_row(record, context)

def _display_secondary_line(record, col_widths, context):
    """Display secondary line with dashes for grouped data"""
    patient_id_dashes = '-' * min(len(str(record.get('patient_id', ''))), col_widths['patient_id'])
    patient_name_dashes = '-' * min(len(str(record.get('patient_name', ''))), col_widths['patient_name'])
    dob_dashes = '-' * min(len(str(record.get('dob', ''))), col_widths['dob'])
    member_id_dashes = '-' * min(len(str(record.get('member_id', ''))), col_widths['member_id'])
    payer_id_dashes = '-' * min(len(str(record.get('payer_id', ''))), col_widths['payer_id'])
    
    if context == "pre_api":
        # Enhanced status display for pre-API context
        status = record.get('status', '')
        if status == 'Ready':
            status_display = '[READY]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "     {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            patient_id_dashes, col_widths['patient_id'],
            patient_name_dashes, col_widths['patient_name'],
            dob_dashes, col_widths['dob'],
            member_id_dashes, col_widths['member_id'],
            payer_id_dashes, col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            status_display[:col_widths['status']], col_widths['status']
        ))
    else:
        insurance_type_dashes = '-' * min(len(str(record.get('insurance_type', ''))), col_widths['insurance_type'])
        policy_status_dashes = '-' * min(len(str(record.get('policy_status', ''))), col_widths['policy_status'])
        
        # Enhanced status display for post-API context
        status = record.get('status', '')
        if status == 'Processed':
            status_display = '[DONE]'
        elif status == 'Error':
            status_display = '[ERROR]'
        else:
            status_display = '[{}]'.format(status.upper())
        
        line_format = "     {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}} | {:<{}}"
        print(line_format.format(
            patient_id_dashes, col_widths['patient_id'],
            patient_name_dashes, col_widths['patient_name'],
            dob_dashes, col_widths['dob'],
            member_id_dashes, col_widths['member_id'],
            payer_id_dashes, col_widths['payer_id'],
            str(record.get('service_date_display', ''))[:col_widths['service_date']], col_widths['service_date'],
            insurance_type_dashes, col_widths['insurance_type'],
            policy_status_dashes, col_widths['policy_status'],
            str(record.get('remaining_amount', ''))[:col_widths['remaining_amount']], col_widths['remaining_amount'],
            str(record.get('data_source', ''))[:col_widths['data_source']], col_widths['data_source']
        )) 

        # For grouped secondary lines, we do not repeat error rows

def _maybe_display_error_row(record, context):
    """Print an explanatory error row beneath the primary line when name or other lookups failed."""
    try:
        if context != 'post_api':
            return
        name_unknown = (not record.get('patient_name')) or (record.get('patient_name') == 'Unknown Patient')
        has_error = (record.get('status') == 'Error') or (record.get('data_source') in ['None', 'Error'])
        amount_missing = (str(record.get('remaining_amount', '')) == 'Not Found')
        reason = record.get('error_reason', '')

        if not reason:
            if name_unknown:
                reason = 'Patient name could not be determined from API responses or CSV backfill'
            elif amount_missing:
                reason = 'Deductible remaining amount not found in eligibility response'
            elif has_error:
                reason = 'Eligibility lookup encountered an error; see logs for details'

        # Prefer diagnostics lines when present; otherwise fall back to reason
        diagnostics = record.get('diagnostics', []) or []
        if diagnostics:
            # Only show first 1-2 lines to avoid noise in XP console
            to_show = diagnostics[:2]
            for line in to_show:
                print("     >> {}".format(line))
        elif reason:
            print("     >> Error: {}".format(reason))
    except Exception:
        # Never let diagnostics break table rendering
        pass