
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Dict, Union
from abc import ABC, abstractmethod

import logging
from yachalk import chalk
import os

import logging

# Disable logging by setting the highest log level (CRITICAL) globally
logging.disable(logging.CRITICAL)
logging.getLogger().addHandler(logging.NullHandler())


class GraphLogger:
    def __init__(self, name="Graph Logger", color="white"):
        # Set the log level (optional, can be DEBUG, INFO, WARNING, ERROR, CRITICAL)
        # log_level = os.environ.get("LOG_LEVEL", "WARNING").upper()

        log_level = logging.CRITICAL

        ## Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False  # Avoid duplicate logs from propagating to the root logger

        # Check if the logger already has handlers
        if not self.logger.hasHandlers():
            ## Formatter
            self.time_format = "%Y-%m-%d %H:%M:%S"
            format = self.format(color)
            self.formatter = logging.Formatter(fmt=format, datefmt=self.time_format)

            ## Handler
            handler = logging.StreamHandler()
            handler.setFormatter(self.formatter)
            handler.setLevel(log_level)  # Ensure the handler follows the same level as the logger

            # Add handler to logger
            self.logger.addHandler(handler)

    def getLogger(self):
        return self.logger

    def format(self, color: str):
        match color:
            case "black":
                format = chalk.black(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "red":
                format = chalk.red(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "green":
                format = chalk.green(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "yellow":
                format = chalk.yellow(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "blue":
                format = chalk.blue(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "magenta":
                format = chalk.magenta(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "cyan":
                format = chalk.cyan(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "white":
                format = chalk.white(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "black_bright":
                format = chalk.black_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "red_bright":
                format = chalk.red_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "green_bright":
                format = chalk.green_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "yellow_bright":
                format = chalk.yellow_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "blue_bright":
                format = chalk.blue_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "magenta_bright":
                format = chalk.magenta_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "cyan_bright":
                format = chalk.cyan_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "white_bright":
                format = chalk.white_bright(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )
            case "grey":
                format = chalk.grey(
                    "\n▶︎ %(name)s - %(asctime)s - %(levelname)s \n%(message)s\n"
                )

        return format

class LLMClient(ABC):
    @abstractmethod
    def __init__(self, model: str, temperature: float, top_p: float):
        pass

    @abstractmethod
    def generate(self, user_message: str, system_message: str) -> str:
        "Generate and return the first choice from chat completion as string"
        pass


# class Ontology(BaseModel):
#     labels: List[Union[str, Dict]]
#     relationships: List[str]
#     sentiment_analysis: bool = True

#     def dump(self):
#         if len(self.relationships) == 0:
#             return self.model_dump(exclude=["relationships"])
#         else:
#             return self.model_dump()


class Ontology(BaseModel):
    labels: List[Dict[str, str]]
    relationships: List[str]
    sentiment_analysis: bool = True
    system_message: str

class Node(BaseModel):
    label: str
    name: str


class Edge(BaseModel):
    node_1: Node
    node_2: Node
    relationship: str
    sentiment: float = 0.0
    metadata: dict = {}
    order: Union[int, None] = None


class Document(BaseModel):
    text: str
    metadata: dict


class OpenAIClient(LLMClient):
    _model: str
    _temperature: float
    _max_tokens: int
    _top_p: float

    def __init__(
        self, model: str = "gpt-4o-mini", temperature=0.2, top_p=1, max_tokens=2048
    ):
        self._model = model
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self.client = OpenAI(api_key=sov.tools.sec.llm_code_generator.get_openai_key())

    def generate(self, user_message: str, system_message: str) -> str:
        # print("Using Model: ", self._model)

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            top_p=self._top_p,
            stop=None,
        )

        return response.choices[0].message.content

class OpenAIClientBatch(LLMClient):
    def __init__(self, model: str = "gpt-3.5-turbo", temperature=0.2, top_p=1, max_tokens=2048):
        self._model = model
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self.client = OpenAI(api_key="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")

    def generate(self, user_messages: List[str], system_message: str) -> List[str]:
        # print("Using Model: ", self._model)

        messages = [
            {"role": "system", "content": system_message},
            *[{"role": "user", "content": msg} for msg in user_messages]
        ]

        response = self.client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            top_p=self._top_p,
            n=len(user_messages),  # Generate one response per user message
        )

        return [choice.message.content for choice in response.choices]

from pydantic import BaseModel
from typing import List, Dict, Union

ontology = ["connection", "causal", "temporal", "stakeholder", "innovation", "esg", "sentiment"]

ontology_dict = {
    "connection": Ontology(
        labels=[
            {"FinancialMetric": "Key financial indicators such as Revenue, Net Income, Gross Margin, Operating Expenses"},
            {"ProductService": "Product lines, service offerings, new releases"},
            {"GeographicSegment": "Geographic regions or market sectors"},
            {"RiskFactor": "Economic, competitive, regulatory, or technological risks"},
            {"StrategicInitiative": "Corporate strategies, acquisitions, partnerships"},
            {"MacroeconomicFactor": "Currency fluctuations, interest rates, inflation"},
            {"Organization": "Company names, subsidiaries, competitors"},
            {"Event": "Significant events affecting the company"},
            {"RegulatoryMatter": "Legal issues, compliance measures, regulatory changes"},
            {"BusinessSegment": "Divisions or segments of the company representing different business lines or products"},
            {"CorporateStructure": "Organizational structure including parent company, subsidiaries, divisions, and joint ventures"},
            {"FinancialPerformance": "Overall performance metrics such as Revenue, Net Income, EBITDA, Gross Margin, Operating Expenses, Cash Flow, and ROE"},
            {"FutureOutlook": "Forecasts, expectations, and forward-looking statements about growth, risks, and opportunities"},
            {"OperationalInfrastructure": "Key assets, supply chains, logistics, manufacturing plants, and operational capabilities"},
            {"MarketCondition": "Market trends, competition dynamics, and overall demand and supply conditions"},
            {"OperationalMetric": "Metrics such as inventory levels, production efficiency, customer retention, and staffing levels"},
            {"RevenueStream": "Sources of revenue, recurring and non-recurring income from products, services, or other business activities"}
        ],
        relationships=["Connection describing how one entity affects, influences, or interacts with another entity"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on general connections:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and their connections from the user-provided text as per the given ontology, focusing on relationships relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple connections between the same pair of nodes.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to financial metrics, market trends, risk factors, and strategic initiatives that investors would find important.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "Connection between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

    "causal": Ontology(
        labels=[
            {"BusinessSegment": "Divisions or segments of the company representing different business lines or products"},
            {"CorporateStructure": "Organizational structure including parent company, subsidiaries, divisions, and joint ventures"},
            {"FinancialPerformance": "Overall performance metrics such as Revenue, Net Income, EBITDA, Gross Margin, Operating Expenses, Cash Flow, and ROE"},
            {"FutureOutlook": "Forecasts, expectations, and forward-looking statements about growth, risks, and opportunities"},
            {"OperationalInfrastructure": "Key assets, supply chains, logistics, manufacturing plants, and operational capabilities"},
            {"ProductService": "Product lines, service offerings, R&D efforts, patents, intellectual property, and market share"},
            {"GeographicSegment": "Regions, countries, or territories contributing to growth or losses"},
            {"RiskFactor": "Economic, competitive, regulatory, or technological risks affecting the business"},
            {"StrategicInitiative": "Corporate strategies like mergers, acquisitions, divestitures, partnerships, restructuring, and innovation initiatives"},
            {"MacroeconomicFactor": "Broader economic factors such as inflation, currency fluctuations, interest rates, supply chain disruptions, GDP changes, or unemployment rates"},
            {"Organization": "Companies, subsidiaries, competitors, stakeholders, joint ventures, and regulatory bodies"},
            {"Event": "Significant events such as lawsuits, regulatory filings, product recalls, executive turnover, financial restatements, or new regulations"},
            {"RegulatoryMatter": "Legal issues, compliance challenges, tax policy changes, and new regulations"},
            {"MarketCondition": "Market trends, competition dynamics, and overall demand and supply conditions"},
            {"OperationalMetric": "Metrics such as inventory levels, production efficiency, customer retention, and staffing levels"},
            {"RevenueStream": "Sources of revenue, recurring and non-recurring income from products, services, or other business activities"}
        ],
        relationships=["Causal Relation between any pair of Entities"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on causal relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and causal relationships from the user-provided text as per the given ontology, focusing on cause-and-effect connections relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple direct (explicit) or implied causal relationships between the same pair of nodes.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to financial metrics, market trends, risk factors, and strategic initiatives that investors would find important.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "Causal relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

    "temporal": Ontology(
        labels=[
            {"ImmediateImpact": "Effects visible within days or weeks"},
            {"ShortTermTrend": "Patterns over 1-6 months"},
            {"MediumTermCycle": "Cycles spanning 6-24 months"},
            {"LongTermShift": "Fundamental changes over 2-5 years"},
            {"HistoricalPattern": "Recurring patterns based on past data"},
            {"FuturePrediction": "Forecasted events or trends"},
            {"QuarterlyResult": "Financial performance and key metrics for a 3-month period"},
            {"AnnualPerformance": "Yearly financial results and business achievements"},
            {"SeasonalVariation": "Recurring patterns tied to specific times of the year"},
            {"ProductLifecycle": "Stages of a product from introduction to obsolescence"},
            {"StrategicHorizon": "Time frame for implementing major business strategies"},
            {"RegulatoryTimeline": "Schedules for compliance with new laws or regulations"},
            {"MarketCycle": "Periods of growth, stability, and decline in the broader market"},
            {"TechnologyAdoption": "Timeline for integrating new technologies into the business"},
            {"InvestmentHorizon": "Time frame for expected returns on major investments"},
            {"OperationalCadence": "Regular cycles of business operations and reporting"}
        ],
        relationships=["Temporal relation describing how one entity precedes, follows, coincides with, or relates in time to another entity"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on temporal relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and temporal relationships from the user-provided text as per the given ontology, focusing on time-based connections relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple direct (explicit) or implied temporal relationships between the same pair of nodes.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to financial metrics, market trends, risk factors, and strategic initiatives that investors would find important.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "Temporal relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

    "stakeholder": Ontology(
        labels=[
            {"Shareholder": "Individual and institutional investors"},
            {"Employee": "Workforce, including executives and labor unions"},
            {"Customer": "End-users and clients"},
            {"Supplier": "Providers of raw materials or services"},
            {"Regulator": "Government bodies and regulatory agencies"},
            {"Competitor": "Direct and indirect market rivals"},
            {"Community": "Local populations affected by company operations"},
            {"MediaAnalyst": "Journalists and financial analysts"},
            {"BoardOfDirectors": "Governing body responsible for major company decisions"},
            {"ExecutiveTeam": "C-suite and other top-level management"},
            {"IndustryAssociation": "Organizations representing the interests of specific sectors"},
            {"StrategicPartner": "Companies with mutual business interests or collaborations"},
            {"Creditor": "Banks, bondholders, and other lenders"},
            {"EnvironmentalGroup": "Organizations focused on ecological impact"},
            {"LaborUnion": "Organizations representing worker interests"},
            {"TechnologyProvider": "Companies supplying critical tech infrastructure or services"}
        ],
        relationships=["Stakeholder relation describing how one entity influences, interacts with, or shapes the actions of another entity"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on stakeholder relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and stakeholder relationships from the user-provided text as per the given ontology, focusing on interactions between different stakeholders relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple relationships between the same pair of stakeholders.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to how different stakeholders influence financial metrics, market trends, risk factors, and strategic initiatives.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the stakeholder"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the stakeholder"}},
       "relationship": "Stakeholder relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

    "innovation": Ontology(
        labels=[
            {"EmergingTechnology": "New tech with potential to change the industry"},
            {"DisruptiveInnovation": "Innovations that create new markets"},
            {"IncumbentResponse": "Established companies' reactions to disruption"},
            {"PatentPortfolio": "Intellectual property assets"},
            {"R&DInitiative": "Research and development projects"},
            {"TechnologyAdoption": "Rate and extent of new tech integration"},
            {"InnovationEcosystem": "Partners, startups, and research institutions"},
            {"ProductInnovation": "New or improved product offerings"},
            {"ProcessInnovation": "Advancements in manufacturing or service delivery methods"},
            {"BusinessModelInnovation": "Novel approaches to value creation and capture"},
            {"OpenInnovation": "Collaborative innovation with external partners"},
            {"DigitalTransformation": "Integration of digital technology into all areas of business"},
            {"SustainableInnovation": "Innovations focused on environmental and social impact"},
            {"InnovationStrategy": "Company's approach to fostering and managing innovation"},
            {"MarketDisruption": "Changes in market dynamics due to innovative offerings"},
            {"TalentAcquisition": "Recruiting and retaining innovative personnel"}
        ],
        relationships=["Innovation relation describing how one entity disrupts, enhances, replaces, or otherwise impacts another entity in terms of technology and market dynamics"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on innovation relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and innovation relationships from the user-provided text as per the given ontology, focusing on technological and market dynamics relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple innovation relationships between the same pair of entities.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to how innovation affects financial metrics, market trends, risk factors, and strategic initiatives.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "Innovation relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

"esg": Ontology(
        labels=[
            {"EnvironmentalFootprint": "Carbon emissions, waste, resource use"},
            {"SocialResponsibility": "Labor practices, community engagement, diversity"},
            {"CorporateGovernance": "Board structure, executive compensation, ethics"},
            {"SustainableInitiative": "Projects aimed at improving ESG metrics"},
            {"ESGRating": "Third-party assessments of ESG performance"},
            {"StakeholderEngagement": "Interaction with various stakeholders on ESG issues"},
            {"ClimateRisk": "Potential impacts of climate change on business operations"},
            {"SupplyChainEthics": "Ethical considerations in procurement and supplier relations"},
            {"DiversityInclusion": "Efforts to promote workplace diversity and inclusivity"},
            {"DataPrivacySecurity": "Measures to protect customer and employee data"},
            {"ProductSafety": "Ensuring the safety and quality of products or services"},
            {"CommunityInvestment": "Initiatives to support local communities"},
            {"HumanRights": "Adherence to human rights principles in operations"},
            {"CircularEconomy": "Practices promoting resource efficiency and waste reduction"},
            {"ESGReporting": "Disclosure of ESG-related information to stakeholders"},
            {"SustainableFinance": "Integration of ESG factors in financial decisions and products"}
        ],
        relationships=["ESG relation describing how one entity impacts, aligns with, or influences the environmental, social, or governance aspects of another entity"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on ESG (Environmental, Social, and Governance) relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and ESG relationships from the user-provided text as per the given ontology, focusing on environmental, social, and governance aspects relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple ESG relationships between the same pair of entities.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to how ESG factors affect financial metrics, market trends, risk factors, and strategic initiatives.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "ESG relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    ),

    "sentiment": Ontology(
        labels=[
            {"InvestorSentiment": "Attitude of investors towards the company"},
            {"ConsumerPerception": "Public opinion about the company's products/services"},
            {"BrandReputation": "Overall image of the company in the market"},
            {"AnalystRating": "Professional analysts' views on the company"},
            {"SocialMediaBuzz": "Online discussions and trends related to the company"},
            {"MediaCoverage": "Tone and frequency of media reports"},
            {"EmployeeMorale": "Sentiment of the company's workforce"},
            {"MarketConfidence": "Overall market sentiment towards the company or industry"},
            {"StakeholderTrust": "Level of trust from various stakeholders"},
            {"RegulatorySentiment": "Attitude of regulatory bodies towards the company"},
            {"IndustryReputation": "Perception of the industry the company operates in"},
            {"CrisisSentiment": "Public reaction to company crises or controversies"},
            {"InnovationPerception": "Views on the company's innovative capabilities"},
            {"SustainabilityImage": "Perception of the company's environmental and social efforts"},
            {"CompetitivePositioning": "How the company is viewed relative to competitors"},
            {"LeadershipConfidence": "Trust in the company's leadership and management"}
        ],
        relationships=["Sentiment relation describing how one entity influences, shapes, or correlates with the perception or sentiment surrounding another entity"],
        sentiment_analysis=True,
        system_message="""
You are an expert at creating Knowledge Graphs, specializing in analyzing 10-K SEC filings for investors.
Consider the following ontology tailored for financial analysis with a focus on sentiment relationships:
{ontology_dump}
The user will provide you with an input text from various 10-K sections, delimited by ```.
Extract all the entities and sentiment relationships from the user-provided text as per the given ontology, focusing on perceptions and attitudes relevant to investors.
Do not use any previous knowledge about the company or context outside of what is provided in the text.
There can be multiple sentiment relationships between the same pair of entities.
Use ONLY the labels and relationships mentioned in the ontology.
Pay special attention to how sentiment affects financial metrics, market trends, risk factors, and strategic initiatives.
Also, analyze the sentiment of the relationship between the entities.
Provide a sentiment score between -1 (very negative) and 1 (very positive), with 0 being neutral.
Format your output as a json with the following schema:
[
   {{
       "node_1": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "node_2": {{"label": "as per the ontology", "name": "Name of the entity"}},
       "relationship": "Sentiment relationship between node_1 and node_2",
       "sentiment": Sentiment score between -1 and 1
   }},
]
Do not add any other comment before or after the json. Respond ONLY with a well formed json that can be directly read by a program.
"""
    )
}

from pydantic import ValidationError
import json
import re
from typing import List, Union
import time

green_logger = GraphLogger(name="GRAPH MAKER LOG", color="green_bright").getLogger()
json_parse_logger = GraphLogger(name="GRAPH MAKER ERROR", color="magenta").getLogger()
verbose_logger = GraphLogger(name="GRAPH MAKER VERBOSE", color="blue").getLogger()
red_logger = GraphLogger(name="GRAPH MAKER ERROR", color="red_bright").getLogger()
yellow_logger = GraphLogger(name="GRAPH MAKER WARNING", color="yellow_bright").getLogger()




import pandas as pd
import numpy as np
import uuid
import json
import re
from typing import List, Union
import time

# Disable the SettingWithCopyWarning
pd.options.mode.chained_assignment = None


class GraphMaker:
    _ontology: Ontology
    _llm_client: LLMClient
    _verbose: bool

    def __init__(
        self,
        ontology_type: str,
        llm_client: LLMClient = None,
        verbose: bool = False,
    ):
        self._ontology = ontology_dict[ontology_type]
        self._llm_client = llm_client
        self._verbose = verbose
        # green_logger.setLevel(logging.NOTSET)
        green_logger.setLevel(logging.CRITICAL)
        # if self._verbose:
        #     verbose_logger.setLevel("INFO")
        #     green_logger.setLevel("INFO")
        #     json_parse_logger.setLevel("INFO")
        #     red_logger.setLevel("INFO")
        #     yellow_logger.setLevel("INFO")
        # else:
        #     verbose_logger.setLevel(logging.NOTSET)
        #     green_logger.setLevel(logging.NOTSET)
        #     json_parse_logger.setLevel(logging.NOTSET)
        #     red_logger.setLevel(logging.NOTSET)
        #     yellow_logger.setLevel(logging.NOTSET)

    def user_message(self, text: str) -> str:
        return f"input text: ```\n{text}\n```"


    def system_message(self) -> str:
        ontology_dump = (
            f"Labels: {self._ontology.labels}\n"
            f"Relationships: {self._ontology.relationships}\n"
            f"Sentiment Analysis: {'Yes' if self._ontology.sentiment_analysis else 'No'}"
        )

        message = self._ontology.system_message.format(ontology_dump=ontology_dump)

        return message

    def generate(self, text: str) -> str:
        response = self._llm_client.generate(
            user_message=self.user_message(text),
            system_message=self.system_message(),
        )
        return response

    def parse_json(self, text: str):
        green_logger.info(f"JSON Parsing: \n{text}")
        try:
            parsed_json = json.loads(text)
            green_logger.info(f"JSON Parsing Successful!")
            return parsed_json
        except json.JSONDecodeError as e:
            json_parse_logger.info(f"JSON Parsing failed with error: {e.msg}")
            verbose_logger.info(f"FAULTY JSON: {text}")
            return None

    def manually_parse_json(self, text: str):
        green_logger.info(f"Trying Manual Parsing: \n{text}")
        pattern = r"\}\s*,\s*\{"
        stripped_text = text.strip("\n[{]}` ")
        splits = re.split(pattern, stripped_text, flags=re.MULTILINE | re.DOTALL)
        obj_string_list = list(map(lambda x: "{" + x + "}", splits))
        edge_list = []
        for string in obj_string_list:
            try:
                edge = json.loads(string)
                edge_list.append(edge)
            except json.JSONDecodeError as e:
                json_parse_logger.info(f"Failed to Parse the Edge: {string}\n{e.msg}")
                verbose_logger.info(f"FAULTY EDGE: {string}")
                continue
        green_logger.info(f"Manually extracted {len(edge_list)} Edges")
        return edge_list

    def from_text(self, text, chunk_id):
        response = self.generate(text)
        verbose_logger.info(f"LLM Response:\n{response}")

        json_data = self.parse_json(response)
        if not json_data:
            json_data = self.manually_parse_json(response)

        rows = []
        for edge in json_data:
            try:
                row = {
                    "node_1": edge["node_1"]["name"].lower(),
                    "node_1_label": edge["node_1"]["label"],
                    "node_2": edge["node_2"]["name"].lower(),
                    "node_2_label": edge["node_2"]["label"],
                    "edge": edge["relationship"],
                    "sentiment": edge.get("sentiment", 0) if self._ontology.sentiment_analysis else 0,
                    "chunk_id": chunk_id,
                    "count": 1  # Default weight
                }
                rows.append(row)
            except KeyError as e:
                verbose_logger.warning(f"Skipping edge due to missing key: {e}")
            except Exception as e:
                verbose_logger.warning(f"Skipping edge due to unexpected error: {e}")

        return rows



    def from_documents(
        self,
        docs: List[Document],
        delay_s_between=0,
    ) -> pd.DataFrame:
        all_rows = []
        for index, doc in enumerate(docs):
            green_logger.info(f"Document: {index+1}")
            chunk_id = doc.metadata.get("chunk_id", uuid.uuid4().hex)
            try:
                rows = self.from_text(doc.text, chunk_id)
                all_rows.extend(rows)
            except Exception as e:
                red_logger.error(f"Error processing document {index+1}: {str(e)}")
                red_logger.error(f"Skipping document and continuing...")
                continue

            if delay_s_between > 0:
                green_logger.info(
                    f"Waiting for {delay_s_between}s before the next request ... "
                )
                time.sleep(delay_s_between)

        if not all_rows:
            yellow_logger.warning("No rows were successfully processed.")
            return pd.DataFrame()

        df = pd.DataFrame(all_rows)
        df.replace("", np.nan, inplace=True)
        df.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
        return df

    def from_documents_batch(
        self,
        docs: List[Document],
        batch_size: int = 5,
        verbose: bool = False
    ) -> pd.DataFrame:
        all_rows = []
        total_batches = (len(docs) + batch_size - 1) // batch_size  # Calculate total number of batches

        for i in tqdm(range(0, len(docs), batch_size), total=total_batches, desc="Processing document batches"):
            batch = docs[i:i+batch_size]

            # Prepare batch of user messages
            user_messages = [self.user_message(doc.text) for doc in batch]

            # Generate responses for the batch
            responses = self._llm_client.generate(user_messages, self.system_message())

            for doc, response in zip(batch, responses):
                chunk_id = doc.metadata.get("chunk_id", uuid.uuid4().hex)
                json_data = self.parse_json(response)
                if not json_data:
                    json_data = self.manually_parse_json(response)

                for edge in json_data:
                    try:
                        row = {
                            "node_1": edge["node_1"]["name"].lower(),
                            "node_1_label": edge["node_1"]["label"],
                            "node_2": edge["node_2"]["name"].lower(),
                            "node_2_label": edge["node_2"]["label"],
                            "edge": edge["relationship"],
                            "sentiment": edge.get("sentiment", 0) if self._ontology.sentiment_analysis else 0,
                            "chunk_id": chunk_id,
                            "count": 1  # Default weight
                        }
                        all_rows.append(row)
                    except KeyError as e:
                        if verbose:
                            verbose_logger.warning(f"Skipping edge due to missing key: {e}")
                    except Exception as e:
                        if verbose:
                            verbose_logger.warning(f"Skipping edge due to unexpected error: {e}")

        df = pd.DataFrame(all_rows)
        df.replace("", np.nan, inplace=True)
        df.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
        return df

    # def from_documents_batch(
    #     self,
    #     docs: List[Document],
    #     batch_size: int = 5,
    # ) -> pd.DataFrame:
    #     all_rows = []
    #     for i in range(0, len(docs), batch_size):
    #         batch = docs[i:i+batch_size]

    #         # Prepare batch of user messages
    #         user_messages = [self.user_message(doc.text) for doc in batch]

    #         # Generate responses for the batch
    #         responses = self._llm_client.generate(user_messages, self.system_message())

    #         for doc, response in zip(batch, responses):
    #             chunk_id = doc.metadata.get("chunk_id", uuid.uuid4().hex)
    #             json_data = self.parse_json(response)
    #             if not json_data:
    #                 json_data = self.manually_parse_json(response)

    #             for edge in json_data:
    #                 try:
    #                     row = {
    #                         "node_1": edge["node_1"]["name"].lower(),
    #                         "node_1_label": edge["node_1"]["label"],
    #                         "node_2": edge["node_2"]["name"].lower(),
    #                         "node_2_label": edge["node_2"]["label"],
    #                         "edge": edge["relationship"],
    #                         "sentiment": edge.get("sentiment", 0) if self._ontology.sentiment_analysis else 0,
    #                         "chunk_id": chunk_id,
    #                         "count": 1  # Default weight
    #                     }
    #                     all_rows.append(row)
    #                 except KeyError as e:
    #                     verbose_logger.warning(f"Skipping edge due to missing key: {e}")
    #                 except Exception as e:
    #                     verbose_logger.warning(f"Skipping edge due to unexpected error: {e}")

    #     df = pd.DataFrame(all_rows)
    #     df.replace("", np.nan, inplace=True)
    #     df.dropna(subset=["node_1", "node_2", 'edge'], inplace=True)
    #     return df



def df2Graph(df: pd.DataFrame, graph_maker: GraphMaker, verbose: bool = False) -> pd.DataFrame:
    documents = [Document(text=row['text'], metadata={"chunk_id": row['chunk_id']}) for _, row in df.iterrows()]
    return graph_maker.from_documents(documents, verbose=verbose)

def df2GraphBatch(df: pd.DataFrame, graph_maker: GraphMaker, batch_size: int = 5, verbose: bool = False) -> pd.DataFrame:
    documents = [Document(text=row['text'], metadata={"chunk_id": row['chunk_id']}) for _, row in df.iterrows()]
    return graph_maker.from_documents_batch(documents, batch_size=batch_size, verbose=verbose)


import polars as pl
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_delta_table_data(table_path, table_full_read,  tickers=None):
    """
    Retrieve data from the Delta table using Polars, efficiently filtering by tickers if provided.

    :param table_path: Path to the Delta table
    :param tickers: List of tickers to filter by, or None to retrieve all data
    :return: Polars DataFrame containing the requested data
    """
    logger.info(f"Retrieving data from Delta table at {table_path}")

    if tickers:
        logger.info(f"Filtering data for tickers: {tickers}")
        # Use pyarrow_options to filter partitions
        df = pl.read_delta(
            table_path,
            pyarrow_options={"partitions": [("ticker", "in", tickers)]}
        )
    else:
        logger.info("Retrieving all data from the Delta table")
        df = pl.read_delta(table_full_read)

    logger.info(f"Retrieved {len(df)} rows of data")

    return df


import polars as pl
import numpy as np
from dateutil.parser import parse
from typing import Optional, List
import seaborn as sns
import random
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import os
import json
import traceback
import html


import sovai as sov
import pandas as pd
from dateutil.parser import parse
from typing import Optional
from datetime import timedelta

def process_10k_data(ticker: str, date: Optional[str] = None, section_select: bool = False):
    # Authenticate

    # If no date is provided, fetch the latest filing
    if not date:
        data = sov.data("sec/10k", tickers=[ticker], limit=1)
        if data.empty:
            print(f"No data found for ticker {ticker}")
            return None
        target_date = data['date'].max().date()
    else:
        try:
            target_date = parse(date).date()
        except ValueError:
            print(f"Invalid date format: {date}. Using the current date.")
            target_date = pd.Timestamp.now().date()

    # Set up a date range around the target date
    start_date = (target_date - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = (target_date + timedelta(days=365)).strftime('%Y-%m-%d')

    # Fetch data within the date range
    data = sov.data("sec/10k", tickers=[ticker], start_date=start_date, end_date=end_date)

    if data.empty:
        print(f"No data found for ticker {ticker} within one year of {target_date}")
        return None

    # Convert date column to datetime
    data['date'] = pd.to_datetime(data['date'])

    # Find the closest date
    closest_date = data.loc[(data['date'] - pd.Timestamp(target_date)).abs().idxmin(), 'date'].date()

    # Filter the data for the closest date
    selected_data = data[data['date'].dt.date == closest_date]

    print(f"Selected date: {closest_date}")
    print(f"Number of entries found: {len(selected_data)}")

    if 'index_url' in selected_data.columns:
        print(f"First 10-K URL: {selected_data['index_url'].iloc[0]}")
    else:
        print("URL information not available")

    # Section selection
    if section_select and 'section' in selected_data.columns:
        unique_sections = selected_data['section'].unique()
        print("\nAvailable sections:")
        for i, section in enumerate(unique_sections, 1):
            print(f"{i}. {section}")

        while True:
            selection = input("\nEnter the numbers of the sections you want to include (comma-separated), or press Enter to include all: ")
            if selection.strip() == "":
                print("Using all sections.")
                break
            try:
                selected_indices = [int(i.strip()) - 1 for i in selection.split(',')]
                selected_sections = [unique_sections[i] for i in selected_indices if 0 <= i < len(unique_sections)]
                if selected_sections:
                    selected_data = selected_data[selected_data['section'].isin(selected_sections)]
                    print(f"Selected sections: {', '.join(selected_sections)}")
                    break
                else:
                    print("Invalid selection. Please try again.")
            except ValueError:
                print("Invalid input. Please enter comma-separated numbers.")

    return selected_data



def smart_adaptive_text_grouping(df, target_rows=100):
    df = df.copy()

    # Calculate word count
    df['word_count'] = df['full_text'].apply(lambda x: len(str(x).split()) if pd.notnull(x) else 0)
    df['word_count'] = pd.to_numeric(df['word_count'], errors='coerce').fillna(0)

    # Calculate total words
    total_words = df['word_count'].sum()

    # Initialize target words per group
    target_words_per_group = total_words // target_rows

    while True:
        # Calculate cumulative word count within each group of ticker, date, and section
        df['cumulative_word_count'] = df.groupby(['ticker', 'date', 'section'])['word_count'].cumsum()

        # Create a group number that increments every time cumulative word count exceeds target_words_per_group
        df['group'] = (df['cumulative_word_count'] - 1) // target_words_per_group

        # Group by ticker, date, section, and the new group number
        grouped = df.groupby(['ticker', 'date', 'section', 'group'])

        # Aggregate the data
        result = grouped.agg({
            'full_text': ' '.join,
            'order': 'first',
            'category': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
            'tag': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
            'word_count': 'sum',
            'cik': 'first',
            'company': 'first',
            'accession_number': 'first',
            'row_id': 'first',
            'index_url': 'first'
        })

        # Check if we've reached or just gone under the target number of rows
        if len(result) <= target_rows:
            break

        # If we have too many rows, increase the target words per group
        target_words_per_group += 1

    # Reset the index to make grouped columns regular columns again
    result = result.reset_index()

    # Rename columns as needed
    result = result.rename(columns={
        'full_text': 'new_text',
        'order': 'new_order',
        'word_count': 'new_word_count'  # Rename to clarify it's the new count
    })

    # Select and reorder final columns
    final_columns = ['ticker', 'date', 'new_text', 'section', 'new_order', 'category', 'tag', 'new_word_count',
                     'cik', 'company', 'accession_number', 'row_id', 'index_url']
    final_result = result[final_columns]

    # Ensure new_order is continuous within each ticker, date, section group
    final_result['new_order'] = final_result.groupby(['ticker', 'date', 'section']).cumcount()

    return final_result



def contextual_proximity(df: pd.DataFrame) -> pd.DataFrame:
    # Melt the dataframe and retain the labels for nodes
    dfg_long = pd.melt(
        df, id_vars=["chunk_id", "node_1_label", "node_2_label"],
        value_vars=["node_1", "node_2"], value_name="node"
    )
    dfg_long.drop(columns=["variable"], inplace=True)

    # Merge on chunk_id to find proximity between nodes
    dfg_wide = pd.merge(dfg_long, dfg_long, on="chunk_id", suffixes=("_1", "_2"))

    # Remove self-loops (where node_1 == node_2)
    self_loops_drop = dfg_wide[dfg_wide["node_1"] == dfg_wide["node_2"]].index
    dfg2 = dfg_wide.drop(index=self_loops_drop).reset_index(drop=True)

    # Group by node pairs and retain node labels
    dfg2 = (
        dfg2.groupby(["node_1", "node_2", "node_1_label_1", "node_2_label_2"])
        .agg({"chunk_id": [",".join, "count"]})
        .reset_index()
    )
    dfg2.columns = ["node_1", "node_2", "node_1_label", "node_2_label", "chunk_id", "count"]

    # Ensure node labels are properly propagated
    dfg2.replace("", np.nan, inplace=True)
    dfg2.dropna(subset=["node_1", "node_2"], inplace=True)
    dfg2 = dfg2[dfg2["count"] != 1]

    # Add edge type and sentiment for contextual proximity
    dfg2["edge"] = "contextual proximity"
    dfg2["sentiment"] = 0  # Neutral sentiment for contextual proximity
    return dfg2



def create_graph_undirected(dfg):
    # Create an undirected graph
    G = nx.Graph()  # Undirected graph
    nodes = set(dfg['node_1']).union(set(dfg['node_2']))

    # Add nodes with their labels as node attributes
    for node in nodes:
        if len(dfg[dfg['node_1'] == node]) > 0:
            node_label = dfg[dfg['node_1'] == node]['node_1_label'].values[0]
        elif len(dfg[dfg['node_2'] == node]) > 0:
            node_label = dfg[dfg['node_2'] == node]['node_2_label'].values[0]
        else:
            node_label = ""

        # Add nodes to the graph with entity labels
        G.add_node(node, entity=node_label)

    # Add undirected edges with other attributes
    edges = [(str(row['node_1']), str(row['node_2']),
              {'title': row['edge'],
               'weight': row['count'],
               'sentiment': row['sentiment'],
               'node_1_label': row['node_1_label'],
               'node_2_label': row['node_2_label']})
             for _, row in dfg.iterrows()]

    G.add_edges_from(edges)  # Add edges without direction
    return G

def create_graph_directed(dfg):
    # Create a directed graph to show causality
    G = nx.DiGraph()  # Directed graph
    nodes = set(dfg['node_1']).union(set(dfg['node_2']))

    # Add nodes with their labels as node attributes
    for node in nodes:
        if len(dfg[dfg['node_1'] == node]) > 0:
            node_label = dfg[dfg['node_1'] == node]['node_1_label'].values[0]
        elif len(dfg[dfg['node_2'] == node]) > 0:
            node_label = dfg[dfg['node_2'] == node]['node_2_label'].values[0]
        else:
            node_label = ""

        # Add nodes to the graph with entity labels
        G.add_node(node, entity=node_label)

    # Add directed edges with other attributes
    edges = [(str(row['node_1']), str(row['node_2']),
              {'title': row['edge'],
               'weight': row['count'],
               'sentiment': row['sentiment'],
               'node_1_label': row['node_1_label'],
               'node_2_label': row['node_2_label']})
             for _, row in dfg.iterrows()]



    G.add_edges_from(edges)  # Add edges with direction
    return G


def detect_communities(G, algorithm='girvan_newman'):
    if algorithm == 'girvan_newman':
        communities_generator = nx.community.girvan_newman(G)
        top_level_communities = next(communities_generator)
        next_level_communities = next(communities_generator)
        communities = sorted(map(sorted, next_level_communities))
    else:
        # Implement other community detection algorithms here
        pass
    print(f"Number of Communities = {len(communities)}")
    return communities

def colors2Community(communities) -> pd.DataFrame:
    palette = "hls"
    p = sns.color_palette(palette, len(communities)).as_hex()
    random.shuffle(p)
    rows = []
    group = 0
    for community in communities:
        color = p.pop()
        group += 1
        for node in community:
            rows += [{"node": node, "color": color, "group": group}]
    df_colors = pd.DataFrame(rows)
    return df_colors

def add_node_attributes(G, colors_df):
    nx.set_node_attributes(G, pd.Series(colors_df.color.values, index=colors_df.node).to_dict(), 'color')
    nx.set_node_attributes(G, pd.Series(colors_df.group.values, index=colors_df.node).to_dict(), 'group')
    degrees = dict(G.degree())
    normalized_degrees = {node: (deg + 1) * 2 for node, deg in degrees.items()}  # Adjust multiplier as needed
    nx.set_node_attributes(G, normalized_degrees, 'size')



def create_pyvis_network(G, communities, output_path, graph_df, final_result):
    try:
        net = Network(notebook=False, cdn_resources="remote", height="900px", width="100%",
                      select_menu=True, filter_menu=True)

        community_sizes = [len(community) for community in communities]
        community_colors = sns.color_palette("husl", n_colors=len(communities)).as_hex()

        node_chunk_ids = {}
        max_chunks_per_node = 5  # Limit the number of chunks displayed per node

        # Preprocess chunk_id_to_text mapping
        chunk_id_to_text = final_result.set_index('chunk_id')['text'].to_dict()

        for node, node_attrs in G.nodes(data=True):
            chunk_ids = set()
            for ids in graph_df[(graph_df['node_1'] == node) | (graph_df['node_2'] == node)]['chunk_id']:
                chunk_ids.update([id.strip() for id in ids.split(',')])
            node_chunk_ids[node] = list(chunk_ids)

            # Prepare node text content
            node_text = []
            for chunk_id in list(chunk_ids)[:max_chunks_per_node]:
                if chunk_id in chunk_id_to_text:
                    node_text.append(f"<h4>Chunk ID: {html.escape(chunk_id)}</h4>")
                    node_text.append(f"<p>{html.escape(chunk_id_to_text[chunk_id])}</p>")
                else:
                    node_text.append(f"<p>No text available for chunk ID: {html.escape(chunk_id)}</p>")

            if len(chunk_ids) > max_chunks_per_node:
                node_text.append(f"<p>... and {len(chunk_ids) - max_chunks_per_node} more chunks</p>")

            node_text_content = "<br>".join(node_text)

            net.add_node(node,
                         title=f"Node: {node}<br>Group: {node_attrs['group']}<br>Degree: {G.degree[node]}",
                         label=node,
                         color=node_attrs['color'],
                         size=node_attrs['size'],
                         group=node_attrs['group'],
                         entity=node_attrs['entity'],
                         chunk_ids=list(chunk_ids),
                         text_content=node_text_content)

        for source, target, edge_attrs in G.edges(data=True):
            sentiment = edge_attrs.get('sentiment', 0)
            relationship = edge_attrs.get('title', 'Unspecified')
            entity_1 = edge_attrs.get('node_1_label')
            entity_2 = edge_attrs.get('node_2_label')

            if abs(sentiment) <= 0.1:
                sentiment_category = "Neutral"
                color = f"rgba(200,200,200,0.5)"
            elif sentiment > 0.1:
                sentiment_category = "Positive"
                intensity = min(1, sentiment)
                color = f"rgba(0,{int(255*intensity)},0,0.7)"
            else:
                sentiment_category = "Negative"
                intensity = min(1, abs(sentiment))
                color = f"rgba(255,{int(128*(1-intensity))},0,0.7)"

            # net.add_edge(source, target,
            #              title=f"{html.escape(relationship)}<br>Sentiment: {sentiment:.2f}",
            #              width=max(1, edge_attrs.get('weight', 1) / 2),
            #              color=color,
            #              smooth=True,
            #              sentiment=sentiment_category,
            #              relationship=relationship)

            net.add_edge(source, target,
                         title=f"Relationship: {html.escape(relationship)}<br>Sentiment: {sentiment:.2f}",
                         width=max(1, edge_attrs.get('weight', 1) / 2),
                         color=color,
                         smooth=True,
                         arrows="to",
                         sentiment=sentiment_category,
                         relationship=relationship,
                         entity_1=entity_1,
                         entity_2=entity_2)

        net.force_atlas_2based(central_gravity=0.015, gravity=-31)

        net.show(output_path, notebook=False)

        with open(output_path, 'r', encoding='utf-8') as file:
            content = file.read()

        community_html = "<div style='position:absolute;top:170px;left:10px;background-color:rgba(255,255,255,0.7);padding:10px;border-radius:5px;'>"
        community_html += "<h3>Communities</h3>"
        for i, (size, color) in enumerate(zip(community_sizes, community_colors)):
            community_html += f"<p style='margin:5px;'><span style='display:inline-block;width:20px;height:20px;background-color:{color};'></span> Community {i+1}: {size} nodes</p>"
        community_html += "</div>"

        stats_html = f"""
        <div id="graph-stats" style='position:absolute;top:170px;right:10px;background-color:rgba(255,255,255,0.7);padding:10px;border-radius:5px;'>
            <h3>Graph Statistics</h3>
            <p>Total Nodes: {G.number_of_nodes()}</p>
            <p>Total Edges: {G.number_of_edges()}</p>
            <p>Number of Communities: {len(communities)}</p>
            <p>Average Degree: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}</p>
        </div>
        """

        node_click_script = """
        <script>
        network.on("click", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var node = network.body.data.nodes.get(nodeId);
                var textContent = node.text_content || "No text available for this node.";
                document.getElementById("text-content").innerHTML = textContent;
                document.getElementById("text-display").style.display = "block";
            }
        });

        network.on("stabilizationIterationsDone", function() {
            network.setOptions({ physics: true });
            document.getElementById("loading").style.display = "none";
        });

        function togglePhysics() {
            var physics = !network.physics.options.enabled;
            network.setOptions({ physics: physics });
            document.getElementById("toggle-physics").innerText = physics ? "Disable Physics" : "Enable Physics";
        }

        // Enable physics automatically at start
        network.setOptions({ physics: true });
        </script>
        """

        physics_toggle = """
        <button id="toggle-physics" onclick="togglePhysics()" style="position:fixed;bottom:10px;right:10px;z-index:1000;">Disable Physics</button>
        """

        text_display_div = """
        <div id="text-display" style="position:fixed;top:170px;left:20px;bottom:100px;width:300px;max-height:calc(100% - 270px);overflow-y:auto;background-color:rgba(255,255,255,0.95);padding:20px;display:none;z-index:1000;box-shadow:0 0 10px rgba(0,0,0,0.5);">
        <button onclick="this.parentElement.style.display='none'" style="position:absolute;top:10px;right:10px;background:none;border:none;font-size:20px;cursor:pointer;">&times;</button>
        <div id="text-content" style="margin-top:40px;padding-bottom:40px;"></div>
        </div>
        """

        loading_div = """
        <div id="loading" style="position:fixed;top:0;left:0;width:100%;height:100%;background-color:rgba(255,255,255,0.8);display:flex;justify-content:center;align-items:center;z-index:2000;">
        <div style="text-align:center;">
            <h2>Loading Graph</h2>
            <p>This may take a few moments...</p>
        </div>
        </div>
        """

        content = content.replace('</body>', f'{community_html}{stats_html}{text_display_div}{node_click_script}{physics_toggle}{loading_div}</body>')

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Enhanced graph saved to {output_path}")
    except Exception as e:
        print(f"Error in create_pyvis_network: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())

# Main execution and the rest of the code remains the same

import hashlib
import json
from typing import Optional

from tqdm import tqdm

# Create a unique chunk_id by hashing the combination of 'ticker', 'date', 'section', and 'new_order'
def generate_chunk_id(row):
    unique_string = f"{row['ticker']}_{row['date']}_{row['section']}_{row['new_order']}"
    return hashlib.md5(unique_string.encode()).hexdigest()


def generate_sec_index_url(row):
    """
    Generate SEC index URL for a given row.
    """
    base_url = "https://www.sec.gov/Archives"
    cik = str(row['cik']).zfill(10)
    accession_number = row['accession_number'].replace('-', '')

    # Construct the URL for the index page
    index_url = f"{base_url}/edgar/data/{cik}/{accession_number}/{row['accession_number']}-index.htm"

    return index_url

import hashlib
import pandas as pd
import json
from typing import Optional
import os
import pickle
from functools import lru_cache

# Cache directory
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

@lru_cache(maxsize=None)
def get_cached_10k_data(ticker: str, date: str):
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{date}_10k_data.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return None

def cache_10k_data(ticker: str, date: str, data):
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{date}_10k_data.pkl")
    with open(cache_file, "wb") as f:
        pickle.dump(data, f)

@lru_cache(maxsize=None)
def get_cached_graph_data(ticker: str, date: str, ontology_type: str):
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{date}_{ontology_type}_graph_data.pkl")
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    return None

def cache_graph_data(ticker: str, date: str, ontology_type: str, data):
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{date}_{ontology_type}_graph_data.pkl")
    with open(cache_file, "wb") as f:
        pickle.dump(data, f)


def analyze_10k_graph(
    ticker: str,
    date: Optional[str] = None,
    section_select: bool = False,
    ontology_type: str = "causal",
    oai_model: str = "gpt-4o-mini",
    batch: bool = True,
    batch_size: int = 10,
    sentiment_filter: [float,bool] = None,
    output_dir: str = "./docs",
    use_cache: bool = True,
    verbose: bool = False
):
    # Check cache for 10-K data
    if use_cache:
        cached_10k_data = get_cached_10k_data(ticker, str(date))
        if cached_10k_data is not None:
            pandas_data, final_result = cached_10k_data
            pandas_data['index_url'] = pandas_data.apply(generate_sec_index_url, axis=1)
        else:
            pandas_data = process_10k_data(ticker=ticker, date=date, section_select=section_select)
            pandas_data['index_url'] = pandas_data.apply(generate_sec_index_url, axis=1) #think can be removed

            final_result = smart_adaptive_text_grouping(pandas_data)
            final_result['chunk_id'] = final_result.apply(generate_chunk_id, axis=1)
            final_result = final_result.rename(columns={'new_text': 'text'})
            cache_10k_data(ticker, str(date), (pandas_data, final_result))
    else:
        pandas_data = process_10k_data(ticker=ticker, date=date, section_select=section_select)
        final_result = smart_adaptive_text_grouping(pandas_data)
        final_result['chunk_id'] = final_result.apply(generate_chunk_id, axis=1)
        final_result = final_result.rename(columns={'new_text': 'text'})

    # Check cache for graph data
    if use_cache:
        cached_graph_data = get_cached_graph_data(ticker, str(date), ontology_type)
        if cached_graph_data is not None:
            graph_df = cached_graph_data
        else:
            # Initialize LLM client
            if batch:
                llm = OpenAIClientBatch(model=oai_model, temperature=0.2, top_p=0.5)
            else:
                llm = OpenAIClient(model=oai_model, temperature=0.1, top_p=0.5)

            # Initialize GraphMaker
            graph_maker = GraphMaker(ontology_type=ontology_type, llm_client=llm, verbose=verbose)

            # Generate graph DataFrame
            if batch:
                graph_df = df2GraphBatch(final_result, graph_maker, batch_size=batch_size, verbose=verbose)
            else:
                graph_df = df2Graph(final_result, graph_maker, verbose=verbose)

            cache_graph_data(ticker, str(date), ontology_type, graph_df)
    else:
        # Initialize LLM client
        if batch:
            llm = OpenAIClientBatch(model=oai_model, temperature=0.2, top_p=0.5)
        else:
            llm = OpenAIClient(model=oai_model, temperature=0.1, top_p=0.5)

        # Initialize GraphMaker
        graph_maker = GraphMaker(ontology_type=ontology_type, llm_client=llm, verbose=verbose)

        # Generate graph DataFrame
        if batch:
            graph_df = df2GraphBatch(final_result, graph_maker, batch_size=batch_size, verbose=verbose)
        else:
            graph_df = df2Graph(final_result, graph_maker, verbose=verbose)

    # Apply sentiment filter (not cached)
    if sentiment_filter:
        graph_df = graph_df[(graph_df["sentiment"] > sentiment_filter) | (graph_df["sentiment"] < -sentiment_filter)]

    # Generate contextual proximity
    dfg2 = contextual_proximity(graph_df)

    # Combine and group data
    dfg = pd.concat([graph_df, dfg2], axis=0)
    dfg = (
        dfg.groupby(["node_1", "node_2", "node_1_label", "node_2_label"])
        .agg({"chunk_id": ",".join, "edge": ','.join, 'count': 'sum', 'sentiment': 'mean'})
        .reset_index()
    )

    # Create graph
    if ontology_type in ["causal", "temporal"]:
        G = create_graph_directed(dfg)
    else:
        G = create_graph_undirected(dfg)

    # Detect communities and add attributes
    communities = detect_communities(G)
    colors_df = colors2Community(communities)
    add_node_attributes(G, colors_df)

    # Create PyVis network
    output_filename = f"{ticker}_{date}_{ontology_type}.html"
    create_pyvis_network(G, communities, output_filename, dfg, final_result)

    # Generate summary
    summary = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "total_communities": len(communities),
        "average_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
        "community_sizes": [len(community) for community in communities]
    }

    # Save summary
    summary_filename = f"{ticker}_{date}_{ontology_type}_summary.json"
    with open(summary_filename, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Graph analysis complete. Results saved in the {output_dir} directory.")

    return graph_df
