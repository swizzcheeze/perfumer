# src/routes/import_bp.py
from flask import Blueprint, jsonify, request
import json
import csv
import io
import os
import re # Make sure re is imported
from src.models.models import db, Ingredient, Category

import_bp = Blueprint('import_bp', __name__)

# --- Keyword Categorization Setup ---
KEYWORD_TO_CORE_CATEGORY = {
    # Citrus
    "lemon": "Citrus", "lime": "Citrus", "bergamot": "Citrus", "orange": "Citrus",
    "grapefruit": "Citrus", "mandarin": "Citrus", "tangerine": "Citrus", "yuzu": "Citrus",
    "citron": "Citrus", "petitgrain": "Citrus", "neroli": "Citrus", "verbena": "Citrus",
    "citric": "Citrus", "orange peel": "Citrus", "agrumen": "Citrus", "citral": "Citrus",
    "citronellal": "Citrus", "citronellol": "Citrus", "citronellyl": "Citrus", 
    "citrylal": "Citrus", "clonal": "Citrus", "peely": "Citrus",

    # Woody
    "sandalwood": "Woody", "cedarwood": "Woody", "cedar": "Woody", "vetiver": "Woody",
    "patchouli": "Woody", "oud": "Woody", "agarwood": "Woody", "guaiacwood": "Woody",
    "hinoki": "Woody", "cypress": "Woody", "pine": "Woody", "fir": "Woody", "fir needle": "Woody",
    "rosewood": "Woody", "birch": "Woody", "oakwood": "Woody", "cashmeran": "Woody",
    "iso e super": "Woody", "teakwood": "Woody", "coniferous": "Woody", "bois": "Woody",
    "bornafix": "Woody", "andrane": "Woody", "blackwood": "Woody", "boisiris": "Woody", 
    "bacdanol": "Woody", "sanjinol": "Woody", "cedrene": "Woody", "cedrol": "Woody",
    "cedroxyde": "Woody", "cedryl": "Woody", "cedramber": "Woody", "clearwood": "Woody",
    "coniferan": "Woody", "costausol": "Woody", "dreamwood": "Woody", "ebanol": "Woody",
    "firsantol": "Woody", "guaiene": "Woody", "guaiol": "Woody", "koavone": "Woody",
    "kohinool": "Woody", "madranol": "Woody", "norlimbanol": "Woody", "orinox": "Woody",
    "osyrol": "Woody", "polysantol": "Woody", "timberol": "Woody", "trimofix": "Woody",
    "vertofix": "Woody", "vetikone": "Woody", "ysamber": "Woody", "z11": "Woody",
    "precious wood": "Woody",

    # Floral
    "rose": "Floral", "rosy": "Floral", "jasmine": "Floral", "jasmin": "Floral", "lily": "Floral", "lilly": "Floral", 
    "lilac": "Floral", "lavender": "Floral", "tuberose": "Floral", "ylang ylang": "Floral", "ylang-ylang": "Floral",
    "gardenia": "Floral", "peony": "Floral", "freesia": "Floral", "magnolia": "Floral",
    "orange blossom": "Floral", "frangipani": "Floral", "violet": "Floral", "violettyne": "Floral",
    "iris": "Floral", "orris": "Floral", "geranium": "Floral", "carnation": "Floral", 
    "mimosa": "Floral", "osmanthus": "Floral", "honeysuckle": "Floral", "chamomile": "Floral",
    "muguet": "Floral", "ionone": "Floral", "hawthorn": "Floral", "heliotrope": "Floral", "heliotropine": "Floral",
    "orange flower": "Floral", "auralva": "Floral", "boronal": "Floral", "lilybelle": "Floral", "lilyflore": "Floral", "lilytol": "Floral",
    "benzyl acetate": "Floral", "benzyl salicylate": "Floral", "amyl cinnamic aldehyde": "Floral",
    "carbinol muguet": "Floral", "cyclamen": "Floral", "cyclemax": "Floral",
    "cyclomethylene citronellol": "Floral", "cyclopidene": "Floral", "damascone": "Floral", 
    "damascol": "Floral", "delphol": "Floral", "dihydro ionone beta": "Floral", 
    "dimethyl benzyl carbinol": "Floral", "dupical": "Floral", "coranol": "Floral", 
    "corps iris": "Floral", "floralol": "Floral", "floralozone": "Floral", "florhydral": "Floral",
    "florocyclene": "Floral", "floropal": "Floral", "florosa": "Floral", "givescone": "Floral",
    "glycolierral": "Floral", "hedione": "Floral", "jasmacyclene": "Floral", "jessemal": "Floral",
    "kharismal": "Floral", "linalool": "Floral", "mayol": "Floral", "meijiff": "Floral",
    "melafleur": "Floral", "methyl anthranilate": "Floral", "methyl dihydro jasmonate": "Floral",
    "methyl ionone": "Floral", "methyl tuberate": "Floral", "muguet alcohol": "Floral",
    "myraldyl acetate": "Floral", "narcisse": "Floral", "nerolione": "Floral", "neryl acetate": "Floral",
    "nympheal": "Floral", "peomosa": "Floral", "peonile": "Floral", "phenethyl alcohol": "Floral",
    "phenoxanol": "Floral", "phenyl propyl alcohol": "Floral", "rhodinol": "Floral", "rosalva": "Floral",
    "rosamusk": "Floral", "rosaphen": "Floral", "rose crystals": "Floral", "rose oxide": "Floral",
    "rosyrane": "Floral", "silvial": "Floral", "starfleur": "Floral", "syringa": "Floral",
    "tubereuse": "Floral", "ylang oliffac": "Floral",

    # Bases & Accords
    "accord": "Bases & Accords", "base": "Bases & Accords", "compound": "Bases & Accords",
    "specialty base": "Bases & Accords", "reconstitution": "Bases & Accords", "fixative base": "Bases & Accords",
    "key accord": "Bases & Accords", "oliffac": "Bases & Accords", "timbrox base": "Bases & Accords",

    # Spicy
    "spice": "Spicy", "spicy": "Spicy", "cinnamon": "Spicy", "cinnamic": "Spicy", "clove": "Spicy", "clove bud": "Spicy",
    "pepper": "Spicy", "peppercorn": "Spicy", "cardamom": "Spicy", "ginger": "Spicy", "nutmeg": "Spicy",
    "coriander": "Spicy", "pimento": "Spicy", "saffron": "Spicy", "anise": "Spicy", "herbs and spices": "Spicy",
    "anisic": "Spicy", "carvacrol": "Spicy", "carvone": "Spicy", "caryophyllene": "Spicy", 
    "dihydro eugenol": "Spicy", "eugenol": "Spicy", "eugenyl acetate": "Spicy",
    "cuminyl": "Spicy", "methyl eugenol": "Spicy", "methyl isoeugenol": "Spicy",
    "poivrol": "Spicy", "prismantol": "Spicy", "safraleine": "Spicy", "safranal": "Spicy",
    "valspice": "Spicy", "veraspice": "Spicy", "zingerone": "Spicy", "thymol": "Spicy", 

    # Resinous & Balsamic
    "resin": "Resinous & Balsamic", "resinous": "Resinous & Balsamic", "balsam": "Resinous & Balsamic", "balsamic": "Resinous & Balsamic",
    "frankincense": "Resinous & Balsamic", "olibanum": "Resinous & Balsamic",
    "myrrh": "Resinous & Balsamic", "benzoin": "Resinous & Balsamic",
    "labdanum": "Resinous & Balsamic", "cistus": "Resinous & Balsamic", "dynamone": "Resinous & Balsamic",
    "elemi": "Resinous & Balsamic", "opoponax": "Resinous & Balsamic",
    "peru balsam": "Resinous & Balsamic", "tolu balsam": "Resinous & Balsamic", "styrax": "Resinous & Balsamic",
    "benzyl cinnamate": "Resinous & Balsamic", "coumarex": "Resinous & Balsamic", 
    "cyclohexyl salicylate": "Resinous & Balsamic", "gurjun balsam": "Resinous & Balsamic",
    "hydrocarboresine": "Resinous & Balsamic",

    # Fruity
    "fruit": "Fruity", "fruity": "Fruity", "berry": "Fruity", "berries": "Fruity", "red fruit": "Fruity",
    "peach": "Fruity", "apple": "Fruity", "pear": "Fruity", "plum": "Fruity",
    "apricot": "Fruity", "fig": "Fruity", "blackcurrant": "Fruity", "cassis": "Fruity",
    "raspberry": "Fruity", "strawberry": "Fruity", "mango": "Fruity", "passionfruit": "Fruity",
    "pineapple": "Fruity", "davana": "Fruity", "cherry": "Fruity", "cranberry": "Fruity",
    "buchu leaf": "Fruity", "frambinon": "Fruity", "raspberry ketone": "Fruity",
    "allyl amyl glycolate": "Fruity", "allyl caproate": "Fruity", "amyl acetate": "Fruity", 
    "amyl butyrate": "Fruity", "apritone": "Fruity", "berryflor": "Fruity", 
    "bisabolene": "Fruity", "fructalate": "Fruity", "cassiffix": "Fruity", "cassione": "Fruity",
    "citronellyl formate": "Fruity", "cyclabute": "Fruity", "datilat": "Fruity", 
    "diethyl malonate": "Fruity", "dimethyl benzyl carbinyl acetate": "Fruity", 
    "dimethyl benzyl carbinyl butyrate": "Fruity", "dimethyl octenone": "Fruity", 
    "dynascone": "Fruity", "ethyl levulinate": "Fruity", "ethyl acetate": "Fruity",
    "ethyl butyrate": "Fruity", "ethyl caprate": "Fruity", "ethyl heptoate": "Fruity",
    "ethyl isobutyrate": "Fruity", "ethyl methyl-2-butyrate": "Fruity", "ethyl propionate": "Fruity",
    "ethyl safranate": "Fruity", "fraise": "Fruity", "fraistone": "Fruity", "framboise": "Fruity",
    "fruit sec": "Fruity", "fruitaleur": "Fruity", "grape butyrate": "Fruity", "guavanate": "Fruity",
    "hexalon": "Fruity", "hexyl acetate": "Fruity", "isopropyl methyl-2-butyrate": "Fruity",
    "manzanate": "Fruity", "nectarate": "Fruity", "nectaryl": "Fruity", "pharaone": "Fruity",
    "prenyl acetate": "Fruity", "prunella": "Fruity", "pyroprunat": "Fruity",
    "rhubofix": "Fruity", "sauvignone": "Fruity", "sultanene": "Fruity", "veloutone": "Fruity",
    "vetikolacetat": "Fruity",

    # Green & Herbal
    "green": "Green & Herbal", "herbal": "Green & Herbal", "leaf": "Green & Herbal", "leaves": "Green & Herbal", "leafy": "Green & Herbal",
    "grass": "Green & Herbal", "grassy": "Green & Herbal", "basil": "Green & Herbal", "mint": "Green & Herbal", "spearmint": "Green & Herbal", "peppermint": "Green & Herbal", "minty": "Green & Herbal",
    "rosemary": "Green & Herbal", "thyme": "Green & Herbal", "sage": "Green & Herbal", "clary sage": "Green & Herbal",
    "galbanum": "Green & Herbal", "artemisia": "Green & Herbal", "eucalyptus": "Green & Herbal", "eucalyptol": "Green & Herbal",
    "tea": "Green & Herbal", "tomato leaf": "Green & Herbal", "helichrysum": "Green & Herbal", 
    "agrestic": "Green & Herbal", "camphoraceous": "Green & Herbal", "borneol": "Green & Herbal", "camphene": "Green & Herbal",
    "buchu": "Green & Herbal", "anther": "Green & Herbal", "apo patchone coeur": "Green & Herbal",
    "canthoxal": "Green & Herbal", "carene": "Green & Herbal", "cis-3-hexenyl tiglate": "Green & Herbal",
    "cyclogalbanate": "Green & Herbal", "cyclal c": "Green & Herbal", "triplal": "Green & Herbal", 
    "dimetol": "Green & Herbal", "dimethyl hydroquinone": "Green & Herbal", "diphenyl oxide": "Green & Herbal",
    "cucumber": "Green & Herbal", "farnesene": "Green & Herbal", "fenchol": "Green & Herbal",
    "folione": "Green & Herbal", "freskomenthe": "Green & Herbal", "herboxane": "Green & Herbal",
    "hexenol": "Green & Herbal", "isocyclocitral": "Green & Herbal", "ivy": "Green & Herbal",
    "linalool oxide": "Green & Herbal", "liffarome": "Green & Herbal", "mintonat": "Green & Herbal",
    "myrac aldehyde": "Green & Herbal", "myrcene": "Green & Herbal", "neofolione": "Green & Herbal",
    "nonadienal": "Green & Herbal", "ocimene": "Green & Herbal", "phellandrene": "Green & Herbal",
    "pino acetaldehyde": "Green & Herbal", "stemone": "Green & Herbal", "syringa aldehyde": "Green & Herbal",
    "syvertal": "Green & Herbal", "terpinene": "Green & Herbal", "terpineol": "Green & Herbal",
    "terpinolene": "Green & Herbal", "toscanol": "Green & Herbal", "trifernal": "Green & Herbal",
    "undecavertol": "Green & Herbal", "vernaldehyde": "Green & Herbal",

    # Musk
    "musk": "Musk", "musky": "Musk", "ambrette": "Musk", "galaxolide": "Musk",
    "tonalide": "Musk", "habanolide": "Musk", "ethylene brassylate": "Musk", "ambrettolide": "Musk",
    "helvetolide": "Musk", "exaltolide": "Musk", "scentolide": "Musk", "ambrettex": "Musk",
    "aurelione": "Musk", "celestolide": "Musk", "cosmone": "Musk", "civettone": "Musk",
    "edenolide": "Musk", "exaltenone": "Musk", "exaltone": "Musk", "fixolide": "Musk",
    "globacenide": "Musk", "globanone": "Musk", "isomuscone": "Musk", "muscenone": "Musk",
    "muscone": "Musk", "musk ketone": "Musk", "musk r1": "Musk", "pentalide": "Musk",
    "romandolide": "Musk", "silvanone": "Musk", "tonquitone": "Musk", "traseolide": "Musk",
    "velvione": "Musk", "zenolide": "Musk",

    # Amber
    "amber": "Amber", "ambroxan": "Amber", "cetalox": "Amber", "ambergris": "Amber", "ambrox": "Amber",
    "ambrox super": "Amber", "bornafix": "Amber", "amber xtreme": "Amber", "ambercore": "Amber", 
    "ambermax": "Amber", "amberwood": "Amber", "ambrocenide": "Amber", "ambrox dl": "Amber", 
    "aldambre": "Amber", "dihydro ambrate": "Amber", "dynamone": "Amber", "fixamber": "Amber",
    "grisalva": "Amber", "karmawood": "Amber", "kephalis": "Amber", "kohinool": "Amber",
    "norlimbanol": "Amber", "okoumal": "Amber", "oxyoctaline formate": "Amber", "sylvamber": "Amber",
    "timberol": "Amber", "tobacarol": "Amber", "trisamber": "Amber",

    # Aquatic & Ozonic
    "aquatic": "Aquatic & Ozonic", "marine": "Aquatic & Ozonic", "oceanic": "Aquatic & Ozonic", "ozonic": "Aquatic & Ozonic", "ozone": "Aquatic & Ozonic",
    "calone": "Aquatic & Ozonic", "seaweed": "Aquatic & Ozonic", "salt": "Aquatic & Ozonic", "water": "Aquatic & Ozonic", "watery": "Aquatic & Ozonic",
    "seashore": "Aquatic & Ozonic", "adoxal": "Aquatic & Ozonic", "aquaflora": "Aquatic & Ozonic", 
    "aquamate": "Aquatic & Ozonic", "cascalone": "Aquatic & Ozonic", "maritima": "Aquatic & Ozonic",
    "ocean propanal": "Aquatic & Ozonic", "ozofleur": "Aquatic & Ozonic", "precyclemone": "Aquatic & Ozonic",
    "scentenal": "Aquatic & Ozonic",

    # Gourmand
    "gourmand": "Gourmand", "vanilla": "Gourmand", "chocolate": "Gourmand", "caramel": "Gourmand", "cocoa": "Gourmand",
    "tonka": "Gourmand", "tonka bean": "Gourmand", "coffee": "Gourmand", "coffee cake": "Gourmand",
    "almond": "Gourmand", "honey": "Gourmand", "milk": "Gourmand", "sugar": "Gourmand", "brown sugar": "Gourmand", 
    "cotton candy": "Gourmand", "praline": "Gourmand", "licorice": "Gourmand",
    "madeleine": "Gourmand", "oatmeal": "Gourmand", "whiskey": "Gourmand", "cognac": "Gourmand", "boozy": "Gourmand", "boozy notes": "Gourmand",
    "coumarin": "Gourmand", "acetanisole": "Gourmand", "anisyl acetone": "Gourmand", 
    "azarbre": "Gourmand", "butyl butyro lactate": "Gourmand", "furaneol": "Gourmand",
    "chocovan": "Gourmand", "dihydrocoumarin": "Gourmand", "espresso": "Gourmand",
    "ethyl cyclopentenolone": "Gourmand", "ethyl maltol": "Gourmand", "ethyl vanillin": "Gourmand",
    "homofuronol": "Gourmand", "isobutavan": "Gourmand", "jasminlactone": "Gourmand", 
    "lactojasmone": "Gourmand", 
    "levistamel": "Gourmand", "maltol": "Gourmand", "massoia lactone": "Gourmand", 
    "methyl cyclo pentenolone": "Gourmand", "milk lactone": "Gourmand", 
    "nuezate": "Gourmand", "sotolone": "Gourmand", "valeric acid": "Gourmand", 
    "vanillin": "Gourmand", "whiskey lactone": "Gourmand", 

    # Note Types
    "top note": "Top Note", "head note": "Top Note",
    "middle note": "Middle Note", "heart note": "Middle Note",
    "base note": "Base Note", "fond": "Base Note", "dry down": "Base Note", "fixative": "Base Note",

    # Olfactory Descriptors & Material Types
    "aldehyde": "Aldehydic", "aldehydic": "Aldehydic", "agrumen aldehyde": "Aldehydic", "decanal": "Aldehydic", "undecylenic aldehyde": "Aldehydic", "lauric aldehyde": "Aldehydic", "mna": "Aldehydic", "hexanal": "Aldehydic",   
    "cardamom aldehyde": "Aldehydic", "cyclamen aldehyde": "Aldehydic", "intreleven aldehyde": "Aldehydic", "mandarine aldehyde": "Aldehydic", "melon aldehyde": "Aldehydic", "myrac aldehyde": "Aldehydic", "phenyl acetaldehyde": "Aldehydic",
    "lactone": "Lactonic", "nonalactone": "Lactonic", "undecalactone": "Lactonic", "octalactone": "Lactonic", "heptalactone": "Lactonic", "dodecalactone": "Lactonic", "bicyclononalactone": "Lactonic", "delta decalactone": "Lactonic", "delta undecalactone": "Lactonic", "gamma decalactone": "Lactonic", "gamma dodecalactone": "Lactonic", "gamma octalactone": "Lactonic", "methyl laitone": "Lactonic",
    "creamy": "Lactonic", "milky": "Lactonic", "buttery": "Lactonic", 
    
    "molecule": "Aroma Chemicals",      
    "aroma chemical": "Aroma Chemicals",
    "scent molecule": "Aroma Chemicals",
    "synthetic": "Aroma Chemicals", 
    "crystals": "Aroma Chemicals", 

    "iff": "Aroma Chemicals", 
    "givaudan": "Aroma Chemicals",
    "firmenich": "Aroma Chemicals",
    "symrise": "Aroma Chemicals",
    "takasago": "Aroma Chemicals",
    "mane": "Aroma Chemicals",
    "kao": "Aroma Chemicals",
    "synarome": "Aroma Chemicals",
    "bedoukian": "Aroma Chemicals",
    "drt": "Aroma Chemicals",
    "robertet": "Aroma Chemicals", 
    "biolandes": "Aroma Chemicals",
    "pfw": "Aroma Chemicals", "quest": "Aroma Chemicals", "kalama": "Aroma Chemicals",

    "powdery": "Powdery",             
    "leathery": "Leathery", "suederal": "Leathery",         
    "animalic": "Animalic", "ambrinol": "Animalic", "civette": "Animalic", "costus": "Animalic", "indocolore": "Animalic", "indolarome": "Animalic", "indole": "Animalic", "skatole": "Animalic",
    
    "smoke": "Smoky & Incense",        
    "smoky": "Smoky & Incense",
    "incense": "Smoky & Incense", "bois dencens": "Smoky & Incense", "tabanon": "Smoky & Incense", 
    "tobacco": "Smoky & Incense", "phenolic": "Smoky & Incense", "syringol": "Smoky & Incense",

    "weird": "Unique & Niche", "sulfurous": "Unique & Niche", "yeasty": "Unique & Niche", "radish-like": "Unique & Niche", "acorn": "Unique & Niche",
    "raw": "Raw Materials", 

    "soapy": "Soapy & Clean",          
    "clean": "Soapy & Clean",
    "fresh": "Soapy & Clean", 

    "earthy": "Earthy",                
    "earth": "Earthy",
    "damp": "Earthy",
    "mushroom": "Earthy", "mushrooms": "Earthy", "matsutake": "Earthy",
    "moss": "Earthy", "mossy": "Earthy", "oakmoss": "Earthy", 
    "forest floor": "Earthy", "woodland": "Earthy", "terrasol": "Earthy", "soil": "Earthy",
    "veramoss": "Earthy",

    "metallic": "Metallic",            
    "waxy": "Aldehydic", 
    "fatty": "Aldehydic" 
}
FIELDS_TO_SCAN_FOR_KEYWORDS = ['name', 'description', 'odor_profile', 'notes']
# --- End of Keyword Categorization Setup ---

