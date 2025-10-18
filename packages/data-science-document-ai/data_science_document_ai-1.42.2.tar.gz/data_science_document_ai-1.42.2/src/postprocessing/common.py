import asyncio
import json
import os
import re
from datetime import timezone

import pandas as pd
from nltk.corpus import stopwords
from rapidfuzz import process

from src.constants import formatting_rules
from src.io import logger
from src.postprocessing.postprocess_partner_invoice import process_partner_invoice
from src.prompts.prompt_library import prompt_library
from src.utils import get_tms_mappings

tms_domain = os.environ["TMS_DOMAIN"]


def convert_container_number(container_number):
    """
    Convert a container number to ISO standard.

    Args:
        container_number (str): The container number to be converted.

    Returns:
        str: The formatted container number if it is valid, None otherwise.
    """
    if not container_number:
        return
    # 'FFAU2932130--FX34650895-40HC' -> 'FFAU2932130'
    match = re.findall(r"[A-Z]{4}\d{7}", container_number)
    stripped_value = match if match else None

    # LLMs do extract all the container numbers as a list of strings
    if stripped_value and len(stripped_value) > 1:
        return stripped_value
    else:
        stripped_value = stripped_value[0] if stripped_value else None

    if not stripped_value:
        stripped_value = "".join(
            filter(lambda char: str.isalnum(char) or char == "/", container_number)
        )

    # This is to catch container number that has the format like: ABCD1234567/40DC or ABCD1234567/SEAL1234567
    formatted_value = stripped_value.split("/")[0]
    if len(formatted_value) != 11:
        return
    # Check if the format is according to the ISO standard
    if not formatted_value[:4].isalpha() or not formatted_value[4:].isdigit():
        return
    return formatted_value


def clean_invoice_number(invoice_number):
    """Post process invoice number

    Args:
        invoice_number (str): The invoice number to be cleaned.

    Returns:
        str: The cleaned invoice number if it is valid, None otherwise.
    """
    if not invoice_number:
        return

    # Remove all non-alphanumeric characters
    stripped_value = re.sub(r"[^\w]", "", invoice_number)

    return stripped_value


def clean_shipment_id(shipment_id):
    """
    Convert shipment_id to Forto standard.

    Args:
        shipment_id (str): The Shipment ID to be converted.

    Returns:
        str: The formatted shipment_id if it is valid, None otherwise.
    """
    if not shipment_id:
        return
    # '#S123456@-1' -> 'S123456'
    # Find the pattern of a shipment ID that starts with 'S' followed by 5 to 7 digits
    match = re.findall(r"S\d{5,7}", shipment_id)
    stripped_value = match[0] if match else None

    if not stripped_value:
        return None

    # Check if length is valid (should be either 7 or 8)
    if len(stripped_value) not in (6, 7, 8):
        return None

    return stripped_value


# Clean the date for date obj parse in tms formatting
def clean_date_string(date_str):
    """Remove hours and timezone information from the date string."""
    date_str = date_str.strip()
    if "hrs" in date_str:
        return date_str.replace("hrs", "")
    if "(CET)" in date_str:
        return date_str.replace("(CET)", "")
    return date_str


def extract_date(date_str):
    """
    Extract date from string using european format (day first).

    Check if starts with year, then YYYY-MM-DD, else DD-MM-YYYY
    """
    if all([c.isnumeric() for c in date_str[:4]]):
        dt_obj = pd.to_datetime(date_str, dayfirst=False).to_pydatetime()
    else:
        dt_obj = pd.to_datetime(date_str, dayfirst=True).to_pydatetime()
    return dt_obj


def extract_number(data_field_value):
    """
    Remove everything not a digit and not in [, .].

    Args:
        data_field_value: string

    Returns:
        formatted_value: string

    """
    formatted_value = ""
    for c in data_field_value:
        if c.isnumeric() or c in [",", "."]:
            formatted_value += c

    # First and last characters should not be  [",", "."]
    formatted_value = formatted_value.strip(",.")

    return formatted_value if formatted_value not in ["''", ""] else None


