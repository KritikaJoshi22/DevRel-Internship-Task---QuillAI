import json
import os
import sys
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper
from cdp_langchain.tools import CdpTool
from pydantic import BaseModel, Field
from typing import Dict, Any
import requests

# Load environment variables from the .env file
load_dotenv()

# Retrieve the API keys from the environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QUILLAI_API_KEY = os.getenv("QUILLAI_API_KEY")
if not GEMINI_API_KEY or not QUILLAI_API_KEY:
    raise ValueError("GEMINI_API_KEY or QUILLAI_API_KEY is not set in the .env file")

# Configure a file to persist the agent's CDP MPC Wallet Data
wallet_data_file = "wallet_data.txt"

TOKEN_INFO_PROMPT = """
This tool fetches detailed information about a token using the Quill API. It provides comprehensive data including 
token metrics, market data, holder information, and security analysis. Use this when you need to analyze or 
verify token information on a specific blockchain.
"""

# Chain ID to Name Mapping
CHAIN_MAPPING = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "base": 8453
}

class TokenInfoInput(BaseModel):
    """Input argument schema for token information action."""
    chain_id: str = Field(
        ...,
        description="The blockchain network ID where the token exists (e.g., '1' for Ethereum mainnet)"
    )
    token_address: str = Field(
        ..., description="The contract address of the token to analyze"
    )

def format_token_info(data: Dict[Any, Any]) -> str:
    """Format token information into a readable, organized string."""
    token_info = data.get('tokenInformation', {})
    market_checks = data.get('marketChecks', {})
    code_checks = data.get('codeChecks', {})
    token_score = data.get('tokenScore', {})
    
    def format_number(num_str):
        try:
            return f"{float(num_str):,.2f}"
        except (ValueError, TypeError):
            return "N/A"

    def format_percent(num):
        try:
            return f"{float(num):.2f}%"
        except (ValueError, TypeError):
            return "N/A"

    def format_usd(num_str):
        try:
            num = float(num_str)
            if num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            else:
                return f"${num:.2f}"
        except (ValueError, TypeError):
            return "N/A"

    def format_pairs():
        pairs = data.get('marketChecks', {}).get('pairByPairInformation', [])
        if not pairs:
            return "No trading pairs found"
        
        pairs_info = "\n🔄 TOP TRADING PAIRS\n" + "=" * 20 + "\n"
        for pair in pairs[:3]:
            pairs_info += (
                f"• {pair.get('token0Symbol', 'N/A')}/{pair.get('token1Symbol', 'N/A')} on {pair.get('dexName', 'N/A')}\n"
                f"  Liquidity: {pair.get('lpSupplyInUsd', 'N/A')}\n"
                f"  Pair Address: {pair.get('pairAddress', 'N/A')}\n"
            )
        return pairs_info

    output = f"""
🔎 TOKEN ANALYSIS REPORT
{"="* 50}

📊 BASIC INFORMATION
-------------------
Name: {token_info.get('tokenName', 'N/A')}
Symbol: {token_info.get('tokenSymbol', 'N/A')}
Address: {token_info.get('tokenAddress', 'N/A')}
Creation Date: {token_info.get('tokenCreationDate', 'N/A').split('T')[0]}
Total Supply: {format_number(token_info.get('totalSupply', 'N/A'))}

💯 SECURITY SCORE
----------------
Overall Score: {format_percent(token_score.get('totalScore', {}).get('percent', 0))}
Code Score: {format_percent(token_score.get('codeScore', {}).get('percent', 0))}
Market Score: {format_percent(token_score.get('marketScore', {}).get('percent', 0))}

👥 HOLDER STATISTICS
------------------
Total Holders: {format_number(market_checks.get('holdersChecks', {}).get('holdersCount', {}).get('number', 0))}
Top 3 Holders: {format_percent(market_checks.get('holdersChecks', {}).get('percentDistributed', {}).get('topThree', {}).get('percent', 0))}
Top 10 Holders: {format_percent(market_checks.get('holdersChecks', {}).get('percentDistributed', {}).get('topTen', {}).get('percent', 0))}

💧 LIQUIDITY INFORMATION
----------------------
Total Liquidity: {format_usd(market_checks.get('liquidityChecks', {}).get('aggregatedInformation', {}).get('totalLpSupplyInUsd', {}).get('number', 0))}
LP Holders: {market_checks.get('liquidityChecks', {}).get('aggregatedInformation', {}).get('lpHolderCount', {}).get('number', 'N/A')}
Trading Pairs: {market_checks.get('liquidityChecks', {}).get('aggregatedInformation', {}).get('tradingPairCount', {}).get('number', 'N/A')}

🔒 SECURITY CHECKS
----------------"""

    security_checks = code_checks.get('ownershipChecks', {})
    for check_name, check_data in security_checks.items():
        if isinstance(check_data, dict) and 'description' in check_data:
            status = "✅" if check_data.get('status') else "❌"
            output += f"\n{status} {check_data['description']}"

    output += f"\n\n{format_pairs()}"

    output += "\n🔗 EXTERNAL LINKS\n----------------"
    for link_name, url in token_info.get('externalLinks', {}).items():
        if url:
            output += f"\n• {link_name}: {url}"

    honeypot_details = data.get('honeypotDetails', {})
    is_honeypot = honeypot_details.get('isTokenHoneypot', 1)
    output += f"\n\n🍯 HONEYPOT CHECK\n----------------\n"
    output += "✅ Not a honeypot" if is_honeypot == 0 else "⚠️ Potential honeypot detected"
    
    return output