# --- Helper Functions for Import Analysis and Processing ---

def _collect_records_recursively(data, collected_records):
    """
    Recursively traverses a data structure (dict or list) and collects all items
    from lists that appear to be lists of ingredient records (i.e., lists of dictionaries).
    """
    if isinstance(data, dict):
        for key, value in data.items():
            _collect_records_recursively(value, collected_records)
    elif isinstance(data, list):
        # Check if this list contains dictionaries (potential ingredient records)
        if data and all(isinstance(item, dict) for item in data):
            collected_records.extend(data) # Add all items from this list
        else:
            # If it's a list of other things (e.g., strings, numbers, or mixed),
            # still iterate through its items in case they are dicts or lists to recurse into.
            for item in data:
                _collect_records_recursively(item, collected_records)

def gather_all_ingredient_records(json_data):
    """
    Extracts all lists of ingredient records from a parsed JSON object,
    traversing the entire nested structure.
    """
    all_records = []
    _collect_records_recursively(json_data, all_records)
    return all_records

def _get_all_fields_from_records(records):
    """
    Collects all unique field names from a list of record dictionaries.
    """
    all_field_names = set()
    for record in records:
        if isinstance(record, dict):
            for key in record.keys():
                all_field_names.add(key)
    return sorted(list(all_field_names))