def extract_string(data_field_value):
    """Remove numeric characters from the string.

    Args:
        data_field_value: string

    Returns:
        formatted_value: string

    """
    if not isinstance(data_field_value, str):
        return None

    excluded_chars = [".", ",", ")", "(", " ", "[", "]"]
    formatted_value = "".join(
        c for c in data_field_value if not c.isdigit() and c not in excluded_chars
    )

    return formatted_value if formatted_value not in ["''", ""] else None


def remove_none_values(d):
    if isinstance(d, dict):
        # Create a new dictionary to store non-None values
        cleaned_dict = {}
        for key, value in d.items():
            cleaned_value = remove_none_values(value)
            if cleaned_value is not None:  # Only add non-None values
                cleaned_dict[key] = cleaned_value
        return cleaned_dict if cleaned_dict else None

    elif isinstance(d, list):
        # Create a new list to store non-None values
        cleaned_list = []
        for item in d:
            cleaned_item = remove_none_values(item)
            if cleaned_item is not None:  # Only add non-None values
                cleaned_list.append(cleaned_item)
        return cleaned_list if cleaned_list else None

    else:
        # Return the value if it's not a dictionary or list
        return d if d is not None else None


def check_formatting_rule(entity_key, document_type_code, rule):
    if (
        document_type_code in formatting_rules.keys()
        and entity_key in formatting_rules[document_type_code].keys()
        and formatting_rules[document_type_code][entity_key] == rule
    ):
        return True
    return False


def convert_invoice_type(data_field_value, params):
    """
    Converts a raw invoice type string to either invoice or creditNote using fuzzy matching.

    Args:
        data_field_value (str): The raw invoice type string from the data.
        params (dict): A dictionary of parameters, including:
            - "lookup_data": A dictionary containing lookup tables.
            - "fuzzy_threshold_invoice_classification": The minimum fuzzy matching score.

    Returns:
        str or None: The standardized invoice type if a match is found, otherwise None.
    """
    lookup_data = params["lookup_data"]["invoice_classification"]
    keywords = list(lookup_data.keys())

    best_match = process.extractOne(
        data_field_value.lower(),
        keywords,
    )
    if best_match:
        best_match_key, score, _ = best_match
        if score >= params["fuzzy_threshold_invoice_classification"]:
            return lookup_data[best_match_key]
    return None


# Function to create KVP dictionary using apply method
def create_kvp_dictionary(df_raw: pd.DataFrame):
    """Create a key-value pair dictionary from the given DataFrame.

    Args:
        df_raw (pd.DataFrame): The input DataFrame containing 'lineitem' and 'Forto SLI' columns.

    return:
        A key-value pair dictionary with 'Processed Lineitem' as key and 'Forto SLI' as value.
    """
    df = df_raw.copy()
    df["Processed Lineitem"] = df["lineitem"].apply(clean_item_description)
    kvp_dict = df.set_index("Processed Lineitem")["Forto SLI"].to_dict()

    return kvp_dict


