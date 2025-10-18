import re


class ResponseProcessor:
    """
    Splits texts into multiple sentences / statements and splits statements into
    textual content and citations.
    """
    def __init__(
            self,
            multiple_statements: bool,
            n_processes: int = 1,
    ):
        """
        :param multiple_statements: Whether to split raw responses into multiple
            statements (sentences).
        :param n_processes:
        """
        self.multiple_statements = multiple_statements
        self.n_processes = n_processes

    def process_response(
            self,
            raw_response: str,
    ) -> tuple[list[str], list[list[int]]] | tuple[str, list[int]]:
        """
        If self.multiple_statements is True, split raw_response into statements
        and then extract citations as integers and free text statement.
        Prediction object.
        :param raw_response: Raw response text
        :return If self.multiple_statements:
            - tuple of list of response_statements (str) and lists of citations (list[list[int]])
            If not self.multiple_statements:
            - tuple of response_statement(str) and list of citations (list[int])
        """
        if self.multiple_statements:
            # Split into statements
            split_raw_response = self.split_raw_response(raw_response)
        else:
            split_raw_response = [raw_response]

        citations = []
        statements = []
        for raw_response in split_raw_response:
            # Extract citations
            citations.append(self._process_citations(raw_response))
            # Extract textual statement
            statement = self._process_response_statement(raw_response)
            statements.append(statement)

        if self.multiple_statements:
            return statements, citations
        else:
            return statements[0], citations[0]

    @staticmethod
    def _process_citations(
            response_statement: str
    ) -> list[int]:
        """Use regex to extract citation numbers and return as ints"""
        pattern = r'\[([0-9]+)\]'
        matches = re.findall(pattern, response_statement)
        citation_idxs = []
        for match in matches:
            try:
                citation_idx = int(match)
                citation_idxs.append(citation_idx)
            except ValueError:
                continue
        return citation_idxs

    @staticmethod
    def _process_response_statement(
            response: str
    ):
        """Remove citations from response to return free text only"""
        # Remove citations
        pattern = r'\[([0-9]+)\]'
        response = re.sub(pattern, '', response)
        # Remove extra spaces
        response = re.sub(r'\s+', ' ', response)
        # Strip leading and trailing spaces
        response = response.strip()
        return response

    @staticmethod
    def split_raw_response(
            raw_response: str
    ) -> list[str]:
        """
        Split texts formatted as "<some content>. [i] [y] <some_content_2> into
        ["<some_content> [i] [j]", "<some_content_2>"
        :param raw_response: Text to split
        :return: List of response statements
        """
        def replace_abbreviations(text):
            """
            Replace common abbreviations in text
            :param text:
            :return:
            """
            # Define common abbreviations
            common_abbrevs = [
                r"Mr\.", r"Mrs\.", r"Ms\.", r"Dr\.", r"Prof\.", r"Sr\.", r"Jr\.",
                r"e\.g\.", r"i\.e\.", r"etc\.", r"vs\.", r"U\.S\.", r"U\.K\."
            ]
            # Match arbitrary abbreviations like A.B.C. or U.S.A.
            arbitrary_abbrev_pattern = r'\b(?:[A-Za-z]\.){2,}'
            # Combine all patterns into one big regex
            full_pattern = re.compile(r'(' + '|'.join(common_abbrevs + [arbitrary_abbrev_pattern]) + r')')
            abbrev_map = {}
            count = 0

            def replacer(match):
                nonlocal count
                token = f"§ABBR{count}§"
                abbrev_map[token] = match.group(0)
                count += 1
                return token

            replaced_text = full_pattern.sub(replacer, text)

            return replaced_text, abbrev_map

        def restore_abbreviations(text, abbrev_map):
            for token, original in abbrev_map.items():
                if token in text:
                    text = text.replace(token, original)
            return text

        # Replace abbreviation patterns
        text_with_tokens, abbrev_map = replace_abbreviations(raw_response)

        # sentence splitting regex (handles citations and avoids dangling dots)
        split_pattern = re.compile(r'(.*?\.(?:\s*\[\d+\])*\s*)', re.DOTALL)
        parts = []
        pos = 0

        # Go over response with replaced abbreviations and split
        while pos < len(text_with_tokens):
            # Look for next split pattern in text that was not yet processed
            match = split_pattern.match(text_with_tokens, pos)
            if not match:
                # If pattern not found, use rest of text
                remainder = text_with_tokens[pos:].strip()
                if remainder:
                    parts.append(remainder)
                break

            chunk = match.group(1).strip()
            parts.append(chunk)
            pos = match.end()

        # Restore abbreviations
        final_sentences = [
            restore_abbreviations(p.strip(), abbrev_map)
            for p in parts if p.strip() and p.strip() != "."
        ]

        return final_sentences