# --- Analysis Functions (to be called by the /api/import/analyze route) ---
def analyze_json_smarter(file_content_string):
    """
    Analyzes JSON file content string, tries to find all data arrays,
    extracts fields from them, and provides sample data from the first found array.
    """
    try:
        data = json.loads(file_content_string)
        
        all_records = gather_all_ingredient_records(data) # Use the new recursive collector
        
        if not all_records:
            return {'error': 'No ingredient-like records (lists of objects) found anywhere in the JSON structure.'}

        fields = _get_all_fields_from_records(all_records)
        sample_data = all_records[:5] 
        item_count = len(all_records)
        
        structure_type = "nested_data"
        if isinstance(data, list) and all(isinstance(item, dict) for item in data) and len(data) == item_count:
            structure_type = "array_at_root"
        elif isinstance(data, dict):
            structure_type = "object_at_root_with_nested_lists"
        
        return {
            'format': 'json',
            'structure': structure_type, 
            'fields': fields,
            'item_count': item_count,
            'sample_data': sample_data,
            'mapping_suggestion': suggest_mapping(fields)
        }

    except json.JSONDecodeError:
        return {'error': 'Invalid JSON format: Could not parse file.'}
    except Exception as e:
        print(f"Error during JSON analysis: {str(e)}") 
        return {'error': f'Error analyzing JSON: {str(e)}'}


