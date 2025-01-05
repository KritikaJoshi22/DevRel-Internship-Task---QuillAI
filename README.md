# QuillAIbot

A chatbot built using Coinbase's CDP AgentKit that provides detailed token analysis and information for various blockchain networks. The chatbot uses QuillCheck API for comprehensive token analysis and Google's Gemini AI for natural language processing.

## Video Walkthrough
Watch a demonstration of how to use this chatbot in this video: [Watch the video](https://www.loom.com/share/e96860c3a5b149cfa5324217797efad8?sid=7596b3f1-d51c-4bae-9928-4da5c21694d2)

## Features

- Token analysis with detailed security metrics
- Support for multiple blockchain networks (Ethereum, BSC, Polygon, Base)
- Security score assessment
- Holder statistics
- Liquidity information
- Honeypot detection
- External links to popular platforms

## Prerequisites

Before running the chatbot, you will need to obtain API keys from the following services:

1. CDP API Key from [CDP Portal](https://portal.cdp.coinbase.com/)
2. QuillCheck API Key from [QuillCheck](https://check.quillai.network/apikey)
3. Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Installation

1. Clone this repository:

```bash
https://github.com/KritikaJoshi22/QuillAIbot.git
```

2. Navigate to the chatbot directory:

```bash
cd cdp-langchain/examples/chatbot
```

3. Install the required package:

```bash
pip install cdp-langchain
```

## Configuration

1. Create a `.env` file in the project directory with the following structure:

```env
CDP_API_KEY_NAME="your_cdp_api_key_name"
CDP_API_KEY_PRIVATE_KEY="your_cdp_private_key"
GEMINI_API_KEY="your_gemini_api_key"
QUILLAI_API_KEY="your_quillcheck_api_key"
NETWORK_ID="base-sepolia"  # Optional, defaults to base-sepolia
```

2. Replace the placeholder values with your actual API keys and credentials

## Usage

1. Start the chatbot:

```bash
python chatbot.py
```

2. Query token information using the following format:

```
What is the token information for the token at address TOKEN_ADDRESS on the CHAIN_NAME chain?
```

Example:

```
What is the token information for the token at address 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 on the Ethereum chain?
```

The chatbot will respond with detailed token information including:

- Basic token information
- Security scores
- Holder statistics
- Liquidity information
- Security checks
- External links
- Honeypot analysis

## Supported Networks

- Ethereum (chain ID: 1)
- BSC (chain ID: 56)
- Polygon (chain ID: 137)
- Base (chain ID: 8453)

## Note

Make sure to keep your API keys secure and never commit them to version control. The `.env` file should be added to your `.gitignore` file.

## Resources

- [CDP AgentKit Documentation](https://github.com/coinbase/cdp-agentkit)
- [QuillCheck Documentation](https://check.quillai.network)
- [Google AI Studio](https://aistudio.google.com)

## License

This project is licensed under the terms specified in the CDP AgentKit repository.
