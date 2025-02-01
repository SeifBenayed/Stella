import os
import subprocess
from bson import ObjectId
from persona.get_persona import persona

from langchain_core.tools import tool
from langchain.schema import HumanMessage
from utils.crawl_website import WebCrawler
from utils.parser import GetLink
from utils.common_utils import beautify, anthropic_payload_gen_text_only
from utils.scratchpad_beautifier import ScratchpadBeautify
from vision.payload_gen import CreateVisionPayload

from prompts.code_generation import code_generation_prompt
from prompts.prompt_injection import PromptInjection

from handlers.handle_long_context import EnhancedLongContextHandler
from llms.llm import LLM, azure_supported_models, anthropic_supported_models
import cv2
import numpy as np
from handlers.HeatmapGenerator import HeatmapGenerator

# Initialize tools with persona context
prompt = PromptInjection(persona(ObjectId(os.getenv("persona"))))

# Beautifier
beau = ScratchpadBeautify(prompt)


#session_manager = SessionManager(mongodb_url=os.getenv("llm_id"), db_name="hedi_db")

# Create new session

# Initialize context handler with session
lch = EnhancedLongContextHandler(
    tmp_folder="./tmp",
    prompt=prompt,
    beau=beau)


# Initialize handlers
lch = EnhancedLongContextHandler(os.getenv("tmp_folder"), prompt, beau)


@tool
def crawl(link: str) -> str:
    """Crawl website and prepare for persona-specific analysis"""
    llm_id = os.getenv("llm_id")
    if os.getenv("crawl_mode") != "initial":
        wc = WebCrawler(llm_id)
        wc.browse(link)
    else:
        os.environ["crawl_mode"] = "tool_mode"
    lch.append_to_agent_scratchpad(f"Analyzing {link} for {prompt.persona['name']}\n", "crawl")
    return f"\nCrawling completed\n of {link} \n"


@tool
def query_site_visually(query: str) -> str:
    """Analyze visual elements from persona perspective"""
    system_instructions = "you are an expert in generating UAT test cases"
    llm_id = os.getenv("llm_id")
    cvp = CreateVisionPayload(lch, system_instructions, prompt.visual_prompt, lch.screenshot_path)
    messages = cvp.get_message()
    llm = LLM(llm_id).get_llm()
    result = llm.invoke(messages)
    lch.append_to_agent_scratchpad(result.content, "query_text_visually")
    return f"Visual analysis completed with persona context for query: {query}"


@tool
def query_site_textually(query: str) -> dict:
    """get command to generate textual information parser
    describe the downloaded and saved html and output should create UAT test cases from the text along with
    website info"""
    try:
        lch.lg_invoke()
        return f"Textual analysis completed successfully with query: {query}"

    except Exception as e:
        error_msg = f"Error in textual analysis: {str(e)}"
        # todo
        # log error message seperately not in scratchpad
        return f"Error during textual analysis: {str(e)}"


