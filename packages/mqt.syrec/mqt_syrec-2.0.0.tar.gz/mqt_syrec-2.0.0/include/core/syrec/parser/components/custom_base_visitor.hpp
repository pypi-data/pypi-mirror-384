/*
 * Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
 * Copyright (c) 2025 Munich Quantum Software Company GmbH
 * All rights reserved.
 *
 * SPDX-License-Identifier: MIT
 *
 * Licensed under the MIT License
 */

#pragma once

#include "Token.h"
#include "core/configurable_options.hpp"
#include "core/syrec/expression.hpp"
#include "core/syrec/number.hpp"
#include "core/syrec/parser/utils/custom_error_messages.hpp"
#include "core/syrec/parser/utils/parser_messages_container.hpp"
#include "core/syrec/parser/utils/symbolTable/base_symbol_table.hpp"
#include "core/syrec/variable.hpp"

#include <charconv>
#include <cstdlib>
#include <format>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>

namespace syrec_parser {
    /**
     * The base class containing data structures and utility functions required in more specialized visitors.
     *
     * Note that this class does not derive from the TSyrecParserVisitor class, defining the potential visitor functions for the SyReC grammar, since we are providing
     * type-safe overloads for the visitor functions instead of relying on complex conversion from the std::any type to the expected return type of the visitor function.
     * The problem with the std::any type is that the user must know the exact type that is stored in the value of the std::any to be able to access it. This std::any_cast<T>
     * operation does not support polymorphism and other convenient behaviour that one can use std::optional<T>. Additionally, we can avoid the dynamic dispatch mechanism to
     * determine the correct visitor function (while still requiring dynamic_cast cascades) which now requires for future extensions of the grammar that the developer correctly
     * defines the handling of these new types in the visitors (instead of relying on the dynamic dispatch mechanism to determine which visitor function overload to call).
     *
     * An example:
     * struct Base { virtual std::string getName() = 0; };
     * struct Derived : Base { std::string getName() { return "Derived"; };
     *
     * std::any polymorphicReturn(int i) {
     *      if (i > 1)
     *          return std::make_shared<Base>();
     *      else if (!i)
     *          return std::make_shared<Derived>();
     *      return std::nullopt;
     * }
     *
     * void usePolymorphicReturn(){
     *      // Throws a std::bad_cast exception since the type stored in the std::any is std::shared_ptr<Derived>;
     *      const std::optional<std::shared_ptr<Base>> x = std::any_cast<std::shared_ptr<Base>>(polymorphicReturn(0);
     *      // Throws a std::bad_cast exception since the type stored in the std::any is std::shared_ptr<Derived>;
     *      const std::optional<std::shared_ptr<Derived>> x = std::any_cast<std::shared_ptr<Base>>(polymorphicReturn(0);
     * }
     */
    class CustomBaseVisitor {
    public:
        CustomBaseVisitor(const std::shared_ptr<ParserMessagesContainer>& sharedGeneratedMessageContainerInstance, const std::shared_ptr<utils::BaseSymbolTable>& sharedSymbolTableInstance, syrec::ConfigurableOptions parserConfiguration):
            sharedGeneratedMessageContainerInstance(sharedGeneratedMessageContainerInstance), symbolTable(sharedSymbolTableInstance), parserConfiguration(std::move(parserConfiguration)) {}

    protected:
        static constexpr unsigned int DEFAULT_EXPRESSION_BITWIDTH   = 32;
        static constexpr unsigned int MAX_SUPPORTED_SIGNAL_BITWIDTH = 32;

        std::shared_ptr<ParserMessagesContainer> sharedGeneratedMessageContainerInstance;
        std::shared_ptr<utils::BaseSymbolTable>  symbolTable;
        syrec::ConfigurableOptions               parserConfiguration;

        [[nodiscard]] static Message::Position mapTokenPositionToMessagePosition(const antlr4::Token& token) {
            return Message::Position(token.getLine(), token.getCharPositionInLine());
        }