def get_token_info(chain_id: str, token_address: str) -> Dict[Any, Any]:
    """Fetch token information from the Quill API."""
    base_url = "https://check-api.quillai.network/api/v1/tokens/information"
    url = f"{base_url}/{token_address}?chainId={chain_id}"

    headers = {
        "x-api-key": QUILLAI_API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        formatted_output = format_token_info(data)
        # Return the formatted output directly without any additional summary
        return formatted_output
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch token information: {str(e)}")

def initialize_agent():
    """Initialize the agent with CDP Agentkit."""
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=GEMINI_API_KEY)
    wallet_data = None
    if os.path.exists(wallet_data_file):
        with open(wallet_data_file) as f:
            wallet_data = f.read()

    values = {}
    if wallet_data is not None:
        values = {"cdp_wallet_data": wallet_data}

    agentkit = CdpAgentkitWrapper(**values)

    wallet_data = agentkit.export_wallet()
    with open(wallet_data_file, "w") as f:
        f.write(wallet_data)

    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()

    tokenInfoTool = CdpTool(
        name="get_token_info",
        description=TOKEN_INFO_PROMPT,
        cdp_agentkit_wrapper=agentkit,
        args_schema=TokenInfoInput,
        func=get_token_info,
    )

    tools.append(tokenInfoTool)

    memory = MemorySaver()
    config = {"configurable": {"thread_id": "CDP Agentkit Chatbot"}}

    return create_react_agent(
        llm,
        tools=tools,
        checkpointer=memory,
        state_modifier=(
            "You are a helpful agent that can interact onchain using the Coinbase Developer Platform Agentkit. "
            "You are empowered to interact onchain using your tools. If you ever need funds, you can request them "
            "from the faucet if you are on network ID base-sepolia. If not, you can provide your wallet details and "
            "request funds from the user. If someone asks you to do something you can't do with your currently "
            "available tools, you must say so, and encourage them to implement it themselves using the CDP SDK + "
            "Agentkit, recommend they go to docs.cdp.coinbase.com for more information. Be concise and helpful with "
            "your responses. Refrain from restating your tools' descriptions unless it is explicitly requested."
        ),
    ), config

def run_chat():
    """Run the chatbot in interactive mode."""
    agent_executor, config = initialize_agent()
    print("Starting chatbot... Type 'exit' to end.")
    
    while True:
        try:
            user_input = input("\nUser: ")
            if user_input.lower() == "exit":
                break

            user_input = user_input.lower().strip()
            if user_input in CHAIN_MAPPING:
                print(f"Chain ID for {user_input.capitalize()}: {CHAIN_MAPPING[user_input]}")
            else:
                for chunk in agent_executor.stream(
                    {"messages": [HumanMessage(content=user_input)]}, config):
                    if "agent" in chunk:
                        print(chunk["agent"]["messages"][0].content)
                    elif "tools" in chunk:
                        print(chunk["tools"]["messages"][0].content)
                    print("-------------------")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

if __name__ == "__main__":
    run_chat()