@tool
def analyze_heatmap(query: str) -> str:
    """Generate and analyze heatmap based on persona preferences and previous analyses"""
    try:
        if not os.path.exists(lch.screenshot_path):
            return "Error: Please run crawl and visual analysis first."

        # Génération de la heatmap
        heatmap_gen = HeatmapGenerator(prompt.persona, lch)
        heatmap = heatmap_gen.generate(lch.screenshot_path)

        # Lecture de l'image originale
        original = cv2.imread(lch.screenshot_path)

        # Redimensionnement de la heatmap à la taille de l'image originale
        heatmap_resized = cv2.resize(heatmap, (original.shape[1], original.shape[0]))

        # Conversion en uint8 et application de la colormap
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Fusion avec l'image originale
        output = cv2.addWeighted(original, 0.7, heatmap_colored, 0.3, 0)

        # Sauvegarde de la heatmap
        heatmap_path = lch.screenshot_path.replace('.png', '_heatmap.png')
        cv2.imwrite(heatmap_path, output)

        # Analyse avec le LLM
        base64_heatmap = lch.encode_image(heatmap_path)
        llm = LLM(os.getenv("llm_id")).get_llm()

        analysis_prompt = f"""
        Analyze this heatmap for {prompt.persona['name']}, focusing on:
        1. Attention patterns matching their needs: {', '.join(prompt.persona['nmb']['needs'])}
        2. Mobile usability: {prompt.persona['ux']['navigation']['mobilePriority']}
        3. Visual hierarchy for their {prompt.persona['ux']['visualStyle']['designStyle']} design preference
        4. Potential barriers: {', '.join(prompt.persona['nmb']['barriers'])}

        Consider previous visual and textual analyses to provide comprehensive insights.
        """

        # Préparation des messages selon le type de modèle
        if os.getenv("llm_id") in azure_supported_models:
            messages = [
                {"role": "system", "content": "You are a UX analysis expert"},
                {"role": "user", "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_heatmap}"}}
                ]}
            ]
        else:  # anthropic_supported_models
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_heatmap}"}}
                    ]
                )
            ]

        result = llm.invoke(messages)

        # Sauvegarde des résultats
        lch.append_to_agent_scratchpad(
            f"Heatmap Analysis for {prompt.persona['name']}:\n{result.content}",
            "analyze_heatmap"
        )

        return f"Heatmap analysis completed and saved. Heatmap path: {heatmap_path}"

    except Exception as e:
        error_msg = f"Error in heatmap analysis: {str(e)}"
        lch.append_to_agent_scratchpad(error_msg, "analyze_heatmap")
        return error_msg




@tool
def generate_python_code(query: str) -> str:
    """Generate persona-specific test cases"""
    text = lch.read_from_agent_scratchpad()
    payload = prompt.code_prompt + code_generation_prompt + text

    llm_id = os.getenv("llm_id")
    llm = LLM(llm_id).get_llm()

    if llm_id in azure_supported_models:
        output = llm.invoke(payload)
    elif llm_id in anthropic_supported_models:
        messages = anthropic_payload_gen_text_only(payload)
        output = llm.invoke(messages)

    processed_code = beautify(output.content)
    final_code = processed_code
    lch.append_file(lch.python_file_path, final_code)
    lch.append_to_agent_scratchpad(final_code, "generate_python_code")
    return f"Generated persona-specific test code: for the query:  {query}"


@tool
def run_python_code(text: str):
    """Execute tests with persona-specific configurations"""
    result = subprocess.run(['python', lch.python_file_path], capture_output=True, text=True)
    test_summary = beau.beautify_python_code_run_results(result)
    lch.read_logs_append_to_agent_scratchpad()
    lch.append_to_agent_scratchpad(test_summary, "run_python_code")
    return "Persona-specific tests executed successfully"


@tool
def generate_feedback(query: str)-> str:
    """ read from the observations and create the feedback template"""
    scratch_pad = lch.read_from_agent_scratchpad()
    llm_id = os.getenv("llm_id")
    llm = LLM(llm_id).get_llm()
    payload = "generate template from the summary based on the defined template structure \n" + scratch_pad
    if llm_id in azure_supported_models:
        content = llm.invoke(payload).content
    elif llm_id in anthropic_supported_models:
        messages = anthropic_payload_gen_text_only(payload)
        content = llm.invoke(messages).content
    lch.append_file(lch.feed_back_file_path, content)
    lch.append_file(lch.feed_back_file_path, "-----------------------")
    return f"feedback generated successfully-> for {query}"

@tool
def check_for_feedback_reliability(query: str) -> str:
    """ check for generated feedback reliability"""
    llm_id = "sonnet-3-5"
    llm = LLM(llm_id).get_llm()
    feedback = lch.read_file(lch.feed_back_file_path)
    scratch_pad = lch.read_file(lch.agent_scratchpad_path)
    answer = llm.invoke(f"check if the feedback: {feedback}  is good enough from the following "
               f"observations {scratch_pad} do not hallucinate")
    return answer

@tool
def get_links(text: str) -> str:
    """Analyze links with persona context"""
    llm = LLM(os.getenv("llm_id")).get_llm()
    structured_llm = llm.with_structured_output(GetLink)
    enhanced_text = beau.beautify_extracted_links(text)
    return structured_llm.invoke(enhanced_text)