        /**
         * Deserialize a number from a given string.
         * @param stringifiedConstantValue The stringified number to process whose whitespace prefix and/or suffix is trimmed prior to processing.
         * @param didDeserializationFailDueToOverflow An optional flag indicating whether the deserialized number was larger than the maximum allowed value UINT_MAX.
         * @param base The expected base of the \p stringifiedConstantValue (10 for integers, 16 for hexadecimal and 2 for binary literals). Must be either 2, 10 or 16.
         * @return The deserialized number if the detected prefix (base=2 => '0b', base=10 => None, base=16 => '0x') in the \p stringifiedConstantValue matched the expected \p base and the deserialized value was not larger than the maximum allowed value, otherwise std::nullopt.
         */
        [[nodiscard]] static std::optional<unsigned int> deserializeConstantFromString(const std::string_view& stringifiedConstantValue, bool* didDeserializationFailDueToOverflow, const int base = 10) {
            if (base != 2 && base != 10 && base != 16) {
                return std::nullopt;
            }

            std::string_view viewOfStringifiedConstantValue = stringifiedConstantValue;
            // Trim leading and trailing whitespaces from given std::string prior to the actual deserialization call
            const std::size_t numLeadingWhitespaces = viewOfStringifiedConstantValue.find_first_not_of(' ');
            viewOfStringifiedConstantValue.remove_prefix(numLeadingWhitespaces != std::string::npos ? numLeadingWhitespaces : 0);

            const std::size_t numTrailingWhitespaces = viewOfStringifiedConstantValue.find_last_not_of(' ');
            viewOfStringifiedConstantValue.remove_suffix(viewOfStringifiedConstantValue.size() - (numTrailingWhitespaces != std::string::npos ? (numTrailingWhitespaces + 1) : viewOfStringifiedConstantValue.size()));

            if (base == 16) {
                if (!viewOfStringifiedConstantValue.starts_with("0x") && !viewOfStringifiedConstantValue.starts_with("0X")) {
                    return std::nullopt;
                }
                viewOfStringifiedConstantValue.remove_prefix(2U);
            } else if (base == 2) {
                if (!viewOfStringifiedConstantValue.starts_with("0b") && !viewOfStringifiedConstantValue.starts_with("0B")) {
                    return std::nullopt;
                }
                viewOfStringifiedConstantValue.remove_prefix(2U);
            }

            unsigned int constantValue                                 = 0;
            auto [pointerToLastNonNumericCharacterInString, errorCode] = std::from_chars(viewOfStringifiedConstantValue.data(), viewOfStringifiedConstantValue.data() + viewOfStringifiedConstantValue.size(), constantValue, base);
            if (errorCode == std::errc::result_out_of_range || errorCode == std::errc::invalid_argument) {
                if (didDeserializationFailDueToOverflow != nullptr && errorCode == std::errc::result_out_of_range) {
                    *didDeserializationFailDueToOverflow = true;
                }
                return std::nullopt;
                // Check whether the whole string was processed by std::from_chars by checking whether the returned out pointer is equal to the end of the processed.
                // Otherwise, the provided input string contained non-numeric character (i.e. '123abc')
            }
            if (errorCode == std::errc() && pointerToLastNonNumericCharacterInString == (viewOfStringifiedConstantValue.data() + viewOfStringifiedConstantValue.size())) {
                return constantValue;
            }
            return std::nullopt;
        }

        [[nodiscard]] static std::optional<unsigned int> tryGetConstantValueOf(const syrec::Expression& expression) {
            if (const auto& expressionAsNumericOne = dynamic_cast<const syrec::NumericExpression*>(&expression); expressionAsNumericOne != nullptr && expressionAsNumericOne->value && expressionAsNumericOne->value) {
                return tryGetConstantValueOf(*expressionAsNumericOne->value);
            }
            return std::nullopt;
        }