def remove_dates(lineitem: str):
    """
    This function removes dates in the format "dd Month yyyy" from the given line item string.

    Args:
    lineitem (str): The input string from which dates will be removed.

    Returns:
    str: The string with dates removed.
    """
    # Remove dates in the format dd.mm.yy or dd.mm.yyyy
    lineitem = re.sub(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b", "", lineitem)

    # Remove dates in the format "dd Month yyyy"
    lineitem = re.sub(
        r"\b\d{1,2} (?:january|february|march|april|may|june|july|august|september|october|november|december|januar|"
        r"februar|märz|mai|juni|juli|oktober|dezember) \d{4}\b",
        "",
        lineitem,
        flags=re.IGNORECASE,
    )

    # Define a list of month abbreviations in English and German
    month_abbreviations = [
        "JAN",
        "FEB",
        "MAR",
        "APR",
        "MAY",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OCT",
        "NOV",
        "DEC",
        "JAN",
        "FEB",
        "MRZ",
        "APR",
        "MAI",
        "JUN",
        "JUL",
        "AUG",
        "SEP",
        "OKT",
        "NOV",
        "DEZ",
    ]

    # Create a regular expression pattern to match month abbreviations
    pattern = r"\b(?:{})\b".format("|".join(month_abbreviations))

    # Remove month abbreviations
    lineitem = re.sub(pattern, "", lineitem, flags=re.IGNORECASE)

    return lineitem


def remove_unwanted_patterns(lineitem: str):
    """
    This function removes dates, month names, and container numbers from the given line item string.

    Args:
    lineitem (str): The input string from which unwanted patterns will be removed.

    Returns:
    str: The string with dates, month names, and container numbers removed.
    """
    # Remove container numbers (4 letters followed by 7 digits)
    lineitem = re.sub(r"\b[A-Z]{4}\d{7}\b", "", lineitem)

    # Remove "HIGH CUBE"
    lineitem = lineitem.replace("HIGH CUBE", "")

    return lineitem


def clean_item_description(lineitem: str, remove_numbers: bool = True):
    """
    This function removes dates, month names, whitespaces, currency patterns and container numbers from the given line item string.  # noqa

    Args:
    lineitem (str): The input string from which unwanted patterns will be removed.

    Returns:
    str: The cleaned string removed.
    """
    currency_codes_pattern = r"\b(USD|EUR|JPY|GBP|CAD|AUD|CHF|CNY|SEK|NZD|KRW|SGD|INR|BRL|ZAR|RUB|MXN|HKD|NOK|TRY|IDR|MYR|PHP|THB|VND|PLN|CZK|HUF|ILS|AED|SAR|QAR|KWD|EGP|NGN|ARS|CLP|COP|PEN|UYU|VEF|INR|PKR|BDT|LKR|NPR|MMK)\b"  # noqa

    # Remove stopwords
    lineitem = remove_stop_words(lineitem)

    # remove dates
    lineitem = remove_dates(lineitem)

    # remove whitespaces
    lineitem = re.sub(r"\s{2,}", " ", lineitem)

    # remove newlines
    lineitem = re.sub(r"\\n|\n", " ", lineitem)

    # Remove the currency codes
    lineitem = re.sub(currency_codes_pattern, "", lineitem, flags=re.IGNORECASE)

    # Remove numbers from the line item
    if (
        remove_numbers
    ):  # Do not remove numbers for the reverse charge sentence as it contains Article number
        lineitem = re.sub(r"\d+", "", lineitem)

    # remove other patterns
    lineitem = remove_unwanted_patterns(lineitem)

    # remove special chars
    lineitem = re.sub(r"[^A-Za-z0-9\s]", " ", lineitem).strip()

    return re.sub(r"\s{2,}", " ", lineitem).strip()


async def format_label(entity_k, entity_value, document_type_code, params):
    llm_client = params["LlmClient"]
    if isinstance(entity_value, dict):  # if it's a nested entity
        format_tasks = [
            format_label(sub_k, sub_v, document_type_code, params)
            for sub_k, sub_v in entity_value.items()
        ]
        return entity_k, {k: v for k, v in await asyncio.gather(*format_tasks)}
    if isinstance(entity_value, list):
        format_tasks = await asyncio.gather(
            *[
                format_label(entity_k, sub_v, document_type_code, params)
                for sub_v in entity_value
            ]
        )
        return entity_k, [v for _, v in format_tasks]
    if isinstance(entity_value, tuple):
        page = entity_value[1]
        entity_value = entity_value[0]
    else:
        page = -1
    entity_key = entity_k.lower()
    formatted_value = None

    if entity_key.startswith("port"):
        formatted_value = await get_port_code_ai(
            entity_value, llm_client, doc_type=document_type_code
        )

    elif (entity_key == "containertype") or (entity_key == "containersize"):
        formatted_value = get_tms_mappings(entity_value, "container_types")

    elif check_formatting_rule(entity_k, document_type_code, "terminal"):
        formatted_value = get_tms_mappings(entity_value, "terminals")

    elif check_formatting_rule(entity_k, document_type_code, "depot"):
        formatted_value = get_tms_mappings(entity_value, "depots")

    elif entity_key.startswith(("eta", "etd", "duedate", "issuedate", "servicedate")):
        try:
            cleaned_data_field_value = clean_date_string(entity_value)
            dt_obj = extract_date(cleaned_data_field_value)
            formatted_value = str(dt_obj.date())
        except ValueError as e:
            logger.info(f"ParserError: {e}")
    elif "cutoff" in entity_key:
        try:
            cleaned_data_field_value = clean_date_string(entity_value)
            dt_obj = extract_date(cleaned_data_field_value)
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=timezone.utc)
            else:
                dt_obj = dt_obj.astimezone(timezone.utc)
            formatted_value = dt_obj.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        except ValueError as e:
            logger.info(f"ParserError: {e}")

    elif entity_key in ["invoicenumber", "creditnoteinvoicenumber"]:
        formatted_value = clean_invoice_number(entity_value)

    elif entity_key in ("shipmentid", "partnerreference"):
        # Clean the shipment ID to match Forto's standard (starts with 'S' followed by 5 to 7 digits)
        formatted_value = clean_shipment_id(entity_value)

    elif entity_key == "containernumber":
        # Remove all non-alphanumeric characters like ' ', '-', etc.
        formatted_value = convert_container_number(entity_value)

    elif any(
        numeric_indicator in entity_key
        for numeric_indicator in ["measurements", "weight"]
    ):
        formatted_value = extract_number(entity_value)

    elif any(
        packaging_type in entity_key
        for packaging_type in ["packagingtype", "packagetype", "currency"]
    ):
        # Remove all numeric characters from the string. For example 23CARTONS -> CARTONS
        formatted_value = extract_string(entity_value)
    elif "lineitemdescription" in entity_key:
        formatted_value = clean_item_description(entity_value)
    elif "documenttype" in entity_key:
        formatted_value = convert_invoice_type(entity_value, params)

    # Handle reverseChargeSentence
    elif "reversechargesentence" in entity_key:
        formatted_value = clean_item_description(entity_value, remove_numbers=False)

    elif "quantity" in entity_key:
        if document_type_code in ["partnerInvoice", "customsInvoice", "bundeskasse"]:
            # For partner invoice, quantity can be mentioned as whole number
            formatted_value = decimal_convertor(
                extract_number(entity_value), quantity=True
            )
        else:
            formatted_value = extract_number(entity_value)

    elif any(
        numeric_indicator in entity_key
        for numeric_indicator in [
            "value",
            "amount",
            "price",
            "totalamount",
            "totalamounteuro",
            "vatamount",
            "vatapplicableamount",
            "grandtotal",
        ]
    ):
        # Convert EU values to English values (e.g., 4.123,45 -> 4123.45)
        formatted_value = decimal_convertor(extract_number(entity_value))

    result = {
        "documentValue": entity_value,
        "formattedValue": formatted_value,
        "page": page,
    }
    return entity_k, result


