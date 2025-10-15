from typing import Dict, Any, Optional, List
from datetime import date, datetime
import base64
import os
from pathlib import Path


def save_attachment(file_content_base64: str, filename: str, candidate_id: str, storage_path: Optional[str] = None) -> Optional[str]:
    """
    Save attachment file from base64 content to disk.
    
    Args:
        file_content_base64: Base64 encoded file content
        filename: Original filename
        candidate_id: Candidate ID for organizing files
        storage_path: Base directory path to save files (defaults to /tmp/workday_attachments)
                     Files will be saved to: {storage_path}/{candidate_id}/{filename}
    
    Returns:
        Path to saved file or None if failed
    """
    if not file_content_base64 or not filename or not candidate_id:
        return None
    
    try:
        # Check if content is already bytes (decoded) or string (base64 encoded)
        if isinstance(file_content_base64, bytes):
            # Already decoded binary content
            print(f"🔍 Content is already binary ({len(file_content_base64)} bytes) for {filename}")
            file_content = file_content_base64
        else:
            # Base64 string that needs decoding
            base64_length = len(file_content_base64)
            print(f"🔍 Base64 content length: {base64_length} chars for {filename}")
            
            # Decode base64
            file_content = base64.b64decode(file_content_base64)
        
        # Create storage directory: {storage_path}/{candidate_id}/
        if not storage_path:
            storage_path = "/tmp/workday_attachments"
        
        storage_dir = Path(storage_path) / candidate_id
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename to avoid path traversal
        safe_filename = os.path.basename(filename)
        
        # Save file
        file_path = storage_dir / safe_filename
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # Get file size for logging
        file_size_kb = len(file_content) / 1024
        print(f"✅ Saved PDF: {safe_filename} ({file_size_kb:.1f} KB) -> {file_path}")
        
        # Show first bytes to verify PDF header
        if len(file_content) > 4:
            header = file_content[:4]
            print(f"🔍 File header: {header} (should be b'%PDF' for valid PDF)")
        
        return str(file_path)
    except Exception as e:
        print(f"❌ Error saving attachment {filename} for candidate {candidate_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def to_date_string(value: Any) -> Optional[str]:
    """Convert datetime/date objects to ISO format string (YYYY-MM-DD)"""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        return value
    return str(value)


def extract_id_by_type(id_list: Any, id_type: str) -> Optional[str]:
    """Helper function to extract ID value by type from ID list"""
    if not id_list:
        return None
    
    if isinstance(id_list, dict):
        if id_list.get("type") == id_type:
            return id_list.get("_value_1")
        return None
    
    if isinstance(id_list, list):
        for id_item in id_list:
            if isinstance(id_item, dict) and id_item.get("type") == id_type:
                return id_item.get("_value_1")
    
    return None


def ensure_list(value: Any) -> List:
    """Ensure value is a list"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_get_reference(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    Safely get a _Reference field that might be a dict, list, or None.
    Returns the first item if it's a list, or the dict if it's a dict, or empty dict.
    """
    ref = data.get(key, {})
    if isinstance(ref, list):
        return ref[0] if ref else {}
    return ref or {}


def parse_candidate_reference(candidate_raw: Dict[str, Any], candidate_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Parse Candidate Reference data and related references (Pre-Hire, Worker).
    
    Args:
        candidate_raw: The top-level Candidate dict (contains Candidate_Reference)
        candidate_data: The Candidate_Data dict (contains Pre-Hire_Reference and Worker_Reference)
    
    Note: In the XML structure:
        - Candidate_Reference is at the Candidate level
        - Pre-Hire_Reference and Worker_Reference are inside Candidate_Data
    """
    parsed = {}
    
    if not candidate_raw:
        return parsed
    
    # Candidate Reference (from candidate_raw level)
    candidate_ref = safe_get_reference(candidate_raw, "Candidate_Reference")
    if candidate_ref:
        ids = ensure_list(candidate_ref.get("ID", []))
        parsed["candidate_id"] = extract_id_by_type(ids, "Candidate_ID")
        parsed["candidate_wid"] = extract_id_by_type(ids, "WID")
    
    # Pre-Hire Reference and Worker Reference are in candidate_data
    if candidate_data:
        # Pre-Hire Reference (if candidate was previously an applicant/pre-hire)
        pre_hire_ref = safe_get_reference(candidate_data, "Pre-Hire_Reference")
        if pre_hire_ref:
            ids = ensure_list(pre_hire_ref.get("ID", []))
            parsed["applicant_id"] = extract_id_by_type(ids, "Applicant_ID")
            parsed["applicant_wid"] = extract_id_by_type(ids, "WID")
        
        # Worker Reference (if candidate was converted to a worker/employee)
        worker_ref = safe_get_reference(candidate_data, "Worker_Reference")
        if worker_ref:
            ids = ensure_list(worker_ref.get("ID", []))
            parsed["associate_id"] = extract_id_by_type(ids, "Employee_ID")
            parsed["worker_wid"] = extract_id_by_type(ids, "WID")
    
    return parsed


def parse_candidate_personal_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Personal Data for Candidate - based on actual Workday XML structure"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Name data - actual structure uses Legal_Name, not Legal_Name_Data
    name_data = candidate_data.get("Name_Data", {})
    if name_data:
        # Try Legal_Name first (actual structure), fallback to Legal_Name_Data
        legal_name = name_data.get("Legal_Name", {})
        if not legal_name:
            legal_name = name_data.get("Legal_Name_Data", {})
        
        legal_name_detail = legal_name.get("Name_Detail_Data", {})
        parsed["first_name"] = legal_name_detail.get("First_Name")
        parsed["middle_name"] = legal_name_detail.get("Middle_Name")
        parsed["last_name"] = legal_name_detail.get("Last_Name")
        parsed["formatted_name"] = legal_name_detail.get("Formatted_Name")
        
        # Build full name if not provided
        if not parsed["formatted_name"] and parsed["first_name"] and parsed["last_name"]:
            middle = f" {parsed['middle_name']}" if parsed.get("middle_name") else ""
            parsed["formatted_name"] = f"{parsed['first_name']}{middle} {parsed['last_name']}"
        
        parsed["legal_name"] = parsed["formatted_name"]
        
        # Preferred name
        preferred_name = name_data.get("Preferred_Name", {})
        if not preferred_name:
            preferred_name = name_data.get("Preferred_Name_Data", {})
        preferred_name_detail = preferred_name.get("Name_Detail_Data", {})
        parsed["preferred_name"] = preferred_name_detail.get("Formatted_Name")
    
    # Gender and demographics - can be in Job_Application_Data -> Job_Applied_To_Data -> Personal_Information_Data
    # or in Personal_Data -> Personal_Information_Data
    personal_data = candidate_data.get("Personal_Data", {})
    if personal_data:
        birth_date_raw = personal_data.get("Birth_Date")
        parsed["birth_date"] = to_date_string(birth_date_raw)
        parsed["tobacco_use"] = personal_data.get("Tobacco_Use")
    
    # Try to get demographics from Job_Application_Data first (more common)
    job_app_data_list = ensure_list(candidate_data.get("Job_Application_Data", []))
    if job_app_data_list:
        job_app_data = job_app_data_list[0] if isinstance(job_app_data_list, list) else job_app_data_list
        
        # Job_Applied_To_Data can also be a list
        job_applied_to_raw = job_app_data.get("Job_Applied_To_Data", {})
        if isinstance(job_applied_to_raw, list):
            job_applied_to = job_applied_to_raw[0] if job_applied_to_raw else {}
        else:
            job_applied_to = job_applied_to_raw
        
        personal_info = job_applied_to.get("Personal_Information_Data", {})
        
        if personal_info:
            # Gender - can be a single dict or list of dicts
            gender_refs = ensure_list(personal_info.get("Gender_Reference", []))
            if gender_refs:
                gender_ref = gender_refs[0] if isinstance(gender_refs, list) else gender_refs
                if gender_ref:
                    gender_ids = ensure_list(gender_ref.get("ID", []))
                    for gid in gender_ids:
                        if isinstance(gid, dict) and gid.get("type") == "Gender_Code":
                            parsed["gender"] = gid.get("_value_1")
                            break
            
            # Ethnicity - can be a single dict or list of dicts
            ethnicity_refs = ensure_list(personal_info.get("Ethnicity_Reference", []))
            if ethnicity_refs:
                ethnicity_ref = ethnicity_refs[0] if isinstance(ethnicity_refs, list) else ethnicity_refs
                if ethnicity_ref:
                    ethnicity_ids = ensure_list(ethnicity_ref.get("ID", []))
                    for eid in ethnicity_ids:
                        if isinstance(eid, dict) and eid.get("type") == "Ethnicity_ID":
                            parsed["ethnicity"] = eid.get("_value_1")
                            break
            
            # Hispanic or Latino
            hispanic = personal_info.get("Hispanic_or_Latino")
            if hispanic is not None:
                parsed["hispanic_or_latino"] = bool(int(hispanic)) if isinstance(hispanic, str) else bool(hispanic)
            
            # Veterans Status
            veterans_ref = safe_get_reference(personal_info, "Veterans_Status_Reference")
            if veterans_ref:
                veterans_ids = ensure_list(veterans_ref.get("ID", []))
                parsed["veterans_status"] = extract_id_by_type(veterans_ids, "Armed_Forces_Status_ID") or \
                                            extract_id_by_type(veterans_ids, "Veteran_Status_ID") or \
                                            veterans_ref.get("Descriptor")
            
            # Disability Status
            disability_ref = safe_get_reference(personal_info, "Disability_Status_Reference")
            if disability_ref:
                disability_ids = ensure_list(disability_ref.get("ID", []))
                parsed["disability_status"] = extract_id_by_type(disability_ids, "Self_Identification_of_Disability_Status_ID") or \
                                              disability_ref.get("Descriptor")
            
            # Disability Status Last Updated
            parsed["disability_status_date"] = to_date_string(personal_info.get("Disability_Status_Last_Updated_On"))
        
        # Try to get birth_date from Global_Personal_Information_Data if not already set
        if not parsed.get("birth_date"):
            global_personal_info = job_applied_to.get("Global_Personal_Information_Data", {})
            if global_personal_info:
                birth_date_raw = global_personal_info.get("Date_of_Birth")
                parsed["birth_date"] = to_date_string(birth_date_raw)
                
                # Also try ethnicity from global data if not already set
                if not parsed.get("ethnicity"):
                    ethnicity_ref = safe_get_reference(global_personal_info, "Ethnicity_Reference")
                    if ethnicity_ref:
                        ethnicity_ids = ensure_list(ethnicity_ref.get("ID", []))
                        for eid in ethnicity_ids:
                            if isinstance(eid, dict) and eid.get("type") == "Ethnicity_ID":
                                parsed["ethnicity"] = eid.get("_value_1")
                                break
                
                # Also try hispanic_or_latino from global data if not already set
                if parsed.get("hispanic_or_latino") is None:
                    hispanic = global_personal_info.get("Hispanic_or_Latino")
                    if hispanic is not None:
                        parsed["hispanic_or_latino"] = bool(int(hispanic)) if isinstance(hispanic, str) else bool(hispanic)
    
    return parsed


def parse_candidate_contact_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Contact Information for Candidate - based on actual Workday XML structure"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Contact_Data has direct fields (not nested in Phone_Data, Email_Address_Data, etc.)
    contact_data = candidate_data.get("Contact_Data", {})
    if not contact_data:
        return parsed
    
    # Phone - direct field
    phone_number = contact_data.get("Phone_Number")
    if phone_number:
        parsed["phone"] = phone_number
        parsed["phones"] = [phone_number]
    
    # Email - direct field  
    email_address = contact_data.get("Email_Address")
    if email_address:
        parsed["email"] = email_address
        parsed["emails"] = [email_address]
        
        # For candidates, typically the email provided is personal
        # unless we can determine otherwise from usage data
        parsed["personal_email"] = email_address
        parsed["corporate_email"] = None
    
    # Address - in Location_Data (not Address_Data)
    location_data = contact_data.get("Location_Data", {})
    if location_data:
        # Build formatted address
        address_parts = []
        address_line_1 = location_data.get("Address_Line_1")
        if address_line_1:
            parsed["address_line_1"] = address_line_1
            address_parts.append(address_line_1)
        
        city = location_data.get("City")
        if city:
            parsed["address_city"] = city
            address_parts.append(city)
        
        # State/Region
        country_region_ref = safe_get_reference(location_data, "Country_Region_Reference")
        if country_region_ref:
            region_ids = ensure_list(country_region_ref.get("ID", []))
            for rid in region_ids:
                if isinstance(rid, dict):
                    if rid.get("type") == "ISO_3166-2_Code":
                        parsed["address_state"] = rid.get("_value_1")
                        address_parts.append(rid.get("_value_1"))
                        break
        
        # Postal code
        postal_code = location_data.get("Postal_Code")
        if postal_code:
            parsed["address_postal_code"] = postal_code
            address_parts.append(postal_code)
        
        # Country
        country_ref = safe_get_reference(location_data, "Country_Reference")
        if country_ref:
            country_ids = ensure_list(country_ref.get("ID", []))
            for cid in country_ids:
                if isinstance(cid, dict):
                    if cid.get("type") == "ISO_3166-1_Alpha-2_Code":
                        parsed["address_country"] = cid.get("_value_1")
                        break
        
        # Build formatted address
        parsed["address"] = ", ".join(filter(None, address_parts)) if address_parts else None
    
    return parsed

def parse_candidate_recruitment_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Recruitment-specific data for Candidate (campos "planos" a partir de la
    postulación más reciente). Soporta Candidate_Job_Applied_To_Data y Job_Applied_To_Data.
    """
    parsed: Dict[str, Any] = {}
    if not candidate_data:
        return parsed

    # Recolectar todas las aplicaciones que vengan en Candidate_Data
    job_apps = ensure_list(candidate_data.get("Job_Application_Data", []))
    collected: List[Dict[str, Any]] = []

    for job_app in job_apps:
        applied_to_raw = job_app.get("Candidate_Job_Applied_To_Data") or job_app.get("Job_Applied_To_Data")
        for applied in ensure_list(applied_to_raw):
            if not isinstance(applied, dict):
                continue

            # --- Job Requisition ---
            job_req_ref = safe_get_reference(applied, "Job_Requisition_Reference")
            job_req_ids = ensure_list(job_req_ref.get("ID", [])) if job_req_ref else []
            job_requisition_id = extract_id_by_type(job_req_ids, "Job_Requisition_ID")
            job_requisition_title = job_req_ref.get("Descriptor") if job_req_ref else None

            # --- Fechas / orden ---
            application_date = to_date_string(applied.get("Job_Application_Date"))
            status_timestamp = to_date_string(applied.get("Status_Timestamp"))

            # --- Status (preferir Candidate_Status_Reference si existe) ---
            status_ref = safe_get_reference(applied, "Candidate_Status_Reference")
            candidate_status = status_ref.get("Descriptor") if status_ref else None

            # --- Stage / Step ---
            stage_ref = safe_get_reference(applied, "Stage_Reference") or safe_get_reference(applied, "Recruiting_Step_Reference")
            stage_ids = ensure_list(stage_ref.get("ID", [])) if stage_ref else []
            stage_code = extract_id_by_type(stage_ids, "Recruiting_Stage_ID")
            stage_desc = stage_ref.get("Descriptor") if stage_ref else None

            # --- Workflow Step ---
            wf_ref = safe_get_reference(applied, "Workflow_Step_Reference")
            wf_ids = ensure_list(wf_ref.get("ID", [])) if wf_ref else []
            workflow_step_id = extract_id_by_type(wf_ids, "Workflow_Step_ID")
            workflow_step_desc = wf_ref.get("Descriptor") if wf_ref else None

            # --- Disposition ---
            disp_ref = safe_get_reference(applied, "Disposition_Reference")
            disp_ids = ensure_list(disp_ref.get("ID", [])) if disp_ref else []
            disposition_code = extract_id_by_type(disp_ids, "Recruiting_Disposition_ID")
            disposition_desc = disp_ref.get("Descriptor") if disp_ref else None

            # --- Source ---
            source_ref = safe_get_reference(applied, "Source_Reference")
            source_ids = ensure_list(source_ref.get("ID", [])) if source_ref else []
            source = extract_id_by_type(source_ids, "Applicant_Source_ID") or (source_ref.get("Descriptor") if source_ref else None)

            # --- Recruiter ---
            recruiter_ref = safe_get_reference(applied, "Recruiter_Reference")
            recruiter_ids = ensure_list(recruiter_ref.get("ID", [])) if recruiter_ref else []
            recruiter_id = extract_id_by_type(recruiter_ids, "Employee_ID")
            recruiter_name = recruiter_ref.get("Descriptor") if recruiter_ref else None

            # --- Disqualification (si aplica) ---
            disqualified = applied.get("Disqualified")
            disqual_reason_ref = safe_get_reference(applied, "Disqualification_Reason_Reference")
            disqualification_reason = disqual_reason_ref.get("Descriptor") if disqual_reason_ref else None

            # --- Derivar un display "amigable" ---
            status_display = candidate_status or stage_desc or stage_code

            collected.append({
                "job_requisition_id": job_requisition_id,
                "job_requisition_title": job_requisition_title,
                "application_date": application_date,
                "status_timestamp": status_timestamp,

                "candidate_status": candidate_status,
                "candidate_stage": stage_code or stage_desc,
                "candidate_stage_desc": stage_desc,
                "status_display": status_display,

                "workflow_step_id": workflow_step_id,
                "workflow_step_desc": workflow_step_desc,

                "disposition_code": disposition_code,
                "disposition_desc": disposition_desc,

                "source": source,
                "recruiter_id": recruiter_id,
                "recruiter_name": recruiter_name,

                "disqualified": disqualified,
                "disqualification_reason": disqualification_reason,
            })

    if not collected:
        return parsed

    # Elegir la postulación "actual": más reciente por Status_Timestamp; fallback a Application_Date
    def _sort_key(app: Dict[str, Any]) -> str:
        return (app.get("status_timestamp") or "") + "|" + (app.get("application_date") or "")

    latest = max(collected, key=_sort_key)

    # Popular campos "planos" con la postulación más reciente
    parsed.update({
        "job_requisition_id": latest.get("job_requisition_id"),
        "job_requisition_title": latest.get("job_requisition_title"),
        "application_date": latest.get("application_date"),
        "applied_date": latest.get("application_date"),

        "candidate_status": latest.get("candidate_status"),
        "candidate_stage": latest.get("candidate_stage"),
        "recruiting_step": latest.get("candidate_stage"),  # alias
        "current_step": latest.get("candidate_stage"),
        "current_step_date": latest.get("status_timestamp"),
        "source": latest.get("source"),
        "recruiter_id": latest.get("recruiter_id"),
        "recruiter_name": latest.get("recruiter_name"),

        "disqualified": latest.get("disqualified"),
        "disqualification_reason": latest.get("disqualification_reason"),

        # Campos nuevos útiles:
        "candidate_stage_desc": latest.get("candidate_stage_desc"),
        "status_display": latest.get("status_display"),
        "workflow_step_id": latest.get("workflow_step_id"),
        "workflow_step_desc": latest.get("workflow_step_desc"),
        "disposition_code": latest.get("disposition_code"),
        "disposition_desc": latest.get("disposition_desc"),
    })

    return parsed

def parse_candidate_status_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Status Data for Candidate (Do Not Hire, Withdrawn)"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    status_data = candidate_data.get("Status_Data", {})
    if status_data:
        do_not_hire = status_data.get("Do_Not_Hire")
        if do_not_hire is not None:
            parsed["do_not_hire"] = bool(int(do_not_hire)) if isinstance(do_not_hire, str) else bool(do_not_hire)
        
        withdrawn = status_data.get("Withdrawn")
        if withdrawn is not None:
            parsed["withdrawn"] = bool(int(withdrawn)) if isinstance(withdrawn, str) else bool(withdrawn)
    
    return parsed


def parse_candidate_prospect_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Prospect Data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    prospect_data = candidate_data.get("Prospect_Data", {})
    if prospect_data:
        prospect = prospect_data.get("Prospect")
        if prospect is not None:
            parsed["prospect"] = bool(int(prospect)) if isinstance(prospect, str) else bool(prospect)
        
        confidential = prospect_data.get("Confidential")
        if confidential is not None:
            parsed["confidential"] = bool(int(confidential)) if isinstance(confidential, str) else bool(confidential)
        
        referral_consent = prospect_data.get("Referral_Consent_Given")
        if referral_consent is not None:
            parsed["referral_consent_given"] = bool(int(referral_consent)) if isinstance(referral_consent, str) else bool(referral_consent)
        
        # Prospect Status
        status_ref = safe_get_reference(prospect_data, "Prospect_Status_Reference")
        if status_ref:
            status_ids = ensure_list(status_ref.get("ID", []))
            parsed["prospect_status"] = extract_id_by_type(status_ids, "Prospect_Status_ID") or status_ref.get("Descriptor")
        
        # Prospect Type
        type_ref = safe_get_reference(prospect_data, "Prospect_Type_Reference")
        if type_ref:
            type_ids = ensure_list(type_ref.get("ID", []))
            parsed["prospect_type"] = extract_id_by_type(type_ids, "Prospect_Type_ID") or type_ref.get("Descriptor")
        
        # Added By Worker
        worker_ref = safe_get_reference(prospect_data, "Added_By_Worker_Reference")
        if worker_ref:
            worker_ids = ensure_list(worker_ref.get("ID", []))
            parsed["added_by_worker_id"] = extract_id_by_type(worker_ids, "Employee_ID")
            parsed["added_by_worker_name"] = worker_ref.get("Descriptor")
    
    return parsed


def parse_candidate_language_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Language data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Language_Reference
    lang_ref = safe_get_reference(candidate_data, "Language_Reference")
    if lang_ref:
        lang_ids = ensure_list(lang_ref.get("ID", []))
        parsed["language"] = extract_id_by_type(lang_ids, "User_Language_ID") or lang_ref.get("Descriptor")
    
    return parsed


def parse_candidate_organization_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Organization/Location data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # This might be in different places - handle lists
    position_data = candidate_data.get("Position_Data", {})
    if not position_data:
        job_app_raw = candidate_data.get("Job_Application_Data", {})
        if isinstance(job_app_raw, list):
            position_data = job_app_raw[0] if job_app_raw else {}
        else:
            position_data = job_app_raw
    
    if position_data:
        # Location
        location_ref = safe_get_reference(position_data, "Location_Reference")
        if location_ref:
            ids = ensure_list(location_ref.get("ID", []))
            parsed["location_id"] = extract_id_by_type(ids, "Location_ID")
            parsed["location"] = location_ref.get("Descriptor")
        
        # Supervisory Organization
        sup_org_ref = safe_get_reference(position_data, "Supervisory_Organization_Reference")
        if sup_org_ref:
            ids = ensure_list(sup_org_ref.get("ID", []))
            parsed["supervisory_organization_id"] = extract_id_by_type(ids, "Organization_Reference_ID")
            parsed["supervisory_organization"] = sup_org_ref.get("Descriptor")
        
        # Company
        company_ref = safe_get_reference(position_data, "Company_Reference")
        if company_ref:
            ids = ensure_list(company_ref.get("ID", []))
            parsed["company_id"] = extract_id_by_type(ids, "Company_Reference_ID")
            parsed["company"] = company_ref.get("Descriptor")
        
        # Cost Center
        cost_center_ref = safe_get_reference(position_data, "Cost_Center_Reference")
        if cost_center_ref:
            ids = ensure_list(cost_center_ref.get("ID", []))
            parsed["cost_center_id"] = extract_id_by_type(ids, "Cost_Center_Reference_ID")
            parsed["cost_center"] = cost_center_ref.get("Descriptor")
    
    return parsed


def parse_candidate_education_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Education data for Candidate.
    In Get_Candidates, education comes from Job_Application_Data -> Resume_Data -> Education_Data
    """
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    schools = []
    degrees = []
    education_history = []
    
    # Get Resume_Data from Job_Application_Data (actual structure in Get_Candidates)
    job_app_data_list = ensure_list(candidate_data.get("Job_Application_Data", []))
    if job_app_data_list:
        job_app_data = job_app_data_list[0] if isinstance(job_app_data_list, list) else job_app_data_list
        resume_data = job_app_data.get("Resume_Data", {})
        
        if resume_data:
            # Parse Education_Data from Resume
            education_data_list = ensure_list(resume_data.get("Education_Data", []))
            
            for edu_data in education_data_list:
                school_name = edu_data.get("School_Name")
                degree_name = None
                
                # Try to get degree from reference first
                degree_ref = safe_get_reference(edu_data, "Degree_Reference")
                if degree_ref:
                    degree_ids = ensure_list(degree_ref.get("ID", []))
                    degree_name = extract_id_by_type(degree_ids, "Degree_ID") or degree_ref.get("Descriptor")
                
                # Try to get school from reference
                school_ref = safe_get_reference(edu_data, "School_Reference")
                if school_ref:
                    school_name = school_ref.get("Descriptor") or school_name
                
                if school_name:
                    schools.append(school_name)
                
                # Build education entry
                edu_entry = {
                    "school": school_name,
                    "degree": degree_name,
                    "first_year": edu_data.get("First_Year_Attended"),
                    "last_year": edu_data.get("Last_Year_Attended"),
                    "field_of_study": edu_data.get("Field_of_Study")
                }
                
                # Only add if we have meaningful data
                if any(v for v in edu_entry.values() if v):
                    education_history.append(edu_entry)
                    if degree_name:
                        degrees.append(edu_entry)
    
    parsed["schools"] = schools if schools else None
    parsed["degrees"] = degrees if degrees else None
    parsed["education_history"] = education_history if education_history else None
    
    return parsed


def parse_candidate_experience_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Experience data for Candidate.
    In Get_Candidates, experience comes from Job_Application_Data -> Resume_Data -> Experience_Data
    """
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    employers = []
    work_experience_list = []
    total_years = 0
    
    # Get Resume_Data from Job_Application_Data (actual structure in Get_Candidates)
    job_app_data_list = ensure_list(candidate_data.get("Job_Application_Data", []))
    if job_app_data_list:
        job_app_data = job_app_data_list[0] if isinstance(job_app_data_list, list) else job_app_data_list
        resume_data = job_app_data.get("Resume_Data", {})
        
        if resume_data:
            # Parse Experience_Data from Resume
            experience_list = ensure_list(resume_data.get("Experience_Data", []))
            
            for exp in experience_list:
                company = exp.get("Company_Name")
                if company and company not in employers:
                    employers.append(company)
                
                # Build dates from month/year fields
                start_month = exp.get("Start_Month")
                start_year = exp.get("Start_Year")
                end_month = exp.get("End_Month")
                end_year = exp.get("End_Year")
                
                # Convert to int if they are strings
                try:
                    start_month = int(start_month) if start_month else None
                    start_year = int(start_year) if start_year else None
                    end_month = int(end_month) if end_month else None
                    end_year = int(end_year) if end_year else None
                except (ValueError, TypeError):
                    start_month = start_year = end_month = end_year = None
                
                start_date = f"{start_year}-{start_month:02d}-01" if start_year and start_month else None
                end_date = f"{end_year}-{end_month:02d}-01" if end_year and end_month else None
                
                exp_detail = {
                    "company": company,
                    "job_title": exp.get("Title"),
                    "location": exp.get("Location"),
                    "start_date": start_date,
                    "end_date": end_date,
                    "currently_work_here": exp.get("Currently_Work_Here"),
                    "description": exp.get("Description")
                }
                
                # Only add if we have meaningful data
                if any(v for v in [company, exp_detail.get("job_title"), exp_detail.get("description")] if v):
                    work_experience_list.append(exp_detail)
                
                # Calculate years of experience
                if start_year and end_year:
                    years = end_year - start_year
                    if start_month and end_month:
                        years += (end_month - start_month) / 12
                    total_years += max(0, years)
    
    parsed["previous_employers"] = employers if employers else None
    parsed["work_experience"] = work_experience_list if work_experience_list else None
    parsed["years_of_experience"] = int(total_years) if total_years > 0 else None
    
    return parsed


def parse_candidate_skills_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Skills and Competencies data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Skills
    skills = []
    skill_data_list = candidate_data.get("Skill_Data", [])
    if isinstance(skill_data_list, dict):
        skill_data_list = [skill_data_list]
    
    for skill_data in skill_data_list:
        skill_ref = skill_data.get("Skill_Reference", {})
        if skill_ref:
            skill_name = skill_ref.get("Descriptor")
            if skill_name:
                skills.append(skill_name)
    
    parsed["skills"] = skills if skills else None
    
    # Competencies - store as list of dicts with more details
    competencies = []
    comp_data_list = candidate_data.get("Competency_Data", [])
    if isinstance(comp_data_list, dict):
        comp_data_list = [comp_data_list]
    
    for comp_data in comp_data_list:
        comp_ref = comp_data.get("Competency_Reference", {})
        if comp_ref:
            competency = {
                "name": comp_ref.get("Descriptor"),
                "proficiency": comp_data.get("Proficiency_Level")
            }
            competencies.append(competency)
    
    parsed["competencies"] = competencies if competencies else None
    
    # Languages
    languages = []
    lang_data_list = candidate_data.get("Language_Data", [])
    if isinstance(lang_data_list, dict):
        lang_data_list = [lang_data_list]
    
    for lang_data in lang_data_list:
        lang_ref = lang_data.get("Language_Reference", {})
        if lang_ref:
            language = {
                "language": lang_ref.get("Descriptor"),
                "proficiency": lang_data.get("Language_Proficiency")
            }
            languages.append(language)
    
    parsed["languages"] = languages if languages else None
    
    return parsed


def parse_candidate_identification_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Identification data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Identification_Data is inside Personal_Data
    personal_data = candidate_data.get("Personal_Data", {})
    if not personal_data:
        return parsed
    
    id_data = personal_data.get("Identification_Data", {})
    if not id_data:
        return parsed
    
    # National ID
    national_id_list = id_data.get("National_ID", [])
    if isinstance(national_id_list, dict):
        national_id_list = [national_id_list]
    
    if national_id_list:
        primary_nat_id = national_id_list[0]
        nat_id_data = primary_nat_id.get("National_ID_Data", {})
        if nat_id_data:
            parsed["national_id"] = nat_id_data.get("ID")
            
            id_type_ref = nat_id_data.get("ID_Type_Reference", {})
            if id_type_ref:
                parsed["national_id_type"] = id_type_ref.get("Descriptor")
    
    # Passport
    passport_list = id_data.get("Passport_ID", [])
    if isinstance(passport_list, dict):
        passport_list = [passport_list]
    
    if passport_list:
        primary_passport = passport_list[0]
        passport_data = primary_passport.get("Passport_ID_Data", {})
        if passport_data:
            parsed["passport_number"] = passport_data.get("Passport_Number")
    
    # Driver's License
    license_list = id_data.get("License_ID", [])
    if isinstance(license_list, dict):
        license_list = [license_list]
    
    if license_list:
        primary_license = license_list[0]
        license_data = primary_license.get("License_ID_Data", {})
        if license_data:
            parsed["license_id"] = license_data.get("ID")
            parsed["license_expiration_date"] = to_date_string(license_data.get("Expiration_Date"))
            
            # License state
            region_ref = license_data.get("Country_Region_Reference", {})
            if region_ref:
                parsed["license_state"] = region_ref.get("Descriptor")
            
            # License type
            license_type_ref = license_data.get("ID_Type_Reference", {})
            if license_type_ref:
                parsed["license_type"] = license_type_ref.get("Descriptor")
    
    # Custom IDs
    custom_id_list = id_data.get("Custom_ID", [])
    if isinstance(custom_id_list, dict):
        custom_id_list = [custom_id_list]
    
    for custom_id_item in custom_id_list:
        custom_id_data = custom_id_item.get("Custom_ID_Data", {})
        if custom_id_data:
            id_type_ref = custom_id_data.get("ID_Type_Reference", {})
            if id_type_ref:
                id_type_ids = id_type_ref.get("ID", [])
                id_type = extract_id_by_type(id_type_ids, "Custom_ID_Type_ID")
                id_value = custom_id_data.get("ID")
                
                # Map custom ID types to fields
                if id_type == "ADP Payroll ID":
                    parsed["adp_payroll_id"] = id_value
                elif id_type == "ADP Payroll Group":
                    parsed["adp_payroll_group"] = id_value
                elif id_type == "Old Corporate Email":
                    parsed["old_corporate_email"] = id_value
                elif id_type == "Associate OID":
                    parsed["associate_oid"] = id_value
                elif id_type == "ICIMS ID":
                    parsed["icims_id"] = id_value
                elif id_type == "MSO Dealer Code":
                    parsed["mso_dealer_code"] = id_value
                elif id_type == "NetSuite Internal ID":
                    parsed["netsuite_internal_id"] = id_value
    
    return parsed


def parse_candidate_background_check_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Background Check data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    bg_check_data = candidate_data.get("Background_Check_Data", {})
    if not bg_check_data:
        return parsed
    
    # Background check status
    status_ref = bg_check_data.get("Background_Check_Status_Reference", {})
    if status_ref:
        parsed["background_check_status"] = status_ref.get("Descriptor")
    
    parsed["background_check_date"] = to_date_string(bg_check_data.get("Background_Check_Date"))
    parsed["background_check_completed"] = bg_check_data.get("Background_Check_Completed")
    
    return parsed


def parse_candidate_interview_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Interview data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    interview_data_list = candidate_data.get("Interview_Data", [])
    if isinstance(interview_data_list, dict):
        interview_data_list = [interview_data_list]
    
    interviews = []
    for interview_data in interview_data_list:
        interview = {
            "interview_date": to_date_string(interview_data.get("Interview_Date")),
            "interviewer": interview_data.get("Interviewer_Reference", {}).get("Descriptor"),
            "interview_type": interview_data.get("Interview_Type_Reference", {}).get("Descriptor"),
            "rating": interview_data.get("Overall_Rating"),
            "notes": interview_data.get("Interview_Notes")
        }
        interviews.append(interview)
    
    parsed["interviews"] = interviews if interviews else None
    parsed["interview_count"] = len(interviews) if interviews else 0
    
    return parsed


def parse_candidate_offer_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Offer data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    offer_data = candidate_data.get("Offer_Data", {})
    if not offer_data:
        return parsed
    
    parsed["offer_extended"] = offer_data.get("Offer_Extended")
    parsed["offer_date"] = to_date_string(offer_data.get("Offer_Date"))
    parsed["offer_accepted"] = offer_data.get("Offer_Accepted")
    
    decline_reason_ref = offer_data.get("Offer_Decline_Reason_Reference", {})
    if decline_reason_ref:
        parsed["offer_declined_reason"] = decline_reason_ref.get("Descriptor")
    
    return parsed


def parse_candidate_assessment_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Assessment/Rating data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Overall rating
    parsed["overall_rating"] = candidate_data.get("Overall_Rating")
    
    # Assessments
    assessment_data_list = candidate_data.get("Assessment_Data", [])
    if isinstance(assessment_data_list, dict):
        assessment_data_list = [assessment_data_list]
    
    assessments = []
    for assessment_data in assessment_data_list:
        assessment = {
            "assessment_type": assessment_data.get("Assessment_Type_Reference", {}).get("Descriptor"),
            "score": assessment_data.get("Score"),
            "assessment_date": to_date_string(assessment_data.get("Assessment_Date")),
            "notes": assessment_data.get("Notes")
        }
        assessments.append(assessment)
    
    parsed["assessments"] = assessments if assessments else None
    
    return parsed


def parse_candidate_document_data(candidate_data: Dict[str, Any], candidate_id: Optional[str] = None, pdf_directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse Document/Attachment data for Candidate.
    
    Args:
        candidate_data: Candidate data dictionary
        candidate_id: Candidate ID for organizing PDF files
        pdf_directory: Base directory to save PDF files
    
    Returns:
        Dictionary with document info including pdf_path if PDF was saved
    """
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    # Check for resume and cover letter
    documents = []
    resume_attached = False
    cover_letter_attached = False
    pdf_path = None
    resume_filename = None
    resume_mime_type = None
    
    # Check for Resume_Attachment_Data in Job_Application_Data (actual structure)
    job_app_data_list = ensure_list(candidate_data.get("Job_Application_Data", []))
    if job_app_data_list:
        job_app_data = job_app_data_list[0] if isinstance(job_app_data_list, list) else job_app_data_list
        
        # Resume_Attachment_Data can also be a list (when multiple resumes)
        resume_attachment_raw = job_app_data.get("Resume_Attachment_Data", {})
        if isinstance(resume_attachment_raw, list):
            resume_attachment = resume_attachment_raw[0] if resume_attachment_raw else {}
        else:
            resume_attachment = resume_attachment_raw
        
        if resume_attachment:
            resume_attached = True
            resume_filename = resume_attachment.get("Filename")
            
            # Get MIME type
            mime_type_ref = safe_get_reference(resume_attachment, "Mime_Type_Reference")
            if mime_type_ref:
                mime_ids = ensure_list(mime_type_ref.get("ID", []))
                for mid in mime_ids:
                    if isinstance(mid, dict) and mid.get("type") == "Content_Type_ID":
                        resume_mime_type = mid.get("_value_1")
                        break
            
            # Save PDF if directory is provided
            if pdf_directory and candidate_id and resume_filename:
                file_content_b64 = resume_attachment.get("File_Content")
                if file_content_b64:
                    pdf_path = save_attachment(
                        file_content_base64=file_content_b64,
                        filename=resume_filename,
                        candidate_id=candidate_id,
                        storage_path=pdf_directory
                    )
            
            if resume_filename:
                documents.append(f"Resume: {resume_filename}")
    
    # Also check for Attachment_Data (alternative structure)
    document_data_list = candidate_data.get("Attachment_Data", [])
    if isinstance(document_data_list, dict):
        document_data_list = [document_data_list]
    
    for doc_data in document_data_list:
        doc_category_ref = doc_data.get("Document_Category_Reference", {})
        if doc_category_ref:
            doc_type = doc_category_ref.get("Descriptor")
            if doc_type:
                documents.append(doc_type)
                
                # Check if it's a resume
                if "resume" in doc_type.lower() or "cv" in doc_type.lower():
                    resume_attached = True
                
                # Check if it's a cover letter
                if "cover" in doc_type.lower() and "letter" in doc_type.lower():
                    cover_letter_attached = True
    
    parsed["documents"] = documents if documents else None
    parsed["resume_attached"] = resume_attached
    parsed["resume_filename"] = resume_filename
    parsed["resume_mime_type"] = resume_mime_type
    parsed["pdf_path"] = pdf_path
    parsed["cover_letter_attached"] = cover_letter_attached
    
    return parsed


def parse_candidate_reference_data(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse Reference (employment references) data for Candidate"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    reference_data_list = candidate_data.get("Reference_Data", [])
    if isinstance(reference_data_list, dict):
        reference_data_list = [reference_data_list]
    
    references = []
    reference_check_completed = False
    
    for ref_data in reference_data_list:
        reference = {
            "name": ref_data.get("Reference_Name"),
            "company": ref_data.get("Company"),
            "title": ref_data.get("Title"),
            "phone": ref_data.get("Phone"),
            "email": ref_data.get("Email"),
            "relationship": ref_data.get("Relationship"),
            "checked": ref_data.get("Reference_Checked")
        }
        references.append(reference)
        
        if ref_data.get("Reference_Checked"):
            reference_check_completed = True
    
    parsed["references"] = references if references else None
    parsed["reference_check_completed"] = reference_check_completed
    
    return parsed


def parse_candidate_metadata(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse metadata like created date, modified date, tags"""
    parsed = {}
    
    if not candidate_data:
        return parsed
    
    parsed["created_date"] = to_date_string(candidate_data.get("Created_Date"))
    parsed["last_modified_date"] = to_date_string(candidate_data.get("Last_Modified_Date"))
    
    # Tags
    tag_data_list = candidate_data.get("Candidate_Tag_Data", [])
    if isinstance(tag_data_list, dict):
        tag_data_list = [tag_data_list]
    
    tags = []
    for tag_data in tag_data_list:
        tag_ref = tag_data.get("Candidate_Tag_Reference", {})
        if tag_ref:
            tag_name = tag_ref.get("Descriptor")
            if tag_name:
                tags.append(tag_name)
    
    parsed["candidate_tags"] = tags if tags else None
    
    return parsed 
def parse_candidate_applications(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Devuelve todas las postulaciones del candidato como una lista en 'applications'.
    - Soporta Candidate_Job_Applied_To_Data y Job_Applied_To_Data.
    - Conserva timestamps completos (no truncados) tal como vienen del SOAP.
    - Incluye WIDs e IDs de Job Application y Job Requisition.
    - Expone Disposition, Workflow Step, Source y descriptores cuando existan.
    """
    out = {"applications": []}
    if not candidate_data:
        return out

    job_apps = ensure_list(candidate_data.get("Job_Application_Data", []))
    for job_app in job_apps:
        # Referencia a la Job Application (WID y Job_Application_ID)
        ja_ref = safe_get_reference(job_app, "Job_Application_Reference")
        ja_ids = ensure_list(ja_ref.get("ID", [])) if ja_ref else []
        job_application_wid = extract_id_by_type(ja_ids, "WID")
        job_application_id_from_ref = extract_id_by_type(ja_ids, "Job_Application_ID")

        # Nodo aplicado (dos variantes)
        applied_to_raw = job_app.get("Candidate_Job_Applied_To_Data") or job_app.get("Job_Applied_To_Data")
        for applied in ensure_list(applied_to_raw):
            if not isinstance(applied, dict):
                continue

            # Job Application ID también puede venir dentro del subnodo
            job_application_id_inline = applied.get("Job_Application_ID")
            job_application_id = job_application_id_inline or job_application_id_from_ref

            # Job Requisition (WID, ID, Descriptor si viene)
            jr_ref = safe_get_reference(applied, "Job_Requisition_Reference")
            jr_ids = ensure_list(jr_ref.get("ID", [])) if jr_ref else []
            job_requisition_wid = extract_id_by_type(jr_ids, "WID")
            job_requisition_id = extract_id_by_type(jr_ids, "Job_Requisition_ID")
            job_requisition_title = jr_ref.get("Descriptor") if jr_ref else None  # puede ser None

            # Fechas/timestamps - conservar tal cual
            application_date_raw = applied.get("Job_Application_Date")
            status_timestamp_raw = applied.get("Status_Timestamp")

            # Candidate Status (si WD lo envía en tu tenant)
            status_ref = safe_get_reference(applied, "Candidate_Status_Reference")
            candidate_status = status_ref.get("Descriptor") if status_ref else None

            # Stage / Recruiting Step
            stage_ref = safe_get_reference(applied, "Stage_Reference") or safe_get_reference(applied, "Recruiting_Step_Reference")
            stage_ids = ensure_list(stage_ref.get("ID", [])) if stage_ref else []
            candidate_stage = extract_id_by_type(stage_ids, "Recruiting_Stage_ID") or (stage_ref.get("Descriptor") if stage_ref else None)
            candidate_stage_wid = extract_id_by_type(stage_ids, "WID")
            candidate_stage_desc = stage_ref.get("Descriptor") if stage_ref else None  # por si WD lo envía

            # Workflow Step
            wf_ref = safe_get_reference(applied, "Workflow_Step_Reference")
            wf_ids = ensure_list(wf_ref.get("ID", [])) if wf_ref else []
            workflow_step_wid = extract_id_by_type(wf_ids, "WID")
            workflow_step_id = extract_id_by_type(wf_ids, "Workflow_Step_ID")
            workflow_step_desc = wf_ref.get("Descriptor") if wf_ref else None

            # Disposition
            disp_ref = safe_get_reference(applied, "Disposition_Reference")
            disp_ids = ensure_list(disp_ref.get("ID", [])) if disp_ref else []
            disposition_wid = extract_id_by_type(disp_ids, "WID")
            disposition_code = extract_id_by_type(disp_ids, "Recruiting_Disposition_ID")
            disposition_desc = disp_ref.get("Descriptor") if disp_ref else None

            # Source
            src_ref = safe_get_reference(applied, "Source_Reference")
            src_ids = ensure_list(src_ref.get("ID", [])) if src_ref else []
            source_wid = extract_id_by_type(src_ids, "WID")
            source = extract_id_by_type(src_ids, "Applicant_Source_ID") or (src_ref.get("Descriptor") if src_ref else None)

            # Recruiter
            recruiter_ref = safe_get_reference(applied, "Recruiter_Reference")
            recruiter_ids = ensure_list(recruiter_ref.get("ID", [])) if recruiter_ref else []
            recruiter_id = extract_id_by_type(recruiter_ids, "Employee_ID")
            recruiter_name = recruiter_ref.get("Descriptor") if recruiter_ref else None

            # Disqualification
            disqualified = applied.get("Disqualified")
            disq_reason_ref = safe_get_reference(applied, "Disqualification_Reason_Reference")
            disqualification_reason = disq_reason_ref.get("Descriptor") if disq_reason_ref else None

            out["applications"].append({
                # Job Application
                "job_application_wid": job_application_wid,
                "job_application_id": job_application_id,

                # Job Requisition
                "job_requisition_wid": job_requisition_wid,
                "job_requisition_id": job_requisition_id,
                "job_requisition_title": job_requisition_title,

                # Fechas/timestamps (raw)
                "application_date": application_date_raw,
                "status_timestamp": status_timestamp_raw,

                # Estado/etapa
                "candidate_status": candidate_status,
                "candidate_stage": candidate_stage,
                "candidate_stage_wid": candidate_stage_wid,
                "candidate_stage_desc": candidate_stage_desc,

                # Workflow step
                "workflow_step_wid": workflow_step_wid,
                "workflow_step_id": workflow_step_id,
                "workflow_step_desc": workflow_step_desc,

                # Disposition
                "disposition_wid": disposition_wid,
                "disposition_code": disposition_code,     # p.ej. Hired_for_another_job
                "disposition_desc": disposition_desc,

                # Source
                "source_wid": source_wid,
                "source": source,                          # Applicant_Source_ID o Descriptor

                # Recruiter
                "recruiter_id": recruiter_id,
                "recruiter_name": recruiter_name,

                # Disqualification
                "disqualified": disqualified,
                "disqualification_reason": disqualification_reason,
            })

    return out
