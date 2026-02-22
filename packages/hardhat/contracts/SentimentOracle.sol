// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SentimentOracle
 * @notice AI-Powered Onchain Sentiment Oracle for SentimentFi
 * @dev Stores aggregated sentiment scores per token pushed from an offchain AI engine.
 *      Scores are integers representing the sentiment * 100 (e.g., +75 = 0.75, -42 = -0.42).
 *      Designed to be minimal and hackathon-ready on Monad Testnet.
 */
contract SentimentOracle {
    /// @notice Mapping from token symbol to its latest sentiment score (scaled by 100)
    mapping(string => int256) public sentimentScores;

    /// @notice Emitted when a sentiment score is updated
    /// @param token The token symbol (e.g., "MONAD", "BTC", "ETH")
    /// @param score The new sentiment score (scaled by 100, range: -100 to +100)
    event SentimentUpdated(string token, int256 score);

    /**
     * @notice Update the sentiment score for a given token
     * @param token The token symbol
     * @param score The sentiment score (scaled by 100)
     */
    function updateSentiment(string memory token, int256 score) public {
        sentimentScores[token] = score;
        emit SentimentUpdated(token, score);
    }

    /**
     * @notice Read the latest sentiment score for a given token
     * @param token The token symbol
     * @return The sentiment score (scaled by 100)
     */
    function getSentiment(string memory token) public view returns (int256) {
        return sentimentScores[token];
    }
}
