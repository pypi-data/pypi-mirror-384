import mimetypes, traceback
from openai import OpenAI
import json
import os
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
import pdfplumber
import docx2txt
import html
from weasyprint import HTML
import weaviate
from weaviate.gql.get import HybridFusion
import re
import loggerutility as logger
import commonutility as common

# from .OpenAIDataExtractor import OpenAIDataExtractor
# from .GenerateExtractTemplate import GenerateExtractTemplate

class Document_Automated_Training:

    alphaValue = 0.54

    def identify_complexity_layout_structure(self, extracted_text, openai_api_key):
        try:
            prompt = f"""
                From the following text which is extracted from a customer purchase order. Analyze the layout and answer following specific questions
                -What is the complexity percentage of the layout simplest is 0 most complex is 100 (complexity_perc)?
                Note: Basis of complexity should be if the data is organized in a simple, structured and easy to extract to structured format
                -Is the line items grouped by Division (division_grouping)?
                -Is there a summary line at the end of Items of a division (is_division_summary)?
                -Is the layout containing multiple data sets in the same row next to each other (is_layout_columnar)?
                -How many sets are there in a row (no_datasets_in_row)?
                -Is there a free quantity column in the document (free_quantity_column)? **Free quantity can be referred as Free, Scheme, Sch, Offer, Bonus, FQ**
                -Is the free quantity specified as a calculation or arithmetic expression with order quantity (free_as_calculation)?
                -Is free quantity specified as a percentage (is_free_percentage)?
                -Is there multiple orders in the same document (multiple_order)?
                -Return the distinct division list in the order (division_list).
                -Is the document an unstructured email. There is no organized data in any pattern(unstructured_email)?
                Return the data in json format with tag specified against the question with answer as true, false or number

                Text:
                \"\"\"
                {extracted_text}
                \"\"\"
                """
            
            message = [{
                "role": "user",
                "content": prompt
            }]
            logger.log(f'-------------------------------------------------------------------------------------')
            logger.log(f'\nDocument_Automated_Training identify_complexity_layout_structure prompt: {message}')
            logger.log(f'-------------------------------------------------------------------------------------')

            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                            model='gpt-4.1',
                            messages=message,
                            temperature=0
                        )
            result =  completion.choices[0].message.content 
            # reply = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))
            match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            data = {}
            if match:
                json_str = match.group(1).strip()
                json_str = json_str.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","")
                data = json.loads(json_str)
            return data        
        except Exception as error:
            raise str(error)  

    def identify_customer_keywords(self, extracted_text, openai_api_key):
        try:
            prompt = f"""
                Following is an extracted text from a purchase order document issued by a customer to supply goods. 
                Identify unique keywords from the data. The keyword should be such that it would be always present 
                in this type of document received. All keywords together should be unique enough to ensure that a 
                code can identify the customer using regex. Typical keywords can be name of customer, part of address 
                such as city, GST No, customer telephone number. Just return maximum 4 in csv string

                Text:
                \"\"\"
                {extracted_text}
                \"\"\"
            """

            message = [{
                "role": "user",
                "content": prompt
            }]

            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                            model='gpt-4.1',
                            messages=message,
                            temperature=0
                        )
            result =  completion.choices[0].message.content 
            return result        
        except Exception as error:
            raise str(error)  
    
    def identify_customer_code(self, cust_name, openai_api_key, schemaName_Updated, server_url, site_code):
        try:
            logger.log(f'\ncust_name : {cust_name}')
            logger.log(f'\nopenai_api_key : {openai_api_key}')
            logger.log(f'\nschemaName_Updated : {schemaName_Updated}')
            logger.log(f'\nserver_url : {server_url}')
            logger.log(f'\nsite_code : {site_code}')

            finalResultJson = {}
            client = weaviate.Client(server_url,additional_headers={"X-OpenAI-Api-Key": openai_api_key})
            logger.log(f'Connection is establish : {client.is_ready()}')

            schemaClasslist = [i['class'] for i in client.schema.get()["classes"]]  
            logger.log(f'schemaClasslist : {schemaClasslist}')

            inputQuery  = cust_name.upper().replace("N/A","").replace("."," ").replace(","," ").replace("-"," ").replace("_"," ")
            logger.log(f'inputQuery : {inputQuery}')
            
            if schemaName_Updated in schemaClasslist:
                logger.log(f'Inside schemaClasslist')
                response    = (
                    client.query
                    .get(schemaName_Updated, ["description", "answer","site_code"]) 
                    .with_hybrid(
                                    alpha       =  self.alphaValue ,
                                    query       =  inputQuery.strip() ,
                                    fusion_type =  HybridFusion.RELATIVE_SCORE
                                )
                    #START - ADDED BY SANDHIYA ON 29 SEPT 2025                               
                    .with_where({
                        "path": ["site_code"],
                        "operator": "Equal",
                        "valueString": site_code
                    })
                    #END
                    .with_additional('score')
                    .with_limit(10)
                    .do()
                    )
                logger.log(f"Input ::: {cust_name}")
                if response != {}:
                    response_List = response['data']['Get'][schemaName_Updated] 
                    finalResultJson = {"cust_code": response_List[0]['answer'] , "cust_name": response_List[0]['description'] } if len(response_List) > 0 else {}

                    for index in range(len(response_List)):
                        cust_name           = response_List[index]['description']
                        cust_name           = cust_name.upper().replace("N/A","").replace("."," ").replace(","," ").replace("-"," ").replace("_"," ")
                        cust_code           = response_List[index]['answer']

                        descr_replaced      = cust_name.replace(" ", "") 
                        inputQuery_replaced = inputQuery.replace(" ", "")

                        if descr_replaced == inputQuery_replaced:
                            logger.log(f"\n Input::: '{inputQuery_replaced}' MATCHEDD with description ::: '{descr_replaced}' \n")
                            finalResultJson    =  {"cust_code": cust_code, "cust_name": cust_name } 
                            break
                        else:
                            logger.log(f"\n Input '{inputQuery_replaced}' not matched with returned response description '{descr_replaced}'\n ")    
                return finalResultJson        
        except Exception as error:
            raise str(error)  
    
    def identify_line_example(self, extracted_text, openai_api_key):
        try:
            message = [
            {
                "role": "user",
                "content": "Give me examples of product names."
            },
            {
                "role": "assistant",
                "content": "Example of Product Names are ACTIFED DM, ANGIOTEC, ANSOLAR, ARZERRA, AUGMENTIN, AUGMENTIN DDS, AUGMENTIN DUO, AUGMENTIN ES, AVAMYS, BACTROBAN, BANOCIDE, BANOCIDE FORTE, BECADEXAMIN, BETNESOL, BETNESOL FORTE, BETNESOL N, BETNOVATE, BETNOVATE C, BETNOVATE GM, BETNOVATE N, BETNOVATE S, BIDURET, BIDURET-L, BOOSTRIX, BREVOXYL, CALPOL, CALPOL T, CARZEC, CCM, CEFSPAN, CEFTUM, CERVARIX, CERVARIX PRTC, CETZINE, CETZINE A, CLINDOXYL, COBADEX, COBADEX CZS, COBADEX FORTE, COBADEX Z, DAPSONE, DERMOCALM, DILOSYN, DITIDE, ELTROXIN, ESPAZINE, EUMOSONE, EUMOSONE M, FACEMASK, FEFOL, FEFOL Z, FESOVIT, FLIXONASE, FLIXOTIDE, FLUARIX, FLUARIX TETRA, FLUTIBACT, FLUTIVATE, FORTUM, GLACEX, GRISOVIN, GRISOVIN FP, HAVRIX, HYCAMTIN, ICTACETAM, INFANRIX CCT, INFANRIX HEXA, IODEX, IODEX RUB, LANOXIN, LONGCET, MENVEO, NEOSPORIN, NEOSPORIN-H, NEOTREXATE, NUCALA, NUCALA FD, OILATUM, OSTO, OSTOCALCIUM, PHEXIN, PHEXIN BD, PHYSIOGEL, PHYSIOGEL HYPOALLERGENIC, PHYSIOGEL HYPOALLERGENIC CRAI, PHYSIOGEL HYPOALLERGENIC DMT, PIRITON, PIRITON CS, PRIORIX, RELVAR, RELVAR ELLIPTA, ROSUTEC, ROTARIX, SARNA, SEPMAX DS, SEPTRAN, SERETIDE, SPECTRABAN, STIEPROX, SUPACEF, SYNFLORIX, T-BACT, TENOVATE, TENOVATE GN, TENOVATE M, TOPGRAF, TRELEGY ELLIPTA, URICOSTAT, VARILRIX, VIBELAN FORTE, VOTRIENT, VOZET, XGEVA, ZENTEL, ZEVIT, ZIMIG, ZIMIVIR, ZINETAC, ZODERM, ZODERM E, ZOVIRAX, ZOVIRAX FD, ZUPAR, ZYLORICACTIFED DM, ANGIOTEC, ANSOLAR, ARZERRA, AUGMENTIN, AUGMENTIN DDS, AUGMENTIN DUO, AUGMENTIN ES, AVAMYS, BACTROBAN, BANOCIDE, BANOCIDE FORTE, BECADEXAMIN, BETNESOL, BETNESOL FORTE, BETNESOL N, BETNOVATE, BETNOVATE C, BETNOVATE GM, BETNOVATE N, BETNOVATE S, BIDURET, BIDURET-L, BOOSTRIX, BREVOXYL, CALPOL, CALPOL T, CARZEC, CCM, CEFSPAN, CEFTUM, CERVARIX, CERVARIX PRTC, CETZINE, CETZINE A, CLINDOXYL, COBADEX, COBADEX CZS, COBADEX FORTE, COBADEX Z, DAPSONE, DERMOCALM, DILOSYN, DITIDE, ELTROXIN, ESPAZINE, EUMOSONE, EUMOSONE M, FACEMASK, FEFOL, FEFOL Z, FESOVIT, FLIXONASE, FLIXOTIDE, FLUARIX, FLUARIX TETRA, FLUTIBACT, FLUTIVATE, FORTUM, GLACEX, GRISOVIN, GRISOVIN FP, HAVRIX, HYCAMTIN, ICTACETAM, INFANRIX CCT, INFANRIX HEXA, IODEX, IODEX RUB, LANOXIN, LONGCET, MENVEO, NEOSPORIN, NEOSPORIN-H, NEOTREXATE, NUCALA, NUCALA FD, OILATUM, OSTO, OSTOCALCIUM, PHEXIN, PHEXIN BD, PHYSIOGEL, PHYSIOGEL HYPOALLERGENIC, PHYSIOGEL HYPOALLERGENIC CRAI, PHYSIOGEL HYPOALLERGENIC DMT, PIRITON, PIRITON CS, PRIORIX, RELVAR, RELVAR ELLIPTA, ROSUTEC, ROTARIX, SARNA, SEPMAX DS, SEPTRAN, SERETIDE, SPECTRABAN, STIEPROX, SUPACEF, SYNFLORIX, T-BACT, TENOVATE, TENOVATE GN, TENOVATE M, TOPGRAF, TRELEGY ELLIPTA, URICOSTAT, VARILRIX, VIBELAN FORTE, VOTRIENT, VOZET, XGEVA, ZENTEL, ZEVIT, ZIMIG, ZIMIVIR, ZINETAC, ZODERM, ZODERM E, ZOVIRAX, ZOVIRAX FD, ZUPAR, ZYLORIC"
            },
            {
                "role": "user",
                "content": "Give me examples of Delivery methods."
            },
            {    
                "role": "assistant",
                "content": "Example Delivery Methods are BALM, BAR, BLISTER, BOTTLE, CAPSULE, CREAM, DROP, EAR DROPS, EMOLLIENT, EYE OINTMENT, EYE/EAR DROPS, FOC, GEL, IN, INF, INJ, INTRAVENOUS, LIQUID, LOTION, NASAL SPRAY, OIL, OINTMENT, ORAL DROPS, POWDER, SENSITIVE, SOLUTION, SPRAY, SUPPRES, SYRUP, TABLET, TABLET, TM, TP, ULTRAGEL, WFRAEROSOL, WFR, AI."
            },
            {
                "role": "user",
                "content": "Give me some examples of Product Strengths.",
            },
            {
                "role": "assistant",
                "content": "Example of Product Strengths are 0.03, 0.05, 0.1, 0.5, 1, 1.16, 1.2, 1.5, 10, 100, 1000, 120, 125, 15, 16, 1G, 2, 20, 200, 22, 25, 250, 3, 3.125, 30, 300, 325, 375, 4, 40, 400, 5, 50, 500, 50M, 6.25, 600, 625, 650, 720, 75, 750, 8, 80, 800, 88, CCT, FPS 30, PREFILLED, SPF300.03. The values can be in mg, milligram or other suffixes.",                
            },
            {
                "role": "user",
                "content": "Give me some examples of Sizes.",
            },
            {
                "role": "assistant",
                "content": "Example of Sizes are 1, 1.7, 10, 100, 1000, 10X10, 10X15, 10X3X15, 10X45, 10X7, 115, 120, 15, 15X10, 16, 1X120, 20, 200, 20X10, 20X100, 20X120, 20X15, 20X20, 20X30, 20X60, 20X600, 20X7, 21X10, 21X30, 25, 25X10, 25X15, 25X20, 30, 30X10, 30X15, 35, 3X5, 4, 40, 450, 45X15, 460, 5, 50, 5X10, 5X15, 5X4, 5X5, 60, 6X15, 6X30, 6X40, 7.5, 75, 750, 7X3, 8, 80, FOC, PACK, TPX1, VIAL1, 1.7, 10, 100, 1000, 10X10, 10X15, 10X3X15, 10X45, 10X7, 115, 120, 15, 15X10, 16, 1X120, 20, 200, 20X10, 20X100, 20X120, 20X15, 20X20, 20X30, 20X60, 20X600, 20X7, 21X10, 21X30, 25, 25X10, 25X15, 25X20, 30, 30X10, 30X15, 35, 3X5, 4, 40, 450, 45X15, 460, 5, 50, 5X10, 5X15, 5X4, 5X5, 60, 6X15, 6X30, 6X40, 7.5, 75, 750, 7X3, 8, 80, FOC, PACK, TPX1, VIAL",
            },
            {
                "role": "user",
                "content": "Give me some examples of packing or ordering units.",
            },
            {
                "role": "assistant",
                "content": "Example of Ordering units are BOT, BOTT, BOTTLE, BOTTLES, BOX, BOXES, BX, C/S, CASE, CASES, CS, DEVICE, DOSES, PC, PCS, SINGLE, STR, STRIP, STRIPS, TAB, TABLET, TUBES, UNIT, UNITS, VIAL, VIALS, NOS, AMP, 0.5ML, 04''S, 1, 1 TAB, 1 VIAL, 1 X 15S, 1.5GM, 110, 110GM, 115, 115GM, 10, 10 CAP, 10 GMS, 10 ML, 10 TAB, 10 TAB, 10''S, 100, 100''S, 1000, 1000TAB, 100ML, 100T, 100TAB, 100X1M, 10CAP, 10CAPS, 10G, 10GM, 10T, 10TAB, 10X10, 10X10G, 10X10T, 120, 120 NOS, 120 TAB, 120S, 120T, 120GM, 120MD, 120TAB, 15, 15 GM, 15 ML, 15 NOS, 15 TAB, 15', 15CAP, 15G, 15GM, 15GMS, 15ML, 15T, 15TAB, 1ML, 1PACK, 1VAIL, 1X120TAB, 1X15, 1X15G, 1X15G, 1X15GM, 1X15ML, 1X1TAB, 1X20, 1X25GM, 1X30G, 1X4, 1X40GM, 1X60ML, 20 GM, 20 TAB, 20S, 20''S, 20''S, 20GM, 20TAB, 20x120, 20x15', 20x30, 21x10', 25 GM, 25GM, 25x10, 25X10T, 25X60, 30, 30 CAP, 30 GM, 30 GMS, 30 MD, 30 ML, 30 MLS, 30 TAB, 30', 30''S, 30''S, 30g, 30GM, 30ML, 30TAB, 30X30ML, 3TAB, 3X100T, 4, 4 CAP, 4 TAB, 4''S, 4S, 40`, 40GM, 40TAB, 45X120, 48X10, 4TAB, 5, 5 bx, 5 GM, 5 ML, 5 STRIP, 5 TAB, 5'S, 50 GM, 50 ML, 50GM, 50gm, 50ML, 50ML, 50X60ML, 5AMP, AMP, 5GM, 5MG, 5ML, 5ml, 5S, 5x10, 5X10, 5X1ML, 5X4, 5X4TAB, 5x5', 60, 60 ML, 60''S, 60`S, 60BLIST, 60ML, 60S, 60TAB, 6x40, 7, 7 TAB, 7 TABS, 7.5GM, 7', 7's, 72x20', 7TAB, 7TABS, 8 S, 81ML, 81VIAL, 8X1ML.",
            },
            {
                "role": "user",
                "content": "Give me examples of sku configuration.",
            },
            {
                "role": "assistant",
                "content": "Examples of SKU Name configuration are following. In SKU Name BECADEXAMIN CAP, Product Name is BECADEXAMIN, Delivery Method is CAP. In SKU Name BETNESOL FORTE 1X1ML, Product Name is BETNESOL FORTE, Ordering unit is 1X1ML. In SKU Name ZIMIVIR-500 3.TAB, Product Name is ZIMIVIR, Delivery Method is TAB, Product Strength is 500, Size is 3.TAB. In SKU Name T-BACT-15GM OINTMENT, Product Name is T-BACT, Delivery Method is OINTMENT, Size is 15GM. In SKU Name AUGMENTIN 625 DUO TAB, Product Name is AUGMENTIN DUO, Delivery Method is TAB, Product Strength is 625.",
            },
            {
                "role": "user",
                "content": f"""From the following text which is extracted from a customer purchase order. Extract only distinct patterns of line item raw data. Distinct should be identified based on the way line item data is organized. /* Ordering units can be standard packing of items or any other units such as box or case pack.  When an ordering-unit is present, output it **exactly as written in the source (line-item), including capitalisation and punctuation**; do not expand, translate, or normalise it.   **Always use the ordering-unit that already appears in the line-item. Only if the ordering unit is not specified, derive it using the following table.**  Derive-Unit table (tablet or cap or capsule = STRIPS, syrup or cream or ointment = NOS, injection or  inj = VIALS) */ /* If the quantity is specified as numeric value1 + numeric value2 calculate quantity by adding both the values. In this case the 1st numeric value is the chargeable quantity and the 2nd value is the free quantity. When the free quantity is specified as a percentage, do not perform the calculation, just consider  the chargeable value as the quantity. Give me the quantity and free quantity in string format.*/ For each distinct line item extract raw data, Line No, Sku Name, Packing (Ordering unit), Order Quantity, Free Quantity or Percentage(if specified), From SKU Name also identify Product Name, Delivery method (Tablet, Capsules, Injection, Powder, Syrup), Product Strength, Pack Size Return only the data in json format with following tag name sample_id, raw_data, line_no, sku_name, ordering_unit, quantity, free_quantity, free_percent, product_name, strength, pack_size, delivery_method. Process following data and build the line example 
                    Text:
                    \"\"\"
                    {extracted_text}
                    \"\"\"
                """
            }]

            logger.log(f'-------------------------------------------------------------------------------------')
            logger.log(f'\nDocument_Automated_Training identify_line_example prompt: {message}')
            logger.log(f'-------------------------------------------------------------------------------------')

            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                            model='gpt-4.1',
                            messages=message,
                            temperature=0
                        )
            result =  completion.choices[0].message.content
            # reply = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))
            match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            data = {}
            if match:
                json_str = match.group(1).strip()
                json_str = json_str.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","").replace("'","").replace("`","")
                data = json.loads(json_str)
            return data        
        except Exception as error:
            raise str(error)  
        
    def identify_line_example_two_column(self, extracted_text, openai_api_key):
        try:
            message = [
            {
                "role": "user",
                "content": "Give me examples of product names."
            },
            {
                "role": "assistant",
                "content": "Example of Product Names are ACTIFED DM, ANGIOTEC, ANSOLAR, ARZERRA, AUGMENTIN, AUGMENTIN DDS, AUGMENTIN DUO, AUGMENTIN ES, AVAMYS, BACTROBAN, BANOCIDE, BANOCIDE FORTE, BECADEXAMIN, BETNESOL, BETNESOL FORTE, BETNESOL N, BETNOVATE, BETNOVATE C, BETNOVATE GM, BETNOVATE N, BETNOVATE S, BIDURET, BIDURET-L, BOOSTRIX, BREVOXYL, CALPOL, CALPOL T, CARZEC, CCM, CEFSPAN, CEFTUM, CERVARIX, CERVARIX PRTC, CETZINE, CETZINE A, CLINDOXYL, COBADEX, COBADEX CZS, COBADEX FORTE, COBADEX Z, DAPSONE, DERMOCALM, DILOSYN, DITIDE, ELTROXIN, ESPAZINE, EUMOSONE, EUMOSONE M, FACEMASK, FEFOL, FEFOL Z, FESOVIT, FLIXONASE, FLIXOTIDE, FLUARIX, FLUARIX TETRA, FLUTIBACT, FLUTIVATE, FORTUM, GLACEX, GRISOVIN, GRISOVIN FP, HAVRIX, HYCAMTIN, ICTACETAM, INFANRIX CCT, INFANRIX HEXA, IODEX, IODEX RUB, LANOXIN, LONGCET, MENVEO, NEOSPORIN, NEOSPORIN-H, NEOTREXATE, NUCALA, NUCALA FD, OILATUM, OSTO, OSTOCALCIUM, PHEXIN, PHEXIN BD, PHYSIOGEL, PHYSIOGEL HYPOALLERGENIC, PHYSIOGEL HYPOALLERGENIC CRAI, PHYSIOGEL HYPOALLERGENIC DMT, PIRITON, PIRITON CS, PRIORIX, RELVAR, RELVAR ELLIPTA, ROSUTEC, ROTARIX, SARNA, SEPMAX DS, SEPTRAN, SERETIDE, SPECTRABAN, STIEPROX, SUPACEF, SYNFLORIX, T-BACT, TENOVATE, TENOVATE GN, TENOVATE M, TOPGRAF, TRELEGY ELLIPTA, URICOSTAT, VARILRIX, VIBELAN FORTE, VOTRIENT, VOZET, XGEVA, ZENTEL, ZEVIT, ZIMIG, ZIMIVIR, ZINETAC, ZODERM, ZODERM E, ZOVIRAX, ZOVIRAX FD, ZUPAR, ZYLORICACTIFED DM, ANGIOTEC, ANSOLAR, ARZERRA, AUGMENTIN, AUGMENTIN DDS, AUGMENTIN DUO, AUGMENTIN ES, AVAMYS, BACTROBAN, BANOCIDE, BANOCIDE FORTE, BECADEXAMIN, BETNESOL, BETNESOL FORTE, BETNESOL N, BETNOVATE, BETNOVATE C, BETNOVATE GM, BETNOVATE N, BETNOVATE S, BIDURET, BIDURET-L, BOOSTRIX, BREVOXYL, CALPOL, CALPOL T, CARZEC, CCM, CEFSPAN, CEFTUM, CERVARIX, CERVARIX PRTC, CETZINE, CETZINE A, CLINDOXYL, COBADEX, COBADEX CZS, COBADEX FORTE, COBADEX Z, DAPSONE, DERMOCALM, DILOSYN, DITIDE, ELTROXIN, ESPAZINE, EUMOSONE, EUMOSONE M, FACEMASK, FEFOL, FEFOL Z, FESOVIT, FLIXONASE, FLIXOTIDE, FLUARIX, FLUARIX TETRA, FLUTIBACT, FLUTIVATE, FORTUM, GLACEX, GRISOVIN, GRISOVIN FP, HAVRIX, HYCAMTIN, ICTACETAM, INFANRIX CCT, INFANRIX HEXA, IODEX, IODEX RUB, LANOXIN, LONGCET, MENVEO, NEOSPORIN, NEOSPORIN-H, NEOTREXATE, NUCALA, NUCALA FD, OILATUM, OSTO, OSTOCALCIUM, PHEXIN, PHEXIN BD, PHYSIOGEL, PHYSIOGEL HYPOALLERGENIC, PHYSIOGEL HYPOALLERGENIC CRAI, PHYSIOGEL HYPOALLERGENIC DMT, PIRITON, PIRITON CS, PRIORIX, RELVAR, RELVAR ELLIPTA, ROSUTEC, ROTARIX, SARNA, SEPMAX DS, SEPTRAN, SERETIDE, SPECTRABAN, STIEPROX, SUPACEF, SYNFLORIX, T-BACT, TENOVATE, TENOVATE GN, TENOVATE M, TOPGRAF, TRELEGY ELLIPTA, URICOSTAT, VARILRIX, VIBELAN FORTE, VOTRIENT, VOZET, XGEVA, ZENTEL, ZEVIT, ZIMIG, ZIMIVIR, ZINETAC, ZODERM, ZODERM E, ZOVIRAX, ZOVIRAX FD, ZUPAR, ZYLORIC"
            },
            {
                "role": "user",
                "content": "Give me examples of Delivery methods."
            },
            {    
                "role": "assistant",
                "content": "Example Delivery Methods are BALM, BAR, BLISTER, BOTTLE, CAPSULE, CREAM, DROP, EAR DROPS, EMOLLIENT, EYE OINTMENT, EYE/EAR DROPS, FOC, GEL, IN, INF, INJ, INTRAVENOUS, LIQUID, LOTION, NASAL SPRAY, OIL, OINTMENT, ORAL DROPS, POWDER, SENSITIVE, SOLUTION, SPRAY, SUPPRES, SYRUP, TABLET, TABLET, TM, TP, ULTRAGEL, WFRAEROSOL, WFR, AI."
            },
            {
                "role": "user",
                "content": "Give me some examples of Product Strengths.",
            },
            {
                "role": "assistant",
                "content": "Example of Product Strengths are 0.03, 0.05, 0.1, 0.5, 1, 1.16, 1.2, 1.5, 10, 100, 1000, 120, 125, 15, 16, 1G, 2, 20, 200, 22, 25, 250, 3, 3.125, 30, 300, 325, 375, 4, 40, 400, 5, 50, 500, 50M, 6.25, 600, 625, 650, 720, 75, 750, 8, 80, 800, 88, CCT, FPS 30, PREFILLED, SPF300.03. The values can be in mg, milligram or other suffixes.",                
            },
            {
                "role": "user",
                "content": "Give me some examples of Sizes.",
            },
            {
                "role": "assistant",
                "content": "Example of Sizes are 1, 1.7, 10, 100, 1000, 10X10, 10X15, 10X3X15, 10X45, 10X7, 115, 120, 15, 15X10, 16, 1X120, 20, 200, 20X10, 20X100, 20X120, 20X15, 20X20, 20X30, 20X60, 20X600, 20X7, 21X10, 21X30, 25, 25X10, 25X15, 25X20, 30, 30X10, 30X15, 35, 3X5, 4, 40, 450, 45X15, 460, 5, 50, 5X10, 5X15, 5X4, 5X5, 60, 6X15, 6X30, 6X40, 7.5, 75, 750, 7X3, 8, 80, FOC, PACK, TPX1, VIAL1, 1.7, 10, 100, 1000, 10X10, 10X15, 10X3X15, 10X45, 10X7, 115, 120, 15, 15X10, 16, 1X120, 20, 200, 20X10, 20X100, 20X120, 20X15, 20X20, 20X30, 20X60, 20X600, 20X7, 21X10, 21X30, 25, 25X10, 25X15, 25X20, 30, 30X10, 30X15, 35, 3X5, 4, 40, 450, 45X15, 460, 5, 50, 5X10, 5X15, 5X4, 5X5, 60, 6X15, 6X30, 6X40, 7.5, 75, 750, 7X3, 8, 80, FOC, PACK, TPX1, VIAL",
            },
            {
                "role": "user",
                "content": "Give me some examples of packing or ordering units.",
            },
            {
                "role": "assistant",
                "content": "Example of Ordering units are BOT, BOTT, BOTTLE, BOTTLES, BOX, BOXES, BX, C/S, CASE, CASES, CS, DEVICE, DOSES, PC, PCS, SINGLE, STR, STRIP, STRIPS, TAB, TABLET, TUBES, UNIT, UNITS, VIAL, VIALS, NOS, AMP, 0.5ML, 04''S, 1, 1 TAB, 1 VIAL, 1 X 15S, 1.5GM, 110, 110GM, 115, 115GM, 10, 10 CAP, 10 GMS, 10 ML, 10 TAB, 10 TAB, 10''S, 100, 100''S, 1000, 1000TAB, 100ML, 100T, 100TAB, 100X1M, 10CAP, 10CAPS, 10G, 10GM, 10T, 10TAB, 10X10, 10X10G, 10X10T, 120, 120 NOS, 120 TAB, 120S, 120T, 120GM, 120MD, 120TAB, 15, 15 GM, 15 ML, 15 NOS, 15 TAB, 15', 15CAP, 15G, 15GM, 15GMS, 15ML, 15T, 15TAB, 1ML, 1PACK, 1VAIL, 1X120TAB, 1X15, 1X15G, 1X15G, 1X15GM, 1X15ML, 1X1TAB, 1X20, 1X25GM, 1X30G, 1X4, 1X40GM, 1X60ML, 20 GM, 20 TAB, 20S, 20''S, 20''S, 20GM, 20TAB, 20x120, 20x15', 20x30, 21x10', 25 GM, 25GM, 25x10, 25X10T, 25X60, 30, 30 CAP, 30 GM, 30 GMS, 30 MD, 30 ML, 30 MLS, 30 TAB, 30', 30''S, 30''S, 30g, 30GM, 30ML, 30TAB, 30X30ML, 3TAB, 3X100T, 4, 4 CAP, 4 TAB, 4''S, 4S, 40`, 40GM, 40TAB, 45X120, 48X10, 4TAB, 5, 5 bx, 5 GM, 5 ML, 5 STRIP, 5 TAB, 5'S, 50 GM, 50 ML, 50GM, 50gm, 50ML, 50ML, 50X60ML, 5AMP, AMP, 5GM, 5MG, 5ML, 5ml, 5S, 5x10, 5X10, 5X1ML, 5X4, 5X4TAB, 5x5', 60, 60 ML, 60''S, 60`S, 60BLIST, 60ML, 60S, 60TAB, 6x40, 7, 7 TAB, 7 TABS, 7.5GM, 7', 7's, 72x20', 7TAB, 7TABS, 8 S, 81ML, 81VIAL, 8X1ML.",
            },
            {
                "role": "user",
                "content": "Give me examples of sku configuration.",
            },
            {
                "role": "assistant",
                "content": "Examples of SKU Name configuration are following. In SKU Name BECADEXAMIN CAP, Product Name is BECADEXAMIN, Delivery Method is CAP. In SKU Name BETNESOL FORTE 1X1ML, Product Name is BETNESOL FORTE, Ordering unit is 1X1ML. In SKU Name ZIMIVIR-500 3.TAB, Product Name is ZIMIVIR, Delivery Method is TAB, Product Strength is 500, Size is 3.TAB. In SKU Name T-BACT-15GM OINTMENT, Product Name is T-BACT, Delivery Method is OINTMENT, Size is 15GM. In SKU Name AUGMENTIN 625 DUO TAB, Product Name is AUGMENTIN DUO, Delivery Method is TAB, Product Strength is 625.",
            },
            {
                "role": "user",
                "content": f"""From the following text which is extracted from a customer purchase order. Extract only distinct patterns of line item raw data. Distinct should be identified based on the way line item data is organized. /* Ordering units can be standard packing of items or any other units such as box or case pack.  When an ordering-unit is present, output it **exactly as written in the source (line-item), including capitalisation and punctuation**; do not expand, translate, or normalise it.   **Always use the ordering-unit that already appears in the line-item. Only if the ordering unit is not specified, derive it using the following table.**  Derive-Unit table (tablet or cap or capsule = STRIPS, syrup or cream or ointment = NOS, injection or  inj = VIALS) */ /* If the quantity is specified as numeric value1 + numeric value2 calculate quantity by adding both the values. In this case the 1st numeric value is the chargeable quantity and the 2nd value is the free quantity. When the free quantity is specified as a percentage, do not perform the calculation, just consider  the chargeable value as the quantity.*/ /* When there are two or more line items in one row, return a list of JSONs. Each JSON in the list should contain prefixed keys like first_product_name, second_product_name, etc., so that each product in the same row is uniquely identified. Prefix all fields for each item accordingly: first_, second_, third_, etc. and If two items in one row, add all json keys of both item in one json, so get each distinct line item json. */ For each distinct line item extract First raw data, First Line No, First Sku Name, First Packing (Ordering unit), First Order Quantity, First Free Quantity or Percentage(if specified), First From SKU Name also identify Product Name, First Delivery method (Tablet, Capsules, Injection, Powder, Syrup), First Product Strength, First Pack Size, Second raw data, Second Line No, Second Sku Name, Second Packing (Ordering unit), Second Order Quantity, Second Free Quantity or Percentage(if specified), Second From SKU Name also identify Product Name, Second Delivery method (Tablet, Capsules, Injection, Powder, Syrup), Second Product Strength, Second Pack Size Return only the data in json format with following tag name first_sample_id, first_raw_data, first_line_no, first_sku_name, first_ordering_unit, first_quantity, first_free_quantity, first_free_percent, first_product_name, first_strength, first_pack_size, first_delivery_method, second_sample_id, second_raw_data, second_line_no, second_sku_name, second_ordering_unit, second_quantity, second_free_quantity, second_free_percent, second_product_name, second_strength, second_pack_size, second_delivery_method. Every time line no is required. Process following data and build the line example
                    Text:
                    \"\"\"
                    {extracted_text}
                    \"\"\"
                """
            }]

            logger.log(f'-------------------------------------------------------------------------------------')
            logger.log(f'Identify_line_example prompt for 2 line example: {message}')
            logger.log(f'-------------------------------------------------------------------------------------')

            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                            model='gpt-4.1',
                            messages=message,
                            temperature=0
                        )
            result =  completion.choices[0].message.content
            # reply = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))
            match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            data = {}
            if match:
                json_str = match.group(1).strip()
                json_str = json_str.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","").replace("'","").replace("`","")
                data = json.loads(json_str)
            return data        
        except Exception as error:
            raise str(error)  

    def get_main_page_line(self, json_data):
        try:
            if 'ai_proc_variables' in json_data:
                ai_proc_vars_str = json_data['ai_proc_variables']
                try:
                    ai_proc_vars = json.loads(ai_proc_vars_str)  # convert to dict
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in 'ai_proc_variables': {e}")

                if 'Details' in ai_proc_vars:
                    for i in ai_proc_vars['Details']:
                        if 'displayName' in i and i['displayName'] == 'Main Page':
                            return i['defaultValue']
            return None        
        except Exception as error:
            raise str(error)  
    
    def get_Split_Text(self, main_page_line, phrase):
        try:
            sentences = re.split(r'(?<=[.])\s+', main_page_line)

            target_sentence = ""
            for sentence in sentences:
                if phrase in sentence:
                    target_sentence = sentence.strip()
                    break

            if target_sentence:
                part1 = main_page_line.split(target_sentence)[0].strip()
                part2 = target_sentence
                part3 = main_page_line.split(target_sentence)[1].strip()
            else:
                part1 = main_page_line
                part2 = ""
                part3 = ""

            return part1, part2, part3        
        except Exception as error:
            raise str(error)  

    def generate_main_page_instruction(self, ocr_data, open_ai_key, json_data):
        try:
            doc_type = ""
            main_page_line = ""
            result_dict = {}

            model_name = "AIT"
            # main_page_line = self.get_main_page_line(json_data)

            if 'doc_type' in json_data.keys():
                doc_type = json_data['doc_type']
            logger.log(f"\ngenerate_main_page_instruction doc_type ::: {doc_type}")

            if doc_type == "Orders":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""    
            elif doc_type == "Order Excel":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""
            elif doc_type == "Order Email":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""
            elif doc_type == "Order Handwritten":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""             

            logger.log(f"\nmain_page_line ::: {main_page_line}")
            if ocr_data:
                res = self.identify_complexity_layout_structure(ocr_data, open_ai_key)
                logger.log(f"\ncomplexity_layout_structure ::: {res}")

                if 'complexity_perc' in res:
                    if res['complexity_perc'] > 80:
                        model_name = "AIT4O" 
                logger.log(f"\nmodel_name ::: {model_name}")

                if 'division_grouping' in res and 'division_list' in res:
                    if res['division_grouping'] == True and len(res['division_list']) > 0:
                        logger.log(f"Inside 1st condition.....")
                        division_names = ', '.join(res.get('division_list', []))
                        phrase = "SKU are grouped"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} SKUs are grouped by Division and at the end of Division there is a line showing total of Division, Division Names are {division_names}. {end_part}"
                    elif res['is_division_summary'] == False:
                        logger.log(f"Inside 2nd condition.....")
                        phrase = "SKU are grouped"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} SKU are grouped by Division, Division Names are GSK-DERMA ACE, GSK-FORTIOR, GLAXO INGINIUM. {end_part}"

                if 'free_quantity_column' in res:
                    if res['free_quantity_column'] == True:
                        logger.log(f"Inside 3rd condition... Add line for free quantity...")
                        phrase = "Line items are in"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} {middle_part} FREE can be a fixed value or percentage. {end_part.replace('Quantity', 'Quantity, FREE')}"

                if 'unstructured_email' in res:
                    if res['unstructured_email'] == True:
                        logger.log(f"Inside 4th condition... Unstructured Email...")
                        main_page_line = f"/* Following is data of email received from a customer of Glaxo, which needs to be extracted and converted to structured format. GLAXO is the seller of this document, not the purchaser. It has a header and multiple line items. Quantity is always specified against each line item, whereas Strength and Size can be optional. SKU can be grouped by Division which is to be ignored. */    /* Ordering units can be  standard packing of items or any other units such as box or case pack.  When an ordering-unit is present, output it **exactly as written in the source (line-item), including capitalisation and punctuation**; do not expand, translate, or normalise it.   **Always use the ordering-unit that already appears in the line-item. Only if the ordering unit is not specified, derive it using the following table.**  Derive-Unit table (tablet or cap or capsule = STRIPS, syrup or cream or ointment = NOS, injection or  inj = VIALS) */  /* If the quantity is specified as numeric value1 + numeric value2 calculate quantity by adding both the values. In this case the 1st numeric value is the chargeable quantity and the 2nd value is the free quantity. When the free quantity is specified as a percentage, do not perform the calculation, just consider  the chargeable value as the quantity.*/  <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Whereas for each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"

                logger.log(f"\nmain_page_line ::: {main_page_line}")

                result_dict = {
                    "default_value" : main_page_line,
                    "modelname" : model_name
                }

            return result_dict      
        except Exception as error:
            raise str(error)  

    def generate_line_example(self, ocr_data, open_ai_key):
        try:
            final_line_example = ""

            res = self.identify_complexity_layout_structure(ocr_data, open_ai_key)
            logger.log(f"\ngenerate_line_example complexity_layout_structure ::: {res}")

            if res.get('unstructured_email','') == True:
                final_line_example = ""
            elif str(res.get('no_datasets_in_row','')) == '2':                     
                line_example_two_column_json_data = self.identify_line_example_two_column(ocr_data, open_ai_key)
                logger.log(f"\n generate_line_example line_example_two_column_json_data length ::{len(line_example_two_column_json_data)}")
                logger.log(f"\n generate_line_example line_example_two_column_json_data ::{line_example_two_column_json_data}")

                line_examples = []
                for item in line_example_two_column_json_data:
                    # Extract first line item fields
                    first_line_no = item.get('first_line_no', '')
                    first_sku_name = '' if item.get('first_sku_name') in [None, "None"] else item.get('first_sku_name').replace('"', '')
                    first_pack_size = '' if item.get('first_pack_size') in [None, "None"] else item.get('first_pack_size').replace('"', '')
                    first_quantity = '' if item.get('first_quantity') in [None, "None"] else item.get('first_quantity').replace('"', '')
                    first_ordering_unit = '' if item.get('first_ordering_unit') in [None, "None"] else item.get('first_ordering_unit').replace('"', '')
                    first_product_name = '' if item.get('first_product_name') in [None, "None"] else item.get('first_product_name').replace('"', '')
                    first_delivery_method = '' if item.get('first_delivery_method') in [None, "None"] else item.get('first_delivery_method').replace('"', '')
                    first_strength = '' if item.get('first_strength') in [None, "None"] else item.get('first_strength').replace('"', '')

                    # Clean quantity
                    first_quantity = str(first_quantity).replace(",", "") if first_quantity else ""

                    # Create a compact line item example string
                    first_parts = [
                        first_line_no if first_line_no else "",
                        first_sku_name if first_sku_name else "",
                        first_pack_size if first_pack_size else "",
                        first_quantity if first_quantity else "",
                        first_ordering_unit if first_ordering_unit else ""
                    ]
                    # first_sentence = ", ".join(filter(None, first_parts)) + "."
                    first_sentence = ", ".join(str(part) for part in first_parts if part) + "."
                    first_sentence = f"In Line Item {first_sentence}"

                    # First line explanation
                    first_explanation_parts = []
                    if first_quantity:
                        first_explanation_parts.append(f"First order item Quantity is {first_quantity}")
                    if first_ordering_unit or first_pack_size:
                        unit = first_ordering_unit if first_ordering_unit else first_pack_size
                        first_explanation_parts.append(f"First Order item Unit is {unit}")
                    if first_sku_name:
                        first_explanation_parts.append(f"First Order item SKU Name is {first_sku_name}")
                    if first_product_name:
                        first_explanation_parts.append(f"First Product Name is {first_product_name}")
                    if first_delivery_method:
                        first_explanation_parts.append(f"First Delivery Method is {first_delivery_method}")
                    if first_strength:
                        first_explanation_parts.append(f"First Order Item Product Strength is {first_strength}")

                    first_explanation = ", ".join(first_explanation_parts) + ". "
                    line_examples.append(f"{first_sentence} {first_explanation}")

                    # Extract second line item fields
                    second_line_no = item.get('second_line_no', '')
                    second_sku_name = '' if item.get('second_sku_name') in [None, "None"] else item.get('second_sku_name').replace('"', '')
                    second_pack_size = '' if item.get('second_pack_size') in [None, "None"] else item.get('second_pack_size').replace('"', '')
                    second_quantity = '' if item.get('second_quantity') in [None, "None"] else item.get('second_quantity').replace('"', '')
                    second_ordering_unit = '' if item.get('second_ordering_unit') in [None, "None"] else item.get('second_ordering_unit').replace('"', '')
                    second_product_name = '' if item.get('second_product_name') in [None, "None"] else item.get('second_product_name').replace('"', '')
                    second_delivery_method = '' if item.get('second_delivery_method') in [None, "None"] else item.get('second_delivery_method').replace('"', '')
                    second_strength = '' if item.get('second_strength') in [None, "None"] else item.get('second_strength').replace('"', '')

                    # Clean quantity
                    second_quantity = str(second_quantity).replace(",", "") if second_quantity else ""

                    # Create a compact line item example string
                    second_parts = [
                        second_line_no if second_line_no else "",
                        second_sku_name if second_sku_name else "",
                        second_pack_size if second_pack_size else "",
                        second_quantity if second_quantity else "",
                        second_ordering_unit if second_ordering_unit else ""
                    ]

                    logger.log(f"second_parts list ::: {second_parts}")
                    logger.log(f"second_parts result ::: {all(not x for x in second_parts)}")
                    if all(not x for x in second_parts) == False:
                        second_sentence = ", ".join(str(part) for part in second_parts if part) + "."
                        second_sentence = f"In Line Item {second_sentence}"

                        # Second line explanation
                        second_explanation_parts = []
                        if second_quantity:
                            second_explanation_parts.append(f"Second order item Quantity is {second_quantity}")
                        if second_ordering_unit or second_pack_size:
                            unit = second_ordering_unit if second_ordering_unit else second_pack_size
                            second_explanation_parts.append(f"Second Order item Unit is {unit}")
                        if second_sku_name:
                            second_explanation_parts.append(f"Second Order item SKU Name is {second_sku_name}")
                        if second_product_name:
                            second_explanation_parts.append(f"Second Product Name is {second_product_name}")
                        if second_delivery_method:
                            second_explanation_parts.append(f"Second Delivery Method is {second_delivery_method}")
                        if second_strength:
                            second_explanation_parts.append(f"Second Order Item Product Strength is {second_strength}")

                        second_explanation = ", ".join(second_explanation_parts) + "."
                        line_examples.append(f"{second_sentence} {second_explanation}")

                final_line_example = "Example of Line Item organisation are as following. " + " ".join(line_examples)

            else:                    
                line_example_json_data = self.identify_line_example(ocr_data, open_ai_key)
                logger.log(f"\ngenerate_line_example line_example_json_data length ::{len(line_example_json_data)}")

                line_examples = []
                for item in line_example_json_data:
                    line_no = item.get('line_no', '')
                    sku_name = '' if item.get('sku_name') in [None, "None"] else item.get('sku_name').replace('"', '')
                    pack_size = '' if item.get('pack_size') in [None, "None"] else item.get('pack_size').replace('"', '')
                    quantity = '' if item.get('quantity') in [None, "None"] else item.get('quantity').replace('"', '')
                    ordering_unit = '' if item.get('ordering_unit') in [None, "None"] else item.get('ordering_unit').replace('"', '')
                    product_name = '' if item.get('product_name') in [None, "None"] else item.get('product_name').replace('"', '')
                    delivery_method = '' if item.get('delivery_method') in [None, "None"] else item.get('delivery_method').replace('"', '')
                    strength = '' if item.get('strength') in [None, "None"] else item.get('strength').replace('"', '')

                    quantity = str(quantity).replace(",","") if quantity else None

                    first_parts = [
                        line_no if line_no else "",
                        sku_name if sku_name else "",
                        pack_size if pack_size else "",
                        quantity if quantity else "",
                        ordering_unit if ordering_unit else ""
                    ]
                    # first_sentence = ", ".join(filter(None, first_parts)) + "."
                    first_sentence = ", ".join(str(part) for part in first_parts if part) + "."
                    first_sentence = f"In Line Item {first_sentence}"
                    logger.log(f"\ngenerate_line_example first_sentence ::{first_sentence}")

                    kv_map = {
                        "Line Number": line_no,
                        "SKU Name": sku_name,
                        "Ordering Unit": ordering_unit,
                        "Quantity": quantity,
                        "Product Name": product_name,
                        "Delivery Method": delivery_method,
                        "Product Strength": strength
                    }

                    second_sentence = ", ".join(
                        [f"{key} is {value}" for key, value in kv_map.items() if value not in [None, ""]]
                    ) + "."

                    line_examples.append(f"{first_sentence} {second_sentence}")

                final_line_example = "Example of Line Item organisation are as following. " + " ".join(line_examples)

            logger.log(f"\nfinal_line_example ::: {final_line_example}")
            result_dict = {
                "default_value" : final_line_example,
            }

            return result_dict        
        except Exception as error:
            raise str(error)  