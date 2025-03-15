# main.py
import re
import time
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional
from lxml import etree
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key='AIzaSyBB7vl2LTJhaCzk1SAE8kWJcLh8o32wuJA')  # Replace with your Gemini API key

@dataclass
class TranslatorConfig:
    model: genai.GenerativeModel
    batch_size: int = 10


def translate_batch(text_batch, dest_lang, model, max_retries=5):
    """
    Translate a batch of texts using the Gemini API with retry logic.
    """
    translations = []
    batch_size = 5  # Reduced from 10 to avoid quota issues
    
    for i in range(0, len(text_batch), batch_size):
        batch = text_batch[i:i + batch_size]
        retries = 0
        success = False
        
        while not success and retries < max_retries:
            try:
                # Combine texts into a single prompt for efficiency
                combined_text = "\n".join(batch)
                prompt = f"Translate the following texts to {dest_lang}:\n{combined_text}"
                
                # Send the batch to the Gemini API
                response = model.generate_content(prompt)
                # Split the response into individual translations
                batch_translations = response.text.split("\n")
                translations.extend(batch_translations)
                success = True
                print(f"Successfully translated batch {i//batch_size + 1} of {len(text_batch)//batch_size + 1}")
                
            except Exception as e:
                retries += 1
                if "429" in str(e):  # Rate limit error
                    wait_time = (2 ** retries) + random.uniform(0, 1)  # Exponential backoff with jitter
                    print(f"Rate limit reached. Waiting {wait_time:.2f} seconds before retry {retries}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    print(f"Error translating batch: {e}")
                    break  # Exit for non-quota errors
        
        if not success:
            # Fallback: Use original texts if translation fails after all retries
            print(f"Failed to translate batch after {max_retries} retries. Using original text.")
            translations.extend(batch)
        
        # Add a small delay between successful batches to avoid hitting rate limits
        time.sleep(1)
            
    return translations


@dataclass
class GElement:
    id: str
    ctype: str
    text: str


@dataclass
class TextContainer:
    text: Optional[str] = None
    g_elements: List[GElement] = field(default_factory=list)


@dataclass
class TransUnit:
    id: str
    source: TextContainer = field(default_factory=TextContainer)
    target: TextContainer = field(default_factory=TextContainer)


@dataclass
class File:
    original: str
    datatype: str
    source_language: str
    target_language: str
    trans_units: List[TransUnit] = field(default_factory=list)


def parse_xliff(file_path):
    """
    Parse an XLIFF file and extract translation units.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = etree.parse(file)
    root = tree.getroot()

    ns = {'default': root.nsmap[None]}
    files = []

    for file_elem in root.findall('default:file', namespaces=ns):
        file_original = file_elem.get('original')
        file_datatype = file_elem.get('datatype')
        file_source_language = file_elem.get('source-language')
        file_target_language = file_elem.get('target-language')
        trans_units = []

        for trans_unit_elem in file_elem.findall('.//default:trans-unit', namespaces=ns):
            trans_unit_id = trans_unit_elem.get('id')
            source = parse_text_container(trans_unit_elem.find('default:source', namespaces=ns), ns)
            target = parse_text_container(trans_unit_elem.find('default:target', namespaces=ns), ns)

            trans_units.append(TransUnit(id=trans_unit_id, source=source, target=target))

        files.append(File(
            original=file_original,
            datatype=file_datatype,
            source_language=file_source_language,
            target_language=file_target_language,
            trans_units=trans_units
        ))

    return files


def parse_text_container(elem, ns):
    """
    Parse a <source> or <target> element and extract text and <g> elements.
    """
    text_container = TextContainer()
    if elem is not None:
        # Extract direct text
        if elem.text:
            text_container.text = elem.text.strip()

        # Extract <g> elements
        for g_elem in elem.findall('default:g', namespaces=ns):
            g_id = g_elem.get('id')
            g_ctype = g_elem.get('ctype')
            g_text = ''.join(g_elem.itertext()).strip()
            text_container.g_elements.append(GElement(id=g_id, ctype=g_ctype, text=g_text))

    return text_container


def copy_source_to_target(files: List[File]):
    """
    Copy source text to target if target is empty.
    """
    for file in files:
        for trans_unit in file.trans_units:
            if trans_unit.source:
                if trans_unit.target is None:
                    trans_unit.target = deepcopy(trans_unit.source)
                else:
                    trans_unit.target.text = deepcopy(trans_unit.source.text)
                    trans_unit.target.g_elements = deepcopy(trans_unit.source.g_elements)


def contains_letters(text):
    """
    Check if a text contains letters (A-Z, a-z).
    """
    return bool(re.search('[a-zA-Z]', text))


def translate_targets(files, dest_lang, model):
    """
    Translate all target texts using the Gemini API.
    """
    text_to_translate = []
    mapping = []  # To map translations back to their respective targets

    for file in files:
        for trans_unit in file.trans_units:
            # Translate source text if it contains letters
            if (trans_unit.source.text and trans_unit.source.text.strip()
                    and contains_letters(trans_unit.source.text)):
                text_to_translate.append(trans_unit.source.text)
                mapping.append((trans_unit, 'text', None))
            else:
                # Preserve original text if no translation is needed
                trans_unit.target.text = trans_unit.source.text

            # Translate <g> elements if they contain letters
            for g_element in trans_unit.source.g_elements:
                if g_element.text and g_element.text.strip() and contains_letters(g_element.text):
                    text_to_translate.append(g_element.text)
                    mapping.append((trans_unit, 'g', g_element))
                else:
                    # Preserve original <g> text if no translation is needed
                    corresponding_g_element = next(
                        (ge for ge in trans_unit.target.g_elements if ge.id == g_element.id), None)
                    if corresponding_g_element:
                        corresponding_g_element.text = g_element.text

    # Translate texts in batches
    if text_to_translate:
        print(f"Translating {len(text_to_translate)} texts...")
        translated_texts = translate_batch(text_to_translate, dest_lang, model)

        # Assign translations back to their respective targets
        for (trans_unit, text_type, g_element), translation in zip(mapping, translated_texts):
            if text_type == 'text':
                trans_unit.target.text = translation
            elif text_type == 'g' and g_element is not None:
                corresponding_g_element = next(
                    (ge for ge in trans_unit.target.g_elements if ge.id == g_element.id), None)
                if corresponding_g_element:
                    corresponding_g_element.text = translation
    else:
        print("No texts to translate.")

    return files


def build_xliff(files, target_language):
    """
    Build an XLIFF file from the translated data.
    """
    nsmap = {
        None: "urn:oasis:names:tc:xliff:document:1.2",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xhtml": "http://www.w3.org/1999/xhtml"
    }
    xliff_elem = etree.Element("xliff", nsmap=nsmap, version="1.2")
    xliff_elem.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation",
                   "urn:oasis:names:tc:xliff:document:1.2 "
                   "http://docs.oasis-open.org/xliff/v1.2/os/xliff-core-1.2-strict.xsd")

    for file in files:
        file_attributes = {
            'original': file.original if file.original is not None else '',
            'datatype': file.datatype if file.datatype is not None else '',
            'source-language': file.source_language if file.source_language is not None else target_language,
            'target-language': file.target_language if file.target_language is not None else target_language,
        }
        file_elem = etree.SubElement(xliff_elem, "file", file_attributes)
        body_elem = etree.SubElement(file_elem, "body")

        for trans_unit in file.trans_units:
            trans_unit_elem = etree.SubElement(body_elem, "trans-unit", {"id": trans_unit.id})
            source_elem = etree.SubElement(trans_unit_elem, "source")
            if trans_unit.source.text:
                source_elem.text = trans_unit.source.text
            for g_element in trans_unit.source.g_elements:
                g_elem = etree.SubElement(source_elem, "g", {"id": g_element.id, "ctype": g_element.ctype})
                g_elem.text = g_element.text

            target_elem = etree.SubElement(trans_unit_elem, "target")
            if trans_unit.target.text:
                target_elem.text = trans_unit.target.text
            for g_element in trans_unit.target.g_elements:
                g_elem = etree.SubElement(target_elem, "g", {"id": g_element.id, "ctype": g_element.ctype})
                g_elem.text = g_element.text

    # Convert the XML tree to a string
    xml_output = etree.tostring(xliff_elem, pretty_print=True, encoding='UTF-8', xml_declaration=True).decode()
    return xml_output


def main(source_path, destination_path, language):
    """
    Main function to handle translation process.
    """
    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Parse, translate, and build the XLIFF file
    files = parse_xliff(source_path)
    copy_source_to_target(files)
    files = translate_targets(files, language, model)
    translated_xliff_content = build_xliff(files, language)

    # Save the translated XLIFF file
    with open(destination_path, 'w', encoding='utf-8') as f:
        f.write(translated_xliff_content)
    print(f"Translation saved to {destination_path}")