        [[nodiscard]] static std::optional<unsigned int> tryGetConstantValueOf(const syrec::Number& number) {
            return number.isConstant() ? number.tryEvaluate({}) : std::nullopt;
        }

        [[nodiscard]] static std::optional<std::pair<unsigned int, unsigned int>> tryDetermineAccessedBitrangeOfVariableAccess(const syrec::VariableAccess& variableAccess) {
            if (!variableAccess.range.has_value()) {
                return std::make_pair(0, variableAccess.bitwidth() - 1);
            }

            if (!variableAccess.range->first || !variableAccess.range->second) {
                return std::nullopt;
            }

            const std::optional<unsigned int> accessedBitrangeStart = variableAccess.range->first->tryEvaluate({});
            const std::optional<unsigned int> accessedBitRangeEnd   = accessedBitrangeStart.has_value() ? variableAccess.range->second->tryEvaluate({}) : std::nullopt;
            if (!accessedBitRangeEnd.has_value()) {
                return std::nullopt;
            }
            return std::make_pair(*accessedBitrangeStart, *accessedBitRangeEnd);
        }

        [[nodiscard]] static unsigned int getLengthOfAccessedBitrange(const std::pair<unsigned int, unsigned int> accessedBitrange) {
            return (accessedBitrange.first > accessedBitrange.second ? accessedBitrange.first - accessedBitrange.second : accessedBitrange.second - accessedBitrange.first) + 1;
        }

        /**
         * @brief Build and record a semantic error of a specific type whose message template accepts one or more arguments
         * @tparam T The types of the arguments provided to the template parameter pack
         * @tparam semanticError The kind of semantic error to create
         * @param messagePosition The origin of the semantic error in the SyReC program
         * @param args User-provided arguments that will be used to replace the placeholders in the message template of the semantic error
         */
        template<SemanticError semanticError, typename... T>
        void recordSemanticError(Message::Position messagePosition, T&&... args) const {
            if (!sharedGeneratedMessageContainerInstance) {
                return;
            }

            static_assert(!getFormatForSemanticErrorMessage<semanticError>().empty(), "No format for message of semantic error found!");
            static_assert(!getIdentifierForSemanticError<semanticError>().empty(), "No identifiers for semantic error found!");

            constexpr std::string_view identifierForSemanticError = getIdentifierForSemanticError<semanticError>();
            sharedGeneratedMessageContainerInstance->recordMessage(std::make_unique<Message>(Message::Type::Error, std::string(identifierForSemanticError), messagePosition, std::format(getFormatForSemanticErrorMessage<semanticError>(), std::forward<T>(args)...)));
        }

        /**
         * @brief Build and record a semantic error of a specific type whose message template accepts no arguments
         * @tparam semanticError The kind of semantic error to create
         * @param messagePosition The origin of the semantic error in the SyReC program
         */
        template<SemanticError semanticError>
        void recordSemanticError(Message::Position messagePosition) const {
            if (!sharedGeneratedMessageContainerInstance) {
                return;
            }

            static_assert(!getFormatForSemanticErrorMessage<semanticError>().empty(), "No format for message of semantic error found!");
            static_assert(!getIdentifierForSemanticError<semanticError>().empty(), "No identifiers for semantic error found!");

            constexpr std::string_view identifierForSemanticError = getIdentifierForSemanticError<semanticError>();
            sharedGeneratedMessageContainerInstance->recordMessage(std::make_unique<Message>(Message::Type::Error, std::string(identifierForSemanticError), messagePosition, std::string(getFormatForSemanticErrorMessage<semanticError>())));
        }

        /**
         * @brief Record a custom error
         * @param messagePosition The origin of the semantic error in the SyReC program
         * @param errorMessage The text of the error message (can be empty)
         */
        void recordCustomError(Message::Position messagePosition, const std::string& errorMessage) const {
            sharedGeneratedMessageContainerInstance->recordMessage(std::make_unique<Message>(Message::Type::Error, "UNKNOWN", messagePosition, errorMessage));
        }
    };
} // namespace syrec_parser