def analyze_csv_content(file_content_string):
    """
    Analyzes CSV file content string, extracts header and sample data.
    """
    try:
        csvfile = io.StringIO(file_content_string)
        try:
            dialect = csv.Sniffer().sniff(csvfile.read(2048)) 
            csvfile.seek(0) 
            reader = csv.reader(csvfile, dialect)
        except csv.Error: 
            csvfile.seek(0)
            reader = csv.reader(csvfile) 

        rows = list(reader)
        if not rows or len(rows) < 2 : 
            return {'error': 'Empty CSV file or CSV file contains only a header. Cannot extract records.'}
        
        header = rows[0]
        if not all(h.strip() for h in header):
            return {'error': 'CSV header contains empty field names. Please ensure all header cells have values.'}

        data_rows = rows[1:6] 
        item_count = len(rows) - 1

        sample_data_list_of_dicts = []
        for row_idx, row in enumerate(data_rows):
            if len(row) != len(header):
                 print(f"Warning: CSV row {row_idx + 2} has {len(row)} columns, header has {len(header)}. Row will be padded/truncated.")
            
            row_dict = {}
            for i, col_name in enumerate(header):
                row_dict[col_name] = row[i] if i < len(row) else None
            sample_data_list_of_dicts.append(row_dict)
            
        return {
            'format': 'csv',
            'structure': 'tabular',
            'fields': header,
            'item_count': item_count,
            'sample_data': sample_data_list_of_dicts,
            'mapping_suggestion': suggest_mapping(header)
        }
    except Exception as e:
        print(f"Error during CSV analysis: {str(e)}") 
        return {'error': f'Error analyzing CSV: {str(e)}'}

