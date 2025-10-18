import re
from typing import Any, Optional
import logging

from transformers import PreTrainedModel, PreTrainedTokenizer, BatchEncoding
import torch
from at2.tasks import ContextAttributionTask

from ..util.response_processor import ResponseProcessor

DEFAULT_GENERATE_KWARGS = {
    "do_sample": False,
    "top_p": None,
    "top_k": None,
    "temperature": None,
}

logger = logging.getLogger(__name__)

class AttributionTask(ContextAttributionTask):
    """
    Generates response given a prompt, splits the response, maps character spans 
    to token spans.
    """
    def __init__(
            self,
            prompt: str,
            char_spans: dict,
            model: PreTrainedModel,
            tokenizer: PreTrainedTokenizer,
            max_new_tokens: int,
            include_source_candidate_ids_in_ranges: bool,
            attention_query: str,
            multiple_statements: bool,
            cache: dict[str, Any] = None,
    ):
        """
        
        :param prompt: Prompt for generation.
        :param char_spans: Character spans with respect to the prompt.
            Required shape:
            {
                "source_candidates": [
                    {
                        "id": (20, 23), # Span of id (e.g. "[0]")
                        "content": (24, 103) # Span of content
                    },
                    {...},
                    ...
                ]
                "question": (120, 151) # Span of question (only required for retriever)
            }
        :param model: LLM for generation.
        :param tokenizer: Tokenizer for LLM.
        :param max_new_tokens: Maximum number of new tokens to generate.
        :param include_source_candidate_ids_in_ranges: Whether to include the
            source candidate ids in the document ranges.
        :param attention_query: Which part of the input to use as query for
            attention-based citation scorers. One of:
            - 'question': Use the question as query.
            - 'statement': Use the generated statement(s) without citations as query.
            - 'statement_and_citations': Use the generated statement(s) with citations as query.
            - 'citations': Use the generated citations as query.
        :param multiple_statements: Whether the generation contains multiple
            statements (e.g. multiple sentences). If True, generated text will be
            split.
        :param cache: Cache for storing intermediate results (can be pre-filled).
        """
        super().__init__(
            model=model,
            tokenizer=tokenizer,
            generate_kwargs=DEFAULT_GENERATE_KWARGS,
            cache=cache
        )

        self._prompt = prompt
        self._char_spans = char_spans
        self.include_source_candidate_ids_in_ranges = include_source_candidate_ids_in_ranges
        self.attention_query = attention_query
        if self.attention_query not in [
            'question',
            'statement',
            'statement_and_citations',
            'citations'
        ]:
            raise ValueError(
                f'Invalid attribution query: {self.attention_query}. '
                f'Valid queries are: question, statement, statement_and_citations, citations'
            )
        self.multiple_statements = multiple_statements

        self.generate_kwargs['max_new_tokens'] = max_new_tokens
        if tokenizer.pad_token == tokenizer.eos_token:
            self.generate_kwargs['pad_token_id'] = tokenizer.eos_token_id

        self._generate_was_run = False

    @property
    def prompt(self):
        return self._prompt

    @property
    def input_text(self):
        return self.prompt

    @property
    def char_spans(self):
        """
        Get char spans for the generated text if needed and return
        :return:
        """
        if not 'statement' in self._char_spans:
            self._char_spans.update(self.get_statement_and_citations_char_ranges())
        return self._char_spans

    @property
    def logits(self):
        """
        Get per-token logits
        :return:
        """
        if self._cache.get("logits") is None:
            self._cache.update(self.get_hidden_states_and_logits())
        return self._cache["logits"]

    @property
    def hidden_states(self):
        """
        Get per-token hidden states
        :return:
        """
        if self._cache.get('hidden_states') is None:
            self._cache.update(self.get_hidden_states_and_logits())
        return self._cache['hidden_states']

    @property
    def sub_target_char_ranges(self) -> list[tuple[int, int]]:
        """
        Get character ranges of attention queries.
        :return:
        """
        return self._get_sub_target_char_ranges()

    def get_sub_target_token_ranges(
            self,
            split_by: Optional[str] = 'sentence',
            relative: bool = False
    ) -> list[tuple[int, int]]:
        """
        Get token ranges of targets (i.e. parts of the generation)
        :param split_by: How to split the generation into sub-parts. Currently
            only "sentence" is available.
        :param relative: Whether the token ranges should be relative to the
            beginning of the generation.
        :return: List of (start, end) token ranges for each sub-target.
        """
        if split_by != 'sentence':
            raise ValueError
        ranges = [
            self.char_range_to_token_range(*char_range)
            for char_range in self.sub_target_char_ranges
        ]
        if relative:
            offset, _ = self.target_token_range
            ranges = [(start - offset, end - offset) for start, end in ranges]
        return ranges

    @property
    def generate_was_run(self):
        """
        Indicates if the current instance generated text or if it was passed to
        the instance during initialization.
        :return:
        """
        return self._generate_was_run

    @property
    def generated_citations(self) -> list[list[int]]:
        """
        Get the generated citations as integers
        :return: List of lists of citation indices (one list per statement)
        """
        if self._cache.get('generated_citations') is None:
            self._cache['generated_citations'] = self._get_generated_citations()

        return self._cache['generated_citations']

    def get_input_tokens(
            self,
            return_tensors=None
    ) -> BatchEncoding:
        """
        Tokenize the input text (prompt)
        Override parent method because we set add_special_tokens to True
        :param return_tensors:
        :return: BatchEncoding object for tokenized input
        """
        if "input_tokens" not in self._cache:
            self._cache["input_tokens"] = {}
        if return_tensors not in self._cache["input_tokens"]:
            self._cache["input_tokens"][return_tensors] = self.tokenizer(
                self.input_text, add_special_tokens=True, return_tensors=return_tensors
            )

        return self._cache["input_tokens"][return_tensors]

    def get_tokens(
            self,
            return_tensors=None
    ) -> BatchEncoding:
        """
        Tokenize input text + generated text (self.text)
        Override parent method because we set add_special_tokens to True
        :param return_tensors:
        :return: BatchEncoding object for tokenized text
        """
        if "tokens" not in self._cache:
            self._cache["tokens"] = {}
        if return_tensors not in self._cache["tokens"]:
            self._cache["tokens"][return_tensors] = self.tokenizer(
                self.text, add_special_tokens=True, return_tensors=return_tensors
            )

        return self._cache["tokens"][return_tensors]

    @staticmethod
    def find_statement_and_citation_char_ranges(
            statement_with_citations: str
    ) -> tuple[tuple[int, int], list[tuple[int, int]]]:
        """
        Split the given statement with citations into statement (text) and citations.
        Return the character spans of statement and individual citations.
        :param statement_with_citations:
        :return:
        """
        # Find index of first citation
        pattern = r'\[([0-9]+)\]'
        citations_char_ranges_in_statement = [
            (match.start(), match.end())
            for match in re.finditer(pattern, statement_with_citations)
        ]

        # statement_char_range is beginning of generation until first citation
        if citations_char_ranges_in_statement:
            statement_end = citations_char_ranges_in_statement[0][0] - 1  # -1 because of space
            statement_char_range = (0, statement_end)
        else:
            statement_char_range = (0, len(statement_with_citations))

        return statement_char_range, citations_char_ranges_in_statement

    def get_statement_and_citations_char_ranges(
            self
    ) -> dict[str, list[tuple[int, int]] | list[list[tuple[int, int]]]]:
        """
        Process the text generated by the model and extract absolute (i.e. with
        respect to the beginning of the LLM input) character spans:
        - of each generated statement (sentence) without citations
        - of each stretch of citations (e.g. "[2] [4]")
        - of statements with citations (e.g. "<statement> [2] [4]")
        - of individual citations (e.g. "[2]", "[4]")
        :return:
        """
        if self.multiple_statements:
            response_processor = ResponseProcessor(
                multiple_statements=True
            )
            # split response
            statements_with_citations = response_processor.split_raw_response(
                self.generation
            )
        else:
            statements_with_citations = [self.generation]

        statement_char_ranges = []
        citations_char_ranges = []
        statement_and_citations_char_ranges = []
        individual_citations_char_ranges = []

        # Process each statement
        absolute_offset = len(self.input_text)
        pos_in_generation = 0
        for statement_with_citations in statements_with_citations:
            # Find position in generation (starting at the end of the last statement)
            pos_in_generation = (
                self.generation[pos_in_generation:].find(statement_with_citations)
                + pos_in_generation
            )

            (
                statement_char_range,
                individual_citations_char_ranges_for_statement
            ) = self.find_statement_and_citation_char_ranges(statement_with_citations)

            # Convert relative ranges to absolute character ranges
            statement_char_range = (
                statement_char_range[0] + absolute_offset + pos_in_generation,
                statement_char_range[1] + absolute_offset + pos_in_generation
            )
            individual_citations_char_ranges_for_statement = [
                (
                    start + absolute_offset + pos_in_generation,
                    end + absolute_offset + pos_in_generation
                )
                for start, end in individual_citations_char_ranges_for_statement
            ]

            if individual_citations_char_ranges_for_statement:
                # Get range of all citations as beginning of first and end of last
                citations_char_range_for_statement = (
                    individual_citations_char_ranges_for_statement[0][0],
                    individual_citations_char_ranges_for_statement[-1][1]
                )
            else:
                # If no citations, set range to end of statement
                citations_char_range_for_statement = (
                    None, None
                )
            statement_and_citations_char_range = (
                pos_in_generation + absolute_offset,
                pos_in_generation + absolute_offset + len(statement_with_citations)
            )
            if statement_char_range[0] == statement_char_range[1]:
                # Sometimes models do not generate text. In these cases we use
                # the generation with citations as the statement to avoid errors
                statement_char_ranges.append(statement_and_citations_char_range)
            else:
                statement_char_ranges.append(statement_char_range)
            citations_char_ranges.append(
                citations_char_range_for_statement
            )
            individual_citations_char_ranges.append(
                individual_citations_char_ranges_for_statement
            )


            # Go to end of current statement
            pos_in_generation += len(statement_with_citations)

        return {
            'statement': statement_char_ranges,
            'citations': citations_char_ranges,
            'statement_and_citations': statement_and_citations_char_ranges,
            'individual_citations': individual_citations_char_ranges
        }

    def _get_generated_citations(self) -> list[list[tuple[int, int]]]:
        """
        Extract the citations from the text generated by the LLM as integers
        :return:
        """
        pattern = r'\[([0-9]+)\]'
        generated_citations = []
        for char_span_list_for_statement in self.char_spans['individual_citations']:
            generated_citations_for_statement = []
            for start, end in char_span_list_for_statement:
                citation_text = self.text[start: end]
                match = re.match(pattern, citation_text)
                citation_number = int(match.group(1))
                generated_citations_for_statement.append(citation_number)
            generated_citations.append(generated_citations_for_statement)
        return generated_citations

    def generate(self, mask=None, output_hidden_states=False):
        """Let the model generate using the given prompt."""
        input_text, input_tokens = self.get_input_text_and_tokens(
            return_tensors="pt", mask=mask
        )
        # FIXME: This could be made more efficient by first doing the fwd
        # pass and then doing the generation based on the existing past key values
        output = self.model.generate(
            **input_tokens.to(self.model.device),
            **self.generate_kwargs,
            return_dict_in_generate=True
        )
        # Get generated text
        # We take the original input because sometimes encoding and decoding changes it
        raw_text = self.tokenizer.decode(output.sequences[0])
        input_ids = input_tokens["input_ids"][0]
        input_length = len(self.tokenizer.decode(input_ids))
        generation = raw_text[input_length:]
        text = input_text + generation

        self._generate_was_run = True

        return {
            'text': text
        }

    def get_hidden_states(self) -> torch.Tensor:
        return self.get_hidden_states_and_logits()['hidden_states']

    def get_hidden_states_and_logits(self) -> dict[str, torch.Tensor]:
        tokens = self.get_tokens(return_tensors='pt')
        if self.generate_was_run:
            # not using last token as the generation did not produce a hidden state for it
            correction = -1
        else:
            # Using the last token because we are using generation from cache,
            # where last token was already removed
            correction = 0
        max_token_idx = tokens['input_ids'].shape[1] + correction

        with torch.no_grad():
            fwd_output = self.model(
                input_ids=tokens['input_ids'].to(self.model.device)[:, : max_token_idx],
                output_hidden_states=True
            )
            logits = fwd_output.logits
            hidden_states = fwd_output.hidden_states

        return {
            "logits": logits,
            "hidden_states": hidden_states,
        }

    def char_range_to_token_range(
            self,
            start_index = None,
            end_index = None
    ) -> tuple[int, int]:
        """
        This is a substitute for target_range_to_token_range. Here, the indices
        are absolute instead of relative to the beginning of the generation.
        :param start_index: Start character index
        :param end_index: End character index
        :return: The token range for the given character range
        """
        text = self.text
        tokens = self.get_tokens(return_tensors='pt')
        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = len(text) - 1

        token_start = tokens.char_to_token(start_index)
        # We subtract 1 from the char end_index to avoid errors when it goes
        # beyond the generation length
        # We add 1 to the resulting token end index to make it exclusive
        token_end = tokens.char_to_token(end_index - 1) + 1

        return token_start, token_end

    def _get_sub_target_char_ranges(self) -> list[tuple[int, int]]:
        """
        Get the absolute character ranges of the target (i.e. generated text part)
        split into statements
        :return:
        """
        query_char_ranges = self.char_spans[self.attention_query]
        if self.attention_query in ['question']:
            query_char_ranges = [query_char_ranges]
        return query_char_ranges

    def _get_document_ranges(self) -> list[tuple[int, int]]:
        """
        Get the character ranges of source candidates (documents).
        :return:
        """
        document_ranges = []
        for source_candidate_dict in self.char_spans['source_candidates']:
            if self.include_source_candidate_ids_in_ranges:
                start = source_candidate_dict['id'][0]
            else:
                start = source_candidate_dict['content'][0]

            end = source_candidate_dict['content'][1]

            document_ranges.append((start, end))

        return document_ranges

    def prompt_range_to_token_range(
            self,
            start_index: int,
            end_index: int
    ) -> tuple[int, int]:
        """
        Convert prompt character range to token range
        :param start_index: Start character index
        :param end_index: End character index
        :return:
        """
        _, prompt_tokens = self.get_input_text_and_tokens()
        token_start_index = prompt_tokens.char_to_token(start_index)
        token_end_index = prompt_tokens.char_to_token(end_index)

        return token_start_index, token_end_index

    def get_mean_sequence_probability(
            self,
            start_index: int,
            end_index: int
    ) -> float:
        """
        Get mean generation probability of given token range
        :param start_index: Start token index
        :param end_index: End token index
        :return:
        """
        if end_index - start_index <= 0 or None in (start_index, end_index):
            logger.warning(
                f'Invalid token range: {start_index} - {end_index}. '
            )
            # Token not found
            return -1.0
        # Get logits
        logits = self.logits
        # We subtract 1 as logits for token were produced before
        logits = logits[:, start_index - 1: end_index - 1]
        # Get token ids
        labels = self.get_tokens(return_tensors='pt') \
            ['input_ids'][:, start_index : end_index].to(logits.device)
        # Get per-token logit probabilities
        logit_probs = compute_logit_probs(logits, labels)
        # Average over tokens and exponentiate to get probabilities
        mean_sequence_probability = float(logit_probs.mean(dim=1).exp().squeeze())
        return mean_sequence_probability


def compute_logit_probs(
        logits: torch.Tensor,
        labels: torch.Tensor
) -> torch.Tensor:
    """
    Compute logit proba
    :param logits: Tensor of shape (batch_size, seq_length, num_classes)
    :param labels: Tensor of shape (batch_size, seq_length)
    :return: Tensor of shape (batch_size, seq_length) with logit probabilities
    """
    batch_size, seq_length, num_classes = logits.shape
    # Reshape to (batch_size * seq_length, num_classes)
    reshaped_logits = logits.reshape(batch_size * seq_length, num_classes)
    # Reshape to (batch_size * seq_length)
    reshaped_labels = labels.reshape(batch_size * seq_length)
    # Get logits of generated tokens (~softmax numerator)
    correct_logits = reshaped_logits.gather(-1, reshaped_labels[:, None])[:, 0]
    cloned_logits = reshaped_logits.clone()
    # Make logsumexp of all logits (~softmax denominator)
    other_logits = cloned_logits.logsumexp(dim=-1)
    # Subtract to get logit probabilities
    reshaped_outputs = correct_logits - other_logits
    return reshaped_outputs.reshape(batch_size, seq_length)