async def get_port_code_ai(port: str, llm_client, doc_type=None):
    """Get port code using AI model."""
    port_llm = await get_port_code_llm(port, llm_client, doc_type=doc_type)

    return get_tms_mappings(port, "ports", port_llm)


async def get_port_code_llm(port: str, llm_client, doc_type=None):
    if (
        "postprocessing" in prompt_library.library.keys()
        and "port_code" in prompt_library.library["postprocessing"].keys()
    ):
        # Get the prompt from the prompt library and prepare the response schema for ChatGPT
        prompt = prompt_library.library["postprocessing"]["port_code"]["prompt"]
        response_schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "port",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "string",
                            "description": f"Get the port code for the given port: {port}",
                        }
                    },
                    "required": ["port"],
                    "additionalProperties": False,
                },
            },
        }

        response = await llm_client.get_unified_json_genai(
            prompt, response_schema=response_schema, model="chatgpt", doc_type=doc_type
        )
        try:
            mapped_port = response["port"]
            return mapped_port
        except json.JSONDecodeError:
            logger.error(f"Error decoding response: {response}")
            return None


def decimal_convertor(value, quantity=False):
    """Convert EU values to English values."""
    if value is None:
        return None

    # Remove spaces
    value = value.strip().replace(" ", "")

    if not quantity:
        # Convert comma to dot for decimal point (e.g., 4.123,45 -> 4123.45)
        if re.match(r"^\d{1,3}(\.\d{3})*,\d{1,2}$", value):
            value = value.replace(".", "").replace(",", ".")

        # European style integer with thousand separator: 2.500
        elif re.match(r"^\d{1,3}(\.\d{3})+$", value):
            value = value.replace(".", "")

        # Format english values as well for consistency (e.g., 4,123.45 -> 4123.45)
        elif re.match(r"^\d{1,3}(,\d{3})*\.\d{1,2}$", value):
            value = value.replace(",", "")

        # English style integer with thousand separator: 2,500
        elif re.match(r"^\d{1,3}(,\d{3})+$", value):
            value = value.replace(",", "")

        # Just replace comma decimals with dot (e.g., 65,45 -> 65.45)
        if re.match(r"^\d+,\d{1,2}$", value):
            value = value.replace(",", ".")

        # If there are more than 3 0s after decimal point, consider only 2 decimal points (e.g., 8.500000 -> 8.50)
        elif re.match(r"^\d+\.\d{3,}$", value):
            value = value[: value.index(".") + 3]

    else:  # quantity=True → only last two
        # Just replace comma decimals with dot (e.g., 65,45 -> 65.45)
        if re.match(r"^\d+,\d{1,2}$", value):
            value = value.replace(",", ".")

        # If there are more than 3 0s after decimal point, consider only 2 decimal points (e.g., 8.500000 -> 8.50)
        elif re.match(r"^\d+\.\d{3,}$", value):
            value = value[: value.index(".") + 3]

    return value