@import_bp.route('/api/import/analyze', methods=['POST'])
def analyze_import_file_route():
    """
    Route to analyze an uploaded file (JSON or CSV).
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    try:
        file_content_string = file.read().decode('utf-8-sig') 
    except UnicodeDecodeError:
        try:
            file.seek(0) 
            file_content_string = file.read().decode('latin-1') 
        except Exception as e_decode:
             return jsonify({'error': f'Could not decode file content. UTF-8 and Latin-1 failed. Error: {str(e_decode)}'}), 400
    except Exception as e_read:
        return jsonify({'error': f'Could not read file: {str(e_read)}'}), 500

    file_ext = os.path.splitext(file.filename)[1].lower()
    analysis_result = {}

    if file_ext == '.json':
        analysis_result = analyze_json_smarter(file_content_string)
    elif file_ext == '.csv':
        analysis_result = analyze_csv_content(file_content_string)
    else:
        return jsonify({'error': 'Unsupported file format. Please upload JSON or CSV.'}), 400

    if 'error' in analysis_result:
        return jsonify(analysis_result), 400 
    
    return jsonify(analysis_result)


# --- Existing suggest_mapping and process_import functions ---
def suggest_mapping(fields):
    ingredient_model_fields = {
        'name': ['name', 'ingredient_name', 'material_name', 'item_name', 'product_name', 'title', 'aroma_chemical_name', 'essential_oil_name', 'raw_material', 
                 'calone_1951_firmenich', 'sulfurol_milky', 'lilial_replacer', 'jasmacyclene_givaudan', 'orinox_pfw', 'ebanol_givaudan'],
        'description': ['description', 'desc', 'details', 'info', 'summary', 'notes', 'aroma_profile', 'olfactive_description', 'scent_profile', 
                        'enhanced_description_aroma_profile', 'product_description', 'full_description', 'characteristics', 
                        'fragrance_family_green_odor_description_fresh_gree', 'fragrance_family_ozone_odor_description_ozone_mari',
                        'fragrance_family_animalic_odor_description_animali', 'fresh_slightly_green_lily_watery_this_replacer_is_',
                        'fragrance_family_floral_odor_description_floral_gr', 'fragrance_family_wood_odor_description_dry_woody_l',
                        'fragrance_family_woody_odor_description_woody_sand'],
        'supplier': ['supplier', 'vendor', 'manufacturer', 'source', 'brand', 'distributor', 'supplied_by'],
        'supplier_code': ['supplier_code', 'vendor_code', 'product_code', 'sku', 'item_code', 'model_number', 'manufacturer_part_number', 'mpn', 'supplier_sku', 'vendor_sku', 'reference_code'],
        'cost_per_unit': ['cost_per_unit', 'cost', 'price', 'unit_cost', 'price_per_unit', 'purchase_price', 'material_cost', 'ingredient_cost', 'value_per_unit'],
        'unit_of_measurement': ['unit_of_measurement', 'unit', 'uom', 'measurement_unit', 'quantity_unit', 'size_raw', 'size', 'measure', 'pack_size_unit', 'standard_unit'],
        'stock_quantity': ['stock_quantity', 'quantity', 'qty', 'stock', 'inventory', 'amount', 'in_stock', 'on_hand', 'available_stock', 'current_stock', 'units_in_stock'],
        'minimum_stock_threshold': ['minimum_stock_threshold', 'min_stock', 'reorder_point', 'minimum_quantity', 'low_stock_level', 'safety_stock', 'min_inventory_level'],
        'viscosity': ['viscosity', 'thickness', 'consistency', 'flow_rate'],
        'color': ['color', 'colour', 'appearance', 'shade', 'hue', 'visual_description'],
        'odor_profile': ['odor_profile', 'scent', 'smell', 'aroma', 'fragrance', 'odor', 'odour', 'notes_olfactives', 'olfactive_family', 'olfactory_profile', 'top_notes', 'middle_notes', 'base_notes', 'heart_notes', 
                         'fragrance_family_green_odor_description_fresh_gree', 'fragrance_family_ozone_odor_description_ozone_mari',
                         'fragrance_family_animalic_odor_description_animali', 'fresh_slightly_green_lily_watery_this_replacer_is_',
                         'fragrance_family_floral_odor_description_floral_gr', 'fragrance_family_wood_odor_description_dry_woody_l',
                         'fragrance_family_woody_odor_description_woody_sand'], 
        'ifra_restricted': ['ifra_restricted', 'restricted', 'ifra_restriction', 'restriction_status', 'is_restricted', 'regulatory_flag', 'ifra_compliance'],
        'ifra_restriction_details': ['ifra_restriction_details', 'restriction_details', 'ifra_details', 'regulatory_info', 'usage_limits', 'compliance_notes', 'ifra_notes'],
        'safety_notes': ['safety_notes', 'safety', 'safety_info', 'hazards', 'sds', 'msds', 'handling_instructions', 'precautions', 'allergen_info', 'enhanced_description_safety_notes'],
        'notes': ['notes', 'comments', 'additional_info', 'remarks', 'extra_details', 'internal_notes', 'observation', 'use', 'enhanced_description_function', 'enhanced_description_species', 'enhanced_description_key_characteristics_wisdom', 'enhanced_description_cosmetic_uses', 'type', 'descriptors', 
                  'fragrance_family_green_odor_description_fresh_gree', 'fragrance_family_ozone_odor_description_ozone_mari',
                  'fragrance_family_animalic_odor_description_animali', 'fresh_slightly_green_lily_watery_this_replacer_is_',
                  'fragrance_family_floral_odor_description_floral_gr', 'fragrance_family_wood_odor_description_dry_woody_l',
                  'fragrance_family_woody_odor_description_woody_sand'], 
        '_categories_source_key_': ['categories', 'category', 'tags', 'descriptors', 'descriptor_list', 'olfactive_group', 'type', 'classification', 'family', 'function', 'fragrance_family'] 
    }
    mapping = {target: None for target in ingredient_model_fields.keys()}
    if not fields: return mapping
    file_fields_normalized_map = { str(f).lower().replace(' ', '_').replace('-', '_'): str(f) for f in fields if isinstance(f, (str, int, float)) } 
    for target_model_field, possible_source_names in ingredient_model_fields.items():
        for possible_name_variant in possible_source_names:
            normalized_possible_name = possible_name_variant.lower().replace(' ', '_').replace('-', '_')
            if normalized_possible_name in file_fields_normalized_map:
                mapping[target_model_field] = file_fields_normalized_map[normalized_possible_name]; break 
            if not mapping[target_model_field]: 
                for f_norm_key, original_f_case in file_fields_normalized_map.items():
                    if normalized_possible_name in f_norm_key: 
                        mapping[target_model_field] = original_f_case; break
    return mapping

@import_bp.route('/api/import/process', methods=['POST'])
def process_import():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
    
    payload = request.json
    required_fields = ['mapping', 'import_type', 'format', 'raw_file_content'] 
    for field in required_fields:
        if field not in payload:
            return jsonify({'error': f'Missing required field: {field}'}), 400

    if payload['import_type'] != 'ingredients':
        return jsonify({'error': f"Import type '{payload['import_type']}' not yet supported."}), 400

    mapping = payload.get('mapping', {})
    records_to_process = []
    
    # NEW: Initialize separate lists for different types of feedback
    imported_count = 0
    skipped_count = 0 
    critical_error_list = [] 
    category_warning_list = []
    
    if payload['format'] == 'json':
        try:
            full_json_data = json.loads(payload['raw_file_content'])
            records_to_process = gather_all_ingredient_records(full_json_data) 
            if not records_to_process:
                 # This is a critical issue if no records are found at all.
                 critical_error_list.append("No ingredient-like records (lists of objects) found anywhere in the JSON structure.")
                 return jsonify({
                     'success': False, 
                     'message': "No ingredient records found in the JSON structure.", 
                     'imported_count': 0, 
                     'skipped_count': 0, # Or len(full_json_data) if it's a list that was expected
                     'errors': critical_error_list, 
                     'category_warnings': []
                }), 200 # 200 because the request was valid, but data was unusable.
        except json.JSONDecodeError: 
            critical_error_list.append("Invalid JSON format in raw_file_content.")
            return jsonify({'success': False, 'message': "Invalid JSON format.", 'errors': critical_error_list, 'imported_count': 0, 'skipped_count': 0, 'category_warnings': [] }), 400
        except Exception as e:
            print(f"Error processing raw JSON for import: {type(e).__name__} - {str(e)}")
            critical_error_list.append(f"Error extracting records from raw JSON content: {str(e)}")
            return jsonify({'success': False, 'message': "Error processing JSON.", 'errors': critical_error_list, 'imported_count': 0, 'skipped_count': 0, 'category_warnings': []}), 500
            
    elif payload['format'] == 'csv':
        try:
            content = payload['raw_file_content']
            csvfile = io.StringIO(content)
            reader = csv.DictReader(csvfile)
            records_to_process = [dict(row) for row in reader] 
            if not records_to_process and content.strip(): 
                critical_error_list.append("Could not parse any records from CSV or CSV is empty after header.")
                return jsonify({'success': False, 'message': "No records parsed from CSV.", 'errors': critical_error_list, 'imported_count': 0, 'skipped_count': 0, 'category_warnings': []}), 400
        except Exception as e:
            print(f"Error processing raw CSV for import: {type(e).__name__} - {str(e)}")
            critical_error_list.append(f"Error extracting records from raw CSV content: {str(e)}")
            return jsonify({'success': False, 'message': "Error processing CSV.", 'errors': critical_error_list, 'imported_count': 0, 'skipped_count': 0, 'category_warnings': []}), 500
    else:
        critical_error_list.append("Unsupported format or missing raw_file_content.")
        return jsonify({'success': False, 'message': "Unsupported import format.", 'errors': critical_error_list, 'imported_count': 0, 'skipped_count': 0, 'category_warnings': []}), 400

    if not records_to_process and not critical_error_list: # If no records but no prior critical error
        critical_error_list.append('No records were extracted to process.')
        # Fall through to return standard response structure

    for index, item_data_flat in enumerate(records_to_process):
        current_item_name_for_error = f"Source Record Index {index + 1}" 
        new_ingredient_attrs = {} 
        
        try:
            # --- NAME PROCESSING ---
            name_source_key = mapping.get('name')
            item_name_value = None
            if name_source_key and name_source_key in item_data_flat:
                item_name_value = item_data_flat[name_source_key]
            
            if not item_name_value: 
                common_name_keys = ['name', 'Name', 'IngredientName', 'Material Name', 'Product Name', 
                                    'calone_1951_firmenich', 'sulfurol_milky', 'lilial_replacer', 
                                    'jasmacyclene_givaudan', 'orinox_pfw', 'ebanol_givaudan']
                for key_try in common_name_keys:
                    if key_try in item_data_flat and item_data_flat[key_try]:
                        item_name_value = item_data_flat[key_try]; break
            
            if item_name_value and str(item_name_value).strip():
                new_ingredient_attrs['name'] = str(item_name_value).strip()
                current_item_name_for_error = f"Record '{new_ingredient_attrs['name']}' (Source Index {index + 1})"
            else:
                critical_error_list.append(f"{current_item_name_for_error}: Skipped - 'name' is missing, empty, or could not be auto-detected."); skipped_count += 1; continue
            
            if Ingredient.query.filter_by(name=new_ingredient_attrs['name']).first():
                critical_error_list.append(f"{current_item_name_for_error}: Skipped - Ingredient with this name already exists."); skipped_count += 1; continue
            
            # --- CORE ATTRIBUTE MAPPING ---
            for model_attr, source_key_suggestion in mapping.items():
                if model_attr == 'name' or model_attr == '_categories_source_key_': continue 
                
                value_from_source = None
                if source_key_suggestion and source_key_suggestion in item_data_flat:
                    value_from_source = item_data_flat[source_key_suggestion]
                elif model_attr in item_data_flat: # Direct match if no suggestion or suggestion not found
                    value_from_source = item_data_flat[model_attr]

                if value_from_source is not None:
                    if model_attr in ['cost_per_unit', 'stock_quantity', 'minimum_stock_threshold']:
                        if str(value_from_source).strip() != '':
                            try: 
                                cleaned_value = re.sub(r'[^\d\.-]', '', str(value_from_source))
                                if cleaned_value: new_ingredient_attrs[model_attr] = float(cleaned_value)
                            except (ValueError, TypeError): 
                                # This is a data issue for an imported ingredient, log as warning for now, or could be critical_error
                                category_warning_list.append(f"{current_item_name_for_error}: Invalid numeric value '{value_from_source}' for '{model_attr}'. Field left blank.")
                    elif model_attr == 'ifra_restricted':
                        new_ingredient_attrs[model_attr] = str(value_from_source).lower().strip() in ['true', '1', 'yes', 'restricted']
                    else: 
                        new_ingredient_attrs[model_attr] = str(value_from_source).strip()
            
            ingredient = Ingredient(**new_ingredient_attrs)
            db.session.add(ingredient)
            db.session.flush() # Get ID for category associations

            # --- CATEGORY ASSIGNMENT ---
            assigned_category_ids = set()
            source_field_for_categories = mapping.get('_categories_source_key_')
            if source_field_for_categories and source_field_for_categories in item_data_flat:
                category_data = item_data_flat[source_field_for_categories]
                category_names_to_process = []
                if isinstance(category_data, str):
                    try: 
                        parsed_list = json.loads(category_data)
                        if isinstance(parsed_list, list): category_names_to_process = [str(cn).strip() for cn in parsed_list if str(cn).strip()]
                        else: category_names_to_process = [str(parsed_list).strip()] if str(parsed_list).strip() else []
                    except json.JSONDecodeError: 
                        match = re.search(r"Fragrance Family:\s*([\w\s&/-]+)", category_data, re.IGNORECASE)
                        if match: family_str = match.group(1); category_names_to_process = [name.strip() for name in re.split(r'[&/,]', family_str) if name.strip()]
                        else: category_names_to_process = [name.strip() for name in category_data.split(',') if name.strip()]
                elif isinstance(category_data, list): 
                     category_names_to_process = [str(cn).strip() for cn in category_data if str(cn).strip()]

                for cat_name_raw in category_names_to_process:
                    for cat_name in re.split(r'[&/,]', cat_name_raw):
                        cat_name = cat_name.strip()
                        if not cat_name: continue
                        category_obj = Category.query.filter(Category.name.ilike(cat_name)).first() 
                        if not category_obj: 
                            mapped_core_cat_name = KEYWORD_TO_CORE_CATEGORY.get(cat_name.lower())
                            if mapped_core_cat_name: category_obj = Category.query.filter(Category.name.ilike(mapped_core_cat_name)).first()
                            if not category_obj: 
                                category_warning_list.append(f"{current_item_name_for_error}: Category '{cat_name}' (or its keyword map) not found."); continue 
                        if category_obj and category_obj.id not in assigned_category_ids:
                            ingredient.categories.append(category_obj); assigned_category_ids.add(category_obj.id)
            
            text_to_scan_combined = ""
            for target_model_field in FIELDS_TO_SCAN_FOR_KEYWORDS:
                source_key_for_scan = mapping.get(target_model_field)
                field_content = None
                if source_key_for_scan and source_key_for_scan in item_data_flat:
                    field_content = item_data_flat[source_key_for_scan]
                elif target_model_field in item_data_flat:
                    field_content = item_data_flat[target_model_field]
                if field_content is not None: text_to_scan_combined += " " + str(field_content).lower()
            
            if text_to_scan_combined.strip(): 
                for keyword, core_category_name in KEYWORD_TO_CORE_CATEGORY.items():
                    pattern = rf'\b{re.escape(keyword.lower())}\b' if ' ' not in keyword.lower() else re.escape(keyword.lower())
                    if re.search(pattern, text_to_scan_combined):
                        core_category_obj = Category.query.filter(Category.name.ilike(core_category_name)).first()
                        if core_category_obj and core_category_obj.id not in assigned_category_ids:
                            ingredient.categories.append(core_category_obj); assigned_category_ids.add(core_category_obj.id)
                        elif not core_category_obj:
                             category_warning_list.append(f"{current_item_name_for_error}: Keyword '{keyword}' matched, but target category '{core_category_name}' not found.")
            
            imported_count += 1 # Ingredient successfully processed and added to session

        except Exception as e: # Catch any other unexpected error during this record's processing
            # This implies a more severe issue with the record's data or logic
            critical_error_list.append(f"Error processing record '{current_item_name_for_error}': {type(e).__name__} - {str(e)}. Record skipped.")
            skipped_count += 1
            # db.session.rollback() # Not strictly needed here if final commit fails, it rolls all back.
                                  # If we wanted to be super safe and this error was after add/flush,
                                  # we might consider removing the specific 'ingredient' from session,
                                  # but that's complex. Simpler to let final commit handle batch.
            import traceback
            print(f"--- UNEXPECTED ERROR PROCESSING RECORD: {current_item_name_for_error} ---")
            traceback.print_exc()
            print(f"--- END ERROR ---")
            continue 
            
    # --- Attempt to commit the batch ---
    if imported_count > 0 : # Only attempt commit if there are items to import
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            commit_error_msg = f'Database commit failed: {str(e)}. All {imported_count} processed ingredients in this batch were rolled back.'
            print(f"Database commit error: {str(e)}") 
            critical_error_list.append(commit_error_msg)
            # Adjust counts as nothing was actually committed
            skipped_count += imported_count # These are now considered skipped
            imported_count = 0
            # The response will be built below, success will be false.
    
    # --- Prepare final response ---
    final_success_flag = imported_count > 0 and not critical_error_list 
    # If there was a commit error, critical_error_list will not be empty, making success false.

    final_message = f'Import finished. Imported: {imported_count}, Skipped: {skipped_count}.'
    if category_warning_list:
        final_message += f" {len(category_warning_list)} category assignment warning(s)."
    if critical_error_list:
        final_message += f" {len(critical_error_list)} critical error(s) encountered."
    elif not records_to_process and not critical_error_list and not category_warning_list: # Edge case: empty file but no errors
        final_message = "Import file was empty or contained no processable records."


    return jsonify({ 
        'success': final_success_flag, 
        'message': final_message, 
        'imported_count': imported_count, 
        'skipped_count': skipped_count, 
        'errors': critical_error_list, 
        'category_warnings': category_warning_list 
    })