async def format_all_entities(result, document_type_code, params):
    """Format the entity values in the result dictionary."""
    # Since we treat `customsInvoice` same as `partnerInvoice`
    document_type_code = (
        "partnerInvoice"
        if document_type_code == "customsInvoice"
        else document_type_code
    )
    # Remove None values from the dictionary
    result = remove_none_values(result)
    if result is None:
        logger.info("No data was extracted.")
        return {}

    # Format all entities recursively
    _, aggregated_data = await format_label(None, result, document_type_code, params)

    # Process partner invoice on lineitem mapping and reverse charge sentence
    if document_type_code in ["partnerInvoice", "bundeskasse"]:
        process_partner_invoice(params, aggregated_data, document_type_code)

    logger.info("Data Extraction completed successfully")
    return aggregated_data


def add_text_without_space(text):
    """If the cleaned text is different from the original text, append it.
    Useful for port names like QUINHON - Quinhon"""
    cleaned_text = "".join(text.split())
    if text != cleaned_text:
        text += f" {cleaned_text}"
    return text


def remove_stop_words(lineitem: str):
    """Remove stop words in English and German from the given line item string.

    Args:
    lineitem (str): The input string from which stop words will be removed.

    Returns:
    str: The string with stop words removed.
    """
    stop_words = set(stopwords.words("english") + stopwords.words("german")) - {"off"}
    return (
        " ".join(word for word in lineitem.split() if word.lower() not in stop_words)
        .upper()
        .strip()
    )


def llm_prediction_to_tuples(llm_prediction):
    """Convert LLM prediction dictionary to tuples of (value, page_number)."""
    if isinstance(llm_prediction, dict):
        if "page_number" in llm_prediction.keys() and "value" in llm_prediction.keys():
            if llm_prediction["value"]:
                try:
                    page_number = int(llm_prediction["page_number"])
                except:  # noqa: E722
                    page_number = -1
                return (llm_prediction["value"], page_number)
            return None
        for key, value in llm_prediction.items():
            llm_prediction[key] = llm_prediction_to_tuples(
                llm_prediction.get(key, value)
            )
    elif isinstance(llm_prediction, list):
        for i, item in enumerate(llm_prediction):
            llm_prediction[i] = llm_prediction_to_tuples(item)
    return llm_prediction
